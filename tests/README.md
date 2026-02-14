# Test Organization

This test suite follows pytest best practices with a hierarchical structure for better organization and selective test execution.

## Directory Structure

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
├── integration/             # Integration tests - component interaction & end-to-end
│   ├── test_integration.py
│   └── test_exporter_import.py
├── performance/             # Performance and load testing
│   └── test_performance.py
├── security/                # Security validation tests
│   └── test_security.py
└── property_based/          # Property-based tests using Hypothesis
    └── test_property_based.py
```

## Running Tests

### All tests
```bash
pytest
```

### By category (recommended for faster feedback)
```bash
# Unit tests only (fast - 219 tests)
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

### By marker (alternative approach)
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

## Test Categories

| Category | Count | Speed | Purpose |
|----------|-------|-------|---------|
| **unit** | 219 | Fast | Core logic, individual functions |
| **integration** | 8 | Medium | End-to-end workflows, file I/O |
| **performance** | 8 | Slow | Benchmarks, scaling tests |
| **security** | 12 | Medium | Input validation, injection prevention |
| **property_based** | 1 | Medium | Generative testing with Hypothesis |

## Benefits of This Structure

✅ **Clear organization** - Test type immediately visible
✅ **Selective execution** - Run only relevant tests during development
✅ **Better scalability** - Easy to add new tests to appropriate category
✅ **Standard practice** - Follows Python/pytest community conventions
✅ **Faster feedback** - Run unit tests (219) separately from slow tests (8)

## Development Workflow

1. **During development**: Run `pytest tests/unit` for quick feedback
2. **Before commit**: Run `pytest tests/unit tests/integration`
3. **CI/CD**: Run all tests with `pytest`
4. **Performance check**: Run `pytest tests/performance` periodically

## Configuration

Test configuration is in `pytest.ini` at the project root. Key settings:
- Test discovery: `testpaths = tests`
- Coverage targets: `--cov-fail-under=90`
- Markers defined for categorization
