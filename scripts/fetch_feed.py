import sys
import requests
import xml.etree.ElementTree as ET
import json
import html

def fetch_feed(url, limit=5):
    try:
        resp = requests.get(url, timeout=15, headers={'User-Agent': 'OpenClaw-RSS-Agent/1.0'})
        if resp.status_code != 200:
            return {"error": f"HTTP {resp.status_code}"}
        
        root = ET.fromstring(resp.content)
        items = []
        
        # Check if RSS 2.0
        channel = root.find('channel')
        if channel is not None:
            for item in channel.findall('item')[:limit]:
                title = item.findtext('title', 'No Title')
                link = item.findtext('link', '')
                pub_date = item.findtext('pubDate', '')
                desc = item.findtext('description', '')
                items.append({
                    "title": title,
                    "link": link,
                    "date": pub_date,
                    "summary": desc[:500] + "..." if len(desc) > 500 else desc
                })
        else:
            # Check if Atom
            entries = root.findall('{http://www.w3.org/2005/Atom}entry')
            for entry in entries[:limit]:
                title = entry.findtext('{http://www.w3.org/2005/Atom}title', 'No Title')
                link_node = entry.find('{http://www.w3.org/2005/Atom}link')
                link = link_node.get('href') if link_node is not None else ''
                pub_date = entry.findtext('{http://www.w3.org/2005/Atom}updated', '')
                summary = entry.findtext('{http://www.w3.org/2005/Atom}summary', '')
                if not summary:
                    summary = entry.findtext('{http://www.w3.org/2005/Atom}content', '')
                items.append({
                    "title": title,
                    "link": link,
                    "date": pub_date,
                    "summary": summary[:500] + "..." if len(summary) > 500 else summary
                })
                
        return {"items": items}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    url = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    print(json.dumps(fetch_feed(url, limit)))
