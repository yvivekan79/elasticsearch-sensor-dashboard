# Elastic Data Stream Setup for Sensor Telemetry

A Python-based solution to set up Elasticsearch data streams for temperature and air quality sensor data with Kibana visualization.

## Overview

This application provides a complete setup for Elasticsearch data streams with two types of sensor telemetry data:

1. **Temperature Sensors** - Temperature readings with timestamp and location data
2. **Air Quality Sensors** - Readings for multiple air quality metrics (CO, NO2, O3, PM10, PM2.5, SO2)

The solution includes:

- Ingest pipelines for data transformation
- Index templates with proper mappings
- Data stream creation and configuration
- Python scripts for bulk data ingestion from CSV files
- Kibana visualization setup with dashboards
- Sample data generation for testing

## Prerequisites

- Elasticsearch 7.x or higher
- Kibana 7.x or higher
- Python 3.6 or higher
- Required Python packages:
  - elasticsearch
  - pandas
  - requests
  - flask (for web interface)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/elastic-sensor-telemetry.git
   cd elastic-sensor-telemetry
   ```

2. Install dependencies:
   ```
   pip install elasticsearch pandas requests flask
   ```

## Setup Instructions

### 1. Configure Environment

Set environment variables for Elasticsearch and Kibana URLs:

```bash
# For Linux/macOS
export ES_HOST=http://localhost:9200
export KIBANA_URL=http://localhost:5601

# For Windows
set ES_HOST=http://localhost:9200
set KIBANA_URL=http://localhost:5601
