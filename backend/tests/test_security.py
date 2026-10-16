from datetime import datetime, timezone
import pytest
from middleware.security import hash_password, verify_password, create_access_token, decode_access_token

def test_password_hash_round_trip():
    hashed = hash_password("StrongPass123")
    assert hashed != "StrongPass123"
    assert verify_password("StrongPass123", hashed)
    assert not verify_password("WrongPass123", hashed)

def test_jwt_contains_expected_claims():
    token = create_access_token("0123456789abcdef01234567", "employee", 0)
    payload = decode_access_token(token)
    assert payload["sub"] == "0123456789abcdef01234567"
    assert payload["role"] == "employee"
    assert payload["ver"] == 0
