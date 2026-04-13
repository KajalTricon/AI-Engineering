import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ModuleSummary } from '../types';

interface ModuleGridProps {
  modules: ModuleSummary[];
}

export default function ModuleGrid({ modules }: ModuleGridProps) {
  if (modules.length === 0) {
    return (
      <div className="rounded-[28px] border border-[#629bb5]/30 bg-white/92 p-8 shadow-[0_18px_40px_rgba(68,127,152,0.12)]">
        <p className="text-lg font-semibold text-[#447f98]">No modules found</p>
        <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-600">
          This project finished processing, but no directory-level modules were
          extracted for display.
        </p>
      </div>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {modules.map((module) => (
        <article
          key={module.module_id}
          className="rounded-[24px] border border-[#629bb5]/22 bg-white/95 p-6 shadow-[0_18px_40px_rgba(68,127,152,0.12)]"
        >
          <div className="flex items-start justify-between gap-4">
            <div>
              <h3 className="font-mono text-base font-semibold text-[#447f98]">
                {module.name}
              </h3>
              {module.repository_name && (
                <p className="mt-1 text-xs font-semibold uppercase tracking-[0.14em] text-[#7aa3b5]">
                  {module.repository_name}
                </p>
              )}
              <p className="mt-2 break-all text-xs text-slate-500">{module.path}</p>
            </div>
            <span className="rounded-full bg-[#d6ebf3] px-3 py-1 text-xs font-semibold text-[#447f98]">
              {module.language || 'unknown'}
            </span>
          </div>
            <div className="mt-4 text-sm leading-7 text-slate-600 prose prose-slate prose-sm max-w-none
                  prose-p:my-1 prose-headings:text-slate-700 prose-headings:font-semibold
                  prose-code:bg-slate-100 prose-code:text-pink-600 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:text-xs
                  prose-strong:text-slate-700 prose-ul:list-disc prose-ol:list-decimal prose-li:my-0">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {module.summary || 'Summary not available yet.'}
                  </ReactMarkdown>
            </div>
          {module.dependencies.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-2">
              {module.dependencies.map((dependency) => (
                <span
                  key={dependency}
                  className="rounded-full bg-[#dadee1] px-3 py-1 text-xs text-slate-700"
                >
                  {dependency}
                </span>
              ))}
            </div>
          )}
        </article>
      ))}
    </div>
  );
}
