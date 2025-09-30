"""
Migration-specific configuration
Uses Google Cloud Secret Manager for secure credential management
"""

import os
from google.cloud import secretmanager

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
    print("✅ Migration: Database credentials loaded from Secret Manager")
except Exception as e:
    print(f"⚠️ Migration: Failed to load secrets from Secret Manager: {e}")
    print("🔄 Migration: Falling back to environment variables")
    # Fallback to environment variables (for local development)
    # NOTE: No default values for security - these MUST be set in environment
    DB_HOST = os.getenv('DB_HOST')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME')
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    
    # Validate that required credentials are available
    if not all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]):
        raise Exception("Database credentials not available. Set environment variables or configure Secret Manager.")

# Cloud SQL Connection (for cloud deployment)
CLOUD_SQL_CONNECTION_NAME = os.getenv('CLOUD_SQL_CONNECTION_NAME', 'toginnsikt:europe-north1:togforsinkelse-db')

# Logging Configuration
LOG_FILE = 'migration_runner.log'