<?php
/**
 * PLEX INDEPENDENT SCRAPER - TIVIMATE COMPATIBLE
 *
 * Created by: BuddyChewChew
 * Discord: https://discord.gg/fnsWGDy2mm
 * Description: Generates stream links with a dynamic Plex Token.
 */

// 1. OBFUSCATED WORKER URL
$encodedWorker = "aHR0cHM6Ly9wbGV4LmJ1ZGR5Y2hld2NoZXcud29ya2Vycy5kZXYv";
$workerUrl     = base64_decode($encodedWorker);
$plexApi       = "http://www.plex.tv/wp-json/plex/v1/mediaverse/livetv/channels/list";

/**
 * HELPER: FETCH VIA WORKER
 * Tells the worker which method to use via query parameter.
 */
function fetch_via_worker($workerUrl, $targetUrl, $method = 'GET') {
    $proxyUrl = rtrim($workerUrl, '/') . "/?url=" . urlencode($targetUrl) . "&method=" . $method;
    
    $ch = curl_init($proxyUrl);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
    curl_setopt($ch, CURLOPT_USERAGENT, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)');
    
    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    return ($httpCode === 200) ? $response : null;
}

// 2. GET FRESH TOKEN
echo "BuddyChewChew Plex Tool: Requesting Token via Method-Override...\n";
$uuid = bin2hex(random_bytes(16));
$tokenApi = "https://clients.plex.tv/api/v2/users/anonymous?X-Plex-Product=Plex%20Web&X-Plex-Client-Identifier=$uuid";

$tokenResponse = fetch_via_worker($workerUrl, $tokenApi, 'POST');
$tokenData = json_decode($tokenResponse, true);
$token = $tokenData['authToken'] ?? null;

if (!$token) {
    echo "Worker Error Output: " . htmlspecialchars(substr($tokenResponse, 0, 150)) . "\n";
    die("CRITICAL ERROR: Failed to acquire Token. Verify Worker script is updated.\n");
}

echo "Token Acquired. Fetching Channels...\n";

// 3. GET CHANNEL LIST
$listResponse = fetch_via_worker($workerUrl, $plexApi, 'GET');
$data = json_decode($listResponse, true);
$cleanList = [];

if (isset($data['data']['list']) && is_array($data['data']['list'])) {
    $m3uContent = "#EXTM3U\n";
    foreach ($data['data']['list'] as $ch) {
        $title = $ch['media_title'] ?? 'Unknown';
        $logo  = $ch['media_thumb'] ?? '';
        $slug  = basename($ch['media_link']); 
        $genre = !empty($ch['media_categories']) ? array_values($ch['media_categories'])[0] : 'Plex';

        $streamUrl = "https://epg.provider.plex.tv/library/parts/{$slug}/?X-Plex-Token={$token}";

        $cleanList[] = [
            'Title' => $title, 'Genre' => $genre, 'Logo' => $logo, 'Link' => $streamUrl
        ];

        $m3uContent .= "#EXTINF:-1 channel-id=\"{$slug}\" tvg-id=\"{$slug}\" tvg-chno=\"\" tvg-name=\"{$title}\" tvg-logo=\"{$logo}\" group-title=\"{$genre}\",{$title}\n";
        $m3uContent .= "{$streamUrl}\n";
    }

    file_put_contents(__DIR__ . '/channels.json', json_encode($cleanList, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES));
    file_put_contents(__DIR__ . '/plex_channels.m3u', $m3uContent);
    
    echo "Success! Created TiviMate playlist and channels.json\n";
    echo "Discord: https://discord.gg/fnsWGDy2mm\n";
} else {
    die("Error: Failed to parse channel data.\n");
}
?>
