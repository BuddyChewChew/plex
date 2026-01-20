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
    
    # We simulate different regions to force the API to give us everything
    regions_to_pull = [
        {"Accept-Language": "en-US,en;q=0.9", "X-Region": "US"},
        {"Accept-Language": "en-GB,en;q=0.9", "X-Region": "UK"},
        {"Accept-Language": "es-MX,es;q=0.9", "X-Region": "MX"},
        {"Accept-Language": "de-DE,de;q=0.9", "X-Region": "DE"},
        {"Accept-Language": "fr-FR,fr;q=0.9", "X-Region": "FR"}
    ]

    all_channels = {} # Use a dict to prevent duplicates across regions

    for region in regions_to_pull:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.plex.tv/live-tv-channels/",
            "Accept": "application/json",
            **region
        }

        try:
            print(f"Pulling data for region: {region.get('X-Region')}...")
            response = requests.get(api_url, headers=headers, timeout=20)
            data = response.json().get("data", {}).get("list", [])

            for item in data:
                m_id = item.get("media_id") or item.get("media_link", "").split("/")[-1]
                if not m_id: continue

                # AGGRESSIVE GENRE EXTRACTION
                genres = item.get("media_categories", []) or item.get("media_genre", [])
                genre_str = ", ".join(genres) if isinstance(genres, list) and genres else "General"
                
                # REGION/LANGUAGE DETECTION
                lang = item.get("media_lang") or item.get("language") or "EN"
                
                # MAP THE CHANNEL TO THE DICTIONARY
                all_channels[m_id] = {
                    "Title": item.get("media_title", "Unknown"),
                    "Genre": genre_str,
                    "Language": lang.upper(),
                    "Summary": item.get("media_summary", ""),
                    "Link": item.get("media_link", "")
                }
        except Exception as e:
            print(f"Error pulling region {region.get('X-Region')}: {e}")

    final_list = list(all_channels.values())

    # Save to JSON - matching your exact structure
    with open("plex_channels.json", "w", encoding="utf-8") as f:
        json.dump(final_list, f, indent=2, ensure_ascii=False)

    # Generate M3U8 with dynamic timestamps for GitHub tracking
    now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    m3u_content = f"#EXTM3U\n# LAST_GLOBAL_SYNC: {now_ts}\n"
    for ch in final_list:
        m3u_content += f'#EXTINF:-1 group-title="{ch["Genre"]}",{ch["Title"]}\n{ch["Link"]}\n'

    with open("plex_master.m3u8", "w", encoding="utf-8") as f:
        f.write(m3u_content)
    
    print(f"Global sync complete. Found {len(final_list)} unique channels.")

if __name__ == "__main__":
    run_sync()
