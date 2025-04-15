#!/bin/bash
# Script to install Python dependencies for Elasticsearch Sensor Dashboard

# Exit on any error
set -e

echo "Installing Python dependencies for Elasticsearch Sensor Dashboard..."

# Check if pip is available
if ! command -v pip &> /dev/null
then
    echo "Error: pip is not installed. Please install Python 3.8+ and pip before continuing."
    exit 1
fi

# Install dependencies from requirements file
pip install -r requirements-elasticsearch.txt

echo "Successfully installed dependencies!"
echo "You can now run the application with: python main.py"
echo "Or set up Elasticsearch with: python setup_elasticsearch.py"