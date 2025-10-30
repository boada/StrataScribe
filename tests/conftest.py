"""
Test configuration and utilities.
"""
import os
import sys
import pytest
from pathlib import Path

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "data"

# Ensure test data directory exists
TEST_DATA_DIR.mkdir(exist_ok=True)