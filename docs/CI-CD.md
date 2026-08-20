# GitHub Actions CI/CD - FAANG-Level Mental Model

## Core Mental Model

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        GITHUB ACTIONS HIERARCHY                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   WORKFLOW (.yml file)                                                      │
│   └── Triggered by EVENTS (push, pull_request, schedule, manual)           │
│       └── Contains JOBS (run in parallel by default)                        │
│           └── Jobs contain STEPS (run sequentially)                         │
│               └── Steps run ACTIONS or shell COMMANDS                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### The 5 Fundamental Concepts

| Concept | What It Is | Analogy |
|---------|------------|---------|
| **Workflow** | A YAML file in `.github/workflows/` | A recipe |
| **Event** | What triggers the workflow | "When to cook" |
| **Job** | A set of steps running on one machine | A chef's station |
| **Step** | A single task within a job | One cooking instruction |
| **Action** | Reusable code (from marketplace or custom) | A kitchen appliance |

---

## Workflow Anatomy

```yaml
# ═══════════════════════════════════════════════════════════════════════════
# SECTION 1: METADATA
# ═══════════════════════════════════════════════════════════════════════════
name: My Workflow                    # Display name in GitHub UI

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 2: TRIGGERS (Events)
# ═══════════════════════════════════════════════════════════════════════════
on:
  push:                              # Trigger on push
    branches: [main]                 # Only main branch
    paths:                           # Only these paths (optimization)
      - 'src/**'
      - '.github/workflows/*.yml'

  pull_request:                      # Trigger on PR
    branches: [main]
    types: [opened, synchronize]     # Specific PR events

  schedule:                          # Cron schedule
    - cron: '0 0 * * *'              # Daily at midnight UTC

  workflow_dispatch:                 # Manual trigger button
    inputs:                          # Optional inputs for manual runs
      environment:
        description: 'Target environment'
        required: true
        default: 'staging'
        type: choice
        options: [staging, production]

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 3: ENVIRONMENT VARIABLES (Workflow-level)
# ═══════════════════════════════════════════════════════════════════════════
env:
  NODE_VERSION: '20'                 # Available to all jobs
  PROJECT_DIR: src/app

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 4: JOBS
# ═══════════════════════════════════════════════════════════════════════════
jobs:
  job-name:
    name: Human Readable Name        # Shows in GitHub UI
    runs-on: ubuntu-latest           # Runner machine type

    # Job-level settings
    timeout-minutes: 30              # Fail if exceeds
    environment: production          # GitHub Environment (for secrets/approvals)
    concurrency:                     # Prevent parallel runs
      group: ${{ github.ref }}
      cancel-in-progress: true

    # Job outputs (for passing data to other jobs)
    outputs:
      version: ${{ steps.get-version.outputs.version }}

    # Steps run sequentially
    steps:
      - name: Step Name
        id: step-id                  # Reference this step later
        uses: actions/checkout@v4    # Use a marketplace action
        with:                        # Action inputs
          fetch-depth: 0
        env:                         # Step-level env vars
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        if: success()                # Conditional execution
        continue-on-error: true      # Don't fail job if this fails
```

---

## Event Types Deep Dive

### Push Events
```yaml
on:
  push:
    branches:
      - main                         # Exact match
      - 'release/**'                 # Glob pattern
      - '!release/beta-*'            # Exclude pattern
    tags:
      - 'v*'                         # Tag patterns
    paths:
      - 'src/**'                     # Only run if these change
    paths-ignore:
      - '**.md'                      # Ignore markdown changes
```

### Pull Request Events
```yaml
on:
  pull_request:
    branches: [main, develop]
    types:
      - opened                       # PR created
      - synchronize                  # New commits pushed
      - reopened                     # PR reopened
      - closed                       # PR closed/merged
```

