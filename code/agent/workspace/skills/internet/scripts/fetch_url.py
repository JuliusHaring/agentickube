#!/usr/bin/env python3
"""Fetch a single URL and print its content to stdout.

Usage: python fetch_url.py <url> [user_agent]
"""

import sys

import httpx

DEFAULT_USER_AGENT = "AgentickubeAgent/1.0 (httpx)"
MAX_CHARS = 15000


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: fetch_url.py <url> [user_agent]", file=sys.stderr)
        sys.exit(1)

    url = sys.argv[1]
    user_agent = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_USER_AGENT
    headers = {"User-Agent": user_agent.strip()}

    try:
        with httpx.Client(follow_redirects=True, timeout=30.0) as client:
            r = client.get(url, headers=headers)
            r.raise_for_status()
            text = r.text
            if len(text) > MAX_CHARS:
                text = (
                    text[:MAX_CHARS]
                    + f"\n\n[Truncated: response was {len(r.text)} chars.]"
                )
            print(text)
    except httpx.HTTPStatusError as e:
        print(
            f"Error: HTTP {e.response.status_code}\n{(e.response.text or '')[:2000]}",
            file=sys.stderr,
        )
        sys.exit(1)
    except httpx.RequestError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
