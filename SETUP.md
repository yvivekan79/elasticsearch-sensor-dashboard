# Elasticsearch Data Stream Setup Guide

This guide explains how to set up and run the Elasticsearch and Kibana environment for sensor telemetry data.

## Prerequisites

- Docker and Docker Compose
- Python 3.8 or higher
- Elasticsearch 8.x and Kibana 8.x compatible environment

## Installation Steps

### 1. Clone the Repository

```bash
git clone <repository-url>
cd elasticsearch-sensor-dashboard
```

### 2. Install Python Dependencies

```bash
pip install elasticsearch==8.12.0 python-dotenv==1.0.0 flask==2.3.3 requests==2.31.0 pandas==2.1.1 gunicorn==21.2.0
```

### 3. Configure Environment Variables

Create a `.env` file in the root directory:

```
# Elasticsearch Configuration
ES_HOST=http://localhost:9200
ES_USERNAME=elastic
ES_PASSWORD=changeme
ES_VERIFY_CERTS=true

# Kibana Configuration
KIBANA_URL=http://localhost:5601

# Flask Configuration
SESSION_SECRET=change-this-secret-key-in-production
```

### 4. Start Elasticsearch and Kibana

```bash
docker-compose up -d
```

### 5. Wait for Services to Start

Wait for Elasticsearch and Kibana to fully start up. This might take a minute or two. You can check the status with:

```bash
docker-compose ps
```

### 6. Set Up Elasticsearch Environment

This script will create the necessary pipelines, templates, and data streams:

```bash
python setup_elasticsearch.py
```

### 7. Ingest Sample Data

Load the sample data into the data streams:

```bash
python ingest_bulk_to_elasticsearch.py --csv temperaturesensor_data.csv --index temperaturesensor-ds
python ingest_bulk_to_elasticsearch.py --csv airqualitysensor_data.csv --index airqualitysensor-ds
```

### 8. Set Up Kibana Dashboards

This script will create index patterns and import dashboards:

```bash
python kibana_setup.py
```

### 9. Start the Web Application

For development:

```bash
python main.py
```

For production:

```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 main:app
```

### 10. Access the Application

Open your browser and navigate to:

- Web UI: http://localhost:5000
- Kibana: http://localhost:5601

## Production Deployment Tips

### Security Considerations

1. Change default passwords for Elasticsearch and Kibana.
2. Enable TLS/SSL for both Elasticsearch and Kibana.
3. Set up proper network security and firewalls.
4. Use a strong, unique SESSION_SECRET value.

### Performance Optimization

1. Adjust Elasticsearch JVM heap size based on available memory.
2. Configure proper index lifecycle management policies.
3. Set appropriate shard counts for data streams.
4. Use multiple Gunicorn workers for the web application.

### Docker Configuration

Update the `docker-compose.yml` file with appropriate resource limits:

```yaml
elasticsearch:
  ...
  environment:
    - "ES_JAVA_OPTS=-Xms1g -Xmx1g"  # Adjust based on available memory
  deploy:
    resources:
      limits:
        memory: 2G
```

### Continuous Data Ingestion

For real-world usage, set up Telegraf to continuously ingest data from your sensors. Here's a sample Telegraf configuration:

```toml
[[outputs.elasticsearch]]
  urls = ["http://localhost:9200"]
  username = "${ES_USERNAME}"
  password = "${ES_PASSWORD}"
  index_name = "temperaturesensor-ds"
  manage_template = false
  
[[inputs.mqtt_consumer]]
  servers = ["tcp://mqtt-broker:1883"]
  topics = ["sensors/temperature/#"]
  data_format = "json"
```

## Troubleshooting

### Connection Issues

If you can't connect to Elasticsearch:
- Check if Docker containers are running: `docker-compose ps`
- Verify Elasticsearch logs: `docker-compose logs elasticsearch`
- Ensure the ES_HOST environment variable is correct
- Check your network configuration and firewall settings

### Data Ingestion Problems

If data isn't showing up:
- Check if data streams are created: `curl -X GET "localhost:9200/_data_stream/temperaturesensor-ds"`
- Verify ingest pipeline is working: `curl -X GET "localhost:9200/_ingest/pipeline/temperaturesensor_pipeline"`
- Run the ingest script with the `--dry-run` flag to see the data being prepared

### Kibana Dashboard Issues

If dashboards aren't loading:
- Ensure index patterns are created
- Check for errors in the browser console
- Verify Kibana logs: `docker-compose logs kibana`

## Maintenance

### Data Stream Management

Delete a data stream:
```bash
curl -X DELETE "localhost:9200/_data_stream/temperaturesensor-ds"
```

Create a new data stream:
```bash
curl -X PUT "localhost:9200/_data_stream/temperaturesensor-ds"
```

### Backup and Restore

For regular backups, set up Elasticsearch Snapshot and Restore:
```bash
# Register repository
curl -X PUT "localhost:9200/_snapshot/my_backup" -H "Content-Type: application/json" -d'
{
  "type": "fs",
  "settings": {
    "location": "/path/to/backup/location"
  }
}'

# Create snapshot
curl -X PUT "localhost:9200/_snapshot/my_backup/snapshot_1?wait_for_completion=true"
```