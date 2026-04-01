<?php

require_once __DIR__ . '/vendor/autoload.php';

use Prometheus\CollectorRegistry;
use Prometheus\Storage\APC;

// ---------------------------
// Redis (for SPX trigger)
// ---------------------------
$redis = new Redis();
$redis->connect('redis');
