import { useState, useEffect } from 'react';
import type { Outline, OutlineSection } from '../../types';

interface OutlineReviewProps {
  outline: Outline;
  topic: string;
  isAuto: boolean;
  onApprove: (body: { title?: string; sections?: OutlineSection[]; revisionPrompt?: string }) => void;
  isPending: boolean;
}

export default function OutlineReview({ outline, topic, isAuto, onApprove, isPending }: OutlineReviewProps) {
  const [title, setTitle] = useState(outline.title);
  const [metaDescription, setMetaDescription] = useState(outline.metaDescription);
  const [sections, setSections] = useState<OutlineSection[]>(
    outline.sections.map((s) => ({ ...s, keyPoints: [...s.keyPoints] }))
  );
  const [revisionPrompt, setRevisionPrompt] = useState('');

  useEffect(() => {
    setTitle(outline.title);
    setMetaDescription(outline.metaDescription);
    setSections(outline.sections.map((s) => ({ ...s, keyPoints: [...s.keyPoints] })));
  }, [outline]);

  const updateSection = (index: number, field: keyof OutlineSection, value: unknown) => {
    setSections((prev) => prev.map((s, i) => (i === index ? { ...s, [field]: value } : s)));
  };

  const updateKeyPoint = (sectionIndex: number, pointIndex: number, value: string) => {
    setSections((prev) =>
      prev.map((s, i) =>
        i === sectionIndex
          ? { ...s, keyPoints: s.keyPoints.map((kp, j) => (j === pointIndex ? value : kp)) }
          : s
      )
    );
  };

  const addKeyPoint = (sectionIndex: number) => {
    setSections((prev) =>
      prev.map((s, i) =>
        i === sectionIndex ? { ...s, keyPoints: [...s.keyPoints, ''] } : s
      )
    );
  };

  const removeKeyPoint = (sectionIndex: number, pointIndex: number) => {
    setSections((prev) =>
      prev.map((s, i) =>
        i === sectionIndex
          ? { ...s, keyPoints: s.keyPoints.filter((_, j) => j !== pointIndex) }
          : s
      )
    );
  };

  const handleApprove = () => {
    onApprove({ title, sections, revisionPrompt: undefined });
  };

  const handleRevise = () => {
    onApprove({ title, sections, revisionPrompt: revisionPrompt || 'Improve the outline' });
  };

  if (isAuto) return null;

  return (
    <div className="space-y-6">
      <div className="bg-white border border-gray-200 rounded-lg p-6 space-y-4">
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Title</label>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full px-3 py-2 border border-gray-200 rounded-md text-sm focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Meta Description</label>
          <textarea
            value={metaDescription}
            onChange={(e) => setMetaDescription(e.target.value)}
            rows={2}
            className="w-full px-3 py-2 border border-gray-200 rounded-md text-sm focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <p className="text-xs text-gray-400">Topic: {topic}</p>
      </div>

      <div>
        <h3 className="text-sm font-medium text-gray-700 mb-3">Sections ({sections.length})</h3>
        <div className="space-y-3">
          {sections.map((section, i) => (
            <div key={section.slug || i} className="bg-white border border-gray-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <span className="text-xs text-gray-400 mt-2.5">{i + 1}.</span>
                <div className="flex-1 space-y-3">
                  <input
                    value={section.heading}
                    onChange={(e) => updateSection(i, 'heading', e.target.value)}
                    className="w-full px-3 py-1.5 border border-gray-200 rounded text-sm font-medium focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Section heading"
                  />
                  <div className="space-y-1.5">
                    {section.keyPoints.map((kp, j) => (
                      <div key={j} className="flex items-center gap-2">
                        <span className="text-gray-300 text-xs">•</span>
                        <input
                          value={kp}
                          onChange={(e) => updateKeyPoint(i, j, e.target.value)}
                          className="flex-1 px-2 py-1 border border-gray-200 rounded text-xs focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                          placeholder="Key point"
                        />
                        <button
                          onClick={() => removeKeyPoint(i, j)}
                          className="text-gray-400 hover:text-red-500 text-xs"
                        >
                          ×
                        </button>
                      </div>
                    ))}
                    <button
                      onClick={() => addKeyPoint(i)}
                      className="text-xs text-blue-600 hover:text-blue-700 ml-4"
                    >
                      + Add point
                    </button>
                  </div>
                  <div className="flex items-center gap-4">
                    <label className="flex items-center gap-1.5 text-xs text-gray-500">
                      Words:
                      <input
                        type="number"
                        value={section.estimatedWords}
                        onChange={(e) => updateSection(i, 'estimatedWords', Number(e.target.value))}
                        className="w-16 px-2 py-0.5 border border-gray-200 rounded text-xs"
                      />
                    </label>
                    <label className="flex items-center gap-1.5 text-xs text-gray-500">
                      <input
                        type="checkbox"
                        checked={section.includeCodeExample}
                        onChange={(e) => updateSection(i, 'includeCodeExample', e.target.checked)}
                        className="rounded"
                      />
                      Code
                    </label>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h3 className="text-sm font-medium text-gray-700 mb-2">AI Revision</h3>
        <textarea
          value={revisionPrompt}
          onChange={(e) => setRevisionPrompt(e.target.value)}
          placeholder='Describe changes you want, e.g. "make it more beginner-friendly" or "add a section about deployment"'
          rows={2}
          className="w-full px-3 py-2 border border-gray-200 rounded-md text-sm focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      <div className="flex justify-end gap-3">
        <button
          onClick={handleApprove}
          disabled={isPending}
          className="px-6 py-2 bg-green-600 text-white text-sm font-medium rounded-md hover:bg-green-700 disabled:opacity-50"
        >
          {isPending ? 'Processing...' : 'Approve as-is'}
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
  );
}
