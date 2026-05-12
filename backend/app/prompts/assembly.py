ASSEMBLY_PROMPT_TEMPLATE = """TASK: Assemble all sections into a complete, publishable blog post.

TITLE: {title}
META DESCRIPTION: {meta_description}

SECTIONS (already written, in order):
{sections_html}

INSTRUCTIONS:
1. Verify all sections are present and in correct order
2. Add a <blockquote> with "Key Takeaways" summary at the end (3-4 bullet points)
3. Ensure smooth transitions between adjacent sections (edit minimally if needed)
4. Do NOT change the core content or structure of any section
5. Output the complete, self-contained HTML document body
6. Add proper alt-text placeholders for images (will be replaced later): <figure><img src="IMAGE_PLACEHOLDER" alt="descriptive alt text"><figcaption>caption</figcaption></figure>"""
