"""
Хэширование паролей для домена "пользователь".

Сама аутентификация (проверка логина/пароля при входе) в этой
лабораторной — заглушка (реализуется в лаб. №4), но регистрация —
реальный метод, поэтому пароль в БД в открытом виде хранить нельзя.
Используем PBKDF2-HMAC-SHA256 из стандартной библиотеки, чтобы не
тянуть дополнительную зависимость вроде passlib/bcrypt.
"""

import hashlib
import hmac
import os

_ITERATIONS = 100_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERATIONS)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt_hex, digest_hex = stored_hash.split("$", 1)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
    except ValueError:
        return False

    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERATIONS)
    return hmac.compare_digest(actual, expected)
