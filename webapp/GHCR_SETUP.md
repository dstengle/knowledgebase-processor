# GitHub Container Registry (GHCR) Setup

This guide walks you through setting up GitHub Container Registry (GHCR) publishing for the Knowledge Base Processor webapp via GitHub Actions.

## Prerequisites

- GitHub repository with admin access
- GitHub Actions enabled in your repository

## Overview

GitHub Container Registry (GHCR) is GitHub's native container registry service that integrates seamlessly with GitHub Actions. Unlike GCR, GHCR requires **no external setup** - it works automatically with your GitHub account using the built-in `GITHUB_TOKEN`.

## Automatic Setup

The good news: **GHCR publishing is already configured!** The GitHub Actions workflow in `.github/workflows/publish-webapp-ghcr.yml` will automatically:

1. Build the Docker image on push to `main` or `claude/**` branches
2. Authenticate using the built-in `GITHUB_TOKEN`
3. Push the image to `ghcr.io/owner/repo/kb-processor-webapp`
4. Create multiple tags (latest, SHA, timestamp, branch)

**No secrets to configure!** The `GITHUB_TOKEN` is automatically provided by GitHub Actions.

## Enabling Package Visibility

By default, packages are private. To make your image public:

1. Go to your repository on GitHub
2. Navigate to "Packages" (in the right sidebar)
3. Click on `kb-processor-webapp`
4. Click "Package settings" (bottom of the page)
5. Scroll to "Danger Zone"
6. Click "Change visibility"
7. Select "Public" and confirm

## Authentication Options

### For CI/CD (GitHub Actions)

Already configured! Uses the built-in `GITHUB_TOKEN`:

```yaml
- name: Log in to GitHub Container Registry
  uses: docker/login-action@v3
  with:
    registry: ghcr.io
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}
```

### For Local Development

**Option 1: Personal Access Token (Recommended)**

