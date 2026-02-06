---
name: rss-agent
description: A powerful RSS subscription manager and reader. Use it to (1) Import/export OPML files, (2) Manage RSS feeds (add, remove, categorize), (3) Validate feed connectivity, (4) Schedule periodic updates via cron, (5) Fetch and summarize articles with a progressive disclosure approach.
---

# RSS Agent

Manage and consume RSS feeds directly within OpenClaw. This skill replaces traditional RSS readers by providing AI-powered summaries, progressive exploration, and automated delivery.

## Quick Start

Use the unified CLI to manage your subscriptions:

```bash
# List all feeds
python3 skills/rss-agent/scripts/rss.py list

# Add a new feed
python3 skills/rss-agent/scripts/rss.py add https://example.com/feed.xml --category Tech

# Fetch latest articles
python3 skills/rss-agent/scripts/rss.py fetch "Feed Name" --limit 5

# Check feed health
python3 skills/rss-agent/scripts/rss.py check

# Export to OPML
python3 skills/rss-agent/scripts/rss.py export -o my_feeds.opml
```

## CLI Commands

### `list` - List subscriptions
```bash
rss list                          # List all subscriptions
rss list --category Tech          # Filter by category
rss list --verbose                # Show URLs
```

### `add` - Add subscription
```bash
rss add <url>                     # Basic add
rss add <url> --name "My Blog"    # Custom name
rss add <url> -c Tech -n "Blog"   # Specify category and name
```

### `remove` - Remove subscription
```bash
rss remove "Feed Name"             # Remove by name
rss remove https://example.com/feed.xml  # Remove by URL
```

### `check` - Health check
```bash
rss check                         # Check all feed status
```
Output example:
```
✅ Feed Name 1      # OK
⚠️  Feed Name 2      # Invalid content
❌ Feed Name 3      # Cannot access
```

### `fetch` - Fetch content
```bash
rss fetch "Feed Name"             # Get latest 5 items
rss fetch "Feed Name" -n 10       # Get latest 10 items
rss fetch "Feed Name" -v          # Show links
rss fetch "Feed Name" --full-content  # Get full content (if supported)
```

### `digest` - Daily digest
```bash
rss digest                        # Get today's updates
rss digest -d 2                   # Get last 2 days
rss digest -c "AI" --limit 5      # Filter by category
```

### `export` - Export to OPML
```bash
rss export                        # Export as rss_export_YYYYMMDD.opml
rss export -o backup.opml         # Specify filename
```

### `import` - Import from OPML
```bash
rss import follow.opml            # Import from OPML
```

## Data Storage

- **Feed list**: `/root/.openclaw/workspace/rss_feeds.json`
- **Schema**:
```json
[
  {
    "name": "Blog Name",
    "xmlUrl": "https://example.com/feed.xml",
    "htmlUrl": "https://example.com/",
    "category": "Technology"
  }
]
```

## Automation (Cron)

Schedule periodic RSS updates using OpenClaw's cron tool:

### Daily Summary Example
```json
{
  "schedule": {"kind": "cron", "expr": "0 9 * * *"},
  "payload": {
    "kind": "agentTurn",
    "message": "Fetch latest 3 items from all RSS feeds in category 'AI', summarize them, and send a report"
  },
  "sessionTarget": "isolated"
}
```

### Implementation Pattern
When asked to check RSS feeds, the agent will:
1. Run `python3 skills/rss-agent/scripts/rss.py list --category <cat>` to get feed list
2. Run `python3 skills/rss-agent/scripts/rss.py fetch "<name>"` for each feed
3. Use `web_fetch` to get full article content if needed
4. Summarize and format results

## Full Content Extraction

Some RSS feeds provide full article content via `content:encoded` (RSS 2.0) or `content` (Atom) fields. Use the `--full-content` flag to extract and read articles directly:

```bash
# Read full article without opening browser
rss fetch "Feed Name" --limit 1 --full-content

# Check which feeds in your collection support full content
rss list --verbose
```

**How it works:**
- RSS 2.0 feeds with `content:encoded` field → ✅ Full content available
- Atom feeds with `content` field → ✅ Full content available
- Feeds with only `description`/`summary` → ❌ Only summary available

**Notes:**
- Full content extraction strips HTML tags for readability
- If a feed doesn't provide full content, the CLI will show a warning
- For feeds without full content, use `web_fetch` or `browser` tools as fallback

## Progressive Reading

The skill supports a 3-level disclosure pattern:

**Level 1 - Headlines**: Quick overview with `rss fetch`
**Level 2 - Summaries**: Agent summarizes interesting articles
**Level 3 - Full content**: Use `rss fetch --full-content` or `web_fetch` for complete article

Example interaction:
```
User: "Check my RSS 'Tech' category"
→ Agent lists new articles from Tech feeds
User: "Tell me more about the AI article"
→ Agent fetches full content using rss fetch --full-content and summarizes
User: "Read the full article"
→ Agent displays the full content or uses TTS for audio playback
```

## File Structure

```
skills/rss-agent/
├── SKILL.md              # This file
└── scripts/
    └── rss.py           # Main CLI (unified interface)
```

## Tips

- Use `rss check` periodically to clean up dead feeds
- Use `rss digest` for quick daily updates overview
- Categories help organize feeds for targeted reading
- Combine with `tts` for audio news briefings
- For complex websites blocked to `web_fetch`, use `browser` tool
- Try `rss fetch --full-content` first before using `web_fetch` - it's faster for supported feeds
