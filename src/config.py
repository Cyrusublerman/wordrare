"""
Configuration management for WordRare system.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
FORMS_DIR = DATA_DIR / "forms"
DATABASE_DIR = BASE_DIR / "databases"
REPORTS_DIR = BASE_DIR / "reports"
LOGS_DIR = BASE_DIR / "logs"

# Create directories if they don't exist
for directory in [RAW_DATA_DIR, PROCESSED_DATA_DIR, FORMS_DIR, DATABASE_DIR, REPORTS_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# API Keys
WORDNIK_API_KEY = os.getenv("WORDNIK_API_KEY", "")
OXFORD_API_KEY = os.getenv("OXFORD_API_KEY", "")
MERRIAM_WEBSTER_API_KEY = os.getenv("MERRIAM_WEBSTER_API_KEY", "")

# Database
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_DIR}/wordrare.db")

# Data sources
PHRONTISTERY_URL = os.getenv("PHRONTISTERY_URL", "http://phrontistery.info/")
CMU_DICT_PATH = RAW_DATA_DIR / "cmudict-0.7b"
NGRAM_DATA_PATH = RAW_DATA_DIR / "ngrams"

# Embedding model
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# Generation defaults
DEFAULT_RARITY_BIAS = float(os.getenv("DEFAULT_RARITY_BIAS", "0.5"))
DEFAULT_FORM = os.getenv("DEFAULT_FORM", "sonnet")
MAX_REPAIR_ITERATIONS = int(os.getenv("MAX_REPAIR_ITERATIONS", "5"))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = LOGS_DIR / "wordrare.log"

# Constraint weights (default)
DEFAULT_CONSTRAINT_WEIGHTS = {
    "rhyme": 0.25,
    "meter": 0.25,
    "semantics": 0.20,
    "affect": 0.15,
    "coherence": 0.10,
    "style": 0.05,
}

# Metric weights
DEFAULT_METRIC_WEIGHTS = {
    "R_rhyme": 0.20,
    "R_meter": 0.20,
    "R_semantic": 0.25,
    "R_depth": 0.15,
    "R_layers": 0.10,
    "R_variation": 0.10,
}


def validate_api_keys(require_wordnik: bool = False,
                      require_oxford: bool = False,
                      require_merriam: bool = False) -> None:
    """
    Validate that required API keys are configured.

    Args:
        require_wordnik: Whether Wordnik API key is required
        require_oxford: Whether Oxford API key is required
        require_merriam: Whether Merriam-Webster API key is required

    Raises:
        ValueError: If required API keys are missing
    """
    missing_keys = []

    if require_wordnik and not WORDNIK_API_KEY:
        missing_keys.append("WORDNIK_API_KEY")

    if require_oxford and not OXFORD_API_KEY:
        missing_keys.append("OXFORD_API_KEY")

    if require_merriam and not MERRIAM_WEBSTER_API_KEY:
        missing_keys.append("MERRIAM_WEBSTER_API_KEY")

    if missing_keys:
        raise ValueError(
            f"Missing required API keys: {', '.join(missing_keys)}. "
            f"Please set these environment variables in your .env file or environment."
        )


def get_configured_apis() -> dict:
    """
    Get information about which APIs are configured.

    Returns:
        Dictionary with API availability status
    """
    return {
        "wordnik": bool(WORDNIK_API_KEY),
        "oxford": bool(OXFORD_API_KEY),
        "merriam_webster": bool(MERRIAM_WEBSTER_API_KEY),
    }
