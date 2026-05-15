export type ArticleStatus =
  | 'draft' | 'outline_generating' | 'outline_ready' | 'outline_approved'
  | 'content_generating' | 'content_ready' | 'content_approved'
  | 'image_keywords_generating' | 'image_keywords_ready' | 'image_searching' | 'images_ready' | 'final_approved'
  | 'publishing' | 'published' | 'failed' | 'cancelled';

export type ArticleMode = 'manual' | 'auto';

export interface ArticleListItem {
  id: string;
  topic: string;
  displayTitle: string;
  status: ArticleStatus;
  mode: ArticleMode;
  wpPostUrl: string | null;
  totalTokens: number | null;
  source: string;
  createdAt: string;
  updatedAt: string;
}

export interface Article {
  id: string;
  topic: string;
  requirements: string | null;
  mode: ArticleMode;
  status: ArticleStatus;
  outline: Outline | null;
  content: ArticleContent | null;
  images: ArticleImage[] | null;
  imagePlan: ImagePlan | null;
  fullHtml: string | null;
  progress: Progress | null;
  wpPostId: number | null;
  wpPostUrl: string | null;
  wpSlug: string | null;
  errorMessage: string | null;
  tokenUsage: Record<string, { input: number; output: number }> | null;
  source: string;
  version: number;
  createdAt: string;
  updatedAt: string;
}

export interface Outline {
  title: string;
  metaDescription: string;
  sections: OutlineSection[];
  seoKeywords: string[];
  category: string;
  tags: string[];
}

export interface OutlineSection {
  heading: string;
  slug: string;
  keyPoints: string[];
  estimatedWords: number;
  includeCodeExample: boolean;
}

export interface ArticleContent {
  sections: ContentSection[];
  fullHtml: string;
  totalWordCount: number;
}

export interface ContentSection {
  heading: string;
  slug: string;
  html: string;
  wordCount: number;
}

export interface ArticleImage {
  id: string;
  url: string;
  fullUrl?: string;
  thumbUrl?: string;
  altText: string;
  sectionSlug: string;
  position: string;
  source: string;
  sourceUrl: string;
  photographer: string;
  type?: 'inline' | 'cover';
}

export interface ImagePlacement {
  sectionSlug: string;
  position: 'before' | 'after';
  keywords: string[];
  suggestedCount: number;
  rationale: string;
  key?: string;
}

export interface CoverImagePlan {
  keywords: string[];
  suggestedCount: number;
  rationale: string;
}

export interface ImagePlan {
  inlineImages: ImagePlacement[];
  coverImage: CoverImagePlan | null;
}

export interface Progress {
  stage: string;
  currentSection: number;
  totalSections: number;
  heading: string;
}

export interface ApiEnvelope<T> {
  success: boolean;
  data: T;
  meta?: PaginationMeta;
  error?: string;
  detail?: string;
}

export interface PaginationMeta {
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface CreateArticleRequest {
  topic: string;
  requirements?: string;
  mode: ArticleMode;
}

export interface PublishRequest {
  title?: string;
  slug?: string;
  status?: string;
  categoryId?: number;
  tagIds?: number[];
  categoryName?: string;
  tagNames?: string[];
  autoCreateTaxonomy?: boolean;
}

export interface UpdateWpRequest {
  title?: string;
  content?: string;
  status?: 'publish' | 'draft';
  slug?: string;
}

export interface WPCategory {
  id: number;
  name: string;
  slug: string;
  count: number;
}

export interface WPUser {
  name: string;
  slug: string;
  avatarUrls: Record<string, string>;
  roles: string[];
  description: string;
}

export interface WPTag {
  id: number;
  name: string;
  slug: string;
  count: number;
}
