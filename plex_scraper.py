import requests
import random
import string
import os
import xml.etree.ElementTree as ET
from datetime import datetime

def generate_device_id():
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(24))

def get_plex_token():
    url = 'https://clients.plex.tv/api/v2/users/anonymous'
    headers = {
        'X-Plex-Client-Identifier': generate_device_id(),
        'X-Plex-Product': 'Plex Web',
        'X-Plex-Version': '4.145.0',
        'X-Plex-Platform': 'Chrome',
        'X-Plex-Device': 'Linux',
        'Accept': 'application/json'
    }
    try:
        r = requests.post(url, headers=headers, timeout=15)
        return r.json().get('authToken')
    except: return None

def generate_files():
    token = get_plex_token()
    if not token: return
    
    headers = {'X-Plex-Token': token, 'Accept': 'application/json'}
    
    # 1. Fetch Channels
    try:
        ch_res = requests.get("https://epg.provider.plex.tv/lineups/plex/channels", headers=headers, timeout=20)
        channels = ch_res.json().get("MediaContainer", {}).get("Channel", [])
    except: return

    root = ET.Element("tv")
    valid_ids = []
    
    # Create the .m3u8 and the <channel> nodes in XML
    repo_path = os.getenv('GITHUB_REPOSITORY', 'USER/plex')
    repo_url = f"https://raw.githubusercontent.com/{repo_path}/main"

    with open("plex.m3u8", "w") as f:
        f.write(f'#EXTM3U x-tvg-url="{repo_url}/plex_guide.xml"\n')
        for ch in channels:
            if any(m.get("drm") for m in ch.get("Media", [])): continue
            ch_id = f"plex-{ch.get('id')}"
            name = ch.get("title")
            logo = ch.get("thumb", "")
            try:
                key = ch["Media"][0]["Part"][0]["key"]
                stream_url = f"https://epg.provider.plex.tv{key}?X-Plex-Token={token}"
                f.write(f'#EXTINF:-1 tvg-id="{ch_id}" tvg-logo="{logo}" group-title="Plex Live",{name}\n{stream_url}\n')
                
                c_node = ET.SubElement(root, "channel", id=ch_id)
                ET.SubElement(c_node, "display-name").text = name
                if logo: ET.SubElement(c_node, "icon", src=logo)
                valid_ids.append(ch.get('id'))
            except: continue

    # 2. Fetch the actual schedule (The missing part!)
    try:
        # Increase timespan to 12 hours for a fuller guide
        grid_url = "https://epg.provider.plex.tv/grid?timespan=12&language=en"
        grid_res = requests.get(grid_url, headers=headers, timeout=25)
        grid_data = grid_res.json().get("MediaContainer", {}).get("Channel", [])
        
        for g_ch in grid_data:
            ch_id = f"plex-{g_ch.get('id')}"
            for prog in g_ch.get("Program", []):
                start = datetime.fromtimestamp(int(prog.get("start"))).strftime('%Y%m%d%H%M%S +0000')
                stop = datetime.fromtimestamp(int(prog.get("start")) + int(prog.get("duration"))).strftime('%Y%m%d%H%M%S +0000')
                
                p_node = ET.SubElement(root, "programme", start=start, stop=stop, channel=ch_id)
                ET.SubElement(p_node, "title").text = prog.get("title")
                if prog.get("summary"):
                    ET.SubElement(p_node, "desc").text = prog.get("summary")
    except Exception as e:
        print(f"Guide fetch error: {e}")

    # 3. Save it
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ", level=0) # Make it readable
    tree.write("plex_guide.xml", encoding="utf-8", xml_declaration=True)

if __name__ == "__main__":
    generate_files()
