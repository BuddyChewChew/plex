import requests
import random
import string
import os
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

def generate_device_id():
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(24))

def get_plex_token():
    # List of various US-based IPs to rotate
    geo_ips = [
        '76.81.9.69',     # Los Angeles, CA
        '67.171.185.151', # Chicago, IL
        '76.203.9.148',    # Dallas, TX
        '24.128.21.104',   # Boston, MA
        '68.45.132.89',    # Philadelphia, PA
        '98.210.101.45',   # San Francisco, CA
        '72.14.201.12'     # Atlanta, GA
    ]
    spoof_ip = random.choice(geo_ips)
    
    url = 'https://clients.plex.tv/api/v2/users/anonymous'
    headers = {
        'X-Plex-Client-Identifier': generate_device_id(),
        'X-Plex-Product': 'Plex Web',
        'X-Plex-Version': '4.145.0',
        'X-Plex-Platform': 'Chrome',
        'X-Plex-Device': 'Linux',
        'X-Forwarded-For': spoof_ip,
        'Accept': 'application/json'
    }
    try:
        # Added a small sleep to avoid instant-hit detection
        time.sleep(random.uniform(1, 3))
        r = requests.post(url, headers=headers, timeout=15)
        return r.json().get('authToken'), spoof_ip
    except:
        return None, None

def generate_files():
    token, active_ip = get_plex_token()
    if not token:
        print("Error: Could not obtain Plex Token.")
        return
    
    print(f"Using Token: {token[:5]}... with Spoofed IP: {active_ip}")
    
    headers = {
        'X-Plex-Token': token, 
        'Accept': 'application/json',
        'X-Forwarded-For': active_ip,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    root = ET.Element("tv")
    
    # 1. Fetch Channels
    try:
        ch_res = requests.get("https://epg.provider.plex.tv/lineups/plex/channels", headers=headers, timeout=20)
        channels = ch_res.json().get("MediaContainer", {}).get("Channel", [])
    except Exception as e:
        print(f"Channel fetch error: {e}")
        return

    print(f"Processing {len(channels)} channels...")

    # 2. Fetch the actual schedule (The Grid)
    # We round to the nearest hour to match Plex's caching window
    now = datetime.utcnow()
    start_time = int(datetime(now.year, now.month, now.day, now.hour).timestamp())
    
    # Fetching in smaller 4-hour chunks is often more reliable than 6 or 12
    grid_url = f"https://epg.provider.plex.tv/grid?timespan=4&language=en&start={start_time}"
    
    try:
        time.sleep(random.uniform(2, 4))
        grid_res = requests.get(grid_url, headers=headers, timeout=30)
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
        print(f"Grid error: {e}")

    # Save logic...
    tree = ET.ElementTree(root)
    tree.write("plex_guide.xml", encoding="utf-8", xml_declaration=True)

if __name__ == "__main__":
    generate_files()
