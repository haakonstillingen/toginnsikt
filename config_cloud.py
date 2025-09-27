"""
Cloud configuration settings for the enhanced commute data collector
"""

import os

# API Configuration
ENTUR_API_URL = "https://api.entur.io/journey-planner/v3/graphql"
CLIENT_NAME = "togforsinkelse-enhanced-collector"

# Database Configuration (Cloud SQL PostgreSQL)
DB_HOST = os.getenv('DB_HOST', '35.228.203.238')  # Cloud SQL external IP
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
        'direction': 'morning'
    },
    {
        'route_name': 'Afternoon Commute',
        'source_station_id': 'NSR:StopPlace:337',
        'source_station_name': 'Oslo S',
        'target_station_id': 'NSR:StopPlace:59638',
        'target_station_name': 'Myrvoll',
        'final_destination_pattern': 'Ski',
        'direction': 'afternoon'
    }
]

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = 'enhanced_collector.log'
