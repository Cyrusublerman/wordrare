"""
Pytest configuration and fixtures.
"""

import pytest
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


@pytest.fixture(scope="session")
def project_root():
    """Get project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def data_dir(project_root):
    """Get data directory."""
    return project_root / "data"


@pytest.fixture(scope="session")
def forms_dir(data_dir):
    """Get forms directory."""
    return data_dir / "forms"
