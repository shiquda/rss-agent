import sys
import requests
import xml.etree.ElementTree as ET
import json
import html

def fetch_feed(url, limit=5, full_content=False):
    try:
        resp = requests.get(url, timeout=15, headers={'User-Agent': 'OpenClaw-RSS-Agent/1.0'})
        if resp.status_code != 200:
            return {"error": f"HTTP {resp.status_code}"}
        
        root = ET.fromstring(resp.content)
        items = []
        
        # Namespaces
        content_ns = '{http://purl.org/rss/1.0/modules/content/}'
        atom_ns = '{http://www.w3.org/2005/Atom}'
        
        # Check if RSS 2.0
        channel = root.find('channel')
        if channel is not None:
            for item in channel.findall('item')[:limit]:
                title = item.findtext('title', 'No Title')
                link = item.findtext('link', '')
                pub_date = item.findtext('pubDate', '')
                desc = item.findtext('description', '')
                
                # Try to get full content
                content = ''
                if full_content:
                    content_elem = item.find(f'{content_ns}encoded')
                    if content_elem is not None and content_elem.text:
                        content = content_elem.text
                
                items.append({
                    "title": title,
                    "link": link,
                    "date": pub_date,
                    "summary": desc[:500] + "..." if len(desc) > 500 else desc,
                    "content": content if full_content else None
                })
        else:
            # Check if Atom
            entries = root.findall(f'{atom_ns}entry')
            for entry in entries[:limit]:
                title = entry.findtext(f'{atom_ns}title', 'No Title')
                link_node = entry.find(f'{atom_ns}link')
                link = link_node.get('href') if link_node is not None else ''
                pub_date = entry.findtext(f'{atom_ns}updated', '')
                summary = entry.findtext(f'{atom_ns}summary', '')
                
                # Try to get full content
                content = ''
                if full_content:
                    content_elem = entry.find(f'{atom_ns}content')
                    if content_elem is not None and content_elem.text:
                        content = content_elem.text
                
                if not summary and not full_content:
                    summary = entry.findtext(f'{atom_ns}content', '')
                    
                items.append({
                    "title": title,
                    "link": link,
                    "date": pub_date,
                    "summary": summary[:500] + "..." if len(summary) > 500 else summary,
                    "content": content if full_content else None
                })
                
        return {"items": items}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    url = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    print(json.dumps(fetch_feed(url, limit)))
