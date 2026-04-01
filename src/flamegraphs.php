<?php

$dir = __DIR__ . '/spx-data';
$files = array_reverse(glob("$dir/*.json"));

$q = $_GET['q'] ?? '';

echo "<h1>SPX Flamegraphs</h1>";
echo "<form><input name='q' placeholder='search route...'></form>";
