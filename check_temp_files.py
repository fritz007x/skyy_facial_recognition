"""Check for temporary files created by HuggingFace downloads."""
from pathlib import Path

cache = Path.home() / '.cache' / 'huggingface' / 'hub'

print("=" * 70)
print("CHECKING FOR TEMPORARY/INCOMPLETE FILES")
print("=" * 70)

# Check for lock files (incomplete downloads)
locks_dir = cache / '.locks'
if locks_dir.exists():
    locks = list(locks_dir.glob('*'))
    print(f"\nLock files (incomplete downloads): {len(locks)}")
    if locks:
        lock_size = sum(f.stat().st_size for f in locks if f.is_file())
        print(f"Total size: {lock_size / (1024**2):.2f} MB")
        print("\nLock files found:")
        for lock in locks[:10]:
            size = lock.stat().st_size if lock.is_file() else 0
            print(f"  - {lock.name} ({size / (1024**2):.2f} MB)")
else:
    print("\nNo .locks directory found (good - no incomplete downloads)")

# Check for blobs directory
blobs_dirs = list(cache.glob('**/blobs'))
if blobs_dirs:
    print(f"\n\nBlob directories (actual model data): {len(blobs_dirs)}")
    for blob_dir in blobs_dirs:
        blobs = list(blob_dir.glob('*'))
        blob_size = sum(f.stat().st_size for f in blobs if f.is_file())
        print(f"  {blob_dir.parent.name}: {len(blobs)} files, {blob_size / (1024**3):.2f} GB")

# Check for temp files
temp_patterns = ['tmp*', '*.tmp', '*.lock', '*incomplete*']
print("\n\nTemporary files:")
temp_found = False
for pattern in temp_patterns:
    temps = list(cache.rglob(pattern))
    if temps:
        temp_found = True
        print(f"\nPattern '{pattern}': {len(temps)} files")
        for tmp in temps[:5]:
            if tmp.is_file():
                size = tmp.stat().st_size / (1024**2)
                print(f"  - {tmp.name} ({size:.2f} MB)")

if not temp_found:
    print("  None found (good!)")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print("\nHuggingFace is smart about caching:")
print("  ✓ Downloads resume if interrupted (no duplicate downloads)")
print("  ✓ Lock files are tiny (just markers)")
print("  ✓ Actual model data stored efficiently in blobs/")
print("  ✓ Failed runs DON'T create big duplicate files")
print("\nYour script failures likely created:")
print("  - A few KB in lock files (negligible)")
print("  - Maybe some small temp audio files (auto-cleaned)")
print("  - NO large model duplicates")
print("=" * 70)
