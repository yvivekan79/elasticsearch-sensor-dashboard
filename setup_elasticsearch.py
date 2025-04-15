#!/usr/bin/env python3
"""
Elasticsearch Setup Script

This script sets up the Elasticsearch environment for telemetry data including:
- Ingest pipelines
- Index templates
- Data streams
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
from elasticsearch.exceptions import ApiError, ConnectionError as ESConnectionError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define constants for ingest pipelines and templates
TEMPERATURE_PIPELINE = {
    "description": "Flatten and enrich temperature telemetry",
    "processors": [
        {"set": {"field": "ingested_at", "value": "{{_ingest.timestamp}}"}},
        {"rename": {"field": "temperaturesensor.telemetry_temperature_value", "target_field": "temperature_value"}},
        {"rename": {"field": "temperaturesensor.telemetry_temperature_unit", "target_field": "temperature_unit"}},
        {"remove": {"field": "temperaturesensor"}}
    ]
}

AIR_QUALITY_PIPELINE = {
    "description": "Flatten and enrich air quality telemetry",
    "processors": [
        {"set": {"field": "ingested_at", "value": "{{_ingest.timestamp}}"}},
        {"rename": {"field": "airqualitysensor.telemetry_co_value", "target_field": "co"}},
        {"rename": {"field": "airqualitysensor.telemetry_no2_value", "target_field": "no2"}},
        {"rename": {"field": "airqualitysensor.telemetry_o3_value", "target_field": "o3"}},
        {"rename": {"field": "airqualitysensor.telemetry_pm10_value", "target_field": "pm10"}},
        {"rename": {"field": "airqualitysensor.telemetry_pm25_value", "target_field": "pm25"}},
        {"rename": {"field": "airqualitysensor.telemetry_so2_value", "target_field": "so2"}},
        {"remove": {"field": "airqualitysensor"}}
    ]
}

TEMPERATURE_TEMPLATE = {
    "index_patterns": ["temperaturesensor-*"],
    "data_stream": {},
    "template": {
        "settings": {
            "index.default_pipeline": "temperaturesensor_pipeline"
        },
        "mappings": {
            "properties": {
                "@timestamp": {"type": "date"},
                "temperature_value": {"type": "float"},
                "temperature_unit": {"type": "keyword"},
                "ingested_at": {"type": "date"},
                "measurement_name": {"type": "keyword"},
                "tag": {
                    "properties": {
                        "host": {"type": "keyword"},
                        "sensor_type": {"type": "keyword"}
                    }
                },
                "uuid": {"type": "keyword"}
            }
        }
    }
}

AIR_QUALITY_TEMPLATE = {
    "index_patterns": ["airqualitysensor-*"],
    "data_stream": {},
    "template": {
        "settings": {
            "index.default_pipeline": "airqualitysensor_pipeline"
        },
        "mappings": {
            "properties": {
                "@timestamp": {"type": "date"},
                "co": {"type": "float"},
                "no2": {"type": "float"},
                "o3": {"type": "float"},
                "pm10": {"type": "float"},
                "pm25": {"type": "float"},
                "so2": {"type": "float"},
                "ingested_at": {"type": "date"},
                "measurement_name": {"type": "keyword"},
                "tag": {
                    "properties": {
                        "host": {"type": "keyword"},
                        "sensor_type": {"type": "keyword"}
                    }
                },
                "uuid": {"type": "keyword"}
            }
        }
    }
}

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Setup Elasticsearch for sensor telemetry')
    parser.add_argument('--host', default=os.environ.get('ES_HOST', 'http://localhost:9200'),
                      help='Elasticsearch host URL')
    parser.add_argument('--username', default=os.environ.get('ES_USERNAME', 'elastic'),
                      help='Elasticsearch username')
    parser.add_argument('--password', default=os.environ.get('ES_PASSWORD', ''),
                      help='Elasticsearch password')
    parser.add_argument('--wait', action='store_true', 
                      help='Wait for Elasticsearch to be available')
    parser.add_argument('--force', action='store_true',
                      help='Force recreate existing components')
    parser.add_argument('--components', default='all',
                      choices=['all', 'pipelines', 'templates', 'datastreams'],
                      help='Components to setup')
    args = parser.parse_args()
    
    # Set environment variables for the credentials
    if args.username:
        os.environ['ES_USERNAME'] = args.username
    if args.password:
        os.environ['ES_PASSWORD'] = args.password
        
    return args

def wait_for_elasticsearch(host, max_retries=12, delay=5):
    """Wait for Elasticsearch to become available, with Elasticsearch 8.x compatibility"""
    logger.info(f"Waiting for Elasticsearch at {host} to be available...")
    
    # Get authentication details from environment
    username = os.environ.get('ES_USERNAME', 'elastic')
    password = os.environ.get('ES_PASSWORD', '')
    api_key = os.environ.get('ES_API_KEY', '')
    
    # Setup headers and auth for requests
    headers = {}
    auth = None
    
    if api_key:
        headers['Authorization'] = f'ApiKey {api_key}'
    elif password:
        auth = (username, password)
    
    # Determine if we need to verify SSL
    verify = True
    if os.environ.get('ES_VERIFY_CERTS', 'true').lower() == 'false':
        verify = False
        # Suppress SSL warning messages if verification is disabled
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    for i in range(max_retries):
        try:
            response = requests.get(
                f"{host}/_cluster/health", 
                headers=headers, 
                auth=auth, 
                verify=verify,
                timeout=10
            )
            
            if response.status_code == 200:
                health = response.json()
                status = health.get('status')
                logger.info(f"Elasticsearch cluster status: {status}")
                if status in ['yellow', 'green']:
                    logger.info("Elasticsearch is available!")
                    return True
                else:
                    logger.warning(f"Elasticsearch status is {status}, waiting...")
            elif response.status_code == 401:
                logger.error("Authentication failed. Check ES_USERNAME and ES_PASSWORD environment variables.")
                return False
            else:
                logger.warning(f"Unexpected status code: {response.status_code}, response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"Elasticsearch not yet available, retry {i+1}/{max_retries}: {str(e)}")
        
        time.sleep(delay)
    
    logger.error("Timed out waiting for Elasticsearch")
    return False

def connect_to_elasticsearch(host):
    """Connect to Elasticsearch cluster with 8.x compatibility"""
    try:
        # Get credentials from environment variables
        username = os.environ.get('ES_USERNAME', 'elastic')
        password = os.environ.get('ES_PASSWORD', '')
        api_key = os.environ.get('ES_API_KEY', '')
        
        # Parse URL to determine if SSL is needed
        parsed_url = urlparse(host)
        use_ssl = parsed_url.scheme == 'https'
        
        # Setup SSL context if using HTTPS
        ssl_context = None
        if use_ssl:
            ssl_context = ssl.create_default_context()
            # If using self-signed certs, you can disable verification
            if os.environ.get('ES_VERIFY_CERTS', 'true').lower() == 'false':
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
        
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
        if ssl_context:
            conn_params['ssl_context'] = ssl_context
            
        # Create the Elasticsearch client with appropriate parameters
        es = Elasticsearch(**conn_params)
        
        # Test the connection
        if not es.ping():
            logger.error(f"Failed to connect to Elasticsearch at {host}")
            return None
            
        logger.info(f"Successfully connected to Elasticsearch at {host}")
        # Log the Elasticsearch version
        info = es.info()
        logger.info(f"Elasticsearch version: {info.get('version', {}).get('number', 'unknown')}")
        
        return es
    except Exception as e:
        logger.error(f"Error connecting to Elasticsearch: {str(e)}")
        return None

def setup_pipelines(es, force=False):
    """Setup ingest pipelines for temperature and air quality sensors"""
    success = True
    
    # Setup temperature sensor pipeline
    try:
        pipeline_id = "temperaturesensor_pipeline"
        if force:
            logger.info(f"Forcing recreation of pipeline: {pipeline_id}")
            es.ingest.delete_pipeline(id=pipeline_id, ignore=[404])
        
        es.ingest.put_pipeline(id=pipeline_id, body=TEMPERATURE_PIPELINE)
        logger.info(f"Successfully created pipeline: {pipeline_id}")
    except Exception as e:
        logger.error(f"Error creating temperature pipeline: {str(e)}")
        success = False
    
    # Setup air quality sensor pipeline
    try:
        pipeline_id = "airqualitysensor_pipeline"
        if force:
            logger.info(f"Forcing recreation of pipeline: {pipeline_id}")
            es.ingest.delete_pipeline(id=pipeline_id, ignore=[404])
        
        es.ingest.put_pipeline(id=pipeline_id, body=AIR_QUALITY_PIPELINE)
        logger.info(f"Successfully created pipeline: {pipeline_id}")
    except Exception as e:
        logger.error(f"Error creating air quality pipeline: {str(e)}")
        success = False
    
    return success

def setup_templates(es, force=False):
    """Setup index templates for temperature and air quality sensors"""
    success = True
    
    # Setup temperature sensor template
    try:
        template_name = "temperaturesensor_template"
        if force:
            logger.info(f"Forcing recreation of template: {template_name}")
            es.indices.delete_index_template(name=template_name, ignore=[404])
        
        es.indices.put_index_template(name=template_name, body=TEMPERATURE_TEMPLATE)
        logger.info(f"Successfully created template: {template_name}")
    except Exception as e:
        logger.error(f"Error creating temperature template: {str(e)}")
        success = False
    
    # Setup air quality sensor template
    try:
        template_name = "airqualitysensor_template"
        if force:
            logger.info(f"Forcing recreation of template: {template_name}")
            es.indices.delete_index_template(name=template_name, ignore=[404])
        
        es.indices.put_index_template(name=template_name, body=AIR_QUALITY_TEMPLATE)
        logger.info(f"Successfully created template: {template_name}")
    except Exception as e:
        logger.error(f"Error creating air quality template: {str(e)}")
        success = False
    
    return success

def setup_data_streams(es, force=False):
    """Setup data streams for temperature and air quality sensors"""
    success = True
    
    # Setup temperature sensor data stream
    try:
        stream_name = "temperaturesensor-ds"
        if force:
            logger.info(f"Forcing recreation of data stream: {stream_name}")
            es.indices.delete_data_stream(name=stream_name, ignore=[404])
        
        es.indices.create_data_stream(name=stream_name)
        logger.info(f"Successfully created data stream: {stream_name}")
    except Exception as e:
        if "resource_already_exists_exception" in str(e):
            logger.info(f"Data stream already exists: {stream_name}")
        else:
            logger.error(f"Error creating temperature data stream: {str(e)}")
            success = False
    
    # Setup air quality sensor data stream
    try:
        stream_name = "airqualitysensor-ds"
        if force:
            logger.info(f"Forcing recreation of data stream: {stream_name}")
            es.indices.delete_data_stream(name=stream_name, ignore=[404])
        
        es.indices.create_data_stream(name=stream_name)
        logger.info(f"Successfully created data stream: {stream_name}")
    except Exception as e:
        if "resource_already_exists_exception" in str(e):
            logger.info(f"Data stream already exists: {stream_name}")
        else:
            logger.error(f"Error creating air quality data stream: {str(e)}")
            success = False
    
    return success

def main():
    """Main function to run the setup process"""
    args = parse_arguments()
    
    # Wait for Elasticsearch if requested
    if args.wait and not wait_for_elasticsearch(args.host):
        sys.exit(1)
    
    # Connect to Elasticsearch
    es = connect_to_elasticsearch(args.host)
    if not es:
        sys.exit(1)
    
    # Setup components based on user selection
    success = True
    
    if args.components in ['all', 'pipelines']:
        logger.info("Setting up ingest pipelines...")
        success = setup_pipelines(es, args.force) and success
    
    if args.components in ['all', 'templates']:
        logger.info("Setting up index templates...")
        success = setup_templates(es, args.force) and success
    
    if args.components in ['all', 'datastreams']:
        logger.info("Setting up data streams...")
        success = setup_data_streams(es, args.force) and success
    
    if success:
        logger.info("Elasticsearch setup completed successfully")
    else:
        logger.error("Elasticsearch setup completed with errors")
        sys.exit(1)

if __name__ == "__main__":
    main()
