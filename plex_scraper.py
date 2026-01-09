import requests
import random
import string
import os
import xml.etree.ElementTree as ET

def generate_device_id():
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(24))

def get_plex_token():
    url = 'https://clients.plex.tv/api/v2/users/anonymous'
    device_id = generate_device_id()
    
    # Plex now often requires these headers to be present
    headers = {
        'X-Plex-Client-Identifier': device_id,
        'X-Plex-Product': 'Plex Web',
        'X-Plex-Version': '4.145.0',
        'X-Plex-Platform': 'Chrome',
        'X-Plex-Device': 'Linux',
        'Accept': 'application/json'
    }
    
    try:
        # We use a POST request to the anonymous user endpoint
        r = requests.post(url, headers=headers, timeout=15)
        r.raise_for_status()
        data = r.json()
        token = data.get('authToken')
        if token:
            print(f"Successfully acquired token: {token[:5]}***")
        return token
    except Exception as e:
        print(f"Error getting token: {e}")
        return None

def create_epg(channels):
    root = ET.Element("tv")
    for ch in channels:
        ch_id = f"plex-{ch.get('id')}"
        channel_node = ET.SubElement(root, "channel", id=ch_id)
        ET.SubElement(channel_node, "display-name").text = ch.get("title")
        if ch.get("thumb"):
            ET.SubElement(channel_node, "icon", src=ch.get("thumb"))
    
    tree = ET.ElementTree(root)
    tree.write("plex_guide.xml", encoding="utf-8", xml_declaration=True)
    print("Successfully created plex_guide.xml")

def generate_files():
    token = get_plex_token()
    if not token:
        print("Failed to acquire token. Exiting.")
        return
    
    # Lineup endpoint
    url = "https://epg.provider.plex.tv/lineups/plex/channels"
    headers = {
        'X-Plex-Token': token,
        'Accept': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        data = response.json()
        channels = data.get("MediaContainer", {}).get("Channel", [])
    except Exception as e:
        print(f"Error fetching channels: {e}")
        return

    valid_channels = []
    repo_path = os.getenv('GITHUB_REPOSITORY', 'USER/plex')
    repo_url = f"https://raw.githubusercontent.com/{repo_path}/main"

    with open("plex.m3u8", "w") as f:
        f.write(f'#EXTM3U x-tvg-url="{repo_url}/plex_guide.xml"\n')
        
        for ch in channels:
            # Filter DRM
            if any(m.get("drm") for m in ch.get("Media", [])): 
                continue
            
            name = ch.get("title")
            ch_id = f"plex-{ch.get('id')}"
            logo = ch.get("thumb", "")
            
            try:
                # Get the stream key
                key = ch["Media"][0]["Part"][0]["key"]
                stream_url = f"https://epg.provider.plex.tv{key}?X-Plex-Token={token}"
                f.write(f'#EXTINF:-1 tvg-id="{ch_id}" tvg-logo="{logo}" group-title="Plex Live",{name}\n')
                f.write(f"{stream_url}\n")
                valid_channels.append(ch)
            except (KeyError, IndexError):
                continue
    
    print(f"Successfully created plex.m3u8 with {len(valid_channels)} channels.")
    create_epg(valid_channels)

if __name__ == "__main__":
    generate_files()
