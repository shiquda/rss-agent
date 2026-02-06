#!/usr/bin/env python3
"""
RSS Agent CLI - 统一的 RSS 订阅管理工具
Usage: rss <command> [options]
"""

import argparse
import json
import os
import sys
from datetime import datetime

# 配置文件路径
CONFIG_DIR = os.path.expanduser("~/.openclaw/workspace")
FEEDS_FILE = os.path.join(CONFIG_DIR, "rss_feeds.json")

def load_feeds():
    """加载订阅列表"""
    if not os.path.exists(FEEDS_FILE):
        return []
    with open(FEEDS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_feeds(feeds):
    """保存订阅列表"""
    with open(FEEDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(feeds, f, ensure_ascii=False, indent=2)

def cmd_list(args):
    """列出所有订阅"""
    feeds = load_feeds()
    
    if args.category:
        feeds = [f for f in feeds if f.get('category') == args.category]
    
    if not feeds:
        print("📭 暂无订阅")
        return
    
    # 按分类分组
    categories = {}
    for feed in feeds:
        cat = feed.get('category') or '未分类'
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(feed)
    
    total = len(feeds)
    print(f"📚 共 {total} 个订阅\n")
    
    for cat, cat_feeds in sorted(categories.items()):
        print(f"\n【{cat}】({len(cat_feeds)}个)")
        print("-" * 40)
        for feed in cat_feeds:
            name = feed.get('name', 'Unknown')
            url = feed.get('xmlUrl', '')
            # 截断长 URL
            url_display = url[:50] + "..." if len(url) > 50 else url
            print(f"  • {name}")
            if args.verbose:
                print(f"    URL: {url_display}")

def cmd_add(args):
    """添加新订阅"""
    feeds = load_feeds()
    
    # 检查是否已存在
    for feed in feeds:
        if feed.get('xmlUrl') == args.url:
            print(f"⚠️ 该订阅已存在: {feed.get('name')}")
            return
    
    new_feed = {
        "xmlUrl": args.url,
        "category": args.category or "未分类"
    }
    
    if args.name:
        new_feed["name"] = args.name
    else:
        # 尝试从 URL 提取名称
        from urllib.parse import urlparse
        parsed = urlparse(args.url)
        new_feed["name"] = parsed.netloc or "未命名"
    
    if args.html_url:
        new_feed["htmlUrl"] = args.html_url
    
    feeds.append(new_feed)
    save_feeds(feeds)
    print(f"✅ 已添加订阅: {new_feed['name']}")
    print(f"   分类: {new_feed['category']}")

def cmd_remove(args):
    """删除订阅"""
    feeds = load_feeds()
    
    # 支持按名称或 URL 删除
    removed = []
    remaining = []
    
    for feed in feeds:
        if feed.get('name') == args.identifier or feed.get('xmlUrl') == args.identifier:
            removed.append(feed)
        else:
            remaining.append(feed)
    
    if not removed:
        print(f"❌ 未找到匹配的订阅: {args.identifier}")
        return
    
    save_feeds(remaining)
    for feed in removed:
        print(f"🗑️ 已删除: {feed.get('name')}")

def cmd_check(args):
    """检查订阅健康状态"""
    import requests
    
    feeds = load_feeds()
    
    if not feeds:
        print("📭 暂无订阅")
        return
    
    print(f"🔍 正在检查 {len(feeds)} 个订阅...\n")
    
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
                    print(f"⚠️ {name} - 返回内容不是有效的 RSS/Atom")
                    fail_count += 1
            else:
                print(f"❌ {name} - HTTP {resp.status_code}")
                fail_count += 1
        except Exception as e:
            print(f"❌ {name} - {str(e)[:50]}")
            fail_count += 1
    
    print(f"\n📊 检查结果: {ok_count} 正常, {fail_count} 异常")

def cmd_fetch(args):
    """获取订阅内容"""
    import requests
    import xml.etree.ElementTree as ET
    
    feeds = load_feeds()
    
    # 查找匹配的订阅
    target_feed = None
    for feed in feeds:
        if feed.get('name') == args.identifier or feed.get('xmlUrl') == args.identifier:
            target_feed = feed
            break
    
    if not target_feed:
        print(f"❌ 未找到订阅: {args.identifier}")
        return
    
    url = target_feed.get('xmlUrl')
    name = target_feed.get('name')
    limit = args.limit
    
    print(f"📡 正在获取: {name}\n")
    
    try:
        resp = requests.get(url, timeout=15, 
                          headers={'User-Agent': 'OpenClaw-RSS-Agent/1.0'})
        if resp.status_code != 200:
            print(f"❌ HTTP {resp.status_code}")
            return
        
        root = ET.fromstring(resp.content)
        items = []
        
        # RSS 2.0
        channel = root.find('channel')
        if channel is not None:
            for item in channel.findall('item')[:limit]:
                title = item.findtext('title', 'No Title')
                link = item.findtext('link', '')
                pub_date = item.findtext('pubDate', '')
                items.append({"title": title, "link": link, "date": pub_date})
        else:
            # Atom
            entries = root.findall('{http://www.w3.org/2005/Atom}entry')
            for entry in entries[:limit]:
                title = entry.findtext('{http://www.w3.org/2005/Atom}title', 'No Title')
                link_node = entry.find('{http://www.w3.org/2005/Atom}link')
                link = link_node.get('href') if link_node is not None else ''
                pub_date = entry.findtext('{http://www.w3.org/2005/Atom}updated', '')
                items.append({"title": title, "link": link, "date": pub_date})
        
        print(f"📰 最新 {len(items)} 条内容:\n")
        for i, item in enumerate(items, 1):
            print(f"{i}. {item['title']}")
            if item['date']:
                print(f"   时间: {item['date']}")
            if args.verbose and item['link']:
                print(f"   链接: {item['link']}")
            print()
            
    except Exception as e:
        print(f"❌ 获取失败: {e}")

def cmd_export(args):
    """导出为 OPML"""
    from xml.etree.ElementTree import Element, SubElement, tostring
    from xml.dom import minidom
    
    feeds = load_feeds()
    
    if not feeds:
        print("📭 暂无订阅可导出")
        return
    
    # 创建 OPML
    opml = Element('opml', version='2.0')
    
    head = SubElement(opml, 'head')
    title = SubElement(head, 'title')
    title.text = 'RSS Subscriptions'
    date_created = SubElement(head, 'dateCreated')
    date_created.text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
    
    body = SubElement(opml, 'body')
    
    # 按分类分组
    categories = {}
    for feed in feeds:
        cat = feed.get('category') or '未分类'
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
    
    # 格式化输出
    xml_str = tostring(opml, encoding='utf-8')
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent='  ', encoding='utf-8')
    lines = [line for line in pretty_xml.decode('utf-8').split('\n') if line.strip()]
    pretty_xml = '\n'.join(lines)
    
    output_file = args.output or f'rss_export_{datetime.now().strftime("%Y%m%d")}.opml'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)
    
    print(f"✅ 已导出: {output_file}")
    print(f"📊 总计 {len(feeds)} 个订阅，{len(categories)} 个分类")

