import apiClient from './client';
import type { ApiEnvelope, Article, ArticleListItem, CreateArticleRequest, PublishRequest, UpdateWpRequest, WPCategory, WPTag, ImagePlan } from '../types';

export async function fetchArticles(params?: { page?: number; limit?: number; status?: string; source?: string; sort_by?: string; sort_order?: string; search?: string }) {
  const { data } = await apiClient.get<ApiEnvelope<ArticleListItem[]>>('/articles', { params });
  return data;
}

export async function fetchArticle(id: string) {
  const { data } = await apiClient.get<ApiEnvelope<Article>>(`/articles/${id}`);
  return data;
}

export async function fetchArticleStatus(id: string) {
  const { data } = await apiClient.get<ApiEnvelope<{ id: string; status: string; progress: unknown; errorMessage: string | null }>>(`/articles/${id}/status`);
  return data;
}

export async function createArticle(body: CreateArticleRequest) {
  const { data } = await apiClient.post<ApiEnvelope<Article>>('/articles', body);
  return data;
}

export async function approveOutline(id: string, body?: unknown) {
  const { data } = await apiClient.post<ApiEnvelope<Article>>(`/articles/${id}/approve-outline`, body || {});
  return data;
}

export async function approveContent(id: string, body?: unknown) {
  const { data } = await apiClient.post<ApiEnvelope<Article>>(`/articles/${id}/approve-content`, body || {});
  return data;
}

export async function approveImageKeywords(id: string, body?: { plan?: ImagePlan; revisionPrompt?: string }) {
  const { data } = await apiClient.post<ApiEnvelope<Article>>(`/articles/${id}/approve-image-keywords`, body || {});
  return data;
}

export async function approveFinal(id: string, body?: { selectedImages?: string[]; removeImages?: string[]; revisionPrompt?: string; coverImageId?: string }) {
  const { data } = await apiClient.post<ApiEnvelope<Article>>(`/articles/${id}/approve-final`, body || {});
  return data;
}

export async function stepBack(id: string) {
  const { data } = await apiClient.post<ApiEnvelope<Article>>(`/articles/${id}/step-back`);
  return data;
}

export async function publishArticle(id: string, body?: PublishRequest) {
  const { data } = await apiClient.post<ApiEnvelope<Article>>(`/articles/${id}/publish`, body || {});
  return data;
}

export async function regenerateArticle(id: string, stage: string) {
  const { data } = await apiClient.post<ApiEnvelope<Article>>(`/articles/${id}/regenerate`, { stage });
  return data;
}

export async function deleteArticle(id: string, deleteWp?: boolean) {
  const params = deleteWp ? { delete_wp: true } : undefined;
  const { data } = await apiClient.delete(`/articles/${id}`, { params });
  return data;
}

export async function updateWpArticle(id: string, body: UpdateWpRequest) {
  const { data } = await apiClient.post<ApiEnvelope<Article>>(`/articles/${id}/update-wp`, body);
  return data;
}

export async function fetchWPCategories() {
  const { data } = await apiClient.get<ApiEnvelope<WPCategory[]>>('/wordpress/categories');
  return data;
}

export async function fetchWPTags() {
  const { data } = await apiClient.get<ApiEnvelope<WPTag[]>>('/wordpress/tags');
  return data;
}

export async function fetchWPPosts(params?: { page?: number; perPage?: number; status?: string }) {
  const { data } = await apiClient.get<ApiEnvelope<unknown[]>>('/wordpress/posts', { params });
  return data;
}

export async function syncWPPosts() {
  const { data } = await apiClient.post<ApiEnvelope<{ totalFetched: number; imported: number; skipped: number; failed: number }>>('/articles/sync-wp');
  return data;
}

export async function importWPPosts() {
  const { data } = await apiClient.post<ApiEnvelope<{ imported: number; skipped: number }>>('/articles/import-wp-posts');
  return data;
}

export async function updateWPPost(postId: number, body: Record<string, unknown>) {
  const { data } = await apiClient.put<ApiEnvelope<unknown>>(`/wordpress/posts/${postId}`, body);
  return data;
}

export async function batchAction(body: { ids: string[]; action: string; deleteWp?: boolean }) {
  const { data } = await apiClient.post<ApiEnvelope<{ processed: number; failed: { id: string; reason: string }[] }>>('/articles/batch', body);
  return data;
}

export async function deleteWPPost(postId: number) {
  const { data } = await apiClient.delete<ApiEnvelope<unknown>>(`/wordpress/posts/${postId}`);
  return data;
}
