import { ExternalLink, Github } from 'lucide-react';

interface RepoHeaderProps {
  name: string;
  repoUrl: string;
  status: string;
}

export default function RepoHeader({ name, repoUrl, status }: RepoHeaderProps) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-[#629bb5]/20 pb-6">
      <div>
        <div className="flex items-center gap-2">
          <Github className="text-[#447f98]" size={18} />
          <h1 className="font-mono text-lg font-semibold text-white">{name}</h1>
          <a href={repoUrl} rel="noreferrer" target="_blank">
            <ExternalLink className="text-[#b9d8e1]" size={14} />
          </a>
        </div>
        <p className="mt-2 text-sm text-[#dadee1]">{status}</p>
      </div>
    </div>
  );
}
