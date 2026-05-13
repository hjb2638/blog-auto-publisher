import { useQuery } from '@tanstack/react-query';
import { fetchArticles } from '../api/articles';

export function useArticlesPaginated(page: number, limit: number, status?: string) {
  return useQuery({
    queryKey: ['articles', { page, limit, status }],
    queryFn: () => fetchArticles({ page, limit, status }),
    staleTime: 30_000,
  });
}
