"""
LLM Confirmation Parser - Smart yes/no confirmation parsing using Gemma 3.

Provides context-aware natural language understanding for user confirmations,
replacing rigid keyword-based parsing with LLM-powered intent detection.

Key Features:
- Uses Gemma 3 via Ollama for natural language understanding
- Context-aware parsing (passes the question that was asked)
- Graceful fallback to rule-based parsing if Ollama is unavailable
- Low latency with optimized parameters
- Synchronous API (no async/await)
"""

import requests
import json
from typing import Optional


class LLMConfirmationParser:
    """
    Parse user confirmations using Gemma 3 LLM with fallback to rule-based parsing.

    This parser understands natural language confirmations like:
    - "Sure thing", "Absolutely", "Go ahead" -> YES
    - "Not really", "I don't think so", "Maybe later" -> NO
    - "I'm not sure", "Hmm", "What?" -> UNCLEAR (None)

    If Ollama is unavailable, falls back to simple keyword matching.
    """

    def __init__(
        self,
        ollama_host: str = "http://localhost:11434",
        model_name: str = "gemma3:4b",
        enable_llm: bool = True,
        timeout_sec: float = 2.0,
        temperature: float = 0.1,
        max_tokens: int = 10
    ):
        """
        Initialize LLM Confirmation Parser.

        Args:
            ollama_host: Ollama API endpoint (default: http://localhost:11434)
            model_name: Ollama model name (default: gemma3:4b)
            enable_llm: Whether to use LLM parsing (default: True)
            timeout_sec: Request timeout in seconds (default: 2.0)
            temperature: LLM temperature for consistency (default: 0.1, low for deterministic output)
            max_tokens: Maximum tokens to generate (default: 10, just need "YES", "NO", or "UNCLEAR")
        """
        self.ollama_host = ollama_host.rstrip('/')
        self.model_name = model_name
        self.enable_llm = enable_llm
        self.timeout_sec = timeout_sec
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Stats tracking
        self.llm_success_count = 0
        self.llm_failure_count = 0
        self.fallback_count = 0

    def parse_confirmation(
        self,
        user_response: str,
        question_context: Optional[str] = None
    ) -> Optional[bool]:
        """
        Parse user confirmation with LLM-based natural language understanding.

        Args:
            user_response: User's transcribed response to parse
            question_context: The question that was asked (helps LLM understand context)

        Returns:
            True: User confirmed (yes)
            False: User declined (no)
            None: Unclear/ambiguous response

        Example:
            >>> parser = LLMConfirmationParser()
            >>> parser.parse_confirmation("Sure thing!", "Is your name John?")
            True
            >>> parser.parse_confirmation("Not really", "Do you want to proceed?")
            False
            >>> parser.parse_confirmation("Maybe later", "Confirm deletion?")
            None
        """
        if not user_response or not user_response.strip():
            return None

        # Try LLM parsing first if enabled
        if self.enable_llm:
            llm_result = self._parse_with_llm(user_response, question_context)
            if llm_result is not None:
                self.llm_success_count += 1
                return llm_result
            else:
                self.llm_failure_count += 1
                # Fall through to rule-based parsing

        # Fallback to rule-based parsing
        self.fallback_count += 1
        return self._parse_with_rules(user_response)

    def _parse_with_llm(
        self,
        user_response: str,
        question_context: Optional[str] = None
    ) -> Optional[bool]:
        """
        Parse confirmation using Gemma 3 LLM via Ollama.

        Args:
            user_response: User's response text
            question_context: Question that was asked

        Returns:
            True for yes, False for no, None if unclear or error
        """
        try:
            # Build context-aware prompt
            prompt = self._build_prompt(user_response, question_context)

            # Call Ollama API
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": self.max_tokens,
                        "stop": ["\n", ".", ","]  # Stop at punctuation for faster response
                    }
                },
                timeout=self.timeout_sec
            )

            if response.status_code != 200:
                print(f"[LLM Parser] Ollama request failed: {response.status_code}", flush=True)
                return None

            # Parse response
            result = response.json()
            llm_output = result.get("response", "").strip().upper()

            # Extract YES/NO/UNCLEAR from LLM output
            if "YES" in llm_output:
                print(f"[LLM Parser] Parsed as YES: '{user_response}'", flush=True)
                return True
            elif "NO" in llm_output:
                print(f"[LLM Parser] Parsed as NO: '{user_response}'", flush=True)
                return False
            elif "UNCLEAR" in llm_output:
                print(f"[LLM Parser] Parsed as UNCLEAR: '{user_response}'", flush=True)
                return None
            else:
                print(f"[LLM Parser] Unexpected LLM output: '{llm_output}'", flush=True)
                return None

        except requests.Timeout:
            print(f"[LLM Parser] Ollama request timed out after {self.timeout_sec}s", flush=True)
            return None
        except requests.ConnectionError:
            print("[LLM Parser] Cannot connect to Ollama - is it running?", flush=True)
            return None
        except Exception as e:
            print(f"[LLM Parser] Unexpected error: {e}", flush=True)
            return None

    def _build_prompt(self, user_response: str, question_context: Optional[str] = None) -> str:
        """
        Build LLM prompt for confirmation parsing.

        Args:
            user_response: User's response
            question_context: Question that was asked

        Returns:
            Formatted prompt string
        """
        if question_context:
            # Context-aware prompt
            prompt = f"""You are analyzing a user's response to a yes/no question.

Question: {question_context}
User's response: {user_response}

Classify the user's intent as one of:
- YES: User is confirming, agreeing, or saying yes
- NO: User is declining, disagreeing, or saying no
- UNCLEAR: Response is ambiguous or doesn't clearly indicate yes or no

Respond with ONLY one word: YES, NO, or UNCLEAR."""
        else:
            # Generic prompt without context
            prompt = f"""Classify this user response as YES (confirming), NO (declining), or UNCLEAR (ambiguous):

User said: {user_response}

Respond with ONLY one word: YES, NO, or UNCLEAR."""

        return prompt

    def _parse_with_rules(self, user_response: str) -> Optional[bool]:
        """
        Fallback rule-based confirmation parsing.

        This is the original keyword-based approach, used when LLM is unavailable.

        Args:
            user_response: User's response text

        Returns:
            True for yes, False for no, None if unclear
        """
        text_lower = user_response.lower().strip()

        # Positive responses
        positive_words = [
            "yes", "yeah", "yep", "yup",
            "correct", "right", "sure", "confirm",
            "okay", "ok", "fine", "absolutely",
            "definitely", "indeed", "affirmative"
        ]

        # Negative responses
        negative_words = [
            "no", "nope", "nah",
            "wrong", "incorrect", "cancel", "stop",
            "negative", "not"
        ]

        # Check positive
        if any(word in text_lower for word in positive_words):
            print(f"[Rule Parser] Parsed as YES: '{user_response}'", flush=True)
            return True

        # Check negative
        if any(word in text_lower for word in negative_words):
            print(f"[Rule Parser] Parsed as NO: '{user_response}'", flush=True)
            return False

        # Unclear
        print(f"[Rule Parser] Parsed as UNCLEAR: '{user_response}'", flush=True)
        return None

    def get_stats(self) -> dict:
        """
        Get parser usage statistics.

        Returns:
            Dictionary with parsing statistics
        """
        total = self.llm_success_count + self.llm_failure_count + self.fallback_count

        return {
            "llm_success": self.llm_success_count,
            "llm_failure": self.llm_failure_count,
            "fallback": self.fallback_count,
            "total": total,
            "llm_success_rate": (self.llm_success_count / total * 100) if total > 0 else 0.0
        }

    def reset_stats(self) -> None:
        """Reset parser statistics."""
        self.llm_success_count = 0
        self.llm_failure_count = 0
        self.fallback_count = 0

    def __repr__(self) -> str:
        """String representation for debugging."""
        stats = self.get_stats()
        return (
            f"LLMConfirmationParser("
            f"model={self.model_name}, "
            f"enabled={self.enable_llm}, "
            f"llm_success_rate={stats['llm_success_rate']:.1f}%)"
        )


# Convenience function for quick usage
def parse_confirmation(
    user_response: str,
    question_context: Optional[str] = None,
    ollama_host: str = "http://localhost:11434",
    model_name: str = "gemma3:4b",
    enable_llm: bool = True
) -> Optional[bool]:
    """
    Convenience function to parse confirmation without creating parser instance.

    Args:
        user_response: User's response text
        question_context: Question that was asked
        ollama_host: Ollama API endpoint
        model_name: Ollama model name
        enable_llm: Whether to use LLM parsing

    Returns:
        True for yes, False for no, None if unclear

    Example:
        >>> from modules.llm_confirmation_parser import parse_confirmation
        >>> parse_confirmation("Sure thing!", "Is that correct?")
        True
    """
    parser = LLMConfirmationParser(
        ollama_host=ollama_host,
        model_name=model_name,
        enable_llm=enable_llm
    )
    return parser.parse_confirmation(user_response, question_context)
