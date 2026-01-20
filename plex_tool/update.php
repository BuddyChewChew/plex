<?php
/**
 * PLEX INDEPENDENT SCRAPER - SUBDIRECTORY VERSION
 * Location: plex_tool/update.php
 */

// 1. YOUR ENCODED WORKER URL
$encodedWorker = "aHR0cHM6Ly9wbGV4LmJ1ZGR5Y2hld2NoZXcud29ya2Vycy5kZXYv";
$workerUrl     = base64_decode($encodedWorker);

// 2. PLEX API SETTINGS
$plexApi   = "http://www.plex.tv/wp-json/plex/v1/mediaverse/livetv/channels/list";
$referer   = "https://www.plex.tv/live-tv-channels/";

// 3. BUILD THE REQUEST
$requestUrl = $workerUrl . "?url=" . urlencode($plexApi) . "&referer=" . urlencode($referer);

echo "Connecting to Worker: plex.buddychewchew.workers.dev ...\n";

// 4. FETCH THE DATA
$response = file_get_contents($requestUrl);

if (!$response) {
    echo "Error: Could not reach Worker.\n";
    exit(1);
}

$data = json_decode($response, true);
$cleanList = [];

// 5. PROCESS AND GENERATE OUTPUTS
if (isset($data['data']['list']) && is_array($data['data']['list'])) {
    
    $m3uContent = "#EXTM3U\n";
    
    foreach ($data['data']['list'] as $index => $ch) {
        $title   = $ch['media_title'] ?? 'Unknown';
        $genre   = !empty($ch['media_categories']) ? array_values($ch['media_categories'])[0] : 'General';
        $link    = $ch['media_link'] ?? '';
        
        $cleanList[] = [
            'Title'    => $title,
            'Genre'    => $genre,
            'Language' => $ch['media_lang'] ?? 'EN',
            'Summary'  => $ch['media_summary'] ?? '',
            'Link'     => $link
        ];

        $m3uContent .= "#EXTINF:-1 tvg-id=\"plex.{$index}\" tvg-name=\"{$title}\" group-title=\"{$genre}\", {$title}\n";
        $m3uContent .= "{$link}\n";
    }

    // Save files specifically into the plex_tool directory
    // __DIR__ ensures it saves in the same folder as the script
    file_put_contents(__DIR__ . '/channels.json', json_encode($cleanList, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES));
    file_put_contents(__DIR__ . '/plex_channels.m3u', $m3uContent);
    
    echo "Success! Updated plex_tool/channels.json and plex_tool/plex_channels.m3u\n";
} else {
    echo "Error: Data structure unexpected.\n";
    exit(1);
}
?>
