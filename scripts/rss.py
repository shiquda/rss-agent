#!/usr/bin/env python3
"""
RSS Agent CLI - Unified RSS Feed Manager
Usage: rss <command> [options]
"""

import argparse
import json
import os
import sys
from datetime import datetime

# Config paths
CONFIG_DIR = os.path.expanduser("~/.openclaw/workspace")
FEEDS_FILE = os.path.join(CONFIG_DIR, "rss_feeds.json")

def load_feeds():
    """Load subscription list"""
    if not os.path.exists(FEEDS_FILE):
        return []
    with open(FEEDS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_feeds(feeds):
    """Save subscription list"""
    with open(FEEDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(feeds, f, ensure_ascii=False, indent=2)

def cmd_list(args):
    """List all subscriptions"""
    feeds = load_feeds()
    
    if args.category:
        feeds = [f for f in feeds if f.get('category') == args.category]
    
    if not feeds:
        print("📭 No subscriptions found")
        return
    
    # Group by category
    categories = {}
    for feed in feeds:
        cat = feed.get('category') or 'Uncategorized'
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(feed)
    
    total = len(feeds)
    print(f"📚 {total} subscriptions\n")
    
    for cat, cat_feeds in sorted(categories.items()):
        print(f"\n【{cat}】({len(cat_feeds)})")
        print("-" * 40)
        for feed in cat_feeds:
            name = feed.get('name', 'Unknown')
            url = feed.get('xmlUrl', '')
            url_display = url[:50] + "..." if len(url) > 50 else url
            print(f"  • {name}")
            if args.verbose:
                print(f"    URL: {url_display}")

def cmd_add(args):
    """Add new subscription"""
    feeds = load_feeds()
    
    # Check if exists
    for feed in feeds:
        if feed.get('xmlUrl') == args.url:
            print(f"⚠️ Already exists: {feed.get('name')}")
            return
    
    new_feed = {
        "xmlUrl": args.url,
        "category": args.category or "Uncategorized"
    }
    
    if args.name:
        new_feed["name"] = args.name
    else:
        from urllib.parse import urlparse
        parsed = urlparse(args.url)
        new_feed["name"] = parsed.netloc or "Unnamed"
    
    if args.html_url:
        new_feed["htmlUrl"] = args.html_url
    
    feeds.append(new_feed)
    save_feeds(feeds)
    print(f"✅ Added: {new_feed['name']}")
    print(f"   Category: {new_feed['category']}")

def cmd_remove(args):
    """Remove subscription"""
    feeds = load_feeds()
    
    removed = []
    remaining = []
    
    for feed in feeds:
        if feed.get('name') == args.identifier or feed.get('xmlUrl') == args.identifier:
            removed.append(feed)
        else:
            remaining.append(feed)
    
    if not removed:
        print(f"❌ Not found: {args.identifier}")
        return
    
    save_feeds(remaining)
    for feed in removed:
        print(f"🗑️ Removed: {feed.get('name')}")

def cmd_check(args):
    """Check feed health"""
    import requests
    
    feeds = load_feeds()
    
    if not feeds:
        print("📭 No subscriptions")
        return
    
    print(f"🔍 Checking {len(feeds)} feeds...\n")
    
    ok_count = 0
    fail_count = 0
    
    for feed in feeds:
        name = feed.get('name', 'Unknown')
        url = feed.get('xmlUrl', '')
        
        try:
            resp = requests.get(url, timeout=10, 
                              headers={'User-Agent': 'OpenClaw-RSS-Agent/1.0'})
            if resp.status_code == 200:
                content_type = resp.headers.get('Content-Type', '').lower()
                is_xml = 'xml' in content_type or 'rss' in content_type or 'atom' in content_type
                if not is_xml:
                    is_xml = resp.text.strip().startswith('<?xml') or '<rss' in resp.text[:500]
                
                if is_xml:
                    print(f"✅ {name}")
                    ok_count += 1
                else:
                    print(f"⚠️ {name} - Invalid RSS/Atom")
                    fail_count += 1
            else:
                print(f"❌ {name} - HTTP {resp.status_code}")
                fail_count += 1
        except Exception as e:
            print(f"❌ {name} - {str(e)[:50]}")
            fail_count += 1
    
    print(f"\n📊 Result: {ok_count} OK, {fail_count} Failed")

def cmd_fetch(args):
    """Fetch feed content"""
    import requests
    import xml.etree.ElementTree as ET
    import html
    
    feeds = load_feeds()
    
    target_feed = None
    for feed in feeds:
        if feed.get('name') == args.identifier or feed.get('xmlUrl') == args.identifier:
            target_feed = feed
            break
    
    if not target_feed:
        print(f"❌ Not found: {args.identifier}")
        return
    
    url = target_feed.get('xmlUrl')
    name = target_feed.get('name')
    limit = args.limit
    full_content = args.full_content
    
    print(f"📡 Fetching: {name}{' (full content)' if full_content else ''}\n")
    
    try:
        resp = requests.get(url, timeout=15, 
                          headers={'User-Agent': 'OpenClaw-RSS-Agent/1.0'})
        if resp.status_code != 200:
            print(f"❌ HTTP {resp.status_code}")
            return
        
        root = ET.fromstring(resp.content)
        items = []
        
        content_ns = '{http://purl.org/rss/1.0/modules/content/}'
        atom_ns = '{http://www.w3.org/2005/Atom}'
        
        # RSS 2.0
        channel = root.find('channel')
        if channel is not None:
            for item in channel.findall('item')[:limit]:
                title = item.findtext('title', 'No Title')
                link = item.findtext('link', '')
                pub_date = item.findtext('pubDate', '')
                desc = item.findtext('description', '')
                
                content = None
                if full_content:
                    content_elem = item.find(f'{content_ns}encoded')
                    if content_elem is not None and content_elem.text:
                        content = html.unescape(content_elem.text)
                
                items.append({
                    "title": title, 
                    "link": link, 
                    "date": pub_date,
                    "summary": desc[:300] + "..." if len(desc) > 300 else desc,
                    "content": content
                })
        else:
            # Atom
            entries = root.findall(f'{atom_ns}entry')
            for entry in entries[:limit]:
                title = entry.findtext(f'{atom_ns}title', 'No Title')
                link_node = entry.find(f'{atom_ns}link')
                link = link_node.get('href') if link_node is not None else ''
                pub_date = entry.findtext(f'{atom_ns}updated', '')
                summary = entry.findtext(f'{atom_ns}summary', '')
                
                content = None
                if full_content:
                    content_elem = entry.find(f'{atom_ns}content')
                    if content_elem is not None and content_elem.text:
                        content = html.unescape(content_elem.text)
                
                items.append({
                    "title": title, 
                    "link": link, 
                    "date": pub_date,
                    "summary": summary[:300] + "..." if len(summary) > 300 else summary,
                    "content": content
                })
        
        print(f"📰 Latest {len(items)} items:\n")
        for i, item in enumerate(items, 1):
            print(f"{'='*50}")
            print(f"{i}. {item['title']}")
            if item['date']:
                print(f"   Date: {item['date']}")
            if args.verbose and item['link']:
                print(f"   Link: {item['link']}")
            
            if full_content and item['content']:
                content = item['content']
                content = content.replace('<p>', '\n').replace('</p>', '')
                content = content.replace('<br>', '\n').replace('<br/>', '\n')
                import re
                content = re.sub('<[^<]+?>', '', content)
                content = html.unescape(content)
                print(f"\n📄 Content:\n{content[:2000]}..." if len(content) > 2000 else f"\n📄 Content:\n{content}")
            elif not full_content:
                print(f"\n📝 Summary: {item['summary']}")
            else:
                print(f"\n⚠️ Full content not available")
            print()
            
    except Exception as e:
        print(f"❌ Failed: {e}")

def cmd_export(args):
    """Export to OPML"""
    from xml.etree.ElementTree import Element, SubElement, tostring
    from xml.dom import minidom
    
    feeds = load_feeds()
    
    if not feeds:
        print("📭 No subscriptions to export")
        return
    
    opml = Element('opml', version='2.0')
    
    head = SubElement(opml, 'head')
    title = SubElement(head, 'title')
    title.text = 'RSS Subscriptions'
    date_created = SubElement(head, 'dateCreated')
    date_created.text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
    
    body = SubElement(opml, 'body')
    
    categories = {}
    for feed in feeds:
        cat = feed.get('category') or 'Uncategorized'
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(feed)
    
    for category, cat_feeds in sorted(categories.items()):
        if len(categories) > 1:
            cat_outline = SubElement(body, 'outline', text=category, title=category)
            parent = cat_outline
        else:
            parent = body
        
        for feed in cat_feeds:
            attrs = {
                'type': 'rss',
                'text': feed.get('name', 'Unknown'),
                'title': feed.get('name', 'Unknown'),
                'xmlUrl': feed.get('xmlUrl', '')
            }
            if feed.get('htmlUrl'):
                attrs['htmlUrl'] = feed['htmlUrl']
            SubElement(parent, 'outline', **attrs)
    
    xml_str = tostring(opml, encoding='utf-8')
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent='  ', encoding='utf-8')
    lines = [line for line in pretty_xml.decode('utf-8').split('\n') if line.strip()]
    pretty_xml = '\n'.join(lines)
    
    output_file = args.output or f'rss_export_{datetime.now().strftime("%Y%m%d")}.opml'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)
    
    print(f"✅ Exported: {output_file}")
    print(f"📊 {len(feeds)} feeds, {len(categories)} categories")

