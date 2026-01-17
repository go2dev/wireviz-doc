# CI/CD Integration Guide

This guide covers integrating WireViz Doc into your development workflow, including pre-commit hooks, GitHub Actions, GitLab CI, and general CI/CD best practices.

## Table of Contents

- [Overview](#overview)
- [Pre-commit Hooks](#pre-commit-hooks)
- [GitHub Actions](#github-actions)
- [GitLab CI](#gitlab-ci)
- [Docker Integration](#docker-integration)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## Overview

WireViz Doc is designed for deterministic, CI-friendly builds:

- **Deterministic output:** Same input always produces same output
- **No network dependencies:** CI mode forbids web scraping
- **Clear exit codes:** 0 (success), 1 (error), 2 (warning)
- **Fast validation:** Lint without full build
- **Glob support:** Process multiple files in one command

### CI/CD Workflow

Typical CI/CD integration:

1. **Lint** - Validate YAML schema and references
2. **Image check** - Verify all images present (no scraping)
3. **Build** - Generate documentation artifacts
4. **Upload** - Store or deploy generated files
5. **Gate** - Block merge if validation fails

---

## Pre-commit Hooks

Pre-commit hooks validate harness files before commit, catching errors early.

### Using pre-commit Framework

**Install pre-commit:**

```bash
pip install pre-commit
```

**Create `.pre-commit-config.yaml`:**

```yaml
repos:
  - repo: local
    hooks:
      - id: wireviz-doc-lint
        name: Lint WireViz Doc files
        entry: wvdoc lint
        language: system
        files: '\.harness\.yml$'
        args: ['--strict']

      - id: wireviz-doc-images
        name: Check WireViz Doc images
        entry: wvdoc images
        language: system
        files: '\.harness\.yml$'
        args: ['--ci']

      - id: wireviz-doc-build
        name: Build WireViz Doc
        entry: wvdoc build
        language: system
        files: '\.harness\.yml$'
        pass_filenames: true
```

**Install hooks:**

```bash
pre-commit install
```

**Run manually:**

```bash
pre-commit run --all-files
```

### Manual Git Hook

**Create `.git/hooks/pre-commit`:**

```bash
#!/bin/bash
set -e

echo "Running WireViz Doc pre-commit checks..."

# Get staged .harness.yml files
FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.harness\.yml$' || true)

if [ -z "$FILES" ]; then
    echo "No harness files changed, skipping checks"
    exit 0
fi

echo "Changed files:"
echo "$FILES"

# Lint each file
echo ""
echo "1. Linting harness files..."
for file in $FILES; do
    echo "  Linting $file..."
    wvdoc lint "$file" --strict || {
        echo "❌ Lint failed for $file"
        exit 1
    }
done
echo "✓ All files passed lint"

# Check images
echo ""
echo "2. Checking images..."
for file in $FILES; do
    echo "  Checking images for $file..."
    wvdoc images "$file" --ci || {
        echo "❌ Image check failed for $file"
        echo "Run 'wvdoc images $file --scrape' to download missing images"
        exit 1
    }
done
echo "✓ All images present"

# Build documentation
echo ""
echo "3. Building documentation..."
wvdoc build $FILES --quiet || {
    echo "❌ Build failed"
    exit 1
}
echo "✓ Build successful"

# Optional: Stage generated files
# git add build/

echo ""
echo "✅ All pre-commit checks passed"
```

**Make executable:**

```bash
chmod +x .git/hooks/pre-commit
```

### Selective Checking

Only run checks when harness files are modified:

```bash
#!/bin/bash

FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.harness\.yml$')

if [ -z "$FILES" ]; then
    exit 0  # No harness files changed
fi

# Run checks only on changed files
wvdoc lint $FILES --strict
wvdoc images $FILES --ci
wvdoc build $FILES
```

---

## GitHub Actions

### Basic Workflow

**`.github/workflows/wireviz-doc.yml`:**

```yaml
name: WireViz Doc

on:
  push:
    branches: [main, develop]
    paths:
      - 'harnesses/**/*.harness.yml'
      - 'images/**'
  pull_request:
    branches: [main, develop]
    paths:
      - 'harnesses/**/*.harness.yml'
      - 'images/**'

jobs:
  validate-and-build:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Graphviz
        run: sudo apt-get update && sudo apt-get install -y graphviz

      - name: Install WireViz Doc
        run: pip install wireviz-doc

      - name: Lint harness files
        run: wvdoc lint harnesses/**/*.harness.yml --strict

      - name: Check images
        run: wvdoc images harnesses/**/*.harness.yml --ci

      - name: Build documentation
        run: wvdoc build harnesses/**/*.harness.yml --output-dir build

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: wiring-documentation
          path: build/
          retention-days: 30
```

### Advanced Workflow

**With caching, matrix builds, and deployment:**

```yaml
name: WireViz Doc Advanced

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  validate:
    name: Validate Harness Files
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Cache pip packages
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-

      - name: Install dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y graphviz
          pip install wireviz-doc

      - name: Lint all harnesses
        run: wvdoc lint "harnesses/**/*.harness.yml" --strict

  build:
    name: Build Documentation
    needs: validate
    runs-on: ubuntu-latest
    strategy:
      matrix:
        format: [svg, pdf]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y graphviz
          pip install wireviz-doc

      - name: Check images
        run: wvdoc images "harnesses/**/*.harness.yml" --ci

      - name: Build ${{ matrix.format }}
        run: wvdoc build "harnesses/**/*.harness.yml" --format ${{ matrix.format }} --output-dir build

      - name: Upload ${{ matrix.format }} artifacts
        uses: actions/upload-artifact@v4
        with:
          name: documentation-${{ matrix.format }}
          path: build/

  deploy:
    name: Deploy to Pages
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    permissions:
      pages: write
      id-token: write

    steps:
      - name: Download SVG artifacts
        uses: actions/download-artifact@v4
        with:
          name: documentation-svg
          path: docs/

      - name: Generate index
        run: |
          cat > docs/index.html << 'EOF'
          <!DOCTYPE html>
          <html>
          <head>
              <title>Wiring Documentation</title>
          </head>
          <body>
              <h1>Wiring Harness Documentation</h1>
              <ul>
          EOF

          find docs -name "diagram.svg" | while read file; do
              harness=$(dirname "$file" | xargs basename)
              echo "<li><a href='$file'>$harness</a></li>" >> docs/index.html
          done

          echo "</ul></body></html>" >> docs/index.html

      - name: Upload to Pages
        uses: actions/upload-pages-artifact@v3
        with:
          path: docs/

      - name: Deploy to GitHub Pages
        uses: actions/deploy-pages@v4
```

### PR Comment Workflow

**Post build results as PR comment:**

```yaml
name: PR Documentation Check

on:
  pull_request:
    paths:
      - 'harnesses/**/*.harness.yml'

jobs:
  check:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          sudo apt-get update && sudo apt-get install -y graphviz
          pip install wireviz-doc

      - name: Lint and capture output
        id: lint
        run: |
          wvdoc lint "harnesses/**/*.harness.yml" --strict > lint-output.txt 2>&1 || true
          echo "output<<EOF" >> $GITHUB_OUTPUT
          cat lint-output.txt >> $GITHUB_OUTPUT
          echo "EOF" >> $GITHUB_OUTPUT

      - name: Comment on PR
        uses: actions/github-script@v7
        with:
          script: |
            const output = `${{ steps.lint.outputs.output }}`;
            const comment = `
            ## WireViz Doc Validation

            \`\`\`
            ${output}
            \`\`\`
            `;

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: comment
            });
```

---

## GitLab CI

**`.gitlab-ci.yml`:**

```yaml
image: python:3.11

stages:
  - validate
  - build
  - deploy

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  paths:
    - .cache/pip

before_script:
  - apt-get update && apt-get install -y graphviz
  - pip install wireviz-doc

lint:
  stage: validate
  script:
    - wvdoc lint harnesses/**/*.harness.yml --strict
  rules:
    - changes:
        - harnesses/**/*.harness.yml

check-images:
  stage: validate
  script:
    - wvdoc images harnesses/**/*.harness.yml --ci
  rules:
    - changes:
        - harnesses/**/*.harness.yml
        - images/**

build:
  stage: build
  script:
    - wvdoc build harnesses/**/*.harness.yml --output-dir build
  artifacts:
    paths:
      - build/
    expire_in: 30 days
  rules:
    - changes:
        - harnesses/**/*.harness.yml

pages:
  stage: deploy
  dependencies:
    - build
  script:
    - mkdir public
    - cp -r build/* public/
    - echo '<html><body><h1>Wiring Documentation</h1></body></html>' > public/index.html
  artifacts:
    paths:
      - public
  only:
    - main
```

---

## Docker Integration

### Dockerfile

**`Dockerfile`:**

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        graphviz \
        fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Install WireViz Doc
RUN pip install --no-cache-dir wireviz-doc

# Set working directory
WORKDIR /workspace

# Default command
CMD ["wvdoc", "--help"]
```

**Build and use:**

```bash
# Build image
docker build -t wireviz-doc .

# Run lint
docker run --rm -v $(pwd):/workspace wireviz-doc \
    wvdoc lint harnesses/my-harness.yml --strict

# Run build
docker run --rm -v $(pwd):/workspace wireviz-doc \
    wvdoc build harnesses/**/*.harness.yml
```

### Docker Compose

**`docker-compose.yml`:**

```yaml
version: '3.8'

services:
  wireviz-doc:
    image: wireviz-doc:latest
    build: .
    volumes:
      - .:/workspace
    working_dir: /workspace
    command: wvdoc build "harnesses/**/*.harness.yml"
```

**Usage:**

```bash
# Build documentation
docker-compose run wireviz-doc

# Lint files
docker-compose run wireviz-doc wvdoc lint harnesses/my-harness.yml
```

---

## Best Practices

### 1. Commit Generated Files

**Recommended approach:**

Commit both source YAML and generated documentation:

```
.gitignore:
# Don't ignore build directory
# !build/

harnesses/
  my-harness.harness.yml
build/
  HAR-0001/
    diagram.svg
    diagram.pdf
    bom.tsv
    wiring_table.tsv
```

**Benefits:**
- Version control of outputs
- Easy diff review in PRs
- No build required to view documentation
- Historical archive of all versions

**Drawbacks:**
- Larger repository size
- Potential merge conflicts

### 2. Don't Commit Generated Files

**Alternative approach:**

Only commit source YAML, generate on demand:

```
.gitignore:
build/

harnesses/
  my-harness.harness.yml
```

**Benefits:**
- Smaller repository
- No merge conflicts on generated files
- Cleaner git history

**Drawbacks:**
- Requires build to view docs
- CI must always succeed
- Need separate documentation hosting

### 3. Image Management

**Best practice:**

Commit images to repository:

```
images/
  Molex_43045-0412.png
  Belden_9536.jpg
harnesses/
  my-harness.harness.yml
```

**CI configuration:**

```yaml
- name: Check images (fail if missing)
  run: wvdoc images harnesses/**/*.harness.yml --ci
```

**Workflow:**

1. Developer: `wvdoc images harness.yml --scrape`
2. Developer: `git add images/`
3. Developer: `git commit -m "Add part images"`
4. CI: Validates images present (no scraping)

### 4. Branch Protection

**Recommended GitHub branch protection rules:**

- Require status check: "WireViz Doc / validate"
- Require status check: "WireViz Doc / build"
- Require PR reviews before merging
- Require branches to be up to date before merging

### 5. Caching

**Cache dependencies and images:**

```yaml
# GitHub Actions
- uses: actions/cache@v4
  with:
    path: |
      ~/.cache/pip
      ./images
    key: ${{ runner.os }}-wireviz-${{ hashFiles('**/requirements.txt', 'harnesses/**/*.harness.yml') }}
```

**GitLab CI:**

```yaml
cache:
  key: ${CI_COMMIT_REF_SLUG}
  paths:
    - .cache/pip
    - images/
```

### 6. Parallel Builds

**Process multiple harnesses in parallel:**

```yaml
# GitHub Actions
jobs:
  build:
    strategy:
      matrix:
        harness:
          - harnesses/power-harness.yml
          - harnesses/can-harness.yml
          - harnesses/sensor-harness.yml

    steps:
      - run: wvdoc build ${{ matrix.harness }}
```

### 7. Notifications

**Slack notification on failure:**

```yaml
# GitHub Actions
- name: Notify on failure
  if: failure()
  uses: slackapi/slack-github-action@v1
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK }}
    payload: |
      {
        "text": "WireViz Doc build failed on ${{ github.ref }}"
      }
```

---

## Troubleshooting

### CI Build Fails Locally Passing

**Check:**
1. Graphviz version differences
2. Python version differences
3. Font availability (affects SVG rendering)
4. File paths (case sensitivity on Linux)

**Solution:**

```bash
# Match CI environment
docker run --rm -v $(pwd):/workspace python:3.11-slim bash -c "
    apt-get update && apt-get install -y graphviz
    pip install wireviz-doc
    cd /workspace
    wvdoc build harnesses/**/*.harness.yml
"
```

### Image Check Fails in CI

**Error:** "Image not found: images/Molex_43045-0412.png"

**Solution:**

```bash
# Download images locally
wvdoc images harnesses/**/*.harness.yml --scrape

# Commit images
git add images/
git commit -m "Add missing part images"
git push
```

### Slow CI Builds

**Optimize:**

1. **Cache pip packages:**
   ```yaml
   - uses: actions/cache@v4
     with:
       path: ~/.cache/pip
       key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
   ```

2. **Only run on changed files:**
   ```yaml
   on:
     push:
       paths:
         - 'harnesses/**/*.harness.yml'
   ```

3. **Parallel jobs:**
   ```yaml
   strategy:
     matrix:
       harness: [...]
   ```

### Memory Issues

**Large harnesses with many images:**

```yaml
# Increase memory limit
jobs:
  build:
    runs-on: ubuntu-latest-8-cores  # Larger runner
```

**Or build separately:**

```bash
# Build one at a time
for file in harnesses/*.harness.yml; do
    wvdoc build "$file"
done
```

---

## Example: Complete CI/CD Setup

**Directory structure:**

```
project/
├── .github/
│   └── workflows/
│       └── wireviz-doc.yml
├── .pre-commit-config.yaml
├── harnesses/
│   ├── power-harness.harness.yml
│   └── can-harness.harness.yml
├── images/
│   └── Molex_43045-0412.png
├── build/  (committed or ignored)
└── README.md
```

**Workflow:**

1. Developer edits `harnesses/power-harness.harness.yml`
2. Pre-commit hook validates before commit
3. Developer pushes to feature branch
4. GitHub Actions runs validation
5. PR opened, Actions runs on PR
6. Code review + Actions must pass
7. Merge to main
8. Actions builds and deploys to GitHub Pages

**Configuration:**

```yaml
# .github/workflows/wireviz-doc.yml
name: WireViz Doc

on: [push, pull_request]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      - run: sudo apt-get install -y graphviz
      - run: pip install wireviz-doc
      - run: wvdoc lint "harnesses/**/*.harness.yml" --strict
      - run: wvdoc images "harnesses/**/*.harness.yml" --ci
      - run: wvdoc build "harnesses/**/*.harness.yml"
      - uses: actions/upload-artifact@v4
        with:
          name: documentation
          path: build/
```

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: wireviz-doc
        name: WireViz Doc
        entry: bash -c 'wvdoc lint "$@" --strict && wvdoc images "$@" --ci'
        language: system
        files: '\.harness\.yml$'
```

This setup ensures:
- Local validation before commit
- CI validation on every push
- Build artifacts for review
- Automatic deployment on merge

---

## See Also

- [CLI Reference](cli.md) - Complete command-line documentation
- [Schema Reference](schema.md) - YAML schema details
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitLab CI Documentation](https://docs.gitlab.com/ee/ci/)
- [pre-commit Documentation](https://pre-commit.com/)
