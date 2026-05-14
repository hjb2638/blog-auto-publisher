import { Link, useLocation } from 'react-router-dom';
import { useCurrentUser } from '../../hooks/useCurrentUser';

function pageTitle(pathname: string): string {
  if (pathname === '/') return '';
  if (pathname === '/new') return 'New Article';
  if (pathname === '/articles') return 'All Articles';
  if (pathname.startsWith('/articles/')) return 'Article';
  if (pathname === '/dashboard') return 'Dashboard';
  return '';
}

export default function Header() {
  const location = useLocation();
  const title = pageTitle(location.pathname);
  const { data: user } = useCurrentUser();

  return (
    <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-200/80">
      <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link to="/" className="font-bold text-gray-900 tracking-tight">
            Blog Manager
          </Link>
          {title && (
            <>
              <span className="text-gray-300">/</span>
              <span className="text-sm text-gray-500">{title}</span>
            </>
          )}
        </div>
        <div className="flex items-center gap-3">
          {user && (
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">{user.name}</span>
              {user.avatarUrls?.['24'] && (
                <img
                  src={user.avatarUrls['24']}
                  alt={user.name}
                  className="w-6 h-6 rounded-full"
                />
              )}
            </div>
          )}
          <Link
            to="/new"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-black text-white text-sm font-medium rounded-lg hover:bg-gray-800 transition-colors"
          >
            + New Article
          </Link>
        </div>
      </div>
    </header>
  );
}
