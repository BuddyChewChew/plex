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

// 2. HELPER: FETCH THROUGH WORKER
function fetch_via_worker($workerUrl, $targetUrl) {
    // Construct the URL exactly like the one you tested in the browser
    $proxyUrl = rtrim($workerUrl, '/') . "/?url=" . urlencode($targetUrl);
    
    $options = [
        "http" => [
            "method" => "GET",
            "header" => "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)\r\n"
        ]
    ];
    $context = stream_context_create($options);
    return @file_get_contents($proxyUrl, false, $context);
}

// 3. START FETCHING TOKEN
echo "BuddyChewChew Plex Tool: Requesting Token via Worker...\n";
$uuid = bin2hex(random_bytes(16));
$tokenApi = "https://clients.plex.tv/api/v2/users/anonymous?X-Plex-Product=Plex%20Web&X-Plex-Client-Identifier=$uuid";

$tokenResponse = fetch_via_worker($workerUrl, $tokenApi);
$tokenData = json_decode($tokenResponse, true);
$token = $tokenData['authToken'] ?? null;

if (!$token) {
    echo "Worker Response: " . substr($tokenResponse, 0, 100) . "...\n";
    die("CRITICAL ERROR: Could not get Token. Your Worker might not support fetching this API.\n");
}

echo "Token Acquired. Fetching Channel List...\n";

// 4. FETCH CHANNEL LIST
$listResponse = fetch_via_worker($workerUrl, $plexApi);
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
    echo "Error: Worker could not parse the Plex channel list.\n";
    exit(1);
}
?>
