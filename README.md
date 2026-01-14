# Plex Free Channels M3U Playlists

Daily auto-updated M3U playlists for **free, ad-supported Plex Live TV channels** using anonymous access (no Plex account needed).

**Important Warnings (January 2026)**
- These are **free FAST channels** only (news, movies, lifestyle, music, etc.) — **no premium/Plex Pass content**.
- Limited to ~100–500 channels depending on region/day (mostly global, but US-heavy).
- **Geo-restricted** — many channels only work in the US or specific countries (use a US VPN if outside supported regions).
- Anonymous tokens refresh every 8 hours — if streams stop after ~12–24 hours, **reload/refresh the playlist** in your player.
- EPG (guide data) is pulled from Matt Huisman's repo (thanks!): `url-tvg="https://github.com/matthuisman/i.mjh.nz/raw/master/Plex/{region}.xml.gz"`.
- Streams may 403/expire — this is Plex limiting anonymous/shared use.

**Playlist Generator Status**  
[![Generate Plex Playlists](https://github.com/BuddyChewChew/plex/actions/workflows/generate-playlists.yml/badge.svg)](https://github.com/BuddyChewChew/plex/actions/workflows/generate-playlists.yml)  
![Last Update](https://img.shields.io/github/last-commit/BuddyChewChew/plex?label=Last%20Playlist%20Update&color=brightgreen)

Playlists regenerate **every 8 hours** with fresh anonymous tokens for better uptime.

### Available Countries / Regions
These are the main regions with dedicated channel lists and EPG from the source data. Add the raw URL for your preferred region (or "all" for a combined list).

| Country/Region       | Group Title in Player | Approx. Channels | Raw M3U URL (copy-paste into player) |
|----------------------|-----------------------|------------------|--------------------------------------|
| All Regions          | Mixed by country     | 300+            | https://raw.githubusercontent.com/BuddyChewChew/plex/main/playlists/plex_all.m3u |
| United States (us)   | United States        | 200+            | https://raw.githubusercontent.com/BuddyChewChew/plex/main/playlists/plex_us.m3u |
| United Kingdom (gb)  | United Kingdom       | 100+            | https://raw.githubusercontent.com/BuddyChewChew/plex/main/playlists/plex_gb.m3u |
| Canada (ca)          | Canada               | 100+            | https://raw.githubusercontent.com/BuddyChewChew/plex/main/playlists/plex_ca.m3u |
| Australia (au)       | Australia            | 50–150          | https://raw.githubusercontent.com/BuddyChewChew/plex/main/playlists/plex_au.m3u |
| New Zealand (nz)     | New Zealand          | 50–100          | https://raw.githubusercontent.com/BuddyChewChew/plex/main/playlists/plex_nz.m3u |
| Spain (es)           | Spain                | 50+             | https://raw.githubusercontent.com/BuddyChewChew/plex/main/playlists/plex_es.m3u |
| France (fr)          | France               | 50+             | https://raw.githubusercontent.com/BuddyChewChew/plex/main/playlists/plex_fr.m3u |
| Mexico (mx)          | Mexico               | 50+             | https://raw.githubusercontent.com/BuddyChewChew/plex/main/playlists/plex_mx.m3u |

**Notes on regions**:
- Channels in each file are grouped by country name (e.g., all in `plex_us.m3u` appear under "United States" in your player).
- "All Regions" groups channels by their primary country (or "Global / Other" if no region tag).
- If a region file has 0 channels or errors, it may be due to Plex changes/DMCA impacts on source data — check the Actions logs in this repo.

### How to Add to Your IPTV Player
1. **TiviMate** (recommended for Android TV/Firestick):
   - Open TiviMate → Playlists → Add Playlist → M3U Playlist
   - Choose "Remote Playlist" → Enter the raw URL (e.g., for US: paste the plex_us.m3u link)
   - Name it (e.g., "Plex Free US") → Save
   - Go to Settings → EPG → it auto-loads from the url-tvg header

2. **IPTV Smarters Pro / GSE Smart IPTV**:
   - Add Playlist → M3U URL → Paste the raw link
   - Set name and enable EPG (auto-detects url-tvg)

3. **VLC** (desktop/mobile):
   - Media → Open Network Stream → Paste the raw URL
   - EPG may need manual setup in VLC settings (less ideal for live TV)

4. **Other players** (OTT Navigator, Perfect Player, etc.):
   - Look for "Add M3U URL" or "Remote Playlist" → paste raw link
   - Refresh/EPG update interval: Set to 6–12 hours for best results

**Tips**:
- Use a **US VPN** for maximum channels (Plex free content is IP-based).
- If streams fail: Reload playlist → or try a different region.
- For issues: Check repo Actions tab for generation logs.

Enjoy free Plex Live TV!
