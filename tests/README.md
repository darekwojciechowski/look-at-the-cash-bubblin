# Test suite

Tests organized into five categories. All configuration lives in
`pytest.ini` at the project root.

## Directory structure

```
tests/
├── conftest.py           # Shared fixtures for all tests
├── unit/                 # Fast, isolated tests (256 tests)
│   ├── test_category.py
│   ├── test_data_core.py
│   ├── test_data_imports.py
│   ├── test_data_loader.py
│   ├── test_exporter.py
│   ├── test_location_processor.py
│   ├── test_logging_setup.py
│   ├── test_main.py
│   └── test_mappings.py
├── integration/          # Cross-module and end-to-end tests (8 tests)
│   ├── test_integration.py
│   └── test_exporter_import.py
├── performance/          # Benchmarks and scaling tests (8 tests)
│   └── test_performance.py
├── security/             # Input validation tests (12 tests)
│   └── test_security.py
└── property_based/       # Generative tests using Hypothesis (8 tests)
    └── test_property_based.py
```

## Running tests

Run all tests:

```bash
pytest
```

Run a specific category:

```bash
pytest tests/unit
pytest tests/integration
pytest tests/performance
pytest tests/security
pytest tests/property_based
```

Filter by marker:

```bash
pytest -m unit
pytest -m integration
pytest -m security
pytest -m "not slow"
```

Run a single file:

```bash
pytest tests/unit/test_data_core.py
```

Generate an HTML coverage report:

```bash
pytest --cov=data_processing --cov-report=html
```

## Test categories

Counts below are approximate and may drift as tests are added.

| Category | Count | Speed | Purpose |
|---|---|---|---|
| unit | ~256 | Fast | Core logic, individual functions |
| integration | ~8 | Medium | End-to-end workflows, file I/O |
| performance | ~8 | Slow | Benchmarks, scaling tests |
| security | ~12 | Medium | Input validation, injection prevention |
| property_based | ~8 | Medium | Generative testing with Hypothesis |

## Development workflow

1. Run `pytest tests/unit` during active development for fast feedback.
2. Run `pytest tests/unit tests/integration` before every commit.
3. Run `pytest` for a full test run in CI/CD.
4. Run `pytest tests/performance` periodically to catch regressions.

## Configuration

Key settings in `pytest.ini`:

- `testpaths = tests` — limits test discovery to the `tests/` directory
- `--cov-fail-under=90` — enforces a 90% coverage threshold
- `--maxfail=3` — stops the run after three failures
- `--strict-markers` — treats unknown markers as errors
