import { useState } from 'react';
import type { ArticleImage } from '../../types';

interface ImageReviewProps {
  images: ArticleImage[];
  isAuto: boolean;
  onApprove: (body: { removeImages?: string[]; revisionPrompt?: string; coverImageId?: string }) => void;
  onRemoveImage?: (imageId: string) => void;
  isPending: boolean;
}

export default function ImageReview({ images, isAuto, onApprove, onRemoveImage, isPending }: ImageReviewProps) {
  const [altEdits, setAltEdits] = useState<Record<string, string>>({});
  const [removedIds, setRemovedIds] = useState<string[]>([]);
  const [coverImageId, setCoverImageId] = useState<string | null>(null);
  const [revisionPrompt, setRevisionPrompt] = useState('');

  const inlineImages = images.filter((img) => img.type !== 'cover' && !removedIds.includes(img.id));
  const coverImages = images.filter((img) => img.type === 'cover' && !removedIds.includes(img.id));

  const imagesBySection = new Map<string, ArticleImage[]>();
  for (const img of inlineImages) {
    const list = imagesBySection.get(img.sectionSlug) || [];
    list.push(img);
    imagesBySection.set(img.sectionSlug, list);
  }

  const handleRemove = (imageId: string) => {
    setRemovedIds((prev) => [...prev, imageId]);
    if (coverImageId === imageId) setCoverImageId(null);
    onRemoveImage?.(imageId);
  };

  const handleApprove = () => {
    onApprove({
      removeImages: removedIds.length > 0 ? removedIds : undefined,
      coverImageId: coverImageId ?? undefined,
    });
  };

  const handleRevise = () => {
    onApprove({
      removeImages: removedIds.length > 0 ? removedIds : undefined,
      coverImageId: coverImageId ?? undefined,
      revisionPrompt: revisionPrompt || 'Improve the images',
    });
  };

  if (isAuto) return null;

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-gray-900">
        Image Review ({images.length - removedIds.length} selected)
      </h2>

      {coverImages.length > 0 && (
        <div className="bg-white border border-blue-200 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Cover Image</h3>
          <div className="grid grid-cols-3 gap-3">
            {coverImages.map((img) => (
              <div
                key={img.id}
                className={`relative rounded-lg overflow-hidden border-2 cursor-pointer ${
                  coverImageId === img.id ? 'border-blue-500' : 'border-gray-100'
                }`}
                onClick={() => setCoverImageId(img.id)}
              >
                <img
                  src={img.url}
                  alt={altEdits[img.id] ?? img.altText}
                  className="w-full h-40 object-cover"
                  loading="lazy"
                />
                {coverImageId === img.id && (
                  <div className="absolute top-2 left-2 w-5 h-5 bg-blue-500 text-white text-xs rounded-full flex items-center justify-center">
                    &#10003;
                  </div>
                )}
                <button
                  onClick={(e) => { e.stopPropagation(); handleRemove(img.id); }}
                  className="absolute top-2 right-2 w-6 h-6 bg-red-600 text-white text-xs rounded-full flex items-center justify-center hover:bg-red-700"
                >
                  x
                </button>
              </div>
            ))}
          </div>
          <button
            onClick={() => setCoverImageId(null)}
            className="mt-2 text-xs text-gray-500 hover:text-red-500"
          >
            No cover image
          </button>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        {Array.from(imagesBySection.entries()).map(([slug, sectionImages]) => (
          <div key={slug} className="bg-white border border-gray-200 rounded-lg p-4">
            <h3 className="text-sm font-medium text-gray-700 mb-3 capitalize">
              {slug.replace(/-/g, ' ')} ({sectionImages.length})
            </h3>
            <div className="space-y-3">
              {sectionImages.map((img) => (
                <div key={img.id} className="relative">
                  <img
                    src={img.url}
                    alt={altEdits[img.id] ?? img.altText}
                    className="w-full h-40 object-cover rounded-lg border border-gray-100"
                    loading="lazy"
                  />
                  <div className="mt-1">
                    <input
                      value={altEdits[img.id] ?? img.altText}
                      onChange={(e) => setAltEdits((prev) => ({ ...prev, [img.id]: e.target.value }))}
                      className="w-full text-xs text-gray-500 border border-gray-200 rounded px-1 py-0.5 focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                    />
                    <p className="text-xs text-gray-400 mt-0.5">
                      {img.source === 'unsplash' && `Photo by ${img.photographer}`}
                    </p>
                  </div>
                  <button
                    onClick={() => handleRemove(img.id)}
                    className="absolute top-2 right-2 w-6 h-6 bg-red-600 text-white text-xs rounded-full flex items-center justify-center hover:bg-red-700"
                    title="Remove image"
                  >
                    x
                  </button>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {removedIds.length > 0 && (
        <p className="text-xs text-gray-400">Removed {removedIds.length} image(s). Click Approve to confirm.</p>
      )}

      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h3 className="text-sm font-medium text-gray-700 mb-2">AI Revision</h3>
        <textarea
          value={revisionPrompt}
          onChange={(e) => setRevisionPrompt(e.target.value)}
          placeholder='Describe image changes, e.g. "use more technical diagrams" or "replace stock photos with architecture illustrations"'
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
          {isPending ? 'Processing...' : 'Approve Final & Publish'}
        </button>
        <button
          onClick={handleRevise}
          disabled={isPending}
          className="px-6 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {isPending ? 'Revising...' : 'Revise Images with AI'}
        </button>
      </div>
    </div>
  );
}