### Manual Trigger with Inputs
```yaml
on:
  workflow_dispatch:
    inputs:
      deploy_env:
        description: 'Environment to deploy'
        required: true
        type: choice
        options: ['dev', 'staging', 'prod']
      full_refresh:
        description: 'Run full refresh?'
        type: boolean
        default: false
```

---

## Jobs: Parallel vs Sequential

### Default: Parallel Execution
```yaml
jobs:
  lint:           # ─┐
    ...           #  ├── Run in PARALLEL
  test:           # ─┤
    ...           #  │
  build:          # ─┘
    ...
```

### Sequential with `needs`
```yaml
jobs:
  lint:
    ...

  test:
    needs: lint              # Wait for lint to complete
    ...

  build:
    needs: [lint, test]      # Wait for BOTH to complete
    ...

  deploy:
    needs: build
    if: github.ref == 'refs/heads/main'  # Only on main branch
    ...
```

### Visualization
```
PARALLEL (default):          SEQUENTIAL (with needs):

┌──────┐ ┌──────┐ ┌──────┐   ┌──────┐
│ lint │ │ test │ │build │   │ lint │
└──────┘ └──────┘ └──────┘   └──┬───┘
    │        │        │          │
    ▼        ▼        ▼          ▼
 (all finish at own pace)     ┌──────┐
                              │ test │
                              └──┬───┘
                                 │
                                 ▼
                              ┌──────┐
                              │build │
                              └──┬───┘
                                 │
                                 ▼
                              ┌──────┐
                              │deploy│
                              └──────┘
```

---

## Steps: Actions vs Commands

### Using Marketplace Actions
```yaml
steps:
  # Checkout code (almost always first step)
  - name: Checkout
    uses: actions/checkout@v4
    with:
      fetch-depth: 0               # Full history (needed for some tools)

  # Setup language runtime
  - name: Setup Python
    uses: actions/setup-python@v5
    with:
      python-version: '3.11'
      cache: 'pip'                 # Cache dependencies

  # Upload/Download artifacts
  - name: Upload Build
    uses: actions/upload-artifact@v4
    with:
      name: my-artifact
      path: dist/
      retention-days: 30
```

### Running Shell Commands
```yaml
steps:
  # Single command
  - name: Install dependencies
    run: pip install -r requirements.txt

  # Multi-line commands
  - name: Build and test
    run: |
      echo "Building..."
      npm run build
      echo "Testing..."
      npm test

  # Change directory (use cd in run, not working-directory for reliability)
  - name: Run in subdirectory
    run: |
      cd my-project
      npm install

  # Use different shell
  - name: PowerShell command
    shell: pwsh
    run: Write-Host "Hello from PowerShell"
```

---

## Secrets and Variables

### Hierarchy (Most Specific Wins)
```
Organization Secrets/Variables
    └── Repository Secrets/Variables
        └── Environment Secrets/Variables  ← Highest priority
```

### Using Secrets
```yaml
env:
  # At workflow level
  API_KEY: ${{ secrets.API_KEY }}

jobs:
  deploy:
    environment: production          # Use environment-specific secrets
    steps:
      - name: Deploy
        env:
          # At step level
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: ./deploy.sh
```

### Security Best Practices
```yaml
# GOOD: Secrets are masked in logs
- run: echo "Deploying to ${{ secrets.SERVER }}"

# BAD: Never echo secrets directly
- run: echo "${{ secrets.API_KEY }}"  # Will show ***

# GOOD: Write to file securely
- name: Setup credentials
  run: |
    echo "${{ secrets.PRIVATE_KEY }}" > /tmp/key.pem
    chmod 600 /tmp/key.pem

# GOOD: Clean up secrets
- name: Cleanup
  if: always()                       # Run even if job fails
  run: rm -f /tmp/key.pem
```

---

## Conditionals and Expressions

