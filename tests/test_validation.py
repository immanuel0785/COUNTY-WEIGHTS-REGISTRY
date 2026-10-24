import pytest
from src.validation import validate_phone_number, validate_mpesa_code, calculate_inspection_fee

def test_validate_phone_number():
    assert validate_phone_number("0722906936") is True
    assert validate_phone_number("+254722906936") is True
    assert validate_phone_number("12345") is False

def test_validate_mpesa_code():
    assert validate_mpesa_code("QHX20481") is True
    assert validate_mpesa_code("abc") is False

def test_calculate_inspection_fee():
    assert calculate_inspection_fee(1, 0, 0) == 2400
    assert calculate_inspection_fee(0, 1, 1) == 2500
    assert calculate_inspection_fee(0, 0, 0) == 2000 # Minimum fee floor
