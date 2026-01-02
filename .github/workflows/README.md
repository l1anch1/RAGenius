# GitHub Actions CI/CD Workflows

This directory contains automated workflows for the RAGenius project.

## Workflows

### 1. CI (`ci.yml`)
**Trigger**: Push to `main`/`develop` branches, Pull Requests

**Jobs**:
- **Backend Tests**: Python syntax check, linting (flake8), formatting (black), import checks
- **Frontend Tests**: ESLint, build verification
- **Docker Build**: Multi-stage build verification for both backend and frontend
- **Security Scan**: Trivy vulnerability scanning
- **Code Quality**: SonarCloud analysis (optional)

**Matrix Strategy**:
- Python: 3.9, 3.10, 3.11
- Node.js: 18.x, 20.x

### 2. Docker Publish (`docker-publish.yml`)
**Trigger**: Version tags (`v*.*.*`), Releases, Manual dispatch

**Features**:
- Multi-architecture builds (amd64, arm64)
- Publishes to GitHub Container Registry (ghcr.io)
- Semantic versioning tags
- Build cache optimization

**Images**:
- `ghcr.io/<username>/ragenius-backend`
- `ghcr.io/<username>/ragenius-frontend`

### 3. CodeQL Security Analysis (`codeql.yml`)
**Trigger**: Push, Pull Requests, Weekly schedule

**Languages**: Python, JavaScript

**Queries**: Security-extended + Quality checks

### 4. Dependency Review (`dependency-review.yml`)
**Trigger**: Pull Requests

**Features**:
- Reviews dependency changes
- Flags vulnerabilities (moderate severity or higher)
- Comments PR summary

## Configuration Files

### Dependabot (`dependabot.yml`)
Auto-updates dependencies weekly:
- Python (pip)
- JavaScript (npm)
- Docker
- GitHub Actions

### SonarCloud (`sonar-project.properties`)
Code quality and security analysis configuration.

**Setup Required**:
1. Connect repository to [SonarCloud](https://sonarcloud.io/)
2. Add `SONAR_TOKEN` to repository secrets

## Setup Instructions

### Required Secrets
Add these to your GitHub repository settings (Settings → Secrets → Actions):

1. **For Docker Publishing**:
   - `GITHUB_TOKEN` (automatically provided by GitHub)

2. **For SonarCloud** (optional):
   - `SONAR_TOKEN`: Get from sonarcloud.io

3. **For Production Deployment** (optional):
   - Add your deployment credentials as needed

### First-time Setup

1. **Update `sonar-project.properties`**:
   ```properties
   sonar.organization=your-github-username
   sonar.projectKey=your-github-username_ragenius
   ```

2. **Enable GitHub Actions**:
   - Go to repository Settings → Actions → General
   - Allow all actions and reusable workflows

3. **Configure GitHub Container Registry**:
   - Actions have write permissions by default
   - Images will be published to `ghcr.io/<username>/ragenius-*`

4. **Test Workflows**:
   ```bash
   git add .github/
   git commit -m "ci: add GitHub Actions workflows"
   git push origin main
   ```

## Workflow Badges

Add to your README.md:

```markdown
[![CI](https://github.com/USERNAME/REPO/actions/workflows/ci.yml/badge.svg)](https://github.com/USERNAME/REPO/actions/workflows/ci.yml)
[![Docker Publish](https://github.com/USERNAME/REPO/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/USERNAME/REPO/actions/workflows/docker-publish.yml)
[![CodeQL](https://github.com/USERNAME/REPO/actions/workflows/codeql.yml/badge.svg)](https://github.com/USERNAME/REPO/actions/workflows/codeql.yml)
```

## Local Testing

Test workflows locally using [act](https://github.com/nektos/act):

```bash
# Install act
brew install act  # macOS
# or
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Run CI workflow
act -j backend-test

# Run all workflows
act push
```

## Troubleshooting

### Docker Build Fails
- Check Dockerfile syntax
- Ensure `.dockerignore` excludes unnecessary files
- Verify build context paths

### Import Errors in Python Tests
- Ensure `requirements.txt` is complete
- Check Python version compatibility
- Verify module paths

### Frontend Build Issues
- Clear npm cache: `npm cache clean --force`
- Check Node.js version compatibility
- Verify all dependencies in `package.json`

## Contributing

When adding new workflows:
1. Test locally first with `act`
2. Use appropriate triggers
3. Add comprehensive error handling
4. Update this README
5. Consider resource usage and build times

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Build Push Action](https://github.com/docker/build-push-action)
- [SonarCloud](https://sonarcloud.io/)
- [Dependabot](https://docs.github.com/en/code-security/dependabot)

