<?php
/**
 * PLEX INDEPENDENT SCRAPER - JSON ONLY
 * Location: plex_tool/update.php
 */

// 1. OBFUSCATED WORKER URL
$encodedWorker = "aHR0cHM6Ly9wbGV4LmJ1ZGR5Y2hld2NoZXcud29ya2Vycy5kZXYv";
$workerUrl     = base64_decode($encodedWorker);

$plexApi   = "http://www.plex.tv/wp-json/plex/v1/mediaverse/livetv/channels/list";
$referer   = "https://www.plex.tv/live-tv-channels/";

// 2. FETCH DATA
$requestUrl = $workerUrl . "?url=" . urlencode($plexApi) . "&referer=" . urlencode($referer);
echo "Connecting to Worker for JSON data...\n";

$response = file_get_contents($requestUrl);

if (!$response) {
    echo "Error: Worker unreachable.\n";
    exit(1);
}

$data = json_decode($response, true);
$cleanList = [];

// 3. GENERATE JSON OUTPUT
if (isset($data['data']['list']) && is_array($data['data']['list'])) {
    
    foreach ($data['data']['list'] as $ch) {
        $cleanList[] = [
            'Title'    => $ch['media_title'] ?? 'Unknown',
            'Genre'    => !empty($ch['media_categories']) ? array_values($ch['media_categories'])[0] : 'General',
            'Language' => $ch['media_lang'] ?? 'EN',
            'Summary'  => $ch['media_summary'] ?? '',
            'Link'     => $ch['media_link'] ?? ''
        ];
    }

    // Save only the JSON file to the current directory
    file_put_contents(__DIR__ . '/channels.json', json_encode($cleanList, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES));
    
    echo "Success: Created channels.json in plex_tool/\n";
} else {
    echo "Error: Unexpected data format from Worker.\n";
    exit(1);
}
?>
