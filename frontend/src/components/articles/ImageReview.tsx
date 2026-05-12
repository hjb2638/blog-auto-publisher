import type { ArticleImage } from '../../types';

interface ImageReviewProps {
  images: ArticleImage[];
  isAuto: boolean;
  onApprove: () => void;
  onRemoveImage: (imageId: string) => void;
  isPending: boolean;
}

export default function ImageReview({ images, isAuto, onApprove, onRemoveImage, isPending }: ImageReviewProps) {
  const imagesBySection = new Map<string, ArticleImage[]>();
  for (const img of images) {
    const list = imagesBySection.get(img.sectionSlug) || [];
    list.push(img);
    imagesBySection.set(img.sectionSlug, list);
  }

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-gray-900">Image Review ({images.length} images)</h2>

      {Array.from(imagesBySection.entries()).map(([slug, sectionImages]) => (
        <div key={slug} className="bg-white border border-gray-200 rounded-lg p-4">
          <h3 className="text-sm font-medium text-gray-700 mb-3 capitalize">{slug.replace(/-/g, ' ')}</h3>
          <div className="grid grid-cols-2 gap-3">
            {sectionImages.map((img: ArticleImage) => (
              <div key={img.id} className="relative group">
                <img
                  src={img.url}
                  alt={img.altText}
                  className="w-full h-40 object-cover rounded-lg border border-gray-100"
                  loading="lazy"
                />
                <div className="mt-1">
                  <p className="text-xs text-gray-500 truncate">{img.altText}</p>
                  <p className="text-xs text-gray-400">
                    {img.source === 'unsplash' && `Photo by ${img.photographer}`}
                  </p>
                </div>
                <button
                  onClick={() => onRemoveImage(img.id)}
                  className="absolute top-2 right-2 w-6 h-6 bg-red-600 text-white text-xs rounded-full opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center"
                >
                  x
                </button>
              </div>
            ))}
          </div>
        </div>
      ))}

      {!isAuto && (
        <div className="flex justify-end">
          <button
            onClick={onApprove}
            disabled={isPending}
            className="px-6 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {isPending ? 'Approving...' : 'Approve Final & Publish'}
          </button>
        </div>
      )}
    </div>
  );
}
