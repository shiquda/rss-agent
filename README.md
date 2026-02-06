# rss-agent

A powerful RSS subscription manager and reader for OpenClaw. This skill replaces traditional RSS readers by providing AI-powered summaries, progressive exploration, and automated delivery.

## Features

- **OPML Support**: Import/Export your existing subscriptions effortlessly.
- **Feed Management**: Add, remove, and categorize feeds with simple commands.
- **Health Checks**: Automatically validate feed connectivity and content validity.
- **Progressive Disclosure**: 
  - Level 1: Quick headline overview.
  - Level 2: AI-generated summaries of interesting articles.
  - Level 3: Deep dive into full article content.
- **Automation**: Schedule periodic updates and summaries via OpenClaw cron.
- **AI Native**: Tailored for AI agents to browse, summarize, and monitor information for you.

## Installation

1. Clone this repository into your OpenClaw workspace:
   ```bash
   cd ~/.openclaw/workspace/skills
   git clone <repository-url> rss-agent
   ```
2. OpenClaw will automatically detect the skill in the next session.

## Usage

Ask your OpenClaw agent to:
- "Import my OPML file from `/path/to/follow.opml`."
- "Show me the latest news from my 'AI' category."
- "Check if all my RSS feeds are still working."
- "Schedule a daily summary of my 'Tech' feeds every morning at 9 AM."

## Directory Structure

- `SKILL.md`: The core instruction file for the AI agent.
- `scripts/`: Python utilities for parsing OPML and fetching feeds.
- `references/`: Detailed API and data schema documentation.

## License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**. This ensures the code remains free and open, especially preventing closed-source commercialization in network-hosted environments.

## Contribution

Contributions are welcome! Please feel free to submit a Pull Request or open an Issue for discussion.
