<?php
/**
 * PLEX INDEPENDENT SCRAPER - TIVIMATE COMPATIBLE
 *
 * Created by: BuddyChewChew
 * Discord: https://discord.gg/fnsWGDy2mm
 * Description: Hybrid fetcher to bypass Worker Method restrictions.
 */

// 1. OBFUSCATED WORKER URL
$encodedWorker = "aHR0cHM6Ly9wbGV4LmJ1ZGR5Y2hld2NoZXcud29ya2Vycy5kZXYv";
$workerUrl     = base64_decode($encodedWorker);

$plexApi = "http://www.plex.tv/wp-json/plex/v1/mediaverse/livetv/channels/list";

/**
 * HELPER: GET PLEX TOKEN
 * Fetches directly from GitHub to ensure POST method is preserved.
 */
function get_token_direct() {
    $uuid = bin2hex(random_bytes(16));
    $url = "https://clients.plex.tv/api/v2/users/anonymous?X-Plex-Product=Plex%20Web&X-Plex-Client-Identifier=$uuid";
    
    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_POST, 1);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_HTTPHEADER, ['Accept: application/json']);
    curl_setopt($ch, CURLOPT_USERAGENT, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) BuddyChewChew/1.1');
    
    $response = curl_exec($ch);
    $data = json_decode($response, true);
    return $data['authToken'] ?? null;
}

/**
 * HELPER: FETCH CHANNEL LIST
 * Uses your Worker which we know works for GET requests.
 */
function fetch_list_via_worker($workerUrl, $targetUrl) {
    $proxyUrl = rtrim($workerUrl, '/') . "/?url=" . urlencode($targetUrl);
    $ch = curl_init($proxyUrl);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
    $response = curl_exec($ch);
    curl_close($ch);
    return $response;
}

// 2. START PROCESS
echo "BuddyChewChew Plex Tool: Fetching Token...\n";
$token = get_token_direct();

if (!$token) {
    die("CRITICAL ERROR: Plex rejected direct Token request from GitHub. We may need to update your Cloudflare Worker JS code.\n");
}

echo "Token Acquired. Fetching Channel List via Worker...\n";
$listResponse = fetch_list_via_worker($workerUrl, $plexApi);
$data = json_decode($listResponse, true);
$cleanList = [];

if (isset($data['data']['list']) && is_array($data['data']['list'])) {
    $m3uContent = "#EXTM3U\n";
    foreach ($data['data']['list'] as $ch) {
        $title = $ch['media_title'] ?? 'Unknown';
        $genre = !empty($ch['media_categories']) ? array_values($ch['media_categories'])[0] : 'Plex';
        $logo  = $ch['media_thumb'] ?? '';
        $slug  = basename($ch['media_link']); 

        $streamUrl = "https://epg.provider.plex.tv/library/parts/{$slug}/?X-Plex-Token={$token}";

        $cleanList[] = [
            'Title' => $title, 'Genre' => $genre, 'Logo' => $logo, 'Link' => $streamUrl
        ];

        $m3uContent .= "#EXTINF:-1 channel-id=\"{$slug}\" tvg-id=\"{$slug}\" tvg-logo=\"{$logo}\" group-title=\"{$genre}\",{$title}\n";
        $m3uContent .= "{$streamUrl}\n";
    }

    file_put_contents(__DIR__ . '/channels.json', json_encode($cleanList, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES));
    file_put_contents(__DIR__ . '/plex_channels.m3u', $m3uContent);
    echo "Success: Created playlist. Discord: https://discord.gg/fnsWGDy2mm\n";
} else {
    echo "Worker Response: " . substr($listResponse, 0, 100) . "\n";
    die("Error: Failed to parse channel list from Worker.\n");
}
?>
