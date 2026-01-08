"""
Pytest configuration and fixtures for Skyy Facial Recognition tests.
"""

import pytest
import sys
from pathlib import Path

# Add src directory to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture
def test_data_dir():
    """Return path to test data directory."""
    return Path(__file__).parent / "test_data"


@pytest.fixture
def sample_image_path(test_data_dir):
    """Return path to a sample test image."""
    return test_data_dir / "sample_face.jpg"


@pytest.fixture
def temp_database(tmp_path):
    """Create a temporary database directory for testing."""
    db_path = tmp_path / "test_db"
    db_path.mkdir(parents=True, exist_ok=True)
    return db_path
