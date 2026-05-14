import { useState, useEffect } from 'react';
import { useSSE } from '../../hooks/useSSE';
import ContentRenderer from './ContentRenderer';

interface StreamSection {
  heading: string;
  slug: string;
  html: string;
  wordCount: number;
}

interface StreamingContentProps {
  articleId: string;
  totalSections: number;
  onComplete?: () => void;
}

function SectionSkeleton() {
  return (
    <div className="animate-pulse space-y-3 py-6">
      <div className="h-6 bg-gray-200 rounded w-2/3" />
      <div className="space-y-2">
        <div className="h-4 bg-gray-100 rounded w-full" />
        <div className="h-4 bg-gray-100 rounded w-5/6" />
        <div className="h-4 bg-gray-100 rounded w-4/6" />
      </div>
    </div>
  );
}

export default function StreamingContent({ articleId, totalSections, onComplete }: StreamingContentProps) {
  const [sections, setSections] = useState<StreamSection[]>([]);
  const [completed, setCompleted] = useState(false);

  useSSE(
    articleId,
    ({ event, data }) => {
      switch (event) {
        case 'section_complete':
          setSections((prev) => [
            ...prev,
            {
              heading: data.heading as string,
              slug: data.slug as string,
              html: data.html as string,
              wordCount: data.word_count as number,
            },
          ]);
          break;
        case 'done':
          setCompleted(true);
          onComplete?.();
          break;
      }
    },
    !completed,
  );

  useEffect(() => {
    if (sections.length >= totalSections && totalSections > 0) {
      setCompleted(true);
      onComplete?.();
    }
  }, [sections.length, totalSections, onComplete]);

  const pct = totalSections > 0
    ? Math.round((sections.length / totalSections) * 100)
    : 0;

  return (
    <div className="space-y-4">
      <div className="bg-white border border-gray-200/80 rounded-2xl shadow-sm p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-gray-900">
            Generating Content
          </h3>
          <span className="text-sm text-gray-500 font-mono">
            {sections.length} / {totalSections} sections
          </span>
        </div>
        <div className="w-full bg-gray-100 rounded-full h-2 mb-3">
          <div
            className="bg-gray-900 h-2 rounded-full transition-all duration-500"
            style={{ width: `${Math.max(pct, 3)}%` }}
          />
        </div>
      </div>

      {sections.map((section) => (
        <div
          key={section.slug}
          className="bg-white border border-gray-200/80 rounded-2xl shadow-sm p-6 animate-fade-in-up"
        >
          <h2 className="text-lg font-semibold text-gray-900 mb-3">{section.heading}</h2>
          <ContentRenderer html={section.html} />
          <div className="mt-3 text-xs text-gray-400 font-mono">
            {section.wordCount} words
          </div>
        </div>
      ))}

      {!completed && sections.length < totalSections && (
        <div className="bg-white border border-gray-200/80 rounded-2xl shadow-sm p-6">
          <SectionSkeleton />
        </div>
      )}
    </div>
  );
}
