import { ModuleSummary } from '../types';

interface ModuleGridProps {
  modules: ModuleSummary[];
}

export default function ModuleGrid({ modules }: ModuleGridProps) {
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
              <p className="mt-2 break-all text-xs text-slate-500">{module.path}</p>
            </div>
            <span className="rounded-full bg-[#d6ebf3] px-3 py-1 text-xs font-semibold text-[#447f98]">
              {module.language || 'unknown'}
            </span>
          </div>
          <p className="mt-4 text-sm leading-7 text-slate-600">
            {module.summary || 'Summary not available yet.'}
          </p>
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
