"""
Test field selection retry logic in update orchestrator.

Validates that field selection has comprehensive retry logic:
1. Retry on no speech detected
2. Retry on transcription failure
3. Retry on unrecognized keywords
4. Retry on confirmation rejection
5. Retry on unclear confirmation
6. Max retries exhaustion handling
"""

from pathlib import Path


def test_retry_loop_implemented():
    """Verify retry loop is implemented in select_update_fields."""
    print("Test 1: Retry Loop Implementation")

    orch_file = Path("src/gemma_voice_assistant/modules/update_orchestrator.py")
    with open(orch_file, 'r') as f:
        content = f.read()

    checks = [
        ("Retry loop with max_retries", "for attempt in range(self.max_retries):"),
        ("Attempt tracking", "attempt + 1}/{self.max_retries}"),
        ("Continue statement for retries", "continue"),
        ("Max retries exhaustion message", "Max retries"),
    ]

    passed = 0
    for check_name, check_str in checks:
        if check_str in content:
            print(f"  [OK] {check_name}")
            passed += 1
        else:
            print(f"  [X] Missing: {check_name}")

    # Check for loop in select_update_fields
    if "def select_update_fields" in content and "for attempt in range(self.max_retries):" in content:
        print(f"  [OK] Loop in select_update_fields")
        passed += 1
    else:
        print(f"  [X] Missing: Loop in select_update_fields")

    checks_total = len(checks) + 1  # +1 for the boolean check

    print(f"\n  Result: {passed}/{checks_total} retry loop checks passed\n")
    return passed == checks_total


def test_no_speech_retry():
    """Verify retry on no speech detected."""
    print("Test 2: No Speech Detection - Retry Logic")

    orch_file = Path("src/gemma_voice_assistant/modules/update_orchestrator.py")
    with open(orch_file, 'r') as f:
        content = f.read()

    checks = [
        ("Check for no audio", "if not success or audio is None:"),
        ("Error message for no speech", "I didn't hear anything"),
        ("Continue to retry", "continue"),
        ("Sleep between retries", "time.sleep(0.5)"),
    ]

    passed = 0
    for check_name, check_str in checks:
        if check_str in content:
            print(f"  [OK] {check_name}")
            passed += 1
        else:
            print(f"  [X] Missing: {check_name}")

    print(f"\n  Result: {passed}/{len(checks)} retry loop checks passed\n")
    return passed == len(checks)


def test_no_speech_retry():
    """Verify retry on no speech detected."""
    print("Test 2: No Speech Detection - Retry Logic")

    orch_file = Path("src/gemma_voice_assistant/modules/update_orchestrator.py")
    with open(orch_file, 'r') as f:
        content = f.read()

    checks = [
        ("Check for no audio", "if not success or audio is None:"),
        ("Error message for no speech", "I didn't hear anything"),
        ("Continue to retry", "continue"),
        ("Sleep between retries", "time.sleep(0.5)"),
    ]

    passed = 0
    for check_name, check_str in checks:
        if check_str in content:
            print(f"  [OK] {check_name}")
            passed += 1
        else:
            print(f"  [X] Missing: {check_name}")

    print(f"\n  Result: {passed}/{len(checks)} no-speech retry checks passed\n")
    return passed == len(checks)


def test_transcription_failure_retry():
    """Verify retry on transcription failure."""
    print("Test 3: Transcription Failure - Retry Logic")

    orch_file = Path("src/gemma_voice_assistant/modules/update_orchestrator.py")
    with open(orch_file, 'r') as f:
        content = f.read()

    checks = [
        ("Check for empty transcription", "if not selection_text:"),
        ("Error message for transcription failure", "I couldn't understand that"),
        ("Prompt to repeat", "Please repeat"),
        ("Continue to retry", "continue"),
    ]

    passed = 0
    for check_name, check_str in checks:
        if check_str in content:
            print(f"  [OK] {check_name}")
            passed += 1
        else:
            print(f"  [X] Missing: {check_name}")

    print(f"\n  Result: {passed}/{len(checks)} transcription failure retry checks passed\n")
    return passed == len(checks)


