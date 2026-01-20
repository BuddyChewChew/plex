<?php
/**
 * PLEX INDEPENDENT SCRAPER - TIVIMATE COMPATIBLE
 *
 * Created by: BuddyChewChew
 * Discord: https://discord.gg/fnsWGDy2mm
 * Description: Generates stream links with a dynamic Plex Token
 * for use in IPTV players like TiviMate.
 */

// 1. OBFUSCATED WORKER URL
$encodedWorker = "aHR0cHM6Ly9wbGV4LmJ1ZGR5Y2hld2NoZXcud29ya2Vycy5kZXYv";
$workerUrl     = base64_decode($encodedWorker);

$plexApi   = "http://www.plex.tv/wp-json/plex/v1/mediaverse/livetv/channels/list";
$referer   = "https://www.plex.tv/live-tv-channels/";

// 2. HELPER: GET ANONYMOUS PLEX TOKEN (Fixed for GitHub Actions)
function get_plex_token($workerUrl) {
    $uuid = bin2hex(random_bytes(16));
    $tokenApi = "https://clients.plex.tv/api/v2/users/anonymous?X-Plex-Product=Plex%20Web&X-Plex-Client-Identifier=$uuid";
    
    // We route the token request THROUGH the worker to avoid GitHub IP blocks
    $proxyUrl = $workerUrl . "?url=" . urlencode($tokenApi);
    
    $ch = curl_init($proxyUrl);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
    $response = curl_exec($ch);
    curl_close($ch);
    
    $data = json_decode($response, true);
    return $data['authToken'] ?? null;
}

// 3. START FETCHING
echo "BuddyChewChew Plex Tool: Requesting Token via Proxy...\n";
$token = get_plex_token($workerUrl);

if (!$token) {
    die("Error: Worker could not fetch Plex Token. Ensure your Worker is running.\n");
}

$requestUrl = $workerUrl . "?url=" . urlencode($plexApi) . "&referer=" . urlencode($referer);
echo "Token Acquired. Connecting to Plex API...\n";

$response = file_get_contents($requestUrl);
$data = json_decode($response, true);
$cleanList = [];

if (isset($data['data']['list']) && is_array($data['data']['list'])) {
    
    $m3uContent = "#EXTM3U\n";
    
    foreach ($data['data']['list'] as $ch) {
        $title = $ch['media_title'] ?? 'Unknown';
        $genre = !empty($ch['media_categories']) ? array_values($ch['media_categories'])[0] : 'Plex';
        $logo  = $ch['media_thumb'] ?? '';
        $slug  = basename($ch['media_link']); 

        // TIVIMATE STREAM FORMAT
        $streamUrl = "https://epg.provider.plex.tv/library/parts/{$slug}/?X-Plex-Token={$token}";

        $cleanList[] = [
            'Title' => $title,
            'Genre' => $genre,
            'Logo'  => $logo,
            'Link'  => $streamUrl
        ];

        $m3uContent .= "#EXTINF:-1 channel-id=\"{$slug}\" tvg-id=\"{$slug}\" tvg-chno=\"\" tvg-name=\"{$title}\" tvg-logo=\"{$logo}\" group-title=\"{$genre}\",{$title}\n";
        $m3uContent .= "{$streamUrl}\n";
    }

    file_put_contents(__DIR__ . '/channels.json', json_encode($cleanList, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES));
    file_put_contents(__DIR__ . '/plex_channels.m3u', $m3uContent);
    
    echo "Success: Created TiviMate playlist for BuddyChewChew's project.\n";
    echo "Join us on Discord: https://discord.gg/fnsWGDy2mm\n";
} else {
    echo "Error: Failed to fetch channel data from Plex.\n";
    exit(1);
}
?>
