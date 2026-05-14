import { useQuery } from '@tanstack/react-query';
import { fetchArticles } from '../api/articles';

export function useArticlesPaginated(page: number, limit: number, status?: string, source?: string) {
  return useQuery({
    queryKey: ['articles', { page, limit, status, source }],
    queryFn: () => fetchArticles({ page, limit, status, source }),
    staleTime: 30_000,
  });
}
