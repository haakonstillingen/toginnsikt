# File Organization Quick Reference Guide

This guide provides a quick reference for where to place different types of files in the Toginnsikt project.

## 📁 Folder Structure

```
toginnsikt/
├── README.md                          # Main project overview
├── enhanced_commute_collector_cloud.py # Core application files
├── collection_scheduler.py            # Core application files
├── config_cloud.py                    # Configuration files
├── requirements.txt                   # Dependencies
├── Dockerfile                         # Deployment files
├── cloudbuild.yaml                    # Deployment files
├── deploy.sh                          # Deployment files
├── toginnsikt-dashboard/              # Frontend application
├── docs/                              # 📚 ALL documentation
│   ├── architecture/                  # System design docs
│   ├── testing/                       # Testing guidelines
│   ├── deployment/                    # Deployment docs
│   └── development/                   # Development docs
├── debug_and_test_scripts/            # 🧪 ALL test/debug scripts
│   ├── test_*.py                      # Test scripts
│   ├── analyze_*.py                   # Analysis scripts
│   ├── debug_*.py                     # Debug scripts
│   ├── check_*.py                     # Status scripts
│   └── testdata/                      # Test data
└── migrations/                        # Database schema changes
```

## 🎯 Where to Place Files

### ✅ Root Directory (Production Files Only)
- **Core Application**: `enhanced_commute_collector_cloud.py`, `collection_scheduler.py`
- **Configuration**: `config_cloud.py`, `requirements.txt`, `env.example`
- **Deployment**: `Dockerfile`, `cloudbuild.yaml`, `deploy.sh`
- **Project Metadata**: `README.md`, `.gitignore`, `.cursorrules`

### 📚 Documentation (`docs/`)
- **Architecture** (`docs/architecture/`): System design, strategies, schemas
- **Testing** (`docs/testing/`): TDD guidelines, test strategies
- **Deployment** (`docs/deployment/`): Migration guides, setup scripts
- **Development** (`docs/development/`): Project status, workflows

### 🧪 Test & Debug Scripts (`debug_and_test_scripts/`)
- **Test Scripts**: `test_<component>_<purpose>.py`
- **Analysis Scripts**: `analyze_<purpose>.py`
- **Debug Scripts**: `debug_<issue>.py`
- **Check Scripts**: `check_<status>.py`
- **Monitor Scripts**: `monitor_<system>.py`

## 📝 File Naming Conventions

### Documentation
- **Format**: `lowercase-with-hyphens.md`
- **Examples**: `collection-strategy.md`, `tdd-guidelines.md`

### Test Scripts
- **Format**: `test_<component>_<purpose>.py`
- **Examples**: `test_route_validation.py`, `test_api_integration.py`

### Analysis Scripts
- **Format**: `analyze_<purpose>.py`
- **Examples**: `analyze_cancellation_data.py`, `analyze_timing_patterns.py`

### Debug Scripts
- **Format**: `debug_<issue>.py`
- **Examples**: `debug_filtering_logic.py`, `debug_time_calculation.py`

### Setup Scripts
- **Format**: `setup-<purpose>.sh`
- **Examples**: `setup-github-trigger.sh`, `setup-database.sh`

## ❌ NEVER Place in Root Directory

- Test scripts
- Documentation files
- Analysis scripts
- Debug scripts
- Setup scripts
- Log files
- Cache files
- Temporary files

## 🤖 For Cursor Agents

**Before creating any file, ask:**
> "Is this a production file or a test/debug/documentation file?"

**If it's a test/debug/documentation file:**
- Place in appropriate `debug_and_test_scripts/` or `docs/` subfolder
- Follow naming conventions
- Never place in root directory

**If it's a production file:**
- Place in root directory
- Ensure it's essential for the application to run

## 🔍 Quick Decision Tree

```
New file to create?
├── Is it a test script? → debug_and_test_scripts/
├── Is it documentation? → docs/<appropriate-subfolder>/
├── Is it analysis/debug? → debug_and_test_scripts/
├── Is it a setup script? → docs/deployment/
└── Is it production code? → root directory
```

## 📋 Code Review Checklist

- [ ] Test scripts are in `debug_and_test_scripts/`
- [ ] Documentation is in appropriate `docs/` subfolder
- [ ] Root directory contains only production files
- [ ] File names follow naming conventions
- [ ] No temporary or cache files in repository
- [ ] Proper categorization of documentation

## 🎯 Benefits

- **Clean Root Directory**: Only essential production files
- **Easy Navigation**: Logical organization by purpose
- **Professional Structure**: Enterprise-grade organization
- **Consistent Naming**: Predictable file locations
- **Maintainable**: Easy to find and update files
