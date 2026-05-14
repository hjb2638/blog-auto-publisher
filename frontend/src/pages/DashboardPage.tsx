import { useApiStatus } from '../hooks/useApiStatus';
import { useArticlesPaginated } from '../hooks/useArticlesPaginated';

function StatCard({ label, value, subtitle }: { label: string; value: string | number; subtitle?: string }) {
  return (
    <div className="bg-white border border-gray-200/80 rounded-2xl shadow-sm p-6
      hover:shadow-md hover:border-gray-300 transition-all duration-200">
      <div className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-3">{label}</div>
      <div className="text-3xl font-bold text-gray-900 tracking-tight font-mono">{value}</div>
      {subtitle && <div className="text-sm text-gray-500 mt-1">{subtitle}</div>}
    </div>
  );
}

function ApiQuotaCard({ name, remaining, limit, tier }: {
  name: string;
  remaining: number | null;
  limit: number;
  tier: string;
}) {
  const percentage = remaining != null ? (remaining / limit) * 100 : 0;
  const color = percentage > 40 ? 'bg-gray-900' : percentage > 20 ? 'bg-amber-500' : 'bg-red-500';

  return (
    <div className="bg-white border border-gray-200/80 rounded-2xl shadow-sm p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold text-gray-900">{name}</h3>
          <p className="text-xs text-gray-500 mt-0.5">{tier} &middot; {limit} requests/hour</p>
        </div>
        <span className="text-2xl font-bold text-gray-900 font-mono">
          {remaining ?? '—'}
          <span className="text-sm text-gray-400 font-normal"> / {limit}</span>
        </span>
      </div>
      <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ease-out ${color}`}
          style={{ width: `${remaining != null ? percentage : 0}%` }}
        />
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const { data: apiStatusData } = useApiStatus();
  const { data: articlesData } = useArticlesPaginated(1, 1);
  const apiStatus = apiStatusData?.data;

  const totalArticles = articlesData?.meta?.total ?? 0;

  return (
    <div className="max-w-5xl mx-auto animate-fade-in-up">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Dashboard</h1>
        <p className="text-gray-500 text-sm mt-1">Monitor your blog system status and API usage.</p>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-8">
        <StatCard label="Total Articles" value={totalArticles} />
        <StatCard
          label="LLM Model"
          value={apiStatus?.llm?.model ?? '—'}
          subtitle={apiStatus?.llm?.baseUrl ?? ''}
        />
        <StatCard
          label="Unsplash"
          value={apiStatus?.unsplash?.remaining ?? '—'}
          subtitle={`of ${apiStatus?.unsplash?.limit ?? 50} remaining`}
        />
      </div>

      <ApiQuotaCard
        name="Unsplash API"
        remaining={apiStatus?.unsplash?.remaining ?? null}
        limit={apiStatus?.unsplash?.limit ?? 50}
        tier="Free Tier"
      />

      <div className="mt-8 bg-white border border-gray-200/80 rounded-2xl shadow-sm p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-1">About</h2>
        <p className="text-sm text-gray-500">
          Unsplash free tier allows 50 requests per hour. The quota resets at the top of each hour.
          Track your remaining requests to avoid hitting the limit during image search.
        </p>
      </div>
    </div>
  );
}
