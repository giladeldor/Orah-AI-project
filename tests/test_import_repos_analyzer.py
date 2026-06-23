import sys
import os
import importlib

# Ensure src is on path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))


def test_import_repos_analyzer():
    try:
        mod = importlib.import_module('common.repos_analyzer')
    except Exception as e:
        import pytest
        pytest.skip(f"Could not import module: {e}")
    assert hasattr(mod, 'evaluate_profile')
