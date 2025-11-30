# Architecture Alignment with skyy_compliment

## Problem

The gemma_mcp_prototype was experiencing TTS issues because it used asyncio extensively, which caused conflicts between pyttsx3.runAndWait() (blocking) and the async event loop. The skyy_compliment project works perfectly because it uses a **fully synchronous architecture**.

## Solution: Match skyy_compliment Architecture

### skyy_compliment Architecture (WORKING)

```python
class ComplimentModule:
    def __init__(self):
        # Initialize all modules synchronously
        self.vision = VisionAnalyzer()
        self.speech = SpeechProcessor()
        self.nlp = ComplimentGenerator()
        self.permission = PermissionHandler()

    def process_request(self):  # ← SYNCHRONOUS, not async
        # Simple sequential flow
        request = self.speech.listen_for_trigger("Skyy, compliment me")
        if not request:
            return False

        if not self.permission.request_permission():
            return False

        visual_features = self.vision.capture_and_analyze()
        compliment = self.nlp.generate_compliment(visual_features)
        self.speech.speak(compliment)
        return True

if __name__ == "__main__":
    compliment_module = ComplimentModule()
    while True:  # ← Simple while loop, no asyncio.run()
        try:
            result = compliment_module.process_request()
        except KeyboardInterrupt:
            break
```

**Key Characteristics:**
- ✅ No `async` or `await`
- ✅ No asyncio event loop
- ✅ Simple `while True` main loop
- ✅ All methods are synchronous
- ✅ Blocking operations (speech, camera) work perfectly
- ✅ `flush=True` on all print statements

### gemma_mcp_prototype OLD Architecture (BROKEN)

```python
class GemmaFacialRecognition:
    async def initialize(self) -> bool:  # ← ASYNC
        # Async initialization
        if not await self.mcp_client.connect():  # ← AWAIT
            return False

    async def run(self) -> None:  # ← ASYNC
        while self._running:
            try:
                # Speech operations mixed with async
                detected, transcription = self.speech.listen_for_wake_word(...)

                if detected:
                    self.speech.speak("Wake word detected!")  # ← BLOCKING in async context
                    await self.handle_recognition()  # ← AWAIT
            except Exception as e:
                await asyncio.sleep(1)  # ← ASYNC SLEEP

async def main():  # ← ASYNC MAIN
    app = GemmaFacialRecognition()
    try:
        if await app.initialize():  # ← AWAIT
            await app.run()
    finally:
        await app.cleanup()

if __name__ == "__main__":
    asyncio.run(main())  # ← ASYNC EVENT LOOP
```

**Problems:**
- ❌ pyttsx3.runAndWait() blocks async event loop
- ❌ Complex async/sync mixing
- ❌ TTS fails after microphone use in async context
- ❌ Harder to debug and reason about

### gemma_mcp_prototype NEW Architecture (FIXED)

```python
class GemmaFacialRecognition:
    def _run_async(self, coro):
        """Helper to run async code synchronously."""
        return asyncio.run(coro)

    def initialize(self) -> bool:  # ← SYNCHRONOUS
        # Synchronous initialization
        if not self._run_async(self.mcp_client.connect()):  # ← Wrapped async call
            return False

    def run(self) -> None:  # ← SYNCHRONOUS
        while True:  # ← Simple while True like skyy_compliment
            try:
                # Refresh token if needed
                self.refresh_token_if_needed()

                # Speech operations are naturally synchronous
                detected, transcription = self.speech.listen_for_wake_word(...)

                if detected:
                    self.speech.speak("Wake word detected!")  # ← Works perfectly!
                    self.handle_recognition()  # ← Simple method call
            except Exception as e:
                time.sleep(1)  # ← Regular sleep

def main():  # ← SYNCHRONOUS MAIN
    app = GemmaFacialRecognition()
    try:
        if app.initialize():
            app.run()
    finally:
        app.cleanup()

if __name__ == "__main__":
    main()  # ← No asyncio.run()
```

