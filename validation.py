"""Checks on input values. Each function answers one yes/no question."""
import re
from datetime import date

from policy import MEMBER_TYPES

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_email(value):
    return EMAIL_PATTERN.match(str(value)) is not None


def is_isbn(value):
    digits = str(value).replace("-", "")
    return digits.isdigit() and len(digits) in (10, 13)


def is_iso_date(value):
    try:
        date.fromisoformat(str(value))
        return True
    except ValueError:
        return False


def is_member_type(value):
    return value in MEMBER_TYPES
