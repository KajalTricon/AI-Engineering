import { CheckCircle2, Circle, Loader2 } from 'lucide-react';
import { RepoStatusResponse } from '../types';

interface ProgressTrackerProps {
  status: RepoStatusResponse | null;
}

const stages = [
  'Cloning repository',
  'Chunking modules',
  'Embedding modules',
  'Summarizing modules',
  'Generating documentation',
];

export default function ProgressTracker({ status }: ProgressTrackerProps) {
  const activeIndex =
    status?.status === 'completed' ? stages.length : status?.status === 'failed' ? 2 : 2;

  return (
    <div className="mt-10 w-full max-w-3xl">
      <div className="mb-4 h-1.5 overflow-hidden rounded-full bg-[#629bb5]/20">
        <div
          className="h-full rounded-full bg-[#629bb5] transition-all duration-700"
          style={{
            width:
              status?.status === 'completed'
                ? '100%'
                : status?.status === 'failed'
                  ? '58%'
                  : '58%',
          }}
        />
      </div>

      <div className="space-y-4">
        {stages.map((label, index) => {
          const done = index < activeIndex || status?.status === 'completed';
          const active =
            status?.status !== 'completed' &&
            status?.status !== 'failed' &&
            index === activeIndex;

          return (
            <div
              key={label}
              className="flex items-center gap-4 rounded-[22px] border border-[#629bb5]/20 bg-white/85 px-5 py-4 shadow-[0_12px_30px_rgba(68,127,152,0.08)]"
            >
              {done ? (
                <CheckCircle2 className="text-[#447f98]" size={18} />
              ) : active ? (
                <Loader2 className="animate-spin text-[#629bb5]" size={18} />
              ) : (
                <Circle className="text-[#629bb5]/45" size={16} />
              )}
              <span className="text-sm font-medium tracking-[0.08em] text-slate-700">
                {label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
