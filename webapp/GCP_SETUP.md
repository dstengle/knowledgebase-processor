# Google Cloud Platform Setup for GCR Publishing

This guide walks you through setting up Google Container Registry (GCR) publishing for the Knowledge Base Processor webapp via GitHub Actions.

## Prerequisites

- A Google Cloud Platform (GCP) account
- A GCP project with billing enabled
- GitHub repository admin access
- `gcloud` CLI installed (optional, for verification)

## Step 1: Create a GCP Project

If you don't already have a GCP project:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Enter a project name (e.g., `kb-processor`)
4. Note your **Project ID** (different from project name)
5. Click "Create"

## Step 2: Enable Required APIs

Enable the following APIs in your GCP project:

```bash
gcloud services enable containerregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable storage-api.googleapis.com
```

Or via the Console:
1. Navigate to "APIs & Services" → "Library"
2. Search for and enable:
   - Container Registry API
   - Cloud Build API
   - Cloud Storage API

## Step 3: Create a Service Account

Create a service account with permissions to push to GCR:

### Using gcloud CLI:

```bash
# Set your project ID
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# Create service account
gcloud iam service-accounts create github-actions-gcr \
    --display-name="GitHub Actions GCR Publisher" \
    --description="Service account for GitHub Actions to publish Docker images to GCR"

# Grant necessary permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:github-actions-gcr@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:github-actions-gcr@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"

# Create and download the key
gcloud iam service-accounts keys create gcr-key.json \
    --iam-account=github-actions-gcr@$PROJECT_ID.iam.gserviceaccount.com
```

### Using GCP Console:

1. Navigate to "IAM & Admin" → "Service Accounts"
2. Click "Create Service Account"
3. **Name**: `github-actions-gcr`
4. **Description**: `Service account for GitHub Actions to publish Docker images to GCR`
5. Click "Create and Continue"
6. Add the following roles:
   - `Storage Admin` (roles/storage.admin)
   - `Storage Object Admin` (roles/storage.objectAdmin)
7. Click "Continue" → "Done"
8. Click on the newly created service account
9. Go to "Keys" tab → "Add Key" → "Create new key"
10. Select "JSON" format
11. Click "Create" (the key will download automatically)

⚠️ **Important**: Keep the JSON key file secure. Do not commit it to your repository!

## Step 4: Configure GitHub Secrets

Add the following secrets to your GitHub repository:

1. Go to your GitHub repository
2. Navigate to "Settings" → "Secrets and variables" → "Actions"
3. Click "New repository secret"

Add these secrets:

### GCP_PROJECT_ID
- **Name**: `GCP_PROJECT_ID`
- **Value**: Your GCP Project ID (e.g., `kb-processor-123456`)

### GCP_SA_KEY
- **Name**: `GCP_SA_KEY`
- **Value**: The entire contents of the `gcr-key.json` file

To get the key contents:
```bash
cat gcr-key.json
```

Copy and paste the entire JSON object (including the curly braces).

## Step 5: Verify the Setup

### Test Locally (Optional)

Authenticate with the service account locally:

```bash
# Authenticate Docker with GCR
gcloud auth activate-service-account --key-file=gcr-key.json
gcloud auth configure-docker

# Build and push test image
docker build -t gcr.io/$PROJECT_ID/kb-processor-webapp:test -f webapp/Dockerfile .
docker push gcr.io/$PROJECT_ID/kb-processor-webapp:test
```

### Trigger GitHub Action

1. Make a change to the `webapp/` directory
2. Commit and push to your branch
3. Go to "Actions" tab in GitHub
4. Watch the "Build and Push Webapp to GCR" workflow run
5. Check the workflow summary for image details

## Step 6: Pull and Run the Image

Once published, pull and run the image:

```bash
# Authenticate Docker (if not already done)
gcloud auth configure-docker

# Pull the image
docker pull gcr.io/$PROJECT_ID/kb-processor-webapp:latest

# Run the container
docker run -p 8000:8000 gcr.io/$PROJECT_ID/kb-processor-webapp:latest

# Access the webapp
open http://localhost:8000
```

## Managing Images

### List Images

```bash
gcloud container images list --repository=gcr.io/$PROJECT_ID
```

### List Tags

```bash
gcloud container images list-tags gcr.io/$PROJECT_ID/kb-processor-webapp
```

### Delete an Image

