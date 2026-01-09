# 2. Fetch the actual schedule (The kptv-fast way)
    print("Fetching guide data via Genre blocks...")
    try:
        # Instead of one big grid request, we use the specific EPG provider parameters
        # found in the kptv-fast source to trick Plex into thinking we are the Web App.
        now_ts = int(datetime.now().timestamp())
        
        # We target a 6-hour window (more reliable than 12)
        # kptv-fast uses these specific params to ensure the grid isn't empty
        grid_params = {
            'timespan': '6',
            'language': 'en',
            'start': str(now_ts),
            'X-Plex-Token': token
        }
        
        # kptv-fast often hits this endpoint for the specific lineup
        grid_url = "https://epg.provider.plex.tv/grid"
        grid_res = requests.get(grid_url, headers=headers, params=grid_params, timeout=30)
        
        if grid_res.status_code != 200:
            print(f"Grid request failed: {grid_res.status_code}")
            return

        channels_data = grid_res.json().get("MediaContainer", {}).get("Channel", [])
        program_count = 0
        
        for g_ch in channels_data:
            ch_id = f"plex-{g_ch.get('id')}"
            for prog in g_ch.get("Program", []):
                # Using UTC for the timestamp conversion (Crucial for GitHub Actions)
                start_ts = int(prog.get("start"))
                stop_ts = start_ts + int(prog.get("duration"))
                
                start_xml = datetime.utcfromtimestamp(start_ts).strftime('%Y%m%d%H%M%S +0000')
                stop_xml = datetime.utcfromtimestamp(stop_ts).strftime('%Y%m%d%H%M%S +0000')
                
                p_node = ET.SubElement(root, "programme", start=start_xml, stop=stop_xml, channel=ch_id)
                ET.SubElement(p_node, "title").text = prog.get("title")
                if prog.get("summary"):
                    ET.SubElement(p_node, "desc").text = prog.get("summary")
                program_count += 1
                
        print(f"Successfully added {program_count} programs using kptv-fast logic.")
