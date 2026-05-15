import { useQuery } from '@tanstack/react-query';
import { fetchArticles } from '../api/articles';

export function useArticlesPaginated(page: number, limit: number, status?: string, source?: string, sortBy?: string, sortOrder?: string, search?: string) {
  return useQuery({
    queryKey: ['articles', { page, limit, status, source, sortBy, sortOrder, search }],
    queryFn: () => fetchArticles({ page, limit, status, source, sort_by: sortBy, sort_order: sortOrder, search }),
    staleTime: 30_000,
  });
}
