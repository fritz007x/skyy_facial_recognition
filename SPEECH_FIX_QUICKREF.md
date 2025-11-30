# Speech Asyncio Fix - Quick Reference

**Status:** FIXED ✓
**Date:** 2025-11-26
**File:** `gemma_mcp_prototype/modules/speech.py` line 190

---

## The Error

```
TypeError: a coroutine was expected, got <Future pending...>
```

---

## The Problem

```python
# WRONG - TypeError
asyncio.create_task(loop.run_in_executor(self._executor, func))
```

**Why it fails:**
- `run_in_executor()` returns a **Future** (not a coroutine)
- `create_task()` expects a **coroutine** (not a Future)

---

## The Fix

```python
# RIGHT - Future auto-scheduled
loop.run_in_executor(self._executor, func)
```

**Why it works:**
- `run_in_executor()` returns a Future that is **already scheduled**
- No need to wrap with `create_task()` or `ensure_future()`
- Fire-and-forget pattern - don't await, let it run async

---

## Verification

```bash
python test_speech_fix.py
```

**Result:**
```
[SUCCESS] All tests passed!
  - Sync context: Works (no RuntimeError)
  - Async context: Works (no TypeError)
```

---

## Key Takeaway

**Asyncio Type Rules:**

| Return Type | Created By | Wrap With |
|------------|------------|----------|
| Coroutine | `async def` | `create_task()` |
| Future | `run_in_executor()` | Nothing (already scheduled) |

**Don't wrap Futures with create_task() - they're already scheduled!**

---

## Impact

- Fixes Gemma MCP prototype crash
- Works in both sync and async contexts
- Maintains fire-and-forget TTS behavior

**Deployment:** READY ✓
