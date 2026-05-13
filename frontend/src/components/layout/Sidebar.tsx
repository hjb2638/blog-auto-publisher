import { useQuery } from '@tanstack/react-query';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { fetchArticles } from '../../api/articles';
import StatusBadge from '../common/StatusBadge';
import type { ArticleListItem } from '../../types';

export default function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();
  const { id } = useParams<{ id: string }>();

  const { data, isLoading } = useQuery({
    queryKey: ['articles'],
    queryFn: () => fetchArticles({ limit: 50 }),
    refetchInterval: 10_000,
  });

  const articles = data?.data || [];

  return (
    <aside className="w-[280px] bg-white border-r border-gray-200 flex flex-col flex-shrink-0">
      <div className="p-4 border-b border-gray-100">
        <button
          onClick={() => navigate('/new')}
          className="w-full py-2 px-4 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700"
        >
          + New Article
        </button>
      </div>
      <nav className="flex-1 overflow-y-auto">
        <div className="px-4 py-2">
          <button
            onClick={() => navigate('/articles')}
            className={`w-full text-left px-3 py-2 text-sm rounded-md ${
              location.pathname === '/articles' ? 'bg-blue-50 text-blue-700 font-medium' : 'text-gray-600 hover:bg-gray-50'
            }`}
          >
            All Articles
          </button>
        </div>
        <div className="px-4 py-1">
          <span className="text-xs font-medium text-gray-400 uppercase tracking-wide">Recent</span>
        </div>
        {isLoading ? (
          <div className="p-4 text-sm text-gray-400">Loading...</div>
        ) : articles.length === 0 ? (
          <div className="p-4 text-sm text-gray-400">No articles yet</div>
        ) : (
          <ul>
            {articles.slice(0, 10).map((article: ArticleListItem) => (
              <li key={article.id}>
                <button
                  onClick={() => navigate(`/articles/${article.id}`)}
                  className={`w-full text-left px-4 py-3 hover:bg-gray-50 border-b border-gray-50 ${
                    id === article.id ? 'bg-blue-50 border-l-2 border-l-blue-500' : ''
                  }`}
                >
                  <div className="text-sm font-medium text-gray-900 truncate">
                    {article.topic.length > 60 ? article.topic.slice(0, 60) + '...' : article.topic}
                  </div>
                  <div className="mt-1 flex items-center gap-2">
                    <StatusBadge status={article.status} />
                    <span className="text-xs text-gray-400">
                      {new Date(article.updatedAt).toLocaleDateString()}
                    </span>
                  </div>
                </button>
              </li>
            ))}
          </ul>
        )}
      </nav>
    </aside>
  );
}
