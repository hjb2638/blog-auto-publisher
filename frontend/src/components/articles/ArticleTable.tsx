import { useNavigate } from 'react-router-dom';
import type { ArticleListItem } from '../../types';
import StatusBadge from '../common/StatusBadge';

interface ArticleTableProps {
  articles: ArticleListItem[];
  isLoading: boolean;
  currentPage: number;
  totalPages: number;
  statusFilter: string | undefined;
  selectedIds: Set<string>;
  onToggle: (id: string) => void;
  onSelectAll: (ids: string[]) => void;
  isAllSelected: boolean;
  onPageChange: (page: number) => void;
  onStatusFilter: (status: string | undefined) => void;
}

const STATUS_TABS = [
  { label: 'All', value: undefined },
  { label: 'Draft', value: 'draft' },
  { label: 'Generating', value: 'outline_generating' },
  { label: 'Review', value: 'outline_ready' },
  { label: 'Published', value: 'published' },
  { label: 'Failed', value: 'failed' },
] as const;

export default function ArticleTable({
  articles,
  isLoading,
  currentPage,
  totalPages,
  statusFilter,
  selectedIds,
  onToggle,
  onSelectAll,
  isAllSelected,
  onPageChange,
  onStatusFilter,
}: ArticleTableProps) {
  const navigate = useNavigate();
  const allIds = articles.map((a) => a.id);

  return (
    <div>
      <div className="flex gap-2 mb-4 flex-wrap">
        {STATUS_TABS.map(({ label, value }) => (
          <button
            key={label}
            onClick={() => onStatusFilter(value)}
            className={`px-3 py-1.5 text-xs font-medium rounded-full ${
              statusFilter === value
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-100 text-left">
              <th className="px-4 py-3 w-10">
                <input
                  type="checkbox"
                  checked={isAllSelected}
                  onChange={() => onSelectAll(isAllSelected ? [] : allIds)}
                  className="w-4 h-4 rounded border-gray-300"
                />
              </th>
              <th className="px-4 py-3 text-xs font-medium text-gray-400 uppercase">Title</th>
              <th className="px-4 py-3 text-xs font-medium text-gray-400 uppercase">Status</th>
              <th className="px-4 py-3 text-xs font-medium text-gray-400 uppercase">Tokens</th>
              <th className="px-4 py-3 text-xs font-medium text-gray-400 uppercase">Mode</th>
              <th className="px-4 py-3 text-xs font-medium text-gray-400 uppercase">Source</th>
              <th className="px-4 py-3 text-xs font-medium text-gray-400 uppercase">Created</th>
              <th className="px-4 py-3 text-xs font-medium text-gray-400 uppercase">WP</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i} className="border-b border-gray-50">
                  <td className="px-4 py-3"><div className="h-4 w-4 bg-gray-100 rounded animate-pulse" /></td>
                  <td className="px-4 py-3"><div className="h-4 bg-gray-100 rounded w-48 animate-pulse" /></td>
                  <td className="px-4 py-3"><div className="h-4 bg-gray-100 rounded w-16 animate-pulse" /></td>
                  <td className="px-4 py-3"><div className="h-4 bg-gray-100 rounded w-12 animate-pulse" /></td>
                  <td className="px-4 py-3"><div className="h-4 bg-gray-100 rounded w-10 animate-pulse" /></td>
                  <td className="px-4 py-3"><div className="h-4 bg-gray-100 rounded w-12 animate-pulse" /></td>
                  <td className="px-4 py-3"><div className="h-4 bg-gray-100 rounded w-20 animate-pulse" /></td>
                  <td className="px-4 py-3"><div className="h-4 bg-gray-100 rounded w-8 animate-pulse" /></td>
                </tr>
              ))
            ) : articles.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-4 py-12 text-center text-sm text-gray-400">
                  No articles found.
                </td>
              </tr>
            ) : (
              articles.map((article) => (
                <tr
                  key={article.id}
                  className="border-b border-gray-50 hover:bg-gray-50 cursor-pointer transition-colors"
                >
                  <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                    <input
                      type="checkbox"
                      checked={selectedIds.has(article.id)}
                      onChange={() => onToggle(article.id)}
                      className="w-4 h-4 rounded border-gray-300"
                    />
                  </td>
                  <td
                    className="px-4 py-3"
                    onClick={() => navigate(`/articles/${article.id}`)}
                  >
                    <span className="text-sm text-gray-900 line-clamp-1">
                      {article.displayTitle}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={article.status} />
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-xs text-gray-500 font-mono">
                      {article.totalTokens != null ? article.totalTokens.toLocaleString() : '—'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-xs text-gray-500">
                      {article.mode === 'auto' ? 'Auto' : 'Manual'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-xs text-gray-500">
                      {article.source === 'wordpress' ? 'WP' : 'Local'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-xs text-gray-500">
                      {new Date(article.createdAt).toLocaleDateString()}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {article.wpPostUrl ? (
                      <a
                        href={article.wpPostUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="text-blue-600 text-xs hover:underline"
                      >
                        View
                      </a>
                    ) : (
                      <span className="text-xs text-gray-300">—</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex justify-center items-center gap-2 mt-4">
          <button
            onClick={() => onPageChange(currentPage - 1)}
            disabled={currentPage <= 1}
            className="px-3 py-1.5 text-xs border border-gray-200 rounded-md disabled:opacity-30 hover:bg-gray-50"
          >
            Prev
          </button>
          {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
            <button
              key={p}
              onClick={() => onPageChange(p)}
              className={`px-3 py-1.5 text-xs rounded-md ${
                p === currentPage
                  ? 'bg-blue-600 text-white'
                  : 'border border-gray-200 hover:bg-gray-50'
              }`}
            >
              {p}
            </button>
          ))}
          <button
            onClick={() => onPageChange(currentPage + 1)}
            disabled={currentPage >= totalPages}
            className="px-3 py-1.5 text-xs border border-gray-200 rounded-md disabled:opacity-30 hover:bg-gray-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
