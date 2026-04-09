import { useEffect, useState } from 'react';
import {
  ChevronLeft,
  FolderGit2,
  GitBranch,
  LayoutGrid,
  Network,
  PanelsTopLeft,
} from 'lucide-react';
import DocumentationFrame from '../components/DocumentationFrame';
import ErrorState from '../components/ErrorState';
import MermaidPanel from '../components/MermaidPanel';
import ModuleGrid from '../components/ModuleGrid';
import QuestionPanel from '../components/QuestionPanel';
import RepoHeader from '../components/RepoHeader';
import { ProjectWorkspace } from '../types';

type Tab = 'documentation' | 'modules' | 'architecture' | 'flow';

interface DashboardProps {
  activeProject: ProjectWorkspace;
  onAskQuestion: (question: string) => Promise<void>;
  onSelectProject: (repoId: string) => void;
  onStartOver: () => void;
  projects: ProjectWorkspace[];
}

function getProjectName(project: ProjectWorkspace) {
  return project.status?.name || project.repoUrl.split('/').filter(Boolean).pop() || 'repository';
}

export default function Dashboard({
  activeProject,
  onAskQuestion,
  onSelectProject,
  onStartOver,
  projects,
}: DashboardProps) {
  const [activeTab, setActiveTab] = useState<Tab>('documentation');
  const [chatOpen, setChatOpen] = useState(false);

  useEffect(() => {
    setActiveTab('documentation');
    setChatOpen(false);
  }, [activeProject.repoId]);

  const projectName = getProjectName(activeProject);

  const tabs = [
    { id: 'documentation', label: 'Documentation', icon: LayoutGrid },
    { id: 'modules', label: 'Modules', icon: PanelsTopLeft },
    { id: 'architecture', label: 'Architecture', icon: Network },
    { id: 'flow', label: 'Flow chart', icon: GitBranch },
  ] as const;

  const renderWorkspace = () => {
    if (activeProject.status?.status === 'failed') {
      return (
        <ErrorState
          message={activeProject.error || activeProject.status.error_message || 'Project processing failed.'}
        />
      );
    }

    if (activeProject.status?.status !== 'completed') {
      return (
        <div className="rounded-[24px] border border-[#629bb5]/22 bg-white/92 p-6 shadow-[0_18px_40px_rgba(68,127,152,0.12)]">
          <p className="text-lg font-semibold text-[#447f98]">
            {projectName} is being prepared
          </p>
          <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-600">
            We keep polling the same repository APIs for this project until the
            documentation, modules, and diagrams are ready.
          </p>
        </div>
      );
    }

    if (activeProject.workspaceLoading || !activeProject.workspaceLoaded) {
      return (
        <div className="rounded-[28px] border border-[#629bb5]/30 bg-white/92 p-8 shadow-[0_18px_40px_rgba(68,127,152,0.12)]">
          <p className="text-lg font-semibold text-[#447f98]">
            Loading project workspace
          </p>
          <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-600">
            The repository analysis is complete. We are now loading the generated
            documentation and module summaries for this project.
          </p>
        </div>
      );
    }

    if (activeProject.error) {
      return <ErrorState message={activeProject.error} />;
    }

    return (
      <>
        {activeTab === 'documentation' && (
          <DocumentationFrame markdown={activeProject.documentation?.markdown ?? null} />
        )}
        {activeTab === 'modules' && <ModuleGrid modules={activeProject.modules} />}
        {activeTab === 'architecture' && (
          <MermaidPanel
            description={activeProject.documentation?.content?.architecture.description}
            mermaid={activeProject.documentation?.content?.architecture.mermaid}
            title={activeProject.documentation?.content?.architecture.title || 'Architecture'}
          />
        )}
        {activeTab === 'flow' && (
          <MermaidPanel
            description={activeProject.documentation?.content?.flow.description}
            mermaid={activeProject.documentation?.content?.flow.mermaid}
            title={activeProject.documentation?.content?.flow.title || 'Flow chart'}
          />
        )}
      </>
    );
  };

  return (
    <div className="min-h-screen bg-[#d6ebf3]">
      <div className="flex min-h-screen">
        <aside className="fixed left-0 top-0 h-screen w-[280px] border-r border-[#629bb5]/30 bg-[#447f98] px-5 py-6">
          <div className="border-b border-[#629bb5]/20 pb-6">
            <p className="text-xs uppercase tracking-[0.28em] text-[#b9d8e1]">
              Projects
            </p>
          </div>

          <div className="mt-6 max-h-[54vh] space-y-2 overflow-y-auto pr-1">
            {projects.map((project) => {
              const isActive = project.repoId === activeProject.repoId;
              const statusLabel = project.status?.status || 'submitted';

              return (
                <button
                  key={project.repoId}
                  className={`w-full rounded-[22px] border px-4 py-4 text-left transition ${
                    isActive
                      ? 'border-[#d6ebf3] bg-[#629bb5]/28'
                      : 'border-[#629bb5]/20 bg-[#629bb5]/10 hover:bg-[#629bb5]/18'
                  }`}
                  onClick={() => onSelectProject(project.repoId)}
                  type="button"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <FolderGit2 className="shrink-0 text-[#d6ebf3]" size={16} />
                        <p className="truncate font-mono text-sm font-semibold text-white">
                          {getProjectName(project)}
                        </p>
                      </div>
                      <p className="mt-2 truncate text-xs text-[#b9d8e1]">
                        {project.repoUrl}
                      </p>
                    </div>
                    <span className="rounded-full bg-white/14 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-[#d6ebf3]">
                      {statusLabel}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>

          <button
            className="mt-8 w-full rounded-full border border-white/70 bg-[#d6ebf3] px-4 py-3 text-sm font-semibold text-[#224e63] shadow-[0_12px_24px_rgba(0,0,0,0.14)] transition hover:-translate-y-0.5 hover:bg-white"
            onClick={() => setChatOpen(true)}
            type="button"
          >
            Ask about selected project
          </button>

          <button
            className="mt-3 w-full rounded-full border border-white/70 bg-[#d6ebf3] px-4 py-3 text-sm font-semibold text-[#224e63] shadow-[0_12px_24px_rgba(0,0,0,0.1)] transition hover:-translate-y-0.5 hover:bg-white"
            onClick={onStartOver}
            type="button"
          >
            Start a new workspace
          </button>
        </aside>

        <main className="ml-[280px] flex-1">
          <div className="mx-auto max-w-7xl px-8 py-8">
            <div className="mb-8 space-y-6">
              <RepoHeader
                name={projectName}
                repoUrl={activeProject.status?.github_url || activeProject.repoUrl}
                status={activeProject.status?.status || 'submitted'}
              />

              {!chatOpen ? (
                <div className="inline-flex rounded-full border border-[#629bb5]/30 bg-white/80 p-1 shadow-[0_12px_30px_rgba(68,127,152,0.12)]">
                  {tabs.map((tab) => (
                    <button
                      key={tab.id}
                      className={`inline-flex items-center gap-2 rounded-full px-5 py-3 text-sm font-semibold transition ${
                        activeTab === tab.id
                          ? 'bg-[#447f98] text-white shadow-[0_10px_24px_rgba(68,127,152,0.2)]'
                          : 'text-[#447f98] hover:bg-[#d6ebf3] hover:text-[#1c4659]'
                      }`}
                      onClick={() => setActiveTab(tab.id)}
                      type="button"
                    >
                      <tab.icon size={16} />
                      {tab.label}
                    </button>
                  ))}
                </div>
              ) : (
                <button
                  className="inline-flex items-center gap-2 rounded-full border border-white/70 bg-[#d6ebf3] px-4 py-3 text-sm font-semibold text-[#224e63] shadow-[0_10px_24px_rgba(68,127,152,0.12)] transition hover:-translate-y-0.5 hover:bg-white"
                  onClick={() => setChatOpen(false)}
                  type="button"
                >
                  <ChevronLeft size={16} />
                  Back to workspace
                </button>
              )}
            </div>

            {!chatOpen && renderWorkspace()}

            {chatOpen && (
              <div className="h-[calc(100vh-220px)] overflow-hidden rounded-[30px] border border-[#629bb5]/30 shadow-[0_18px_40px_rgba(68,127,152,0.14)]">
                <QuestionPanel
                  history={activeProject.qaHistory}
                  onAsk={onAskQuestion}
                  onClose={() => setChatOpen(false)}
                  projectName={projectName}
                />
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
