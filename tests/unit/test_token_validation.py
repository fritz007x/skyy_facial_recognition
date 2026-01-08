"""
Direct test of token validation
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.oauth_config import oauth_config

print("=" * 60)
print("TOKEN VALIDATION TEST")
print("=" * 60)

# Create a client
client_id = "validation_test_client"
clients = oauth_config.load_clients()
if client_id not in clients:
    print(f"\n[+] Creating client: {client_id}")
    oauth_config.create_client(client_id=client_id, client_name="Validation Test")

# Generate valid token
print(f"\n[+] Generating valid token for {client_id}...")
valid_token = oauth_config.create_access_token(client_id)
print(f"[+] Token: {valid_token[:50]}...")

# Test valid token
print("\n" + "=" * 60)
print("TEST 1: Valid Token")
print("=" * 60)
result = oauth_config.verify_token(valid_token)
if result:
    print(f"[+] SUCCESS - Token is valid")
    print(f"    Subject: {result.get('sub')}")
    print(f"    Issuer: {result.get('iss')}")
    print(f"    Type: {result.get('type')}")
else:
    print("[-] FAILED - Token should be valid but was rejected")

# Test invalid token
print("\n" + "=" * 60)
print("TEST 2: Invalid Token")
print("=" * 60)
invalid_token = "invalid_token_12345"
result = oauth_config.verify_token(invalid_token)
if result is None:
    print(f"[+] SUCCESS - Invalid token correctly rejected")
else:
    print(f"[-] FAILED - Invalid token should be rejected")

# Test malformed JWT
print("\n" + "=" * 60)
print("TEST 3: Malformed JWT")
print("=" * 60)
malformed_token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.malformed.signature"
result = oauth_config.verify_token(malformed_token)
if result is None:
    print(f"[+] SUCCESS - Malformed token correctly rejected")
else:
    print(f"[-] FAILED - Malformed token should be rejected")

# Test expired token (we'll create one with negative expiry)
print("\n" + "=" * 60)
print("TEST 4: Expired Token")
print("=" * 60)
import jwt
from datetime import datetime, timedelta
expired_payload = {
    "sub": client_id,
    "iat": datetime.utcnow() - timedelta(hours=2),
    "exp": datetime.utcnow() - timedelta(hours=1),  # Already expired
    "type": "access_token",
    "iss": "skyy_facial_recognition_mcp"
}
expired_token = jwt.encode(expired_payload, oauth_config.private_key, algorithm=oauth_config.ALGORITHM)
result = oauth_config.verify_token(expired_token)
if result is None:
    print(f"[+] SUCCESS - Expired token correctly rejected")
else:
    print(f"[-] FAILED - Expired token should be rejected")

print("\n" + "=" * 60)
print("ALL TOKEN VALIDATION TESTS COMPLETED")
print("=" * 60)
