import requests
import json
import uuid
import time
import random
import logging
from typing import Optional

# ... (keep your existing imports/config like OUTPUT_DIR, USER_AGENT, REGION_MAP, TOP_REGIONS, etc.)

logger = logging.getLogger(__name__)

def get_anonymous_token(region: str = 'local') -> Optional[str]:
    """Fetch a fresh anonymous Plex token"""
    headers = {
        'Accept': 'application/json',
        'User-Agent': USER_AGENT,
        'X-Plex-Product': 'Plex Web',
        'X-Plex-Version': '4.150.0',  # Updated to recent-ish
        'X-Plex-Client-Identifier': str(uuid.uuid4()).replace('-', ''),
        'X-Plex-Platform': 'Web',
        'X-Plex-Platform-Version': 'Chrome',
    }

    x_forward_ips = {
        'us': '76.81.9.69',   # Example US proxy IP - rotate or use real residential if possible
        # Add more if you want regional spoofing
    }
    if region in x_forward_ips:
        headers['X-Forwarded-For'] = x_forward_ips[region]

    params = {
        'X-Plex-Product': 'Plex Web',
        'X-Plex-Client-Identifier': headers['X-Plex-Client-Identifier'],
    }

    for attempt in range(4):
        try:
            resp = requests.post(
                'https://clients.plex.tv/api/v2/users/anonymous',
                headers=headers,
                params=params,
                timeout=15
            )
            if resp.status_code == 429:
                wait = (2 ** attempt) * 10 + random.uniform(0, 5)
                logger.warning(f"429 on anon token - sleeping {wait:.1f}s")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            data = resp.json()
            token = data.get('authToken')
            if token:
                logger.info(f"Got anonymous token for region {region}")
                return token
        except Exception as e:
            logger.warning(f"Anon token attempt {attempt+1} failed: {e}")
            time.sleep(5)

    logger.error("Failed to get anonymous Plex token after retries")
    return None

def generate_plex_m3u():
    # Fetch the channels metadata (this is from matt huisman's repo - assumes it still has Plex data)
    channels_data_url = 'https://github.com/matthuisman/i.mjh.nz/raw/refs/heads/master/Plex/.channels.json.gz'
    data = fetch_url(channels_data_url, is_json=True, is_gzipped=True, headers={'User-Agent': USER_AGENT})
    if not data or 'channels' not in data:
        logger.error("Failed to load Plex channels metadata")
        return

    # Get unique regions from the data
    found_regions = set()
    for ch in data['channels'].values():
        found_regions.update(ch.get('regions', []))

    regions = list(found_regions) + ['all']

    for region in regions:
        token = get_anonymous_token(region=region if region != 'all' else 'us')  # default to US for 'all'
        if not token:
            logger.error(f"Skipping region {region} - no token")
            continue

        output_lines = []
        epg_url = f"https://github.com/matthuisman/i.mjh.nz/raw/master/Plex/{region}.xml.gz"
        output_lines.append(f'#EXTM3U url-tvg="{epg_url}"\n')

        count = 0
        for c_id, ch in data['channels'].items():
            if region == 'all' or region in ch.get('regions', []):
                # Build direct Plex stream URL with fresh anon token
                # Note: The actual key/path comes from Plex API; this is a placeholder based on common patterns
                # If matt's json doesn't have the /library/parts/... key, you may need to query epg.provider.plex.tv per channel
                # For simplicity, assuming matt's data proxies or has compatible IDs
                stream_url = f"https://epg.provider.plex.tv/library/parts/{c_id}/?X-Plex-Token={token}"

                # Alternative common pattern if above fails (test in browser):
                # stream_url = f"https://epg.provider.plex.tv/hls/{c_id}/master.m3u8?X-Plex-Token={token}"

                extinf = format_extinf(
                    c_id, c_id, ch.get('chno'), ch['name'], ch['logo'],
                    "Plex Free", ch['name']
                )
                output_lines.extend([extinf, stream_url + "\n"])
                count += 1

        if count > 0:
            filename = f"plex_{region}.m3u"
            write_m3u_file(filename, "".join(output_lines))
            logger.info(f"Wrote {filename} with {count} channels")
        else:
            logger.warning(f"No channels for region {region}")

# In your __main__:
# generate_plex_m3u()
