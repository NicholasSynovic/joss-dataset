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

# Format code (ruff, isort)
ruff format src/
isort src/

# Check for issues (ruff lint, bandit)
ruff check src/
bandit src/
```

### Testing
Currently, the project does not have a test suite. All analysis scripts are in `src/analysis/` and can be verified by:
- Running them manually with appropriate data inputs
- Checking linter/formatter compliance
- Verifying imports and type hints with ruff

## Code Style Guidelines

### Language & Version
- **Python**: 3.13 (as per `pyproject.toml`), compatible with 3.10+
- **Modern Python**: Use `from __future__ import annotations` for forward compatibility

### Imports
- **Order**: Follow isort (Black profile)
  1. Future imports (`from __future__ import annotations`)
  2. Standard library imports
  3. Third-party imports (blank line before)
  4. Local imports (blank line before)
- **Configuration**: `.isort.cfg` enforces Black profile with 79-char line length
- **Style**: Use explicit absolute imports; avoid star imports

Example:
```python
from __future__ import annotations

import json
import logging
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt

from .utils import count_years, load_submissions
```

### Formatting
- **Formatter**: Ruff (replaces Black)
- **Line length**: 88 characters (Ruff/Black standard)
- **Quotes**: Double quotes (`"string"`)
- **Indentation**: 4 spaces
- **Trailing commas**: Respected (magic trailing comma)

### Type Hints
- **Mandatory**: All function parameters and returns must have type hints
- **Style**: Use modern syntax (e.g., `list[T]` instead of `List[T]`)
- **Generics**: Use `dict[str, Any]`, `list[dict[str, Any]]`, etc.
- **Return types**: Always specify, use `-> None` for void functions
- **Union types**: Use `|` operator: `int | str`

Example:
```python
def count_years(
    submissions: list[dict[str, Any]],
    key: str,
    *,
    skip_zero: bool,
) -> Counter[int]:
    """Count occurrences per UTC year."""
```

### Naming Conventions
- **Functions/variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Privates**: Prefix with `_` (e.g., `_internal_helper()`)
- **Logger**: Name as `LOGGER = logging.getLogger(__name__)`

### Documentation
- **Module docstrings**: Required at top of file (after shebang and copyright)
- **Function/method docstrings**: Required for all public functions
- **Format**: Google-style docstrings with Args, Returns, Raises sections
- **Doctest formatting**: Ruff auto-formats code examples in docstrings

Example:
```python
def unix_to_year(ts: int) -> int:
    """
    Convert unix seconds to UTC year.

    Args:
        ts: UNIX timestamp in seconds.

    Returns:
        The UTC year corresponding to the timestamp.

    """
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return int(dt.year)
```

### Error Handling
- **Exceptions**: Raise with explicit error messages (use f-strings or message variables)
- **Type validation**: Check types explicitly before operations
- **Custom messages**: Store in `msg` variable before raising

Example:
```python
data = json.loads(path.read_text(encoding="utf-8"))
if not isinstance(data, list):
    msg = "Expected top-level JSON list of submissions"
    raise RuntimeError(msg)
```

### Shebangs and Headers
- **Shebang**: `#!/usr/bin/env python3` (first line of executable scripts)
- **Copyright**: Include copyright year header
- **License**: Use SPDX identifier in comment (e.g., `# SPDX-License-Identifier: MIT`)

Example:
```python
#!/usr/bin/env python3
# Copyright (c) 2026.
# SPDX-License-Identifier: MIT
```

### Linting Rules (Ruff)
Enabled rule categories include: security (S), type annotations (ANN), naming (N), error handling (E), imports (I), docstrings (D), and many others. Key ignored rules:
- `D203`: Blank line before docstring (conflicts with D211)
- `D212`: Summary after description newline
- `COM812`: Trailing comma conflicts with Black
- `S404`: Use of subprocess (when intentional)

### File Encoding
- **Encoding**: UTF-8 with LF line endings
- **Final newline**: All files must end with newline character
- **Trailing whitespace**: None allowed

## Project Structure

```
src/
  ├── __init__.py
  ├── main.py          # Entry point
  ├── analysis/        # Analysis scripts for JOSS dataset
  ├── ingest/          # Data ingestion modules
  └── transform/       # Data transformation modules
```

## Key Tools & Versions
- **Build**: Hatchling
- **Dependency manager**: uv
- **Linter/Formatter**: Ruff v0.15.0+
- **Pre-commit**: v6.0.0+
- **Security checker**: Bandit v1.9.3+
- **Import sorter**: isort 7.0.0+
