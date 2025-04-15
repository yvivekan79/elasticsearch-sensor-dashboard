#!/usr/bin/env python3
"""
Sample Data Generator

This script generates sample CSV data for temperature and air quality sensors.
"""

import argparse
import csv
import logging
import os
import random
import sys
import uuid
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Generate sample sensor data')
    parser.add_argument('--output-dir', default='.', help='Output directory for CSV files')
    parser.add_argument('--count', type=int, default=1000, help='Number of records to generate')
    parser.add_argument('--interval', type=int, default=15, help='Time interval in minutes')
    parser.add_argument('--seed', type=int, help='Random seed for reproducibility')
    parser.add_argument('--hosts', default='sensor1,sensor2,sensor3',
                      help='Comma-separated list of host names')
    return parser.parse_args()

def generate_temperature_data(count, interval, hosts, start_time=None):
    """Generate temperature sensor data"""
    if start_time is None:
        start_time = datetime.now() - timedelta(minutes=count * interval)
    
    data = []
    host_list = hosts.split(',')
    
    for i in range(count):
        timestamp = start_time + timedelta(minutes=i * interval)
        host = random.choice(host_list)
        temperature = round(random.uniform(15.0, 30.0), 2)  # Temperature between 15-30°C
        
        record = {
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'host': host,
            'temperature_value': temperature,
            'temperature_unit': 'C',
            'uuid': str(uuid.uuid4())
        }
        data.append(record)
    
    return data

def generate_air_quality_data(count, interval, hosts, start_time=None):
    """Generate air quality sensor data"""
    if start_time is None:
        start_time = datetime.now() - timedelta(minutes=count * interval)
    
    data = []
    host_list = hosts.split(',')
    
    for i in range(count):
        timestamp = start_time + timedelta(minutes=i * interval)
        host = random.choice(host_list)
        
        # Generate air quality metrics (typical ranges for urban environments)
        co = round(random.uniform(0.1, 3.0), 2)       # Carbon monoxide (0.1-3 ppm)
        no2 = round(random.uniform(10.0, 70.0), 2)    # Nitrogen dioxide (10-70 ppb)
        o3 = round(random.uniform(20.0, 80.0), 2)     # Ozone (20-80 ppb)
        pm10 = round(random.uniform(10.0, 50.0), 2)   # PM10 (10-50 μg/m³)
        pm25 = round(random.uniform(5.0, 35.0), 2)    # PM2.5 (5-35 μg/m³)
        so2 = round(random.uniform(0.5, 10.0), 2)     # Sulfur dioxide (0.5-10 ppb)
        
        record = {
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'host': host,
            'co_value': co,
            'no2_value': no2,
            'o3_value': o3,
            'pm10_value': pm10,
            'pm25_value': pm25,
            'so2_value': so2,
            'uuid': str(uuid.uuid4())
        }
        data.append(record)
    
    return data

def write_csv(data, filename, fieldnames=None):
    """Write data to CSV file"""
    if not data:
        logger.error("No data to write")
        return False
    
    if fieldnames is None:
        fieldnames = data[0].keys()
    
    try:
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        
        logger.info(f"Successfully wrote {len(data)} records to {filename}")
        return True
    except Exception as e:
        logger.error(f"Error writing CSV file: {str(e)}")
        return False

def main():
    """Main function to run the data generation process"""
    args = parse_arguments()
    
    # Set random seed if provided
    if args.seed is not None:
        random.seed(args.seed)
    
    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Generate data
    logger.info(f"Generating {args.count} temperature sensor records...")
    temperature_data = generate_temperature_data(args.count, args.interval, args.hosts)
    
    logger.info(f"Generating {args.count} air quality sensor records...")
    air_quality_data = generate_air_quality_data(args.count, args.interval, args.hosts)
    
    # Write data to CSV files
    temp_filename = os.path.join(args.output_dir, 'temperaturesensor_data.csv')
    air_filename = os.path.join(args.output_dir, 'airqualitysensor_data.csv')
    
    write_csv(temperature_data, temp_filename)
    write_csv(air_quality_data, air_filename)
    
    logger.info("Sample data generation complete")

if __name__ == "__main__":
    main()
