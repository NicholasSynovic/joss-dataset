# JOSS Dataset Toolkit

## About

This repository provides a command-line toolkit for building a local dataset
from the Journal of Open Source Software (JOSS) GitHub issues. The `joss` CLI
fetches issues from the JOSS review tracker, normalizes them, and loads the
results into a SQLite database for analysis.

## Build Instructions

This project uses `uv` for dependency management and pre-commit for linting.

```bash
# Install dependencies and set up pre-commit hooks
make create-dev

# Build and install from source
make build
```

## Run Instructions

The CLI entry point is `joss`.

```text
usage: joss [-h] {joss} ...

joss dataset toolkit.

positional arguments:
  {joss}
    joss      Get all Journal of Open Source Software (JOSS) projects.

options:
  -h, --help  show this help message and exit
```

### Environment Requirements

`GITHUB_TOKEN` is required and must be a classic GitHub Personal Access Token
(PAT) with access to the JOSS repository. Export it before running the CLI.

```bash
export GITHUB_TOKEN="ghp_your_classic_token_here"
```

### Usage Examples

```bash
# Fetch JOSS issues and write to a SQLite database
joss joss --out-file joss.db

# Write to a custom database path
joss joss --out-file data/joss_issues.db
```