def cmd_import(args):
    """从 OPML 导入"""
    import xml.etree.ElementTree as ET
    
    if not os.path.exists(args.file):
        print(f"❌ 文件不存在: {args.file}")
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
                        "category": category or "未分类"
                    })
                
                # 递归处理嵌套分类
                walk(outline, category=text if not xml_url else category)
        
        walk(root.find('body'))
        
        if not new_feeds:
            print("⚠️ 未在 OPML 中找到订阅源")
            return
        
        # 合并现有订阅
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
        print(f"✅ 导入完成: 新增 {added} 个, 跳过 {skipped} 个重复")
        
    except Exception as e:
        print(f"❌ 导入失败: {e}")

def main():
    parser = argparse.ArgumentParser(
        prog='rss',
        description='RSS Agent CLI - 管理你的 RSS 订阅',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  rss list                      # 列出所有订阅
  rss list --category 博客       # 按分类筛选
  rss add https://example.com/feed.xml --category 科技
  rss remove "某个订阅名称"
  rss check                     # 检查所有订阅状态
  rss fetch "DIYgod" --limit 3  # 获取某订阅最新3条
  rss export                    # 导出为 OPML
  rss import follow.opml        # 从 OPML 导入
        '''
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # list 命令
    list_parser = subparsers.add_parser('list', help='列出所有订阅')
    list_parser.add_argument('-c', '--category', help='按分类筛选')
    list_parser.add_argument('-v', '--verbose', action='store_true', help='显示详细信息')
    
    # add 命令
    add_parser = subparsers.add_parser('add', help='添加订阅')
    add_parser.add_argument('url', help='RSS feed URL')
    add_parser.add_argument('-n', '--name', help='自定义名称')
    add_parser.add_argument('-c', '--category', help='分类')
    add_parser.add_argument('--html-url', help='网站主页 URL')
    
    # remove 命令
    remove_parser = subparsers.add_parser('remove', help='删除订阅')
    remove_parser.add_argument('identifier', help='订阅名称或 URL')
    
    # check 命令
    check_parser = subparsers.add_parser('check', help='检查订阅健康状态')
    
    # fetch 命令
    fetch_parser = subparsers.add_parser('fetch', help='获取订阅内容')
    fetch_parser.add_argument('identifier', help='订阅名称或 URL')
    fetch_parser.add_argument('-n', '--limit', type=int, default=5, help='获取数量 (默认5)')
    fetch_parser.add_argument('-v', '--verbose', action='store_true', help='显示链接')
    
    # export 命令
    export_parser = subparsers.add_parser('export', help='导出 OPML')
    export_parser.add_argument('-o', '--output', help='输出文件名')
    
    # import 命令
    import_parser = subparsers.add_parser('import', help='导入 OPML')
    import_parser.add_argument('file', help='OPML 文件路径')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # 执行对应命令
    commands = {
        'list': cmd_list,
        'add': cmd_add,
        'remove': cmd_remove,
        'check': cmd_check,
        'fetch': cmd_fetch,
        'export': cmd_export,
        'import': cmd_import,
    }
    
    commands[args.command](args)

if __name__ == '__main__':
    main()