```bash
gcloud container images delete gcr.io/$PROJECT_ID/kb-processor-webapp:TAG --quiet
```

### View Image Details

```bash
gcloud container images describe gcr.io/$PROJECT_ID/kb-processor-webapp:TAG
```

## Image Registry Structure

Images are stored at:
```
gcr.io/[PROJECT_ID]/kb-processor-webapp:[TAG]
```

Available tags after publishing:
- `latest` - Latest version from main branch
- `stable` - Alias for latest
- `<commit-sha>` - Specific commit (e.g., `a1b2c3d`)
- `<timestamp>` - Build timestamp (e.g., `20240115-143022`)
- `<branch-name>` - Branch-specific builds

## Troubleshooting

### Permission Denied Errors

**Issue**: GitHub Action fails with "Permission denied" when pushing to GCR.

**Solution**: Verify the service account has the correct roles:
```bash
gcloud projects get-iam-policy $PROJECT_ID \
    --flatten="bindings[].members" \
    --filter="bindings.members:serviceAccount:github-actions-gcr@$PROJECT_ID.iam.gserviceaccount.com"
```

Ensure both `roles/storage.admin` and `roles/storage.objectAdmin` are present.

### Invalid Credentials

**Issue**: "Invalid credentials" error in GitHub Action.

**Solution**:
1. Verify the `GCP_SA_KEY` secret contains the full JSON key
2. Ensure the JSON is valid (no extra spaces or formatting)
3. Check that the service account key hasn't been deleted or disabled

### API Not Enabled

**Issue**: "Container Registry API has not been used" error.

**Solution**: Enable the API:
```bash
gcloud services enable containerregistry.googleapis.com
```

### Build Fails for ARM64

**Issue**: Build fails with "no matching manifest for linux/arm64" error.

**Solution**: Remove the `platforms` line in the workflow file or build only for `linux/amd64`:
```yaml
platforms: linux/amd64
```

### Rate Limiting

**Issue**: "Too many requests" error during build.

**Solution**:
- GitHub Actions has build minute limits
- GCR has bandwidth/storage limits on free tier
- Check your GCP billing and quotas

## Security Best Practices

1. **Rotate Service Account Keys Regularly**
   ```bash
   # Create new key
   gcloud iam service-accounts keys create new-key.json \
       --iam-account=github-actions-gcr@$PROJECT_ID.iam.gserviceaccount.com

   # Update GitHub secret
   # Delete old key
   gcloud iam service-accounts keys delete OLD_KEY_ID \
       --iam-account=github-actions-gcr@$PROJECT_ID.iam.gserviceaccount.com
   ```

2. **Use Least Privilege**: Only grant necessary permissions
3. **Enable MFA**: Enable two-factor authentication on your GCP account
4. **Monitor Access**: Review service account activity in Cloud Audit Logs
5. **Scan Images**: Use vulnerability scanning (available in GCR)

## Cost Considerations

GCR costs are based on:
- **Storage**: ~$0.026/GB/month
- **Network Egress**: Varies by region ($0.12-$0.23/GB)
- **Operations**: Free for most operations

Estimated cost for this project:
- Image size: ~500MB
- With 10 tags: ~5GB storage
- Monthly cost: ~$0.13/month

[GCP Pricing Calculator](https://cloud.google.com/products/calculator)

## Alternative: Artifact Registry

Google recommends migrating to Artifact Registry (next-gen GCR):

```bash
# Enable Artifact Registry API
gcloud services enable artifactregistry.googleapis.com

# Create repository
gcloud artifacts repositories create kb-processor \
    --repository-format=docker \
    --location=us-central1 \
    --description="Knowledge Base Processor images"

# Update workflow to use:
# us-central1-docker.pkg.dev/$PROJECT_ID/kb-processor/webapp
```

## Support

For issues with:
- **GCP/GCR**: [GCP Support](https://cloud.google.com/support)
- **GitHub Actions**: [GitHub Actions Documentation](https://docs.github.com/en/actions)
- **This Project**: Open an issue in the repository

## References

- [GCR Documentation](https://cloud.google.com/container-registry/docs)
- [GitHub Actions with GCP](https://github.com/google-github-actions)
- [Docker Build Push Action](https://github.com/docker/build-push-action)
- [Service Account Best Practices](https://cloud.google.com/iam/docs/best-practices-service-accounts)
