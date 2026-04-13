# Test suite

Tests organized into five categories. All configuration lives in
`pytest.ini` at the project root.

## Directory structure

```
tests/
├── conftest.py                 # Shared fixtures for all tests
├── unit/                       # Fast, isolated tests (315 tests)
│   ├── test_category.py
│   ├── test_data_contracts.py  # Inter-stage DataFrame schema contracts
│   ├── test_data_core.py
│   ├── test_data_imports.py
│   ├── test_data_loader.py
│   ├── test_exporter.py
│   ├── test_location_processor.py
│   ├── test_logging_setup.py
│   ├── test_main.py
│   ├── test_mappings.py
│   └── test_observability.py   # Audit log and structured event tests
├── integration/                # Cross-module and end-to-end tests (9 tests)
│   ├── test_integration.py
│   └── test_exporter_import.py
├── performance/                # Benchmarks and scaling tests (8 tests)
│   └── test_performance.py
├── security/                   # Input validation tests (12 tests)
│   └── test_security.py
└── property_based/             # Generative tests using Hypothesis (9 tests)
    ├── test_property_based.py
    └── test_stateful_pipeline.py  # Stateful state-machine tests
```

## Running tests

Run all tests:

```bash
poetry run pytest
```

Run a specific category:

```bash
poetry run pytest tests/unit
poetry run pytest tests/integration
poetry run pytest tests/performance
poetry run pytest tests/security
poetry run pytest tests/property_based
```

Filter by marker:

```bash
poetry run pytest -m unit
poetry run pytest -m integration
poetry run pytest -m security
poetry run pytest -m "not slow"
```

Run a single file:

```bash
poetry run pytest tests/unit/test_data_core.py
```

Generate an HTML coverage report:

```bash
poetry run pytest --cov=data_processing --cov-report=html
```

## Test categories

Counts below are approximate and may drift as tests are added.

| Category | Count | Speed | Purpose |
|---|---|---|---|
| unit | ~315 | Fast | Core logic, individual functions |
| integration | ~9 | Medium | End-to-end workflows, file I/O |
| performance | ~8 | Slow | Benchmarks, scaling tests |
| security | ~12 | Medium | Input validation, injection prevention |
| property_based | ~9 | Medium | Generative testing with Hypothesis |

## Development workflow

1. Run `poetry run pytest tests/unit` during active development for fast feedback.
2. Run `poetry run pytest tests/unit tests/integration` before every commit.
3. Run `poetry run pytest` for a full test run in CI/CD.
4. Run `poetry run pytest tests/performance` periodically to catch regressions.

## Configuration

Key settings in `pytest.ini`:

- `testpaths = tests` — limits test discovery to the `tests/` directory
- `--cov=config,data_processing,main` — measures coverage across all source modules
- `--cov-report=html,json` — writes an HTML report to `htmlcov/` and a
  machine-readable JSON report to `coverage.json`
- `--cov-fail-under=90` — enforces a 90% coverage threshold
- `--maxfail=3` — stops the run after three failures
- `--strict-markers` — treats unknown markers as errors
- `--strict-config` — treats unknown `pytest.ini` keys as errors
- `log_cli = true` — streams live log output during the run

Available markers: `unit`, `integration`, `slow`, `security`, `performance`,
`property`, `contract`

### Data contract tests

`tests/unit/test_data_contracts.py` (markers: `unit`, `contract`) validates the
DataFrame schema that each pipeline stage promises to the next. Four contracts
are defined:

- `TestIpkoImportOutputContract` — `ipko_import()` must produce exactly
  `{price, data, month, year}` with lowercase text, no raw integer columns,
  month values in [1, 12], and correct year extraction.
- `TestProcessDataframeOutputContract` — `process_dataframe()` must produce
  columns in `[month, year, price, category, data]` order, drop income rows,
  keep price as a string dtype, and never increase row count.
- `TestCleanDescriptionsContract` — `clean_descriptions()` must preserve row
  count and string dtype, and must honour the Open/Closed Principle for custom
  replacement dicts.
- `TestLocationExtractorOutputContract` — `extract_location_from_data()` must
  always return `str`, return `""` for `None`, and not raise on `float("nan")`.

### Stateful pipeline tests

`tests/property_based/test_stateful_pipeline.py` (marker: `property`) uses
`hypothesis.stateful.RuleBasedStateMachine` to verify that any valid sequence
of state transitions through `EMPTY → LOADED → CLEANED → PROCESSED → EMPTY`
satisfies these invariants at every step:

- The buffer is always a `pd.DataFrame`.
- Column names never leave the set `{data, price, month, year, category}`.
- Prices in `PROCESSED` state are non-negative absolute values.

This catches ordering bugs and cross-state corruption that per-function unit
tests miss. Run with `poetry run pytest tests/property_based/test_stateful_pipeline.py`.
