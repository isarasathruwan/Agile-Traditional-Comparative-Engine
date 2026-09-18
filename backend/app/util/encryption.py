from __future__ import annotations

from base64 import b64decode, b64encode
from os import urandom

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config.config import settings


class DocumentCipher:
    """Authenticated encryption for document bytes and text persisted by the RAG pipeline."""

    def __init__(self) -> None:
        self._cipher = AESGCM(b64decode(settings.document_encryption_key_base64))

    def encrypt(self, value: bytes, aad: bytes = b"") -> tuple[str, str]:
        nonce = urandom(12)
        ciphertext = self._cipher.encrypt(nonce, value, aad)
        return b64encode(ciphertext).decode("ascii"), b64encode(nonce).decode("ascii")

    def decrypt(self, ciphertext: str, nonce: str, aad: bytes = b"") -> bytes:
        return self._cipher.decrypt(b64decode(nonce), b64decode(ciphertext), aad)

    def encrypt_text(self, value: str, aad: bytes = b"") -> tuple[str, str]:
        return self.encrypt(value.encode("utf-8"), aad)

    def decrypt_text(self, ciphertext: str, nonce: str, aad: bytes = b"") -> str:
        return self.decrypt(ciphertext, nonce, aad).decode("utf-8")
