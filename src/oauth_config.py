"""
OAuth 2.1 Configuration for Skyy Facial Recognition MCP Server

Implements Client Credentials flow with JWT tokens.
"""

import os
import secrets
import json
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime, timedelta
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend


class OAuthConfig:
    """OAuth 2.1 configuration and token management"""

    # Token expiration times
    ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour

    # JWT algorithm
    ALGORITHM = "RS256"  # RSA signature for better security

    # Paths
    CONFIG_DIR = Path("oauth_data")
    PRIVATE_KEY_PATH = CONFIG_DIR / "private_key.pem"
    PUBLIC_KEY_PATH = CONFIG_DIR / "public_key.pem"
    CLIENTS_PATH = CONFIG_DIR / "clients.json"

    def __init__(self):
        """Initialize OAuth configuration"""
        self.CONFIG_DIR.mkdir(exist_ok=True)
        self._ensure_keys_exist()
        self._load_keys()
        self._ensure_clients_file()

    def _ensure_keys_exist(self):
        """Generate RSA key pair if it doesn't exist"""
        if not self.PRIVATE_KEY_PATH.exists() or not self.PUBLIC_KEY_PATH.exists():
            print("[OAuth] Generating new RSA key pair...")

            # Generate private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )

            # Save private key
            pem_private = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            self.PRIVATE_KEY_PATH.write_bytes(pem_private)

            # Save public key
            public_key = private_key.public_key()
            pem_public = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            self.PUBLIC_KEY_PATH.write_bytes(pem_public)

            print(f"[OAuth] RSA keys saved to {self.CONFIG_DIR}")

    def _load_keys(self):
        """Load RSA keys from files"""
        self.private_key = self.PRIVATE_KEY_PATH.read_text()
        self.public_key = self.PUBLIC_KEY_PATH.read_text()

    def _ensure_clients_file(self):
        """Ensure clients file exists"""
        if not self.CLIENTS_PATH.exists():
            self.CLIENTS_PATH.write_text(json.dumps({}, indent=2))

    def load_clients(self) -> Dict[str, Dict[str, str]]:
        """Load client credentials from file"""
        if self.CLIENTS_PATH.exists():
            return json.loads(self.CLIENTS_PATH.read_text())
        return {}

    def save_clients(self, clients: Dict[str, Dict[str, str]]):
        """Save client credentials to file"""
        self.CLIENTS_PATH.write_text(json.dumps(clients, indent=2))

    def create_client(self, client_id: Optional[str] = None,
                     client_name: Optional[str] = None) -> Dict[str, str]:
        """
        Create a new OAuth client

        Args:
            client_id: Optional custom client ID
            client_name: Optional human-readable name

        Returns:
            Dict with client_id and client_secret
        """
        if client_id is None:
            client_id = f"client_{secrets.token_urlsafe(16)}"

        client_secret = secrets.token_urlsafe(32)

        clients = self.load_clients()
        clients[client_id] = {
            "client_secret": client_secret,
            "client_name": client_name or client_id,
            "created_at": datetime.utcnow().isoformat()
        }
        self.save_clients(clients)

        print(f"[OAuth] Created client: {client_id}")
        return {
            "client_id": client_id,
            "client_secret": client_secret
        }

    def verify_client(self, client_id: str, client_secret: str) -> bool:
        """
        Verify client credentials

        Args:
            client_id: Client ID
            client_secret: Client secret

        Returns:
            True if credentials are valid
        """
        clients = self.load_clients()
        if client_id not in clients:
            return False

        return clients[client_id]["client_secret"] == client_secret

    def create_access_token(self, client_id: str) -> str:
        """
        Create a JWT access token

        Args:
            client_id: Client ID to create token for

        Returns:
            JWT token string
        """
        now = datetime.utcnow()
        expires = now + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)

        payload = {
            "sub": client_id,  # Subject (client ID)
            "iat": now,  # Issued at
            "exp": expires,  # Expiration
            "type": "access_token",
            "iss": "skyy_facial_recognition_mcp"  # Issuer
        }

        token = jwt.encode(payload, self.private_key, algorithm=self.ALGORITHM)
        return token

    def verify_token(self, token: str) -> Optional[Dict]:
        """
        Verify and decode a JWT token

        Args:
            token: JWT token string

        Returns:
            Decoded token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(
                token,
                self.public_key,
                algorithms=[self.ALGORITHM],
                options={"verify_exp": True}
            )

            # Verify token type
            if payload.get("type") != "access_token":
                return None

            # Verify issuer
            if payload.get("iss") != "skyy_facial_recognition_mcp":
                return None

            return payload
        except jwt.ExpiredSignatureError:
            print("[OAuth] Token expired")
            return None
        except jwt.InvalidTokenError as e:
            print(f"[OAuth] Invalid token: {e}")
            return None

    def delete_client(self, client_id: str) -> bool:
        """
        Delete a client

        Args:
            client_id: Client ID to delete

        Returns:
            True if deleted, False if not found
        """
        clients = self.load_clients()
        if client_id in clients:
            del clients[client_id]
            self.save_clients(clients)
            print(f"[OAuth] Deleted client: {client_id}")
            return True
        return False

    def list_clients(self) -> Dict[str, Dict[str, str]]:
        """
        List all clients (without secrets)

        Returns:
            Dict of clients with public information
        """
        clients = self.load_clients()
        return {
            cid: {
                "client_name": info["client_name"],
                "created_at": info["created_at"]
            }
            for cid, info in clients.items()
        }


# Global OAuth config instance
oauth_config = OAuthConfig()
