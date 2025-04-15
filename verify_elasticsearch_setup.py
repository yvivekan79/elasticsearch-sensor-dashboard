#!/usr/bin/env python3
"""
Elasticsearch Library Verification Script

This script verifies that all required Elasticsearch dependencies are installed correctly
and provides a simple demonstration of how to use the Elasticsearch client.
"""

import sys
import os
import json
import logging
from datetime import datetime

try:
    # Test imports of all required packages
    from elasticsearch import Elasticsearch, helpers
    from elasticsearch.exceptions import ApiError, ConnectionError as ESConnectionError
    import pandas as pd
    from dotenv import load_dotenv
    import requests
    import urllib3

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    def verify_elasticsearch_imports():
        """Verify that all Elasticsearch-related packages are imported successfully."""
        imports = {
            "elasticsearch": "Elasticsearch Client Library",
            "pandas": "Data Analysis Library",
            "dotenv": "Environment Variable Manager",
            "requests": "HTTP Client Library",
            "urllib3": "HTTP Client Library (used by elasticsearch)"
        }
        
        logger.info("Verifying Python package imports...")
        for package, description in imports.items():
            logger.info(f"✓ {package}: {description} - Successfully imported")
        
        return True

    def demonstrate_elasticsearch_client_creation():
        """Demonstrate how to create an Elasticsearch client with proper configuration."""
        logger.info("Demonstrating Elasticsearch client creation (no connection required)...")
        
        # Sample host configuration
        host = "http://localhost:9200"
        username = "elastic"
        password = "changeme"
        
        # Configure connection options for Elasticsearch 8.x
        conn_params = {
            'hosts': [host],
            'request_timeout': 30,
            'retry_on_timeout': True,
            'basic_auth': (username, password)
        }
        
        # Create the Elasticsearch client with appropriate parameters (but don't connect)
        logger.info(f"Creating Elasticsearch client for host: {host}")
        es = Elasticsearch(**conn_params)
        
        logger.info(f"✓ Elasticsearch client object created successfully")
        logger.info(f"✓ Connection parameters configured properly")
        
        return True

    def demonstrate_index_template_creation():
        """Demonstrate how to create an index template (no connection required)."""
        logger.info("Demonstrating index template creation (no connection required)...")
        
        # Sample template definition
        template = {
            "index_patterns": ["sensor-*"],
            "data_stream": {},
            "template": {
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 1
                },
                "mappings": {
                    "properties": {
                        "@timestamp": {"type": "date"},
                        "value": {"type": "float"},
                        "sensor_id": {"type": "keyword"},
                        "location": {"type": "geo_point"}
                    }
                }
            }
        }
        
        # Print template as JSON
        logger.info(f"Sample index template JSON:")
        print(json.dumps(template, indent=2))
        
        logger.info(f"✓ Index template created successfully")
        
        return True

    def demonstrate_data_stream_document():
        """Demonstrate how to create a data stream document (no connection required)."""
        logger.info("Demonstrating data stream document creation (no connection required)...")
        
        # Sample document
        doc = {
            "_index": "sensor-data",
            "@timestamp": datetime.now().isoformat(),
            "sensor_id": "temp-1234",
            "value": 25.6,
            "unit": "celsius",
            "location": {
                "lat": 40.7128,
                "lon": -74.0060
            }
        }
        
        # Print document as JSON
        logger.info(f"Sample document JSON:")
        print(json.dumps(doc, indent=2))
        
        logger.info(f"✓ Data stream document created successfully")
        
        return True

    def main():
        """Main function to run verification."""
        logger.info("Starting Elasticsearch library verification")
        
        # Verify imports
        if not verify_elasticsearch_imports():
            logger.error("Failed to verify imports")
            return 1
        
        # Demonstrate client creation
        if not demonstrate_elasticsearch_client_creation():
            logger.error("Failed to demonstrate client creation")
            return 1
        
        # Demonstrate template creation
        if not demonstrate_index_template_creation():
            logger.error("Failed to demonstrate template creation")
            return 1
        
        # Demonstrate document creation
        if not demonstrate_data_stream_document():
            logger.error("Failed to demonstrate document creation")
            return 1
        
        logger.info("")
        logger.info("===============================================")
        logger.info("✓ All Elasticsearch library tests passed!")
        logger.info("✓ All required packages are installed correctly")
        logger.info("===============================================")
        logger.info("")
        logger.info("To use these packages in your scripts:")
        logger.info("1. Import them at the top of your scripts")
        logger.info("2. Create clients with the appropriate parameters")
        logger.info("3. Use the client to interact with Elasticsearch")
        logger.info("")
        logger.info("For production use with Docker:")
        logger.info("- Use the provided docker-compose.yml file")
        logger.info("- All dependencies are pre-installed in the Docker images")
        logger.info("")
        
        return 0

except ImportError as e:
    print(f"Error: {str(e)}")
    print("One or more required packages are not installed.")
    print("To install them, run:")
    print("  ./install_dependencies.sh")
    print("  OR")
    print("  pip install -r requirements-elasticsearch.txt")
    sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())