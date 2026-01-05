# Git/GitHub Workflow Guide

This document outlines the complete workflow from introducing a local change to merging into the main branch, specifically tailored for the Toginnsikt project structure.

## Overview

The workflow follows these main steps:
1. Local Development (Create Branch → Make Changes → Commit)
2. Push to Remote (GitHub)
3. Create Pull Request (PR)
4. Review Process (Automated + Manual)
5. Merge PR
6. Sync Local Repository
7. Handle Submodule Updates (if applicable)

---

## 1. Local Development - Making Changes

### Start from the Base Branch

```bash
# In the dashboard submodule directory
cd toginnsikt-dashboard
git checkout feature/issue-47-route-filter-fix  # or main
git pull origin feature/issue-47-route-filter-fix  # Get latest changes
```

### Create a New Feature Branch

```bash
git checkout -b feature/issue-50-my-feature
```

**Branch naming convention:**
- `feature/issue-XX-description` for new features
- `fix/issue-XX-description` for bug fixes
- Follows separation of concerns (one concern per branch)

### Make Changes

- Edit files in your IDE
- Save files
- Changes are now in your **working directory** (unstaged)

---

## 2. Staging and Committing

### Stage Changes

```bash
git add src/components/my-component.tsx  # Stage specific file
# OR
git add .  # Stage all changes
```

### Commit with Message

```bash
git commit -m "feat(dashboard): add my feature

Description of what this change does.
Refs #50"
```

**Commit message format (Conventional Commits):**
- `feat(scope): description` - New feature
- `fix(scope): description` - Bug fix
- `docs(scope): description` - Documentation
- `refactor(scope): description` - Code refactoring
- `test(scope): description` - Tests
- `chore(scope): description` - Maintenance

**Multiple Commits:**
- You can make multiple commits on the branch as you work
- Each commit should be a logical unit of change

---

## 3. Push to Remote (GitHub)

### First Push (Create Remote Branch)

```bash
git push -u origin feature/issue-50-my-feature
```

The `-u` flag sets up tracking between local and remote branch.

### Subsequent Pushes (After More Commits)

```bash
git push  # Or: git push origin feature/issue-50-my-feature
```

---

## 4. Create a Pull Request (PR)

### Option A: Using GitHub CLI (gh)

```bash
gh pr create \
  --title "feat(dashboard): add my feature" \
  --body "Description of changes..." \
  --base feature/issue-47-route-filter-fix \
  --head feature/issue-50-my-feature
```

### Option B: Using GitHub Web UI

1. After pushing, GitHub shows a banner: "Compare & pull request"
2. Click the banner
3. Fill in title and description
4. Select base branch (usually `feature/issue-47-route-filter-fix` or `main`)
5. Click "Create pull request"

**PR Description Template:**
- Clear title following conventional commits
- Description of changes
- Related issue number (e.g., "Refs #50")
- Testing checklist

---

## 5. Review Process

### Automated Checks

- **CI/CD**: Automated tests and builds run
- **Bugbot**: Cursor's automated code review
- Status checks appear on the PR page

### Manual Review

- Reviewers comment on specific lines or overall PR
- Reviewers can:
  - **Approve**: PR is ready to merge
  - **Request Changes**: Needs fixes before approval
  - **Comment**: General feedback

### Making Changes During Review

```bash
# Make changes locally
git add .
git commit -m "fix(dashboard): address review feedback"
git push  # Updates the PR automatically
```

Each push to the branch automatically updates the PR.

---

## 6. Merging the PR

### After Approval

**Via GitHub Web UI:**
1. Click "Squash and merge" (or "Merge" or "Rebase and merge")
2. Review the commit message
3. Click "Confirm squash and merge"
4. Delete branch (usually auto-deleted if checked)

**Via GitHub CLI:**
```bash
gh pr merge 54 --squash --delete-branch
```

**Merge Options:**
- **Squash and merge**: Combines all commits into one (recommended for feature branches)
- **Merge commit**: Preserves all individual commits
- **Rebase and merge**: Linear history, preserves commits

---

## 7. Syncing Local Repository After Merge

### Update Your Base Branch

```bash
git checkout feature/issue-47-route-filter-fix
git pull origin feature/issue-47-route-filter-fix  # Get merged changes
```

### Clean Up Local Feature Branch

```bash
git branch -d feature/issue-50-my-feature  # Delete local branch
```

If the branch has unmerged changes, use `-D` instead:
```bash
git branch -D feature/issue-50-my-feature  # Force delete
```

---

## 8. Special Consideration: Dashboard as Submodule

Since `toginnsikt-dashboard` is a Git submodule:

### In the Main Repository

```bash
cd /Users/hakonstillingen/Development/toginnsikt
git checkout feature/issue-47-route-filter-fix
git pull
# The submodule reference may need updating
cd toginnsikt-dashboard
git checkout feature/issue-47-route-filter-fix
git pull
cd ..
git add toginnsikt-dashboard
git commit -m "chore: update dashboard submodule reference"
```

### Submodule Workflow

