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

// ---------------------------
// Prometheus Metrics
// ---------------------------
$registry = new CollectorRegistry(new APC());

$histogram = $registry->getOrRegisterHistogram(
    'app',
    'request_duration_seconds',
    'Request duration',
    ['method', 'route', 'status'],
    [0.01, 0.05, 0.1, 0.3, 0.5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 30, 60, 120, 180, 240, 300]
);

$counter = $registry->getOrRegisterCounter(
    'app',
    'requests_total',
    'Total requests',
    ['method', 'route', 'status']
);

// ---------------------------
// Request handling
// ---------------------------
$start = microtime(true);

if (isset($_GET['delay'])) {
    usleep($_GET['delay'] * 1000000);
}

// Fake routing (replace with your framework)
$path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);

if ($path === '/') {
    usleep(rand(10000, 200000)); // simulate latency
    echo "Home";
} elseif ($path === '/api/users') {
    usleep(rand(50000, 500000)); // slower endpoint
    echo json_encode(["users" => []]);
} else {
    http_response_code(404);
    echo "Not Found";
}
