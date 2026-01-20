import subprocess
import sys
import os
import json
import traceback
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

# --- CONFIGURATION ---
GITHUB_USER = "BuddyChewChew"
REPO_NAME = "plex"
BRANCH = "main"
EPG_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/{BRANCH}/plex_tool/plex_guide.xml"

def install_dependencies():
    try:
        import requests
    except ImportError:
        print("Installing 'requests' library...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
        import requests
    return requests

def run_sync():
    requests = install_dependencies()
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if not os.path.exists(current_dir):
        os.makedirs(current_dir)
    os.chdir(current_dir)

    api_url = "https://www.plex.tv/wp-json/plex/v1/mediaverse/livetv/channels/list"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://www.plex.tv/live-tv-channels/",
        "Accept": "application/json"
    }

    try:
        print(f"Connecting to Plex API...")
        response = requests.get(api_url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        raw_channels = data.get("data", {}).get("list", [])
        if not raw_channels:
            print("No channels found.")
            return

        clean_data = []
        for item in raw_channels:
            # Format Genre: Convert list ["Genre1", "Genre2"] to "Genre1, Genre2"
            cats = item.get("media_categories", [])
            genre_str = ", ".join(cats) if isinstance(cats, list) and cats else "General"
            
            # Extract Logo and Language
            logo_url = item.get("media_image", "")
            language = item.get("media_lang", "EN")
            m_id = item.get("media_id") or item.get("media_title", "unknown").replace(" ", "")

            clean_data.append({
                "Title": item.get("media_title", "Unknown Channel"),
                "Genre": genre_str,
                "Language": language,
                "Summary": item.get("media_summary", "No description available."),
                "Link": item.get("media_link"),
                "Logo": logo_url,
                "ID": m_id
            })
        
        # 1. Save JSON (Matches your requested format)
        with open("plex_channels.json", "w", encoding="utf-8") as f:
            json.dump(clean_data, f, indent=4, ensure_ascii=False)

        # 2. Generate M3U8 (Using Genre for group-title)
        m3u_lines = [f'#EXTM3U x-tvg-url="{EPG_URL}" url-tvg="{EPG_URL}"']
        
        # 3. Generate XMLTV
        root = ET.Element("tv", {"generator-info-name": "PlexScraper"})
        
        for ch in clean_data:
            safe_id = f"plex.{ch['ID']}"
            
            # Add to M3U8 (group-title handles the categories)
            m3u_lines.append(f'#EXTINF:-1 tvg-id="{safe_id}" tvg-logo="{ch["Logo"]}" group-title="{ch["Genre"]}",{ch["Title"]}')
            m3u_lines.append(ch["Link"])

            # Add Channel to XML
            chan_xml = ET.SubElement(root, "channel", id=safe_id)
            ET.SubElement(chan_xml, "display-name").text = ch["Title"]
            if ch["Logo"]:
                ET.SubElement(chan_xml, "icon", src=ch["Logo"])

            # 24h Program Block
            now = datetime.now()
            start = now.strftime("%Y%m%d%H%M%S +0000")
            stop = (now + timedelta(hours=24)).strftime("%Y%m%d%H%M%S +0000")
            prog_xml = ET.SubElement(root, "programme", start=start, stop=stop, channel=safe_id)
            ET.SubElement(prog_xml, "title").text = f"Live: {ch['Title']}"
            ET.SubElement(prog_xml, "desc").text = ch["Summary"]

        # Save the final files
        with open("plex_master.m3u8", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_lines))

        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ", level=0)
        tree.write("plex_guide.xml", encoding="utf-8", xml_declaration=True)

        print(f"Success! Processed {len(clean_data)} channels with Genres and Logos.")

    except Exception as e:
        print("--- CRITICAL ERROR ---")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    run_sync()
