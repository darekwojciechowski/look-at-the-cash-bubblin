# Test organization

This test suite follows pytest best practices with a hierarchical structure
for better organization and selective test execution.

## Directory structure

```
tests/
├── conftest.py              # Shared fixtures for all tests
├── unit/                    # Unit tests - fast, isolated, no external dependencies
│   ├── test_category.py
│   ├── test_data_core.py
│   ├── test_data_imports.py
│   ├── test_data_loader.py
│   ├── test_exporter.py
│   ├── test_location_processor.py
│   ├── test_logging_setup.py
│   ├── test_main.py
│   └── test_mappings.py
├── integration/             # Integration tests - component interaction and end-to-end
│   ├── test_integration.py
│   └── test_exporter_import.py
├── performance/             # Performance and load testing
│   └── test_performance.py
├── security/                # Security validation tests
│   └── test_security.py
└── property_based/          # Property-based tests using Hypothesis
    └── test_property_based.py
```

## Running tests

### All tests

```bash
pytest
```

### By category

```bash
# Unit tests only (fast - 224 tests)
pytest tests/unit

# Integration tests (8 tests)
pytest tests/integration

# Performance tests (slow - 8 tests)
pytest tests/performance

# Security tests (12 tests)
pytest tests/security

# Property-based tests (requires hypothesis)
pytest tests/property_based
```

### By marker

```bash
# Unit tests
pytest -m unit

# Integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"

# Security tests only
pytest -m security
```

### Specific test file

```bash
pytest tests/unit/test_data_core.py
```

### With coverage report

```bash
pytest --cov=data_processing --cov-report=html
```

## Test categories

| Category | Count | Speed | Purpose |
|---|---|---|---|
| unit | 224 | Fast | Core logic, individual functions |
| integration | 8 | Medium | End-to-end workflows, file I/O |
| performance | 8 | Slow | Benchmarks, scaling tests |
| security | 12 | Medium | Input validation, injection prevention |
| property_based | 8 | Medium | Generative testing with Hypothesis |

## Development workflow

1. **During development**: Run `pytest tests/unit` for quick feedback.
2. **Before commit**: Run `pytest tests/unit tests/integration`.
3. **CI/CD**: Run all tests with `pytest`.
4. **Performance check**: Run `pytest tests/performance` periodically.

## Configuration

Test configuration is in `pytest.ini` at the project root. Key settings:

- Test discovery: `testpaths = tests`
- Coverage target: `--cov-fail-under=90`
- Markers defined for categorization
