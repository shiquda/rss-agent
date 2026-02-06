#!/usr/bin/env python3
"""
Convert RSS feeds JSON to standard OPML format.
Usage: python3 json_to_opml.py <input.json> [output.opml]
"""

import json
import sys
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

def json_to_opml(json_file, opml_file=None):
    """Convert RSS feeds JSON to OPML format."""
    
    # Read JSON file
    with open(json_file, 'r', encoding='utf-8') as f:
        feeds = json.load(f)
    
    # Create OPML structure
    opml = Element('opml', version='2.0')
    
    # Head section
    head = SubElement(opml, 'head')
    title = SubElement(head, 'title')
    title.text = 'RSS Subscriptions'
    date_created = SubElement(head, 'dateCreated')
    date_created.text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
    
    # Body section
    body = SubElement(opml, 'body')
    
    # Group feeds by category
    categories = {}
    for feed in feeds:
        category = feed.get('category') or '未分类'
        if category not in categories:
            categories[category] = []
        categories[category].append(feed)
    
    # Create outline elements
    for category, category_feeds in sorted(categories.items()):
        if len(categories) > 1:
            # Create category outline
            category_outline = SubElement(body, 'outline', text=category, title=category)
            parent = category_outline
        else:
            # No category grouping if only one category
            parent = body
        
        # Add feeds
        for feed in category_feeds:
            feed_attrs = {
                'type': 'rss',
                'text': feed['name'],
                'title': feed['name'],
                'xmlUrl': feed['xmlUrl']
            }
            
            if feed.get('htmlUrl'):
                feed_attrs['htmlUrl'] = feed['htmlUrl']
            
            SubElement(parent, 'outline', **feed_attrs)
    
    # Pretty print XML
    xml_str = tostring(opml, encoding='utf-8')
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent='  ', encoding='utf-8')
    
    # Remove extra blank lines
    lines = [line for line in pretty_xml.decode('utf-8').split('\n') if line.strip()]
    pretty_xml = '\n'.join(lines)
    
    # Write to file or stdout
    if opml_file:
        with open(opml_file, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)
        print(f"✅ OPML 文件已生成: {opml_file}")
        print(f"📊 总计 {len(feeds)} 个订阅源，{len(categories)} 个分类")
    else:
        print(pretty_xml)
    
    return pretty_xml

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 json_to_opml.py <input.json> [output.opml]")
        print("示例: python3 json_to_opml.py rss_feeds.json subscriptions.opml")
        sys.exit(1)
    
    json_file = sys.argv[1]
    opml_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        json_to_opml(json_file, opml_file)
    except FileNotFoundError:
        print(f"❌ 错误: 找不到文件 {json_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ 错误: JSON 格式无效 - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)
