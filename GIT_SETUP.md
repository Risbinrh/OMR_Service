# Git Setup & Repository Push Guide

## Initial Setup

### 1. Initialize Git Repository

```bash
cd omr-microservice
git init
```

### 2. Configure Git (if not done globally)

```bash
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

### 3. Create GitHub Repository

1. Go to https://github.com
2. Click "New repository"
3. Name it: `omr-microservice` or `omr-detection-api`
4. Description: "OMR Detection & Autograding Microservice - REST API for processing mobile photos of OMR answer sheets"
5. Choose Public or Private
6. **DO NOT** initialize with README (we have one)
7. Click "Create repository"

### 4. Add Remote and Push

```bash
# Add remote (replace with your URL)
git remote add origin https://github.com/YOUR_USERNAME/omr-microservice.git

# Check gitignore is in place
cat .gitignore

# Add all files
git add .

# Initial commit
git commit -m "Initial commit: OMR Detection & Autograding Microservice

- FastAPI REST API with all endpoints
- OMR processing pipeline (99.5% accuracy)
- Autograding engine with flexible scoring
- Answer key management system
- Batch processing support
- Docker deployment ready
- Comprehensive documentation"

# Push to GitHub
git push -u origin main

# Or if default branch is 'master'
git push -u origin master
```

---

## Important: Model File Handling

The YOLO model file (`models/epoch20.pt`) is **67MB** and may be too large for GitHub's file size limit (100MB).

### Option 1: Use Git LFS (Large File Storage)

```bash
# Install Git LFS
git lfs install

# Track the model file
git lfs track "models/*.pt"

# Add .gitattributes
git add .gitattributes

# Now add and commit the model
git add models/epoch20.pt
git commit -m "Add YOLO model with Git LFS"
git push
```

### Option 2: Exclude Model (Recommended if >100MB)

Update `.gitignore`:
```bash
# Models - download separately
models/epoch20.pt
```

Add download instructions to README:
```markdown
## Model Setup

Download the YOLO model:
- File: epoch20.pt
- Size: 67MB
- Place in: `models/epoch20.pt`
- Download link: [Your cloud storage link]
```

Host model on:
- Google Drive
- Dropbox
- AWS S3
- GitHub Releases (if <2GB)

---

## Branch Strategy

### Main Branch
```bash
# Ensure you're on main
git checkout -b main

# Set as default
git branch -M main
```

### Development Branch
```bash
# Create dev branch
git checkout -b development

# Make changes, then
git add .
git commit -m "Your commit message"
git push origin development
```

### Feature Branches
```bash
# Create feature branch
git checkout -b feature/answer-key-api

# Work on feature...
git add .
git commit -m "Add answer key API endpoints"
git push origin feature/answer-key-api

# Create Pull Request on GitHub
# Merge to main after review
```

---

## .gitignore Verification

Before pushing, verify these are ignored:

```bash
# Check what will be committed
git status

# Should NOT see:
# - venv/
# - __pycache__/
# - .env
# - uploads/ (except .gitkeep)
# - results/ (except .gitkeep)
# - answer_keys/ (except .gitkeep)
# - *.log files
```

---

## Commit Message Convention

Use conventional commits:

```bash
# Features
git commit -m "feat: add batch processing endpoint"

# Bug fixes
git commit -m "fix: resolve corner detection issue"

# Documentation
git commit -m "docs: update deployment guide"

# Refactoring
git commit -m "refactor: optimize grading engine"

# Tests
git commit -m "test: add API endpoint tests"

