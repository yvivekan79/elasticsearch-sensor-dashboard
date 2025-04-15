#!/usr/bin/env python3
"""
Kibana Setup Script

This script configures Kibana with index patterns and dashboards for sensor telemetry data:
- Creates index patterns for temperature and air quality sensors
- Imports dashboard configurations
"""

import argparse
import json
import logging
import os
import sys
import time
import ssl
from urllib.parse import urlparse

import requests
from elasticsearch import Elasticsearch
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Setup Kibana for sensor telemetry')
    parser.add_argument('--kibana-host', default=os.environ.get('KIBANA_URL', 'http://localhost:5601'),
                      help='Kibana host URL')
    parser.add_argument('--es-host', default=os.environ.get('ES_HOST', 'http://localhost:9200'),
                      help='Elasticsearch host URL')
    parser.add_argument('--wait', action='store_true', 
                      help='Wait for Kibana to be available')
    parser.add_argument('--dashboard-file', default='static/kibana_telemetry_dashboard.json',
                      help='Path to Kibana dashboard JSON file')
    parser.add_argument('--force', action='store_true',
                      help='Force recreate existing components')
    return parser.parse_args()

def wait_for_kibana(host, max_retries=12, delay=5):
    """Wait for Kibana to become available"""
    logger.info(f"Waiting for Kibana at {host} to be available...")
    api_url = f"{host}/api/status"
    
    for i in range(max_retries):
        try:
            response = requests.get(api_url)
            if response.status_code == 200:
                status = response.json()
                if status.get('status', {}).get('overall', {}).get('state') == 'green':
                    logger.info("Kibana is available!")
                    return True
                else:
                    logger.warning(f"Kibana status is not green, waiting...")
            else:
                logger.warning(f"Kibana returned status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Kibana not yet available, retry {i+1}/{max_retries}")
        
        time.sleep(delay)
    
    logger.error("Timed out waiting for Kibana")
    return False

def create_index_pattern(kibana_host, pattern_title, time_field="@timestamp"):
    """Create an index pattern in Kibana"""
    api_url = f"{kibana_host}/api/saved_objects/index-pattern"
    
    # Check if pattern already exists
    search_url = f"{api_url}/_find?type=index-pattern&search_fields=title&search={pattern_title}"
    try:
        response = requests.get(search_url)
        if response.status_code == 200:
            data = response.json()
            if data.get('total', 0) > 0:
                logger.info(f"Index pattern '{pattern_title}' already exists")
                return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Error checking for existing index pattern: {str(e)}")
        return False
    
    # Create the index pattern
    headers = {'Content-Type': 'application/json', 'kbn-xsrf': 'true'}
    payload = {
        "attributes": {
            "title": pattern_title,
            "timeFieldName": time_field
        }
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=payload)
        if response.status_code in [200, 201]:
            logger.info(f"Successfully created index pattern: {pattern_title}")
            return True
        else:
            logger.error(f"Failed to create index pattern: {response.status_code} - {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Error creating index pattern: {str(e)}")
        return False

def import_kibana_dashboard(kibana_host, dashboard_file):
    """Import Kibana dashboard from JSON file"""
    api_url = f"{kibana_host}/api/kibana/dashboards/import"
    headers = {'Content-Type': 'application/json', 'kbn-xsrf': 'true'}
    
    try:
        with open(dashboard_file, 'r') as f:
            dashboard_json = json.load(f)
        
        # Make POST request to import dashboard
        response = requests.post(api_url, headers=headers, json=dashboard_json)
        
        if response.status_code in [200, 201]:
            logger.info(f"Successfully imported dashboard from {dashboard_file}")
            return True
        else:
            logger.error(f"Failed to import dashboard: {response.status_code} - {response.text}")
            return False
    except FileNotFoundError:
        logger.error(f"Dashboard file not found: {dashboard_file}")
        return False
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in dashboard file: {dashboard_file}")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Error importing dashboard: {str(e)}")
        return False

