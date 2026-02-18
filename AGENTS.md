# Agent Guidelines for JOSS Dataset Repository

This document provides instructions for agentic coding systems working in this Python project.

## Build, Lint, and Test Commands

### Development Setup

```bash
# Initial setup (installs pre-commit hooks and dependencies via uv)
make create-dev

# Full build (versions, builds distribution, installs package)
make build
```

### Linting and Formatting

Pre-commit hooks automatically enforce code quality:

```bash
# Run all pre-commit checks
pre-commit run --all

# Run on specific files
pre-commit run ruff-check --files joss/utils.py joss/main.py
pre-commit run ruff-format --files joss/utils.py joss/main.py
pre-commit run isort --files joss/utils.py joss/main.py
pre-commit run bandit --files joss/utils.py joss/main.py
```

### Testing

Currently, the project does not have a test suite. All analysis scripts are in `joss/analysis/` and can be verified by running them manually with appropriate data inputs or checking linter/formatter compliance.

## Code Style Guidelines

### Language & Version

- **Python**: 3.13 (as per `pyproject.toml`), compatible with 3.10+

### Imports

- **Order**: Follow isort (Black profile)
  1. Standard library imports
  2. Third-party imports (blank line before)
  3. Local imports (blank line before)
- **Style**: Use explicit absolute imports; avoid star imports

### Formatting

- **Formatter**: Ruff (replaces Black)
- **Line length**: 88 characters
- **Quotes**: Double quotes (`"string"`)
- **Indentation**: 4 spaces
- **Trailing commas**: Respected

### Type Hints

- **Mandatory**: All function parameters and returns must have type hints
- **Style**: Use modern syntax (e.g., `list[T]` instead of `List[T]`)
- **Return types**: Always specify, use `-> None` for void functions
- **Union types**: Use `|` operator: `int | str`
- **ANN401 Exception**: `typing.Any` is allowed when necessary (e.g., `json.loads`); suppress with `# noqa: ANN401`

### Naming Conventions

- **Functions/variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Privates**: Prefix with `_` (e.g., `_internal_helper()`)
- **Logger**: Name as `LOGGER = logging.getLogger(__name__)`

### Documentation

- **Module docstrings**: Required at top of file
- **Function/method docstrings**: Required for all public functions
- **Format**: Google-style docstrings with Args, Returns, Raises sections

### Error Handling

- **Exceptions**: Raise with explicit error messages
- **Type validation**: Check types explicitly before operations
- **Custom messages**: Store in `msg` variable before raising

## Linting Rules (Ruff)

Enabled rule categories include: security (S), type annotations (ANN), naming (N), error handling (E), imports (I), docstrings (D), and many others. Key ignored rules:

- `D203`: Blank line before docstring (conflicts with D211)
- `D212`: Summary after description newline
- `COM812`: Trailing comma conflicts with Black
- `S404`: Use of subprocess (when intentional)

## File Encoding

- **Encoding**: UTF-8 with LF line endings
- **Final newline**: All files must end with newline character

## Project Structure

```text
joss/
  ├── __init__.py
  ├── main.py              # Entry point with subcommands (joss ingest/transform)
  ├── cli.py               # CLI utilities class
  ├── logger.py             # Logging utilities class
  ├── utils.py             # Shared utility functions (JOSSUtils class)
  ├── analysis/            # Analysis scripts for JOSS dataset
  ├── ingest/
  │   ├── github_issues.py       # Standalone ingestion (backward compatible)
  │   └── joss.py                 # Unified ingest subcommand
  └── transform/
      ├── joss_submission.py           # JOSS submission model
      ├── normalize_joss_submissions.py # Standalone transform (backward compatible)
      └── joss.py                      # Unified transform subcommand
```

## CLI Commands

### Unified CLI (via pyproject.toml entry point `joss`)

```bash
# Ingest GitHub issues
joss ingest --max-pages 1

# Transform issues to normalized format
joss transform --in-file github_issues_1234567890.json
```

### Standalone Scripts (backward compatible)

```bash
python joss/ingest/github_issues.py --max-pages 1
python joss/transform/normalize_joss_submissions.py --in-file github_issues_1234567890.json
```

## Key Tools & Versions

- **Build**: Hatchling | **Dependency manager**: uv | **Linter**: Ruff v0.15.0+
- **Pre-commit**: v6.0.0+ | **Security**: Bandit v1.9.3+ | **Import sorter**: isort 7.0.0+
- **Data validation**: pydantic v2.12.5+ | **Terminal spinners**: progress v1.6+

## Dependencies

- **requests**: HTTP client for GitHub API
- **pydantic**: Data validation and settings management
- **progress**: Terminal spinners for progress indication
- **matplotlib**: Visualization library
- **seaborn**: Statistical data visualization
