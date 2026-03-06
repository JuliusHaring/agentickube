"""Fetch URLs and parse markdown. Uses httpx and an optional custom User-Agent."""

import markdown
import httpx

DEFAULT_USER_AGENT = "AgentickubeAgent/1.0 (httpx)"


def fetch_url(
    url: str,
    user_agent: str | None = None,
) -> str:
    """Fetch a URL with GET and return the response body as text.

    Args:
        url: The URL to fetch (e.g. https://example.com/page).
        user_agent: Optional User-Agent header. If not set, a default agent string is used.
    """
    headers = {"User-Agent": (user_agent or DEFAULT_USER_AGENT).strip()}
    try:
        with httpx.Client(follow_redirects=True) as client:
            r = client.get(url, headers=headers)
            r.raise_for_status()
            return r.text
    except httpx.HTTPStatusError as e:
        return (
            f"Error: HTTP {e.response.status_code} for {url}\n{e.response.text[:2000]}"
        )
    except httpx.RequestError as e:
        return f"Error fetching {url}: {e}"


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
