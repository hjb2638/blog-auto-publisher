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
