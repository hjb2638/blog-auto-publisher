import { useState } from 'react';
import type { ArticleContent, ContentSection } from '../../types';
import ContentRenderer from './ContentRenderer';

interface ContentReviewProps {
  content: ArticleContent;
  isAuto: boolean;
  onApprove: (body: { sectionEdits?: Record<string, string>; revisionPrompt?: string; regenerateSections?: string[] }) => void;
  onBack?: () => void;
  isPending: boolean;
}

export default function ContentReview({ content, isAuto, onApprove, onBack, isPending }: ContentReviewProps) {
  const [activeSection, setActiveSection] = useState(0);
  const [editing, setEditing] = useState(false);
  const [sectionEdits, setSectionEdits] = useState<Record<string, string>>({});
  const [revisionPrompt, setRevisionPrompt] = useState('');
  const [reviseAll, setReviseAll] = useState(true);

  const section = content.sections[activeSection];
  const currentHtml = sectionEdits[section?.slug] ?? section?.html ?? '';

  const handleHtmlChange = (html: string) => {
    setSectionEdits((prev) => ({ ...prev, [section.slug]: html }));
  };

  const handleApprove = () => {
    onApprove({ sectionEdits: Object.keys(sectionEdits).length > 0 ? sectionEdits : undefined });
  };

  const handleRevise = () => {
    const regenerateSections = reviseAll
      ? content.sections.map((s) => s.slug)
      : [section.slug];
    onApprove({
      sectionEdits: Object.keys(sectionEdits).length > 0 ? sectionEdits : undefined,
      revisionPrompt: revisionPrompt || 'Improve this section',
      regenerateSections,
    });
  };

  if (isAuto) return null;

  return (
    <div className="space-y-6">
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Content Draft</h2>
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-400">
              {content.sections.length} sections &middot; {content.totalWordCount} words
            </span>
            <label className="flex items-center gap-1.5 text-xs text-gray-500">
              <input
                type="checkbox"
                checked={editing}
                onChange={(e) => setEditing(e.target.checked)}
                className="rounded"
              />
              Edit HTML
            </label>
          </div>
        </div>

        <div className="flex gap-4">
          <nav className="w-48 flex-shrink-0 space-y-1">
            {content.sections.map((s: ContentSection, i: number) => {
              const hasEdit = sectionEdits[s.slug] !== undefined;
              return (
                <button
                  key={s.slug}
                  onClick={() => setActiveSection(i)}
                  className={`w-full text-left px-3 py-2 text-sm rounded-md ${
                    i === activeSection
                      ? 'bg-blue-50 text-blue-700 font-medium'
                      : 'text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  <span className="truncate block">
                    {hasEdit && <span className="text-yellow-500 mr-1">*</span>}
                    {s.heading}
                  </span>
                  <span className="text-xs text-gray-400">{s.wordCount} words</span>
                </button>
              );
            })}
          </nav>

          <div className="flex-1 min-w-0">
            {editing ? (
              <textarea
                value={currentHtml}
                onChange={(e) => handleHtmlChange(e.target.value)}
                rows={20}
                className="w-full px-3 py-2 border border-gray-200 rounded-md text-sm font-mono focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
              />
            ) : (
              <ContentRenderer html={currentHtml} />
            )}
          </div>
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-medium text-gray-700">AI Revision</h3>
          <label className="flex items-center gap-1.5 text-xs text-gray-500">
            <input
              type="checkbox"
              checked={reviseAll}
              onChange={(e) => setReviseAll(e.target.checked)}
              className="rounded"
            />
            Apply to all sections
          </label>
        </div>
        <textarea
          value={revisionPrompt}
          onChange={(e) => setRevisionPrompt(e.target.value)}
          placeholder='Describe changes you want, e.g. "add more code examples" or "make it more beginner-friendly"'
          rows={2}
          className="w-full px-3 py-2 border border-gray-200 rounded-md text-sm focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      <div className="flex justify-between">
        {onBack && (
          <button onClick={onBack} disabled={isPending} className="px-5 py-2 border border-gray-200 text-sm font-medium rounded-md hover:bg-gray-50 disabled:opacity-50">
            &larr; Back
          </button>
        )}
        <div className="flex gap-3 ml-auto">
        <button
          onClick={handleApprove}
          disabled={isPending}
          className="px-6 py-2 bg-green-600 text-white text-sm font-medium rounded-md hover:bg-green-700 disabled:opacity-50"
        >
          {isPending ? 'Processing...' : 'Approve Content & Search Images'}
        </button>
        <button
          onClick={handleRevise}
          disabled={isPending}
          className="px-6 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {isPending ? 'Revising...' : 'Revise with AI →'}
        </button>
        </div>
      </div>
    </div>
  );
}