def create_sample_dashboard(kibana_host):
    """Create a sample telemetry dashboard if no dashboard file is available"""
    # First, check if data exists in Elasticsearch
    # Connect to Elasticsearch with 8.x compatibility
    host = os.environ.get('ES_HOST', 'http://localhost:9200')
    username = os.environ.get('ES_USERNAME', 'elastic')
    password = os.environ.get('ES_PASSWORD', 'changeme')
    api_key = os.environ.get('ES_API_KEY', '')
    
    # Parse URL to determine if SSL is needed
    parsed_url = urlparse(host)
    use_ssl = parsed_url.scheme == 'https'
    
    # Configure connection options for Elasticsearch 8.x
    conn_params = {
        'hosts': [host],
        'request_timeout': 30,
        'retry_on_timeout': True
    }
    
    # Add authentication
    if api_key:
        conn_params['api_key'] = api_key
    elif password:
        conn_params['basic_auth'] = (username, password)
    
    # Add SSL if needed
    if use_ssl:
        ssl_context = ssl.create_default_context()
        # If using self-signed certs, you can disable verification
        if os.environ.get('ES_VERIFY_CERTS', 'true').lower() == 'false':
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        conn_params['ssl_context'] = ssl_context
        
    es = Elasticsearch(**conn_params)
    
    temperature_exists = False
    airquality_exists = False
    
    try:
        temp_resp = es.count(index="temperaturesensor-ds")
        temp_count = temp_resp.get('count', 0)
        temperature_exists = temp_count > 0
        
        air_resp = es.count(index="airqualitysensor-ds")
        air_count = air_resp.get('count', 0)
        airquality_exists = air_count > 0
    except Exception as e:
        logger.warning(f"Error checking for existing data: {str(e)}")
    
    # If neither data stream has data, we can't create visualizations
    if not temperature_exists and not airquality_exists:
        logger.warning("No data found in data streams. Please ingest data before creating visualizations.")
        return False
    
    # Create visualizations
    visualizations = []
    dashboard_panels = []
    panel_index = 0
    
    # Headers for kbn requests
    headers = {
        'Content-Type': 'application/json',
        'kbn-xsrf': 'true'
    }
    
    # Create temperature visualization if data exists
    if temperature_exists:
        try:
            temp_vis = {
                "attributes": {
                    "title": "Temperature Over Time",
                    "visState": json.dumps({
                        "title": "Temperature Over Time",
                        "type": "line",
                        "params": {
                            "type": "line",
                            "grid": {"categoryLines": False},
                            "categoryAxes": [{
                                "id": "CategoryAxis-1",
                                "type": "category",
                                "position": "bottom",
                                "show": True,
                                "scale": {"type": "linear"},
                                "labels": {"show": True, "truncate": 100},
                                "title": {}
                            }],
                            "valueAxes": [{
                                "id": "ValueAxis-1",
                                "name": "LeftAxis-1",
                                "type": "value",
                                "position": "left",
                                "show": True,
                                "scale": {"type": "linear", "mode": "normal"},
                                "labels": {"show": True, "rotate": 0, "filter": False, "truncate": 100},
                                "title": {"text": "Temperature (°C)"}
                            }],
                            "seriesParams": [{
                                "show": "true",
                                "type": "line",
                                "mode": "normal",
                                "data": {"label": "Average Temperature", "id": "1"},
                                "valueAxis": "ValueAxis-1",
                                "drawLinesBetweenPoints": True,
                                "showCircles": True
                            }],
                            "addTooltip": True,
                            "addLegend": True,
                            "legendPosition": "right",
                            "times": [],
                            "addTimeMarker": False
                        },
                        "aggs": [
                            {
                                "id": "1",
                                "enabled": True,
                                "type": "avg",
                                "schema": "metric",
                                "params": {"field": "temperature_value"}
                            },
                            {
                                "id": "2",
                                "enabled": True,
                                "type": "date_histogram",
                                "schema": "segment",
                                "params": {
                                    "field": "@timestamp",
                                    "timeRange": {"from": "now-7d", "to": "now"},
                                    "useNormalizedEsInterval": True,
                                    "interval": "auto",
                                    "drop_partials": False,
                                    "min_doc_count": 1,
                                    "extended_bounds": {}
                                }
                            }
                        ]
                    }),
                    "uiStateJSON": "{}",
                    "description": "",
                    "version": 1,
                    "kibanaSavedObjectMeta": {
                        "searchSourceJSON": json.dumps({
                            "index": "temperaturesensor-*",
                            "filter": [],
                            "query": {"query": "", "language": "kuery"}
                        })
                    }
                }
            }
            
            temp_vis_url = f"{kibana_host}/api/saved_objects/visualization/temperature-over-time"
            temp_vis_response = requests.post(temp_vis_url, headers=headers, json=temp_vis)
            
            if temp_vis_response.status_code in [200, 201]:
                logger.info("Created temperature visualization")
                dashboard_panels.append({
                    "panelIndex": panel_index,
                    "gridData": {
                        "x": 0,
                        "y": 0,
                        "w": 24,
                        "h": 15,
                        "i": str(panel_index)
                    },
                    "embeddableConfig": {},
                    "type": "visualization",
                    "id": "temperature-over-time"
                })
                panel_index += 1
            else:
                logger.error(f"Failed to create temperature visualization: {temp_vis_response.status_code} - {temp_vis_response.text}")
        
        except Exception as e:
            logger.error(f"Error creating temperature visualization: {str(e)}")
    
    # Create air quality visualization if data exists
    if airquality_exists:
        try:
            air_vis = {
                "attributes": {
                    "title": "Air Quality Metrics",
                    "visState": json.dumps({
                        "title": "Air Quality Metrics",
                        "type": "line",
                        "params": {
                            "type": "line",
                            "grid": {"categoryLines": False},
                            "categoryAxes": [{
                                "id": "CategoryAxis-1",
                                "type": "category",
                                "position": "bottom",
                                "show": True,
                                "scale": {"type": "linear"},
                                "labels": {"show": True, "truncate": 100},
                                "title": {}
                            }],
                            "valueAxes": [{
                                "id": "ValueAxis-1",
                                "name": "LeftAxis-1",
                                "type": "value",
                                "position": "left",
                                "show": True,
                                "scale": {"type": "linear", "mode": "normal"},
                                "labels": {"show": True, "rotate": 0, "filter": False, "truncate": 100},
                                "title": {"text": "Concentration"}
                            }],
                            "seriesParams": [
                                {
                                    "show": "true",
                                    "type": "line",
                                    "mode": "normal",
                                    "data": {"label": "Average PM2.5", "id": "1"},
                                    "valueAxis": "ValueAxis-1",
                                    "drawLinesBetweenPoints": True,
                                    "showCircles": True
                                },
                                {
                                    "show": "true",
                                    "type": "line",
                                    "mode": "normal",
                                    "data": {"label": "Average CO", "id": "2"},
                                    "valueAxis": "ValueAxis-1",
                                    "drawLinesBetweenPoints": True,
                                    "showCircles": True
                                },
                                {
                                    "show": "true",
                                    "type": "line",
                                    "mode": "normal",
                                    "data": {"label": "Average NO2", "id": "3"},
                                    "valueAxis": "ValueAxis-1",
                                    "drawLinesBetweenPoints": True,
                                    "showCircles": True
                                }
                            ],
                            "addTooltip": True,
                            "addLegend": True,
                            "legendPosition": "right",
                            "times": [],
                            "addTimeMarker": False
                        },
                        "aggs": [
                            {
                                "id": "1",
                                "enabled": True,
                                "type": "avg",
                                "schema": "metric",
                                "params": {"field": "pm25"}
                            },
                            {
                                "id": "2",
                                "enabled": True,
                                "type": "avg",
                                "schema": "metric",
                                "params": {"field": "co"}
                            },
                            {
                                "id": "3",
                                "enabled": True,
                                "type": "avg",
                                "schema": "metric",
                                "params": {"field": "no2"}
                            },
                            {
                                "id": "4",
                                "enabled": True,
                                "type": "date_histogram",
                                "schema": "segment",
                                "params": {
                                    "field": "@timestamp",
                                    "timeRange": {"from": "now-7d", "to": "now"},
                                    "useNormalizedEsInterval": True,
                                    "interval": "auto",
                                    "drop_partials": False,
                                    "min_doc_count": 1,
                                    "extended_bounds": {}
                                }
                            }
                        ]
                    }),
                    "uiStateJSON": "{}",
                    "description": "",
                    "version": 1,
                    "kibanaSavedObjectMeta": {
                        "searchSourceJSON": json.dumps({
                            "index": "airqualitysensor-*",
                            "filter": [],
                            "query": {"query": "", "language": "kuery"}
                        })
                    }
                }
            }
            
            air_vis_url = f"{kibana_host}/api/saved_objects/visualization/air-quality-metrics"
            air_vis_response = requests.post(air_vis_url, headers=headers, json=air_vis)
            
            if air_vis_response.status_code in [200, 201]:
                logger.info("Created air quality visualization")
                dashboard_panels.append({
                    "panelIndex": panel_index,
                    "gridData": {
                        "x": 0,
                        "y": 15,
                        "w": 24,
                        "h": 15,
                        "i": str(panel_index)
                    },
                    "embeddableConfig": {},
                    "type": "visualization",
                    "id": "air-quality-metrics"
                })
                panel_index += 1
            else:
                logger.error(f"Failed to create air quality visualization: {air_vis_response.status_code} - {air_vis_response.text}")
        
        except Exception as e:
            logger.error(f"Error creating air quality visualization: {str(e)}")
    
    # Create dashboard to hold visualizations
    if dashboard_panels:
        try:
            dashboard = {
                "attributes": {
                    "title": "Sensor Telemetry Dashboard",
                    "hits": 0,
                    "description": "Dashboard for sensor telemetry data",
                    "panelsJSON": json.dumps(dashboard_panels),
                    "optionsJSON": json.dumps({
                        "useMargins": True,
                        "hidePanelTitles": False
                    }),
                    "version": 1,
                    "timeRestore": True,
                    "timeTo": "now",
                    "timeFrom": "now-7d",
                    "refreshInterval": {
                        "pause": True,
                        "value": 0
                    },
                    "kibanaSavedObjectMeta": {
                        "searchSourceJSON": json.dumps({
                            "query": {"query": "", "language": "kuery"},
                            "filter": []
                        })
                    }
                }
            }
            
            dashboard_url = f"{kibana_host}/api/saved_objects/dashboard/sensor-telemetry-dashboard"
            dashboard_response = requests.post(dashboard_url, headers=headers, json=dashboard)
            
            if dashboard_response.status_code in [200, 201]:
                logger.info("Created sensor telemetry dashboard")
                return True
            else:
                logger.error(f"Failed to create dashboard: {dashboard_response.status_code} - {dashboard_response.text}")
                return False
        
        except Exception as e:
            logger.error(f"Error creating dashboard: {str(e)}")
            return False
    
    return False

def main():
    """Main function to run the Kibana setup process"""
    args = parse_arguments()
    
    # Wait for Kibana if requested
    if args.wait and not wait_for_kibana(args.kibana_host):
        sys.exit(1)
    
    # Create index patterns
    logger.info("Creating index patterns...")
    temp_pattern_created = create_index_pattern(args.kibana_host, "temperaturesensor-*")
    air_pattern_created = create_index_pattern(args.kibana_host, "airqualitysensor-*")
    
    if not temp_pattern_created or not air_pattern_created:
        logger.warning("Some index patterns could not be created")
    
    # Import dashboard or create sample dashboard
    logger.info("Setting up dashboards...")
    dashboard_imported = False
    
    if os.path.exists(args.dashboard_file):
        dashboard_imported = import_kibana_dashboard(args.kibana_host, args.dashboard_file)
    else:
        logger.warning(f"Dashboard file not found: {args.dashboard_file}")
        logger.info("Creating sample dashboard...")
        dashboard_imported = create_sample_dashboard(args.kibana_host)
    
    if not dashboard_imported:
        logger.warning("Dashboard could not be imported/created")
    
    logger.info("Kibana setup completed")

if __name__ == "__main__":
    main()
