"""
Input validation utilities
"""

import re


def validate_phone(phone: str):
    cleaned = re.sub(r'\D', '', phone)
    if len(cleaned) == 10 and cleaned[0] in '6789':
        return True, cleaned
    if len(cleaned) == 12 and cleaned.startswith('91'):
        return True, cleaned[2:]
    if len(cleaned) == 11 and cleaned.startswith('0'):
        return True, cleaned[1:]
    return False, "Invalid phone number. Please enter a valid 10-digit Indian number."


def validate_email(email: str):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return True, email
    return False, "Invalid email address."


def validate_cost(cost_str: str):
    try:
        cost = float(cost_str)
        if cost < 0:
            return False, 0.0
        return True, cost
    except ValueError:
        return False, 0.0


def validate_quantity(qty_str: str):
    try:
        qty = int(qty_str)
        if qty < 1 or qty > 100:
            return False, 0
        return True, qty
    except ValueError:
        return False, 0


def sanitize_input(text: str, max_length: int = 200):
    if not text:
        return ""
    cleaned = re.sub(r'[<>{}/\\]', '', text)
    return cleaned.strip()[:max_length]
