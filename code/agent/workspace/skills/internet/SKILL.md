---
name: internet
description: Fetch URLs over HTTP/HTTPS. Uses httpx with an optional custom User-Agent. Use when the user asks to fetch a URL, fetch a webpage, or get content from the internet.
---

# Internet

Use the tools in this skill to fetch content from the web.

## When to use

- User asks to fetch a URL, open a link, or get content from the web.
- User provides a URL and wants the page body or text.

## Tools

- **fetch_url**: Fetches a URL with GET. Optionally set a custom User-Agent; otherwise a default agent string is used. Returns the response body as text. Use for APIs, docs, or plain pages.

## Notes

- For HTML pages, `fetch_url` returns raw HTML; you may need to extract text or links from it.
- Set `user_agent` when a site requires a browser-like or specific User-Agent.
- Timeouts and redirects follow httpx defaults; large responses are read into memory.
