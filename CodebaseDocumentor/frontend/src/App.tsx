import { useEffect, useRef, useState } from 'react';
import {
  getRepositoryDocumentation,
  getRepositoryModules,
  getRepositoryStatus,
  queryRepository,
  submitRepositories,
} from './lib/api';
import Dashboard from './pages/Dashboard';
import Home from './pages/Home';
import { ProjectWorkspace } from './types';

type View = 'submit' | 'dashboard';

function parseRepositoryUrls(input: string) {
  const seen = new Set<string>();

  return input
    .split(/\r?\n|,/)
    .map((value) => value.trim())
    .filter(Boolean)
    .filter((value) => {
      if (seen.has(value)) {
        return false;
      }

      seen.add(value);
      return true;
    });
}

function updateProject(
  projects: ProjectWorkspace[],
  repoId: string,
  updater: (project: ProjectWorkspace) => ProjectWorkspace,
) {
  return projects.map((project) => (
    project.repoId === repoId ? updater(project) : project
  ));
}

function isTerminalStatus(status: ProjectWorkspace['status']) {
  return status?.status === 'completed' || status?.status === 'failed';
}

function App() {
  const [view, setView] = useState<View>('submit');
  const [projects, setProjects] = useState<ProjectWorkspace[]>([]);
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const projectsRef = useRef<ProjectWorkspace[]>([]);

  useEffect(() => {
    projectsRef.current = projects;
  }, [projects]);

  const loadProjectWorkspace = async (repoId: string) => {
    const currentProject = projectsRef.current.find((project) => project.repoId === repoId);

    if (!currentProject || currentProject.workspaceLoaded || currentProject.workspaceLoading) {
      return;
    }

    setProjects((previous) => updateProject(previous, repoId, (project) => ({
      ...project,
      workspaceLoading: true,
      error: null,
    })));

    try {
      const [documentation, modulesResponse] = await Promise.all([
        getRepositoryDocumentation(repoId),
        getRepositoryModules(repoId),
      ]);

      setProjects((previous) => updateProject(previous, repoId, (project) => ({
        ...project,
        documentation,
        modules: modulesResponse.modules,
        workspaceLoaded: true,
        workspaceLoading: false,
        error: null,
      })));
    } catch (workspaceError) {
      setProjects((previous) => updateProject(previous, repoId, (project) => ({
        ...project,
        workspaceLoading: false,
        error:
          workspaceError instanceof Error
            ? workspaceError.message
            : 'Unable to load the selected project workspace.',
      })));
    }
  };

  const refreshProjectStatus = async (repoId: string) => {
    try {
      const nextStatus = await getRepositoryStatus(repoId);

      setProjects((previous) => updateProject(previous, repoId, (project) => ({
        ...project,
        status: nextStatus,
        error:
          nextStatus.status === 'failed'
            ? nextStatus.error_message || 'Repository processing failed.'
            : project.error,
      })));

      if (nextStatus.status === 'completed') {
        await loadProjectWorkspace(repoId);
      }
    } catch (statusError) {
      setProjects((previous) => updateProject(previous, repoId, (project) => ({
        ...project,
        error:
          statusError instanceof Error
            ? statusError.message
            : 'Unable to refresh repository status.',
      })));
    }
  };

  useEffect(() => {
    if (!projects.length) {
      return;
    }

    let cancelled = false;

    const refreshPendingProjects = async () => {
      const pendingRepoIds = projectsRef.current
        .filter((project) => !isTerminalStatus(project.status))
        .map((project) => project.repoId);

      if (!pendingRepoIds.length) {
        return;
      }

      await Promise.all(
        pendingRepoIds.map(async (repoId) => {
          if (cancelled) {
            return;
          }

          await refreshProjectStatus(repoId);
        }),
      );
    };

    void refreshPendingProjects();

    const poll = window.setInterval(() => {
      void refreshPendingProjects();
    }, 3000);

    return () => {
      cancelled = true;
      window.clearInterval(poll);
    };
  }, [projects.length]);

  useEffect(() => {
    if (view !== 'submit' || !projects.length) {
      return;
    }

    const allCompleted = projects.every((project) => project.status?.status === 'completed');
    const hasFailed = projects.some((project) => project.status?.status === 'failed');
    const allWorkspacesLoaded = projects.every((project) => project.workspaceLoaded);

    if (!allCompleted || hasFailed || !allWorkspacesLoaded) {
      return;
    }

    setView('dashboard');
  }, [projects, view]);

  const handleSubmit = async (input: string) => {
    const githubUrls = parseRepositoryUrls(input);

    if (!githubUrls.length) {
      setError('Enter at least one GitHub repository URL.');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const response = await submitRepositories(githubUrls);
      const nextProjects: ProjectWorkspace[] = response.repositories.map((repository) => ({
        repoId: repository.repo_id,
        repoUrl: repository.github_url,
        status: null,
        documentation: null,
        modules: [],
        qaHistory: [],
        error: null,
        workspaceLoaded: false,
        workspaceLoading: false,
      }));

      projectsRef.current = nextProjects;
      setProjects(nextProjects);
      setActiveProjectId(nextProjects[0]?.repoId ?? null);

      await Promise.all(
        nextProjects.map(async (project) => {
          await refreshProjectStatus(project.repoId);
        }),
      );
    } catch (submitError) {
      setError(
        submitError instanceof Error
          ? submitError.message
          : 'Unable to submit repositories.',
      );
    } finally {
      setSubmitting(false);
    }
  };

  const handleAskQuestion = async (question: string) => {
    if (!activeProjectId) {
      return;
    }

    const pairId = `${Date.now()}-${question.length}`;

    try {
      const response = await queryRepository(activeProjectId, question);

      setProjects((previous) => updateProject(previous, activeProjectId, (project) => ({
        ...project,
        qaHistory: [
          ...project.qaHistory,
          {
            id: pairId,
            question,
            answer: response.answer,
            sources: response.sources.map((source) => source.path || source.module),
          },
        ],
      })));
    } catch (queryError) {
      setProjects((previous) => updateProject(previous, activeProjectId, (project) => ({
        ...project,
        qaHistory: [
          ...project.qaHistory,
          {
            id: pairId,
            question,
            answer:
              queryError instanceof Error
                ? queryError.message
                : 'Unable to answer that question right now.',
            sources: [],
          },
        ],
      })));
    }
  };

  const handleSelectProject = (repoId: string) => {
    setActiveProjectId(repoId);

    const project = projectsRef.current.find((item) => item.repoId === repoId);

    if (
      project?.status?.status === 'completed'
      && !project.workspaceLoaded
      && !project.workspaceLoading
    ) {
      void loadProjectWorkspace(repoId);
    }
  };

  const handleReset = () => {
    projectsRef.current = [];
    setView('submit');
    setProjects([]);
    setActiveProjectId(null);
    setError(null);
  };

  const activeProject = projects.find((project) => project.repoId === activeProjectId) ?? null;

  if (view === 'dashboard' && activeProject) {
    return (
      <Dashboard
        activeProject={activeProject}
        onAskQuestion={handleAskQuestion}
        onSelectProject={handleSelectProject}
        onStartOver={handleReset}
        projects={projects}
      />
    );
  }

  return (
    <Home
      error={error}
      isSubmitting={submitting}
      onSubmit={handleSubmit}
      projects={projects}
    />
  );
}

export default App;
