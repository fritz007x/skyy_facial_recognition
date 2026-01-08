#!/usr/bin/env python3
"""
Test script for LLM Confirmation Parser.

Verifies that Gemma 3-based confirmation parsing works correctly
and gracefully falls back to rule-based parsing when Ollama is unavailable.

Usage:
    python test_llm_confirmation.py
"""

import sys
from modules.llm_confirmation_parser import LLMConfirmationParser


def test_llm_parsing():
    """Test LLM-based confirmation parsing with various inputs."""

    print("=" * 80)
    print("LLM CONFIRMATION PARSER TEST")
    print("=" * 80)
    print()

    # Initialize parser with LLM enabled
    print("Initializing LLM Confirmation Parser...")
    parser = LLMConfirmationParser(
        ollama_host="http://localhost:11434",
        model_name="gemma3:4b",
        enable_llm=True,
        timeout_sec=2.0,
        temperature=0.1,
        max_tokens=10
    )
    print(f"Parser initialized: {parser}")
    print()

    # Test cases (response, context, expected_result)
    test_cases = [
        # Clear positive responses
        ("Yes", "Is that correct?", True),
        ("Yeah", "Is that correct?", True),
        ("Sure thing", "Is that correct?", True),
        ("Absolutely", "Proceed with deletion?", True),
        ("Go ahead", "Do you want to continue?", True),
        ("That's right", "Is your name John?", True),

        # Clear negative responses
        ("No", "Is that correct?", False),
        ("Nope", "Is that correct?", False),
        ("Not really", "Is that correct?", False),
        ("I don't think so", "Is your name John?", False),
        ("Try again", "Is that correct?", False),
        ("Cancel that", "Proceed with deletion?", False),

        # Ambiguous/unclear responses
        ("Maybe", "Is that correct?", None),
        ("I'm not sure", "Is that correct?", None),
        ("Hmm", "Is that correct?", None),
        ("What?", "Is that correct?", None),
        ("Possibly", "Is that correct?", None),

        # Natural language variations
        ("Of course", "Is that correct?", True),
        ("Definitely", "Proceed?", True),
        ("Not at all", "Is that correct?", False),
        ("Forget it", "Proceed with deletion?", False),
    ]

    print("Running test cases...")
    print("-" * 80)

    passed = 0
    failed = 0

    for i, (response, context, expected) in enumerate(test_cases, 1):
        result = parser.parse_confirmation(response, context)

        status = "PASS" if result == expected else "FAIL"
        symbol = "[OK]" if status == "PASS" else "[X]"

        if result == expected:
            passed += 1
        else:
            failed += 1

        print(f"{symbol} Test {i:2d}: '{response:20s}' -> {str(result):5s} (expected: {str(expected):5s})")

    print("-" * 80)
    print()

    # Print statistics
    stats = parser.get_stats()
    print("PARSER STATISTICS:")
    print(f"  Total tests:        {stats['total']}")
    print(f"  LLM successful:     {stats['llm_success']}")
    print(f"  LLM failed:         {stats['llm_failure']}")
    print(f"  Fallback used:      {stats['fallback']}")
    print(f"  LLM success rate:   {stats['llm_success_rate']:.1f}%")
    print()

    # Print test results
    total = passed + failed
    pass_rate = (passed / total * 100) if total > 0 else 0

    print("TEST RESULTS:")
    print(f"  Passed:    {passed}/{total}")
    print(f"  Failed:    {failed}/{total}")
    print(f"  Pass rate: {pass_rate:.1f}%")
    print()

    if failed == 0:
        print("SUCCESS: All tests passed!")
        return 0
    else:
        print("FAILURE: Some tests failed.")
        return 1


