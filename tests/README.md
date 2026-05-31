# Test suite

Tests organized into five categories. All configuration lives in
`pytest.ini` at the project root.

## Directory structure

```
tests/
├── conftest.py                 # Shared fixtures for all tests
├── unit/                       # Fast, isolated tests (350 tests)
│   ├── test_category.py
│   ├── test_data_contracts.py  # Inter-stage DataFrame schema contracts
│   ├── test_data_core.py
│   ├── test_data_imports.py
│   ├── test_expense.py
│   ├── test_exporter.py
│   ├── test_location_processor.py
│   ├── test_logging_setup.py
│   ├── test_main.py
│   ├── test_mappings.py
│   └── test_observability.py   # Audit log and structured event tests
├── integration/                # Cross-module and end-to-end tests (11 tests)
│   ├── test_export_integration.py
│   ├── test_large_dataset.py
│   ├── test_main_workflow.py
│   └── test_pipeline_e2e.py
├── performance/                # Benchmarks and scaling tests (9 tests)
│   ├── conftest.py             # Large-DataFrame factory fixture
│   ├── test_clean_descriptions.py
│   ├── test_csv_reading.py
│   ├── test_dataframe_primitives.py
│   ├── test_memory_footprint.py
│   └── test_process_dataframe.py
├── security/                   # Input validation and hardening tests (77 tests)
│   ├── conftest.py
│   ├── test_csv_injection.py
│   ├── test_encoding.py
│   ├── test_export_hardening.py
│   ├── test_input_validation.py
│   ├── test_logging_disclosure.py
│   ├── test_path_traversal.py
│   └── test_resource_exhaustion.py
└── property_based/             # Generative tests using Hypothesis (9 tests)
    ├── strategies.py           # Shared Hypothesis strategies
    ├── test_clean_descriptions.py
    ├── test_pipeline_stateful.py  # Stateful state-machine tests
    └── test_process_dataframe.py
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
| unit | ~350 | Fast | Core logic, individual functions |
| integration | ~11 | Medium | End-to-end workflows, file I/O |
| performance | ~9 | Slow | Benchmarks, scaling tests |
| security | ~77 | Medium | Input validation, injection prevention, I/O hardening |
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
- Coverage threshold (90%) is enforced in CI via
  `.github/workflows/ci.yml` (`coverage report --fail-under=90`)
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
  `{booking_date, value_date, txn_type, amount, currency, description, data, month, year, day}`
  with lowercase merged text, no raw integer columns, month values in [1, 12], and correct year extraction.
- `TestProcessDataframeOutputContract` — `process_dataframe()` must produce
  columns in `[txn_id, day, month, year, amount, category, data]` order, drop income rows,
  keep amount as a string dtype, and never increase row count.
- `TestCleanDescriptionsContract` — `clean_descriptions()` must preserve row
  count and string dtype, and must honour the Open/Closed Principle for custom
  replacement dicts.
- `TestLocationExtractorOutputContract` — `extract_location_from_data()` must
  always return `str`, return `""` for `None`, and not raise on `float("nan")`.

### Stateful pipeline tests

`tests/property_based/test_pipeline_stateful.py` (marker: `property`) uses
`hypothesis.stateful.RuleBasedStateMachine` to verify that any valid sequence
of state transitions through `EMPTY → LOADED → CLEANED → PROCESSED → EMPTY`
satisfies these invariants at every step:

- The buffer is always a `pd.DataFrame`.
- Column names never leave the stage-specific schema:
  - raw stages: `{data, amount, day, month, year}`
  - processed stage: `[txn_id, day, month, year, amount, category, data]`
- Amounts in `PROCESSED` state are non-negative absolute values.

This catches ordering bugs and cross-state corruption that per-function unit
tests miss. Run with `poetry run pytest tests/property_based/test_pipeline_stateful.py`.
