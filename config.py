from __future__ import annotations
import os

# ==========================================
# CONFIGURATION - Now loaded from agent_config.py
# ==========================================
# This file provides backward compatibility
# All settings are now configurable in agent_config.py

try:
    from agent_config import (
        REQUIRED_FIELDS as _REQUIRED_FIELDS,
        OPTIONAL_FIELDS as _OPTIONAL_FIELDS,
        MAX_ATTEMPTS_PER_FIELD as _MAX_ATTEMPTS,
        AIRTABLE_FIELD_MAPPING,
    )
    REQUIRED_FIELDS = _REQUIRED_FIELDS
    OPTIONAL_FIELDS = _OPTIONAL_FIELDS
    MAX_ATTEMPTS_PER_FIELD = _MAX_ATTEMPTS
except ImportError:
    # Fallback defaults
    REQUIRED_FIELDS = ["name", "email", "mobile"]
    OPTIONAL_FIELDS = ["age", "city"]
    MAX_ATTEMPTS_PER_FIELD = 3
    AIRTABLE_FIELD_MAPPING = {
        "name": "Name",
        "email": "Email",
        "mobile": "Mobile",
        "age": "Age",
        "city": "City",
        "summary": "Summary",
    }

# If user types "skip" for optional fields 
ALLOW_SKIP_OPTIONAL = True

# If user refuses required fields, go to handoff state
REQUIRED_REFUSAL_TO_HANDOFF = True

# SQLite checkpoint DB path
CHECKPOINT_DB_PATH = "checkpoints.sqlite3"

# ==========================================
# AIRTABLE CONFIGURATION (from environment)
# ==========================================
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME", "Leads")
