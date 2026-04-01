<?php

require_once __DIR__ . '/vendor/autoload.php';

use Prometheus\CollectorRegistry;
use Prometheus\Storage\APC;

// ---------------------------
// Redis (for SPX trigger)
// ---------------------------
$redis = new Redis();
$redis->connect('redis');

// ---------------------------
// Normalize route (CRITICAL)
// ---------------------------
function normalize_route($uri)
{
    $path = parse_url($uri, PHP_URL_PATH);

    // Replace IDs (numbers) → :id
    $path = preg_replace('#/\\d+#', '/:id', $path);

    // Replace UUIDs → :uuid
    $path = preg_replace(
        '#[0-9a-fA-F-]{36}#',
        ':uuid',
        $path
    );

    return $path ?: '/';
}

$route = normalize_route($_SERVER['REQUEST_URI']);
