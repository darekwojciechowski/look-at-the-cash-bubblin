# Poetry Instructions for Project Setup

Poetry is a dependency management and packaging tool for Python. It helps manage your project's dependencies, virtual environments, and packaging. Follow these steps to get started with Poetry:

## Step 1: Install Poetry

**MacOS** Install Poetry: Use Homebrew to install Poetry by running the following command:

```bash
brew install poetry
```

Alternatively, if you're on **Windows**, you can use:

```bash
pip install poetry
```

## Step 2: Navigate to Project Directory

Navigate to your project directory:

```bash
cd look-at-the-cash-bubblin
```

## Step 3: Install Project Dependencies

Install all dependencies defined in `pyproject.toml`:

```bash
poetry install
```

This will create a virtual environment and install:
- **Core dependencies**: `pandas`, `numpy`
- **Dev dependencies**: `pytest`, `pytest-cov`, `black`, `isort`, `flake8`, `mypy`

## Step 4: Work with the Virtual Environment

You can work with Poetry in two ways:

Run commands with `poetry run`:
```bash
poetry run python main.py
poetry run pytest
```


## Step 5: Run Your Project

Process your transaction data:

```bash
poetry run python main.py
```

## Step 6: Run Tests

Execute the test suite:

```bash
poetry run pytest
```

## Updating dependencies to latest versions

Poetry's built-in `poetry update` respects the version constraints in
`pyproject.toml` (e.g. `^1.0.0`) and will not bump major versions. To upgrade
all dependencies to their **latest available versions** and rewrite the
constraints in `pyproject.toml`, use the `poetry-plugin-up` plugin.

### Install the plugin (one-time)

```bash
poetry self add poetry-plugin-up
```

### Upgrade all dependencies (runtime + dev)

```bash
poetry up --latest
```

### Upgrade only dev dependencies

```bash
poetry up --latest --only dev
```

### Check what is outdated before upgrading

```bash
poetry show --outdated
```

> **Note:** `poetry up --latest` modifies `pyproject.toml` and regenerates
> `poetry.lock`. Review the diff and run `make all` afterwards to confirm
> nothing is broken.

### Alternative: upgrade without the plugin

If you prefer not to install the plugin, pass `@latest` to `poetry add` directly:

```bash
poetry add --group dev \
  pytest@latest \
  pytest-cov@latest \
  pytest-mock@latest \
  pytest-xdist@latest \
  pytest-html@latest \
  pytest-timeout@latest \
  hypothesis@latest \
  black@latest \
  isort@latest \
  flake8@latest \
  mypy@latest \
  ruff@latest \
  pre-commit@latest
```

This rewrites the constraints in `pyproject.toml` and updates `poetry.lock` in
one step, without requiring any plugin.

---

## Common Poetry commands

| Command | Description |
|---|---|
| `poetry add package-name` | Add a runtime dependency |
| `poetry add --group dev package-name` | Add a dev dependency |
| `poetry update` | Update dependencies within existing constraints |
| `poetry up --latest` | Upgrade all deps to latest and rewrite constraints |
| `poetry show` | List installed packages |
| `poetry remove package-name` | Remove a dependency |
| `poetry show --outdated` | List outdated packages |

## Code quality

Run linting with auto-fix and formatting using Ruff:

```bash
poetry run ruff check --fix .
poetry run ruff format --check .
```