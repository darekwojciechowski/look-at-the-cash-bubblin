# Pre-commit setup

This guide resolves the `pre-commit not found` error that occurs when
the pre-commit hook points to a virtual environment created outside the
project directory.

## Problem

When attempting a commit, the following error appears:

```
`pre-commit` not found. Did you forget to activate your virtualenv?
```

Poetry creates the virtual environment outside the project directory by default.
The `.git/hooks/pre-commit` hook then references `.venv\Scripts\python.exe`,
which does not exist at that path.

## Solution

Run these commands once to reconfigure Poetry and reinstall the hooks:

```bash
poetry config virtualenvs.in-project true
poetry install
poetry run pre-commit install
```

What each command does:

1. `poetry config virtualenvs.in-project true` — tells Poetry to create `.venv`
   inside the project directory on every `poetry install`.
2. `poetry install` — creates or refreshes the virtual environment at `.venv/`.
3. `poetry run pre-commit install` — rewrites `.git/hooks/pre-commit` with the
   correct Python path.

## Verify the fix

Check that the hook references an existing `python.exe`:

```bash
# macOS / Linux
grep INSTALL_PYTHON .git/hooks/pre-commit

# Windows (PowerShell)
Select-String INSTALL_PYTHON .git\hooks\pre-commit
```

The printed path must point to an existing file.
