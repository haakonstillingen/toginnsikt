# Dashboard Deployment Guide

This guide explains how to deploy the Toginnsikt Next.js dashboard to Google Cloud Run.

## Prerequisites

- Google Cloud Project with billing enabled
- `gcloud` CLI installed and authenticated
- Cloud Build API enabled
- Cloud Run API enabled

## Environment Variables

The dashboard requires the following environment variables to connect to the database:

- `DB_HOST` - Database hostname (e.g., `35.228.203.238`)
- `DB_PORT` - Database port (default: `5432`)
- `DB_NAME` - Database name (e.g., `togforsinkelse_enhanced`)
- `DB_USER` - Database username (e.g., `togforsinkelse-user`)
- `DB_PASSWORD` - Database password (sensitive - use Secret Manager)

## Deployment Options

### Option 1: Using deploy.sh Script (Recommended)

```bash
cd toginnsikt-dashboard
./deploy.sh [PROJECT_ID]
```

This script will:
1. Enable required APIs
2. Build the Docker image
3. Deploy to Cloud Run with environment variables

### Option 2: Using Cloud Build Directly

```bash
gcloud builds submit --config toginnsikt-dashboard/cloudbuild.yaml
```

### Option 3: Using Secret Manager (Most Secure)

For production deployments, store the database password in Google Secret Manager:

```bash
# Create secret
echo -n "fPl21YN#cF0RngM9" | gcloud secrets create db-password \
  --data-file=- \
  --replication-policy="automatic"

# Grant Cloud Run access to the secret
gcloud secrets add-iam-policy-binding db-password \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

Then update `cloudbuild.yaml` to use the secret reference (already configured).

## Manual Environment Variable Setup

If you prefer to set environment variables manually in Cloud Run:

```bash
gcloud run services update togginnsikt-dashboard \
  --region=europe-north1 \
  --set-env-vars="DB_HOST=35.228.203.238,DB_PORT=5432,DB_NAME=togforsinkelse_enhanced,DB_USER=togforsinkelse-user" \
  --update-secrets="DB_PASSWORD=db-password:latest"
```

## Verification

After deployment, verify the service is running:

```bash
# Get service URL
gcloud run services describe togginnsikt-dashboard \
  --region=europe-north1 \
  --format='value(status.url)'

# Check logs
gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=toginnsikt-dashboard' \
  --limit=50
```

## Troubleshooting

### Environment Variables Not Set

If the dashboard fails to connect to the database, check that all environment variables are set:

```bash
gcloud run services describe togginnsikt-dashboard \
  --region=europe-north1 \
  --format='value(spec.template.spec.containers[0].env)'
```

### Database Connection Issues

1. Verify Cloud SQL instance is running
2. Check that the database credentials are correct
3. Ensure Cloud Run has network access to Cloud SQL (if using private IP)
4. Check Cloud Run logs for connection errors

### Build Failures

If the Docker build fails:
1. Verify Node.js version compatibility
2. Check that all dependencies are in `package.json`
3. Review Cloud Build logs for specific errors

## Security Best Practices

1. **Never commit secrets to version control** - Use `.env.local` for local development (git-ignored)
2. **Use Secret Manager for production** - Store sensitive values in Google Secret Manager
3. **Limit access** - Use IAM roles to restrict who can access secrets
4. **Rotate credentials** - Regularly update database passwords and secrets
5. **Monitor access** - Review Cloud Run logs and Secret Manager access logs

## Local Development

For local development, create a `.env.local` file in `toginnsikt-dashboard/`:

```bash
DB_HOST=35.228.203.238
DB_PORT=5432
DB_NAME=togforsinkelse_enhanced
DB_USER=togforsinkelse-user
DB_PASSWORD=your-password-here
```

This file is git-ignored and will not be committed to version control.



