import sys
import xml.etree.ElementTree as ET
import json
import requests
import os
from datetime import datetime

def parse_opml(file_path):
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        feeds = []
        
        def walk(node, category=None):
            for outline in node.findall('outline'):
                text = outline.get('text')
                xml_url = outline.get('xmlUrl')
                html_url = outline.get('htmlUrl')
                type_attr = outline.get('type')
                
                if xml_url:
                    feeds.append({
                        "name": text,
                        "xmlUrl": xml_url,
                        "htmlUrl": html_url,
                        "category": category
                    })
                
                # Nested outlines (categories)
                walk(outline, category=text if not xml_url else category)
        
        walk(root.find('body'))
        return feeds
    except Exception as e:
        return {"error": str(e)}

def check_feed(url):
    try:
        # Simple head check or get first few bytes
        resp = requests.get(url, timeout=10, headers={'User-Agent': 'OpenClaw-RSS-Agent/1.0'})
        if resp.status_code == 200:
            content_type = resp.headers.get('Content-Type', '').lower()
            is_xml = 'xml' in content_type or 'rss' in content_type or 'atom' in content_type
            # Fallback check content if type is missing
            if not is_xml:
                is_xml = resp.text.strip().startswith('<?xml') or '<rss' in resp.text[:500]
            return {"status": "ok" if is_xml else "invalid_content", "code": resp.status_code}
        return {"status": "error", "code": resp.status_code}
    except Exception as e:
        return {"status": "exception", "error": str(e)}

if __name__ == "__main__":
    action = sys.argv[1]
    if action == "parse":
        print(json.dumps(parse_opml(sys.argv[2])))
    elif action == "check":
        print(json.dumps(check_feed(sys.argv[2])))