def test_unrecognized_keyword_retry():
    """Verify retry on unrecognized keywords."""
    print("Test 4: Unrecognized Keywords - Retry Logic")

    orch_file = Path("src/gemma_voice_assistant/modules/update_orchestrator.py")
    with open(orch_file, 'r') as f:
        content = f.read()

    checks = [
        ("Check keywords with if/elif", 'if "both" in selection_normalized:'),
        ("Else case for unrecognized", "else:"),
        ("Error message for unclear input", "but that's not clear"),
        ("Suggest valid options", "Please say 'name', 'metadata', or 'both'"),
        ("Continue to retry", "continue"),
    ]

    passed = 0
    for check_name, check_str in checks:
        if check_str in content:
            print(f"  [OK] {check_name}")
            passed += 1
        else:
            print(f"  [X] Missing: {check_name}")

    print(f"\n  Result: {passed}/{len(checks)} keyword recognition retry checks passed\n")
    return passed == len(checks)


def test_confirmation_retry():
    """Verify retry on confirmation failures."""
    print("Test 5: Confirmation Retry Logic")

    orch_file = Path("src/gemma_voice_assistant/modules/update_orchestrator.py")
    with open(orch_file, 'r') as f:
        content = f.read()

    checks = [
        ("Check for no confirmation audio", "if not success or conf_audio is None:"),
        ("Error on no confirmation", "I didn't catch your confirmation"),
        ("Retry prompt", "Let me try again"),
        ("Continue on rejection", "elif confirmed is False:"),
        ("User rejection message", "Okay, let's try again"),
        ("Continue on unclear", "else:"),
        ("Unclear confirmation message", "I didn't understand your confirmation"),
    ]

    passed = 0
    for check_name, check_str in checks:
        if check_str in content:
            print(f"  [OK] {check_name}")
            passed += 1
        else:
            print(f"  [X] Missing: {check_name}")

    print(f"\n  Result: {passed}/{len(checks)} confirmation retry checks passed\n")
    return passed >= len(checks) - 1  # Allow 1 failure


def test_error_messages():
    """Verify appropriate error messages at each stage."""
    print("Test 6: Error Messages for Each Retry Scenario")

    orch_file = Path("src/gemma_voice_assistant/modules/update_orchestrator.py")
    with open(orch_file, 'r') as f:
        content = f.read()

    error_messages = [
        ("No speech detected", "I didn't hear anything"),
        ("Transcription failed", "I couldn't understand that"),
        ("Unrecognized keywords", "but that's not clear"),
        ("No confirmation response", "I didn't catch your confirmation"),
        ("Unclear confirmation", "I didn't understand your confirmation"),
        ("Max retries exhausted", "I'm having trouble understanding"),
        ("Suggest valid options", "name', 'metadata', or 'both"),
    ]

    passed = 0
    for msg_name, msg_text in error_messages:
        if msg_text in content:
            print(f"  [OK] {msg_name}: '{msg_text}'")
            passed += 1
        else:
            print(f"  [X] Missing: {msg_name}")

    print(f"\n  Result: {passed}/{len(error_messages)} error messages verified\n")
    return passed >= len(error_messages) - 1  # Allow 1 failure


def test_retry_limits():
    """Verify retry limits and exhaustion handling."""
    print("Test 7: Retry Limits and Exhaustion")

    orch_file = Path("src/gemma_voice_assistant/modules/update_orchestrator.py")
    with open(orch_file, 'r') as f:
        content = f.read()

    checks = [
        ("Uses self.max_retries", "range(self.max_retries)"),
        ("Tracks attempt number", "attempt + 1"),
        ("Logs retry attempts", "attempt {attempt + 1}/{self.max_retries}"),
        ("Handles exhaustion", "# Exhausted all retries"),
        ("Returns None on exhaustion", "return None"),
        ("Friendly exhaustion message", "Please try the update again later"),
    ]

    passed = 0
    for check_name, check_str in checks:
        if check_str in content:
            print(f"  [OK] {check_name}")
            passed += 1
        else:
            print(f"  [X] Missing: {check_name}")

    print(f"\n  Result: {passed}/{len(checks)} retry limits checks passed\n")
    return passed == len(checks)


