---
name: internet
description: Fetch URLs over HTTP/HTTPS. Uses httpx with an optional custom User-Agent. Use when the user asks to fetch a URL, fetch a webpage, or get content from the internet.
---

# Internet

Use the tools in this skill to fetch content from the web.

## When to use

- User asks to fetch a URL, open a link, or get content from the web.
- User provides a URL and wants the page body or text.
- User asks for multiple sites at once (e.g. compare pages, aggregate from several URLs).

## Tools

- **fetch_url**: Fetches a single URL with GET. Optionally set a custom User-Agent. Returns the response body as text. Use for one page or API.

- **fetch_urls**: Fetches multiple URLs in parallel. Pass a list of URLs; returns one combined result with a clear section per URL (each block starts with `---`, then `URL: <url>`, then the content). Use when you need several websites at once (e.g. compare top movers from two sources, or fetch a fixed set of pages). Optional `user_agent` and `timeout_per_url` (seconds, default 30). Each response is truncated to avoid huge output; use `fetch_url` for a single URL if you need the full body.

## Notes

- For HTML pages, tools return raw HTML; you may need to extract text or links from it.
- Set `user_agent` when a site requires a browser-like or specific User-Agent.
- Large or slow responses are truncated; multiple URLs are fetched concurrently.
