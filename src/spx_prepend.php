<?php

$_SERVER['SPX_AUTO_START'] = '0';

// ---------------------------
// SPX AUTO-TRIGGER
// ---------------------------
$redis = new Redis();
$redis->connect('redis');

$route = strtok($_SERVER["REQUEST_URI"], '?');

if ($redis->get("spx:$route")) {
    echo "Request Profiled\n";
    $_SERVER['SPX_AUTO_START'] = '1';
    //ini_set('spx.http_enabled', '1');
    spx_profiler_start();
    register_shutdown_function('spx_profiler_stop');

}
