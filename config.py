from __future__ import annotations

# Field priority
REQUIRED_FIELDS = ["name", "email", "mobile"]
OPTIONAL_FIELDS = ["age", "city"]

# Validation behavior means how many times to retry per field before giving up
MAX_ATTEMPTS_PER_FIELD = 3

# If user types "skip" for optional fields 
ALLOW_SKIP_OPTIONAL = True

# If user refuses required fields, go to handoff state
REQUIRED_REFUSAL_TO_HANDOFF = True

# SQLite checkpoint DB path
CHECKPOINT_DB_PATH = "checkpoints.sqlite3"
