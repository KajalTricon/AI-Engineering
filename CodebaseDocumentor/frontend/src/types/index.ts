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
  name?: string | null;
  status: RepoStatus;
  commit_sha?: string | null;
}

export interface ProjectSummary {
  project_id: string;
  name: string;
  status: RepoStatus;
  repository_count: number;
}

export interface SubmitProjectResponse {
  project_id: string;
  name: string;
  status: RepoStatus;
  message: string;
  repositories: SubmittedRepository[];
  total_repositories: number;
  related_projects?: ProjectSummary[] | null;
}

export interface ProjectStatusResponse {
  project_id: string;
  name: string;
  status: RepoStatus;
  error_message?: string | null;
  repository_count: number;
  created_at: string;
  updated_at: string;
  repositories: SubmittedRepository[];
}

export interface ModuleSummary {
  module_id: string;
  repository_id: string;
  repository_name?: string | null;
  path: string;
  name: string;
  language?: string | null;
  summary?: string | null;
  dependencies: string[];
}

export interface ModulesResponse {
  project_id: string;
  total_modules: number;
  modules: ModuleSummary[];
}

export interface DocumentationResponse {
  project_id: string;
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
    repositories: Array<{
      name: string;
      github_url: string;
      summary: string;
      key_modules: string[];
      depends_on: string[];
    }>;
    modules: Array<{
      repository: string;
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
  repository: string;
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
  projectId: string;
  projectName: string;
  repositories: SubmittedRepository[];
  status: ProjectStatusResponse | null;
  documentation: DocumentationResponse | null;
  modules: ModuleSummary[];
  qaHistory: QAPair[];
  error: string | null;
  workspaceLoaded: boolean;
  workspaceLoading: boolean;
}
 