# MCP Client Fix - Quick Reference

## The Problem
```
RuntimeError: Attempted to exit cancel scope in a different task than it was entered in
```

## The Cause
Using `asyncio.run()` for each async call creates a new event loop every time, breaking the MCP client's persistent async context.

## The Fix

### Before (Broken)
```python
def _run_async(self, coro):
    """Helper to run async code synchronously."""
    return asyncio.run(coro)  # Creates NEW loop each time!
```

### After (Fixed)
```python
def __init__(self):
    # ... other fields ...
    self._event_loop: Optional[asyncio.AbstractEventLoop] = None

def _run_async(self, coro):
    """Helper to run async code synchronously using persistent event loop."""
    if self._event_loop is None:
        # Create persistent event loop on first use
        self._event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._event_loop)

    return self._event_loop.run_until_complete(coro)

def cleanup(self):
    # ... other cleanup ...

    if self.mcp_client:
        try:
            self._run_async(self.mcp_client.disconnect())
        except RuntimeError as e:
            if "different task" not in str(e):
                raise
            print(f"[Cleanup] MCP disconnect warning: {e}", flush=True)

    # Close the persistent event loop
    if self._event_loop is not None:
        self._event_loop.close()
```

## Why This Works
- **One event loop** created on first async call
- **Same loop reused** for all subsequent async operations
- **MCP context preserved** across all calls
- **Proper cleanup** when application shuts down

## Test
```bash
python test_mcp_client_fix.py
```

Expected output:
```
[Test] PASSED: Initialization successful
[Test] PASSED: Second MCP call successful
[Test] PASSED: Third MCP call successful
[Test] PASSED: Fourth MCP call successful

ALL TESTS PASSED!
```

## Files Changed
- `gemma_mcp_prototype/main_sync.py` - Lines 74, 102-116, 191-213
