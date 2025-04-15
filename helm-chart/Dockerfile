FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .
COPY setup_elasticsearch.py .
COPY ingest_bulk_to_elasticsearch.py .
COPY kibana_setup.py .
COPY kibana_telemetry_dashboard.json .
COPY temperaturesensor_data.csv .
COPY airqualitysensor_data.csv .
COPY sample_data_generator.py .
COPY static/ static/
COPY templates/ templates/

# Expose port
EXPOSE 5000

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "main:app"]