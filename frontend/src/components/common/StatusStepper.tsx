import type { ArticleStatus } from '../../types';

interface Step {
  key: string;
  label: string;
  activeStates: ArticleStatus[];
  doneStates: ArticleStatus[];
}

const STEPS: Step[] = [
  {
    key: 'outline',
    label: 'Outline',
    activeStates: ['outline_generating'],
    doneStates: ['outline_ready', 'outline_approved', 'content_generating', 'content_ready', 'content_approved', 'image_keywords_generating', 'image_keywords_ready', 'image_searching', 'images_ready', 'final_approved', 'publishing', 'published'],
  },
  {
    key: 'content',
    label: 'Content',
    activeStates: ['content_generating'],
    doneStates: ['content_ready', 'content_approved', 'image_keywords_generating', 'image_keywords_ready', 'image_searching', 'images_ready', 'final_approved', 'publishing', 'published'],
  },
  {
    key: 'images',
    label: 'Images',
    activeStates: ['image_keywords_generating', 'image_searching', 'image_keywords_ready'],
    doneStates: ['images_ready', 'final_approved', 'publishing', 'published'],
  },
  {
    key: 'publish',
    label: 'Publish',
    activeStates: ['publishing'],
    doneStates: ['published'],
  },
];

interface StatusStepperProps {
  status: ArticleStatus;
  mode: 'manual' | 'auto';
}

export default function StatusStepper({ status, mode }: StatusStepperProps) {
  if (status === 'draft' || status === 'cancelled') {
    return null;
  }

  return (
    <div className="flex items-center gap-2 mb-6">
      {STEPS.map((step, i) => {
        const isDone = step.doneStates.includes(status);
        const isActive = step.activeStates.includes(status);

        return (
          <div key={step.key} className="flex items-center gap-2">
            {i > 0 && <div className={`w-8 h-px ${isDone ? 'bg-green-500' : 'bg-gray-200'}`} />}
            <div className="flex items-center gap-1.5">
              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${
                isDone ? 'bg-green-500 text-white' :
                isActive ? 'bg-blue-500 text-white animate-pulse' :
                'bg-gray-200 text-gray-400'
              }`}>
                {isDone ? '✓' : i + 1}
              </div>
              <span className={`text-sm ${isDone || isActive ? 'text-gray-900 font-medium' : 'text-gray-400'}`}>
                {step.label}
              </span>
            </div>
          </div>
        );
      })}
      {mode === 'auto' && (
        <span className="ml-2 text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded">Auto</span>
      )}
      {status === 'failed' && (
        <span className="ml-2 text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded">Error</span>
      )}
    </div>
  );
}
