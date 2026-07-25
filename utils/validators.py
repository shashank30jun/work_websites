"""Input validation & sanitization utilities for BSGP Platform forms."""
import re
from typing import Tuple, Union

def sanitize_input(text: str, max_length: int = 200) -> str:
    return re.sub(r"[<>{}/\\]", "", str(text or "")).strip()[:max_length]

def validate_phone(phone: str) -> Tuple[bool, str]:
    c = re.sub(r"\D", "", str(phone or ""))
    if len(c) == 10 and c[0] in "6789": return True, c
    if len(c) == 12 and c.startswith("91") and c[2] in "6789": return True, c[2:]
    if len(c) == 11 and c.startswith("0") and c[1] in "6789": return True, c[1:]
    return False, "Invalid phone number. Please enter a valid 10-digit mobile number."

def validate_pincode(pincode: str) -> Tuple[bool, str]:
    c = re.sub(r"\D", "", str(pincode or ""))
    if len(c) == 6 and c[0] != "0": return True, c
    return False, "Pin Code must be a valid 6-digit Indian PIN code (e.g., 249411)."

def validate_email(email: str) -> Tuple[bool, str]:
    e = str(email or "").strip()
    if re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", e): return True, e
    return False, "Invalid email address format."

def validate_cost(cost_val: Union[str, float, int]) -> Tuple[bool, float]:
    try:
        c = float(cost_val)
        return (True, c) if c >= 0 else (False, 0.0)
    except (ValueError, TypeError):
        return False, 0.0

def validate_quantity(qty_val: Union[str, int], min_qty: int = 1, max_qty: int = 500) -> Tuple[bool, int]:
    try:
        q = int(qty_val)
        return (True, q) if min_qty <= q <= max_qty else (False, 0)
    except (ValueError, TypeError):
        return False, 0

def filter_digits_only(val: str, max_len: int) -> str:
    """Strips all non-numeric characters and truncates to max_len."""
    if not val:
        return ""
    digits = re.sub(r"\D", "", str(val))
    return digits[:max_len]
