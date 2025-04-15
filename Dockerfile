FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
COPY requirements-elasticsearch.txt .
RUN pip install --no-cache-dir -r requirements-elasticsearch.txt

# Copy application code
COPY . .

# Default command to run the Flask app
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--reuse-port", "--reload", "main:app"]