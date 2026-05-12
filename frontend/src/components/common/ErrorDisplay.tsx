interface ErrorDisplayProps {
  message: string;
  errorStage?: string;
  onRetry?: () => void;
}

export default function ErrorDisplay({ message, errorStage, onRetry }: ErrorDisplayProps) {
  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-6">
      <div className="flex items-start gap-3">
        <span className="text-red-500 text-xl">!</span>
        <div className="flex-1">
          <h3 className="text-sm font-medium text-red-800">Generation Failed</h3>
          {errorStage && <p className="text-xs text-red-500 mt-0.5">Stage: {errorStage}</p>}
          <p className="text-sm text-red-600 mt-2">{message}</p>
          {onRetry && (
            <button onClick={onRetry} className="mt-4 px-4 py-2 bg-red-600 text-white text-sm rounded-md hover:bg-red-700">
              Retry
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
