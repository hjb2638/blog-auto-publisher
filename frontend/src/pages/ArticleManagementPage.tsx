import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useArticlesPaginated } from '../hooks/useArticlesPaginated';
import ArticleTable from '../components/articles/ArticleTable';

export default function ArticleManagementPage() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState<string | undefined>();
  const limit = 20;

  const { data, isLoading } = useArticlesPaginated(page, limit, status);

  const articles = data?.data || [];
  const meta = data?.meta;
  const totalPages = meta?.pages || 1;

  return (
    <div className="max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold text-gray-900">Article Management</h1>
        <button
          onClick={() => navigate('/new')}
          className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700"
        >
          + New Article
        </button>
      </div>

      <ArticleTable
        articles={articles}
        isLoading={isLoading}
        currentPage={page}
        totalPages={totalPages}
        statusFilter={status}
        onPageChange={setPage}
        onStatusFilter={(s) => { setStatus(s); setPage(1); }}
      />
    </div>
  );
}
