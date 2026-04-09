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
  return project.status?.name || project.repoUrl.split('/').filter(Boolean).pop() || 'repository';
}

export default function ProgressTracker({ projects }: ProgressTrackerProps) {
  if (!projects.length) {
    return null;
  }

  const completedCount = projects.filter((project) => project.status?.status === 'completed').length;
  const failedCount = projects.filter((project) => project.status?.status === 'failed').length;
  const totalCount = projects.length;
  const allCompleted = completedCount === totalCount;

  const steps = [
    {
      id: 'submitted',
      icon: <Clock3 size={18} />,
      title: `Submitted ${totalCount} ${totalCount === 1 ? 'repository' : 'repositories'}`,
      tone: 'text-[#d6ebf3]',
      done: true,
    },
    ...projects.map((project) => {
      const status = project.status?.status;
      const statusLabel = status || 'submitted';

      if (status === 'completed') {
        return {
          id: project.repoId,
          icon: <CheckCircle2 size={18} />,
          title: `${getProjectName(project)} completed`,
          tone: 'text-[#d6ebf3]',
          done: true,
        };
      }

      if (status === 'failed') {
        return {
          id: project.repoId,
          icon: <AlertCircle size={18} />,
          title: `${getProjectName(project)} failed`,
          subtitle: project.error || project.status?.error_message || 'Processing stopped before completion.',
          tone: 'text-rose-200',
          done: false,
        };
      }

      return {
        id: project.repoId,
        icon: <Loader2 className="animate-spin" size={18} />,
        title: `${getProjectName(project)} ${statusLabel}`,
        subtitle: 'Generating summaries and documentation',
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
          : `Waiting for ${totalCount - completedCount} ${totalCount - completedCount === 1 ? 'repository' : 'repositories'}`,
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
