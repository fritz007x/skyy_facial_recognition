#!/usr/bin/env python
"""
Diagnostic script to check ChromaDB data consistency.

Identifies mismatches between ChromaDB document IDs and user_id in metadata.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import chromadb
from chromadb.config import Settings

# Path to ChromaDB
PROJECT_ROOT = Path(__file__).parent.parent
CHROMA_PATH = PROJECT_ROOT / "skyy_face_data" / "chroma_db"

def main():
    print("=" * 60)
    print("ChromaDB Diagnostic Tool")
    print("=" * 60)
    print(f"ChromaDB path: {CHROMA_PATH}")
    print()

    # Connect to ChromaDB
    client = chromadb.PersistentClient(
        path=str(CHROMA_PATH),
        settings=Settings(anonymized_telemetry=False)
    )

    # Get collection
    try:
        collection = client.get_collection("face_embeddings")
    except Exception as e:
        print(f"ERROR: Could not get collection: {e}")
        return

    # Get all data
    result = collection.get(include=["metadatas"])

    if not result["ids"]:
        print("No users found in database.")
        return

    print(f"Total users: {len(result['ids'])}")
    print()
    print("-" * 60)
    print("Checking for ID mismatches...")
    print("-" * 60)

    mismatches = []
    for i, doc_id in enumerate(result["ids"]):
        metadata = result["metadatas"][i] if result["metadatas"] else {}
        metadata_user_id = metadata.get("user_id", "<not set>")
        name = metadata.get("name", "<no name>")

        if doc_id != metadata_user_id:
            mismatches.append({
                "doc_id": doc_id,
                "metadata_user_id": metadata_user_id,
                "name": name
            })
            print(f"MISMATCH: doc_id='{doc_id}' != metadata.user_id='{metadata_user_id}' (name: {name})")
        else:
            print(f"OK: {doc_id} - {name}")

    print()
    print("-" * 60)
    if mismatches:
        print(f"FOUND {len(mismatches)} MISMATCHES!")
        print()
        print("This is causing the 'User not found' error.")
        print("The recognize_face tool returns metadata.user_id, but")
        print("get_user_profile looks up by document ID.")
        print()
        print("To fix, run: python scripts/fix_chromadb_ids.py")
    else:
        print("All IDs match correctly.")
        print()
        print("If you're still seeing 'User not found' errors,")
        print("there may be a different issue (e.g., data corruption).")

    print("-" * 60)


if __name__ == "__main__":
    main()
