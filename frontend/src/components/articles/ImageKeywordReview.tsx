import { useState } from 'react';
import type { ImagePlan, ImagePlacement, CoverImagePlan } from '../../types';

interface ImageKeywordReviewProps {
  imagePlan: ImagePlan;
  sectionNames: Record<string, string>;
  isAuto: boolean;
  onApprove: (body: { plan?: ImagePlan; revisionPrompt?: string }) => void;
  onBack?: () => void;
  isPending: boolean;
}

export default function ImageKeywordReview({
  imagePlan,
  sectionNames,
  isAuto,
  onApprove,
  onBack,
  isPending,
}: ImageKeywordReviewProps) {
  const [plan, setPlan] = useState<ImagePlan>(structuredClone(imagePlan));
  const [revisionPrompt, setRevisionPrompt] = useState('');

  if (isAuto) return null;

  const updateInline = (index: number, updates: Partial<ImagePlacement>) => {
    setPlan((prev) => {
      const next = structuredClone(prev);
      next.inlineImages[index] = { ...next.inlineImages[index], ...updates };
      return next;
    });
  };

  const addInline = () => {
    setPlan((prev) => ({
      ...prev,
      inlineImages: [
        ...prev.inlineImages,
        { sectionSlug: '', position: 'before' as const, keywords: [''], suggestedCount: 1, rationale: '', key: crypto.randomUUID() },
      ],
    }));
  };

  const removeInline = (index: number) => {
    setPlan((prev) => ({
      ...prev,
      inlineImages: prev.inlineImages.filter((_, i) => i !== index),
    }));
  };

  const updateCover = (updates: Partial<CoverImagePlan>) => {
    setPlan((prev) => ({
      ...prev,
      coverImage: prev.coverImage ? { ...prev.coverImage, ...updates } : null,
    }));
  };

  const setCoverKeywords = (value: string) => {
    setPlan((prev) => ({
      ...prev,
      coverImage: {
        keywords: value.split(',').map((k) => k.trim()).filter(Boolean),
        suggestedCount: prev.coverImage?.suggestedCount ?? 1,
        rationale: prev.coverImage?.rationale ?? '',
      },
    }));
  };

  const handleApprove = () => {
    onApprove({ plan });
  };

  const handleRevise = () => {
    onApprove({ revisionPrompt: revisionPrompt || 'Improve image placement recommendations' });
  };

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-gray-900">Image Keywords Review</h2>
      <p className="text-sm text-gray-500">
        Review and edit image placements before searching. You can adjust keywords, positions, and counts.
      </p>

      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">
          Inline Images ({plan.inlineImages.length})
        </h3>
        <div className="space-y-4">
          {plan.inlineImages.map((placement, i) => (
            <div key={placement.key || i} className="border border-gray-100 rounded-md p-3 bg-gray-50">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium text-gray-500">Image {i + 1}</span>
                <button
                  onClick={() => removeInline(i)}
                  className="text-xs text-red-500 hover:text-red-700"
                >
                  Remove
                </button>
              </div>

              <div className="grid grid-cols-2 gap-3 mb-2">
                <div>
                  <label className="block text-xs text-gray-500 mb-0.5">Section</label>
                  <select
                    value={placement.sectionSlug}
                    onChange={(e) => updateInline(i, { sectionSlug: e.target.value })}
                    className="w-full px-2 py-1.5 border border-gray-200 rounded text-xs"
                  >
                    <option value="">Select section</option>
                    {Object.entries(sectionNames).map(([slug, name]) => (
                      <option key={slug} value={slug}>{name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-0.5">Position</label>
                  <select
                    value={placement.position}
                    onChange={(e) => updateInline(i, { position: e.target.value as 'before' | 'after' })}
                    className="w-full px-2 py-1.5 border border-gray-200 rounded text-xs"
                  >
                    <option value="before">Before heading</option>
                    <option value="after">After heading</option>
                  </select>
                </div>
              </div>

              <div className="mb-2">
                <label className="block text-xs text-gray-500 mb-0.5">
                  Keywords (comma separated)
                </label>
                <input
                  value={placement.keywords.join(', ')}
                  onChange={(e) =>
                    updateInline(i, {
                      keywords: e.target.value.split(',').map((k) => k.trim()).filter(Boolean),
                    })
                  }
                  className="w-full px-2 py-1.5 border border-gray-200 rounded text-xs"
                  placeholder="e.g. neural network diagram, AI architecture"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-gray-500 mb-0.5">Count</label>
                  <input
                    type="number"
                    min={1}
                    max={5}
                    value={placement.suggestedCount}
                    onChange={(e) => updateInline(i, { suggestedCount: parseInt(e.target.value) || 1 })}
                    className="w-20 px-2 py-1.5 border border-gray-200 rounded text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-0.5">Rationale</label>
                  <p className="text-xs text-gray-400">{placement.rationale}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
        <button
          onClick={addInline}
          className="mt-3 text-xs text-blue-600 hover:text-blue-800"
        >
          + Add inline image
        </button>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Cover Image</h3>
        {plan.coverImage ? (
          <div className="space-y-3">
            <div>
              <label className="block text-xs text-gray-500 mb-0.5">
                Keywords (comma separated)
              </label>
              <input
                value={plan.coverImage.keywords.join(', ')}
                onChange={(e) => setCoverKeywords(e.target.value)}
                className="w-full px-2 py-1.5 border border-gray-200 rounded text-xs"
                placeholder="e.g. modern software architecture cover"
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-gray-500 mb-0.5">Count</label>
                <input
                  type="number"
                  min={1}
                  max={5}
                  value={plan.coverImage.suggestedCount}
                  onChange={(e) => updateCover({ suggestedCount: parseInt(e.target.value) || 1 })}
                  className="w-20 px-2 py-1.5 border border-gray-200 rounded text-xs"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-0.5">Rationale</label>
                <p className="text-xs text-gray-400">{plan.coverImage.rationale}</p>
              </div>
            </div>
            <button
              onClick={() => setPlan((prev) => ({ ...prev, coverImage: null }))}
              className="text-xs text-red-500 hover:text-red-700"
            >
              Remove cover image
            </button>
          </div>
        ) : (
          <button
            onClick={() =>
              setPlan((prev) => ({
                ...prev,
                coverImage: { keywords: [''], suggestedCount: 1, rationale: '' },
              }))
            }
            className="text-xs text-blue-600 hover:text-blue-800"
          >
            + Add cover image
          </button>
        )}
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h3 className="text-sm font-medium text-gray-700 mb-2">AI Revision</h3>
        <textarea
          value={revisionPrompt}
          onChange={(e) => setRevisionPrompt(e.target.value)}
          placeholder='Describe changes, e.g. "add more technical diagram images" or "focus on abstract illustrations"'
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
          {isPending ? 'Processing...' : 'Approve & Search Images'}
        </button>
        <button
          onClick={handleRevise}
          disabled={isPending}
          className="px-6 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {isPending ? 'Revising...' : 'Revise Plan with AI'}
        </button>
        </div>
      </div>
    </div>
  );
}
