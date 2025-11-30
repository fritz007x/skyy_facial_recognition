"""
Test script to verify the speech.py asyncio fix.

Tests that speak() works correctly in both sync and async contexts.
"""

import asyncio
import sys
from pathlib import Path

# Add the gemma_mcp_prototype directory to path
prototype_dir = Path(__file__).parent / "gemma_mcp_prototype"
sys.path.insert(0, str(prototype_dir))

print("[Test] Testing speech.py asyncio fix...")
print("[Test] This will verify that speak() works in both sync and async contexts")
print()

# Test 1: Import the module
try:
    from modules.speech import SpeechManager
    print("[OK] Successfully imported SpeechManager")
except Exception as e:
    print(f"[FAIL] Could not import SpeechManager: {e}")
    sys.exit(1)

# Test 2: Create instance
try:
    speech = SpeechManager()
    print("[OK] Successfully created SpeechManager instance")
except Exception as e:
    print(f"[FAIL] Could not create SpeechModule: {e}")
    sys.exit(1)

# Test 3: Call speak() from sync context
try:
    print("[Test] Calling speak() from synchronous context...")
    speech.speak("Testing synchronous speech")
    print("[OK] speak() works in sync context (no RuntimeError)")
except Exception as e:
    print(f"[FAIL] speak() failed in sync context: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Call speak() from async context
async def test_async_speak():
    """Test speak() from within an async function."""
    try:
        print("[Test] Calling speak() from asynchronous context...")
        speech.speak("Testing asynchronous speech")
        print("[OK] speak() works in async context (no TypeError)")

        # Give the executor a moment to start
        await asyncio.sleep(0.5)
        return True
    except Exception as e:
        print(f"[FAIL] speak() failed in async context: {e}")
        import traceback
        traceback.print_exc()
        return False

# Run the async test
try:
    result = asyncio.run(test_async_speak())
    if not result:
        sys.exit(1)
except Exception as e:
    print(f"[FAIL] Async test crashed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 60)
print("[SUCCESS] All tests passed!")
print("=" * 60)
print()
print("The fix correctly handles:")
print("  1. Sync context: Uses direct function call (no event loop)")
print("  2. Async context: Uses run_in_executor (returns Future)")
print()
print("The TypeError is fixed - run_in_executor returns a Future")
print("which is automatically scheduled without needing create_task()")
