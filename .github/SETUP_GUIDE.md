# GitHub Actions Setup Guide

This guide will help you configure GitHub Actions CI/CD for your RAGenius fork.

## Quick Start (5 minutes)

### 1. Enable GitHub Actions

1. Go to your repository on GitHub
2. Click **Settings** → **Actions** → **General**
3. Under "Actions permissions", select **Allow all actions and reusable workflows**
4. Click **Save**

### 2. Configure GitHub Container Registry (GHCR)

GitHub Actions can automatically publish Docker images to GHCR:

1. Go to **Settings** → **Actions** → **General**
2. Scroll to "Workflow permissions"
3. Select **Read and write permissions**
4. Check **Allow GitHub Actions to create and approve pull requests**
5. Click **Save**

**That's it!** Your CI/CD is now configured. Push to `main` or create a PR to trigger workflows.

## Optional Configurations

### SonarCloud (Code Quality Analysis)

1. Go to [SonarCloud](https://sonarcloud.io/)
2. Sign in with GitHub
3. Click **+** → **Analyze new project**
4. Select your repository
5. Copy the **SONAR_TOKEN**
6. In GitHub: **Settings** → **Secrets and variables** → **Actions** → **New repository secret**
   - Name: `SONAR_TOKEN`
   - Value: [paste token]
7. Update `sonar-project.properties`:
   ```properties
   sonar.organization=your-github-username
   sonar.projectKey=your-github-username_ragenius
   ```

### Docker Hub (Alternative to GHCR)

If you prefer Docker Hub over GitHub Container Registry:

1. Get your Docker Hub credentials
2. Add secrets in GitHub:
   - `DOCKERHUB_USERNAME`: Your Docker Hub username
   - `DOCKERHUB_TOKEN`: Your Docker Hub access token
3. Modify `.github/workflows/docker-publish.yml`:
   ```yaml
   env:
     REGISTRY: docker.io
     IMAGE_NAME_BACKEND: your-username/ragenius-backend
     IMAGE_NAME_FRONTEND: your-username/ragenius-frontend
   ```

## Workflow Overview

### Automatic Triggers

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| **CI** | Push to main/develop, PRs | Test, lint, build |
| **Docker Publish** | Tags (`v*.*.*`), Releases | Publish images |
| **CodeQL** | Push, PRs, Weekly | Security analysis |
| **Dependency Review** | PRs | Check dependency vulnerabilities |

### Manual Triggers

You can manually trigger workflows:

1. Go to **Actions** tab
2. Select a workflow
3. Click **Run workflow**
4. Choose branch and click **Run workflow**

## Testing Your Setup

### 1. Test CI Workflow

```bash
# Make a small change
echo "# Test" >> README.md
git add README.md
git commit -m "test: trigger CI workflow"
git push origin main
```

Go to **Actions** tab to see the workflow running.

### 2. Test Docker Publishing

```bash
# Create a version tag
git tag v1.0.0
git push origin v1.0.0
```

This will build and push Docker images to GHCR.

### 3. View Published Images

1. Go to your GitHub profile
2. Click **Packages**
3. You should see `ragenius-backend` and `ragenius-frontend`

## Using Published Docker Images

Once published, anyone can use your images:

```bash
# Pull from GHCR
docker pull ghcr.io/your-username/ragenius-backend:latest
docker pull ghcr.io/your-username/ragenius-frontend:latest

# Or use in docker-compose.yml
services:
  backend:
    image: ghcr.io/your-username/ragenius-backend:v1.0.0
  frontend:
    image: ghcr.io/your-username/ragenius-frontend:v1.0.0
```

## Troubleshooting

### CI Fails on First Run

**Problem**: Import errors or missing dependencies

**Solution**: This is normal for first run. The workflow will:
1. Install dependencies
2. Run syntax checks (these should pass)
3. Some import checks may fail without environment setup

### Docker Build Fails

**Problem**: Context or permission errors

**Solution**:
1. Check `.dockerignore` files are present
2. Verify Dockerfile paths are correct
3. Ensure workflow permissions are set to "Read and write"

### CodeQL Timeout

**Problem**: Analysis takes too long

**Solution**: CodeQL may timeout on large repos. You can:
1. Disable CodeQL temporarily
2. Adjust timeout in workflow file
3. Use manual triggers instead of automatic

### Dependabot PRs Not Created

**Problem**: No dependency update PRs

**Solution**:
1. Wait up to 24 hours after setup
2. Check **Insights** → **Dependency graph** → **Dependabot**
3. Verify `dependabot.yml` syntax

## Customization

### Change CI Python Versions

Edit `.github/workflows/ci.yml`:

```yaml
strategy:
  matrix:
    python-version: ['3.9', '3.10', '3.11', '3.12']  # Add 3.12
```

### Add Slack Notifications

Add to any workflow job:

```yaml
- name: Slack Notification
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    text: 'CI Failed!'
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### Skip CI for Docs Changes

Add to workflow:

```yaml
on:
  push:
    branches: [ main ]
    paths-ignore:
      - '**.md'
      - 'docs/**'
```

## Best Practices

1. **Always test locally first**:
   ```bash
   # Run linters
   black --check backend/
   flake8 backend/
   cd frontend && npm run lint
   
   # Test builds
   docker-compose build
   ```

2. **Use feature branches**:
   ```bash
   git checkout -b feature/my-feature
   # Make changes
   git push origin feature/my-feature
   # Create PR (triggers CI)
   ```

3. **Tag releases properly**:
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```

4. **Monitor Actions usage**:
   - GitHub provides 2,000 free minutes/month
   - Check usage: **Settings** → **Billing** → **Actions**

## Status Badges

Add to your README.md:

```markdown
[![CI](https://github.com/USERNAME/REPO/actions/workflows/ci.yml/badge.svg)](https://github.com/USERNAME/REPO/actions/workflows/ci.yml)
[![Docker Publish](https://github.com/USERNAME/REPO/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/USERNAME/REPO/actions/workflows/docker-publish.yml)
[![CodeQL](https://github.com/USERNAME/REPO/actions/workflows/codeql.yml/badge.svg)](https://github.com/USERNAME/REPO/actions/workflows/codeql.yml)
```

Replace `USERNAME` and `REPO` with your values.

## Need Help?

- 📖 [GitHub Actions Documentation](https://docs.github.com/en/actions)
- 💬 [GitHub Community Forum](https://github.community/)
- 🐛 [Open an Issue](https://github.com/l1anch1/DeepSeek-RAG/issues)

---

**Next Steps**: Read [CONTRIBUTING.md](../CONTRIBUTING.md) to learn about the development workflow.

