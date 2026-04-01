<?php

$dir = __DIR__ . '/spx-data';
$files = array_reverse(glob("$dir/*.json"));

$q = $_GET['q'] ?? '';

echo "<h1>SPX Flamegraphs</h1>";
echo "<form><input name='q' placeholder='search route...'></form>";

foreach ($files as $file) {
    $name = basename($file);

    if ($q && stripos($name, $q) === false) {
        continue;
    }

    echo "<div style='margin:10px;padding:10px;border:1px solid #ccc'>";
    echo "<a target='_blank' href='/spx-data/$name'>$name</a>";
    echo "</div>";
}
