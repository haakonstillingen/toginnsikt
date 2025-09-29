"""
Migration-specific configuration
Simplified config for migration system without Google Cloud dependencies
"""

import os

# Database Configuration
DB_HOST = os.getenv('DB_HOST', '35.228.203.238')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'togforsinkelse_enhanced')
DB_USER = os.getenv('DB_USER', 'togforsinkelse-user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'fPl21YN#cF0RngM9')

# Cloud SQL Connection (for cloud deployment)
CLOUD_SQL_CONNECTION_NAME = os.getenv('CLOUD_SQL_CONNECTION_NAME', '')

# Logging Configuration
LOG_FILE = 'migration_runner.log'
