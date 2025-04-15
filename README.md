# Elastic Data Stream Setup for Sensor Telemetry

This project sets up an Elasticsearch 8.x and Kibana 8.x environment for ingesting and analyzing temperature and air quality sensor data using data streams. It includes a web interface to monitor the data streams and visualize the data through Kibana dashboards.

## Features

- **Elasticsearch 8.x Integration**: Configured with authentication and SSL support for secure data handling
- **Data Streams**: Using the time-series optimized data streams for efficient storage and querying
- **Ingest Pipelines**: Automatic data transformation during ingestion
- **Kibana 8.x Dashboards**: Visualize temperature and air quality metrics
- **Web Interface**: Monitor the status of data streams and access dashboards

## Architecture

1. **Data Sources**: Temperature and air quality sensors (simulated with sample data)
2. **Data Ingestion**: 
   - Sample data provided via CSV files
   - Production ingestion handled by Telegraf (external to this project)
3. **Storage**: Elasticsearch 8.x with data streams
4. **Visualization**: Kibana 8.x dashboards
5. **Monitoring**: Flask web application

## Setup Instructions

### Prerequisites

- Docker and Docker Compose
- Python 3.x
- pip

### Installation

1. Clone this repository
2. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Start the Elasticsearch and Kibana containers:
   ```
   docker-compose up -d
   ```
4. Set up the Elasticsearch environment:
   ```
   python setup_elasticsearch.py
   ```
5. Ingest sample data:
   ```
   python ingest_bulk_to_elasticsearch.py --csv temperaturesensor_data.csv --index temperaturesensor-ds
   python ingest_bulk_to_elasticsearch.py --csv airqualitysensor_data.csv --index airqualitysensor-ds
   ```
6. Configure Kibana:
   ```
   python kibana_setup.py
   ```
7. Start the web application:
   ```
   python main.py
   ```
8. Access the web interface at http://localhost:5000

## Environment Variables

Configure the system through environment variables in a `.env` file:

```
# Elasticsearch Configuration
ES_HOST=http://localhost:9200
ES_USERNAME=elastic
ES_PASSWORD=changeme
ES_VERIFY_CERTS=true

# Kibana Configuration
KIBANA_URL=http://localhost:5601

# Flask Configuration
SESSION_SECRET=your-secret-key
```

## Production Deployment

For production deployments:

1. Update the credentials in the `.env` file
2. Enable SSL for both Elasticsearch and Kibana
3. Configure proper resource allocation in `docker-compose.yml`
4. Set up Telegraf for continuous data ingestion from sensors
5. Implement proper data retention policies

## Data Format

### Temperature Sensor Data

```json
{
  "@timestamp": "2023-01-01T00:00:00Z",
  "measurement_name": "temperature",
  "tag": {
    "host": "sensor001",
    "sensor_type": "temperature"
  },
  "uuid": "abcd1234",
  "temperature_value": 22.5,
  "temperature_unit": "C"
}
```

### Air Quality Sensor Data

```json
{
  "@timestamp": "2023-01-01T00:00:00Z",
  "measurement_name": "air_quality",
  "tag": {
    "host": "sensor002",
    "sensor_type": "air_quality"
  },
  "uuid": "efgh5678",
  "co": 0.5,
  "no2": 0.02,
  "o3": 0.03,
  "pm10": 15,
  "pm25": 8,
  "so2": 0.01
}
```

## License

This project is licensed under the MIT License.