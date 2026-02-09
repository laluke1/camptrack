# NOTE: In this application, default users simply have the empty string as
# their password. However, best practice requires the use of password hashing.
# Here, we use standard library facilities to simulate it. However, it would
# be better practice to use a third-party module such as `bcrypt` or `argon2`.
# We do not use them to avoid using additional dependencies.

import hashlib
import secrets
import base64

SHA256_ITERATIONS = 500_000


def password_hash(password: str) -> str:
    salt = secrets.token_bytes(16)
    dkey = hashlib.pbkdf2_hmac(  # Derived key
        'sha256',
        password.encode(),
        salt,
        SHA256_ITERATIONS
    )
    b64_salt = base64.b64encode(salt).decode('ascii')
    b64_dkey = base64.b64encode(dkey).decode('ascii')
    return f'pbkdf2_hmac_sha256${SHA256_ITERATIONS}${b64_salt}${b64_dkey}'


def password_verify(password: str, hashed_password: str) -> bool:
    _algo, iterations, b64_salt, b64_dkey = hashed_password.split('$')
    salt = base64.b64decode(b64_salt)
    dkey = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode(),
        salt,
        int(iterations)
    )
    return secrets.compare_digest(
        base64.b64encode(dkey).decode('ascii'), b64_dkey
    )