def cmd_import(args):
    """Import from OPML"""
    import xml.etree.ElementTree as ET
    
    if not os.path.exists(args.file):
        print(f"❌ File not found: {args.file}")
        return
    
    try:
        tree = ET.parse(args.file)
        root = tree.getroot()
        
        new_feeds = []
        
        def walk(node, category=None):
            for outline in node.findall('outline'):
                text = outline.get('text')
                xml_url = outline.get('xmlUrl')
                html_url = outline.get('htmlUrl')
                
                if xml_url:
                    new_feeds.append({
                        "name": text,
                        "xmlUrl": xml_url,
                        "htmlUrl": html_url,
                        "category": category or "Uncategorized"
                    })
                
                walk(outline, category=text if not xml_url else category)
        
        walk(root.find('body'))
        
        if not new_feeds:
            print("⚠️ No feeds found in OPML")
            return
        
        existing_feeds = load_feeds()
        existing_urls = {f.get('xmlUrl') for f in existing_feeds}
        
        added = 0
        skipped = 0
        
        for feed in new_feeds:
            if feed['xmlUrl'] not in existing_urls:
                existing_feeds.append(feed)
                added += 1
            else:
                skipped += 1
        
        save_feeds(existing_feeds)
        print(f"✅ Imported: {added} new, {skipped} skipped")
        
    except Exception as e:
        print(f"❌ Import failed: {e}")