### Common Conditions
```yaml
steps:
  # Run only on main branch
  - if: github.ref == 'refs/heads/main'

  # Run only on PR
  - if: github.event_name == 'pull_request'

  # Run only if previous step succeeded
  - if: success()

  # Run only if previous step failed
  - if: failure()

  # Always run (cleanup)
  - if: always()

  # Run if specific file changed
  - if: contains(github.event.head_commit.modified, 'package.json')

  # Combine conditions
  - if: github.ref == 'refs/heads/main' && github.event_name == 'push'
```

### Using Outputs Between Steps
```yaml
steps:
  - name: Get version
    id: version
    run: echo "value=$(cat VERSION)" >> $GITHUB_OUTPUT

  - name: Use version
    run: echo "Version is ${{ steps.version.outputs.value }}"
```

### Using Outputs Between Jobs
```yaml
jobs:
  build:
    outputs:
      artifact-name: ${{ steps.build.outputs.name }}
    steps:
      - id: build
        run: echo "name=my-build-123" >> $GITHUB_OUTPUT

  deploy:
    needs: build
    steps:
      - run: echo "Deploying ${{ needs.build.outputs.artifact-name }}"
```

---

## Matrix Builds (Parallel Testing)

```yaml
jobs:
  test:
    strategy:
      fail-fast: false              # Don't cancel others if one fails
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python: ['3.9', '3.10', '3.11']
        exclude:                    # Skip specific combinations
          - os: windows-latest
            python: '3.9'
        include:                    # Add specific combinations
          - os: ubuntu-latest
            python: '3.12'
            experimental: true

    runs-on: ${{ matrix.os }}
    continue-on-error: ${{ matrix.experimental || false }}

    steps:
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python }}
```

---

## CI vs CD: The Mental Model

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CI/CD PIPELINE FLOW                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   DEVELOPER                                                                 │
│       │                                                                     │
│       ▼                                                                     │
│   ┌───────────┐     ┌─────────────────────────────────────────────────┐    │
│   │  Create   │────▶│              CI (Continuous Integration)        │    │
│   │    PR     │     │  ┌─────────┐  ┌─────────┐  ┌─────────────────┐  │    │
│   └───────────┘     │  │  Lint   │─▶│  Test   │─▶│  Build Preview  │  │    │
│                     │  └─────────┘  └─────────┘  └─────────────────┘  │    │
│                     │         Runs on: pull_request                   │    │
│                     │         Purpose: Validate changes               │    │
│                     │         Output: Pass/Fail status on PR          │    │
│                     └─────────────────────────────────────────────────┘    │
│                                        │                                    │
│                                        ▼                                    │
│                              ┌─────────────────┐                            │
│                              │  Code Review    │                            │
│                              │  + CI Passes    │                            │
│                              └────────┬────────┘                            │
│                                       │                                     │
│                                       ▼                                     │
│   ┌───────────┐     ┌─────────────────────────────────────────────────┐    │
│   │   Merge   │────▶│              CD (Continuous Deployment)         │    │
│   │ to main   │     │  ┌─────────┐  ┌─────────┐  ┌─────────────────┐  │    │
│   └───────────┘     │  │  Build  │─▶│  Test   │─▶│     Deploy      │  │    │
│                     │  └─────────┘  └─────────┘  └─────────────────┘  │    │
│                     │         Runs on: push to main                   │    │
│                     │         Purpose: Deploy to production           │    │
│                     │         Output: Live application                │    │
│                     └─────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## FAANG-Level CI Workflow Template

