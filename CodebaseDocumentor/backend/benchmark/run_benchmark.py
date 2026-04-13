"""Benchmark runner for CodebaseDocumentor project processing."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class BenchmarkRun:
    benchmark_name: str
    bucket: str
    run_index: int
    project_id: str
    success: bool
    final_status: str
    resumed: bool
    documentation_ok: bool
    query_ok: bool
    total_seconds: float
    error_message: str
    repository_count: int


def request_json(method: str, url: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"{method} {url} failed with {exc.code}: {body}") from exc


def poll_project(base_url: str, project_id: str, timeout_seconds: int, poll_interval_seconds: int) -> dict[str, Any]:
    deadline = time.time() + timeout_seconds
    last_payload: dict[str, Any] | None = None

    while time.time() < deadline:
        last_payload = request_json("GET", f"{base_url}/projects/{project_id}")
        status = last_payload.get("status")
        if status in {"completed", "failed"}:
            return last_payload
        time.sleep(poll_interval_seconds)

    raise TimeoutError(f"Timed out waiting for project {project_id}. Last payload: {last_payload}")


def run_single_project(
    *,
    base_url: str,
    benchmark_name: str,
    bucket: str,
    github_urls: list[str],
    run_index: int,
    timeout_seconds: int,
    poll_interval_seconds: int,
    resume_once_on_failure: bool,
    query_smoke_test: str,
) -> BenchmarkRun:
    start_time = time.time()
    submit_payload = request_json(
        "POST",
        f"{base_url}/projects",
        {
            "project_name": f"{benchmark_name} run {run_index}",
            "github_urls": github_urls,
        },
    )
    project_id = submit_payload["project_id"]
    repository_count = submit_payload.get("total_repositories", len(github_urls))

    resumed = False
    status_payload = poll_project(base_url, project_id, timeout_seconds, poll_interval_seconds)

    if status_payload.get("status") == "failed" and resume_once_on_failure:
        resumed = True
        request_json("POST", f"{base_url}/projects/{project_id}/resume")
        status_payload = poll_project(base_url, project_id, timeout_seconds, poll_interval_seconds)

    documentation_ok = False
    query_ok = False
    error_message = status_payload.get("error_message") or ""

    if status_payload.get("status") == "completed":
        try:
            docs_payload = request_json("GET", f"{base_url}/projects/{project_id}/documentation")
            documentation_ok = bool(docs_payload.get("content") or docs_payload.get("markdown"))
        except Exception as exc:
            error_message = str(exc)

        try:
            query_payload = request_json(
                "POST",
                f"{base_url}/projects/{project_id}/query",
                {"question": query_smoke_test},
            )
            query_ok = bool(query_payload.get("answer"))
        except Exception as exc:
            error_message = str(exc)

    success = (
        status_payload.get("status") == "completed"
        and documentation_ok
        and query_ok
    )

    return BenchmarkRun(
        benchmark_name=benchmark_name,
        bucket=bucket,
        run_index=run_index,
        project_id=project_id,
        success=success,
        final_status=status_payload.get("status", "unknown"),
        resumed=resumed,
        documentation_ok=documentation_ok,
        query_ok=query_ok,
        total_seconds=round(time.time() - start_time, 2),
        error_message=error_message,
        repository_count=repository_count,
    )


def write_reports(results: list[BenchmarkRun], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "benchmark_results.json"
    csv_path = output_dir / "benchmark_results.csv"
    summary_path = output_dir / "benchmark_summary.txt"

    payload = [result.__dict__ for result in results]
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(results[0].__dict__.keys()) if results else [])
        if results:
            writer.writeheader()
            for result in results:
                writer.writerow(result.__dict__)

    bucket_groups: dict[str, list[BenchmarkRun]] = {}
    for result in results:
        bucket_groups.setdefault(result.bucket, []).append(result)

    lines = ["Benchmark Summary", "================="]
    total_success = sum(1 for result in results if result.success)
    total_runs = len(results)
    lines.append(f"Overall success rate: {total_success}/{total_runs} = {percentage(total_success, total_runs)}")

    if results:
        durations = [result.total_seconds for result in results]
        lines.append(f"Median duration: {statistics.median(durations):.2f}s")
        lines.append(f"Average duration: {statistics.mean(durations):.2f}s")

    for bucket, bucket_results in sorted(bucket_groups.items()):
        bucket_success = sum(1 for result in bucket_results if result.success)
        resumed_count = sum(1 for result in bucket_results if result.resumed)
        lines.append("")
        lines.append(f"Bucket: {bucket}")
        lines.append(f"  Success rate: {bucket_success}/{len(bucket_results)} = {percentage(bucket_success, len(bucket_results))}")
        lines.append(f"  Resume used: {resumed_count}/{len(bucket_results)}")
        lines.append(f"  Failures: {sum(1 for result in bucket_results if not result.success)}")

    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def percentage(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "n/a"
    return f"{(numerator / denominator) * 100:.1f}%"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run CodebaseDocumentor benchmark suites.")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000/api/v1",
        help="Base API URL for the backend.",
    )
    parser.add_argument(
        "--config",
        default="backend/benchmark/sample_benchmark_config.json",
        help="Path to benchmark config JSON.",
    )
    parser.add_argument(
        "--output-dir",
        default="backend/benchmark/results",
        help="Directory where JSON/CSV/summary reports are written.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_path = Path(args.config)
    config = json.loads(config_path.read_text(encoding="utf-8"))

    poll_interval_seconds = int(config.get("poll_interval_seconds", 5))
    timeout_seconds = int(config.get("timeout_seconds", 1800))
    resume_once_on_failure = bool(config.get("resume_once_on_failure", True))
    query_smoke_test = str(config.get("query_smoke_test", "What does this project do?"))

    results: list[BenchmarkRun] = []

    for project in config.get("projects", []):
        benchmark_name = project["name"]
        bucket = project.get("bucket", "unclassified")
        github_urls = list(project["github_urls"])
        repeats = int(project.get("repeats", 1))

        for run_index in range(1, repeats + 1):
            print(f"Running benchmark: {benchmark_name} [{bucket}] run {run_index}/{repeats}")
            result = run_single_project(
                base_url=args.base_url,
                benchmark_name=benchmark_name,
                bucket=bucket,
                github_urls=github_urls,
                run_index=run_index,
                timeout_seconds=timeout_seconds,
                poll_interval_seconds=poll_interval_seconds,
                resume_once_on_failure=resume_once_on_failure,
                query_smoke_test=query_smoke_test,
            )
            results.append(result)
            print(
                f"  -> status={result.final_status} success={result.success} resumed={result.resumed} duration={result.total_seconds}s"
            )
            if result.error_message:
                print(f"  -> error={result.error_message}")

    write_reports(results, Path(args.output_dir))
    print(f"Saved benchmark reports to {args.output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
