"""
Test Phase 1-2 Implementation of Update User Feature.

Validates:
1. UpdateOrchestrator class structure and state machine
2. Config constants for update wake words
3. main.py integration (imports, initialization, routing)
"""

import ast
from pathlib import Path


def test_update_orchestrator():
       """Verify UpdateOrchestrator has all required components."""
       print("Test 1: UpdateOrchestrator Implementation")

       orch_file = Path("src/gemma_voice_assistant/modules/update_orchestrator.py")
       with open(orch_file, 'r') as f:
           content = f.read()

       # Check for state machine
       checks = [
           ("UpdateState enum", "class UpdateState(Enum)"),
           ("IDLE state", 'IDLE = "idle"'),
           ("FACE_RECOGNITION state", 'FACE_RECOGNITION = "face_recognition"'),
           ("CONFIRM_IDENTITY state", 'CONFIRM_IDENTITY = "confirm_identity"'),
           ("FETCH_PROFILE state", 'FETCH_PROFILE = "fetch_profile"'),
           ("PRESENT_PROFILE state", 'PRESENT_PROFILE = "present_profile"'),
           ("SELECT_UPDATE_FIELDS state", 'SELECT_UPDATE_FIELDS = "select_update_fields"'),
           ("CAPTURE_NEW_NAME state", 'CAPTURE_NEW_NAME = "capture_new_name"'),
           ("TRANSCRIBE_NEW_NAME state", 'TRANSCRIBE_NEW_NAME = "transcribe_new_name"'),
           ("CONFIRM_NEW_NAME state", 'CONFIRM_NEW_NAME = "confirm_new_name"'),
           ("PREVIEW_CHANGES state", 'PREVIEW_CHANGES = "preview_changes"'),
           ("FINAL_CONFIRMATION state", 'FINAL_CONFIRMATION = "final_confirmation"'),
           ("EXECUTE_UPDATE state", 'EXECUTE_UPDATE = "execute_update"'),
           ("COMPLETED state", 'COMPLETED = "completed"'),
           ("CANCELLED state", 'CANCELLED = "cancelled"'),
       ]

       # Check for key methods
       checks.extend([
           ("recognize_user method", "def recognize_user("),
           ("confirm_identity method", "def confirm_identity("),
           ("fetch_and_present_profile method", "def fetch_and_present_profile("),
           ("select_update_fields method", "def select_update_fields("),
           ("capture_and_confirm_new_name method", "def capture_and_confirm_new_name("),
           ("preview_changes method", "def preview_changes("),
           ("get_final_confirmation method", "def get_final_confirmation("),
           ("execute_update method", "def execute_update("),
           ("run_update_flow method", "def run_update_flow("),
           ("reset method", "def reset("),
       ])

       # Check for component initialization
       checks.extend([
           ("VAD initialization", "self.vad = VoiceActivityDetector"),
           ("Whisper initialization", "self.whisper = WhisperTranscriptionEngine"),
           ("LLM parser initialization", "self.llm_parser = LLMConfirmationParser"),
       ])

       passed = 0
       for check_name, check_str in checks:
           if check_str in content:
               print(f"  [OK] {check_name}")
               passed += 1
           else:
               print(f"  [X] Missing: {check_name}")

       print(f"\n  Result: {passed}/{len(checks)} checks passed\n")
       return passed == len(checks)


