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
        'X-Forwarded-For': '85.254.181.50',
        'Accept': 'application/json'
    }
    try:
        r = requests.post(url, headers=headers, timeout=15)
        return r.json().get('authToken')
    except:
        return None

def generate_files():
    token = get_plex_token()
    if not token:
        print("Error: Could not obtain Plex Token.")
        return
    
    headers = {
        'X-Plex-Token': token, 
        'Accept': 'application/json',
        'X-Forwarded-For': '85.254.181.50'
    }
    
    root = ET.Element("tv")
    
    # 1. Fetch Channels
    try:
        ch_res = requests.get("https://epg.provider.plex.tv/lineups/plex/channels", headers=headers, timeout=20)
        channels = ch_res.json().get("MediaContainer", {}).get("Channel", [])
    except Exception as e:
        print(f"Channel fetch error: {e}")
        return

    repo_path = os.getenv('GITHUB_REPOSITORY', 'USER/plex')
    repo_url = f"https://raw.githubusercontent.com/{repo_path}/main"

    print(f"Processing {len(channels)} channels...")

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
            except:
                continue

    # 2. Fetch the actual schedule (kptv-fast/Genre strategy)
    print("Fetching guide data via Grid...")
    try:
        now_ts = int(datetime.now().timestamp())
        grid_params = {
            'timespan': '6',
            'language': 'en',
            'start': str(now_ts),
            'X-Plex-Token': token
        }
        
        grid_url = "https://epg.provider.plex.tv/grid"
        grid_res = requests.get(grid_url, headers=headers, params=grid_params, timeout=30)
        
        if grid_res.status_code == 200:
            grid_data = grid_res.json().get("MediaContainer", {}).get("Channel", [])
            program_count = 0
            for g_ch in grid_data:
                ch_id = f"plex-{g_ch.get('id')}"
                for prog in g_ch.get("Program", []):
                    start_ts = int(prog.get("start"))
                    stop_ts = start_ts + int(prog.get("duration"))
                    
                    start_xml = datetime.utcfromtimestamp(start_ts).strftime('%Y%m%d%H%M%S +0000')
                    stop_xml = datetime.utcfromtimestamp(stop_ts).strftime('%Y%m%d%H%M%S +0000')
                    
                    p_node = ET.SubElement(root, "programme", start=start_xml, stop=stop_xml, channel=ch_id)
                    ET.SubElement(p_node, "title").text = prog.get("title")
                    if prog.get("summary"):
                        ET.SubElement(p_node, "desc").text = prog.get("summary")
                    program_count += 1
            print(f"Successfully added {program_count} programs.")
    except Exception as e:
        print(f"Guide fetch error: {e}")

    # 3. Save the XML
    tree = ET.ElementTree(root)
    try:
        ET.indent(tree, space="  ", level=0)
    except:
        pass 
    tree.write("plex_guide.xml", encoding="utf-8", xml_declaration=True)

if __name__ == "__main__":
    generate_files()
