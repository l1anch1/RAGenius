#!/bin/bash

# GitHub Actions CI/CD Setup - Commit Script
# This script commits all CI/CD related files

set -e  # Exit on error

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║   Committing GitHub Actions CI/CD Configuration              ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Error: Not a git repository"
    exit 1
fi

echo "📝 Files to be committed:"
echo "─────────────────────────────────────────────────────────────────"

# Add all CI/CD related files
git add .github/
git add CONTRIBUTING.md
git add CI_CD_SETUP_SUMMARY.md
git add pyproject.toml
git add sonar-project.properties
git add .flake8
git add .dockerignore
git add backend/.dockerignore
git add frontend/.dockerignore
git add README.md

# Show what will be committed
git status --short

echo ""
echo "─────────────────────────────────────────────────────────────────"
echo ""
echo "📊 Summary:"
git diff --cached --stat

echo ""
echo "─────────────────────────────────────────────────────────────────"
echo ""
read -p "🤔 Proceed with commit? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "✅ Committing changes..."
    git commit -m "ci: add GitHub Actions workflows and CI/CD configuration

- Add CI pipeline for automated testing (Python, Node.js, Docker)
- Add Docker publishing workflow for multi-arch images
- Add security scanning (CodeQL, Trivy, dependency review)
- Add Dependabot for automated dependency updates
- Add PR and issue templates
- Add contribution guidelines and setup documentation
- Configure code quality tools (Black, Flake8, ESLint)
- Add status badges to README
- Add comprehensive CI/CD documentation"

    echo ""
    echo "✅ Commit successful!"
    echo ""
    echo "🚀 Next steps:"
    echo "   1. Push to GitHub:  git push origin main"
    echo "   2. Enable Actions:  Settings → Actions → General"
    echo "   3. Watch it run:    Actions tab"
    echo ""
    echo "📚 Documentation:"
    echo "   - Quick Start:  .github/workflows/QUICKSTART.md"
    echo "   - Full Guide:   .github/SETUP_GUIDE.md"
    echo "   - Summary:      CI_CD_SETUP_SUMMARY.md"
    echo ""
else
    echo ""
    echo "❌ Commit cancelled"
    echo "   Changes are staged. You can commit manually with:"
    echo "   git commit -m 'ci: add GitHub Actions workflows'"
    echo ""
fi