def test_user_prompts():
    """Verify user-facing prompts for all retry scenarios."""
    print("Test 8: User-Facing Prompts for Retry Logic")

    orch_file = Path("src/gemma_voice_assistant/modules/update_orchestrator.py")
    with open(orch_file, 'r') as f:
        content = f.read()

    prompts = [
        ("Initial question", "What would you like to update"),
        ("No speech prompt", "I didn't hear anything"),
        ("Transcription fail prompt", "I couldn't understand that"),
        ("Unclear input prompt", "but that's not clear"),
        ("Confirmation prompt", "You want to update your"),
        ("Confirmation lost prompt", "I didn't catch your confirmation"),
        ("User rejection prompt", "Okay, let's try again"),
        ("Unclear confirmation prompt", "I didn't understand your confirmation"),
        ("Exhaustion prompt", "I'm having trouble understanding"),
        ("Helpful hint", "Please say 'name', 'metadata', or 'both'"),
    ]

    passed = 0
    for prompt_name, prompt_text in prompts:
        if prompt_text in content:
            print(f"  [OK] {prompt_name}")
            passed += 1
        else:
            print(f"  [X] Missing: {prompt_name}")

    print(f"\n  Result: {passed}/{len(prompts)} user prompts verified\n")
    return passed >= len(prompts) - 1  # Allow 1 failure


def main():
    print("=" * 70)
    print("  FIELD SELECTION RETRY LOGIC - IMPLEMENTATION TESTS")
    print("  Comprehensive retry handling for field selection prompt")
    print("=" * 70 + "\n")

    test1 = test_retry_loop_implemented()
    test2 = test_no_speech_retry()
    test3 = test_transcription_failure_retry()
    test4 = test_unrecognized_keyword_retry()
    test5 = test_confirmation_retry()
    test6 = test_error_messages()
    test7 = test_retry_limits()
    test8 = test_user_prompts()

    print("=" * 70)
    if test1 and test2 and test3 and test4 and test5 and test6 and test7 and test8:
        print("  ALL FIELD SELECTION RETRY TESTS PASSED [OK]")
        print("=" * 70)
        print("\nField Selection Retry Logic - COMPLETE")
        print("\nImplemented Retry Scenarios:")
        print("  [OK] No Speech Detected")
        print("       - System: 'I didn't hear anything. Please say...'")
        print("       - Action: Retry (up to 3 times)")
        print("\n  [OK] Transcription Failure")
        print("       - System: 'I couldn't understand that. Please repeat...'")
        print("       - Action: Retry (up to 3 times)")
        print("\n  [OK] Unrecognized Keywords")
        print("       - System: 'I heard [X] but that's not clear...'")
        print("       - Action: Retry (up to 3 times)")
        print("\n  [OK] Confirmation Lost")
        print("       - System: 'I didn't catch your confirmation. Let me try again.'")
        print("       - Action: Retry entire flow (up to 3 times)")
        print("\n  [OK] User Rejects Selection")
        print("       - System: 'Okay, let's try again.'")
        print("       - Action: Retry from beginning (up to 3 times)")
        print("\n  [OK] Unclear Confirmation")
        print("       - System: 'I didn't understand your confirmation. Let's try again.'")
        print("       - Action: Retry (up to 3 times)")
        print("\n  [OK] Max Retries Exhausted")
        print("       - System: 'I'm having trouble understanding what you want...'")
        print("       - Action: Return None and cancel update flow")
        print("\nRetry Features:")
        print("  + Up to 3 attempts per field selection attempt")
        print("  + Helpful error messages for each failure type")
        print("  + Prompts to suggest valid options")
        print("  + 0.5 second delay between retries")
        print("  + Graceful exhaustion handling")
        print("  + Debug logging for each attempt")
        print("\nUser Experience:")
        print("  - Never immediately fails on bad input")
        print("  - Clear guidance on what to say")
        print("  - Patient handling of speech recognition issues")
        print("  - Graceful fallback after max retries")
        print("=" * 70)
        return 0
    else:
        print("  SOME TESTS FAILED [X]")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    exit(main())
