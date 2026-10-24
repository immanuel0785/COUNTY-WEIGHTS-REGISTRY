import re

def validate_phone_number(phone: str) -> bool:
    """Validates Kenyan phone numbers (e.g., 0722000111 or +254722000111)."""
    clean_phone = phone.strip()
    pattern = r"^(?:254|\+254|0)?(7\d{8}|1\d{8})$"
    return bool(re.match(pattern, clean_phone))

def validate_mpesa_code(code: str) -> bool:
    """Validates M-Pesa transaction codes (e.g., QHX20481)."""
    clean_code = code.strip().upper()
    pattern = r"^[A-Z0-9]{8,12}$"
    return bool(re.match(pattern, clean_code))

def calculate_inspection_fee(pumps: int, scales: int, weights: int) -> float:
    """Calculates official county statutory verification fees."""
    fee = (pumps * 2400) + (scales * 2000) + (weights * 500)
    return float(fee if fee > 0 else 2000)
