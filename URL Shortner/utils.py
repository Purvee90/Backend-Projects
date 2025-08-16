from sqlalchemy.orm import Session
from models import URL
import random, string


def generate_short_code(length=6, prefix=""):
    code = "".join(random.choices(string.ascii_letters + string.digits, k=length))
    return prefix + code


def generate_unique_short_code(db: Session, length=6):
    while True:
        code = generate_short_code(length)
        if not db.query(URL).filter(URL.short_code == code).first():
            return code


def validate_custom_code(code: str) -> bool:
    """Validate custom short code format."""
    if not code or len(code) < 4:
        return False
    # Only allow alphanumeric characters
    return code.isalnum()
