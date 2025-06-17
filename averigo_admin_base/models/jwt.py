import datetime

import jwt
from Crypto.Util.Padding import pad
import base64
from Crypto.Cipher import AES

from odoo import models
# Secret Key for JWT Signing
JWT_SECRET_KEY = "OnEpIeCe"  # Replace with a secure key
JWT_ALGORITHM = "HS256"  # HMAC-SHA256

class JWTManager(models.AbstractModel):
    _name = "jwt.manager"

    def generate_jwt_token(self, user_id):
        """Generate a JWT token for the given user."""
        payload = {
            "user_id": user_id,
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1),  # Expiry time (1 hour)
            "iat": datetime.datetime.now(datetime.timezone.utc)  # Issued at time
        }
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return token

    def decode_jwt_token(self, token):
        """Decode and validate the JWT token."""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return {"error": "Token has expired"}
        except jwt.InvalidTokenError:
            return {"error": "Invalid token"}


class AESEncryption:

    # def pad(data):
    #     """
    #     Pads the input data using PKCS7 padding.
    #     Args:
    #         data (bytes): The data to be padded.
    #     Returns:
    #         bytes: Padded data.
    #     """
    #     padding_length = 16 - (len(data) % 16)
    #     return data + bytes([padding_length] * padding_length)

    def encrypt_password(plain_text, key):
        """
        Encrypts plaintext using AES-ECB encryption with Base64 encoding.

        Args:
            plain_text (str): The plaintext to encrypt.
            key (bytes): The AES key (must be 16, 24, or 32 bytes long).

        Returns:
            str: The Base64 encoded AES encrypted string.
        """
        try:
            # Verify the key length
            if len(key) not in (16, 24, 32):
                raise ValueError("Invalid AES key length. Key must be 16, 24, or 32 bytes long.")

            # Pad the plaintext to make it a multiple of 16 bytes
            padded_data = pad(plain_text.encode('utf-8'))

            # Encrypt using AES in ECB mode
            cipher = AES.new(key, AES.MODE_ECB)
            encrypted_data = cipher.encrypt(padded_data)

            # Return the encrypted data as a Base64 encoded string
            return base64.b64encode(encrypted_data).decode('utf-8')

        except Exception as e:
            return None

    def decrypt_password(encrypted_data, key):
        """
        Decrypts AES-ECB encrypted data with Base64 encoding.

        Args:
            encrypted_data (str): The Base64 encoded AES encrypted string.
            key (bytes): The AES key (must be 16, 24, or 32 bytes long).

        Returns:
            str: The decrypted and unpadded string.
        """
        try:
            # Verify the key length
            if len(key) not in (16, 24, 32):
                raise ValueError("Invalid AES key length. Key must be 16, 24, or 32 bytes long.")

            # Base64 decode the encrypted data
            encrypted_data_bytes = base64.b64decode(encrypted_data)

            # Decrypt using AES in ECB mode
            cipher = AES.new(key, AES.MODE_ECB)
            decrypted_data = cipher.decrypt(encrypted_data_bytes)

            # Remove padding (assuming PKCS7 padding)
            padding_length = decrypted_data[-1]
            if padding_length > 16:  # Invalid padding length
                raise ValueError("Invalid padding detected in decrypted data.")

            unpadded_data = decrypted_data[:-padding_length]

            # Return the decrypted data as a UTF-8 string
            return unpadded_data.decode('utf-8')

        except Exception as e:
            return None