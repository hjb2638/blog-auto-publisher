from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = {"alias_generator": to_camel, "populate_by_name": True}


class ArticleMode(str, Enum):
    manual = "manual"
    auto = "auto"


class ArticleStatus(str, Enum):
    draft = "draft"
    outline_generating = "outline_generating"
    outline_ready = "outline_ready"
    outline_approved = "outline_approved"
    content_generating = "content_generating"
    content_ready = "content_ready"
    content_approved = "content_approved"
    image_keywords_ready = "image_keywords_ready"
    image_searching = "image_searching"
    images_ready = "images_ready"
    final_approved = "final_approved"
    publishing = "publishing"
    published = "published"
    failed = "failed"
    cancelled = "cancelled"


class OutlineSectionSchema(CamelModel):
    heading: str
    slug: str
    key_points: list[str]
    estimated_words: int = 300
    include_code_example: bool = False


class OutlineSchema(CamelModel):
    title: str
    meta_description: str = ""
    sections: list[OutlineSectionSchema]
    seo_keywords: list[str] = []
    category: str = ""
    tags: list[str] = []


class ContentSectionSchema(CamelModel):
    heading: str
    slug: str
    html: str
    word_count: int


class ArticleContentSchema(CamelModel):
    sections: list[ContentSectionSchema]
    full_html: str = ""
    total_word_count: int = 0


class ArticleImageSchema(CamelModel):
    id: str
    url: str
    alt_text: str
    section_slug: str
    position: str = "before"
    source: str = ""
    source_url: str = ""
    photographer: str = ""


class ProgressSchema(CamelModel):
    stage: str
    current_section: int = 0
    total_sections: int = 0
    heading: str = ""


class CreateArticleRequest(CamelModel):
    topic: str = Field(..., min_length=10, max_length=500)
    requirements: str | None = Field(None, max_length=2000)
    mode: ArticleMode = ArticleMode.manual


class ArticleListItem(CamelModel):
    id: UUID
    topic: str
    status: ArticleStatus
    mode: ArticleMode
    wp_post_url: str | None = None
    created_at: datetime
    updated_at: datetime


class ArticleDetail(CamelModel):
    id: UUID
    topic: str
    requirements: str | None
    mode: ArticleMode
    status: ArticleStatus
    outline: OutlineSchema | None = None
    content: ArticleContentSchema | None = None
    images: list[ArticleImageSchema] | None = None
    image_plan: "ImagePlanSchema | None" = None
    full_html: str | None = None
    progress: ProgressSchema | None = None
    wp_post_id: int | None = None
    wp_post_url: str | None = None
    wp_slug: str | None = None
    error_message: str | None = None
    version: int
    created_at: datetime
    updated_at: datetime


class ApproveOutlineRequest(CamelModel):
    title: str | None = None
    sections: list[OutlineSectionSchema] | None = None
    revision_prompt: str | None = None
    regenerate: bool = False


class ApproveContentRequest(CamelModel):
    section_edits: dict[str, str] | None = None
    revision_prompt: str | None = None
    regenerate_sections: list[str] | None = None


class ImagePlacementSchema(CamelModel):
    section_slug: str
    position: str = "before"  # "before" | "after"
    keywords: list[str] = []
    suggested_count: int = 1
    rationale: str = ""


class CoverImageSchema(CamelModel):
    keywords: list[str] = []
    suggested_count: int = 1
    rationale: str = ""


class ImagePlanSchema(CamelModel):
    inline_images: list[ImagePlacementSchema] = []
    cover_image: CoverImageSchema | None = None


class ApproveImageKeywordsRequest(CamelModel):
    plan: ImagePlanSchema | None = None
    revision_prompt: str | None = None


class ApproveFinalRequest(CamelModel):
    remove_images: list[str] | None = None
    revision_prompt: str | None = None
    replace_image: dict | None = None
    cover_image_id: str | None = None


class PublishRequest(CamelModel):
    title: str | None = None
    slug: str | None = None
    category_id: int | None = None
    tag_ids: list[int] | None = None
    category_name: str | None = None
    tag_names: list[str] | None = None
    auto_create_taxonomy: bool = False
    status: str = "publish"


class WPCategory(CamelModel):
    id: int
    name: str
    slug: str
    count: int = 0


class WPTag(CamelModel):
    id: int
    name: str
    slug: str
    count: int = 0


class RegenerateRequest(CamelModel):
    stage: str
    section_slugs: list[str] | None = None
    updated_requirements: str | None = None


class HealthResponse(CamelModel):
    status: str
    database: str
    llm_service: str
    wordpress: str
