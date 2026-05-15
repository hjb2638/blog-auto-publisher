import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { fetchArticles } from '../../api/articles';
import StatusBadge from '../common/StatusBadge';
import type { ArticleListItem } from '../../types';

function NavItem({ href, label, active }: { href: string; label: string; active: boolean }) {
  const navigate = useNavigate();
  return (
    <button
      onClick={() => navigate(href)}
      className={`w-full text-left flex items-center gap-2.5 px-2 py-1.5 rounded-lg text-sm font-medium
        transition-colors duration-100
        ${active
          ? 'bg-white text-gray-900 shadow-sm border border-gray-200/80'
          : 'text-gray-500 hover:text-gray-900 hover:bg-white/60'
        }`}
    >
      {label}
    </button>
  );
}

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
    <aside className="w-60 border-r border-gray-200/80 bg-gray-50/50 min-h-screen flex flex-col flex-shrink-0">
      <nav className="p-4 space-y-6 flex-1 overflow-y-auto">
        <section>
          <h3 className="px-2 mb-1 text-xs font-medium text-gray-400 uppercase tracking-wider">
            Create
          </h3>
          <NavItem href="/new" label="New Article" active={location.pathname === '/new'} />
        </section>
        <section>
          <h3 className="px-2 mb-1 text-xs font-medium text-gray-400 uppercase tracking-wider">
            Manage
          </h3>
          <NavItem href="/articles" label="All Articles" active={location.pathname === '/articles'} />
        </section>
        <section>
          <h3 className="px-2 mb-1 text-xs font-medium text-gray-400 uppercase tracking-wider">
            Monitor
          </h3>
          <NavItem href="/dashboard" label="Dashboard" active={location.pathname === '/dashboard'} />
        </section>

        <section>
          <h3 className="px-2 mb-1 text-xs font-medium text-gray-400 uppercase tracking-wider">
            Recent
          </h3>
          {isLoading ? (
            <div className="p-2 text-sm text-gray-400">Loading...</div>
          ) : articles.length === 0 ? (
            <div className="p-2 text-sm text-gray-400">No articles</div>
          ) : (
            <ul className="space-y-0.5">
              {articles.slice(0, 10).map((article: ArticleListItem) => (
                <li key={article.id}>
                  <button
                    onClick={() => navigate(`/articles/${article.id}`)}
                    className={`w-full text-left px-2 py-1.5 rounded-lg text-sm hover:bg-white/60 transition-colors ${
                      id === article.id ? 'bg-white shadow-sm border border-gray-200/80' : ''
                    }`}
                  >
                    <div className="text-sm font-medium text-gray-900 truncate">
                      {article.displayTitle}
                    </div>
                    <div className="mt-0.5 flex items-center gap-1.5">
                      <StatusBadge status={article.status} />
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
      </nav>
    </aside>
  );
}
