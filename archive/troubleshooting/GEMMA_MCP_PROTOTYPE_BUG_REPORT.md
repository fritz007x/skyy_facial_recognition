# Gemma MCP Prototype - Bug Report

**Date:** 2025-11-25
**Scope:** Complete code review of `gemma_mcp_prototype/` directory
**Files Reviewed:** 9 files (7 Python files, 1 requirements.txt, 1 README.md)

---

## Critical Bugs (Must Fix)

### 1. Import Error - oauth_config Module Not Accessible

**File:** `main.py:44`
**Severity:** CRITICAL - Code will not run
**Description:**

```python
from oauth_config import oauth_config
```

The `oauth_config.py` file is located in `src/oauth_config.py`, not in the parent directory of `gemma_mcp_prototype/`. This import will fail with `ModuleNotFoundError`.

**Impact:** Application cannot start

**Fix:**
```python
# Add src directory to path before importing
import sys
from pathlib import Path

# Add src directory for oauth_config
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from oauth_config import oauth_config
```

**Alternative Fix:** Use relative import
```python
from ..src.oauth_config import oauth_config
```

---

## High-Priority Bugs

### 2. Path Construction is Windows-Specific

**File:** `config.py:18`
**Severity:** HIGH - Cross-platform compatibility issue
**Description:**

```python
MCP_PYTHON_PATH = PROJECT_ROOT / "facial_mcp_py311" / "Scripts" / "python.exe"
```

Uses hardcoded `"Scripts"` directory which is Windows-specific. On Linux/macOS, virtual environments use `"bin"` directory, not `"Scripts"`.

**Impact:** Code will fail on Linux/macOS systems

**Fix:**
```python
import sys
import platform

# Detect platform
if platform.system() == "Windows":
    venv_bin = "Scripts"
    python_exe = "python.exe"
else:
    venv_bin = "bin"
    python_exe = "python"

MCP_PYTHON_PATH = PROJECT_ROOT / "facial_mcp_py311" / venv_bin / python_exe
```

**Alternative Fix:** Use `sys.executable` to detect current Python
```python
import sys
from pathlib import Path

# Use the current Python interpreter's path as a template
current_python = Path(sys.executable)
venv_root = PROJECT_ROOT / "facial_mcp_py311"

if current_python.parent.name == "Scripts":  # Windows
    MCP_PYTHON_PATH = venv_root / "Scripts" / "python.exe"
else:  # Linux/Mac
    MCP_PYTHON_PATH = venv_root / "bin" / "python"
```

---

### 3. Incorrect Similarity Calculation

**File:** `main.py:202`
**Severity:** HIGH - Logic error affecting user experience
**Description:**

```python
similarity = max(0, (1 - distance)) * 100
```

This calculation assumes `distance` is always in range [0, 1], but cosine distance can exceed 1.0 in edge cases. While `max(0, ...)` prevents negative results, it doesn't handle distances > 1 correctly (they would show as 0% similarity).

Additionally, the formula `1 - distance` is incorrect for cosine distance. Cosine similarity should be used instead:
- Cosine similarity = 1 - cosine distance
- For cosine distance in range [0, 2]: similarity = (1 - distance/2) * 100

**Impact:**
- Misleading confidence scores shown to users
- Potential for 0% similarity shown for valid matches
- Incorrect prompt to Gemma for greeting generation

**Fix:**
```python
# Cosine distance range is [0, 2]
# Convert to similarity percentage: 0 distance = 100%, 2 distance = 0%
similarity = max(0, min(100, (1 - distance / 2) * 100))
```

Or use the actual cosine similarity if available from the API:
```python
# If API returns cosine similarity instead of distance:
similarity = max(0, min(100, cosine_similarity * 100))
```

**Context:** The MCP server returns `distance` (lower is better), which is cosine distance. This should be converted properly to a 0-100% scale for user-facing output.

---

## Medium-Priority Issues

### 4. Unused Instance Variables

**File:** `modules/mcp_client.py:100`
**Severity:** MEDIUM - Code smell, potential confusion
**Description:**

```python
# Read and write streams
self.read_stream, self.write_stream = stdio_transport
```

These instance variables are stored but never used anywhere else in the code. The `session` object handles all communication.

**Impact:**
- Code clutter
- Potential confusion for maintainers
- Minimal memory overhead

**Fix:** Remove the unused assignment or make them private if needed for debugging:
```python
# Store for potential debugging, but not used in normal operation
read_stream, write_stream = stdio_transport
# Or if needed for debugging:
self._read_stream, self._write_stream = stdio_transport
```

**Recommendation:** Remove entirely if not needed for debugging.

---

### 5. Missing Wake Word Variant

**File:** `config.py:42`
**Severity:** LOW-MEDIUM - Inconsistency with documentation
**Description:**

```python
WAKE_WORD_ALTERNATIVES = ["hey gemma", "gemma"]
```

The `gemma3n_live_voice_assistant.py` documentation mentions "Hi Gemma" as a wake word variant, but it's not included in the prototype's alternatives.

**Impact:** User confusion - "Hi Gemma" won't work despite being mentioned in related documentation

**Fix:**
```python
WAKE_WORD_ALTERNATIVES = ["hey gemma", "hi gemma", "gemma"]
```

---

## Low-Priority Issues

### 6. No Input Validation for User Name

**File:** `main.py:292`
**Severity:** LOW - Potential for invalid data
**Description:**

```python
# Clean up name (capitalize, remove filler words)
name = name.strip().title()
```

No validation is performed on the user's spoken name. This could result in:
- Empty names if user just says noise
- Special characters or numbers
- Very long names
- Names with profanity or inappropriate content

**Impact:**
- Database could contain invalid or inappropriate names
- Potential security issue if names are displayed without sanitization

