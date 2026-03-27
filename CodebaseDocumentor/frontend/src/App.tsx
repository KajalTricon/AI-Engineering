import { useEffect, useState } from 'react';
import ErrorState from './components/ErrorState';
import {
  getRepositoryDocumentation,
  getRepositoryModules,
  getRepositoryStatus,
  queryRepository,
  submitRepository,
} from './lib/api';
import Dashboard from './pages/Dashboard';
import Home from './pages/Home';
import {
  DocumentationResponse,
  ModuleSummary,
  QAPair,
  RepoStatusResponse,
} from './types';

type View = 'submit' | 'dashboard';

function App() {
  const [view, setView] = useState<View>('submit');
  const [repoId, setRepoId] = useState<string | null>(null);
  const [repoUrl, setRepoUrl] = useState('');
  const [status, setStatus] = useState<RepoStatusResponse | null>(null);
  const [documentation, setDocumentation] = useState<DocumentationResponse | null>(null);
  const [modules, setModules] = useState<ModuleSummary[]>([]);
  const [qaHistory, setQaHistory] = useState<QAPair[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!repoId || view !== 'submit') return;

    let cancelled = false;

    const loadWorkspace = async () => {
      const [docsResponse, modulesResponse] = await Promise.all([
        getRepositoryDocumentation(repoId),
        getRepositoryModules(repoId),
      ]);

      if (cancelled) return;

      setDocumentation(docsResponse);
      setModules(modulesResponse.modules);
      setView('dashboard');
    };

    const poll = window.setInterval(async () => {
      try {
        const nextStatus = await getRepositoryStatus(repoId);
        if (cancelled) return;
        setStatus(nextStatus);

        if (nextStatus.status === 'completed') {
          window.clearInterval(poll);
          await loadWorkspace();
        } else if (nextStatus.status === 'failed') {
          window.clearInterval(poll);
          setError(nextStatus.error_message || 'Repository processing failed.');
        }
      } catch (pollError) {
        if (!cancelled) {
          setError(
            pollError instanceof Error
              ? pollError.message
              : 'Unable to refresh repository status.',
          );
        }
      }
    }, 3000);

    return () => {
      cancelled = true;
      window.clearInterval(poll);
    };
  }, [repoId, view]);

  const handleSubmit = async (url: string) => {
    setSubmitting(true);
    setError(null);
    setQaHistory([]);
    setDocumentation(null);
    setModules([]);

    try {
      const response = await submitRepository(url);
      setRepoId(response.repo_id);
      setRepoUrl(url);

      const nextStatus = await getRepositoryStatus(response.repo_id);
      setStatus(nextStatus);

      if (nextStatus.status === 'completed') {
        const [docsResponse, modulesResponse] = await Promise.all([
          getRepositoryDocumentation(response.repo_id),
          getRepositoryModules(response.repo_id),
        ]);
        setDocumentation(docsResponse);
        setModules(modulesResponse.modules);
        setView('dashboard');
      }
    } catch (submitError) {
      setError(
        submitError instanceof Error
          ? submitError.message
          : 'Unable to submit repository.',
      );
    } finally {
      setSubmitting(false);
    }
  };

  const handleAskQuestion = async (question: string) => {
    if (!repoId) return;

    const response = await queryRepository(repoId, question);
    setQaHistory((previous) => [
      ...previous,
      {
        id: `${Date.now()}-${previous.length}`,
        question,
        answer: response.answer,
        sources: response.sources.map((source) => source.path || source.module),
      },
    ]);
  };

  const handleReset = () => {
    setView('submit');
    setRepoId(null);
    setRepoUrl('');
    setStatus(null);
    setDocumentation(null);
    setModules([]);
    setQaHistory([]);
    setError(null);
  };

  if (view === 'dashboard' && status) {
    return (
      <Dashboard
        documentation={documentation}
        modules={modules}
        onAskQuestion={handleAskQuestion}
        onStartOver={handleReset}
        qaHistory={qaHistory}
        repoStatus={status}
        repoUrl={repoUrl}
      />
    );
  }

  return (
    <Home
      error={error}
      isSubmitting={submitting}
      onReset={handleReset}
      onSubmit={handleSubmit}
      repoUrl={repoUrl}
      status={status}
    />
  );
}

export default App;
