import subprocess
import sys
import os
import json
import traceback
import re
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

    # Use the Direct XML/JSON directory for full metadata (Logos/Genres)
    api_url = "https://cache.v.plex.tv/api/v2/channels?includePremium=1&X-Plex-Token="
    
    # Simulating different languages to force regional metadata
    locales = ["en", "es", "de", "fr"]
    all_channels = {}

    for lang_code in locales:
        headers = {
            "Accept": "application/json",
            "User-Agent": "Plex/1.0",
            "Accept-Language": lang_code
        }

        try:
            print(f"Syncing region: {lang_code.upper()}...")
            response = requests.get(api_url, headers=headers, timeout=20)
            data = response.json()

            for item in data:
                # Plex internal unique identifier
                m_id = item.get("identifier") or item.get("uuid")
                if not m_id: continue

                # GENRE: Pulling from the detailed category list
                cats = item.get("categories", [])
                genre_str = ", ".join(cats) if cats else "General"
                
                # LOGO: Pulling high-res images
                logo = item.get("logo") or ""
                
                # TITLE & LINK
                title = item.get("title", "Unknown")
                slug = item.get("slug")
                link = f"https://watch.plex.tv/live-tv/channel/{slug}" if slug else ""

                all_channels[m_id] = {
                    "Title": title,
                    "Genre": genre_str,
                    "Language": lang_code.upper(),
                    "Summary": item.get("description", ""),
                    "Link": link,
                    "Logo": logo,
                    "ID": m_id
                }
        except Exception as e:
            print(f"Failed {lang_code}: {e}")

    final_list = list(all_channels.values())

    # Save JSON matching your preferred style
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
    
    print(f"Success! Found {len(final_list)} unique channels with logos.")

if __name__ == "__main__":
    run_sync()
