import { useState } from 'react';
import type { ArticleContent, ContentSection } from '../../types';
import ContentRenderer from './ContentRenderer';

interface ContentReviewProps {
  content: ArticleContent;
  isAuto: boolean;
  onApprove: () => void;
  isPending: boolean;
}

export default function ContentReview({ content, isAuto, onApprove, isPending }: ContentReviewProps) {
  const [activeSection, setActiveSection] = useState(0);

  return (
    <div className="space-y-6">
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Content Draft</h2>
          <span className="text-sm text-gray-400">
            {content.sections.length} sections &middot; {content.totalWordCount} words
          </span>
        </div>

        <div className="flex gap-4">
          <nav className="w-48 flex-shrink-0 space-y-1">
            {content.sections.map((section: ContentSection, i: number) => (
              <button
                key={section.slug}
                onClick={() => setActiveSection(i)}
                className={`w-full text-left px-3 py-2 text-sm rounded-md ${
                  i === activeSection
                    ? 'bg-blue-50 text-blue-700 font-medium'
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                <span className="truncate block">{section.heading}</span>
                <span className="text-xs text-gray-400">{section.wordCount} words</span>
              </button>
            ))}
          </nav>

          <div className="flex-1 min-w-0">
            <ContentRenderer html={content.sections[activeSection]?.html || ''} />
          </div>
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Full Article Preview</h3>
        <ContentRenderer html={content.fullHtml} />
      </div>

      {!isAuto && (
        <div className="flex justify-end">
          <button
            onClick={onApprove}
            disabled={isPending}
            className="px-6 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {isPending ? 'Approving...' : 'Approve Content & Search Images'}
          </button>
        </div>
      )}
    </div>
  );
}
