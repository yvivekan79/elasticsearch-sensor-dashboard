from flask import Flask, render_template, redirect, url_for, flash, request
import os
import logging
import threading
import time
import ssl
from urllib.parse import urlparse
from elasticsearch import Elasticsearch
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key")

# Elasticsearch configuration
ES_HOST = os.environ.get("ES_HOST", "http://localhost:9200")
es_client = None

def create_elasticsearch_client():
    """Create Elasticsearch client with 8.x compatibility settings"""
    # Get credentials from environment variables
    username = os.environ.get('ES_USERNAME', 'elastic')
    password = os.environ.get('ES_PASSWORD', '')
    api_key = os.environ.get('ES_API_KEY', '')
    
    # Parse URL to determine if SSL is needed
    parsed_url = urlparse(ES_HOST)
    use_ssl = parsed_url.scheme == 'https'
    
    # Setup connection params
    conn_params = {
        'hosts': [ES_HOST],
        'request_timeout': 10,  # Reduce timeout to avoid long waits
        'retry_on_timeout': True,
        'max_retries': 2  # Limit retries to avoid excessive delays
    }
    
    # Add authentication
    if api_key:
        conn_params['api_key'] = api_key
    elif password:
        conn_params['basic_auth'] = (username, password)
    
    # Setup SSL if needed
    if use_ssl:
        ssl_context = ssl.create_default_context()
        # If using self-signed certs, you can disable verification
        if os.environ.get('ES_VERIFY_CERTS', 'true').lower() == 'false':
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        conn_params['ssl_context'] = ssl_context
    
    return Elasticsearch(**conn_params)

def connect_elasticsearch():
    """Connect to Elasticsearch with retry logic and 8.x compatibility"""
    global es_client
    max_retries = 2  # Reduce retries to avoid excessive delays
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Create new client
            es_client = create_elasticsearch_client()
            if es_client.ping():
                logger.info("Connected to Elasticsearch")
                info = es_client.info()
                logger.info(f"Elasticsearch version: {info.get('version', {}).get('number', 'unknown')}")
                return es_client
            else:
                raise Exception("Elasticsearch ping failed")
        except Exception as e:
            retry_count += 1
            wait_time = retry_count * 5
            logger.warning(f"Connection to Elasticsearch failed, retrying in {wait_time} seconds... ({retry_count}/{max_retries})")
            logger.warning(f"Error: {str(e)}")
            time.sleep(wait_time)
    
    logger.error("Failed to connect to Elasticsearch after multiple attempts")
    return None

def check_es_connection_async():
    """Check Elasticsearch connection in a separate thread"""
    global es_client
    
    # Initial connection attempt
    es_client = connect_elasticsearch()
    
    # Setup periodic connection check (every 60 seconds)
    while True:
        time.sleep(60)
        try:
            if not es_client or not es_client.ping():
                logger.info("Elasticsearch connection lost or not established, attempting to reconnect...")
                es_client = connect_elasticsearch()
        except Exception as e:
            logger.warning(f"Error checking Elasticsearch connection: {str(e)}")
            es_client = None

# Start ES connection in background thread
threading.Thread(target=check_es_connection_async, daemon=True).start()

@app.route('/')
def index():
    """Render the main dashboard page"""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Render the Kibana dashboard page"""
    kibana_url = os.environ.get('KIBANA_URL', 'http://localhost:5601')
    return render_template('dashboard.html', kibana_url=kibana_url)

@app.route('/status')
def status():
    """Check the Elasticsearch connection status"""
    # If Elasticsearch client exists, attempt to get status
    if es_client:
        try:
            # Try to ping Elasticsearch
            if es_client.ping():
                try:
                    # Check if the data streams exist
                    temp_ds_exists = es_client.indices.exists_data_stream(name="temperaturesensor-ds")
                    air_ds_exists = es_client.indices.exists_data_stream(name="airqualitysensor-ds")
                    
                    # Get basic stats about the data streams
                    status_data = {
                        "elasticsearch": "connected",
                        "temperaturesensor_ds": "available" if temp_ds_exists else "not found",
                        "airqualitysensor_ds": "available" if air_ds_exists else "not found"
                    }
                    
                    # If data streams exist, get document counts
                    if temp_ds_exists:
                        temp_count = es_client.count(index="temperaturesensor-ds")
                        status_data["temperaturesensor_count"] = temp_count.get("count", 0)
                        
                    if air_ds_exists:
                        air_count = es_client.count(index="airqualitysensor-ds")
                        status_data["airqualitysensor_count"] = air_count.get("count", 0)
                        
                    return status_data
                except Exception as e:
                    logger.error(f"Error checking data streams: {str(e)}")
                    return {
                        "elasticsearch": "error", 
                        "error": str(e),
                        "temperaturesensor_ds": "unknown",
                        "airqualitysensor_ds": "unknown"
                    }
            else:
                # Ping failed
                return {
                    "elasticsearch": "disconnected", 
                    "message": "Elasticsearch is running but ping failed",
                    "temperaturesensor_ds": "unknown",
                    "airqualitysensor_ds": "unknown"
                }
        except Exception as e:
            # Connection error
            logger.error(f"Error connecting to Elasticsearch: {str(e)}")
            return {
                "elasticsearch": "error", 
                "error": str(e),
                "temperaturesensor_ds": "unknown",
                "airqualitysensor_ds": "unknown"
            }
    else:
        # No client at all
        return {
            "elasticsearch": "disconnected",
            "message": "Elasticsearch client not initialized",
            "temperaturesensor_ds": "unknown",
            "airqualitysensor_ds": "unknown"
        }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
