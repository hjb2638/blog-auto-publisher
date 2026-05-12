import bleach


ALLOWED_TAGS = [
    "h2", "h3", "h4", "p", "ul", "ol", "li",
    "pre", "code", "blockquote", "strong", "em",
    "a", "img", "figure", "figcaption", "br", "hr",
    "table", "thead", "tbody", "tr", "th", "td",
    "div", "span", "article", "section",
]

ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "rel"],
    "img": ["src", "alt", "width", "height", "loading"],
    "code": ["class"],
    "pre": ["class"],
    "figure": ["class"],
    "figcaption": ["class"],
    "div": ["class"],
    "span": ["class"],
}


def sanitize_html(html: str) -> str:
    return bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True,
    )


def sanitize_text(text: str) -> str:
    return bleach.clean(text, tags=[], strip=True)
