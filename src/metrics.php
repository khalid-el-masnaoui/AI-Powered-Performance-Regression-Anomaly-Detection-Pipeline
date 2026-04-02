<?php

require_once __DIR__ . '/vendor/autoload.php';

use Prometheus\CollectorRegistry;
use Prometheus\RenderTextFormat;
use Prometheus\Storage\APC;

// Same storage as index.php
$registry = new CollectorRegistry(new APC());

$renderer = new RenderTextFormat();

header('Content-Type: ' . RenderTextFormat::MIME_TYPE);

echo $renderer->render(
    $registry->getMetricFamilySamples()
);
