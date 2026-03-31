<?php

$_SERVER['SPX_AUTO_START'] = '0';

// ---------------------------
// SPX AUTO-TRIGGER
// ---------------------------
$redis = new Redis();
$redis->connect('redis');
