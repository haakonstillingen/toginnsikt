"""
Cloud configuration settings for the enhanced commute data collector
"""

import os
from google.cloud import secretmanager

# API Configuration
ENTUR_API_URL = "https://api.entur.io/journey-planner/v3/graphql"
CLIENT_NAME = "togforsinkelse-enhanced-collector"

# Google Cloud Project ID
PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT', 'toginnsikt')

def get_secret(secret_name):
    """
    Retrieve a secret from Google Cloud Secret Manager
    
    Args:
        secret_name (str): Name of the secret to retrieve
        
    Returns:
        str: The secret value
        
    Raises:
        Exception: If secret cannot be retrieved
    """
    try:
        client = secretmanager.SecretManagerServiceClient()
        secret_path = f"projects/{PROJECT_ID}/secrets/{secret_name}/versions/latest"
        response = client.access_secret_version(request={"name": secret_path})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        raise Exception(f"Failed to retrieve secret '{secret_name}': {str(e)}")

# Database Configuration (Cloud SQL PostgreSQL)
# Try to get credentials from Secret Manager first, fallback to environment variables
try:
    DB_HOST = get_secret('toginnsikt-db-host')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = get_secret('toginnsikt-db-name')
    DB_USER = get_secret('toginnsikt-db-user')
    DB_PASSWORD = get_secret('toginnsikt-db-password')
    print("✅ Database credentials loaded from Secret Manager")
except Exception as e:
    print(f"⚠️ Failed to load secrets from Secret Manager: {e}")
    print("🔄 Falling back to environment variables")
    # Fallback to environment variables (for local development)
    DB_HOST = os.getenv('DB_HOST', '35.228.203.238')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'togforsinkelse_enhanced')
    DB_USER = os.getenv('DB_USER', 'togforsinkelse-user')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'fPl21YN#cF0RngM9')

# Cloud SQL Connection
CLOUD_SQL_CONNECTION_NAME = os.getenv('CLOUD_SQL_CONNECTION_NAME', 'toginnsikt:europe-north1:togforsinkelse-db')

# Collection Settings
COLLECTION_INTERVAL_MINUTES = 15  # Default interval
DATA_RETENTION_HOURS = 2
RETRY_DELAY_MINUTES = 5

# Route Configuration
COMMUTE_ROUTES = [
    {
        'route_name': 'Morning Commute',
        'source_station_id': 'NSR:StopPlace:59638',
        'source_station_name': 'Myrvoll',
        'target_station_id': 'NSR:StopPlace:337',
        'target_station_name': 'Oslo S',
        'final_destination_pattern': 'Lysaker|Stabekk',
        'direction': 'westbound'
    },
    {
        'route_name': 'Afternoon Commute',
        'source_station_id': 'NSR:StopPlace:337',
        'source_station_name': 'Oslo S',
        'target_station_id': 'NSR:StopPlace:59638',
        'target_station_name': 'Myrvoll',
        'final_destination_pattern': 'Ski',
        'direction': 'eastbound'
    }
]

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = 'enhanced_collector.log'
