# Vosk Grammar Fix - Quick Reference

**Issue**: App crashed with segmentation fault when using grammar-based transcription
**Root Cause**: Incorrect JSON format passed to KaldiRecognizer
**Status**: FIXED

---

## The Problem

```python
# WRONG (caused crash):
grammar_dict = {"grammar": ["hello gemma", "hey gemma"]}
grammar_json = json.dumps(grammar_dict)
recognizer = KaldiRecognizer(model, 16000, grammar_json)
# Produced: {"grammar": [...]}  <- WRONG!
# Result: Segmentation fault (exit code 139)
```

---

## The Solution

```python
# CORRECT (works perfectly):
grammar = ["hello gemma", "hey gemma"]
grammar_json = json.dumps(grammar)
recognizer = KaldiRecognizer(model, 16000, grammar_json)
# Produces: [...]  <- CORRECT!
# Result: Works perfectly!
```

---

## Vosk Error Message

```
WARNING (VoskAPI:UpdateGrammarFst():recognizer.cc:283)
Expecting array of strings, got: '{"grammar": ["hello gemma", ...]}'

Segmentation fault (core dumped)
```

---

## Files Modified

1. **gemma_mcp_prototype/modules/transcription_engine.py**
   - Line 136: Removed `grammar_dict = {"grammar": grammar}`
   - Line 136: Changed to `grammar_json = json.dumps(grammar)`
   - Line 186: Same fix in `transcribe_with_confidence()`

2. **VOSK_MIGRATION.md**
   - Updated all examples to show correct format
   - Added warnings about incorrect dict format

---

## Test Results

All tests pass:
- `test_vosk_grammar_correct.py` - Confirms correct format works
- `test_grammar_transcription_fix.py` - Full unit test suite
- Live app test - No crashes, stable operation

---

## Quick Verification

**To verify the fix is working**:

```bash
# Run the app
python gemma_mcp_prototype/main_sync_refactored.py

# Expected behavior:
# 1. App initializes without errors
# 2. Listens for wake words
# 3. No crashes when audio is detected
# 4. Transcription completes successfully
```

**To test grammar directly**:

```bash
python test_grammar_transcription_fix.py
# All tests should pass
```

---

## Remember

- Vosk expects: `["word1", "word2"]` (JSON array)
- NOT: `{"grammar": ["word1", "word2"]}` (dict wrapper)
- Always pass the list directly to `json.dumps()`
- No dict wrapper needed!

---

**Fixed**: 2025-11-29
**Impact**: Critical bug - app was completely unusable for grammar-based recognition
**Status**: Verified and tested
