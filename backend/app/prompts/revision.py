OUTLINE_REVISION_PROMPT = """TASK: Revise the blog post outline based on user feedback.

CURRENT OUTLINE:
{current_outline_json}

USER FEEDBACK:
{revision_prompt}

IMPORTANT: The user has provided specific guidance. Follow their feedback carefully while maintaining the overall structure and quality.
Modify only what the user asked to change. Keep sections and key points that the user is satisfied with.

OUTPUT: Return ONLY valid JSON with the revised outline, using the exact same format as the original.
"""

CONTENT_REVISION_PROMPT = """TASK: Revise a section of a blog post based on user feedback.

ARTICLE TITLE: {title}
SECTION HEADING: {heading}

CURRENT SECTION HTML:
{current_html}

USER FEEDBACK:
{revision_prompt}

IMPORTANT: The user has provided specific guidance. Follow their feedback carefully while maintaining the HTML format and writing quality.
Modify only what the user asked to change.

OUTPUT: Raw HTML for the revised section. Start with the appropriate heading tag. No preamble, no meta-commentary.
"""
