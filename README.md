# Elasticsearch Sensor Telemetry Dashboard

A Python-based solution to set up Elasticsearch 8.x data streams for sensor telemetry data with Kibana 8.x visualization. This project provides a complete environment for monitoring temperature and air quality sensor data with support for both Docker Compose and Kubernetes deployments.

## Features

- **Elasticsearch 8.x Integration**: Fully compatible with Elasticsearch's latest security features and data streams
- **Kibana 8.x Dashboards**: Pre-configured visualization dashboards for sensor data analysis
- **Flask Web Interface**: Simple web UI to monitor the status of data streams
- **Automated Setup**: Scripts to set up the Elasticsearch environment, including pipelines, templates, and data streams
- **Sample Data**: CSV files and ingestion tools for testing and demonstration
- **Docker Compose**: Easy local deployment for development and testing
- **Kubernetes Helm Charts**: Production-ready deployment to Kubernetes clusters

## Structure

```
├── helm-chart/                     # Kubernetes deployment files
│   ├── elasticsearch-sensor-dashboard/  # Helm chart for the application
│   ├── Dockerfile                  # Container image for the web application
│   └── Dockerfile.init             # Container image for initialization jobs
├── templates/                      # Flask web application templates
├── static/                         # Static assets for the web UI
├── setup_elasticsearch.py          # Script to set up Elasticsearch environment
├── ingest_bulk_to_elasticsearch.py # Script to ingest CSV data
├── kibana_setup.py                 # Script to configure Kibana
├── main.py                         # Flask web application
├── docker-compose.yml              # Docker Compose configuration
├── temperaturesensor_data.csv      # Sample temperature sensor data
└── airqualitysensor_data.csv       # Sample air quality sensor data
```

## Quick Start with Docker Compose

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/elasticsearch-sensor-dashboard.git
   cd elasticsearch-sensor-dashboard
   ```

2. Set up environment variables (create a `.env` file):
   ```
   ES_HOST=http://elasticsearch:9200
   ES_USERNAME=elastic
   ES_PASSWORD=changeme
   KIBANA_URL=http://kibana:5601
   ```

3. Start the containers:
   ```bash
   docker-compose up -d
   ```

4. Set up the Elasticsearch environment:
   ```bash
   python setup_elasticsearch.py
   ```

5. Ingest sample data:
   ```bash
   python ingest_bulk_to_elasticsearch.py --csv temperaturesensor_data.csv --index temperaturesensor-ds
   python ingest_bulk_to_elasticsearch.py --csv airqualitysensor_data.csv --index airqualitysensor-ds
   ```

6. Set up Kibana dashboards:
   ```bash
   python kibana_setup.py
   ```

7. Access the applications:
   - Web Dashboard: http://localhost:5000
   - Kibana: http://localhost:5601

## Kubernetes Deployment

For production deployment to Kubernetes, please refer to the [Helm Chart README](helm-chart/README.md).

## Configuration

### Environment Variables

- `ES_HOST`: Elasticsearch host URL
- `ES_USERNAME`: Elasticsearch username
- `ES_PASSWORD`: Elasticsearch password
- `ES_API_KEY`: Elasticsearch API key (alternative to username/password)
- `ES_VERIFY_CERTS`: Whether to verify SSL certificates (default: true)
- `KIBANA_URL`: Kibana host URL
- `SESSION_SECRET`: Secret key for Flask sessions

## Sample Data

The repository includes sample CSV files for temperature and air quality sensors:

- `temperaturesensor_data.csv`: Time-series data from temperature sensors
- `airqualitysensor_data.csv`: Time-series data from air quality sensors

You can generate additional sample data using:
```bash
python sample_data_generator.py --type temperature --count 1000
python sample_data_generator.py --type airquality --count 1000
```

## Development

### Prerequisites

- Python 3.8+
- Docker and Docker Compose
- Elasticsearch 8.x and Kibana 8.x (via Docker or standalone)

### Installation

```bash
# Install Python dependencies
pip install elasticsearch==8.12.0 python-dotenv==1.0.0 flask==2.3.3 requests==2.31.0 pandas==2.1.1 gunicorn==21.2.0
```

### Running the Flask Application

```bash
# Start the Flask web app
python main.py
```

## Production Deployment

For production environments, it's recommended to:

1. Use Kubernetes for container orchestration
2. Enable TLS/SSL for Elasticsearch and Kibana
3. Configure proper authentication and role-based access
4. Set up proper data lifecycle management
5. Use a Telegraf agent for continuous data ingestion

## License

MIT

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request