import {
  DocumentationResponse,
  ModulesResponse,
  QueryResponse,
  RepoStatusResponse,
  SubmitRepoResponse,
} from '../types';

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers || {}),
    },
    ...init,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function submitRepository(githubUrl: string) {
  return request<SubmitRepoResponse>('/repositories', {
    method: 'POST',
    body: JSON.stringify({ github_url: githubUrl }),
  });
}

export function getRepositoryStatus(repoId: string) {
  return request<RepoStatusResponse>(`/repositories/${repoId}`);
}

export function getRepositoryModules(repoId: string) {
  return request<ModulesResponse>(`/repositories/${repoId}/modules`);
}

export function getRepositoryDocumentation(repoId: string) {
  return request<DocumentationResponse>(`/repositories/${repoId}/documentation`);
}

export function queryRepository(repoId: string, question: string) {
  return request<QueryResponse>(`/repositories/${repoId}/query`, {
    method: 'POST',
    body: JSON.stringify({ question }),
  });
}
