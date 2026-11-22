"""Password hashing.

Passwords are never stored. Only an Argon2 hash of each password is kept,
which cannot be turned back into the password. To check a login, the
password the user typed is hashed again and compared with the stored hash.

Each hash includes its own random salt, so two users with the same password
get different hashes.
"""

from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Return an Argon2 hash of the password, safe to store in the database."""
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Return True if the password matches the stored hash."""
    return password_hash.verify(password, hashed_password)