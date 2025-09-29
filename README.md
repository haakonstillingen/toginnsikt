# Toginnsikt - Train Delay Analytics

A comprehensive system for collecting, analyzing, and visualizing Norwegian train delay data using Google Cloud Platform and modern development practices.

## 🚀 Quick Start for AI Agents

**⚠️ IMPORTANT: Read `.cursorrules` file first before making any changes!**

### Development Workflow
1. **Always work on feature branches** - never directly on `main`
2. **Reference GitHub issues** in commit messages: `fix: resolve issue #123`
3. **Follow conventional commits**: `feat:`, `fix:`, `docs:`, `style:`, `refactor:`, `test:`, `chore:`
4. **Create PRs for all changes** - no direct pushes to main
5. **Wait for all workflow checks** to pass before merging

### Security Requirements
- **NEVER hardcode secrets** - use Google Cloud Secret Manager
- **Database credentials** are stored in Secret Manager (see `config_cloud.py`)
- **Environment variables** are only for non-sensitive configuration
- **All changes must pass security scans**

### Architecture Overview
- **Data Collection**: Python scripts collect train data from APIs
- **Database**: PostgreSQL on Google Cloud SQL
- **Deployment**: Google Cloud Run with Cloud Build
- **Secrets**: Google Cloud Secret Manager
- **CI/CD**: GitHub Actions with comprehensive validation

## 📁 Key Files
- `.cursorrules` - **AI agent instructions (READ FIRST)**
- `.github/DEVELOPMENT_WORKFLOW.md` - Complete workflow documentation
- `config_cloud.py` - Configuration and secret management
- `cloudbuild.yaml` - Google Cloud Build configuration
- `.github/workflows/` - CI/CD workflows

## 🔧 Setup for Development
1. Clone repository
2. Create feature branch: `git checkout -b feature/your-feature`
3. Install dependencies: `pip install -r requirements.txt`
4. Configure environment variables (see `.env.example`)
5. Make changes following security guidelines
6. Create PR and wait for checks to pass

## 🚨 Critical Rules for AI Agents
- **Read `.cursorrules` before making any changes**
- **Never bypass security checks** without understanding impact
- **Always test in feature branches** first
- **Always reference issues** when making changes
- **Follow the established deployment pipeline**

## 📊 Project Status
- ✅ Security: Database credentials moved to Secret Manager
- ✅ CI/CD: GitHub Actions workflows configured
- ✅ Branch Protection: Direct pushes to main blocked
- ✅ Code Quality: Automated validation and testing
- ✅ Documentation: Comprehensive workflow guidelines

## 🤝 Contributing
See `.github/DEVELOPMENT_WORKFLOW.md` for detailed contribution guidelines.

---
**For AI Agents**: This project handles production data and requires careful handling of secrets and database operations. Always follow the security guidelines and workflow requirements.
