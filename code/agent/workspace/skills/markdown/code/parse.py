"""Parse markdown to HTML. Uses the markdown library with 'extra' extension."""

import markdown


def parse_markdown(markdown_text: str) -> str:
    """Parse markdown text and return HTML.

    Args:
        markdown_text: Raw markdown string (e.g. from a file or fetch_url).
    """
    if not markdown_text or not markdown_text.strip():
        return ""
    return markdown.markdown(
        markdown_text.strip(),
        extensions=["extra"],
    )
