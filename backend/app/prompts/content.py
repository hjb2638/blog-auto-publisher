CONTENT_PROMPT_TEMPLATE = """TASK: Write exactly ONE section of a blog post. Do NOT write the entire article.

ARTICLE TITLE: {title}
ARTICLE TOPIC: {topic}

PREVIOUS SECTION (for context): {previous_section_summary}
NEXT SECTION (for transition): {next_section_heading}

CURRENT SECTION:
- Heading: {heading}
- Key points that MUST be covered: {key_points}
- Target word count: {estimated_words} words
- Include code example: {include_code_example}
- Section position: {section_number} of {total_sections}

GUIDELINES:
1. Write ONLY the content for this section - start with <h2>, end with a transition sentence
2. Cover ALL key points listed above - do not skip any
3. If include_code_example is true, provide a practical, runnable code example with explanation
4. Open with a brief 1-sentence transition from the previous section
5. End with a 1-sentence natural transition to the next section
6. Use <pre><code class="language-python"> (or js, bash, etc.) for code blocks
7. Target the specified word count (within 20%)

FORMAT: Output raw HTML starting with an <h2> tag. No preamble, no closing remarks.

Write in {language} language."""
