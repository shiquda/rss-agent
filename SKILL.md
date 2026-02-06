---
name: rss-agent
description: A powerful RSS subscription manager and reader. Use it to (1) Import/export OPML files, (2) Manage RSS feeds (add, remove, categorize), (3) Validate feed connectivity, (4) Schedule periodic updates via cron, (5) Fetch and summarize articles with a progressive disclosure approach.
---

# RSS Agent

Manage and consume RSS feeds directly within OpenClaw. This skill replaces traditional RSS readers by providing AI-powered summaries, progressive exploration, and automated delivery.

## Core Workflows

### 1. Feed Management
- **Import OPML**: Provide an OPML file. The agent parses it using `scripts/rss_utils.py parse <path>`.
- **Export OPML**: Convert JSON feeds to standard OPML format using `scripts/json_to_opml.py <input.json> [output.opml]`.
- **Validation**: Check if feeds are alive using `scripts/rss_utils.py check <url>`.
- **Storage**: Feed list is stored in `/root/.openclaw/workspace/rss_feeds.json`.
- **Operations**: Manually add/delete/update feeds in the JSON.

### 2. Automated Updates (Cron)
- Use the `cron` tool to schedule `agentTurn` jobs.
- **Setup Pattern**: Schedule a message like: "Using the rss-agent skill, fetch the latest 3 items from all feeds in the 'AI' category, summarize the top 5 most interesting ones, and send me a report."
- **Example**: 
    - `schedule`: `{"kind": "cron", "expr": "0 9 * * *"}` (Every day at 9 AM)
    - `payload`: `{"kind": "agentTurn", "message": "Check my RSS 'Blogs' category for new posts and summarize them."}`
- The agent will use `scripts/fetch_feed.py` to retrieve data and then format a human-friendly notification.

### 3. Progressive Reading
- **Fetch List**: Use `scripts/fetch_feed.py <url> <limit>` to get latest headlines.
- **Preview**: Show titles and short summaries.
- **Drill-down**: If interested, use `web_fetch` to get the full article or ask the agent to summarize specific links.

## File Structure
- `rss_feeds.json`: Current subscriptions and metadata.
- `scripts/rss_utils.py`: OPML parsing and connectivity checks.
- `scripts/fetch_feed.py`: Lightweight RSS/Atom fetching without external dependencies.
- `scripts/json_to_opml.py`: Convert JSON feeds to standard OPML 2.0 format for export.

## Data Schema (rss_feeds.json)
```json
[
  {
    "name": "Blog Name",
    "xmlUrl": "https://example.com/feed.xml",
    "category": "Technology",
    "lastChecked": "2026-02-06T09:00:00Z"
  }
]
```

## Tips
- For complex websites, use `browser` to capture content if `web_fetch` is blocked.
- Use `tts` to listen to your daily news summary.
