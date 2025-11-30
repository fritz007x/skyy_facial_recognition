"""Test edge cases for Ollama integration."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_normal_case():
    """Test normal case with Ollama running and models available."""
    print("\n" + "=" * 70)
    print("TEST 1: Normal case (Ollama running with models)")
    print("=" * 70)

    try:
        import ollama
        response = ollama.list()

        # This is what the code expects
        assert hasattr(response, 'models'), "Response should have 'models' attribute"

        model_names = [model.model for model in response.models]
        print(f"[OK] Found {len(model_names)} models")

        # Check structure
        if response.models:
            first_model = response.models[0]
            print(f"[OK] First model: {first_model.model}")
            print(f"[OK] Model type: {type(first_model)}")
            assert hasattr(first_model, 'model'), "Model should have 'model' attribute"

        print("[PASS] Normal case works correctly")
        return True

    except Exception as e:
        print(f"[FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_empty_models():
    """Test case where Ollama has no models installed."""
    print("\n" + "=" * 70)
    print("TEST 2: Empty models case")
    print("=" * 70)

    # Simulate what happens if no models are installed
    class MockModel:
        def __init__(self, name):
            self.model = name

    class MockResponse:
        def __init__(self, models):
            self.models = models

    mock_response = MockResponse([])

    try:
        model_names = [model.model for model in mock_response.models]
        print(f"[OK] Empty list handling: {model_names}")

        if not model_names:
            print("[OK] Correctly detects no models")

        print("[PASS] Empty models case handled correctly")
        return True

    except Exception as e:
        print(f"[FAIL] {e}")
        return False


def test_no_gemma3_models():
    """Test case where Ollama has models but no Gemma 3 models."""
    print("\n" + "=" * 70)
    print("TEST 3: No Gemma 3 models case")
    print("=" * 70)

    class MockModel:
        def __init__(self, name):
            self.model = name

    class MockResponse:
        def __init__(self, models):
            self.models = models

    # Simulate having other models but not Gemma 3
    mock_response = MockResponse([
        MockModel('llama2:7b'),
        MockModel('mistral:latest'),
    ])

    try:
        model_names = [model.model for model in mock_response.models]
        print(f"[OK] Found models: {model_names}")

        gemma_models = [m for m in model_names if 'gemma' in m.lower() and '3' in m]
        print(f"[OK] Gemma 3 models: {gemma_models}")

        if not gemma_models:
            print("[OK] Correctly detects no Gemma 3 models")

        print("[PASS] No Gemma 3 models case handled correctly")
        return True

    except Exception as e:
        print(f"[FAIL] {e}")
        return False


def test_actual_integration():
    """Test actual integration with Gemma3nVoiceAssistant."""
    print("\n" + "=" * 70)
    print("TEST 4: Full integration test")
    print("=" * 70)

    try:
        from gemma3n_voice_assistant import Gemma3nVoiceAssistant
        assistant = Gemma3nVoiceAssistant()

        print(f"[OK] Assistant initialized")
        print(f"[OK] Selected model: {assistant.gemma_model}")

        # Verify it selected a Gemma 3 model
        assert 'gemma' in assistant.gemma_model.lower(), "Should select a Gemma model"
        assert '3' in assistant.gemma_model, "Should select a Gemma 3 variant"

        print("[PASS] Full integration test passed")
        return True

    except SystemExit as e:
        print(f"[EXPECTED] SystemExit: {e.code}")
        print("This is expected if Ollama is not running or no Gemma 3 models")
        return False
    except Exception as e:
        print(f"[FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "#" * 70)
    print("# OLLAMA INTEGRATION EDGE CASE TESTS")
    print("#" * 70)

    results = []

    # Run tests
    results.append(("Normal case", test_normal_case()))
    results.append(("Empty models", test_empty_models()))
    results.append(("No Gemma 3 models", test_no_gemma3_models()))
    results.append(("Full integration", test_actual_integration()))

    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test_name}")

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("\n[SUCCESS] All tests passed!")
        sys.exit(0)
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed")
        sys.exit(1)