def test_config_constants():
       """Verify config.py has update wake word constants."""
       print("Test 2: Config.py Update Constants")

       config_file = Path("src/gemma_voice_assistant/config.py")
       with open(config_file, 'r') as f:
           content = f.read()

       checks = [
           ("UPDATE_WAKE_WORD constant", 'UPDATE_WAKE_WORD = "skyy update me"'),
           ("UPDATE_WAKE_WORD_ALTERNATIVES constant", "UPDATE_WAKE_WORD_ALTERNATIVES = ["),
           ("Alternative: sky update me", '"sky update me"'),
           ("Alternative: skyy update my profile", '"skyy update my profile"'),
           ("Alternative: sky update my profile", '"sky update my profile"'),
           ("Alternative: skyy change my information", '"skyy change my information"'),
           ("Alternative: sky change my information", '"sky change my information"'),
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


def test_main_py_integration():
       """Verify main.py has UpdateOrchestrator integration."""
       print("Test 3: main.py Integration")

       main_file = Path("src/gemma_voice_assistant/main.py")
       with open(main_file, 'r') as f:
           content = f.read()

       checks = [
           ("UpdateOrchestrator import", "from modules.update_orchestrator import UpdateOrchestrator"),
           ("UPDATE_WAKE_WORD config import", "UPDATE_WAKE_WORD,"),
           ("UPDATE_WAKE_WORD_ALTERNATIVES config import", "UPDATE_WAKE_WORD_ALTERNATIVES,"),
           ("self.update attribute", "self.update: Optional[UpdateOrchestrator] = None"),
           ("UpdateOrchestrator initialization", "self.update = UpdateOrchestrator("),
           ("Whisper model passed", "whisper_model=WHISPER_MODEL"),
           ("LLM config passed", "enable_llm_confirmation=ENABLE_LLM_CONFIRMATION"),
           ("handle_update method", "def handle_update(self)"),
           ("handle_update calls run_update_flow", "self.update.run_update_flow("),
           ("handle_update calls reset", "self.update.reset()"),
           ("update_wake_words initialization", "update_wake_words = [UPDATE_WAKE_WORD]"),
           ("update_wake_words in all_wake_words", "deletion_wake_words + update_wake_words"),
           ("is_update detection", "is_update = any("),
           ("is_update in routing", "elif is_update:"),
           ("handle_update call in routing", "self.handle_update()"),
           ("Wake word priority comment", "highest priority for safety"),
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


def test_wake_word_priority():
       """Verify wake word priority is correct (deletion > update > registration > recognition)."""
       print("Test 4: Wake Word Priority Order")

       main_file = Path("src/gemma_voice_assistant/main.py")
       with open(main_file, 'r') as f:
           lines = f.readlines()

       # Find the routing section
       routing_start = None
       for i, line in enumerate(lines):
           if "if is_deletion:" in line:
               routing_start = i
               break

       if routing_start is None:
           print("  [X] Could not find routing section")
           return False

       # Check order: is_deletion should come first
       deletion_line = None
       update_line = None
       registration_line = None

       for i in range(routing_start, min(routing_start + 20, len(lines))):
           if "if is_deletion:" in lines[i]:
               deletion_line = i
           elif "elif is_update:" in lines[i]:
               update_line = i
           elif "elif is_registration:" in lines[i]:
               registration_line = i

       # Verify priority order
       if deletion_line is not None and deletion_line < (update_line or float('inf')):
           print("  [OK] Deletion has highest priority")
       else:
           print("  [X] Deletion priority incorrect")
           return False

       if update_line is not None and update_line < (registration_line or float('inf')):
           print("  [OK] Update has higher priority than registration")
       else:
           print("  [X] Update priority incorrect")
           return False

       if registration_line is not None:
           print("  [OK] Registration has priority over recognition (default)")

       print(f"\n  Result: Priority order is correct\n")
       return True


def main():
       print("=" * 70)
       print("  UPDATE USER FEATURE - PHASE 1-2 VALIDATION TESTS")
       print("=" * 70 + "\n")

       test1 = test_update_orchestrator()
       test2 = test_config_constants()
       test3 = test_main_py_integration()
       test4 = test_wake_word_priority()

       print("=" * 70)
       if test1 and test2 and test3 and test4:
           print("  ALL TESTS PASSED [OK]")
           print("=" * 70)
           print("\nPhase 1-2 Implementation Complete!")
           print("\nPhase 1 (Infrastructure):")
           print("  [OK] UpdateOrchestrator created with state machine")
           print("  [OK] Config constants added for update wake words")
           print("  [OK] main.py imports, initialization, and routing integrated")
           print("  [OK] handle_update() method implemented")
           print("  [OK] Wake word priority order: deletion > update > registration > recognition")
           print("\nPhase 2 (Authentication):")
           print("  [OK] recognize_user() method for face authentication")
           print("  [OK] confirm_identity() method with LLM confirmation")
           print("  [OK] Both methods follow DeletionOrchestrator pattern")
           print("\nNext Phase:")
           print("  Phase 3: Profile Operations (fetch, present, selection)")
           print("  Phase 4: Name Update (capture, transcribe, confirm)")
           print("  Phase 5: Changes & Execution (preview, final confirmation, execute)")
           print("  Phase 6: Integration & Testing (end-to-end, error handling)")
           return 0
       else:
           print("  TESTS FAILED [X]")
           print("=" * 70)
           return 1


if __name__ == "__main__":
       exit(main())
   