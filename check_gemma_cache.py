"""Check Gemma 3n model cache location and size."""
from pathlib import Path

# HuggingFace cache location
cache_dir = Path.home() / '.cache' / 'huggingface' / 'hub'

print("=" * 70)
print("HUGGINGFACE MODEL CACHE LOCATION")
print("=" * 70)
print(f"\nCache directory: {cache_dir}")
print(f"Exists: {cache_dir.exists()}")

if cache_dir.exists():
    # Find Gemma models
    gemma_models = list(cache_dir.glob('models--google--gemma*'))

    print(f"\nGemma models found: {len(gemma_models)}")
    print("=" * 70)

    for model_dir in gemma_models:
        print(f"\nModel: {model_dir.name}")
        print(f"Location: {model_dir}")

        # Calculate size
        total_size = sum(f.stat().st_size for f in model_dir.rglob('*') if f.is_file())
        print(f"Size: {total_size / (1024**3):.2f} GB ({total_size:,} bytes)")

        # Count files
        file_count = sum(1 for f in model_dir.rglob('*') if f.is_file())
        print(f"Files: {file_count}")

    # Total cache size
    print("\n" + "=" * 70)
    total_cache = sum(f.stat().st_size for f in cache_dir.rglob('*') if f.is_file())
    print(f"Total HuggingFace cache size: {total_cache / (1024**3):.2f} GB")
    print("=" * 70)

else:
    print("\nCache directory not found. No models downloaded yet.")

print("\n\nTo clear cache (free up space):")
print("  1. Delete specific model:")
print(f"     rmdir /s {cache_dir}\\models--google--gemma-3n-E2B-it")
print("  2. Clear all cache:")
print(f"     rmdir /s {cache_dir}")
print("\nTo change cache location (set environment variable):")
print("  set HF_HOME=D:\\my_custom_cache")
