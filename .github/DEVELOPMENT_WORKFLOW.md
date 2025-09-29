# Development Workflow Guide

## 🔄 **Proper Development Process**

To ensure all changes are properly reviewed and tested, follow this workflow:

### **1. Create Feature Branch**
```bash
# Create and switch to feature branch
git checkout -b feature/issue-15-migration-versioning

# Or for bug fixes
git checkout -b fix/issue-16-user-privileges
```

### **2. Make Changes**
- Make your code changes
- Test locally if possible
- Commit with conventional commit format:
  ```bash
  git commit -m "feat: implement migration versioning system
  
  - Add migration tracking table
  - Implement rollback capabilities
  - Separate migration execution from app startup
  
  Fixes #15"
  ```

### **3. Push and Create Pull Request**
```bash
git push origin feature/issue-15-migration-versioning
```

Then create a PR on GitHub with:
- **Title**: `feat: implement migration versioning system`
- **Description**: Reference the issue `Fixes #15`
- **Reviewers**: Assign appropriate reviewers

### **4. Automated Checks**
The following checks will run automatically:

#### **PR Validation Workflow** (`pr-validation.yml`)
- ✅ Validates PR references an issue
- ✅ Checks for hardcoded secrets
- ✅ Runs code quality checks
- ✅ Tests configuration imports
- ✅ Validates Docker build
- ✅ Tests Cloud Build configuration

#### **Branch Protection Workflow** (`branch-protection.yml`)
- ✅ Prevents direct pushes to main
- ✅ Validates commit messages
- ✅ Runs security scans
- ✅ Enforces conventional commit format

### **5. Review Process**
- **Code Review**: At least one reviewer must approve
- **Testing**: All automated checks must pass
- **Security**: No hardcoded secrets allowed
- **Documentation**: Update relevant docs if needed

### **6. Merge and Deploy**
- **Merge**: Only after all checks pass and review approved
- **Deploy**: Automatic deployment via Cloud Build
- **Issue Update**: Issue automatically moves to "Done" status

## 🚫 **What NOT to Do**

### **❌ Direct Commits to Main**
```bash
# DON'T DO THIS
git checkout main
git commit -m "fix: something"
git push origin main
```

### **❌ Skipping PR Process**
- Never push directly to main
- Always create a feature branch
- Always submit a PR for review

### **❌ Hardcoded Secrets**
```python
# DON'T DO THIS
DB_PASSWORD = "my-secret-password"

# DO THIS INSTEAD
DB_PASSWORD = get_secret('toginnsikt-db-password')
```

## 📋 **Issue Workflow States**

1. **Backlog** → Issue created, not started
2. **In Progress** → Feature branch created, work started
3. **In Review** → Pull Request created, under review
4. **Testing** → PR approved, testing in progress
5. **Done** → Merged and deployed

## 🔧 **Branch Naming Convention**

- `feature/issue-XX-description` - New features
- `fix/issue-XX-description` - Bug fixes
- `docs/issue-XX-description` - Documentation
- `refactor/issue-XX-description` - Code refactoring
- `security/issue-XX-description` - Security fixes

## 📝 **Commit Message Format**

Use conventional commits:
```
type(scope): description

Detailed description if needed

Fixes #XX
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Maintenance tasks
- `security`: Security improvements

## 🛡️ **Security Requirements**

- ✅ No hardcoded secrets in code
- ✅ Use Secret Manager for sensitive data
- ✅ All PRs must pass security scans
- ✅ Database credentials must be properly managed
- ✅ Service accounts with minimal permissions

## 🧪 **Testing Requirements**

- ✅ All code must be tested locally when possible
- ✅ Configuration changes must be validated
- ✅ Docker builds must succeed
- ✅ Cloud Build configuration must be valid
- ✅ No breaking changes without proper migration

## 📊 **Project Board Integration**

Issues automatically move through states:
- **Backlog** → **In Progress** (when branch created)
- **In Progress** → **In Review** (when PR created)
- **In Review** → **Testing** (when PR approved)
- **Testing** → **Done** (when merged)

## 🚀 **Deployment Process**

1. **PR Merged** → Triggers Cloud Build
2. **Cloud Build** → Builds and deploys to Cloud Run
3. **Deployment** → Updates project board
4. **Monitoring** → Logs and health checks

## 📞 **Getting Help**

- Check existing issues for similar problems
- Review this workflow guide
- Ask in PR comments for clarification
- Use GitHub discussions for general questions
