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

/**
 * HELPER: PROXY REQUEST
 * Routes requests through the Cloudflare Worker using custom headers.
 */
function worker_proxy($workerUrl, $targetUrl, $method = 'GET') {
    $ch = curl_init($workerUrl);
    
    $headers = [
        "X-Target-Url: $targetUrl",
        "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) BuddyChewChew/1.0"
    ];

    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 15);

    if ($method === 'POST') {
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, ""); // Plex token API likes an empty POST
    }

    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    return ($httpCode === 200) ? $response : null;
}

// 2. START FETCHING TOKEN
echo "BuddyChewChew Plex Tool: Requesting Token via Proxy...\n";
$uuid = bin2hex(random_bytes(16));
$tokenApi = "https://clients.plex.tv/api/v2/users/anonymous?X-Plex-Product=Plex%20Web&X-Plex-Client-Identifier=$uuid";

$tokenResponse = worker_proxy($workerUrl, $tokenApi, 'POST');
$tokenData = json_decode($tokenResponse, true);
$token = $tokenData['authToken'] ?? null;

if (!$token) {
    die("CRITICAL ERROR: Failed to acquire Plex Token through Worker. Ensure Worker handles X-Target-Url header.\n");
}

echo "Token Acquired. Fetching Channel List...\n";

// 3. FETCH CHANNEL LIST
$listResponse = worker_proxy($workerUrl, $plexApi);
$data = json_decode($listResponse, true);
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
    echo "Discord: https://discord.gg/fnsWGDy2mm\n";
} else {
    echo "Error: Worker could not retrieve or parse the Plex channel list.\n";
    exit(1);
}
?>
