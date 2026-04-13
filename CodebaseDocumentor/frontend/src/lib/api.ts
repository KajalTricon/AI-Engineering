import {
  DocumentationResponse,
  ModulesResponse,
  ProjectStatusResponse,
  QueryResponse,
  SubmitProjectResponse,
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

export function submitProject(githubUrls: string[], projectName?: string) {
  return request<SubmitProjectResponse>('/projects', {
    method: 'POST',
    body: JSON.stringify({
      project_name: projectName,
      github_urls: githubUrls,
    }),
  });
}

export function getProjectStatus(projectId: string) {
  return request<ProjectStatusResponse>(`/projects/${projectId}`);
}

export function getProjectModules(projectId: string) {
  return request<ModulesResponse>(`/projects/${projectId}/modules`);
}

export function getProjectDocumentation(projectId: string) {
  return request<DocumentationResponse>(`/projects/${projectId}/documentation`);
}

export function queryProject(projectId: string, question: string) {
  return request<QueryResponse>(`/projects/${projectId}/query`, {
    method: 'POST',
    body: JSON.stringify({ question }),
  });
}

export function resumeProject(projectId: string) {
  return request<ProjectStatusResponse>(`/projects/${projectId}/resume`, {
    method: 'POST',
  });
}