```yaml
# .github/workflows/ci.yml
name: CI

on:
  pull_request:
    branches: [main]
    paths:
      - 'src/**'
      - 'tests/**'
      - '.github/workflows/ci.yml'

env:
  PROJECT_PATH: src

jobs:
  # ─────────────────────────────────────────────────────────────────────────
  # JOB 1: Code Quality (Fast feedback)
  # ─────────────────────────────────────────────────────────────────────────
  lint:
    name: Code Quality
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install linters
        run: pip install ruff black mypy

      - name: Run linters
        run: |
          ruff check ${{ env.PROJECT_PATH }}
          black --check ${{ env.PROJECT_PATH }}
          mypy ${{ env.PROJECT_PATH }}

  # ─────────────────────────────────────────────────────────────────────────
  # JOB 2: Unit Tests
  # ─────────────────────────────────────────────────────────────────────────
  test:
    name: Unit Tests
    runs-on: ubuntu-latest
    timeout-minutes: 15

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: pip install -r requirements.txt -r requirements-test.txt

      - name: Run tests with coverage
        run: pytest --cov=${{ env.PROJECT_PATH }} --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: coverage.xml

  # ─────────────────────────────────────────────────────────────────────────
  # JOB 3: Integration Tests (May need secrets)
  # ─────────────────────────────────────────────────────────────────────────
  integration:
    name: Integration Tests
    runs-on: ubuntu-latest
    timeout-minutes: 30
    needs: [lint, test]  # Only run if lint and test pass

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup environment
        run: |
          # Setup test database, etc.
          docker-compose -f docker-compose.test.yml up -d

      - name: Run integration tests
        env:
          DATABASE_URL: ${{ secrets.TEST_DATABASE_URL }}
        run: pytest tests/integration/

      - name: Cleanup
        if: always()
        run: docker-compose -f docker-compose.test.yml down

  # ─────────────────────────────────────────────────────────────────────────
  # JOB 4: PR Comment (Always runs, summarizes results)
  # ─────────────────────────────────────────────────────────────────────────
  summary:
    name: PR Summary
    runs-on: ubuntu-latest
    needs: [lint, test, integration]
    if: always()
    permissions:
      pull-requests: write

    steps:
      - name: Comment on PR
        uses: actions/github-script@v7
        with:
          script: |
            const results = {
              lint: '${{ needs.lint.result }}',
              test: '${{ needs.test.result }}',
              integration: '${{ needs.integration.result }}'
            };

            const emoji = (r) => r === 'success' ? '✅' : r === 'failure' ? '❌' : '⚠️';
            const allPassed = Object.values(results).every(r => r === 'success');

            const body = `## CI Results

            | Check | Status |
            |-------|--------|
            | Lint | ${emoji(results.lint)} ${results.lint} |
            | Unit Tests | ${emoji(results.test)} ${results.test} |
            | Integration | ${emoji(results.integration)} ${results.integration} |

            ${allPassed ? '🎉 All checks passed!' : '⚠️ Some checks need attention.'}
            `;

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: body
            });
```

---

## FAANG-Level CD Workflow Template

