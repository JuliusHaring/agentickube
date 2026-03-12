---
name: internet
description: Fetch URLs over HTTP/HTTPS. Use when the user asks to fetch a URL, get content from the web, or retrieve multiple pages.
---

# Internet

Fetch content from the web over HTTP/HTTPS.

## When to use

- User asks to fetch a URL, open a link, or get content from the web.
- User provides a URL and wants the page body or text.
- User asks for multiple sites at once (e.g. compare pages, aggregate from several URLs).

## Scripts

### fetch_url.py

Fetch a single URL and print the response body.

**Usage:** `python fetch_url.py <url> [user_agent]`

- `url`: The URL to fetch.
- `user_agent`: Optional custom User-Agent header (default: AgentickubeAgent/1.0).
- Output is the response text printed to stdout (truncated at 15000 chars).

### fetch_urls.py

Fetch multiple URLs in parallel and print combined results.

**Usage:** `python fetch_urls.py <url1> <url2> ... [--user-agent UA] [--timeout SECS]`

- Each URL's result is printed as a separate section.
- `--user-agent`: Optional custom User-Agent for all requests.
- `--timeout`: Timeout per request in seconds (default 30).

## Notes

- For HTML pages, scripts return raw HTML; you may need to extract text or links from it.
- Large or slow responses are truncated; multiple URLs are fetched concurrently.
