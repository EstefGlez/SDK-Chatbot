import os
from cryptography.fernet import Fernet

def encrypt_api_key(plain_text: str) -> str:
    """
    Encrypt a plain text API key using Fernet symmetric encryption.
    Returns the encrypted token as a string.
    """
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        raise ValueError("ENCRYPTION_KEY environment variable is not set")
    f = Fernet(key)
    encrypted = f.encrypt(plain_text.encode())
    return encrypted.decode()

def decrypt_api_key(encrypted_text: str) -> str:
    """
    Decrypt an encrypted API key using Fernet symmetric encryption.
    Returns the plain text API key.
    """
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        raise ValueError("ENCRYPTION_KEY environment variable is not set")
    f = Fernet(key)
    decrypted = f.decrypt(encrypted_text.encode())
    return decrypted.decode()