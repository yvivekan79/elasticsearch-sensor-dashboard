#!/bin/bash
# Elasticsearch setup script for Elasticsearch 8.x
# This script is executed inside the Elasticsearch container

set -e

# Wait for Elasticsearch to be ready
until curl -s -u elastic:${ELASTIC_PASSWORD} http://localhost:9200 >/dev/null; do
    echo "Waiting for Elasticsearch..."
    sleep 5
done

echo "Elasticsearch is up and running! Setting up users..."

# Set kibana_system user password
echo "Setting kibana_system user password..."
curl -X POST -u elastic:${ELASTIC_PASSWORD} -H "Content-Type: application/json" \
    http://localhost:9200/_security/user/kibana_system/_password \
    -d "{\"password\":\"${KIBANA_SYSTEM_PASSWORD}\"}"

echo "Security setup completed successfully."
exit 0