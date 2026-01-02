# CI/CD Quick Start

## ✅ What's Already Configured

Your repository now has:

- ✅ **CI Pipeline** - Automated testing and linting
- ✅ **Docker Publishing** - Multi-arch image builds
- ✅ **Security Scanning** - CodeQL and Trivy
- ✅ **Dependency Updates** - Dependabot automation
- ✅ **Code Quality** - Linting and formatting checks

## 🚀 3-Step Setup

### Step 1: Enable Actions (30 seconds)

1. Go to your GitHub repo → **Settings** → **Actions** → **General**
2. Select "Allow all actions and reusable workflows"
3. Under "Workflow permissions", select "Read and write permissions"
4. Save

### Step 2: Test It (1 minute)

```bash
# Trigger CI
git add .github/
git commit -m "ci: add GitHub Actions workflows"
git push origin main
```

Go to **Actions** tab to watch it run!

### Step 3: Publish Docker Images (Optional)

```bash
# Create a release tag
git tag v1.0.0
git push origin v1.0.0
```

Images will be published to `ghcr.io/YOUR_USERNAME/ragenius-*`

## 📊 Add Status Badges

Copy to your README.md:

```markdown
[![CI](https://github.com/l1anch1/DeepSeek-RAG/actions/workflows/ci.yml/badge.svg)](https://github.com/l1anch1/DeepSeek-RAG/actions/workflows/ci.yml)
[![Docker](https://github.com/l1anch1/DeepSeek-RAG/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/l1anch1/DeepSeek-RAG/actions/workflows/docker-publish.yml)
```

## 🎯 What Happens Now?

| Event | Workflow Triggered | What It Does |
|-------|-------------------|--------------|
| Push to `main` | CI | Tests, lints, builds |
| Create PR | CI + Dependency Review | Validates changes |
| Push tag `v*.*.*` | Docker Publish | Builds & publishes images |
| Weekly | CodeQL | Security scan |

## 📚 Learn More

- [Detailed Setup Guide](./SETUP_GUIDE.md)
- [Workflow Documentation](./README.md)
- [Contributing Guidelines](../../CONTRIBUTING.md)

## 🐛 Issues?

Check the [Troubleshooting section](./SETUP_GUIDE.md#troubleshooting) in the setup guide.

---

**That's it!** Your CI/CD is ready. Every push will now be automatically tested. 🎉

