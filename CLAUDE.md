# CLAUDE.md - Portfolio Projects

This is a multi-project repository containing data engineering portfolio projects.

## Project Navigation

| Project | CLAUDE.md | Description |
|---------|-----------|-------------|
| E-Commerce Analytics | [ecommerce-retail-analytics/CLAUDE.md](./ecommerce-retail-analytics/CLAUDE.md) | dbt + Snowflake analytics project |

## Repository Structure

```
portfolio-projects/
├── .github/workflows/           # Shared CI/CD pipelines
├── ecommerce-retail-analytics/  # E-Commerce Analytics Project
│   ├── CLAUDE.md               # Project-specific instructions
│   ├── .claude/                # Skills, agents, references
│   ├── dbt/                    # dbt project
│   └── report/                 # Power BI PBIP files
└── [future-projects]/
```

## Working with Projects

When working on a specific project, navigate to its directory and load its CLAUDE.md for detailed context:

```bash
cd ecommerce-retail-analytics
# Then follow project-specific instructions
```

## CI/CD

GitHub Actions workflows are at the repository root (`.github/workflows/`) and use path-based triggers to run appropriate pipelines per project.