def test_fallback_parsing():
    """Test fallback to rule-based parsing when Ollama is unavailable."""

    print("=" * 80)
    print("FALLBACK PARSING TEST (Ollama unavailable)")
    print("=" * 80)
    print()

    # Initialize parser with LLM disabled
    print("Initializing parser with LLM disabled...")
    parser = LLMConfirmationParser(
        enable_llm=False  # Force fallback to rule-based parsing
    )
    print(f"Parser initialized: {parser}")
    print()

    # Test rule-based parsing
    test_cases = [
        ("yes", None, True),
        ("yeah", None, True),
        ("correct", None, True),
        ("no", None, False),
        ("nope", None, False),
        ("wrong", None, False),
        ("maybe", None, None),
        ("hmm", None, None),
    ]

    print("Running fallback test cases...")
    print("-" * 80)

    passed = 0
    failed = 0

    for i, (response, context, expected) in enumerate(test_cases, 1):
        result = parser.parse_confirmation(response, context)

        status = "PASS" if result == expected else "FAIL"
        symbol = "[OK]" if status == "PASS" else "[X]"

        if result == expected:
            passed += 1
        else:
            failed += 1

        print(f"{symbol} Test {i}: '{response:15s}' -> {str(result):5s} (expected: {str(expected):5s})")

    print("-" * 80)
    print()

    # Print statistics
    stats = parser.get_stats()
    print("PARSER STATISTICS:")
    print(f"  Fallback used:  {stats['fallback']} (100% as expected)")
    print()

    # Print test results
    total = passed + failed
    pass_rate = (passed / total * 100) if total > 0 else 0

    print("TEST RESULTS:")
    print(f"  Passed:    {passed}/{total}")
    print(f"  Failed:    {failed}/{total}")
    print(f"  Pass rate: {pass_rate:.1f}%")
    print()

    if failed == 0:
        print("SUCCESS: All fallback tests passed!")
        return 0
    else:
        print("FAILURE: Some tests failed.")
        return 1


def test_invalid_ollama_host():
    """Test graceful degradation when Ollama host is unreachable."""

    print("=" * 80)
    print("GRACEFUL DEGRADATION TEST (Invalid Ollama host)")
    print("=" * 80)
    print()

    # Initialize parser with invalid Ollama host
    print("Initializing parser with invalid Ollama host...")
    parser = LLMConfirmationParser(
        ollama_host="http://invalid-host:11434",
        enable_llm=True,
        timeout_sec=1.0  # Short timeout for faster testing
    )
    print(f"Parser initialized: {parser}")
    print()

    # Test that it falls back to rule-based parsing
    print("Testing automatic fallback to rule-based parsing...")
    print("-" * 80)

    test_cases = [
        ("yes", "Is that correct?", True),
        ("no", "Is that correct?", False),
    ]

    passed = 0
    failed = 0

    for i, (response, context, expected) in enumerate(test_cases, 1):
        result = parser.parse_confirmation(response, context)

        status = "PASS" if result == expected else "FAIL"
        symbol = "[OK]" if status == "PASS" else "[X]"

        if result == expected:
            passed += 1
        else:
            failed += 1

        print(f"{symbol} Test {i}: '{response}' -> {str(result):5s} (expected: {str(expected):5s})")

    print("-" * 80)
    print()

    # Print statistics
    stats = parser.get_stats()
    print("PARSER STATISTICS:")
    print(f"  LLM failures:   {stats['llm_failure']} (should be > 0)")
    print(f"  Fallback used:  {stats['fallback']} (should be > 0)")
    print()

    if stats['llm_failure'] > 0 and stats['fallback'] > 0:
        print("SUCCESS: Parser gracefully degraded to fallback!")
        return 0
    else:
        print("FAILURE: Parser did not degrade gracefully.")
        return 1


def main():
    """Run all tests."""

    print()
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "  LLM CONFIRMATION PARSER - COMPREHENSIVE TEST SUITE".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "═" * 78 + "╝")
    print()

    results = []

    # Test 1: LLM parsing (requires Ollama running)
    print("TEST 1: LLM-Based Parsing")
    print()
    try:
        result = test_llm_parsing()
        results.append(("LLM Parsing", result))
    except Exception as e:
        print(f"ERROR: {e}")
        results.append(("LLM Parsing", 1))

    print()
    print()

    # Test 2: Fallback parsing
    print("TEST 2: Fallback Rule-Based Parsing")
    print()
    try:
        result = test_fallback_parsing()
        results.append(("Fallback Parsing", result))
    except Exception as e:
        print(f"ERROR: {e}")
        results.append(("Fallback Parsing", 1))

    print()
    print()

    # Test 3: Graceful degradation
    print("TEST 3: Graceful Degradation")
    print()
    try:
        result = test_invalid_ollama_host()
        results.append(("Graceful Degradation", result))
    except Exception as e:
        print(f"ERROR: {e}")
        results.append(("Graceful Degradation", 1))

    print()
    print()

    # Summary
    print("=" * 80)
    print("OVERALL SUMMARY")
    print("=" * 80)

    for test_name, result in results:
        status = "PASS" if result == 0 else "FAIL"
        symbol = "[OK]" if result == 0 else "[X]"
        print(f"{symbol} {test_name:30s}: {status}")

    print("=" * 80)

    # Determine overall result
    overall = 0 if all(r == 0 for _, r in results) else 1

    if overall == 0:
        print()
        print("SUCCESS: All tests passed!")
        print()
    else:
        print()
        print("FAILURE: Some tests failed.")
        print()

    return overall


if __name__ == "__main__":
    sys.exit(main())
