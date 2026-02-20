# Agent Guidelines for JOSS Dataset Repository

Instructions for agentic coding systems working in this Python project.

## Build, Lint, and Test Commands

### Development Setup

```bash
# Initial setup (installs pre-commit hooks and dependencies via uv)
make create-dev

# Full build (versions, builds distribution, installs package)
make build
```

### Linting and Formatting

Pre-commit hooks enforce code quality. Run manually:

```bash
# Run all pre-commit checks
pre-commit run --all-files

# Run on specific files
pre-commit run ruff-check --files joss/utils.py joss/main.py
pre-commit run ruff-format --files joss/utils.py joss/main.py
pre-commit run isort --files joss/utils.py joss/main.py
pre-commit run bandit --files joss/utils.py joss/main.py
```

### Testing

No test suite exists yet. When tests are added:

```bash
# Run all tests
pytest

# Run a single test file
pytest tests/test_parsers.py

# Run a single test function
pytest tests/test_parsers.py::test_parse_joss_issue

# Run with coverage
pytest --cov=joss --cov-report=term-missing
```

Verify analysis scripts in `joss/analysis/` by running them manually.

## Code Style Guidelines

### Language & Version

- **Python**: 3.13 (as per `pyproject.toml`), compatible with 3.10+

### Imports

- **Order**: isort (Black profile), configured in `.isort.cfg`
- **Line length**: 79 for import wrapping (matches `.isort.cfg`)
- **Style**: Explicit absolute imports; no star imports
- Separate groups with blank lines (stdlib → third-party → local)

### Formatting

- **Formatter**: Ruff (`ruff format` via pre-commit)
- **Line length**: follow Ruff defaults unless project config adds one
- **Quotes**: Double quotes (`"string"`)
- **Indentation**: 4 spaces
- **Trailing commas**: Keep if formatter adds them

### Type Hints

- **Mandatory**: All function parameters and returns must have type hints
- **Style**: Modern syntax (`list[T]` not `List[T]`)
- **Returns**: Always specify, use `-> None` for void functions
- **Unions**: Use `|` operator (e.g., `int | str`)
- **Any**: `typing.Any` allowed only when necessary, use `# noqa: ANN401`

### Naming Conventions

- **Functions/variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Privates**: Prefix with `_` (e.g., `_internal_helper()`)
- **Logger**: Use `LOGGER = logging.getLogger(__name__)` or `JOSSLogger`

### Documentation

- **Module docstrings**: Required at top of file
- **Public functions/methods**: Required docstrings
- **Format**: Google-style with Args, Returns, Raises sections
- Start multi-line docstrings on second line (not same line as quotes)

### Error Handling

- **Exceptions**: Raise with explicit error messages
- **Type validation**: Check types explicitly before operations
- **Message style**: Store in `msg` variable before raising
- **Logging**: Use structured logging (`logger.info("... %s", value)`)

### Data and IO

- **Paths**: Use `pathlib.Path`
- **Encoding**: UTF-8 for file IO (`read_text`/`write_text`)
- **JSON**: Use `json.dumps(..., sort_keys=True)` for stable output

## Linting Rules (Ruff + Bandit)

Enabled: security (S), type annotations (ANN), naming (N), docstrings (D), and
other defaults via Ruff pre-commit hooks.

Ignored rules:
- `D203`: Blank line before docstring (conflicts with D211)
- `D212`: Summary after description newline
- `COM812`: Trailing comma conflicts with Black
- `S404`: Use of subprocess (when intentional)

Bandit runs via pre-commit on `*.py` files.

## File Requirements

- **Encoding**: UTF-8 with LF line endings
- **Final newline**: All files must end with newline
- **Copyright**: Include copyright notice at top of file

## Project Structure

```text
joss/
  ├── __init__.py          # APPLICATION_NAME constant
  ├── main.py              # Entry point with subcommands
  ├── cli.py               # CLI class with parser setup
  ├── logger.py            # Logging utilities
  ├── utils.py             # Shared utility functions
  ├── parsers.py           # Text parsing utilities
  ├── analysis/            # Analysis scripts
  ├── ingest/              # Data ingestion modules
  └── transform/           # Data transformation modules
```

## CLI Usage

```bash
# Ingest GitHub issues (writes SQLite DB)
joss joss --out-file joss.db
```

## Key Tools

- **Build**: Hatchling
- **Dependency manager**: uv
- **Linter/Formatter**: Ruff v0.15.1
- **Pre-commit**: v6.0.0
- **Security**: Bandit v1.9.3
- **Import sorting**: isort 7.0.0
- **Data validation**: pydantic v2.12.5+

## Dependencies

- **requests**: HTTP client for GitHub API
- **pydantic**: Data validation
- **progress**: Terminal spinners
- **matplotlib**: Visualization
- **seaborn**: Statistical visualization
- **ghapi**: GitHub API wrapper
- **sqlalchemy**: Database access
- **pandas**: Dataframe transformations

## Cursor/Copilot Rules

No Cursor rules found in `.cursor/rules/` or `.cursorrules`.
No Copilot instructions found in `.github/copilot-instructions.md`.
