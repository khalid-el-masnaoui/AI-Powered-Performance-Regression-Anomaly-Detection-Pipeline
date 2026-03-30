#!/bin/sh
set -e

# Replace placeholders with environment variable values in the config file
sed -i "s|\${REGRESSION_SERVICE_URL}|${REGRESSION_SERVICE_URL}|g" /etc/alertmanager/alertmanager.yml

# Start Alertmanager
exec alertmanager --config.file=/etc/alertmanager/alertmanager.yml
