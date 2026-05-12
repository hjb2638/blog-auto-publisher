import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  createArticle, approveOutline, approveContent, approveFinal,
  publishArticle, regenerateArticle, deleteArticle,
} from '../api/articles';
import type { CreateArticleRequest, PublishRequest } from '../types';
import { useNavigate } from 'react-router-dom';

export function useCreateArticle() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  return useMutation({
    mutationFn: (body: CreateArticleRequest) => createArticle(body),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['articles'] });
      if (data.data?.id) navigate(`/articles/${data.data.id}`);
    },
  });
}

export function useApproveOutline(id: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body?: unknown) => approveOutline(id!, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['article', id] });
      queryClient.invalidateQueries({ queryKey: ['articles'] });
    },
  });
}

export function useApproveContent(id: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body?: unknown) => approveContent(id!, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['article', id] });
      queryClient.invalidateQueries({ queryKey: ['articles'] });
    },
  });
}

export function useApproveFinal(id: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body?: unknown) => approveFinal(id!, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['article', id] });
      queryClient.invalidateQueries({ queryKey: ['articles'] });
    },
  });
}

export function usePublishArticle(id: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body?: PublishRequest) => publishArticle(id!, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['article', id] });
      queryClient.invalidateQueries({ queryKey: ['articles'] });
    },
  });
}

export function useRegenerateArticle(id: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (stage: string) => regenerateArticle(id!, stage),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['article', id] });
      queryClient.invalidateQueries({ queryKey: ['articles'] });
    },
  });
}

export function useDeleteArticle(id: string | undefined) {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  return useMutation({
    mutationFn: () => deleteArticle(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['articles'] });
      navigate('/');
    },
  });
}
