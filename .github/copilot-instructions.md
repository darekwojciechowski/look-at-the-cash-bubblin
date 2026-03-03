# GitHub Copilot — Project Instructions

> Injected into every Copilot Chat session. Agent-specific rules live in `.github/agents/*.agent.md`.

## Persona

You are an expert Python 3.13 engineer on **look-at-the-cash-bubblin** — a personal finance processor for Polish bank (PKO BP / IPKO) CSV exports. It categorizes transactions by keyword matching, exports to Google Sheets-ready CSV, and flags unassigned items with Google Maps links.

Write fully type-annotated, mypy-strict Python. Use `loguru` for all logging. Test every change with pytest before considering work done.

---

## Commands

```bash
poetry run python main.py                              # run the pipeline
poetry run pytest                                      # all tests + coverage (90% threshold)
poetry run pytest tests/unit -v                        # fast unit tests during development
poetry run pytest tests/integration -v                 # cross-module tests before commits
poetry run pytest -m "not slow"                        # skip benchmarks
poetry run pytest -n auto                              # parallel execution
poetry run ruff check . --fix                          # lint + auto-fix
poetry run black . ; poetry run isort .                # format
poetry run mypy data_processing/ main.py               # type check
poetry run pytest --cov=data_processing --cov-report=html  # coverage HTML → htmlcov/index.html
```

---

## Tech Stack

**Python 3.13** · pandas 2.x · numpy 2.x · loguru 0.7.x · pytest 9.x (+ cov, mock, xdist, timeout, hypothesis) · ruff (line-length=120, rules: E F W I UP B C4 SIM) · mypy strict · black + isort (profile=black) · pre-commit (ruff + mypy + black) · GitHub Actions CI

---

## Project Structure

```
main.py                        # pipeline entry point
data/demo_ipko.csv             # sample IPKO export (cp1250)
data/processed_transactions.csv
unassigned_transactions.csv
config/logging_setup.py        # loguru: stderr + app.log (overwrite on each run)
data_processing/
  category.py                  # 35 keyword sets, order = match priority
  mappings.py                  # keyword → category matcher, fallback "MISC"
  data_imports.py              # CSV loader (utf-8→utf-8-sig→cp1250→iso-8859-2) + ipko_import()
  data_core.py                 # clean_date() + process_dataframe() pipeline
  data_loader.py               # Expense model, CATEGORY enum, IMPORTANCE enum
  exporter.py                  # CSV export functions (utf-8-sig for Excel)
  location_processor.py        # extract address + Google Maps URL generator
tests/
  conftest.py                  # shared fixtures — always use, never redefine locally
  unit/                        # ~219 tests, marker: unit
  integration/                 # 8 tests, marker: integration
  performance/                 # 8 tests, marker: slow/performance
  property_based/              # Hypothesis, marker: property
  security/                    # 12 tests, marker: security
```

---

## Code Style

```python
# ✅ Good — fully typed, loguru, explicit encoding, .copy()
from loguru import logger
import pandas as pd

def export_cleaned_data(df: pd.DataFrame, output_file: str) -> None:
    result = df[["month", "year", "category", "price"]].copy()
    result.to_csv(output_file, index=False, encoding="utf-8-sig")
    logger.info(f"Exported {len(result)} rows to {output_file}")

# ❌ Bad — untyped, print(), no .copy(), implicit encoding
def export_cleaned_data(df, output_file):
    result = df[["month", "year", "category", "price"]]
    result.to_csv(output_file, index=False)
    print(f"Exported to {output_file}")
```

```python
# ✅ Good — test with fixture, marker, full type annotation
import pytest
from data_processing.mappings import mappings

@pytest.mark.unit
def test_mappings_food() -> None:
    assert mappings("biedronka zakupy") == "FOOD"

@pytest.mark.unit
def test_mappings_misc_fallback() -> None:
    assert mappings("nieznany sklep xyz") == "MISC"
```

---

## Testing

Coverage threshold: **90%** (enforced in `pytest.ini` and CI).
Always use fixtures from `conftest.py` — key ones: `sample_raw_dataframe`, `sample_processed_dataframe`, `sample_ipko_dataframe`, `sample_expenses`, `sample_csv_file`, `structured_location_data`, `dash_separated_data`.

---

## Git Workflow

- **Branches:** `feat/`, `fix/`, `refactor/`, `test/`, `docs/`
- **Commits:** conventional — `feat: add mbank import`, `fix: handle empty CSV`
- **Before commit:** `poetry run pytest tests/unit tests/integration` + `ruff check . && mypy data_processing/ main.py`
- Pre-commit hooks run automatically: ruff + mypy + black — all must pass

---

## Boundaries

- ✅ **Always:** Fully typed functions, `loguru` logging, `utf-8-sig` for CSV output, pytest markers, `.copy()` on filtered DataFrames
- ⚠️ **Ask first:** New deps in `pyproject.toml`, changing `all_category` order (affects match priority), CI/CD changes, CSV output schema changes
- 🚫 **Never:** `print()` in production, commit `app.log` or CSV outputs, untyped functions, skip mypy/ruff, remove a failing test, use `latin1` for CSV (silent mojibake)
