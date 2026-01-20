<?php
/**
 * PLEX INDEPENDENT SCRAPER - TIVIMATE COMPATIBLE
 *
 * Created by: BuddyChewChew
 * Discord: https://discord.gg/fnsWGDy2mm
 */

// 1. OBFUSCATED WORKER URL
$encodedWorker = "aHR0cHM6Ly9wbGV4LmJ1ZGR5Y2hld2NoZXcud29ya2Vycy5kZXYv";
$workerUrl     = base64_decode($encodedWorker);

$plexApi   = "http://www.plex.tv/wp-json/plex/v1/mediaverse/livetv/channels/list";

/**
 * HELPER: FETCH DATA
 * Uses POST for the token and GET for the list.
 */
function fetch_plex_data($workerUrl, $targetUrl, $isPost = false) {
    $proxyUrl = rtrim($workerUrl, '/') . "/?url=" . urlencode($targetUrl);
    
    $ch = curl_init($proxyUrl);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
    curl_setopt($ch, CURLOPT_USERAGENT, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)');
    
    if ($isPost) {
        // Plex token API requires a POST request
        curl_setopt($ch, CURLOPT_CUSTOMREQUEST, "POST");
        curl_setopt($ch, CURLOPT_POSTFIELDS, ""); 
    }

    $response = curl_exec($ch);
    curl_close($ch);
    return $response;
}

// 2. START FETCHING TOKEN
echo "BuddyChewChew Plex Tool: Requesting Token (via POST)...\n";
$uuid = bin2hex(random_bytes(16));
$tokenApi = "https://clients.plex.tv/api/v2/users/anonymous?X-Plex-Product=Plex%20Web&X-Plex-Client-Identifier=$uuid";

$tokenResponse = fetch_plex_data($workerUrl, $tokenApi, true);
$tokenData = json_decode($tokenResponse, true);
$token = $tokenData['authToken'] ?? null;

if (!$token) {
    echo "Worker Error Log: " . htmlspecialchars(substr($tokenResponse, 0, 150)) . "\n";
    die("CRITICAL ERROR: Token API rejected the request. Check if Worker allows POST methods.\n");
}

echo "Token Acquired. Fetching Channel List...\n";

// 3. FETCH CHANNEL LIST
$listResponse = fetch_plex_data($workerUrl, $plexApi, false);
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
            'Title' => $title, 'Genre' => $genre, 'Logo'  => $logo, 'Link'  => $streamUrl
        ];

        $m3uContent .= "#EXTINF:-1 channel-id=\"{$slug}\" tvg-id=\"{$slug}\" tvg-logo=\"{$logo}\" group-title=\"{$genre}\",{$title}\n";
        $m3uContent .= "{$streamUrl}\n";
    }

    file_put_contents(__DIR__ . '/channels.json', json_encode($cleanList, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES));
    file_put_contents(__DIR__ . '/plex_channels.m3u', $m3uContent);
    echo "Success: Created playlist. Discord: https://discord.gg/fnsWGDy2mm\n";
} else {
    die("Error: Failed to parse channel list.\n");
}
?>
