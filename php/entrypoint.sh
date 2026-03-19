#!/bin/sh
set -e

# Run composer install if composer.json exists
if [ -f "composer.json" ]; then
    echo "Installing dependencies..."
    composer install --no-interaction --optimize-autoloader
fi

# Execute the main container command (passed via CMD)
exec "$@"
