import type { ArticleStatus } from '../../types';

const STATUS_STYLES: Record<ArticleStatus, string> = {
  draft: 'bg-gray-100 text-gray-700',
  outline_generating: 'bg-blue-100 text-blue-700',
  outline_ready: 'bg-indigo-100 text-indigo-700',
  outline_approved: 'bg-indigo-200 text-indigo-800',
  content_generating: 'bg-sky-100 text-sky-700',
  content_ready: 'bg-cyan-100 text-cyan-700',
  content_approved: 'bg-cyan-200 text-cyan-800',
  image_searching: 'bg-teal-100 text-teal-700',
  images_ready: 'bg-green-100 text-green-700',
  final_approved: 'bg-green-200 text-green-800',
  publishing: 'bg-emerald-100 text-emerald-700',
  published: 'bg-green-500 text-white',
  failed: 'bg-red-100 text-red-700',
  cancelled: 'bg-gray-200 text-gray-500',
};

const STATUS_LABELS: Record<ArticleStatus, string> = {
  draft: 'Draft',
  outline_generating: 'Generating Outline',
  outline_ready: 'Outline Ready',
  outline_approved: 'Outline Approved',
  content_generating: 'Generating Content',
  content_ready: 'Content Ready',
  content_approved: 'Content Approved',
  image_searching: 'Searching Images',
  images_ready: 'Images Ready',
  final_approved: 'Ready to Publish',
  publishing: 'Publishing',
  published: 'Published',
  failed: 'Failed',
  cancelled: 'Cancelled',
};

interface StatusBadgeProps {
  status: ArticleStatus;
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_STYLES[status] || 'bg-gray-100 text-gray-700'}`}>
      {STATUS_LABELS[status] || status}
    </span>
  );
}
