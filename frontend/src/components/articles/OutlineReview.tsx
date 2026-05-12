import type { Outline, OutlineSection } from '../../types';

interface OutlineReviewProps {
  outline: Outline;
  topic: string;
  isAuto: boolean;
  onApprove: () => void;
  isPending: boolean;
}

export default function OutlineReview({ outline, topic, isAuto, onApprove, isPending }: OutlineReviewProps) {
  return (
    <div className="space-y-6">
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-gray-900">{outline.title}</h2>
        {outline.metaDescription && (
          <p className="mt-2 text-sm text-gray-500">{outline.metaDescription}</p>
        )}
        <p className="mt-1 text-xs text-gray-400">Topic: {topic}</p>

        {outline.seoKeywords.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1">
            {outline.seoKeywords.map((kw: string) => (
              <span key={kw} className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-gray-100 text-gray-600">
                {kw}
              </span>
            ))}
          </div>
        )}

        {outline.tags.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {outline.tags.map((tag: string) => (
              <span key={tag} className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-blue-50 text-blue-600">
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>

      <div>
        <h3 className="text-sm font-medium text-gray-700 mb-3">Sections ({outline.sections.length})</h3>
        <div className="space-y-2">
          {outline.sections.map((section: OutlineSection, i: number) => (
            <div key={section.slug || i} className="bg-white border border-gray-200 rounded-lg p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h4 className="text-sm font-medium text-gray-900">
                    {i + 1}. {section.heading}
                  </h4>
                  {section.keyPoints.length > 0 && (
                    <ul className="mt-2 space-y-1">
                      {section.keyPoints.map((kp: string, j: number) => (
                        <li key={j} className="text-xs text-gray-500 flex items-start gap-1.5">
                          <span className="text-gray-300 mt-0.5">•</span>
                          {kp}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
                <div className="ml-4 flex flex-col items-end gap-1 text-xs text-gray-400">
                  <span>~{section.estimatedWords} words</span>
                  {section.includeCodeExample && (
                    <span className="text-blue-500">code</span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {!isAuto && (
        <div className="flex justify-end">
          <button
            onClick={onApprove}
            disabled={isPending}
            className="px-6 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {isPending ? 'Approving...' : 'Approve Outline & Generate Content'}
          </button>
        </div>
      )}
    </div>
  );
}