```yaml
# .github/workflows/cd.yml
name: CD

on:
  push:
    branches: [main]
    paths:
      - 'src/**'
      - '.github/workflows/cd.yml'

  workflow_dispatch:
    inputs:
      environment:
        description: 'Deploy environment'
        required: true
        default: 'production'
        type: choice
        options: [staging, production]

env:
  PROJECT_PATH: src

jobs:
  # ─────────────────────────────────────────────────────────────────────────
  # JOB 1: Build
  # ─────────────────────────────────────────────────────────────────────────
  build:
    name: Build
    runs-on: ubuntu-latest
    timeout-minutes: 15
    outputs:
      version: ${{ steps.version.outputs.value }}

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Generate version
        id: version
        run: echo "value=$(date +%Y%m%d)-${GITHUB_SHA::7}" >> $GITHUB_OUTPUT

      - name: Build application
        run: |
          cd ${{ env.PROJECT_PATH }}
          # Build commands here

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: build-${{ steps.version.outputs.value }}
          path: dist/
          retention-days: 30

  # ─────────────────────────────────────────────────────────────────────────
  # JOB 2: Deploy to Staging (automatic)
  # ─────────────────────────────────────────────────────────────────────────
  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: build
    environment: staging

    steps:
      - name: Download artifact
        uses: actions/download-artifact@v4
        with:
          name: build-${{ needs.build.outputs.version }}

      - name: Deploy to staging
        env:
          DEPLOY_KEY: ${{ secrets.STAGING_DEPLOY_KEY }}
        run: |
          echo "Deploying version ${{ needs.build.outputs.version }} to staging"
          # Deploy commands here

  # ─────────────────────────────────────────────────────────────────────────
  # JOB 3: Deploy to Production (requires approval)
  # ─────────────────────────────────────────────────────────────────────────
  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: [build, deploy-staging]
    environment: production          # Requires approval if configured
    if: github.ref == 'refs/heads/main'

    steps:
      - name: Download artifact
        uses: actions/download-artifact@v4
        with:
          name: build-${{ needs.build.outputs.version }}

      - name: Deploy to production
        env:
          DEPLOY_KEY: ${{ secrets.PROD_DEPLOY_KEY }}
        run: |
          echo "Deploying version ${{ needs.build.outputs.version }} to production"
          # Deploy commands here

  # ─────────────────────────────────────────────────────────────────────────
  # JOB 4: Notify (Slack, Teams, etc.)
  # ─────────────────────────────────────────────────────────────────────────
  notify:
    name: Notify
    runs-on: ubuntu-latest
    needs: [build, deploy-staging, deploy-production]
    if: always()

    steps:
      - name: Send notification
        run: |
          if [ "${{ needs.deploy-production.result }}" == "success" ]; then
            echo "✅ Deployment successful!"
          else
            echo "❌ Deployment failed!"
          fi
          # Send to Slack/Teams/etc.
```

---

## Your dbt CI/CD Explained

### CI Workflow (dbt-ci.yml)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         YOUR dbt CI WORKFLOW                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TRIGGER: pull_request to main                                              │
│           (only if dbt files changed)                                       │
│                                                                             │
│  ┌─────────────────┐     ┌─────────────────────────────────────────────┐   │
│  │   lint (Job 1)  │     │            dbt-build (Job 2)                │   │
│  │                 │     │                                             │   │
│  │  1. Checkout    │     │  1. Checkout (full history)                 │   │
│  │  2. Setup Python│     │  2. Setup Python                            │   │
│  │  3. SQLFluff    │     │  3. Debug directory structure               │   │
│  │     (lenient)   │     │  4. Install dbt                             │   │
│  │                 │     │  5. Validate account format                 │   │
│  └────────┬────────┘     │  6. Setup private key                       │   │
│           │              │  7. Create profiles.yml                     │   │
│           │              │  8. dbt deps                                │   │
│           │              │  9. dbt debug (connection test)             │   │
│           │              │ 10. Check for prod manifest                 │   │
│           │              │ 11. dbt build (Slim CI or Full)             │   │
│           │              │ 12. dbt docs generate                       │   │
│           │              │ 13. Upload manifest artifact                │   │
│           │              │ 14. Cleanup private key                     │   │
│           │              └─────────────────────────────────────────────┘   │
│           │                              │                                  │
│           └──────────────┬───────────────┘                                  │
│                          ▼                                                  │
│               ┌─────────────────────┐                                       │
│               │  comment (Job 3)    │                                       │
│               │                     │                                       │
│               │  Post CI results    │                                       │
│               │  as PR comment      │                                       │
│               └─────────────────────┘                                       │
│                                                                             │
│  KEY FEATURES:                                                              │
│  • Slim CI: Only tests modified models + downstream                         │
│  • Isolated schema: CI_PR_xxx (no impact on dev/prod)                       │
│  • Lenient linting: Warnings don't fail the build                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### CD Workflow (dbt-cd.yml)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         YOUR dbt CD WORKFLOW                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TRIGGER: push to main (merge) OR manual workflow_dispatch                  │
│           (only if dbt files changed)                                       │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      deploy (Job 1)                                 │   │
│  │                      environment: production                        │   │
│  │                                                                     │   │
│  │   1. Checkout                                                       │   │
│  │   2. Setup Python                                                   │   │
│  │   3. Install dbt                                                    │   │
│  │   4. Validate account format                                        │   │
│  │   5. Setup private key                                              │   │
│  │   6. Create profiles.yml (PROD)                                     │   │
│  │   7. dbt deps                                                       │   │
│  │   8. dbt debug                                                      │   │
│  │   9. dbt build (full or --full-refresh)                             │   │
│  │  10. dbt docs generate                                              │   │
│  │  11. Upload prod manifest (for Slim CI)                             │   │
│  │  12. Upload docs artifact                                           │   │
│  │  13. Cleanup private key                                            │   │
│  │                                                                     │   │
│  └──────────────────────────────┬──────────────────────────────────────┘   │
│                                 │                                           │
│                                 ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      notify (Job 2)                                 │   │
│  │                                                                     │   │
│  │   Print deployment status (success/failure)                         │   │
│  │   Could be extended to Slack/Teams notification                     │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  KEY FEATURES:                                                              │
│  • Deploys to PROD database (ECOMMERCE_RETAIL_DB_PROD)                      │
│  • Saves manifest for future Slim CI comparisons                            │
│  • Manual trigger option with full_refresh flag                             │
│  • Production environment (can require approvals)                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## FAANG Best Practices Checklist

