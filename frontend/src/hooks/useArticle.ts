import { useQuery, useQueryClient } from '@tanstack/react-query';
import { fetchArticle } from '../api/articles';
import type { Article } from '../types';

function isGenerating(status: string): boolean {
  return ['outline_generating', 'content_generating', 'content_approved',
          'image_keywords_generating', 'image_keywords_ready', 'image_searching',
          'publishing'].includes(status);
}

export function useArticle(id: string | undefined) {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ['article', id],
    queryFn: () => fetchArticle(id!),
    enabled: !!id,
    refetchInterval: (query) => {
      const data = query.state.data?.data as Article | undefined;
      if (data && isGenerating(data.status)) return 3_000;
      return false;
    },
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['article', id] });
    queryClient.invalidateQueries({ queryKey: ['articles'] });
  };

  return { ...query, invalidate };
}
