# GitHub Copilot — Project Instructions

> Automatically injected into every Copilot Chat session and all custom agents (`@commit`, `@docs`, `@python-testing-patterns`, etc.).
> Do NOT duplicate behavioral rules here — those live in `.github/agents/*.agent.md`.

---

## Project Identity

**Name:** look-at-the-cash-bubblin
**Purpose:** Personal finance transaction processor for Polish bank (PKO/IPKO) CSV exports.
Parses raw bank CSV → categorizes transactions by keyword matching → exports to Google Sheets-ready CSV and flags unassigned transactions with Google Maps search links.
Named after Anderson .Paak's "Bubblin'" 💰

**Python version:** 3.13 (strict — `pyproject.toml` enforces `^3.13`)
**Package manager:** Poetry (`pyproject.toml`) + `requirements.txt` for pip fallback

---

## Tech Stack

| Layer | Tool | Notes |
|---|---|---|
| Language | Python 3.13 | |
| Data processing | pandas 2.x, numpy 2.x | |
| Logging | loguru 0.7.x | never use `print()` in production code |
| Tests | pytest 9.x | + pytest-cov, pytest-mock, pytest-xdist, pytest-timeout, hypothesis |
| Linting | ruff | line-length=120; rules: E, F, W, I, UP, B, C4, SIM |
| Type checking | mypy | **strict mode** — all functions must be fully typed |
| Formatting | black + isort | isort profile=black |
| Pre-commit | pre-commit hooks | ruff + mypy + black |
| CI/CD | GitHub Actions | 3 stages: code quality → parallel tests → coverage |

---

## Repository Structure

```
look-at-the-cash-bubblin/
├── main.py                          # entry point — orchestrates full pipeline
├── pyproject.toml                   # Poetry config, ruff, mypy, isort settings
├── pytest.ini                       # test config, coverage thresholds (90%)
├── requirements.txt                 # pinned runtime deps for pip
├── app.log                          # overwritten on every run
├── unassigned_transactions.csv      # output: MISC transactions + Maps links
│
├── data/
│   ├── demo_ipko.csv                # sample IPKO bank export (cp1250 encoding)
│   └── processed_transactions.csv  # output: cleaned categorized transactions
│
├── config/
│   ├── __init__.py
│   └── logging_setup.py            # loguru: stderr (color) + app.log (overwrite)
│
├── data_processing/
│   ├── __init__.py
│   ├── category.py                  # 35 keyword sets for transaction categorization
│   ├── mappings.py                  # keyword → category name matcher
│   ├── data_imports.py              # CSV loader + IPKO column normalizer
│   ├── data_core.py                 # description cleaner + full processing pipeline
│   ├── data_loader.py               # Expense model, CATEGORY enum, IMPORTANCE enum
│   ├── exporter.py                  # all CSV export functions
│   └── location_processor.py        # extract address + Google Maps URL generator
│
├── tests/
│   ├── conftest.py                  # all shared fixtures
│   ├── unit/                        # 9 files, ~219 tests — one file per module
│   ├── integration/                 # 2 files, 8 tests — cross-module pipeline
│   ├── performance/                 # 1 file, 8 tests — benchmarks (marked slow)
│   ├── property_based/              # 1 file — Hypothesis property tests
│   └── security/                    # 1 file, 12 tests — input validation
│
└── .github/
    ├── copilot-instructions.md      # ← this file
    ├── agents/                      # custom Copilot agents
    └── workflows/ci.yml             # GitHub Actions pipeline
```

---

## Architecture & Data Flow

```
data/demo_ipko.csv  (cp1250)
        │
        ▼
read_transaction_csv()        # tries utf-8 → utf-8-sig → cp1250 → iso-8859-2
        │
        ▼
ipko_import()                 # normalize 9-column IPKO format
                              # concat: type // description // unnamed_6 // unnamed_8 // data
                              # extract month + year from transaction_date
        │
        ▼
process_dataframe()
  ├── clean_date()             # replace verbose phrases, expand brand names
  └── df["category"] = mappings(data)   # keyword substring match → category name
                                         # uses category.py sets, first match wins
        │
        ▼
export_misc_transactions()    # MISC rows → extract_location + Maps link → unassigned_transactions.csv
        │
        ▼
export_cleaned_data()         # columns: [month, year, category, price] → processed_transactions.csv
```

### Dependency Graph

