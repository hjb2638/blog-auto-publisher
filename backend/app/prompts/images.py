IMAGE_PLAN_PROMPT = """TASK: Recommend image placements for a blog article.

Read the article carefully. You must decide:
1. Which sections need an illustrative inline image, and where (before or after the heading)
2. How many images each section should have
3. What keywords would find the right image on Unsplash
4. Whether the article needs a cover/featured image, and with what keywords

ARTICLE TITLE: {title}
ARTICLE TOPIC: {topic}

SECTIONS:
{sections_summary}

OUTPUT - Return ONLY valid JSON with this exact structure:
{{
  "inline_images": [
    {{
      "section_slug": "section-slug-from-above",
      "position": "before",
      "keywords": ["specific visual keyword 1", "keyword 2"],
      "suggested_count": 1,
      "rationale": "Brief explanation of why this section benefits from an image"
    }}
  ],
  "cover_image": {{
    "keywords": ["cover image keyword 1", "keyword 2"],
    "suggested_count": 1,
    "rationale": "Why this cover image represents the article"
  }}
}}

RULES:
- Not every section needs an inline image. Only recommend images for sections that truly benefit from visual illustration (diagrams, comparisons, concrete examples)
- Typically 2-4 inline images per article, not more
- position is "before" (image before section heading) or "after" (image after section heading, within the section)
- Cover image: exactly one cover image recommendation, or set cover_image to null if the topic really doesn't suit a cover
- Keywords must be specific, visual, and Unsplash-searchable (not abstract concepts)
- Avoid brand names, trademarked terms, or NSFW concepts
- Use section slugs EXACTLY as provided in the sections list above
- suggested_count: 1 for most sections, 2 for comparison/step-by-step sections"""

IMAGE_KEYWORD_PROMPT_TEMPLATE = """TASK: Generate image search keywords for a blog section.

SECTION HEADING: {heading}
SECTION CONTENT PREVIEW (first 500 chars): {content_preview}

Generate 2-3 search keywords that would find relevant, visually-appealing images on stock photo sites (Unsplash, Pexels).

RULES:
- Keywords must be specific and visual (not abstract concepts)
- Avoid brand names or trademarked terms
- Consider: diagrams, illustrations, photos, screenshots, infographics
- Rank by relevance (best match first)

OUTPUT - Return ONLY valid JSON:
{{"keywords": ["precise visual keyword phrase 1", "phrase 2", "phrase 3"]}}

EXAMPLE: For a section about "Training LoRA adapters with HuggingFace PEFT":
{{"keywords": ["neural network fine-tuning diagram", "LoRA adapter architecture illustration", "machine learning model optimization"]}}"""