1. Work in the submodule directory (`toginnsikt-dashboard/`)
2. Create branches, commit, push, create PRs in the submodule
3. After merging in submodule, update the submodule reference in main repo
4. Commit the submodule reference update in main repo

---

## Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    LOCAL DEVELOPMENT                          │
├─────────────────────────────────────────────────────────────┤
│  Create Branch → Make Changes → Commit → Push                │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    REMOTE (GitHub)                          │
├─────────────────────────────────────────────────────────────┤
│  Branch exists on GitHub                                    │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    PULL REQUEST                              │
├─────────────────────────────────────────────────────────────┤
│  Create PR → Automated Review → Manual Review → Feedback     │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    MERGE                                     │
├─────────────────────────────────────────────────────────────┤
│  Squash & Merge → Delete Branch                              │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    SYNC LOCAL                                │
├─────────────────────────────────────────────────────────────┤
│  Pull Base Branch → Delete Local Branch → Update Submodule   │
└─────────────────────────────────────────────────────────────┘
```

---

## Common Commands Reference

### Status and Information

```bash
# Check current status
git status

# See what branch you're on
git branch

# See recent commits
git log --oneline -5

# View changes
git diff

# View staged changes
git diff --staged
```

### Working with Changes

```bash
# Discard local changes (if needed)
git restore <file>

# Discard all uncommitted changes
git restore .

# Stash changes temporarily
git stash

# Apply stashed changes
git stash pop

# List stashes
git stash list
```

### Branch Management

```bash
# List all branches
git branch -a

# Switch branches
git checkout <branch-name>

# Create and switch to new branch
git checkout -b <branch-name>

# Delete local branch
git branch -d <branch-name>

# Force delete local branch
git branch -D <branch-name>
```

### Pull Requests

```bash
# View PR status
gh pr view <number>

# List your PRs
gh pr list

# List all PRs
gh pr list --state all

# Checkout PR locally
gh pr checkout <number>
```

### Submodule Commands

```bash
# Initialize submodules
git submodule update --init --recursive

# Update submodule to latest
cd <submodule-directory>
git pull origin <branch>
cd ..
git add <submodule-directory>
git commit -m "chore: update submodule"
```

---

## Best Practices

### Separation of Concerns

- **One concern per branch/PR**: Never mix different types of changes
- **Infrastructure changes** (CI/CD, workflows, deployment) → Separate branch/PR
- **Feature changes** (dashboard, API, data collection) → Separate branch/PR
- **Bug fixes** → Isolated from feature work
- **Documentation updates** → Can be combined only if directly related

### Commit Messages

- Use conventional commit format: `type(scope): description`
- Be descriptive but concise
- Reference issue numbers: `Refs #50` or `Fixes #23`
- Write in imperative mood: "Add feature" not "Added feature"

### Branch Management

- Keep branches focused and short-lived
- Delete branches after merging
- Regularly sync with base branch: `git pull origin <base-branch>`
- Avoid force pushing to shared branches

### Pull Requests

- Write clear, descriptive PR titles
- Include detailed descriptions
- Reference related issues
- Keep PRs small and focused
- Respond to review feedback promptly

---

## Troubleshooting

### "Your local changes would be overwritten by checkout"

**Solution:**
```bash
# Commit your changes
git add .
git commit -m "WIP: temporary commit"

# Or stash them
git stash
git checkout <branch>
git stash pop  # When you return
```

### "Branch has diverged"

**Solution:**
```bash
git pull --rebase origin <branch>
# Or
git pull origin <branch>
```

### "Submodule is dirty"

**Solution:**
```bash
cd <submodule-directory>
git status  # Check what's changed
git add . && git commit -m "..."  # Commit changes
# Or discard: git restore .
```

### Accidentally Committed to Wrong Branch

**Solution:**
```bash
# Create correct branch from current state
git checkout -b correct-branch

# Go back to original branch
git checkout original-branch

# Reset to remove the commit
git reset --hard HEAD~1

# Or use cherry-pick to move commit
git checkout correct-branch
git cherry-pick <commit-hash>
```

---

## Quick Reference Checklist

**Starting New Feature:**
- [ ] Pull latest from base branch
- [ ] Create feature branch
- [ ] Make changes
- [ ] Commit with proper message
- [ ] Push to remote

**Creating PR:**
- [ ] Write clear title and description
- [ ] Reference related issue
- [ ] Wait for automated checks
- [ ] Address any failures

**During Review:**
- [ ] Respond to comments
- [ ] Make requested changes
- [ ] Push updates to PR
- [ ] Re-request review if needed

**After Merge:**
- [ ] Pull base branch locally
- [ ] Delete local feature branch
- [ ] Update submodule reference (if applicable)
- [ ] Verify changes are present

---

## Additional Resources

- [Git Documentation](https://git-scm.com/doc)
- [GitHub CLI Documentation](https://cli.github.com/manual/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Git Submodules](https://git-scm.com/book/en/v2/Git-Tools-Submodules)

---

*Last updated: 2025-12-14*

