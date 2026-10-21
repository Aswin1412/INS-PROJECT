"""
crypto_utils.py — Password-based file encryption / decryption.

Uses PBKDF2-HMAC-SHA256 to derive a Fernet key from a user-supplied
password.  A random 16-byte salt is generated per encryption and
stored as the first 16 bytes of the output file so that decryption
only requires the original password.

Encrypted file layout:
    [ 16-byte salt ][ Fernet ciphertext ... ]

Security notes:
    • PBKDF2 with 480 000 iterations (OWASP 2023 recommendation).
    • Fernet provides AES-128-CBC encryption + HMAC-SHA256 authentication.
    • Each file gets a unique random salt, so identical files encrypted
      with the same password produce different ciphertext.
"""

from __future__ import annotations

import base64
import os

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

# OWASP-recommended minimum iterations for PBKDF2-HMAC-SHA256 (2023).
_KDF_ITERATIONS = 480_000
_SALT_LENGTH = 16  # bytes


# -------------------------------------------------------------------
# Internal helpers
# -------------------------------------------------------------------

def _derive_key(password: str, salt: bytes) -> bytes:
    """Derive a Fernet-compatible key from a password and salt.

    Args:
        password: The user's plaintext password.
        salt: A 16-byte random salt.

    Returns:
        A URL-safe base64-encoded 32-byte key suitable for Fernet.
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=_KDF_ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))


# -------------------------------------------------------------------
# Public API
# -------------------------------------------------------------------

def encrypt_file(source_path: str, password: str) -> str:
    """Encrypt a file with a password.

    The encrypted output is saved as ``<source_path>.enc`` in the same
    directory.  The original file is **not** modified or deleted.

    Args:
        source_path: Path to the plaintext file.
        password: The encryption password chosen by the user.

    Returns:
        The path of the newly created ``.enc`` file.

    Raises:
        FileNotFoundError: If *source_path* does not exist.
        PermissionError: If read/write access is denied.
    """
    salt = os.urandom(_SALT_LENGTH)
    key = _derive_key(password, salt)
    fernet = Fernet(key)

    with open(source_path, "rb") as f:
        plaintext = f.read()

    ciphertext = fernet.encrypt(plaintext)

    encrypted_path = source_path + ".locked"
    with open(encrypted_path, "wb") as f:
        f.write(salt + ciphertext)  # salt is first 16 bytes

    return encrypted_path


def decrypt_file(encrypted_path: str, password: str) -> str:
    """Decrypt a ``.enc`` file using the original password.

    The restored file is saved alongside the encrypted one with the
    ``.enc`` extension stripped.

    Args:
        encrypted_path: Path to the ``.enc`` file.
        password: The password that was used during encryption.

    Returns:
        The path of the restored plaintext file.

    Raises:
        FileNotFoundError: If *encrypted_path* does not exist.
        PermissionError: If read/write access is denied.
        InvalidToken: If the password is wrong or the data is corrupted.
    """
    with open(encrypted_path, "rb") as f:
        raw = f.read()

    if len(raw) < _SALT_LENGTH:
        raise InvalidToken  # file is too small to be valid

    salt = raw[:_SALT_LENGTH]
    ciphertext = raw[_SALT_LENGTH:]

    key = _derive_key(password, salt)
    fernet = Fernet(key)

    plaintext = fernet.decrypt(ciphertext)  # raises InvalidToken on bad pw

    if encrypted_path.endswith(".locked"):
        decrypted_path = encrypted_path[:-7]
    else:
        decrypted_path = encrypted_path + ".dec"

    with open(decrypted_path, "wb") as f:
        f.write(plaintext)

    return decrypted_path
