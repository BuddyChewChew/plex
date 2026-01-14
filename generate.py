import requests
import gzip
import json
import os
import logging
import uuid
import time
import shutil
import random
from io import BytesIO

# --- Configuration ---
OUTPUT_DIR = "playlists"
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
REQUEST_TIMEOUT = 30

REGION_MAP = {
    'us': 'United States', 'gb': 'United Kingdom', 'ca': 'Canada',
    'de': 'Germany', 'at': 'Austria', 'ch': 'Switzerland',
    'es': 'Spain', 'fr': 'France', 'it': 'Italy', 'br': 'Brazil',
    'mx': 'Mexico', 'ar': 'Argentina', 'cl': 'Chile', 'co': 'Colombia',
    'pe': 'Peru', 'se': 'Sweden', 'no': 'Norway', 'dk': 'Denmark',
    'in': 'India', 'jp': 'Japan', 'kr': 'South Korea', 'au': 'Australia'
}

TOP_REGIONS = ['United States', 'Canada', 'United Kingdom']

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Helper Functions ---

def cleanup_output_dir():
    if os.path.exists(OUTPUT_DIR):
        logger.info(f"Cleaning up old playlists in {OUTPUT_DIR}...")
        for filename in os.listdir(OUTPUT_DIR):
            file_path = os.path.join(OUTPUT_DIR, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                logger.error(f"Failed to delete {file_path}: {e}")
    else:
        os.makedirs(OUTPUT_DIR)

def fetch_url(url, is_json=True, is_gzipped=False, headers=None, retries=3):
    headers = headers or {'User-Agent': USER_AGENT}
    for i in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            if response.status_code == 429:
                time.sleep((i + 1) * 10 + random.uniform(0, 5))
                continue
            response.raise_for_status()
            content = response.content
            if is_gzipped:
                try:
                    with gzip.GzipFile(fileobj=BytesIO(content), mode='rb') as f:
                        content = f.read().decode('utf-8')
                except:
                    content = content.decode('utf-8')
            else:
                content = content.decode('utf-8')
            return json.loads(content) if is_json else content
        except Exception as e:
            logger.warning(f"Fetch failed (attempt {i+1}): {e}")
            if i < retries - 1:
                time.sleep(5)
    return None

def write_m3u_file(filename, content):
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def format_extinf(channel_id, tvg_id, tvg_chno, tvg_name, tvg_logo, group_title, display_name):
    chno_str = str(tvg_chno) if tvg_chno and str(tvg_chno).isdigit() else ""
    return (f'#EXTINF:-1 channel-id="{channel_id}" tvg-id="{tvg_id}" tvg-chno="{chno_str}" '
            f'tvg-name="{tvg_name.replace(chr(34), chr(39))}" tvg-logo="{tvg_logo}" '
            f'group-title="{group_title.replace(chr(34), chr(39))}",{display_name.replace(",", "")}\n')

# --- Anonymous Token Fetch ---

def get_anonymous_token(region: str = 'us') -> str | None:
    headers = {
        'Accept': 'application/json',
        'User-Agent': USER_AGENT,
        'X-Plex-Product': 'Plex Web',
        'X-Plex-Version': '4.150.0',
        'X-Plex-Client-Identifier': str(uuid.uuid4()).replace('-', ''),
        'X-Plex-Platform': 'Web',
    }

    # Optional geo spoof (US bias for better channel count)
    x_forward_ips = {
        'us': '76.81.9.69',  # example US IP – replace/rotate if needed
    }
    if region in x_forward_ips and x_forward_ips[region]:
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
                logger.info(f"Got anonymous Plex token for region {region}")
                return token
        except Exception as e:
            logger.warning(f"Anon token attempt {attempt+1} failed: {e}")
            time.sleep(5)
    logger.error("Failed to get anonymous Plex token after retries")
    return None

# --- Plex Generator (main function) ---

def generate_plex_m3u():
    url = 'https://github.com/matthuisman/i.mjh.nz/raw/refs/heads/master/Plex/.channels.json.gz'
    data = fetch_url(url, is_json=True, is_gzipped=True)
    if not data or 'channels' not in data:
        logger.error("Failed to load Plex channels metadata")
        return

    found_regions = set()
    for ch in data['channels'].values():
        found_regions.update(ch.get('regions', []))

    regions = sorted(list(found_regions)) + ['all']

    for region in regions:
        token = get_anonymous_token(region=region if region != 'all' else 'us')
        if not token:
            logger.error(f"Skipping region {region} - no token")
            continue

        output_lines = [f'#EXTM3U url-tvg="https://github.com/matthuisman/i.mjh.nz/raw/master/Plex/{region}.xml.gz"\n']
        count = 0

        for c_id, ch in data['channels'].items():
            ch_regions = ch.get('regions', [])
            if region == 'all' or region in ch_regions:
                # Determine group title = just the country name
                if region != 'all':
                    # Single-region file: use this file's region as group
                    group_title = REGION_MAP.get(region.lower(), region.upper())
                else:
                    # All file: group by the channel's primary region (first one listed)
                    if ch_regions:
                        primary_region = ch_regions[0]
                        group_title = REGION_MAP.get(primary_region.lower(), primary_region.upper())
                    else:
                        group_title = "Global / Other"

                # Stream URL - using library/parts/... pattern
                # If this gives 404/403, try the alternative HLS pattern below after testing
                stream_url = f"https://epg.provider.plex.tv/library/parts/{c_id}/?X-Plex-Token={token}"

                # Alternative HLS pattern (uncomment if needed):
                # stream_url = f"https://epg.provider.plex.tv/hls/{c_id}/master.m3u8?X-Plex-Token={token}"

                extinf = format_extinf(
                    c_id, c_id, ch.get('chno'), ch['name'], ch.get('logo', ''),
                    group_title, ch['name']
                )
                output_lines.extend([extinf, stream_url + "\n"])
                count += 1

        if count > 0:
            filename = f"plex_{region}.m3u"
            write_m3u_file(filename, "".join(output_lines))
            logger.info(f"Wrote {filename} with {count} channels")
        else:
            logger.warning(f"No channels written for region {region}")

# --- Other generators (keep your originals or stubs) ---

def generate_pluto_m3u():
    pass  # ← add your original Pluto code here if you want to keep it

# ... add Samsung, Roku, etc. as needed ...

if __name__ == "__main__":
    cleanup_output_dir()
    generate_plex_m3u()
    # generate_pluto_m3u()  # uncomment when ready
    # ... other calls ...
    logger.info("Playlist generation complete.")