```
main.py
  ├── config.logging_setup
  ├── data_processing.data_imports   (read_transaction_csv, ipko_import)
  ├── data_processing.data_core      (clean_date, process_dataframe)
  │     └── data_processing.mappings
  │           └── data_processing.category
  └── data_processing.exporter
        ├── data_processing.data_loader    (Expense, CATEGORY, IMPORTANCE)
        └── data_processing.location_processor
```

---

## Module Reference

### `data_processing/category.py`
- `all_category: list[str]` — ordered list of all 35 category names; **order = match priority**
- One `set[str]` per category: keywords are lowercase substrings matched against transaction `data`
- `MISC: set[str] = set()` — always empty, used as catch-all default
- Excluded from ruff E501 (long lines are intentional)
- **35 categories:** `REMOVE_ENTRY`, `FOOD`, `GREENFOOD`, `TRANSPORTATION`, `CAR`, `LEASING`, `FUEL`, `REPAIRS`, `COFFEE`, `FASTFOOD`, `GROCERIES`, `CATERING`, `ALCOHOL`, `APARTMENT`, `BILLS`, `RENOVATION`, `CLOTHES`, `JEWELRY`, `ENTERTAINMENT`, `PCGAMES`, `BIKE`, `SPORT`, `PHARMACY`, `COSMETICS`, `TRAVEL`, `BOOKS`, `ANIMALS`, `INSURANCE`, `SUBSCRIPTIONS`, `INVESTMENTS`, `SELF_DEVELOPMENT`, `ELECTRONIC`, `SELF_CARE`, `KIDS`, `SHOPPING`, `MISC`

### `data_processing/mappings.py`
- `mappings(data: str) -> str` — iterates `all_category`, returns first category whose keyword set has any substring match in `data.lower()`, fallback `"MISC"`
- Has doctests: `mappings("biedronka groceries")` → `'FOOD'`

### `data_processing/data_core.py`
- `clean_date(df)` — string replacement dict: Polish IPKO phrases → short labels, brand expansions, location tags
- `process_dataframe(df)` — pipeline: clean → categorize → drop `REMOVE_ENTRY` → drop positive prices (income) → strip `-` from price → reorder to `["month", "year", "price", "category", "data"]` → drop `"nan"` prices

### `data_processing/data_imports.py`
- IPKO CSV: 9 columns (0–8), no header, cp1250 encoding by default
- `read_transaction_csv(file_path, encoding)` — encoding fallback chain: utf-8 → utf-8-sig → cp1250 → iso-8859-2 (avoids latin1 silent mojibake)
- `ipko_import(df)` — lowercases all text columns, builds unified `data` column

### `data_processing/data_loader.py`
- `Expense(month, year, item, price)` — auto-assigns `CATEGORY` + `IMPORTANCE` via keyword match on `item.lower()`
- `CATEGORY` enum — values are display strings with emoji
- `IMPORTANCE` enum — `ESSENTIAL` > `HAVE_TO_HAVE` > `NICE_TO_HAVE` > `SHOULDNT_HAVE` > `NEEDS_REVIEW`
- `__repr__` format: `"month,year,item,category_value,price,importance_value"`

### `data_processing/exporter.py`
- `export_cleaned_data(df, output_file)` — columns `["month", "year", "category", "price"]`, utf-8-sig
- `export_misc_transactions(df)` — filters `category` contains `"MISC"` → calls `export_unassigned_transactions_to_csv`
- `export_unassigned_transactions_to_csv(df)` — adds `extracted_location` + `google_maps_link` columns, utf-8-sig
- `get_data()` — reads `data/processed_transactions.csv` → `list[Expense]`
- All CSV outputs use `utf-8-sig` (BOM) — required for Windows Excel

### `data_processing/location_processor.py`
- Handles Polish, Spanish, Italian address formats
- `extract_location_from_data(data_string)` — priority: structured `lokalizacja:` block → dash pattern (`DESC - ADDRESS`) → address heuristic → any non-generic text
- `create_google_maps_link(location)` — validates (needs street indicator OR comma+number/city), URL-encodes, returns `https://www.google.com/maps/search/...` or `""`
- `normalize_polish_names(location)` — ASCII → Unicode diacritics (`lodz` → `łódź`, `krakow` → `kraków`)
- `clean_location_text(location)` — strips Polish metadata prefixes (`"miasto :"`, `"adres:"`, etc.)

### `config/logging_setup.py`
- `setup_logging()` — removes loguru default handler, sets up console (stderr, INFO, color) + file (`app.log`, INFO, mode=`"w"`)
- `app.log` is **overwritten** on each run — not appended