**Fix:**
```python
# Clean up name
name = name.strip().title()

# Validate name
if not name or len(name) < 2:
    self.speech.speak("I didn't catch a valid name. Please try again.")
    return

if len(name) > 100:
    self.speech.speak("That name is too long. Please use a shorter name.")
    return

# Optional: Check for invalid characters
import re
if not re.match(r'^[a-zA-Z\s\-\.\']+$', name):
    self.speech.speak("Please use only letters and common punctuation in your name.")
    return
```

---

### 7. Error Handling for OAuth Token Expiry

**File:** `main.py:330-364`
**Severity:** LOW - Edge case not handled
**Description:**

The main run loop doesn't handle OAuth token expiration. If the token expires during a long-running session (default is set in oauth_config), subsequent MCP calls will fail.

**Impact:**
- After token expires (typically 60 minutes), all recognition attempts will fail
- User will see cryptic errors instead of being prompted to restart

**Fix:** Add token refresh logic:
```python
async def run(self) -> None:
    """Main run loop - listen for wake word and handle interactions."""
    self._running = True
    token_created = time.time()

    wake_words = [WAKE_WORD] + WAKE_WORD_ALTERNATIVES

    print("\n" + "=" * 60)
    print(f"  Listening for: {wake_words}")
    print("  Press Ctrl+C to exit")
    print("=" * 60 + "\n")

    self.speech.speak("Hello! I'm Gemma. Say 'Hello Gemma' when you're ready.")

    while self._running:
        try:
            # Check if token needs refresh (before expiry)
            elapsed_minutes = (time.time() - token_created) / 60
            if elapsed_minutes > (oauth_config.ACCESS_TOKEN_EXPIRE_MINUTES - 5):
                print("[OAuth] Refreshing access token...")
                self.access_token = self.setup_oauth()
                token_created = time.time()

            # Listen for wake word
            detected, transcription = self.speech.listen_for_wake_word(
                wake_words,
                timeout=None
            )

            if detected:
                print(f"\n[Wake] Detected wake word in: '{transcription}'")
                await self.handle_recognition()
                print("\n[Main] Returning to listening mode...\n")

        except KeyboardInterrupt:
            print("\n[Main] Interrupt received, shutting down...")
            self._running = False
            break
        except Exception as e:
            print(f"[Main] Error: {e}")
            await asyncio.sleep(1)
```

---

## Recommendations (Not Bugs)

### 8. PyAudio Installation Challenge

**File:** `requirements.txt:21`
**Note:** PyAudio can be difficult to install on some systems

**Recommendation:** Add installation notes to README:

```markdown
### PyAudio Installation

**Windows:**
If `pip install pyaudio` fails, download the appropriate wheel from:
https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio

Then install with:
```bash
pip install PyAudio-0.2.13-cp311-cp311-win_amd64.whl
```

**Linux:**
```bash
sudo apt-get install portaudio19-dev python3-pyaudio
pip install pyaudio
```

**macOS:**
```bash
brew install portaudio
pip install pyaudio
```
```

---

### 9. Ollama Model Naming

**File:** `config.py:29`
**Note:** Verify the Ollama model name is correct

The configuration uses:
```python
OLLAMA_MODEL = "gemma3:4b"
```

Ollama model naming typically uses format `model:tag`. Verify that:
1. The model is pulled: `ollama list`
2. The exact name matches (could be `gemma2:2b`, `gemma:7b`, etc.)

**Recommendation:** Add a verification step in the README:
```bash
# Pull the model if not already available
ollama pull gemma3:4b

# Verify it's available
ollama list
```

---

## Summary

| Severity | Count | Must Fix Before Release |
|----------|-------|-------------------------|
| Critical | 1 | Yes |
| High | 2 | Yes |
| Medium | 2 | Recommended |
| Low | 2 | Optional |
| Recommendations | 2 | Optional |

**Critical Issues That Prevent Execution:**
1. OAuth config import error (main.py:44)

**High-Priority Cross-Platform Issues:**
1. Windows-specific path construction (config.py:18)
2. Incorrect similarity calculation (main.py:202)

**Files Requiring Fixes:**
- `gemma_mcp_prototype/main.py` (3 issues)
- `gemma_mcp_prototype/config.py` (2 issues)
- `gemma_mcp_prototype/modules/mcp_client.py` (1 issue)

**Files Without Issues:**
- `modules/__init__.py` ✓
- `modules/speech.py` ✓
- `modules/vision.py` ✓
- `modules/permission.py` ✓
- `requirements.txt` ✓ (with installation notes recommendation)

---

## Testing Recommendations

After applying fixes:

1. **Test OAuth import:**
   ```bash
   python -c "from gemma_mcp_prototype.main import GemmaFacialRecognition"
   ```

2. **Test cross-platform compatibility:**
   ```bash
   python gemma_mcp_prototype/config.py  # Add print statements to verify paths
   ```

3. **Test similarity calculation:**
   Create unit test with known distance values:
   - Distance 0.0 → Should show ~100% similarity
   - Distance 0.4 → Should show ~80% similarity
   - Distance 1.0 → Should show ~50% similarity
   - Distance 2.0 → Should show ~0% similarity

4. **Integration test:**
   ```bash
   cd gemma_mcp_prototype
   python main.py
   ```
   Verify:
   - OAuth authentication succeeds
   - MCP server connection succeeds
   - Speech recognition works
   - Camera initialization works
   - Wake word detection works

---

## Conclusion

The codebase is well-structured and mostly follows good practices. The critical import error must be fixed before the code can run. The cross-platform compatibility issues should be addressed to ensure the prototype works on Linux/macOS systems. The similarity calculation bug should be fixed to provide accurate user feedback.

Overall code quality: **Good**, with fixable issues preventing execution.
