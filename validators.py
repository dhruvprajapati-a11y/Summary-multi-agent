from __future__ import annotations

import re
from typing import Tuple, Dict, Any, List

# Regular expression for basic email validation 
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")

def normalize_name(s: str) -> str: # Normalize to Title Case and single spaces 
    s = re.sub(r"\s+", " ", s.strip())
    return s.title()
 
def normalize_email(s: str) -> str: # Lowercase and remove trailing punctuation 
    s = s.strip().strip(".,;:")  # remove trailing punctuation
    return s.lower()

def normalize_mobile(s: str) -> str: # Keep digits and '+' only 
    s = s.strip()
    s = re.sub(r"[^\d+]", "", s)  # keep digits and '+'
    return s

def normalize_age(s: str) -> str: # Just strip spaces
    return s.strip()

def normalize_city(s: str) -> str: # Normalize to Title Case and single spaces 
    s = re.sub(r"\s+", " ", s.strip())
    return s.title()

def normalize(field: str, value: str) -> str: # Normalize based on field type  
    if field == "name":
        return normalize_name(value)
    if field == "email":
        return normalize_email(value)
    if field == "mobile":
        return normalize_mobile(value)
    if field == "age":
        return normalize_age(value)
    if field == "city":
        return normalize_city(value)
    return value.strip()

def validate(field: str, value: str) -> Tuple[bool, str]: # Validate based on field type 
    v = value.strip()

    if field == "name": # Basic checks for name validity 
        if len(v) < 2:
            return False, "Name is too short."
        if re.fullmatch(r"[\d\W_]+", v):
            return False, "Name can't be only numbers/symbols."
        return True, ""

    if field == "email": # Basic email format check 
        if not EMAIL_RE.search(v):
            return False, "Email looks invalid (example: name@example.com)."
        return True, ""

    if field == "mobile": # Basic mobile number checks
        digits = v.replace("+", "")
        if not digits.isdigit():
            return False, "Mobile must contain digits only."
        if len(digits) < 8 or len(digits) > 15:
            return False, "Mobile length should be 8–15 digits."
        return True, ""

    if field == "age": # Age should be a number between 1 and 120, or 'skip'
        if v.lower() == "skip":
            return True, ""
        if not v.isdigit():
            return False, "Age must be a number (or type 'skip')."
        age = int(v)
        if age < 1 or age > 120:
            return False, "Age should be between 1 and 120."
        return True, ""
 
    if field == "city": # Basic checks for city name 
        if v.lower() == "skip":
            return True, ""
        if len(v) < 2:
            return False, "City is too short."
        return True, ""

    return True, ""

def compute_missing(profile: Dict[str, Any], required: List[str], optional: List[str]) -> List[str]: # Check for missing fields
    missing: List[str] = []
    for f in required:
        if not profile.get(f):
            missing.append(f)
    for f in optional:
        if not profile.get(f):
            missing.append(f)
    return missing
