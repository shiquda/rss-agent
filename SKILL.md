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

### `list` - 列出订阅
```bash
rss list                          # 列出所有订阅
rss list --category 博客          # 按分类筛选
rss list --verbose                # 显示 URL 详情
```

### `add` - 添加订阅
```bash
rss add <url>                     # 基础添加
rss add <url> --name "My Blog"    # 自定义名称
rss add <url> -c 科技 -n "博客名"  # 指定分类和名称
```

### `remove` - 删除订阅
```bash
rss remove "博客名称"              # 按名称删除
rss remove https://example.com/feed.xml  # 按 URL 删除
```

### `check` - 健康检查
```bash
rss check                         # 检查所有订阅状态
```
输出示例：
```
✅ Feed Name 1      # 正常
⚠️  Feed Name 2      # 返回非 RSS 内容
❌ Feed Name 3      # 无法访问
```

### `fetch` - 获取内容
```bash
rss fetch "Feed Name"             # 获取最新 5 条
rss fetch "Feed Name" -n 10       # 获取最新 10 条
rss fetch "Feed Name" -v          # 显示文章链接
```

### `export` - 导出 OPML
```bash
rss export                        # 导出为 rss_export_YYYYMMDD.opml
rss export -o backup.opml         # 指定文件名
```

### `import` - 导入 OPML
```bash
rss import follow.opml            # 从 OPML 导入
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
    "message": "Fetch latest 3 items from all RSS feeds in category 'AI', summarize them in Chinese, and send a report"
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

## Progressive Reading

The skill supports a 3-level disclosure pattern:

**Level 1 - Headlines**: Quick overview with `rss fetch`
**Level 2 - Summaries**: Agent summarizes interesting articles
**Level 3 - Full content**: Use `web_fetch` for complete article

Example interaction:
```
User: "Check my RSS 'Tech' category"
→ Agent lists new articles from Tech feeds
User: "Tell me more about the AI article"
→ Agent fetches full content and summarizes
User: "Read the full article"
→ Agent uses web_fetch + TTS for audio playback
```

## File Structure

```
skills/rss-agent/
├── SKILL.md              # This file
├── scripts/
│   ├── rss.py           # Main CLI (unified interface)
│   ├── fetch_feed.py    # Low-level feed fetching
│   ├── rss_utils.py     # OPML parsing utilities
│   └── json_to_opml.py  # Export helper (legacy, use rss.py export)
└── references/          # Additional documentation
```

## Legacy Scripts

For backward compatibility, these scripts remain available:

- `fetch_feed.py <url> <limit>` - Direct feed fetching
- `rss_utils.py parse <opml>` - OPML parsing
- `rss_utils.py check <url>` - Single feed check
- `json_to_opml.py <json> [opml]` - JSON to OPML conversion

Prefer using the unified `rss.py` CLI for new workflows.

## Tips

- Use `rss check` periodically to clean up dead feeds
- Categories help organize feeds for targeted reading
- Combine with `tts` for audio news briefings
- For complex websites blocked to `web_fetch`, use `browser` tool