def cmd_digest(args):
    """Get daily digest of updates (concurrent fetch)"""
    import requests
    import xml.etree.ElementTree as ET
    from datetime import datetime, timedelta
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    feeds = load_feeds()
    
    if not feeds:
        print("📭 No subscriptions")
        return
    
    if args.category:
        feeds = [f for f in feeds if f.get('category') == args.category]
        if not feeds:
            print(f"📭 No feeds in category '{args.category}'")
            return
    
    now = datetime.now()
    if args.days:
        since = now - timedelta(days=args.days)
    else:
        since = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    print(f"📅 Updates: {since.strftime('%Y-%m-%d %H:%M')} → {now.strftime('%Y-%m-%d %H:%M')}\n")
    
    if args.max_feeds > 0:
        feeds = feeds[:args.max_feeds]
    
    all_updates = []
    processed = 0
    
    def fetch_feed_updates(feed):
        """Fetch updates from a single feed"""
        name = feed.get('name', 'Unknown')
        url = feed.get('xmlUrl', '')
        category = feed.get('category') or 'Uncategorized'
        items = []
        
        try:
            resp = requests.get(url, timeout=10, 
                              headers={'User-Agent': 'OpenClaw-RSS-Agent/1.0'})
            if resp.status_code != 200:
                return []
            
            root = ET.fromstring(resp.content)
            
            content_ns = '{http://purl.org/rss/1.0/modules/content/}'
            atom_ns = '{http://www.w3.org/2005/Atom}'
            
            channel = root.find('channel')
            if channel is not None:
                for item in channel.findall('item'):
                    title = item.findtext('title', 'No Title')
                    link = item.findtext('link', '')
                    pub_date = item.findtext('pubDate', '')
                    
                    if pub_date:
                        try:
                            from email.utils import parsedate_to_datetime
                            item_date = parsedate_to_datetime(pub_date)
                            if item_date.tzinfo:
                                item_date = item_date.replace(tzinfo=None)
                            if item_date >= since:
                                items.append({
                                    'title': title,
                                    'link': link,
                                    'date': item_date,
                                    'feed_name': name,
                                    'category': category
                                })
                        except:
                            pass
            else:
                entries = root.findall(f'{atom_ns}entry')
                for entry in entries:
                    title = entry.findtext(f'{atom_ns}title', 'No Title')
                    link_node = entry.find(f'{atom_ns}link')
                    link = link_node.get('href') if link_node is not None else ''
                    pub_date = entry.findtext(f'{atom_ns}updated', '')
                    
                    if pub_date:
                        try:
                            item_date = datetime.fromisoformat(pub_date.replace('Z', '+00:00').replace('+00:00', ''))
                            if item_date >= since:
                                items.append({
                                    'title': title,
                                    'link': link,
                                    'date': item_date,
                                    'feed_name': name,
                                    'category': category
                                })
                        except:
                            pass
            
            return items
            
        except Exception as e:
            return []
    
    # Concurrent fetch using ThreadPoolExecutor
    max_workers = min(20, len(feeds))  # Max 20 concurrent threads
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_feed = {executor.submit(fetch_feed_updates, feed): feed for feed in feeds}
        
        for future in as_completed(future_to_feed):
            feed = future_to_feed[future]
            processed += 1
            try:
                items = future.result()
                all_updates.extend(items)
            except Exception as e:
                pass
    
    all_updates.sort(key=lambda x: x['date'], reverse=True)
    
    if not all_updates:
        print(f"📭 No new content in this period (checked {processed} feeds)")
        return
    
    by_category = {}
    for item in all_updates:
        cat = item['category'] or 'Uncategorized'
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(item)
    
    print(f"📊 {len(all_updates)} new items from {processed} feeds\n")
    print("="*60)
    
    for category in sorted(by_category.keys()):
        items = by_category[category]
        print(f"\n【{category}】({len(items)})")
        print("-"*40)
        
        for item in items[:args.limit]:
            time_str = item['date'].strftime('%m-%d %H:%M')
            print(f"  • [{time_str}] {item['title'][:50]}{'...' if len(item['title']) > 50 else ''}")
            print(f"    Source: {item['feed_name']}")
            if args.verbose and item['link']:
                print(f"    Link: {item['link']}")
        
        if len(items) > args.limit:
            print(f"    ... {len(items) - args.limit} more")
    
    print(f"\n{'='*60}")
    print(f"🕐 Updated: {now.strftime('%Y-%m-%d %H:%M')}")

