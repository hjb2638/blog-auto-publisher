import { useQuery } from '@tanstack/react-query';
import { fetchArticles } from '../api/articles';

export function useArticles(params?: { page?: number; limit?: number; status?: string }) {
  return useQuery({
    queryKey: ['articles', params],
    queryFn: () => fetchArticles(params),
    staleTime: 30_000,
  });
}
