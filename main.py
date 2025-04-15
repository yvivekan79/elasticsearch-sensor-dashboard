from flask import Flask, render_template, redirect, url_for, flash, request
import os
import logging
import threading
import time
from elasticsearch import Elasticsearch
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key")

# Elasticsearch configuration
ES_HOST = os.environ.get("ES_HOST", "http://localhost:9200")
es_client = None

def connect_elasticsearch():
    """Connect to Elasticsearch with retry logic"""
    global es_client
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            es_client = Elasticsearch(ES_HOST)
            if es_client.ping():
                logger.info("Connected to Elasticsearch")
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
    connect_elasticsearch()

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
    if es_client and es_client.ping():
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
            return {"elasticsearch": "error", "error": str(e)}
    else:
        return {"elasticsearch": "disconnected"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
