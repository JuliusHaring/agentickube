#!/usr/bin/env python3
"""Fetch multiple URLs in parallel and print combined results.

Usage: python fetch_urls.py <url1> <url2> ... [--user-agent UA] [--timeout SECS]
"""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx

DEFAULT_USER_AGENT = "AgentickubeAgent/1.0 (httpx)"
MAX_CHARS_PER_URL = 15000


def _fetch_one(url: str, user_agent: str, timeout: float) -> tuple[str, str]:
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch multiple URLs in parallel.")
    parser.add_argument("urls", nargs="+", help="URLs to fetch")
    parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT)
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()

    seen: set[str] = set()
    unique: list[str] = []
    for u in args.urls:
        u = u.strip()
        if u and u not in seen:
            seen.add(u)
            unique.append(u)

    if not unique:
        print("No URLs provided.")
        return

    parts: list[str] = []
    with ThreadPoolExecutor(max_workers=min(10, len(unique))) as executor:
        futures = {
            executor.submit(_fetch_one, u, args.user_agent, args.timeout): u
            for u in unique
        }
        for future in as_completed(futures):
            url, content = future.result()
            parts.append(f"---\nURL: {url}\n---\n{content}")

    print("\n\n".join(parts))


if __name__ == "__main__":
    main()