# CI/CD
git commit -m "ci: add GitHub Actions workflow"
```

---

## GitHub Repository Setup

### 1. Add Topics/Tags

In your GitHub repo settings, add topics:
- `omr`
- `optical-mark-recognition`
- `fastapi`
- `yolov8`
- `computer-vision`
- `autograding`
- `education`
- `machine-learning`
- `rest-api`
- `docker`

### 2. Create Description

```
🎯 OMR Detection & Autograding Microservice - REST API for processing mobile photos of OMR answer sheets with automatic grading. Built with FastAPI, YOLOv8, and Docker.
```

### 3. Add README Badges

Add to top of README.md:

```markdown
# OMR Detection & Autograding Microservice

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Status](https://img.shields.io/badge/status-production%20ready-success.svg)
```

### 4. Create GitHub Issues Templates

Create `.github/ISSUE_TEMPLATE/bug_report.md`:
```markdown
---
name: Bug report
about: Create a report to help improve the service
---

**Describe the bug**
A clear description of the bug.

**To Reproduce**
Steps to reproduce the behavior.

**Expected behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**
- OS: [e.g., Ubuntu 22.04]
- Python version: [e.g., 3.10]
- Deployment: [e.g., Docker, AWS]
```

---

## GitHub Actions Secrets

Set up these secrets in GitHub repo settings:

1. Go to Settings → Secrets and variables → Actions
2. Add new repository secrets:

```
DOCKER_USERNAME=your_dockerhub_username
DOCKER_PASSWORD=your_dockerhub_password
```

(Optional for AWS):
```
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
```

---

## Useful Git Commands

### Check Status
```bash
git status
git log --oneline --graph --all
```

### Undo Changes
```bash
# Undo unstaged changes
git checkout -- filename

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1
```

### Update from Remote
```bash
git pull origin main
```

### Create Release
```bash
# Tag a version
git tag -a v1.0.0 -m "Version 1.0.0 - Initial Release"
git push origin v1.0.0
```

---

## Clone Repository (for others)

After pushing, others can clone:

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/omr-microservice.git
cd omr-microservice

# Download model (if not in repo)
# ... follow instructions in README

# Set up environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run
cd app
python main.py
```

---

## Collaborate with Others

### Add Collaborators
1. Go to repository Settings → Collaborators
2. Add GitHub usernames

### Accept Pull Requests
1. Review code changes
2. Run tests
3. Merge if approved

---

## Repository Structure for GitHub

```
omr-microservice/
├── .github/
│   ├── workflows/
│   │   └── deploy.yml          # CI/CD
│   └── ISSUE_TEMPLATE/
│       └── bug_report.md
├── app/                         # Application code
├── models/                      # ML models (or download link)
├── data/
│   ├── templates/
│   └── test_images/
├── deploy/                      # Deployment configs
│   ├── render.yaml
│   └── railway.json
├── scripts/                     # Utility scripts
├── docs/                        # Documentation
├── .gitignore                   # Git ignore rules
├── .dockerignore                # Docker ignore rules
├── .env.example                 # Environment template
├── Dockerfile                   # Docker image
├── docker-compose.yml           # Docker Compose
├── requirements.txt             # Dependencies
├── README.md                    # Main documentation
├── DEPLOYMENT.md                # Deployment guide
└── GIT_SETUP.md                 # This file
```

---

## Quick Start Commands

```bash
# Initialize and push in one go
cd omr-microservice
git init
git add .
git commit -m "Initial commit: OMR Microservice"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/omr-microservice.git
git push -u origin main
```

---

## Troubleshooting

### Large File Error
```
remote: error: File models/epoch20.pt is 67MB; this exceeds GitHub's file size limit of 100MB
```

**Solution:** Use Git LFS or host model separately

### Permission Denied
```bash
# Use HTTPS with personal access token
# Or set up SSH keys
ssh-keygen -t ed25519 -C "your_email@example.com"
# Add public key to GitHub
```

### Merge Conflicts
```bash
# Pull latest changes
git pull origin main

# Resolve conflicts in files
# Then:
git add .
git commit -m "Resolve merge conflicts"
git push
```

---

## Next Steps After Pushing

1. ✅ Verify all files are uploaded correctly
2. ✅ Check README renders properly on GitHub
3. ✅ Test cloning the repo fresh
4. ✅ Set up GitHub Actions (if using CI/CD)
5. ✅ Add collaborators if needed
6. ✅ Create first release/tag
7. ✅ Share repository link!

---

**Your repository is ready!** 🎉

Share it: `https://github.com/YOUR_USERNAME/omr-microservice`
