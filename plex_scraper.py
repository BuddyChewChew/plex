import requests
import random
import string
import time
import os

def generate_device_id():
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(24))

def get_plex_token():
    url = 'https://clients.plex.tv/api/v2/users/anonymous'
    params = {'X-Plex-Client-Identifier': generate_device_id(), 'X-Plex-Product': 'Plex Web'}
    try:
        r = requests.post(url, params=params, timeout=10)
        return r.json().get('authToken')
    except: return None

def generate_m3u():
    token = get_plex_token()
    if not token: return
    
    # Plex EPG Endpoint
    url = "https://epg.provider.plex.tv/lineups/plex/channels"
    params = {"X-Plex-Token": token}
    
    response = requests.get(url, params=params).json()
    channels = response.get("MediaContainer", {}).get("Channel", [])

    with open("plex.m3u8", "w") as f:
        f.write("#EXTM3U\n")
        # You can add a static EPG link here if you have an XMLTV provider
        f.write(f'#EXT-X-SESSION-DATA:ID="EPG",VALUE="https://raw.githubusercontent.com/{os.getenv("GITHUB_REPOSITORY")}/main/plex.m3u8"\n')
        
        for ch in channels:
            # Skip DRM
            if any(m.get("drm") for m in ch.get("Media", [])): continue
            
            name = ch.get("title")
            ch_id = ch.get("id")
            logo = ch.get("thumb", "")
            group = "Plex Live"
            
            # Extract stream key
            try:
                key = ch["Media"][0]["Part"][0]["key"]
                stream_url = f"https://epg.provider.plex.tv{key}?X-Plex-Token={token}"
                
                f.write(f'#EXTINF:-1 tvg-id="{ch_id}" tvg-logo="{logo}" group-title="{group}",{name}\n')
                f.write(f'{stream_url}\n')
            except: continue

if __name__ == "__main__":
    generate_m3u()
