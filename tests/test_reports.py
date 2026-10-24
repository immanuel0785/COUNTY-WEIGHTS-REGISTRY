import pytest
from src.reports import number_to_words_kes

def test_number_to_words_kes():
    res = number_to_words_kes(2400)
    assert "KENYA SHILLINGS" in res
    assert "TWO THOUSAND" in res or "TWENTY" in res or "FOUR HUNDRED" in res
