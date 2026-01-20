<?php
/**
 * PLEX INDEPENDENT SCRAPER - TIVIMATE COMPATIBLE
 *
 * Created by: BuddyChewChew
 * Discord: https://discord.gg/fnsWGDy2mm
 */

$encodedWorker = "aHR0cHM6Ly9wbGV4LmJ1ZGR5Y2hld2NoZXcud29ya2Vycy5kZXYv";
$workerUrl     = base64_decode($encodedWorker);
$plexApi       = "http://www.plex.tv/wp-json/plex/v1/mediaverse/livetv/channels/list";

function fetch_via_worker($workerUrl, $targetUrl, $method = 'GET') {
    $proxyUrl = rtrim($workerUrl, '/') . "/?url=" . urlencode($targetUrl);
    $ch = curl_init($proxyUrl);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
    curl_setopt($ch, CURLOPT_USERAGENT, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) BuddyChewChew/1.1');
    
    if ($method === 'POST') {
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, ""); // Crucial for Plex Token
    }

    $response = curl_exec($ch);
    curl_close($ch);
    return $response;
}

// 1. GET TOKEN
echo "BuddyChewChew Plex Tool: Requesting Token via Universal Worker...\n";
$uuid = bin2hex(random_bytes(16));
$tokenApi = "https://clients.plex.tv/api/v2/users/anonymous?X-Plex-Product=Plex%20Web&X-Plex-Client-Identifier=$uuid";

$tokenResponse = fetch_via_worker($workerUrl, $tokenApi, 'POST');
$tokenData = json_decode($tokenResponse, true);
$token = $tokenData['authToken'] ?? null;

if (!$token) {
    echo "Worker Response Preview: " . substr($tokenResponse, 0, 100) . "\n";
    die("CRITICAL ERROR: Worker could not fetch Token. Verify Worker deployment.\n");
}

// 2. GET CHANNELS
echo "Token Acquired. Fetching Channels...\n";
$listResponse = fetch_via_worker($workerUrl, $plexApi, 'GET');
$data = json_decode($listResponse, true);

if (isset($data['data']['list'])) {
    $m3u = "#EXTM3U\n";
    foreach ($data['data']['list'] as $ch) {
        $title = $ch['media_title'] ?? 'Unknown';
        $logo  = $ch['media_thumb'] ?? '';
        $slug  = basename($ch['media_link']); 
        $genre = !empty($ch['media_categories']) ? array_values($ch['media_categories'])[0] : 'Plex';

        $streamUrl = "https://epg.provider.plex.tv/library/parts/{$slug}/?X-Plex-Token={$token}";

        $m3u .= "#EXTINF:-1 channel-id=\"{$slug}\" tvg-id=\"{$slug}\" tvg-logo=\"{$logo}\" group-title=\"{$genre}\",{$title}\n";
        $m3u .= "{$streamUrl}\n";
    }

    file_put_contents(__DIR__ . '/plex_channels.m3u', $m3u);
    echo "Success! Playlist updated. Join us on Discord: https://discord.gg/fnsWGDy2mm\n";
} else {
    die("Error: Could not parse channel list.\n");
}
?>