### Security
- [ ] Never echo secrets (they're masked but still risky)
- [ ] Use `environment` for production secrets (enables approvals)
- [ ] Clean up credentials in `if: always()` step
- [ ] Validate secret formats before use
- [ ] Use OIDC for cloud providers (no long-lived secrets)

### Performance
- [ ] Use `paths` filter to skip unnecessary runs
- [ ] Cache dependencies (`actions/cache` or built-in caching)
- [ ] Run independent jobs in parallel
- [ ] Use matrix builds for multi-platform testing
- [ ] Implement Slim CI (only test what changed)

### Reliability
- [ ] Set `timeout-minutes` on all jobs
- [ ] Use `continue-on-error` for non-critical steps
- [ ] Add `if: always()` for cleanup steps
- [ ] Use `concurrency` to prevent race conditions
- [ ] Pin action versions (`@v4` not `@latest`)

### Observability
- [ ] Add PR comments with results
- [ ] Upload artifacts for debugging
- [ ] Use meaningful step names
- [ ] Add debug steps for troubleshooting
- [ ] Integrate with Slack/Teams for notifications

### Maintainability
- [ ] Use environment variables for repeated values
- [ ] Extract complex logic to composite actions
- [ ] Document workflow purpose in comments
- [ ] Keep workflows focused (CI separate from CD)
- [ ] Use reusable workflows for shared logic

---

## Rollback & Recovery Procedures

### When to Rollback

| Scenario | Severity | Action |
|----------|----------|--------|
| Tests fail in production | 🔴 Critical | Immediate rollback |
| Model produces wrong data | 🔴 Critical | Rollback + investigate |
| Performance degradation | 🟡 High | Assess impact, then rollback |
| Non-critical model fails | 🟢 Low | Fix forward in new PR |

### Rollback Methods

#### Method 1: Git Revert (Recommended)

Safest approach - creates a new commit that undoes the breaking change:

```bash
# 1. Find the breaking commit
git log --oneline -10

# 2. Revert it (creates new commit)
git revert <commit-sha>

# 3. Push to main (triggers CD automatically)
git push origin main
```

**Pros:** Full audit trail, no force push needed
**Cons:** Adds commits to history

#### Method 2: Manual Re-deployment

Use workflow_dispatch to redeploy a previous state:

1. Go to **Actions** → **dbt CD** → **Run workflow**
2. Optionally enable `full_refresh` if schema changed
3. Monitor deployment

**When to use:** When you need to rebuild all models from scratch

#### Method 3: Exclude Broken Model

If one model is broken but others are fine:

```bash
# Run in Snowflake or via dbt
dbt build --exclude model_name
```

**When to use:** Isolate a single broken model while investigating

### Recovery Checklist

When a production deployment fails:

- [ ] **1. Assess impact** - Which models failed? Are dashboards affected?
- [ ] **2. Notify stakeholders** - Alert data consumers of potential issues
- [ ] **3. Check test results** - Review the failed tests in GitHub Actions
- [ ] **4. Decide: rollback or fix forward?**
  - Rollback if: Critical data errors, multiple models affected
  - Fix forward if: Minor issue, quick fix available
- [ ] **5. Execute recovery** - Use Method 1, 2, or 3 above
- [ ] **6. Verify** - Run `dbt test` on affected models
- [ ] **7. Post-mortem** - Document what went wrong and how to prevent it

### Snowflake-Specific Recovery

#### Check Recent Table Changes
```sql
-- See what changed in the last 24 hours
SELECT *
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE QUERY_TYPE IN ('CREATE_TABLE_AS_SELECT', 'INSERT', 'MERGE')
  AND DATABASE_NAME = 'ECOMMERCE_RETAIL_DB_PROD'
  AND START_TIME > DATEADD(hour, -24, CURRENT_TIMESTAMP())
ORDER BY START_TIME DESC;
```

#### Time Travel Recovery (if needed)
```sql
-- Restore table to state before bad deployment
CREATE OR REPLACE TABLE MARTS.fct_orders AS
SELECT * FROM MARTS.fct_orders AT (OFFSET => -3600);  -- 1 hour ago

-- Or use timestamp
CREATE OR REPLACE TABLE MARTS.fct_orders AS
SELECT * FROM MARTS.fct_orders AT (TIMESTAMP => '2024-01-15 10:00:00'::TIMESTAMP);
```

**Note:** Time travel retention is 1 day by default (up to 90 days on Enterprise).

### Prevention: Pre-deployment Checks

Add these to your workflow before deploying:

```yaml
# Add to dbt-cd.yml before the deploy step
- name: Pre-deployment validation
  run: |
    cd ${{ env.DBT_PROJECT_PATH }}
    # Compile to catch SQL errors
    dbt compile
    # Run tests on source data
    dbt test --select source:*
```

---

## Quick Reference: Context Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `github.event_name` | Event that triggered workflow | `pull_request` |
| `github.ref` | Full ref | `refs/heads/main` |
| `github.sha` | Commit SHA | `a1b2c3d4...` |
| `github.actor` | User who triggered | `username` |
| `github.repository` | Repo name | `owner/repo` |
| `github.event.pull_request.number` | PR number | `123` |
| `github.run_id` | Workflow run ID | `1234567890` |
| `runner.os` | Runner OS | `Linux` |
| `secrets.GITHUB_TOKEN` | Auto-generated token | (masked) |

---

## Debugging Workflows

```yaml
# Add debug step
- name: Debug context
  run: |
    echo "Event: ${{ github.event_name }}"
    echo "Ref: ${{ github.ref }}"
    echo "SHA: ${{ github.sha }}"
    echo "Actor: ${{ github.actor }}"
    echo "Working directory: $(pwd)"
    ls -la

# Enable debug logging (set in repository secrets)
# ACTIONS_RUNNER_DEBUG: true
# ACTIONS_STEP_DEBUG: true
```

---

## Summary: The 10 Commandments of GitHub Actions

1. **Trigger wisely** - Use `paths` to avoid unnecessary runs
2. **Fail fast** - Run linters before expensive tests
3. **Parallelize** - Independent jobs should run in parallel
4. **Cache aggressively** - Dependencies, build outputs, Docker layers
5. **Secure secrets** - Use environments, validate formats, clean up
6. **Timeout everything** - Prevent runaway jobs
7. **Comment on PRs** - Give developers immediate feedback
8. **Artifact everything** - Logs, coverage, manifests for debugging
9. **Pin versions** - Actions, runtimes, dependencies
10. **Keep it simple** - Split complex workflows, document thoroughly
