import subprocess
import sys
import os
import json
import traceback
from datetime import datetime

def install_dependencies():
    try:
        import requests
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
        import requests
    return requests

def run_sync():
    requests = install_dependencies()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if not os.path.exists(current_dir): os.makedirs(current_dir)
    os.chdir(current_dir)

    api_url = "https://www.plex.tv/wp-json/plex/v1/mediaverse/livetv/channels/list"
    
    # Simulating different regions to get global data
    regions = [
        {"Accept-Language": "en-US,en;q=0.9", "X-Region": "US"},
        {"Accept-Language": "es-MX,es;q=0.9", "X-Region": "MX"},
        {"Accept-Language": "de-DE,de;q=0.9", "X-Region": "DE"}
    ]

    all_channels = {}

    for reg in regions:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.plex.tv/live-tv-channels/",
            "Accept": "application/json",
            **reg
        }

        try:
            print(f"Pulling {reg['X-Region']}...")
            response = requests.get(api_url, headers=headers, timeout=20)
            data = response.json().get("data", {}).get("list", [])

            for item in data:
                m_id = item.get("media_id") or item.get("media_title", "").replace(" ", "")
                if not m_id: continue

                # Genre Extraction
                cats = item.get("media_categories", []) or item.get("media_genre", [])
                genre_str = ", ".join(cats) if isinstance(cats, list) and cats else "General"
                
                # Language
                lang = item.get("media_lang") or item.get("language") or "EN"

                all_channels[m_id] = {
                    "Title": item.get("media_title", "Unknown"),
                    "Genre": genre_str,
                    "Language": lang.upper(),
                    "Summary": item.get("media_summary", ""),
                    "Link": item.get("media_link", ""),
                    "Logo": item.get("media_image", ""),
                    "ID": m_id
                }
        except:
            continue

    final_list = list(all_channels.values())

    # Save JSON
    with open("plex_channels.json", "w", encoding="utf-8") as f:
        json.dump(final_list, f, indent=2, ensure_ascii=False)

    # Save M3U8 with timestamp to force update
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    m3u_lines = [f"#EXTM3U\n# LAST_SYNC: {ts}"]
    for ch in final_list:
        m3u_lines.append(f'#EXTINF:-1 tvg-id="{ch["ID"]}" tvg-logo="{ch["Logo"]}" group-title="{ch["Genre"]}",{ch["Title"]}')
        m3u_lines.append(ch["Link"])

    with open("plex_master.m3u8", "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines))
    
    print(f"Done. Found {len(final_list)} unique channels.")

if __name__ == "__main__":
    run_sync()
