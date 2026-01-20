import subprocess
import sys
import os
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

# --- SELF-INSTALLER FOR REQUIREMENTS ---
def install_dependencies():
    try:
        import requests
    except ImportError:
        print("Installing missing 'requests' library...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
        import requests
    return requests

# Force the script to use its own folder for all file operations
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

def run_sync():
    requests = install_dependencies()
    
    # Official Direct Plex API (No middleman/encoded strings)
    api_url = "https://www.plex.tv/wp-json/plex/v1/mediaverse/livetv/channels/list"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://www.plex.tv/live-tv-channels/",
        "Accept": "application/json"
    }

    try:
        print("Fetching latest channel data from Plex...")
        response = requests.get(api_url, headers=headers, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        raw_channels = data.get("data", {}).get("list", [])
        if not raw_channels:
            print("No channels found.")
            return

        # 1. Generate Clean JSON
        clean_data = []
        for item in raw_channels:
            clean_data.append({
                "Title": item.get("media_title"),
                "Genre": item.get("media_categories", ["General"])[0],
                "Language": item.get("media_lang"),
                "Summary": item.get("media_summary"),
                "Link": item.get("media_link"),
                "Logo": item.get("media_image")
            })
        
        with open("plex_channels.json", "w", encoding="utf-8") as f:
            json.dump(clean_data, f, indent=4, ensure_ascii=False)

        # 2. Generate M3U & XML
        m3u_lines = ["#EXTM3U"]
        root = ET.Element("tv")
        
        for item in clean_data:
            title = item["Title"]
            link = item["Link"]
            logo = item["Logo"]
            genre = item["Genre"]
            safe_id = title.replace(" ", "_").replace("&", "and")

            # M3U Entry
            m3u_lines.append(f'#EXTINF:-1 tvg-id="{safe_id}" tvg-logo="{logo}" group-title="{genre}",{title}')
            m3u_lines.append(link)

            # XML Entry
            chan_xml = ET.SubElement(root, "channel", id=safe_id)
            ET.SubElement(chan_xml, "display-name").text = title
            if logo:
                ET.SubElement(chan_xml, "icon", src=logo)

            # 24h Dummy Program
            now = datetime.now()
            start = now.strftime("%Y%m%d%H%M%S +0000")
            stop = (now + timedelta(hours=24)).strftime("%Y%m%d%H%M%S +0000")
            prog_xml = ET.SubElement(root, "programme", start=start, stop=stop, channel=safe_id)
            ET.SubElement(prog_xml, "title").text = f"Live: {title}"
            ET.SubElement(prog_xml, "desc").text = item["Summary"]

        # Write files
        with open("plex_playlist.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_lines))

        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ", level=0)
        tree.write("plex_guide.xml", encoding="utf-8", xml_declaration=True)

        print(f"Success! Updated files in {script_dir}")

    except Exception as e:
        print(f"Sync failed: {e}")

if __name__ == "__main__":
    run_sync()
