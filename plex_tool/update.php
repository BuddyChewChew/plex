<?php
/**
 * PLEX INDEPENDENT SCRAPER - ANONYMOUS ONLY
 * Created by: BuddyChewChew
 * Discord: https://discord.gg/fnsWGDy2mm
 */

$encodedWorker = "aHR0cHM6Ly9wbGV4LmJ1ZGR5Y2hld2NoZXcud29ya2Vycy5kZXYv";
$workerUrl     = base64_decode($encodedWorker);
$plexApi       = "http://www.plex.tv/wp-json/plex/v1/mediaverse/livetv/channels/list";

/**
 * HELPER: FETCH VIA WORKER
 */
function fetch_via_worker($workerUrl, $targetUrl, $method = 'GET', $uuid = null) {
    $proxyUrl = rtrim($workerUrl, '/') . "/?url=" . urlencode($targetUrl) . "&method=" . $method;
    if ($uuid) $proxyUrl .= "&uuid=" . $uuid;
    
    $ch = curl_init($proxyUrl);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
    curl_setopt($ch, CURLOPT_USERAGENT, 'BuddyChewChew-Scraper/1.0');
    
    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    return ($httpCode === 200) ? $response : null;
}

// 1. GET ANONYMOUS TOKEN
echo "BuddyChewChew Plex Tool: Generating Anonymous Token via Worker...\n";
$uuid = bin2hex(random_bytes(16));
$tokenApi = "https://clients.plex.tv/api/v2/users/anonymous?X-Plex-Product=Plex%20Web&X-Plex-Client-Identifier=$uuid";

$tokenResponse = fetch_via_worker($workerUrl, $tokenApi, 'POST', $uuid);
$tokenData = json_decode($tokenResponse, true);
$token = $tokenData['authToken'] ?? null;

if (!$token) {
    echo "Worker Output: " . substr($tokenResponse, 0, 200) . "\n";
    die("CRITICAL ERROR: Anonymous Token could not be generated. Plex might be blocking the Worker IP.\n");
}

echo "Success: Anonymous Token Acquired.\n";

// 2. GET CHANNEL LIST
$listResponse = fetch_via_worker($workerUrl, $plexApi, 'GET');
$data = json_decode($listResponse, true);

if (isset($data['data']['list'])) {
    $m3u = "#EXTM3U\n";
    $jsonStore = [];

    foreach ($data['data']['list'] as $ch) {
        $title = $ch['media_title'] ?? 'Unknown';
        $logo  = $ch['media_thumb'] ?? '';
        $slug  = basename($ch['media_link']); 
        $genre = !empty($ch['media_categories']) ? array_values($ch['media_categories'])[0] : 'Plex';

        $streamUrl = "https://epg.provider.plex.tv/library/parts/{$slug}/?X-Plex-Token={$token}";

        $jsonStore[] = ['Title' => $title, 'Genre' => $genre, 'Logo' => $logo, 'Link' => $streamUrl];
        $m3u .= "#EXTINF:-1 channel-id=\"{$slug}\" tvg-id=\"{$slug}\" tvg-logo=\"{$logo}\" group-title=\"{$genre}\",{$title}\n{$streamUrl}\n";
    }

    file_put_contents(__DIR__ . '/channels.json', json_encode($jsonStore, JSON_PRETTY_PRINT));
    file_put_contents(__DIR__ . '/plex_channels.m3u', $m3u);
    echo "Success! Playlist and JSON updated.\n";
} else {
    die("Error: Could not retrieve channels.\n");
}
?>
