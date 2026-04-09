export type RepoStatus = 'pending' | 'processing' | 'completed' | 'failed';

export type ProcessingStep =
  | 'cloning'
  | 'chunking'
  | 'embedding'
  | 'analyzing'
  | 'generating';

export type StepStatus = 'done' | 'running' | 'pending' | 'failed';

export type ProcessingStage =
  | 'submitted'
  | 'cloning'
  | 'chunking'
  | 'embedding'
  | 'summarizing'
  | 'documentation';

export interface SubmittedRepository {
  repo_id: string;
  github_url: string;
  status: RepoStatus;
  message: string;
  reused: boolean;
  commit_sha?: string | null;
}

export interface SubmitRepoResponse {
  repositories: SubmittedRepository[];
  total_submitted: number;
  total_reused: number;
  repo_id?: string | null;
  status?: RepoStatus | null;
  message?: string | null;
  reused?: boolean | null;
  commit_sha?: string | null;
}

export interface RepoStatusResponse {
  repo_id: string;
  github_url: string;
  name?: string | null;
  normalized_url?: string | null;
  commit_sha?: string | null;
  status: RepoStatus;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ModuleSummary {
  module_id: string;
  path: string;
  name: string;
  language?: string | null;
  summary?: string | null;
  dependencies: string[];
}

export interface ModulesResponse {
  repo_id: string;
  total_modules: number;
  modules: ModuleSummary[];
}

export interface DocumentationResponse {
  repo_id: string;
  url: string;
  created_at: string;
  markdown?: string | null;
  content?: {
    title: string;
    overview: string;
    architecture: {
      title: string;
      description: string;
      mermaid: string;
    };
    flow: {
      title: string;
      description: string;
      mermaid: string;
    };
    setup_notes: string[];
    modules: Array<{
      name: string;
      path: string;
      summary: string;
      responsibilities: string[];
      important_files: string[];
      dependencies: string[];
    }>;
    operational_notes: string[];
  } | null;
}

export interface QuerySource {
  module: string;
  path: string;
}

export interface QueryResponse {
  answer: string;
  sources: QuerySource[];
}

export interface QAPair {
  id: string;
  question: string;
  answer: string;
  sources: string[];
}

export interface ProjectWorkspace {
  repoId: string;
  repoUrl: string;
  status: RepoStatusResponse | null;
  documentation: DocumentationResponse | null;
  modules: ModuleSummary[];
  qaHistory: QAPair[];
  error: string | null;
  workspaceLoaded: boolean;
  workspaceLoading: boolean;
}
