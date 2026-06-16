import pytest

def pytest_configure(config):
    config.addinivalue_line(
        "markers", "golden_test: mark test as golden test, using YAML files."
    )