from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
from flask import current_app


class MessageCrypto:
    """Handles encryption and decryption of messages using Fernet symmetric encryption"""
    
    @staticmethod
    def _get_key():
        """Generate or retrieve encryption key from app config"""
        secret_key = current_app.config['SECRET_KEY'].encode()
        salt = b'stable_salt_for_messages'  # In production, use a random salt per user
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(secret_key))
        return Fernet(key)
    
    @staticmethod
    def encrypt_message(plaintext: str) -> str:
        """Encrypt a message and return base64 encoded ciphertext"""
        if not plaintext:
            return ''
        
        fernet = MessageCrypto._get_key()
        encrypted = fernet.encrypt(plaintext.encode('utf-8'))
        return base64.urlsafe_b64encode(encrypted).decode('utf-8')
    
    @staticmethod
    def decrypt_message(ciphertext: str) -> str:
        """Decrypt a message from base64 encoded ciphertext"""
        if not ciphertext:
            return ''
        
        try:
            fernet = MessageCrypto._get_key()
            encrypted_data = base64.urlsafe_b64decode(ciphertext.encode('utf-8'))
            decrypted = fernet.decrypt(encrypted_data)
            return decrypted.decode('utf-8')
        except Exception:
            return '[Message could not be decrypted]'