1. Create a Personal Access Token (classic):
   - Go to Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Click "Generate new token (classic)"
   - Name: `GHCR Access`
   - Select scopes:
     - `read:packages` - Download images
     - `write:packages` - Push images
     - `delete:packages` - Delete images (optional)
   - Click "Generate token"
   - **Copy the token** (you won't see it again!)

2. Authenticate Docker:
   ```bash
   echo "YOUR_TOKEN" | docker login ghcr.io -u YOUR_USERNAME --password-stdin
   ```

**Option 2: GitHub CLI**

```bash
# Install GitHub CLI if not already installed
# https://cli.github.com/

# Login to GitHub
gh auth login

# Configure Docker to use GitHub CLI
gh auth token | docker login ghcr.io -u YOUR_USERNAME --password-stdin
```

**Option 3: Using `.netrc` (Unix/Linux)**

```bash
# Create/edit ~/.netrc
cat >> ~/.netrc << EOF
machine ghcr.io
login YOUR_USERNAME
password YOUR_TOKEN
EOF

chmod 600 ~/.netrc
```

## Image URLs

Your images will be available at:

```
ghcr.io/OWNER/REPO/kb-processor-webapp:TAG
```

For example:
```bash
# Main branch (latest)
ghcr.io/dstengle/knowledgebase-processor/kb-processor-webapp:latest

# Specific commit
ghcr.io/dstengle/knowledgebase-processor/kb-processor-webapp:a1b2c3d

# Specific branch
ghcr.io/dstengle/knowledgebase-processor/kb-processor-webapp:claude-feature-branch
```

## Using the Published Image

### Pull and Run

```bash
# Pull the latest image
docker pull ghcr.io/OWNER/REPO/kb-processor-webapp:latest

# Run the container
docker run -p 8000:8000 ghcr.io/OWNER/REPO/kb-processor-webapp:latest

# Access the webapp
open http://localhost:8000
```

### With Docker Compose

Update `docker-compose.yml`:

```yaml
version: '3.8'

services:
  webapp:
    image: ghcr.io/OWNER/REPO/kb-processor-webapp:latest
    ports:
      - "8000:8000"
    restart: unless-stopped
```

Then run:
```bash
docker-compose up
```

## Managing Packages

### Via GitHub Web UI

1. Go to your repository
2. Click "Packages" in the right sidebar
3. Click on `kb-processor-webapp`
4. View available tags, downloads, and manifest

### List Tags (CLI)

```bash
# Using GitHub CLI
gh api "/users/OWNER/packages/container/kb-processor-webapp%2Fversions" \
  --jq '.[].metadata.container.tags[]'

# Or view in browser
open https://github.com/OWNER/REPO/pkgs/container/kb-processor-webapp
```

### Delete a Tag

```bash
# Via GitHub web UI
1. Go to Package settings
2. Find the tag under "Manage versions"
3. Click the trash icon

# Or via API
gh api -X DELETE \
  "/user/packages/container/kb-processor-webapp%2Fversions/VERSION_ID"
```

## Workflow Triggers

The workflow automatically runs on:

- **Push to main**: Creates `latest` and `stable` tags
- **Push to claude/** branches**: Creates branch-specific tags
- **Pull requests**: Builds but doesn't push (verification only)
- **Manual dispatch**: Allows custom tags via workflow_dispatch

### Trigger Manual Build

```bash
# Via GitHub CLI
gh workflow run publish-webapp-ghcr.yml

# With custom tag
gh workflow run publish-webapp-ghcr.yml -f tag=v1.0.0
```

Or via GitHub UI:
1. Go to "Actions" tab
2. Select "Build and Push Webapp to GHCR"
3. Click "Run workflow"
4. Enter optional custom tag
5. Click "Run workflow"

## Package Permissions

### Organization Repositories

If your repo is in an organization, you may need to:

1. Go to Organization Settings → Packages
2. Enable "Improved container support"
3. Set default permissions for packages
4. Grant repository access to packages

### Repository Access

Control who can push/pull images:

1. Go to Package settings
2. Scroll to "Manage Actions access"
3. Add repositories that can push images
4. Set permissions (read, write, admin)

## Troubleshooting

### Permission Denied When Pushing

**Issue**: `denied: permission_denied: write_package`

**Solution**: Ensure the workflow has `packages: write` permission:

```yaml
permissions:
  contents: read
  packages: write
```

This is already configured in the workflow.

### Cannot Pull Private Image

**Issue**: `unauthorized: authentication required`

**Solutions**:
1. Make the package public (see "Enabling Package Visibility" above)
2. Authenticate with a PAT that has `read:packages` scope
3. Use the GitHub CLI for authentication

### Image Not Found After Push

**Issue**: Image doesn't appear immediately after push.

**Solution**:
- Check the Actions tab for workflow status
- Verify the workflow completed successfully
- Package may take a few seconds to appear in the UI
- Check the package URL directly: `https://github.com/OWNER/REPO/pkgs/container/kb-processor-webapp`

### Rate Limiting

**Issue**: `rate limit exceeded`

**Solution**:
- GHCR has generous rate limits (unlimited for public images when authenticated)
- Ensure you're authenticated even for public images
- Use caching in GitHub Actions (already configured)

### Multi-Architecture Build Fails

**Issue**: ARM64 build fails or times out.

**Solution**:
Remove the platforms line to build for amd64 only:

```yaml
# In .github/workflows/publish-webapp-ghcr.yml
# Change:
platforms: linux/amd64,linux/arm64
# To:
platforms: linux/amd64
```

## Cost and Limits

**GitHub Container Registry Pricing (2024)**:

- **Public images**: Unlimited storage and bandwidth (FREE)
- **Private images**:
  - Free tier: 500MB storage, 1GB bandwidth/month
  - Paid plans: $0.25/GB storage, $0.50/GB bandwidth
- **Actions minutes**: Counted against your GitHub Actions quota

This project (~500MB image):
- **Public**: Completely free
- **Private**: ~$0.13/month for 1 image

[GitHub Packages Pricing](https://docs.github.com/en/billing/managing-billing-for-github-packages/about-billing-for-github-packages)

## Best Practices

### 1. Use Descriptive Tags

```bash
# Good
ghcr.io/owner/repo/kb-processor-webapp:v1.2.3
ghcr.io/owner/repo/kb-processor-webapp:2024-01-15

# Avoid
ghcr.io/owner/repo/kb-processor-webapp:test
ghcr.io/owner/repo/kb-processor-webapp:latest-2
```

### 2. Clean Up Old Images

Regularly delete unused tags to save storage:
- Keep `latest`, `stable`, and recent versions
- Delete old branch-specific builds
- Delete test/debug builds

### 3. Use Image Digests for Production

For reproducible deployments:

```bash
# Instead of:
docker pull ghcr.io/owner/repo/kb-processor-webapp:latest

# Use digest (immutable):
docker pull ghcr.io/owner/repo/kb-processor-webapp@sha256:abc123...
```

### 4. Scan Images for Vulnerabilities

Enable vulnerability scanning:
1. Go to repository Settings → Code security and analysis
2. Enable "Dependency graph"
3. Enable "Dependabot alerts"
4. Review security advisories regularly

### 5. Use `.dockerignore`

Already configured! Reduces build context and image size:
- Excludes `.git`, `__pycache__`, `*.pyc`
- Includes only necessary files

## Comparison: GHCR vs GCR

| Feature | GHCR | GCR |
|---------|------|-----|
| Setup | None (automatic) | Service account + secrets |
| Authentication | GITHUB_TOKEN | GCP service account key |
| Cost (public) | Free | ~$0.13/month |
| Integration | Native GitHub | External GCP project |
| Rate Limits | Generous | Based on GCP quota |
| Multi-arch | Yes | Yes |
| Vulnerability Scanning | Yes | Yes |
| Best For | GitHub-first workflows | Multi-cloud, GKE |

## Advanced: Using Multiple Registries

You can push to both GHCR and other registries:

```yaml
# In workflow file
- name: Login to GHCR
  uses: docker/login-action@v3
  with:
    registry: ghcr.io
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}

- name: Login to Docker Hub
  uses: docker/login-action@v3
  with:
    username: ${{ secrets.DOCKER_USERNAME }}
    password: ${{ secrets.DOCKER_TOKEN }}

- name: Build and push
  uses: docker/build-push-action@v5
  with:
    tags: |
      ghcr.io/${{ github.repository }}/kb-processor-webapp:latest
      dockerhub/username/kb-processor-webapp:latest
```

## Support and Resources

- [GitHub Container Registry Docs](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [GitHub Actions Docker Docs](https://docs.github.com/en/actions/publishing-packages/publishing-docker-images)
- [Docker Build Push Action](https://github.com/docker/build-push-action)
- [Package Issues](https://github.com/orgs/community/discussions/categories/packages)

## Quick Reference

```bash
# Login to GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Pull image
docker pull ghcr.io/OWNER/REPO/kb-processor-webapp:latest

# Run container
docker run -p 8000:8000 ghcr.io/OWNER/REPO/kb-processor-webapp:latest

# View packages
open https://github.com/OWNER/REPO/pkgs/container/kb-processor-webapp

# Trigger workflow
gh workflow run publish-webapp-ghcr.yml

# List tags
gh api "/users/OWNER/packages/container/kb-processor-webapp%2Fversions" --jq '.[].metadata.container.tags[]'
```

## Summary

GitHub Container Registry provides the simplest way to publish Docker images for GitHub-hosted projects:

✅ **No setup required** - works automatically with `GITHUB_TOKEN`
✅ **Free for public images** - unlimited storage and bandwidth
✅ **Native integration** - seamless with GitHub Actions
✅ **Multi-architecture** - amd64 and arm64 support
✅ **Secure** - built-in security scanning and access controls

Just push to your repository and let GitHub Actions handle the rest!
