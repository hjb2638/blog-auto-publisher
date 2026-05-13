import { useState, useEffect } from 'react';
import type { Article, WPCategory, WPTag, PublishRequest } from '../../types';
import { fetchWPCategories, fetchWPTags } from '../../api/articles';
import ContentRenderer from './ContentRenderer';

interface FinalReviewProps {
  article: Article;
  isPending: boolean;
  onPublish: (body: PublishRequest) => void;
}

export default function FinalReview({ article, isPending, onPublish }: FinalReviewProps) {
  const [categories, setCategories] = useState<WPCategory[]>([]);
  const [tags, setTags] = useState<WPTag[]>([]);
  const [selectedCategoryId, setSelectedCategoryId] = useState<number | null>(null);
  const [selectedTagIds, setSelectedTagIds] = useState<number[]>([]);
  const [title, setTitle] = useState(article.outline?.title || article.topic);
  const [slug, setSlug] = useState('');
  const [autoCreate, setAutoCreate] = useState(true);

  useEffect(() => {
    fetchWPCategories().then((res) => {
      if (res.success) setCategories(res.data);
    });
    fetchWPTags().then((res) => {
      if (res.success) setTags(res.data);
    });
  }, []);

  const toggleTag = (tagId: number) => {
    setSelectedTagIds((prev) =>
      prev.includes(tagId) ? prev.filter((id) => id !== tagId) : [...prev, tagId]
    );
  };

  const handlePublish = () => {
    onPublish({
      title: title || undefined,
      slug: slug || undefined,
      categoryId: selectedCategoryId ?? undefined,
      tagIds: selectedTagIds.length > 0 ? selectedTagIds : undefined,
      autoCreateTaxonomy: autoCreate,
    });
  };

  const outlineCategory = article.outline?.category;
  const outlineTags = article.outline?.tags || [];

  return (
    <div className="space-y-6">
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-3">Final Review</h2>
        {article.content?.fullHtml && <ContentRenderer html={article.content.fullHtml} />}
        {article.images && article.images.length > 0 && (
          <div className="mt-4 grid grid-cols-3 gap-3">
            {article.images.map((img) => (
              <div key={img.id}>
                <img
                  src={img.url}
                  alt={img.altText}
                  className="w-full h-32 object-cover rounded"
                  loading="lazy"
                />
                <p className="text-xs text-gray-400 mt-1 truncate">{img.altText}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-6 space-y-4">
        <h3 className="text-sm font-semibold text-gray-700">Publish Settings</h3>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Title</label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-md text-sm focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Slug</label>
            <input
              value={slug}
              onChange={(e) => setSlug(e.target.value)}
              placeholder="Auto-generated if empty"
              className="w-full px-3 py-2 border border-gray-200 rounded-md text-sm focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">
              Category
              {outlineCategory && !selectedCategoryId && (
                <span className="text-blue-500 ml-1">(auto: {outlineCategory})</span>
              )}
              {selectedCategoryId && (
                <span className="text-green-500 ml-1">(manual)</span>
              )}
            </label>
            <select
              value={selectedCategoryId ?? ''}
              onChange={(e) =>
                setSelectedCategoryId(e.target.value ? Number(e.target.value) : null)
              }
              className="w-full px-3 py-2 border border-gray-200 rounded-md text-sm focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">
                {outlineCategory ? `Auto-match: ${outlineCategory}` : 'None'}
              </option>
              {categories.map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {cat.name} ({cat.count})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">
              Tags
              {selectedTagIds.length === 0 && outlineTags.length > 0 && (
                <span className="text-blue-500 ml-1">(auto: {outlineTags.join(', ')})</span>
              )}
              {selectedTagIds.length > 0 && (
                <span className="text-green-500 ml-1">(manual: {selectedTagIds.length} selected)</span>
              )}
            </label>
            <div className="max-h-40 overflow-y-auto border border-gray-200 rounded-md p-2 space-y-1">
              {tags.map((tag) => (
                <label key={tag.id} className="flex items-center gap-1.5 text-xs cursor-pointer hover:bg-gray-50 px-1 rounded">
                  <input
                    type="checkbox"
                    checked={selectedTagIds.includes(tag.id)}
                    onChange={() => toggleTag(tag.id)}
                    className="rounded"
                  />
                  <span>{tag.name}</span>
                  <span className="text-gray-400">({tag.count})</span>
                </label>
              ))}
              {tags.length === 0 && (
                <p className="text-xs text-gray-400 p-2">Loading tags...</p>
              )}
            </div>
          </div>
        </div>

        <label className="flex items-center gap-1.5 text-xs text-gray-500">
          <input
            type="checkbox"
            checked={autoCreate}
            onChange={(e) => setAutoCreate(e.target.checked)}
            className="rounded"
          />
          Auto-create missing categories/tags on WordPress
        </label>
      </div>

      <div className="flex justify-end">
        <button
          onClick={handlePublish}
          disabled={isPending}
          className="px-6 py-2 bg-green-600 text-white text-sm font-medium rounded-md hover:bg-green-700 disabled:opacity-50"
        >
          {isPending ? 'Publishing...' : 'Publish to WordPress'}
        </button>
      </div>
    </div>
  );
}
