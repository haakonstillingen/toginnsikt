#!/bin/bash

# Setup GitHub integration with Cloud Build
# Usage: ./setup-github-trigger.sh [PROJECT_ID] [REPO_NAME]

set -e

PROJECT_ID=${1:-$GOOGLE_CLOUD_PROJECT}
REPO_NAME=${2:-"togforsinkelse"}

if [ -z "$PROJECT_ID" ]; then
    echo "Error: PROJECT_ID not provided. Usage: ./setup-github-trigger.sh [PROJECT_ID] [REPO_NAME]"
    exit 1
fi

echo "🔧 Setting up GitHub integration for project: $PROJECT_ID"

# Set project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "📋 Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable sourcerepo.googleapis.com

echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Go to: https://console.cloud.google.com/cloud-build/triggers?project=$PROJECT_ID"
echo "2. Click 'Connect Repository'"
echo "3. Select GitHub and authorize"
echo "4. Choose repository: $REPO_NAME"
echo "5. Create trigger with these settings:"
echo "   - Name: togforsinkelse-deploy"
echo "   - Event: Push to a branch"
echo "   - Branch: ^main$"
echo "   - Configuration: Cloud Build configuration file"
echo "   - Location: /cloudbuild.yaml"
echo ""
echo "🎯 This will automatically deploy when you push to the main branch!"
