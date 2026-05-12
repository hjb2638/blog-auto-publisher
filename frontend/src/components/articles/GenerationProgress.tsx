import type { Progress } from '../../types';

interface GenerationProgressProps {
  progress: Progress;
  onCancel?: () => void;
  elapsedSeconds: number;
}

const STAGE_LABELS: Record<string, string> = {
  outline: 'Generating outline...',
  content: 'Writing content...',
  images: 'Searching for images...',
};

export default function GenerationProgress({ progress, onCancel, elapsedSeconds }: GenerationProgressProps) {
  const stageLabel = STAGE_LABELS[progress.stage] || `Processing ${progress.stage}...`;
  const pct = progress.totalSections > 0
    ? Math.round((progress.currentSection / progress.totalSections) * 100)
    : 0;

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-medium text-gray-900">{stageLabel}</h3>
          {progress.heading && (
            <p className="text-xs text-gray-500 mt-1">{progress.heading}</p>
          )}
        </div>
        <span className="text-sm text-gray-500">{Math.floor(elapsedSeconds)}s</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
        <div
          className="bg-blue-600 h-2 rounded-full transition-all duration-500"
          style={{ width: `${Math.min(pct || 5, 100)}%` }}
        />
      </div>
      <div className="flex items-center justify-between text-xs text-gray-400">
        <span>
          {progress.currentSection > 0
            ? `Section ${progress.currentSection} of ${progress.totalSections}`
            : 'Starting...'}
        </span>
        {onCancel && (
          <button onClick={onCancel} className="text-red-500 hover:text-red-700">
            Cancel
          </button>
        )}
      </div>
    </div>
  );
}
