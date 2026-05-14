import { useQuery } from '@tanstack/react-query';
import apiClient from '../api/client';
import type { ApiEnvelope, WPUser } from '../types';

async function fetchCurrentUser() {
  const { data } = await apiClient.get<ApiEnvelope<WPUser>>('/wordpress/me');
  return data.data;
}

export function useCurrentUser() {
  return useQuery({
    queryKey: ['currentUser'],
    queryFn: fetchCurrentUser,
    staleTime: Infinity,
    retry: 1,
  });
}
