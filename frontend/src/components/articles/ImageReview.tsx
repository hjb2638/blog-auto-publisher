import { useState, useMemo } from 'react';
import type { ArticleImage, ContentSection } from '../../types';

interface ImageReviewProps {
  images: ArticleImage[];
  sections?: ContentSection[];
  isAuto: boolean;
  onApprove: (body: { selectedImages?: string[]; removeImages?: string[]; revisionPrompt?: string; coverImageId?: string }) => void;
  onRemoveImage?: (imageId: string) => void;
  onBack?: () => void;
  isPending: boolean;
}

function stripHtml(html: string): string {
  const div = document.createElement('div');
  div.innerHTML = html;
  return div.textContent || div.innerText || '';
}

function ImageSkeleton() {
  return (
    <div className="animate-pulse">
      <div className="w-full h-40 bg-gray-200 rounded-lg" />
      <div className="mt-1 h-3 bg-gray-100 rounded w-3/4" />
      <div className="mt-1 h-2 bg-gray-100 rounded w-1/2" />
    </div>
  );
}

export default function ImageReview({ images, sections, isAuto, onApprove, onRemoveImage, onBack, isPending }: ImageReviewProps) {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(() => new Set(images.map((img) => img.id)));
  const [altEdits, setAltEdits] = useState<Record<string, string>>({});
  const [coverImageId, setCoverImageId] = useState<string | null>(null);
  const [revisionPrompt, setRevisionPrompt] = useState('');
  const [loadedImages, setLoadedImages] = useState<Set<string>>(new Set());

  const sectionMap = useMemo(() => {
    if (!sections) return new Map<string, ContentSection>();
    const m = new Map<string, ContentSection>();
    for (const s of sections) {
      m.set(s.slug, s);
    }
    return m;
  }, [sections]);

  const selectedList = images.filter((img) => selectedIds.has(img.id));
  const inlineImages = selectedList.filter((img) => img.type !== 'cover');
  const coverImages = selectedList.filter((img) => img.type === 'cover');

  const imagesBySection = new Map<string, ArticleImage[]>();
  for (const img of inlineImages) {
    const list = imagesBySection.get(img.sectionSlug) || [];
    list.push(img);
    imagesBySection.set(img.sectionSlug, list);
  }

  const toggleSelect = (imageId: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(imageId)) {
        next.delete(imageId);
      } else {
        next.add(imageId);
      }
      return next;
    });
  };

  const handleRemove = (imageId: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      next.delete(imageId);
      return next;
    });
    if (coverImageId === imageId) setCoverImageId(null);
    onRemoveImage?.(imageId);
  };

  const handleApprove = () => {
    onApprove({
      selectedImages: [...selectedIds],
      coverImageId: coverImageId ?? undefined,
    });
  };

  const handleRevise = () => {
    onApprove({
      selectedImages: [...selectedIds],
      coverImageId: coverImageId ?? undefined,
      revisionPrompt: revisionPrompt || 'Improve the images',
    });
  };

  const onImageLoad = (id: string) => {
    setLoadedImages((prev) => new Set(prev).add(id));
  };

  if (isAuto) return null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">
          Image Review ({selectedIds.size} of {images.length} selected)
        </h2>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setSelectedIds(new Set(images.map((img) => img.id)))}
            className="text-xs text-blue-600 hover:text-blue-800"
          >
            Select all
          </button>
          <button
            onClick={() => setSelectedIds(new Set())}
            className="text-xs text-gray-500 hover:text-red-500"
          >
            Deselect all
          </button>
        </div>
      </div>

      {coverImages.length > 0 && (
        <div className="bg-white border border-blue-200 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Cover Image</h3>
          <div className="grid grid-cols-3 gap-3">
            {coverImages.map((img) => (
              <div
                key={img.id}
                className={`relative rounded-lg overflow-hidden border-2 cursor-pointer ${
                  coverImageId === img.id ? 'border-blue-500' : 'border-gray-100'
                } ${!loadedImages.has(img.id) ? 'border-dashed' : ''}`}
                onClick={() => setCoverImageId(img.id)}
              >
                {!loadedImages.has(img.id) && <ImageSkeleton />}
                <img
                  src={img.url}
                  alt={altEdits[img.id] ?? img.altText}
                  className={`w-full h-40 object-cover ${!loadedImages.has(img.id) ? 'hidden' : ''}`}
                  loading="lazy"
                  onLoad={() => onImageLoad(img.id)}
                />
                <label
                  className="absolute top-2 left-2 flex items-center gap-1 bg-white/90 rounded px-1.5 py-0.5"
                  onClick={(e) => e.stopPropagation()}
                >
                  <input
                    type="checkbox"
                    checked={selectedIds.has(img.id)}
                    onChange={() => toggleSelect(img.id)}
                    className="rounded w-3.5 h-3.5"
                  />
                </label>
                {coverImageId === img.id && (
                  <div className="absolute top-8 left-2 w-5 h-5 bg-blue-500 text-white text-xs rounded-full flex items-center justify-center">
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
        {Array.from(imagesBySection.entries()).map(([slug, sectionImages]) => {
          const section = sectionMap.get(slug);
          const beforeImages = sectionImages.filter((img) => img.position === 'before');
          const afterImages = sectionImages.filter((img) => img.position !== 'before');
          const sectionText = section ? stripHtml(section.html).substring(0, 150) : '';

          return (
            <div key={slug} className="bg-white border border-gray-200 rounded-lg p-4">
              <h3 className="text-sm font-medium text-gray-700 mb-1 capitalize">
                {slug.replace(/-/g, ' ')}
              </h3>
              <p className="text-xs text-gray-400 mb-3">
                {sectionImages.length} image{sectionImages.length !== 1 ? 's' : ''}
                {sectionText && (
                  <span className="ml-2 italic">&ldquo;{sectionText}{sectionText.length >= 150 ? '...' : ''}&rdquo;</span>
                )}
              </p>

              {sectionText && (
                <details className="mb-3 text-xs">
                  <summary className="text-gray-400 cursor-pointer hover:text-gray-600">
                    Show image positions
                  </summary>
                  <div className="mt-2 p-3 bg-gray-50 rounded border border-gray-100 space-y-1.5">
                    {beforeImages.length > 0 && (
                      <div className="flex items-center gap-1.5 text-blue-600">
                        <span className="text-lg">&#x1f5bc;</span>
                        <span>&lt;image&gt; (before heading) x{beforeImages.length}</span>
                      </div>
                    )}
                    <p className="text-gray-500 leading-relaxed">
                      <span className="font-medium text-gray-700">{section?.heading || slug}</span>
                      <br />
                      {sectionText}
                      {sectionText.length >= 150 ? '...' : ''}
                    </p>
                    {afterImages.length > 0 && (
                      <div className="flex items-center gap-1.5 text-green-600">
                        <span className="text-lg">&#x1f5bc;</span>
                        <span>&lt;image&gt; (after heading) x{afterImages.length}</span>
                      </div>
                    )}
                  </div>
                </details>
              )}

              <div className="space-y-3">
                {sectionImages.map((img) => (
                  <div key={img.id} className="relative">
                    {!loadedImages.has(img.id) && <ImageSkeleton />}
                    <img
                      src={img.url}
                      alt={altEdits[img.id] ?? img.altText}
                      className={`w-full h-40 object-cover rounded-lg border border-gray-100 ${!loadedImages.has(img.id) ? 'hidden' : ''}`}
                      loading="lazy"
                      onLoad={() => onImageLoad(img.id)}
                    />
                    <label className="absolute top-2 left-2 flex items-center gap-1 bg-white/90 rounded px-1.5 py-0.5">
                      <input
                        type="checkbox"
                        checked={selectedIds.has(img.id)}
                        onChange={() => toggleSelect(img.id)}
                        className="rounded w-3.5 h-3.5"
                      />
                    </label>
                    <div className="mt-1">
                      <input
                        value={altEdits[img.id] ?? img.altText}
                        onChange={(e) => setAltEdits((prev) => ({ ...prev, [img.id]: e.target.value }))}
                        className="w-full text-xs text-gray-500 border border-gray-200 rounded px-1 py-0.5 focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                      />
                      <p className="text-xs text-gray-400 mt-0.5">
                        {img.source === 'unsplash' && `Photo by ${img.photographer}`}
                        <span className="ml-1 text-gray-300">({img.position})</span>
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
          );
        })}
      </div>

      {imagesBySection.size === 0 && (
        <p className="text-gray-400 text-center py-8">No images selected. Select images above or go back to adjust keywords.</p>
      )}

      {selectedIds.size < images.length && (
        <p className="text-xs text-gray-400">{images.length - selectedIds.size} image(s) deselected. Click Approve to confirm.</p>
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

      <div className="flex justify-between">
        {onBack && (
          <button
            onClick={onBack}
            disabled={isPending}
            className="px-5 py-2 border border-gray-200 text-sm font-medium rounded-md hover:bg-gray-50 disabled:opacity-50"
          >
            &larr; Back
          </button>
        )}
        <div className="flex gap-3 ml-auto">
          <button
            onClick={handleApprove}
            disabled={isPending || selectedIds.size === 0}
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
    </div>
  );
}