def main():
    parser = argparse.ArgumentParser(
        prog='rss',
        description='RSS Agent CLI - Manage your RSS subscriptions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  rss list                      # List all subscriptions
  rss list --category Tech      # Filter by category
  rss add https://example.com/feed.xml --category Tech
  rss remove "Feed Name"
  rss check                     # Check feed health
  rss fetch "Feed Name" --limit 3      # Get latest 3 items
  rss digest                    # Get today's updates
  rss digest -d 2               # Get last 2 days updates
  rss export                    # Export to OPML
  rss import follow.opml        # Import from OPML
        '''
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # list
    list_parser = subparsers.add_parser('list', help='List all subscriptions')
    list_parser.add_argument('-c', '--category', help='Filter by category')
    list_parser.add_argument('-v', '--verbose', action='store_true', help='Show details')
    
    # add
    add_parser = subparsers.add_parser('add', help='Add subscription')
    add_parser.add_argument('url', help='RSS feed URL')
    add_parser.add_argument('-n', '--name', help='Custom name')
    add_parser.add_argument('-c', '--category', help='Category')
    add_parser.add_argument('--html-url', help='Website URL')
    
    # remove
    remove_parser = subparsers.add_parser('remove', help='Remove subscription')
    remove_parser.add_argument('identifier', help='Feed name or URL')
    
    # check
    check_parser = subparsers.add_parser('check', help='Check feed health')
    
    # fetch
    fetch_parser = subparsers.add_parser('fetch', help='Fetch feed content')
    fetch_parser.add_argument('identifier', help='Feed name or URL')
    fetch_parser.add_argument('-n', '--limit', type=int, default=5, help='Number of items (default 5)')
    fetch_parser.add_argument('-v', '--verbose', action='store_true', help='Show links')
    fetch_parser.add_argument('--full-content', action='store_true', help='Get full content (if supported)')
    
    # export
    export_parser = subparsers.add_parser('export', help='Export to OPML')
    export_parser.add_argument('-o', '--output', help='Output filename')
    
    # import
    import_parser = subparsers.add_parser('import', help='Import from OPML')
    import_parser.add_argument('file', help='OPML file path')
    
    # digest
    digest_parser = subparsers.add_parser('digest', help='Get daily digest')
    digest_parser.add_argument('-d', '--days', type=int, help='Last N days')
    digest_parser.add_argument('-n', '--limit', type=int, default=3, help='Items per category (default 3)')
    digest_parser.add_argument('-c', '--category', help='Filter by category')
    digest_parser.add_argument('-v', '--verbose', action='store_true', help='Show links')
    digest_parser.add_argument('--max-feeds', type=int, default=0, help='Max feeds to check (0=all)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    commands = {
        'list': cmd_list,
        'add': cmd_add,
        'remove': cmd_remove,
        'check': cmd_check,
        'fetch': cmd_fetch,
        'export': cmd_export,
        'import': cmd_import,
        'digest': cmd_digest,
    }
    
    commands[args.command](args)

if __name__ == '__main__':
    main()
