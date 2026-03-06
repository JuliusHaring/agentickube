---
name: internet
description: Fetch URLs over HTTP/HTTPS and parse markdown. Uses httpx with an optional custom User-Agent. Use when the user asks to fetch a URL, fetch a webpage, get content from the internet, or parse markdown text.
---

# Internet Usage

Use the tools in this skill to fetch content from the web and to parse markdown.

## When to use

- User asks to fetch a URL, open a link, or get content from the web.
- User provides a URL and wants the page body or text.
- User has markdown text and wants it parsed (e.g. converted to HTML or normalized).

## Tools

- **fetch_url**: Fetches a URL with GET. Optionally set a custom User-Agent; otherwise a default agent string is used. Returns the response body as text. Use for APIs, docs, or plain pages.
- **parse_markdown**: Converts markdown text to HTML. Use when you need to render or structure markdown (e.g. for display or further processing).

## Notes

- For HTML pages, `fetch_url` returns raw HTML; you may need to extract text or links from it.
- Set `user_agent` when a site requires a browser-like or specific User-Agent.
- Timeouts and redirects follow httpx defaults; large responses are read into memory.
