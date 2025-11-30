"""
Test Hugging Face Authentication

This script checks if you are properly authenticated with Hugging Face
and have access to the Gemma 3n models.

Usage:
    python test_hf_auth.py
"""

import sys
import os
from pathlib import Path

print("\n" + "=" * 70)
print("HUGGING FACE AUTHENTICATION TEST")
print("=" * 70)

# Check if huggingface_hub is installed
try:
    from huggingface_hub import whoami, list_repo_files, login
    from huggingface_hub.utils import GatedRepoError, RepositoryNotFoundError
    print("[OK] huggingface_hub is installed")
except ImportError:
    print("[ERROR] huggingface_hub not installed")
    print("\nInstall with:")
    print("    pip install huggingface-hub")
    sys.exit(1)

# Check for authentication
print("\n1. Checking authentication status...")
try:
    user_info = whoami()
    print(f"   [OK] Authenticated as: {user_info['name']}")
    print(f"   [OK] User ID: {user_info.get('id', 'N/A')}")
except Exception as e:
    print(f"   [ERROR] Not authenticated: {e}")
    print("\n   You need to authenticate first:")
    print("   Method 1: huggingface-cli login")
    print("   Method 2: set HF_TOKEN=your_token_here")
    sys.exit(1)

# Check environment variables
print("\n2. Checking environment variables...")
hf_token = os.environ.get('HF_TOKEN')
hf_hub_token = os.environ.get('HUGGING_FACE_HUB_TOKEN')

if hf_token:
    print(f"   [OK] HF_TOKEN found (length: {len(hf_token)})")
elif hf_hub_token:
    print(f"   [OK] HUGGING_FACE_HUB_TOKEN found (length: {len(hf_hub_token)})")
else:
    print("   [INFO] No token in environment variables")
    print("   (This is OK if you logged in with huggingface-cli)")

# Check token file
print("\n3. Checking token file...")
token_path = Path.home() / ".huggingface" / "token"
if token_path.exists():
    print(f"   [OK] Token file exists: {token_path}")
    print(f"   [OK] Token file size: {token_path.stat().st_size} bytes")
else:
    print(f"   [INFO] No token file at: {token_path}")
    print("   (This is OK if you use HF_TOKEN environment variable)")

# Test access to Gemma 3n E2B model
print("\n4. Testing access to Gemma 3n E2B model...")
model_id = "google/gemma-3n-E2B-it"

try:
    # Try to list files in the repo (this requires access)
    files = list_repo_files(model_id, repo_type="model")
    print(f"   [OK] Access granted to {model_id}")
    print(f"   [OK] Model has {len(files)} files")
    print(f"   [OK] Key files found:")

    key_files = ['config.json', 'model.safetensors', 'tokenizer.json']
    for key_file in key_files:
        if any(key_file in f for f in files):
            print(f"       - {key_file}")

except GatedRepoError as e:
    print(f"   [ERROR] Access denied to {model_id}")
    print(f"   [ERROR] You need to request access to this model")
    print(f"\n   Steps to fix:")
    print(f"   1. Visit: https://huggingface.co/{model_id}")
    print(f"   2. Click 'Request Access'")
    print(f"   3. Accept the terms")
    print(f"   4. Wait for approval (usually instant)")
    sys.exit(1)

except RepositoryNotFoundError:
    print(f"   [ERROR] Model not found: {model_id}")
    print(f"   [ERROR] This could mean:")
    print(f"       - Model ID is incorrect")
    print(f"       - Model has been deleted or moved")
    sys.exit(1)

except Exception as e:
    print(f"   [ERROR] Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test access to Gemma 3n E4B model
print("\n5. Testing access to Gemma 3n E4B model...")
model_id_e4b = "google/gemma-3n-E4B-it"

try:
    files = list_repo_files(model_id_e4b, repo_type="model")
    print(f"   [OK] Access granted to {model_id_e4b}")
    print(f"   [OK] Model has {len(files)} files")
except GatedRepoError:
    print(f"   [WARNING] No access to {model_id_e4b}")
    print(f"   (You can still use the E2B model)")
    print(f"\n   To get access to E4B:")
    print(f"   Visit: https://huggingface.co/{model_id_e4b}")
except Exception as e:
    print(f"   [INFO] Could not check E4B access: {e}")

# Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print("\n[SUCCESS] You are properly authenticated!")
print(f"[SUCCESS] You have access to Gemma 3n models!")
print(f"\nYou can now run:")
print(f"    python src\\gemma3n_native_audio_assistant.py test_audio\\hello_gemma.wav")
print("=" * 70 + "\n")