**Improvements:**
- ✅ Matches skyy_compliment architecture
- ✅ All public methods are synchronous
- ✅ TTS works perfectly (no event loop conflicts)
- ✅ Simple `while True` loop
- ✅ Async MCP calls isolated in `_run_async()` helper
- ✅ Easy to understand and debug
- ✅ `flush=True` on all prints

## Key Architectural Changes

### 1. Removed Async from Main Flow

**Before:**
```python
async def run(self) -> None:
    while self._running:
        detected, transcription = self.speech.listen_for_wake_word(...)
        if detected:
            await self.handle_recognition()
```

**After:**
```python
def run(self) -> None:  # ← No async
    while True:  # ← Simple loop
        detected, transcription = self.speech.listen_for_wake_word(...)
        if detected:
            self.handle_recognition()  # ← Direct call
```

### 2. Wrapped MCP Async Calls

**Before:**
```python
async def initialize(self):
    if not await self.mcp_client.connect():
        return False
```

**After:**
```python
def initialize(self):
    if not self._run_async(self.mcp_client.connect()):
        return False

def _run_async(self, coro):
    """Helper to run async code synchronously."""
    return asyncio.run(coro)
```

### 3. Replaced asyncio.sleep with time.sleep

**Before:**
```python
await asyncio.sleep(1)
```

**After:**
```python
time.sleep(1)
```

### 4. Simple Main Entry Point

**Before:**
```python
async def main():
    app = GemmaFacialRecognition()
    if await app.initialize():
        await app.run()

if __name__ == "__main__":
    asyncio.run(main())
```

**After:**
```python
def main():
    app = GemmaFacialRecognition()
    if app.initialize():
        app.run()

if __name__ == "__main__":
    main()  # ← Just call it directly
```

## Why This Fixes TTS

### The Problem with Async + pyttsx3

```python
async def run(self):
    # Event loop is running
    detected = self.speech.listen_for_wake_word(...)  # OK - blocking but sequential

    if detected:
        self.speech.speak("Test")  # ← PROBLEM!
        # speak() calls runAndWait() which is blocking
        # But we're inside an async event loop
        # Event loop gets stuck waiting for runAndWait()
        # runAndWait() may be waiting for event loop
        # = DEADLOCK
```

### The Solution with Sync Architecture

```python
def run(self):
    # No event loop!
    detected = self.speech.listen_for_wake_word(...)  # OK - just blocks

    if detected:
        self.speech.speak("Test")  # ← WORKS!
        # speak() calls runAndWait() which blocks
        # No event loop to conflict with
        # Everything is sequential
        # = WORKS PERFECTLY
```

## Files Structure

### Original (Async)
- `main.py` - Async architecture with asyncio.run()

### New (Sync)
- `main_sync.py` - Synchronous architecture matching skyy_compliment
- Recommended to replace main.py with main_sync.py

### Supporting Modules
- `modules/speech.py` - Already synchronous ✅
- `modules/vision.py` - Already synchronous ✅
- `modules/permission.py` - Already synchronous ✅
- `modules/mcp_client.py` - Async methods, wrapped in main_sync.py ✅

## Testing

Use `test_speech_in_async.py` (now fully synchronous) to verify:

```bash
cd gemma_mcp_prototype
..\facial_mcp_py311\Scripts\python.exe test_speech_in_async.py
```

Or run the new main:

```bash
cd gemma_mcp_prototype
..\facial_mcp_py311\Scripts\python.exe main_sync.py
```

## Lesson Learned

**Don't mix blocking I/O (like pyttsx3) with asyncio unless absolutely necessary.**

The skyy_compliment architecture is simpler, more maintainable, and actually works better for this use case. Sometimes the "old-fashioned" synchronous approach is the right choice!

## Recommendation

Replace `main.py` with `main_sync.py` as the production version. The synchronous architecture is:
- ✅ More reliable (no TTS issues)
- ✅ Easier to understand
- ✅ Easier to debug
- ✅ Matches proven working architecture (skyy_compliment)
- ✅ No performance penalty (operations are already sequential)
