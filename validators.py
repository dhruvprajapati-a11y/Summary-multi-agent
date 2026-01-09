"""
Utility functions for the multi-agent system
"""
from __future__ import annotations
import re
from typing import Dict, Any, List

def compute_missing(profile: Dict[str, Any], required: List[str], optional: List[str]) -> List[str]:
    """Check which required and optional fields are missing from profile"""
    missing: List[str] = []
    for f in required:
        if not profile.get(f):
            missing.append(f)
    for f in optional:
        if not profile.get(f):
            missing.append(f)
    return missing
