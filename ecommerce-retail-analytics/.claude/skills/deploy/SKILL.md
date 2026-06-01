---
name: deploy
description: Commit changes and open a pull request
allowed-tools: Read Bash Glob Grep
---

# /deploy - Commit & Open PR

## Purpose
Commit validated changes to the repository and open a draft pull request with proper context.

## Prerequisites
- `/test` has been run and all tests pass
- Changes are ready for review

## Procedure

### Step 1: Review Changed Files

```bash
git status
git diff --stat
```

Verify:
- [ ] Only intended files are modified
- [ ] No sensitive data (credentials, .env) included
- [ ] No unrelated changes mixed in

### Step 2: Create Feature Branch (if not already on one)

```bash
# If on main, create a feature branch
git checkout -b feature/<descriptive-name>

# Branch naming conventions:
# feature/<name>    - New functionality
# fix/<name>        - Bug fixes
# refactor/<name>   - Code improvements
# docs/<name>       - Documentation only
```

### Step 3: Stage Changes

Stage specific files (preferred over `git add -A`):

```bash
# Stage SQL files
git add dbt/models/<path>/<model>.sql

# Stage YAML files
git add dbt/models/<path>/_*_models.yml

# Stage any modified macros
git add dbt/macros/<macro>.sql
```

### Step 4: Create Commit

Write a clear commit message following conventions:

**Commit types:**
- `feat`: New feature/model
- `fix`: Bug fix
- `refactor`: Code improvement
- `docs`: Documentation
- `test`: Test additions
- `chore`: Maintenance

### Step 5: Push to Remote

```bash
git push -u origin <branch-name>
```

### Step 6: Open Pull Request

Use GitHub CLI with a proper PR template including:
- Summary (1-3 bullet points)
- Changes made
- Test results
- Checklist

### Step 7: Verify CI Pipeline

After PR is created:
1. Check GitHub Actions workflow starts
2. Monitor CI job progress
3. Address any CI failures before requesting review

```bash
# Watch CI status
gh pr checks --watch
```

## Output Checklist

- [ ] Feature branch created
- [ ] Changes staged (no sensitive files)
- [ ] Commit message follows conventions
- [ ] Pushed to remote
- [ ] PR opened with full context
- [ ] CI pipeline started

## Next Steps
1. Monitor CI for any failures
2. Request review from team members
3. Address feedback
4. Merge when approved
