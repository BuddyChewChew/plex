import subprocess
import sys
import os
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

# --- CONFIGURATION ---
# Change these if you rename your repo or branch
GITHUB_USER = "BuddyChewChew"
REPO_NAME = "plex"
BRANCH = "main"
EPG_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/{BRANCH}/plex_tool/plex_guide.xml"

def install_dependencies():
    """Self-installs 'requests' if not present."""
    try:
        import requests
    except ImportError:
        print("Installing 'requests' library...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
        import requests
    return requests

# Ensure the script works relative to its own folder
base_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(base_dir)

def run_sync():
    requests = install_dependencies()
    api_url = "https://www.plex.tv/wp-json/plex/v1/mediaverse/livetv/channels/list"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://www.plex.tv/live-tv-channels/"
    }

    try:
        print(f"Connecting to Plex API...")
        response = requests.get(api_url, headers=headers, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        raw_channels = data.get("data", {}).get("list", [])
        if not raw_channels:
            print("No channels found.")
            return

        # 1. PROCESS DATA & CREATE JSON
        clean_data = []
        for item in raw_channels:
            clean_data.append({
                "Title": item.get("media_title"),
                "Category": item.get("media_categories", ["General"])[0],
                "Summary": item.get("media_summary", ""),
                "Link": item.get("media_link"),
                "Logo": item.get("media_image"),
                "ID": item.get("media_id")
            })
        
        with open("plex_channels.json", "w", encoding="utf-8") as f:
            json.dump(clean_data, f, indent=4, ensure_ascii=False)

        # 2. GENERATE MASTER M3U8 (With Categories and EPG Header)
        # We include both x-tvg-url and url-tvg for maximum player compatibility
        m3u_lines = [f'#EXTM3U x-tvg-url="{EPG_URL}" url-tvg="{EPG_URL}"']
        
        # 3. GENERATE XMLTV EPG
        root = ET.Element("tv")
        
        for ch in clean_data:
            safe_id = f"plex.{ch['ID']}"
            
            # M3U8 Line with group-title for categorization
            m3u_lines.append(f'#EXTINF:-1 tvg-id="{safe_id}" tvg-logo="{ch["Logo"]}" group-title="{ch["Category"]}",{ch["Title"]}')
            m3u_lines.append(ch["Link"])

            # XMLTV Channel
            chan_xml = ET.SubElement(root, "channel", id=safe_id)
            ET.SubElement(chan_xml, "display-name").text = ch["Title"]
            if ch["Logo"]:
                ET.SubElement(chan_xml, "icon", src=ch["Logo"])

            # 24h Placeholder Program
            now = datetime.now()
            start = now.strftime("%Y%m%d%H%M%S +0000")
            stop = (now + timedelta(hours=24)).strftime("%Y%m%d%H%M%S +0000")
            prog_xml = ET.SubElement(root, "programme", start=start, stop=stop, channel=safe_id)
            ET.SubElement(prog_xml, "title").text = f"Live: {ch['Title']}"
            ET.SubElement(prog_xml, "desc").text = ch["Summary"]

        # Write files
        with open("plex_master.m3u8", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_lines))

        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ", level=0)
        tree.write("plex_guide.xml", encoding="utf-8", xml_declaration=True)

        print(f"Update Successful. Generated files in /plex_tool/")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_sync()
