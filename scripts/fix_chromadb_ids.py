#!/usr/bin/env python
"""
Fix script to repair ChromaDB ID mismatches.

This script fixes the issue where ChromaDB document IDs don't match
the user_id stored in metadata, causing "User not found" errors.

The fix updates the metadata.user_id to match the document ID.
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
    print("ChromaDB ID Fix Tool")
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

    # Find and fix mismatches
    fixed_count = 0
    for i, doc_id in enumerate(result["ids"]):
        metadata = result["metadatas"][i] if result["metadatas"] else {}
        metadata_user_id = metadata.get("user_id", "")
        name = metadata.get("name", "<no name>")

        if doc_id != metadata_user_id:
            print(f"Fixing: '{name}'")
            print(f"  Document ID: {doc_id}")
            print(f"  Metadata user_id: {metadata_user_id}")

            # Update metadata to match document ID
            updated_metadata = metadata.copy()
            updated_metadata["user_id"] = doc_id

            try:
                collection.update(
                    ids=[doc_id],
                    metadatas=[updated_metadata]
                )
                print(f"  -> Fixed: user_id now set to '{doc_id}'")
                fixed_count += 1
            except Exception as e:
                print(f"  -> ERROR: {e}")

    print()
    print("-" * 60)
    if fixed_count > 0:
        print(f"Fixed {fixed_count} user(s).")
        print()
        print("The 'User not found' error should now be resolved.")
        print("Please restart the voice assistant and try again.")
    else:
        print("No mismatches found - nothing to fix.")

    print("-" * 60)


if __name__ == "__main__":
    main()
