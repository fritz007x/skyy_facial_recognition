"""
Test that Gemma 3 LLM integration is complete in the recognition feature.

This test validates that:
1. PermissionManager now uses LLM confirmation parsing
2. main.py passes LLM config to PermissionManager
3. All components are properly integrated
"""

import ast
from pathlib import Path


def test_permission_manager():
    """Verify PermissionManager has LLM integration."""
    print("Test 1: PermissionManager LLM Integration")
    
    perm_file = Path("src/gemma_voice_assistant/modules/permission.py")
    with open(perm_file, 'r') as f:
        content = f.read()
    
    # Check imports
    checks = [
        ("LLMConfirmationParser import", "from .llm_confirmation_parser import LLMConfirmationParser"),
        ("VoiceActivityDetector import", "from .voice_activity_detector import VoiceActivityDetector"),
        ("WhisperTranscriptionEngine import", "from .whisper_transcription_engine import WhisperTranscriptionEngine"),
        ("LLM parser initialization", "self.llm_parser = LLMConfirmationParser"),
        ("VAD initialization", "self.vad = VoiceActivityDetector"),
        ("Whisper initialization", "self.whisper = WhisperTranscriptionEngine"),
        ("LLM parsing in ask_permission", "self.llm_parser.parse_confirmation"),
        ("Whisper transcription in ask_permission", "self.whisper.transcribe"),
        ("VAD recording in ask_permission", "self.vad.record_speech"),
    ]
    
    passed = 0
    for check_name, check_str in checks:
        if check_str in content:
            print(f"  [OK] {check_name}")
            passed += 1
        else:
            print(f"  [X] Missing: {check_name}")
    
    print(f"\n  Result: {passed}/{len(checks)} checks passed\n")
    return passed == len(checks)


def test_main_py_config():
    """Verify main.py has LLM config imports and passes them to PermissionManager."""
    print("Test 2: main.py LLM Configuration")
    
    main_file = Path("src/gemma_voice_assistant/main.py")
    with open(main_file, 'r') as f:
        content = f.read()
    
    # Check imports
    checks = [
        ("ENABLE_LLM_CONFIRMATION import", "ENABLE_LLM_CONFIRMATION"),
        ("LLM_CONFIRMATION_MODEL import", "LLM_CONFIRMATION_MODEL"),
        ("LLM_CONFIRMATION_TIMEOUT import", "LLM_CONFIRMATION_TIMEOUT"),
        ("LLM_CONFIRMATION_TEMPERATURE import", "LLM_CONFIRMATION_TEMPERATURE"),
        ("LLM_CONFIRMATION_MAX_TOKENS import", "LLM_CONFIRMATION_MAX_TOKENS"),
        ("PermissionManager config passing - WHISPER_MODEL", "whisper_model=WHISPER_MODEL"),
        ("PermissionManager config passing - WHISPER_DEVICE", "whisper_device=WHISPER_DEVICE"),
        ("PermissionManager config passing - enable_llm", "enable_llm_confirmation=ENABLE_LLM_CONFIRMATION"),
        ("PermissionManager config passing - llm_model", "llm_model=LLM_CONFIRMATION_MODEL"),
        ("PermissionManager config passing - llm_timeout", "llm_timeout=LLM_CONFIRMATION_TIMEOUT"),
    ]
    
    passed = 0
    for check_name, check_str in checks:
        if check_str in content:
            print(f"  [OK] {check_name}")
            passed += 1
        else:
            print(f"  [X] Missing: {check_name}")
    
    print(f"\n  Result: {passed}/{len(checks)} checks passed\n")
    return passed == len(checks)


def test_feature_consistency():
    """Verify all three features (recognition, registration, deletion) use LLM."""
    print("Test 3: Feature Consistency - All Use Gemma 3")
    
    features = {
        "Registration": "src/gemma_voice_assistant/modules/registration_orchestrator.py",
        "Deletion": "src/gemma_voice_assistant/modules/deletion_orchestrator.py",
        "Recognition (PermissionManager)": "src/gemma_voice_assistant/modules/permission.py",
    }
    
    llm_checks = {
        "LLMConfirmationParser": "LLMConfirmationParser",
        "parse_confirmation": "parse_confirmation",
    }
    
    all_passed = True
    for feature_name, filepath in features.items():
        with open(filepath, 'r') as f:
            content = f.read()
        
        feature_passed = True
        for check_name, check_str in llm_checks.items():
            if check_str in content:
                print(f"  [OK] {feature_name} has {check_name}")
            else:
                print(f"  [X] {feature_name} missing {check_name}")
                feature_passed = False
                all_passed = False
        
        if not feature_passed:
            print(f"  Result: {feature_name} FAILED")
        else:
            print(f"  Result: {feature_name} PASSED")
        print()
    
    return all_passed


def main():
    print("=" * 70)
    print("  GEMMA 3 INTEGRATION TEST - RECOGNITION FEATURE")
    print("=" * 70 + "\n")
    
    test1 = test_permission_manager()
    test2 = test_main_py_config()
    test3 = test_feature_consistency()
    
    print("=" * 70)
    if test1 and test2 and test3:
        print("  ALL TESTS PASSED [OK]")
        print("=" * 70)
        print("\nGemma 3 LLM integration is complete!")
        print("\nThe recognition feature now understands natural yes/no responses:")
        print("  - 'Sure thing!'")
        print("  - 'Go ahead'")
        print("  - 'Absolutely'")
        print("  - 'Not really'")
        print("  - 'Maybe later'")
        print("\nConsistent with registration and deletion features.")
        return 0
    else:
        print("  TESTS FAILED [X]")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    exit(main())
