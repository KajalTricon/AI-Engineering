import { useMemo, useState } from 'react';
import { BookOpen, ChevronLeft, GitBranch, LayoutGrid, MessageSquare, Network } from 'lucide-react';
import DocumentationFrame from '../components/DocumentationFrame';
import MermaidPanel from '../components/MermaidPanel';
import ModuleGrid from '../components/ModuleGrid';
import QuestionPanel from '../components/QuestionPanel';
import RepoHeader from '../components/RepoHeader';
import {
  DocumentationResponse,
  ModuleSummary,
  QAPair,
  RepoStatusResponse,
} from '../types';

type Tab = 'documentation' | 'modules' | 'architecture' | 'flow';

interface DashboardProps {
  documentation: DocumentationResponse | null;
  modules: ModuleSummary[];
  onAskQuestion: (question: string) => Promise<void>;
  onStartOver: () => void;
  qaHistory: QAPair[];
  repoStatus: RepoStatusResponse;
  repoUrl: string;
}

export default function Dashboard({
  documentation,
  modules,
  onAskQuestion,
  onStartOver,
  qaHistory,
  repoStatus,
  repoUrl,
}: DashboardProps) {
  const [activeTab, setActiveTab] = useState<Tab>('documentation');
  const [chatOpen, setChatOpen] = useState(false);

  const repoName = useMemo(
    () => repoStatus.name || repoUrl.split('/').filter(Boolean).pop() || 'repository',
    [repoStatus.name, repoUrl],
  );

  const tabs = [
    { id: 'documentation', label: 'Documentation', icon: LayoutGrid },
    { id: 'modules', label: 'Modules', icon: BookOpen },
    { id: 'architecture', label: 'Architecture', icon: Network },
    { id: 'flow', label: 'Flow chart', icon: GitBranch },
  ] as const;

  return (
    <div className="min-h-screen bg-[#d6ebf3]">
      <div className="flex min-h-screen">
        <aside className="fixed left-0 top-0 h-screen w-[240px] border-r border-[#629bb5]/30 bg-[#447f98] px-5 py-6">
          <RepoHeader name={repoName} repoUrl={repoStatus.github_url} status={repoStatus.status} />

          <div className="mt-8">
            <p className="text-xs uppercase tracking-[0.28em] text-[#b9d8e1]">
              Modules
            </p>
            <div className="mt-4 max-h-[48vh] space-y-1 overflow-y-auto pr-1">
              {modules.map((module) => (
                <div
                  key={module.module_id}
                  className="rounded-r-full border-l-2 border-[#629bb5] bg-[#629bb5]/10 px-3 py-2 font-mono text-sm text-[#d6ebf3]"
                >
                  {module.path}
                </div>
              ))}
            </div>
          </div>

          <div className="mt-8 space-y-2 text-sm text-[#dadee1]">
            <p>Overview</p>
            <p>Architecture</p>
            <p>Setup Guide</p>
            <p>API Reference</p>
          </div>

          <button
            className="mt-10 w-full rounded-full bg-[#629bb5] px-4 py-3 text-sm font-semibold text-[#447f98] transition hover:bg-white"
            onClick={() => setChatOpen(true)}
            type="button"
          >
            Ask a question
          </button>

          <button
            className="mt-3 w-full rounded-full border border-[#629bb5]/40 px-4 py-3 text-sm font-semibold text-[#d6ebf3] transition hover:bg-[#629bb5]/15"
            onClick={onStartOver}
            type="button"
          >
            Analyze another repo
          </button>
        </aside>

        <main className="ml-[240px] flex-1">
          <div className="mx-auto max-w-7xl px-8 py-8">
            <div className="mb-8 flex items-center justify-between">
              {!chatOpen ? (
                <div className="inline-flex rounded-full border border-[#629bb5]/30 bg-white/80 p-1 shadow-[0_12px_30px_rgba(68,127,152,0.12)]">
                  {tabs.map((tab) => (
                    <button
                      key={tab.id}
                      className={`inline-flex items-center gap-2 rounded-full px-5 py-3 text-sm font-semibold transition ${
                        activeTab === tab.id
                          ? 'bg-[#447f98] text-white'
                          : 'text-[#447f98] hover:bg-[#d6ebf3]'
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
                  className="inline-flex items-center gap-2 rounded-full border border-[#629bb5]/30 bg-white/85 px-4 py-3 text-sm font-semibold text-[#447f98]"
                  onClick={() => setChatOpen(false)}
                  type="button"
                >
                  <ChevronLeft size={16} />
                  Back to workspace
                </button>
              )}
            </div>

            {!chatOpen && (
              <>
                {activeTab === 'documentation' && (
                  <DocumentationFrame markdown={documentation?.markdown ?? null} />
                )}
                {activeTab === 'modules' && <ModuleGrid modules={modules} />}
                {activeTab === 'architecture' && (
                  <MermaidPanel
                    description={documentation?.content?.architecture.description}
                    mermaid={documentation?.content?.architecture.mermaid}
                    title={documentation?.content?.architecture.title || 'Architecture'}
                  />
                )}
                {activeTab === 'flow' && (
                  <MermaidPanel
                    description={documentation?.content?.flow.description}
                    mermaid={documentation?.content?.flow.mermaid}
                    title={documentation?.content?.flow.title || 'Flow chart'}
                  />
                )}
              </>
            )}

            {chatOpen && (
              <div className="h-[calc(100vh-120px)] overflow-hidden rounded-[30px] border border-[#629bb5]/30 shadow-[0_18px_40px_rgba(68,127,152,0.14)]">
                <QuestionPanel
                  history={qaHistory}
                  onAsk={onAskQuestion}
                  onClose={() => setChatOpen(false)}
                />
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
