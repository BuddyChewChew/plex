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

    # Reliable public endpoint for full metadata
    api_url = "https://www.plex.tv/wp-json/plex/v1/mediaverse/livetv/channels/list"
    
    # Common regions to aggregate
    regions = [
        {"lang": "en", "country": "US"},
        {"lang": "es", "country": "MX"},
        {"lang": "de", "country": "DE"},
        {"lang": "fr", "country": "FR"}
    ]

    all_channels = {}

    for reg in regions:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Language": f"{reg['lang']}-{reg['country']},{reg['lang']};q=0.9",
            "Referer": "https://www.plex.tv/live-tv-channels/"
        }

        try:
            print(f"Fetching {reg['country']} channels...")
            response = requests.get(api_url, headers=headers, timeout=20)
            data = response.json().get("data", {}).get("list", [])

            for item in data:
                # Use media_id or title as a unique key
                m_id = item.get("media_id") or item.get("media_title", "unk").replace(" ", "")
                if m_id in all_channels: continue

                # Deep Genre Search
                genres = item.get("media_categories", []) or item.get("media_genre", [])
                genre_str = ", ".join(genres) if isinstance(genres, list) and genres else "General"
                
                # High quality logo
                logo = item.get("media_image") or ""
                
                all_channels[m_id] = {
                    "Title": item.get("media_title", "Unknown"),
                    "Genre": genre_str,
                    "Language": reg['country'],
                    "Summary": item.get("media_summary", ""),
                    "Link": item.get("media_link", ""),
                    "Logo": logo,
                    "ID": m_id
                }
        except Exception as e:
            print(f"Region {reg['country']} failed: {e}")

    final_list = list(all_channels.values())

    # Save JSON matching your desired structure
    with open("plex_channels.json", "w", encoding="utf-8") as f:
        json.dump(final_list, f, indent=2, ensure_ascii=False)

    # Save M3U8 with Logos and Genres
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    m3u_lines = [f"#EXTM3U\n# TOTAL_CHANNELS: {len(final_list)}\n# LAST_SYNC: {ts}"]
    
    for ch in final_list:
        m3u_lines.append(f'#EXTINF:-1 tvg-id="{ch["ID"]}" tvg-logo="{ch["Logo"]}" group-title="{ch["Genre"]}",{ch["Title"]}')
        m3u_lines.append(ch["Link"])

    with open("plex_master.m3u8", "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines))
    
    print(f"Success! Found {len(final_list)} unique channels.")

if __name__ == "__main__":
    run_sync()
