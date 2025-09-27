#!/bin/bash

# Deploy Togforsinkelse Data Collector to Google Cloud
# Usage: ./deploy.sh [PROJECT_ID]

set -e

# Get project ID from argument or environment
PROJECT_ID=${1:-$GOOGLE_CLOUD_PROJECT}

if [ -z "$PROJECT_ID" ]; then
    echo "Error: PROJECT_ID not provided. Usage: ./deploy.sh [PROJECT_ID]"
    echo "Or set GOOGLE_CLOUD_PROJECT environment variable"
    exit 1
fi

echo "🚀 Deploying to project: $PROJECT_ID"

# Set project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "📋 Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable cloudscheduler.googleapis.com

# Create Cloud SQL instance (if it doesn't exist)
echo "🗄️ Setting up Cloud SQL..."
gcloud sql instances create togforsinkelse-db \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=europe-north1 \
    --storage-type=SSD \
    --storage-size=10GB \
    --backup-start-time=03:00 \
    --enable-bin-log \
    --retained-backups-count=7 \
    --retained-transaction-log-days=7 \
    --maintenance-window-day=SUN \
    --maintenance-window-hour=04 \
    --maintenance-release-channel=production \
    --quiet || echo "Cloud SQL instance already exists"

# Create enhanced collection database
echo "📊 Creating enhanced collection database..."
gcloud sql databases create togforsinkelse_enhanced \
    --instance=togforsinkelse-db \
    --quiet || echo "Enhanced database already exists"

# Create database user
echo "👤 Creating database user..."
gcloud sql users create togforsinkelse-user \
    --instance=togforsinkelse-db \
    --password=fPl21YN#cF0RngM9 \
    --quiet || echo "User already exists"

# Get connection name
CONNECTION_NAME=$(gcloud sql instances describe togforsinkelse-db --format="value(connectionName)")

# Build and deploy to Cloud Run
echo "🏗️ Building and deploying to Cloud Run..."
gcloud builds submit --config cloudbuild.yaml

# Note: Enhanced collection system runs continuously with built-in scheduling
echo "⏰ Enhanced collection system will run continuously with adaptive scheduling"

echo "✅ Enhanced collection system deployed!"
echo ""
echo "📋 System Features:"
echo "  - Two-tier collection: Planned (03:00 UTC) + Actual (continuous)"
echo "  - Adaptive scheduling: 15min (rush), 30min (regular), 60min (night)"
echo "  - Retry logic: +5min timing with 2-hour data retention"
echo "  - Route-specific: Myrvoll↔Oslo S with proper filtering"
echo ""
echo "🔗 Useful commands:"
echo "  View logs: gcloud logging read 'resource.type=cloud_run_revision' --limit=50"
echo "  Check Cloud Run: gcloud run services list"
echo "  Check Cloud SQL: gcloud sql instances list"
echo "  Monitor collection: Check logs for collection statistics"