---

## File I/O Summary

| File | Direction | Encoding | Purpose |
|---|---|---|---|
| `data/demo_ipko.csv` | input | cp1250 | Raw IPKO bank export |
| `data/processed_transactions.csv` | output | utf-8-sig | Cleaned, categorized transactions |
| `unassigned_transactions.csv` | output | utf-8-sig | MISC rows + Google Maps links |
| `for_google_spreadsheet.csv` | output | utf-8-sig | Google Sheets import |
| `app.log` | output | utf-8 | Run log (overwritten each run) |

---

## Running the App

```bash
# activate venv (Poetry)
poetry shell
# or
.venv\Scripts\Activate.ps1   # Windows PowerShell

# install deps
poetry install
# or
pip install -r requirements.txt

# run pipeline
python main.py
```

---

## Running Tests

```bash
# all tests with coverage (default — configured in pytest.ini)
pytest

# by category
pytest tests/unit                    # fast, run during development
pytest tests/integration             # cross-module, run before commits
pytest tests/performance             # slow benchmarks
pytest tests/security                # input validation
pytest tests/property_based          # Hypothesis property tests

# skip slow tests
pytest -m "not slow"

# parallel execution
pytest -n auto

# coverage HTML report only
pytest --cov=data_processing --cov-report=html
# → opens htmlcov/index.html
```

**Coverage threshold: 90%** — enforced in `pytest.ini` (`--cov-fail-under=90`) and CI.

---

## Test Architecture

```
tests/
├── conftest.py       # shared fixtures — use these, do not redefine locally
├── unit/             # 9 files, ~219 tests
├── integration/      # 2 files, 8 tests
├── performance/      # 1 file, 8 tests  (marker: slow)
├── property_based/   # 1 file           (marker: property, uses hypothesis)
└── security/         # 1 file, 12 tests (marker: security)
```

**Available pytest markers:** `unit`, `integration`, `slow`, `security`, `performance`, `property`, `smoke`, `regression`

**Key fixtures in `conftest.py`:**

| Fixture | Type | Description |
|---|---|---|
| `sample_raw_dataframe` | `pd.DataFrame` | 5-row raw transaction DF |
| `sample_processed_dataframe` | `pd.DataFrame` | 4-row final output DF |
| `sample_ipko_dataframe` | `pd.DataFrame` | Raw IPKO format (int column names 0–8) |
| `expected_cleaned_data` | `pd.DataFrame` | Expected after `clean_date()` |
| `sample_expenses` | `list[Expense]` | 3 Expense objects |
| `structured_location_data` | `list[str]` | `lokalizacja: adres: ... miasto: ...` strings |
| `dash_separated_data` | `list[str]` | `DESC - ADDRESS` format strings |
| `sample_csv_file` | `Path` | Temp CSV file in `tmp_path` |
| `test_data_dir` | `Path` | `tmp_path / "test_data"` |

---

## Code Conventions

- **Type hints everywhere** — mypy strict; no untyped functions, no `Any` without justification
- **Line length:** 120 chars (ruff + black); `category.py` exempt from E501
- **Import order:** isort black profile; first-party: `data_processing`, `config`
- **Logging:** `loguru` only — `logger.info/warning/error`; never `print()` in production
- **pandas:** avoid chained assignment; use `.copy()` when mutating filtered DataFrames
- **Encodings:** always explicit; CSV outputs use `utf-8-sig` for Windows Excel compatibility
- **Tests:** use fixtures from `conftest.py`; `pytest-mock` for mocking; mark tests with appropriate markers

---

## How to Extend

### Add a new transaction category
1. Add name to `all_category` list in [data_processing/category.py](data_processing/category.py) — position = match priority
2. Add `MY_CATEGORY: set[str] = {"keyword1", "keyword2"}` in the same file
3. To map it to `CATEGORY`/`IMPORTANCE` for `Expense`, update `_determine_category_and_importance()` in [data_processing/data_loader.py](data_processing/data_loader.py)

### Add a new bank format
1. Add import function in [data_processing/data_imports.py](data_processing/data_imports.py) following `ipko_import()` pattern
2. Output must be a DataFrame with columns: `transaction_date`, `price`, `data`, `month`, `year`
3. Wire it up in `main.py`

---

## Supported Banks

| Bank | Format | Encoding | Import Function |
|---|---|---|---|
| PKO BP | IPKO CSV export (9 columns, no header) | cp1250 | `ipko_import()` |
