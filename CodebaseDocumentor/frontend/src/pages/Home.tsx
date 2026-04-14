import { FormEvent, useEffect, useRef, useState } from 'react';
import { Github } from 'lucide-react';
import ErrorState from '../components/ErrorState';
import ProgressTracker from '../components/ProgressTracker';
import { ProjectWorkspace } from '../types';

interface HomeProps {
  error: string | null;
  isSubmitting: boolean;
  onSubmit: (urls: string) => Promise<void>;
  projects: ProjectWorkspace[];
}

export default function Home({
  error,
  isSubmitting,
  onSubmit,
  projects,
}: HomeProps) {
  const [urls, setUrls] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    const element = textareaRef.current;

    if (!element) {
      return;
    }

    element.style.height = '0px';
    const nextHeight = Math.min(Math.max(element.scrollHeight, 38), 220);
    element.style.height = `${nextHeight}px`;
  }, [urls]);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!urls.trim() || isSubmitting) return;
    await onSubmit(urls);
  };

  return (
    <div className="min-h-screen bg-[#447f98]">
      <div className="mx-auto flex min-h-screen w-full max-w-5xl flex-col px-6 py-8 lg:px-8">
        <main className="flex flex-1 flex-col items-center justify-center">
          <div className="w-full max-w-3xl text-center">
            <h1 className="text-5xl font-semibold tracking-tight text-white sm:text-6xl">
              Analyze, Understand, Document - All in One
            </h1>
            <p className="mx-auto mt-5 max-w-2xl text-base leading-8 text-[#dadee1]">
              Group one or many repositories into a single project and get structured docs, module summaries, diagrams, and project-specific
              Q&amp;A in one workspace.
            </p>

            <div className="mt-10 flex flex-col items-start justify-center gap-6">
              <form className="w-full flex-1" onSubmit={handleSubmit}>
                <div className="mx-auto max-w-[760px]">
                  <div className="rounded-[20px] bg-[#4f87a1] px-4 py-3.5 shadow-[0_14px_34px_rgba(0,0,0,0.12)]">
                    <div className="rounded-[16px] bg-[#4f87a1] px-3 py-2.5">
                      <div className="flex items-center gap-3">
                        <Github className="text-[#dadee1]" size={17} />
                        <p className="text-sm font-medium text-[#dadee1]">
                          Add one or more GitHub repos
                        </p>
                      </div>
                      <textarea
                        ref={textareaRef}
                        className="mt-2 w-full resize-none overflow-hidden bg-transparent text-[15px] leading-6 text-white outline-none placeholder:text-[#b9d8e1]"
                        onChange={(event) => setUrls(event.target.value)}
                        placeholder="Enter GitHub repository URLs"
                        rows={1}
                        value={urls}
                      />

                      <div className="mt-3 flex justify-start">
                        <button
                          className="rounded-full bg-[#d6ebf3] px-5 py-2.5 text-sm font-semibold text-[#224e63] shadow-[0_10px_22px_rgba(0,0,0,0.12)] transition hover:-translate-y-0.5 hover:bg-white"
                          disabled={!urls.trim() || isSubmitting}
                          type="submit"
                        >
                          {isSubmitting ? 'Starting workspace...' : 'Analyze projects →'}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </form>
            </div>

            {(isSubmitting || projects.length > 0) && (
              <div className="mt-8 text-left">
                <ProgressTracker projects={projects} />
              </div>
            )}

            <p className="mt-5 text-sm text-[#b9d8e1]">
              Supports single-repo and multi-repo workspaces across Python,
              JavaScript, TypeScript, Java, Go, Rust and more
            </p>

            {error && (
              <div className="mt-8 text-left">
                <ErrorState message={error} />
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
 