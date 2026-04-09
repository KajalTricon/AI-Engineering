import { ExternalLink, Github } from 'lucide-react';

interface RepoHeaderProps {
  name: string;
  repoUrl: string;
  status: string;
}

const statusStyles: Record<string, string> = {
  completed: 'bg-emerald-400/20 text-emerald-300 border border-emerald-400/30',
  processing: 'bg-yellow-400/20 text-yellow-300 border border-yellow-400/30',
  pending:    'bg-slate-400/20 text-slate-300 border border-slate-400/30',
  failed:     'bg-red-400/20 text-red-300 border border-red-400/30',
};

export default function RepoHeader({ name, repoUrl, status }: RepoHeaderProps) {
  const badgeClass = statusStyles[status] ?? statusStyles.pending;

  return (
    <div className="border-b border-[#629bb5]/20 pb-5">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <Github className="shrink-0 text-[#224e63]" size={16} />
          <h1 className="font-mono text-base font-bold text-[#224e63] leading-tight break-all">
            {name}
          </h1>
        </div>
        <a
          href={repoUrl}
          rel="noreferrer"
          target="_blank"
          className="shrink-0 mt-0.5 text-[#b9d8e1] hover:text-white transition"
        >
          <ExternalLink size={14} />
        </a>
      </div>
      <span className={`mt-3 inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${badgeClass}`}>
        {status}
      </span>
    </div>
  );
}

