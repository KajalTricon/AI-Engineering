import { FormEvent, useState } from 'react';
import { Github } from 'lucide-react';
import ErrorState from '../components/ErrorState';
import ProgressTracker from '../components/ProgressTracker';
import { RepoStatusResponse } from '../types';

interface HomeProps {
  error: string | null;
  isSubmitting: boolean;
  onReset: () => void;
  onSubmit: (url: string) => Promise<void>;
  repoUrl: string;
  status: RepoStatusResponse | null;
}

export default function Home({
  error,
  isSubmitting,
  onReset,
  onSubmit,
  repoUrl,
  status,
}: HomeProps) {
  const [url, setUrl] = useState(repoUrl);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!url.trim() || isSubmitting) return;
    await onSubmit(url.trim());
  };

  const showProgress = Boolean(repoUrl);

  return (
    <div className="min-h-screen bg-[#447f98]">
      <div className="mx-auto flex min-h-screen w-full max-w-5xl flex-col px-6 py-8 lg:px-8">
        <main className="flex flex-1 flex-col items-center justify-center">
          <div className="w-full max-w-3xl text-center">
            <h1 className="text-5xl font-semibold tracking-tight text-white sm:text-6xl">
              Documentation that writes itself.
            </h1>
            <p className="mx-auto mt-5 max-w-2xl text-base leading-8 text-[#dadee1]">
              Paste a GitHub URL. Get structured docs, module summaries, and a live
              Q&amp;A interface powered by AI agents.
            </p>

            <form className="mt-10" onSubmit={handleSubmit}>
              <div className="rounded-full border border-[#629bb5]/45 bg-[#447f98] px-3 py-3 shadow-[0_16px_45px_rgba(0,0,0,0.18)]">
                <div className="flex items-center rounded-full border border-[#629bb5]/35 bg-[#447f98]/95 px-4 py-2 focus-within:shadow-[0_0_0_4px_rgba(98,155,181,0.4)]">
                  <Github className="mr-3 text-[#dadee1]" size={18} />
                  <input
                    className="min-w-0 flex-1 bg-transparent py-3 text-base text-white outline-none placeholder:text-[#b9d8e1]"
                    onChange={(event) => setUrl(event.target.value)}
                    placeholder="https://github.com/username/repository"
                    value={url}
                  />
                  <button
                    className="rounded-full bg-[#629bb5] px-6 py-3 text-sm font-semibold text-[#447f98] transition hover:bg-[#d6ebf3] disabled:cursor-not-allowed disabled:opacity-70"
                    disabled={!url.trim() || isSubmitting}
                    type="submit"
                  >
                    {showProgress ? 'Re-run →' : 'Analyze repo →'}
                  </button>
                </div>
              </div>
            </form>

            <p className="mt-4 text-sm text-[#b9d8e1]">
              Supports Python, JavaScript, TypeScript, Java, Go, Rust and more
            </p>

            {showProgress && <ProgressTracker status={status} />}

            {error && (
              <div className="mt-8 text-left">
                <ErrorState message={error} onRetry={onReset} />
              </div>
            )}
          </div>
        </main>

        <footer className="flex items-center justify-center gap-3 py-5 text-sm text-[#b9d8e1]">
          <span>© 2026 codedoc</span>
          <span>·</span>
          <a className="underline-offset-4 hover:underline" href="http://localhost:8000/docs" rel="noreferrer" target="_blank">
            API docs
          </a>
        </footer>
      </div>
    </div>
  );
}
