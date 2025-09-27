# Use Python 3.13 slim image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the enhanced collection system
COPY enhanced_commute_collector_cloud.py .
COPY collection_scheduler.py .
COPY config_cloud.py .
COPY cloud_run_server.py .
COPY migrations/ ./migrations/

# Create directory for database
RUN mkdir -p /app/data

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DB_NAME=togforsinkelse_enhanced
ENV DB_USER=togforsinkelse-user
ENV DB_PASSWORD=fPl21YN#cF0RngM9
ENV DB_HOST=35.228.203.238
ENV DB_PORT=5432

# Run the enhanced collection scheduler with HTTP server
CMD ["python", "cloud_run_server.py"]
