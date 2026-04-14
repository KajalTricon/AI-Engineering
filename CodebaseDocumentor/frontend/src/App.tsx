import { useEffect, useRef, useState } from 'react';
import {
  getProjectDocumentation,
  getProjectModules,
  getProjectStatus,
  queryProject,
  resumeProject,
  submitProject,
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
  projectId: string,
  updater: (project: ProjectWorkspace) => ProjectWorkspace,
) {
  return projects.map((project) => (
    project.projectId === projectId ? updater(project) : project
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

  const loadProjectWorkspace = async (projectId: string) => {
    const currentProject = projectsRef.current.find((project) => project.projectId === projectId);

    if (!currentProject || currentProject.workspaceLoaded || currentProject.workspaceLoading) {
      return;
    }

    setProjects((previous) => updateProject(previous, projectId, (project) => ({
      ...project,
      workspaceLoading: true,
      error: null,
    })));

    try {
      const [documentation, modulesResponse] = await Promise.all([
        getProjectDocumentation(projectId),
        getProjectModules(projectId),
      ]);

      setProjects((previous) => updateProject(previous, projectId, (project) => ({
        ...project,
        documentation,
        modules: modulesResponse.modules,
        workspaceLoaded: true,
        workspaceLoading: false,
        error: null,
      })));
    } catch (workspaceError) {
      setProjects((previous) => updateProject(previous, projectId, (project) => ({
        ...project,
        workspaceLoading: false,
        error:
          workspaceError instanceof Error
            ? workspaceError.message
            : 'Unable to load the selected project workspace.',
      })));
    }
  };

  const refreshProjectStatus = async (projectId: string) => {
    try {
      const nextStatus = await getProjectStatus(projectId);

      setProjects((previous) => updateProject(previous, projectId, (project) => ({
        ...project,
        status: nextStatus,
        error:
          nextStatus.status === 'failed'
            ? nextStatus.error_message || 'Project processing failed.'
            : project.error,
      })));

      if (nextStatus.status === 'completed') {
        await loadProjectWorkspace(projectId);
      }
    } catch (statusError) {
      setProjects((previous) => updateProject(previous, projectId, (project) => ({
        ...project,
        error:
          statusError instanceof Error
            ? statusError.message
            : 'Unable to refresh project status.',
      })));
    }
  };

  useEffect(() => {
    if (!projects.length) {
      return;
    }

    let cancelled = false;

    const refreshPendingProjects = async () => {
      const pendingProjectIds = projectsRef.current
        .filter((project) => !isTerminalStatus(project.status))
        .map((project) => project.projectId);

      if (!pendingProjectIds.length) {
        return;
      }

      await Promise.all(
        pendingProjectIds.map(async (projectId) => {
          if (cancelled) {
            return;
          }

          await refreshProjectStatus(projectId);
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
      const response = await submitProject(githubUrls);
      
      // If there are related_projects (individual + combined), create workspace for each
      let nextProjects: ProjectWorkspace[];
      
      if (response.related_projects) {
        // Fetch full status for each related project to get their repositories
        const projectPromises = response.related_projects.map(async (proj) => {
          const fullStatus = await getProjectStatus(proj.project_id);
          return {
            projectId: proj.project_id,
            projectName: proj.name,
            repositories: fullStatus.repositories,
            status: fullStatus,
            documentation: null,
            modules: [],
            qaHistory: [],
            error: null,
            workspaceLoaded: false,
            workspaceLoading: false,
          };
        });
        
        nextProjects = await Promise.all(projectPromises);
      } else {
        // Single project submission
        nextProjects = [{
          projectId: response.project_id,
          projectName: response.name,
          repositories: response.repositories,
          status: null,
          documentation: null,
          modules: [],
          qaHistory: [],
          error: null,
          workspaceLoaded: false,
          workspaceLoading: false,
        }];
      }

      projectsRef.current = nextProjects;
      setProjects(nextProjects);
      setActiveProjectId(nextProjects[0]?.projectId ?? null);

      // Refresh status for all projects
      await Promise.all(
        nextProjects.map(async (project) => {
          await refreshProjectStatus(project.projectId);
        }),
      );
    } catch (submitError) {
      setError(
        submitError instanceof Error
          ? submitError.message
          : 'Unable to submit project.',
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
      const response = await queryProject(activeProjectId, question);

      setProjects((previous) => updateProject(previous, activeProjectId, (project) => ({
        ...project,
        qaHistory: [
          ...project.qaHistory,
          {
            id: pairId,
            question,
            answer: response.answer,
            sources: response.sources.map((source) => (
              [source.repository, source.path || source.module].filter(Boolean).join(' / ')
            )),
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

  const handleResumeProject = async (projectId: string) => {
    try {
      const nextStatus = await resumeProject(projectId);
      setProjects((previous) => updateProject(previous, projectId, (project) => ({
        ...project,
        status: nextStatus,
        error: null,
      })));
      await refreshProjectStatus(projectId);
    } catch (resumeError) {
      setProjects((previous) => updateProject(previous, projectId, (project) => ({
        ...project,
        error:
          resumeError instanceof Error
            ? resumeError.message
            : 'Unable to resume this project right now.',
      })));
    }
  };

  const handleSelectProject = (projectId: string) => {
    setActiveProjectId(projectId);

    const project = projectsRef.current.find((item) => item.projectId === projectId);

    if (
      project?.status?.status === 'completed'
      && !project.workspaceLoaded
      && !project.workspaceLoading
    ) {
      void loadProjectWorkspace(projectId);
    }
  };

  const handleReset = () => {
    projectsRef.current = [];
    setView('submit');
    setProjects([]);
    setActiveProjectId(null);
    setError(null);
  };

  const activeProject = projects.find((project) => project.projectId === activeProjectId) ?? null;

  if (view === 'dashboard' && activeProject) {
    return (
      <Dashboard
        activeProject={activeProject}
        onAskQuestion={handleAskQuestion}
        onResumeProject={handleResumeProject}
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
 