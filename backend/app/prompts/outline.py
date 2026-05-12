OUTLINE_PROMPT_TEMPLATE = """TASK: Generate a detailed, well-structured blog post outline.

TOPIC: {topic}

ADDITIONAL REQUIREMENTS: {requirements}

OUTPUT FORMAT - Return ONLY valid JSON, no other text:
{{
  "title": "SEO-friendly, compelling title (max 60 chars)",
  "meta_description": "SEO meta description (max 155 chars)",
  "sections": [
    {{
      "heading": "Descriptive, scannable section heading",
      "slug": "url-friendly-slug",
      "key_points": ["Concrete point 1", "Concrete point 2", "Concrete point 3"],
      "estimated_words": 300,
      "include_code_example": false
    }}
  ],
  "seo_keywords": ["keyword1", "keyword2", "keyword3", "keyword4"],
  "category": "Most appropriate technology category",
  "tags": ["relevant", "specific", "tags"]
}}

STRUCTURE RULES:
- Section 1 MUST be an introduction that hooks the reader and defines scope
- Sections 2 through N-1 are body content (4-7 body sections)
- Final section MUST be a conclusion with key takeaways
- Sections should progress logically: fundamentals-to-advanced, or problem-to-solution, or chronological
- Each key_point must be a concrete, specific item (not vague like "explain the concept")
- Total estimated words across all sections should be 1500-3000

Write the output in {language} language."""
