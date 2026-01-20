import subprocess
import sys
import os
import json
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

    # High-quality API used by official clients
    api_url = "https://cache.v.plex.tv/api/v2/channels"
    
    all_channels = {}
    # Locales to pull: US, Mexico, Germany, France, etc.
    locales = ["en", "es", "de", "fr", "it"]

    for locale in locales:
        params = {
            "includePremium": "1",
            "X-Plex-Language": locale
        }
        headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) PlexWeb/4.110.1"
        }

        try:
            print(f"Scraping Plex Guide for region: {locale.upper()}...")
            response = requests.get(api_url, headers=headers, params=params, timeout=15)
            data = response.json()

            for item in data:
                # Use identifier to prevent duplicates across different regional pulls
                uid = item.get("identifier") or item.get("uuid")
                if not uid: continue

                # Deep Genre Extraction
                cats = item.get("categories", [])
                genre_str = ", ".join(cats) if cats else "General"
                
                # High-Res Logos
                logo = item.get("logo") or ""
                
                # Build specific Watch Link
                slug = item.get("slug")
                link = f"https://watch.plex.tv/live-tv/channel/{slug}" if slug else ""

                all_channels[uid] = {
                    "Title": item.get("title", "Unknown"),
                    "Genre": genre_str,
                    "Language": locale.upper(),
                    "Summary": item.get("description", ""),
                    "Link": link,
                    "Logo": logo,
                    "ID": uid
                }
        except:
            continue

    final_list = list(all_channels.values())

    # Write the Final JSON (Matches your saved requirement)
    with open("plex_channels.json", "w", encoding="utf-8") as f:
        json.dump(final_list, f, indent=2, ensure_ascii=False)

    # Write the M3U8 for your IPTV players
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    m3u = [f"#EXTM3U\n# SOURCE: Official Plex Cache\n# UPDATED: {ts}"]
    for ch in final_list:
        m3u.append(f'#EXTINF:-1 tvg-id="{ch["ID"]}" tvg-logo="{ch["Logo"]}" group-title="{ch["Genre"]}",{ch["Title"]}')
        m3u.append(ch["Link"])

    with open("plex_master.m3u8", "w", encoding="utf-8") as f:
        f.write("\n".join(m3u))
    
    print(f"Complete! Found {len(final_list)} unique channels with full metadata.")

if __name__ == "__main__":
    run_sync()
