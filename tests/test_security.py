"""Tests for password hashing."""

from __future__ import annotations

import pytest

from food_processing_system.security import hash_password, verify_password


def test_hash_is_not_plaintext() -> None:
    hashed = hash_password("s3cret")
    assert "s3cret" not in hashed
    assert hashed.startswith("pbkdf2_sha256$")


def test_hashes_are_salted_and_unique() -> None:
    assert hash_password("same") != hash_password("same")


def test_verify_accepts_correct_password() -> None:
    hashed = hash_password("correct horse")
    assert verify_password("correct horse", hashed) is True


def test_verify_rejects_wrong_password() -> None:
    hashed = hash_password("correct horse")
    assert verify_password("battery staple", hashed) is False


def test_verify_rejects_malformed_hash() -> None:
    assert verify_password("anything", "not-a-valid-hash") is False


def test_empty_password_is_rejected() -> None:
    with pytest.raises(ValueError):
        hash_password("")
