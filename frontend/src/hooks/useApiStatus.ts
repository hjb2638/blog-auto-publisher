import { useQuery } from '@tanstack/react-query';
import apiClient from '../api/client';
import type { ApiEnvelope } from '../types';

interface ApiStatusData {
  unsplash: { remaining: number | null; limit: number };
  llm: { baseUrl: string; model: string };
}

export function useApiStatus() {
  return useQuery({
    queryKey: ['api-status'],
    queryFn: async () => {
      const { data } = await apiClient.get<ApiEnvelope<ApiStatusData>>('/api-status');
      return data;
    },
    refetchInterval: 60_000,
  });
}
