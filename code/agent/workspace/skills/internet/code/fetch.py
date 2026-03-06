"""Fetch URLs over HTTP/HTTPS. Uses httpx with an optional custom User-Agent."""

from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx

DEFAULT_USER_AGENT = "AgentickubeAgent/1.0 (httpx)"

# Max chars per URL in fetch_urls output to avoid huge combined responses.
MAX_CHARS_PER_URL = 15000


def _fetch_one(
    url: str,
    user_agent: str,
    timeout: float = 30.0,
) -> tuple[str, str]:
    """Fetch a single URL. Returns (url, content_or_error)."""
    headers = {"User-Agent": user_agent}
    try:
        with httpx.Client(follow_redirects=True, timeout=timeout) as client:
            r = client.get(url, headers=headers)
            r.raise_for_status()
            text = r.text
            if len(text) > MAX_CHARS_PER_URL:
                text = (
                    text[:MAX_CHARS_PER_URL]
                    + f"\n\n[Truncated: response was {len(r.text)} chars.]"
                )
            return (url, text)
    except httpx.HTTPStatusError as e:
        return (
            url,
            f"Error: HTTP {e.response.status_code}\n{(e.response.text or '')[:2000]}",
        )
    except httpx.RequestError as e:
        return (url, f"Error: {e}")


def fetch_url(
    url: str,
    user_agent: str | None = None,
) -> str:
    """Fetch a URL with GET and return the response body as text.

    Args:
        url: The URL to fetch (e.g. https://example.com/page).
        user_agent: Optional User-Agent header. If not set, a default agent string is used.
    """
    return _fetch_one(url, user_agent)


def fetch_urls(
    urls: list[str],
    user_agent: str | None = None,
    timeout_per_url: float = 30.0,
) -> str:
    """Fetch multiple URLs in parallel and return combined results.

    Each URL's result is under a clear section. Use when you need to compare
    or aggregate content from several sites at once.

    Args:
        urls: List of URLs to fetch (e.g. ["https://a.com", "https://b.com"]).
        user_agent: Optional User-Agent header for all requests.
        timeout_per_url: Timeout in seconds per request (default 30).
    """
    if not urls:
        return "No URLs provided."
    ua = (user_agent or DEFAULT_USER_AGENT).strip()
    # Deduplicate and keep order
    seen: set[str] = set()
    unique: list[str] = []
    for u in urls:
        u = (u or "").strip()
        if u and u not in seen:
            seen.add(u)
            unique.append(u)

    parts: list[str] = []
    with ThreadPoolExecutor(max_workers=min(10, len(unique))) as executor:
        futures = {
            executor.submit(_fetch_one, u, ua, timeout_per_url): u for u in unique
        }
        for future in as_completed(futures):
            url, content = future.result()
            parts.append(f"---\nURL: {url}\n---\n{content}")
    return "\n\n".join(parts)
