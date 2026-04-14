import {
  AlertCircle,
  CheckCircle2,
  Clock3,
  Loader2,
} from 'lucide-react';
import { ProjectWorkspace } from '../types';

interface ProgressTrackerProps {
  projects: ProjectWorkspace[];
}

function getProjectName(project: ProjectWorkspace) {
  return project.status?.name || project.projectName || 'project';
}

export default function ProgressTracker({ projects }: ProgressTrackerProps) {
  if (!projects.length) {
    return null;
  }

  const completedCount = projects.filter((project) => project.status?.status === 'completed').length;
  const failedCount = projects.filter((project) => project.status?.status === 'failed').length;
  
  // Count unique repositories (not projects)
  const uniqueRepos = new Set<string>();
  projects.forEach(project => {
    project.repositories.forEach(repo => uniqueRepos.add(repo.github_url));
  });
  const totalRepoCount = uniqueRepos.size;
  
  const allCompleted = completedCount === projects.length;

  const steps = [
    {
      id: 'submitted',
      icon: <Clock3 size={18} />,
      title: `Submitted ${totalRepoCount} ${totalRepoCount === 1 ? 'repository' : 'repositories'}`,
      tone: 'text-[#d6ebf3]',
      done: true,
    },
    ...projects.map((project) => {
      const status = project.status?.status;
      const statusLabel = status || 'submitted';
      const isCombined = project.status?.repository_count && project.status.repository_count > 1;

      if (status === 'completed') {
        return {
          id: project.projectId,
          icon: <CheckCircle2 size={18} />,
          title: `${getProjectName(project)} completed`,
          tone: 'text-[#d6ebf3]',
          done: true,
        };
      }

      if (status === 'failed') {
        return {
          id: project.projectId,
          icon: <AlertCircle size={18} />,
          title: `${getProjectName(project)} failed`,
          subtitle: project.error || project.status?.error_message || 'Processing stopped before completion.',
          tone: 'text-rose-200',
          done: false,
        };
      }

      return {
        id: project.projectId,
        icon: <Loader2 className="animate-spin" size={18} />,
        title: `${getProjectName(project)} ${isCombined ? 'analyzing' : statusLabel}`,
        subtitle: isCombined ? 'Generating combined documentation' : 'Generating summaries and documentation',
        tone: 'text-[#d6ebf3]',
        done: false,
      };
    }),
    {
      id: 'done',
      icon: <CheckCircle2 size={18} />,
      title: allCompleted
        ? 'Done'
        : failedCount > 0
          ? 'Waiting for successful completion'
          : `Waiting for ${projects.length - completedCount} ${projects.length - completedCount === 1 ? 'project' : 'projects'}`,
      tone: allCompleted ? 'text-[#d6ebf3]' : 'text-[#b9d8e1]',
      done: allCompleted,
    },
  ];

  return (
    <div className="w-full max-w-[920px] text-left">
      <div className="space-y-3">
        {steps.map((step, index) => (
          <div key={step.id} className="relative pl-10">
            {index < steps.length - 1 && (
              <span className="absolute left-[8px] top-7 h-[calc(100%+6px)] w-px bg-white/18" />
            )}
            <span className={`absolute left-0 top-0 ${step.tone}`}>
              {step.icon}
            </span>
            <div className={step.done ? 'text-[#d6ebf3]' : step.tone}>
              <p className="text-[15px] leading-7">{step.title}</p>
              {'subtitle' in step && step.subtitle && (
                <p className="text-sm leading-6 text-[#b9d8e1]">{step.subtitle}</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
 