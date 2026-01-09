import requests
import random
import string
import os
import datetime
import xml.etree.ElementTree as ET

def generate_device_id():
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(24))

def get_plex_token():
    url = 'https://clients.plex.tv/api/v2/users/anonymous'
    params = {'X-Plex-Client-Identifier': generate_device_id(), 'X-Plex-Product': 'Plex Web'}
    try:
        r = requests.post(url, params=params, timeout=10)
        return r.json().get('authToken')
    except: return None

def create_epg(channels):
    """Generates a basic XMLTV file"""
    root = ET.Element("tv")
    for ch in channels:
        ch_id = f"plex-{ch.get('id')}"
        channel_node = ET.SubElement(root, "channel", id=ch_id)
        ET.SubElement(channel_node, "display-name").text = ch.get("title")
        if ch.get("thumb"):
            ET.SubElement(channel_node, "icon", src=ch.get("thumb"))
    
    tree = ET.ElementTree(root)
    tree.write("plex_guide.xml", encoding="utf-8", xml_declaration=True)

def generate_files():
    token = get_plex_token()
    if not token: return
    
    url = "https://epg.provider.plex.tv/lineups/plex/channels"
    params = {"X-Plex-Token": token}
    response = requests.get(url, params=params).json()
    channels = response.get("MediaContainer", {}).get("Channel", [])

    valid_channels = []
    with open("plex.m3u8", "w") as f:
        # Include the EPG link directly in the M3U header
        repo_url = f"https://raw.githubusercontent.com/{os.getenv('GITHUB_REPOSITORY')}/main"
        f.write(f'#EXTM3U x-tvg-url="{repo_url}/plex_guide.xml"\n')
        
        for ch in channels:
            # Skip DRM streams
            if any(m.get("drm") for m in ch.get("Media", [])): continue
            
            name = ch.get("title")
            ch_id = f"plex-{ch.get('id')}"
            logo = ch.get("thumb", "")
            
            try:
                key = ch["Media"][0]["Part"][0]["key"]
                stream_url = f"https://epg.provider.plex.tv{key}?X-Plex-Token={token}"
                f.write(f'#EXTINF:-1 tvg-id="{ch_id}" tvg-logo="{logo}" group-title="Plex Live",{name}\n')
                f.write(f"{stream_url}\n")
                valid_channels.append(ch)
            except: continue
            
    create_epg(valid_channels)

if __name__ == "__main__":
    generate_files()
