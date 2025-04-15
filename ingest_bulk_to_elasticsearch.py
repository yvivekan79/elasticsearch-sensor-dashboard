#!/usr/bin/env python3
"""
Elasticsearch Bulk Ingestion Script

This script ingests CSV data into Elasticsearch data streams.
It supports temperature and air quality sensor data formats.
"""

import argparse
import csv
import json
import logging
import os
import sys
import uuid
import ssl
from datetime import datetime
from urllib.parse import urlparse

import pandas as pd
import requests
from elasticsearch import Elasticsearch, helpers
from elasticsearch.exceptions import ApiError, ConnectionError as ESConnectionError
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
    parser = argparse.ArgumentParser(description='Ingest CSV data into Elasticsearch')
    parser.add_argument('--csv', required=True, help='Path to the CSV file')
    parser.add_argument('--index', required=True, help='Target Elasticsearch data stream')
    parser.add_argument('--host', default=os.environ.get('ES_HOST', 'http://localhost:9200'), 
                        help='Elasticsearch host URL')
    parser.add_argument('--batch-size', type=int, default=1000, 
                        help='Batch size for bulk ingestion')
    parser.add_argument('--timestamp-field', default='timestamp', 
                        help='Field name for timestamp in the CSV')
    parser.add_argument('--timestamp-format', default='%Y-%m-%d %H:%M:%S', 
                        help='Format for parsing timestamps')
    parser.add_argument('--dry-run', action='store_true', 
                        help='Print documents instead of ingesting')
    return parser.parse_args()

def connect_to_elasticsearch(host):
    """Connect to Elasticsearch cluster with 8.x compatibility"""
    try:
        # Get credentials from environment variables
        username = os.environ.get('ES_USERNAME', 'elastic')
        password = os.environ.get('ES_PASSWORD', 'changeme')
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

def prepare_temperature_document(row, index_name):
    """Prepare a temperature sensor document for ingestion"""
    doc = {
        "_index": index_name,
        "@timestamp": row.get("timestamp"),
        "measurement_name": "temperature",
        "tag": {
            "host": row.get("host", "unknown"),
            "sensor_type": "temperature"
        },
        "uuid": str(uuid.uuid4()),
        "temperaturesensor": {
            "telemetry_temperature_value": float(row.get("temperature_value", 0)),
            "telemetry_temperature_unit": row.get("temperature_unit", "C")
        }
    }
    return doc

def prepare_air_quality_document(row, index_name):
    """Prepare an air quality sensor document for ingestion"""
    doc = {
        "_index": index_name,
        "@timestamp": row.get("timestamp"),
        "measurement_name": "air_quality",
        "tag": {
            "host": row.get("host", "unknown"),
            "sensor_type": "air_quality"
        },
        "uuid": str(uuid.uuid4()),
        "airqualitysensor": {
            "telemetry_co_value": float(row.get("co_value", 0)),
            "telemetry_no2_value": float(row.get("no2_value", 0)),
            "telemetry_o3_value": float(row.get("o3_value", 0)),
            "telemetry_pm10_value": float(row.get("pm10_value", 0)),
            "telemetry_pm25_value": float(row.get("pm25_value", 0)),
            "telemetry_so2_value": float(row.get("so2_value", 0))
        }
    }
    return doc

def prepare_documents(df, index_name):
    """Prepare documents for bulk ingestion based on index type"""
    docs = []
    
    if "temperaturesensor" in index_name.lower():
        for _, row in df.iterrows():
            doc = prepare_temperature_document(row, index_name)
            docs.append(doc)
    elif "airqualitysensor" in index_name.lower():
        for _, row in df.iterrows():
            doc = prepare_air_quality_document(row, index_name)
            docs.append(doc)
    else:
        logger.error(f"Unknown index type: {index_name}")
        return []
    
    return docs

def bulk_ingest(es, documents, batch_size, dry_run):
    """Perform bulk ingestion of documents into Elasticsearch"""
    if dry_run:
        for doc in documents[:5]:  # Print first 5 documents as a sample
            logger.info(f"Document sample (dry run): {json.dumps(doc, indent=2)}")
        logger.info(f"Dry run complete. Would have ingested {len(documents)} documents")
        return True

    total_docs = len(documents)
    success_count = 0
    error_count = 0
    
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i+batch_size]
        try:
            resp = helpers.bulk(es, batch)
            success_count += resp[0]
            error_count += len(resp[1]) if len(resp) > 1 else 0
            logger.info(f"Ingested batch {i//batch_size + 1}/{(total_docs//batch_size) + 1}")
        except Exception as e:
            logger.error(f"Error during bulk ingestion: {str(e)}")
            error_count += len(batch)
    
    logger.info(f"Ingestion complete. Successfully ingested {success_count}/{total_docs} documents")
    if error_count > 0:
        logger.warning(f"Failed to ingest {error_count}/{total_docs} documents")
    
    return error_count == 0

def main():
    """Main function to run the ingestion process"""
    args = parse_arguments()
    
    # Connect to Elasticsearch
    es = connect_to_elasticsearch(args.host)
    if not es:
        sys.exit(1)
    
    # Read CSV file
    try:
        logger.info(f"Reading data from {args.csv}")
        df = pd.read_csv(args.csv)
        
        # Convert timestamp column to proper format
        if args.timestamp_field in df.columns:
            df[args.timestamp_field] = pd.to_datetime(df[args.timestamp_field], 
                                                    format=args.timestamp_format)
            # Convert to ISO format for Elasticsearch
            df["timestamp"] = df[args.timestamp_field].dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        else:
            logger.warning(f"Timestamp field '{args.timestamp_field}' not found in CSV. Using current time.")
            df["timestamp"] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        
        # Prepare documents for ingestion
        logger.info(f"Preparing documents for ingestion into {args.index}")
        documents = prepare_documents(df, args.index)
        
        if not documents:
            logger.error("No valid documents to ingest")
            sys.exit(1)
        
        # Perform bulk ingestion
        logger.info(f"Starting bulk ingestion of {len(documents)} documents")
        success = bulk_ingest(es, documents, args.batch_size, args.dry_run)
        
        if not success and not args.dry_run:
            logger.error("Ingestion completed with errors")
            sys.exit(1)
        
        logger.info("Ingestion completed successfully")
        
    except FileNotFoundError:
        logger.error(f"CSV file not found: {args.csv}")
        sys.exit(1)
    except pd.errors.ParserError as e:
        logger.error(f"Error parsing CSV file: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
