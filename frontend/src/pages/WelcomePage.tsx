import { Link, useNavigate } from 'react-router-dom';
import { useArticlesPaginated } from '../hooks/useArticlesPaginated';

export default function WelcomePage() {
  const navigate = useNavigate();
  const { data } = useArticlesPaginated(1, 5);

  const articles = data?.data || [];
  const total = data?.meta?.total ?? 0;

  return (
    <div className="-m-8">
      <div className="bg-gradient-to-br from-gray-50 via-white to-gray-100 py-20 px-8">
        <div className="max-w-2xl mx-auto text-center animate-fade-in-up">
          <h1 className="text-4xl font-bold text-gray-900 tracking-tight mb-4">
            Blog Auto-Publishing
          </h1>
          <p className="text-lg text-gray-500 mb-8 leading-relaxed">
            AI-powered content generation, image search, and one-click WordPress publishing.
          </p>
          <Link
            to="/new"
            className="inline-flex items-center gap-2 px-6 py-3 bg-black text-white font-medium rounded-xl hover:bg-gray-800 transition-colors text-base"
          >
            Start a New Article &rarr;
          </Link>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-8 -mt-10 animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-white border border-gray-200/80 rounded-2xl shadow-sm p-6 hover:shadow-md hover:-translate-y-0.5 transition-all duration-200">
            <div className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-3">Articles</div>
            <div className="text-3xl font-bold text-gray-900 tracking-tight font-mono">{total}</div>
          </div>
          <button
            onClick={() => navigate('/new')}
            className="bg-white border border-gray-200/80 rounded-2xl shadow-sm p-6 hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 cursor-pointer text-left"
          >
            <div className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-3">New Article</div>
            <div className="text-3xl font-bold text-gray-900 tracking-tight">+</div>
          </button>
          <button
            onClick={() => navigate('/dashboard')}
            className="bg-white border border-gray-200/80 rounded-2xl shadow-sm p-6 hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 cursor-pointer text-left"
          >
            <div className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-3">Dashboard</div>
            <div className="text-3xl font-bold text-gray-900 tracking-tight">&rarr;</div>
          </button>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-8 py-12 animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Articles</h2>
        {articles.length > 0 ? (
          <div className="space-y-2">
            {articles.map((article) => (
              <button
                key={article.id}
                onClick={() => navigate(`/articles/${article.id}`)}
                className="w-full text-left bg-white border border-gray-200/80 rounded-xl p-4 hover:shadow-sm hover:border-gray-300 transition-all duration-200"
              >
                <div className="text-sm font-medium text-gray-900 truncate">{article.topic}</div>
                <div className="text-xs text-gray-400 mt-1">
                  {new Date(article.updatedAt).toLocaleDateString()}
                </div>
              </button>
            ))}
            {total > 5 && (
              <Link
                to="/articles"
                className="block text-center text-sm text-gray-500 hover:text-gray-900 py-2"
              >
                View all {total} articles &rarr;
              </Link>
            )}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-16 px-4 border-2 border-dashed border-gray-300 rounded-2xl">
            <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center mb-4">
              <span className="text-gray-400 text-xl">+</span>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-1">No articles yet</h3>
            <p className="text-sm text-gray-500 mb-6 text-center max-w-sm">
              Create your first AI-generated blog post in minutes.
            </p>
            <Link
              to="/new"
              className="px-4 py-2 bg-black text-white text-sm font-medium rounded-lg hover:bg-gray-800 transition-colors"
            >
              Create Article
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
