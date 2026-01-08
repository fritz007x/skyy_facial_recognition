#!/usr/bin/env python3
"""
OAuth 2.1 Test Script

Comprehensive test suite for OAuth 2.1 implementation.
Tests client creation, token generation, validation, and MCP tool authentication.
"""

import sys
import time
from pathlib import Path
import json

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Import with absolute imports
import oauth_config as oauth_config_module
import oauth_middleware

oauth_config = oauth_config_module.oauth_config
require_auth = oauth_middleware.require_auth
AuthenticationError = oauth_middleware.AuthenticationError

# ANSI color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text:^70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 70}{Colors.RESET}\n")


def print_test(test_name):
    """Print test name"""
    print(f"{Colors.BLUE}> {test_name}{Colors.RESET}")


def print_success(message):
    """Print success message"""
    print(f"{Colors.GREEN}  [OK] {message}{Colors.RESET}")


def print_error(message):
    """Print error message"""
    print(f"{Colors.RED}  [X] {message}{Colors.RESET}")


def print_info(message):
    """Print info message"""
    print(f"{Colors.YELLOW}  [i] {message}{Colors.RESET}")


class OAuthTester:
    """Test suite for OAuth 2.1 implementation"""

    def __init__(self):
        self.test_client_id = None
        self.test_client_secret = None
        self.test_token = None
        self.passed_tests = 0
        self.failed_tests = 0
        self.total_tests = 0

    def run_all_tests(self):
        """Run all OAuth tests"""
        print_header("OAuth 2.1 Test Suite")

        # Test 1: RSA Key Generation
        self.test_rsa_keys()

        # Test 2: Client Creation
        self.test_client_creation()

        # Test 3: Client Verification
        self.test_client_verification()

        # Test 4: Token Generation
        self.test_token_generation()

        # Test 5: Token Validation
        self.test_token_validation()

        # Test 6: Invalid Token Handling
        self.test_invalid_token()

        # Test 7: Expired Token Handling
        self.test_expired_token()

        # Test 8: Client Management
        self.test_client_management()

        # Test 9: Authentication Decorator
        self.test_auth_decorator()

        # Print summary
        self.print_summary()

        # Cleanup
        self.cleanup()

    def test_rsa_keys(self):
        """Test RSA key generation and loading"""
        print_test("Test 1: RSA Key Generation and Loading")
        self.total_tests += 1

        try:
            # Check if keys exist
            if not oauth_config.PRIVATE_KEY_PATH.exists():
                print_error("Private key file not found")
                self.failed_tests += 1
                return

            if not oauth_config.PUBLIC_KEY_PATH.exists():
                print_error("Public key file not found")
                self.failed_tests += 1
                return

            # Check if keys are loaded
            if not oauth_config.private_key:
                print_error("Private key not loaded")
                self.failed_tests += 1
                return

            if not oauth_config.public_key:
                print_error("Public key not loaded")
                self.failed_tests += 1
                return

            print_success("RSA keys generated and loaded successfully")
            print_info(f"Private key: {oauth_config.PRIVATE_KEY_PATH}")
            print_info(f"Public key: {oauth_config.PUBLIC_KEY_PATH}")
            self.passed_tests += 1

        except Exception as e:
            print_error(f"RSA key test failed: {e}")
            self.failed_tests += 1

    def test_client_creation(self):
        """Test OAuth client creation"""
        print_test("Test 2: OAuth Client Creation")
        self.total_tests += 1

        try:
            # Create a test client
            credentials = oauth_config.create_client(
                client_id="test_client_oauth",
                client_name="OAuth Test Client"
            )

            self.test_client_id = credentials['client_id']
            self.test_client_secret = credentials['client_secret']

            if not self.test_client_id or not self.test_client_secret:
                print_error("Client credentials not returned")
                self.failed_tests += 1
                return

            # Verify client was saved
            clients = oauth_config.load_clients()
            if self.test_client_id not in clients:
                print_error("Client not found in storage")
                self.failed_tests += 1
                return

            print_success("OAuth client created successfully")
            print_info(f"Client ID: {self.test_client_id}")
            print_info(f"Client Secret: {self.test_client_secret[:20]}...")
            self.passed_tests += 1

        except Exception as e:
            print_error(f"Client creation test failed: {e}")
            self.failed_tests += 1

    def test_client_verification(self):
        """Test client credential verification"""
        print_test("Test 3: Client Credential Verification")
        self.total_tests += 1

        try:
            # Test valid credentials
            if oauth_config.verify_client(self.test_client_id, self.test_client_secret):
                print_success("Valid credentials verified correctly")
            else:
                print_error("Valid credentials rejected")
                self.failed_tests += 1
                return

            # Test invalid credentials
            if not oauth_config.verify_client(self.test_client_id, "wrong_secret"):
                print_success("Invalid credentials rejected correctly")
            else:
                print_error("Invalid credentials accepted")
                self.failed_tests += 1
                return

            # Test non-existent client
            if not oauth_config.verify_client("non_existent_client", "secret"):
                print_success("Non-existent client rejected correctly")
            else:
                print_error("Non-existent client accepted")
                self.failed_tests += 1
                return

            self.passed_tests += 1

        except Exception as e:
            print_error(f"Client verification test failed: {e}")
            self.failed_tests += 1

    def test_token_generation(self):
        """Test JWT token generation"""
        print_test("Test 4: JWT Token Generation")
        self.total_tests += 1

        try:
            # Generate token
            self.test_token = oauth_config.create_access_token(self.test_client_id)

            if not self.test_token:
                print_error("Token not generated")
                self.failed_tests += 1
                return

            # Check token format (JWT has 3 parts separated by dots)
            parts = self.test_token.split('.')
            if len(parts) != 3:
                print_error(f"Invalid JWT format (expected 3 parts, got {len(parts)})")
                self.failed_tests += 1
                return

            print_success("JWT token generated successfully")
            print_info(f"Token: {self.test_token[:50]}...")
            print_info(f"Token length: {len(self.test_token)} characters")
            self.passed_tests += 1

        except Exception as e:
            print_error(f"Token generation test failed: {e}")
            self.failed_tests += 1

    def test_token_validation(self):
        """Test token validation"""
        print_test("Test 5: Token Validation")
        self.total_tests += 1

        try:
            # Validate the token
            payload = oauth_config.verify_token(self.test_token)

            if not payload:
                print_error("Valid token rejected")
                self.failed_tests += 1
                return

            # Check payload contents
            required_fields = ['sub', 'iat', 'exp', 'type', 'iss']
            for field in required_fields:
                if field not in payload:
                    print_error(f"Missing required field: {field}")
                    self.failed_tests += 1
                    return

            # Verify payload values
            if payload['sub'] != self.test_client_id:
                print_error(f"Wrong client ID in token (expected {self.test_client_id}, got {payload['sub']})")
                self.failed_tests += 1
                return

            if payload['type'] != 'access_token':
                print_error(f"Wrong token type (expected 'access_token', got {payload['type']})")
                self.failed_tests += 1
                return

            if payload['iss'] != 'skyy_facial_recognition_mcp':
                print_error(f"Wrong issuer (got {payload['iss']})")
                self.failed_tests += 1
                return

            print_success("Token validated successfully")
            print_info(f"Client ID: {payload['sub']}")
            print_info(f"Token Type: {payload['type']}")
            print_info(f"Issuer: {payload['iss']}")
            self.passed_tests += 1

        except Exception as e:
            print_error(f"Token validation test failed: {e}")
            self.failed_tests += 1

    def test_invalid_token(self):
        """Test invalid token handling"""
        print_test("Test 6: Invalid Token Handling")
        self.total_tests += 1

        try:
            # Test with completely invalid token
            invalid_tokens = [
                "invalid_token",
                "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature",
                "",
                "a.b.c"
            ]

            all_rejected = True
            for token in invalid_tokens:
                payload = oauth_config.verify_token(token)
                if payload is not None:
                    print_error(f"Invalid token accepted: {token[:30]}...")
                    all_rejected = False

            if all_rejected:
                print_success("All invalid tokens rejected correctly")
                self.passed_tests += 1
            else:
                print_error("Some invalid tokens were accepted")
                self.failed_tests += 1

        except Exception as e:
            print_error(f"Invalid token test failed: {e}")
            self.failed_tests += 1

    def test_expired_token(self):
        """Test expired token handling"""
        print_test("Test 7: Expired Token Handling")
        self.total_tests += 1

        try:
            # Note: We can't easily test actual expiration without waiting 60 minutes
            # or modifying the system clock. Instead, we'll verify that the expiration
            # is set correctly in the token.

            import jwt

            # Decode without verification to check expiration
            payload = jwt.decode(
                self.test_token,
                options={"verify_signature": False}
            )

            # Check that expiration is set and is in the future
            if 'exp' not in payload:
                print_error("Token missing expiration claim")
                self.failed_tests += 1
                return

            import time
            current_time = int(time.time())
            exp_time = payload['exp']

            if exp_time <= current_time:
                print_error("Token already expired")
                self.failed_tests += 1
                return

            # Check that expiration is approximately 60 minutes from now
            time_diff = exp_time - current_time
            expected_diff = 60 * 60  # 60 minutes

            if abs(time_diff - expected_diff) > 10:  # Allow 10 second tolerance
                print_error(f"Token expiration incorrect (expected ~{expected_diff}s, got {time_diff}s)")
                self.failed_tests += 1
                return

            print_success("Token expiration configured correctly")
            print_info(f"Token expires in {time_diff} seconds ({time_diff/60:.1f} minutes)")
            self.passed_tests += 1

        except Exception as e:
            print_error(f"Expired token test failed: {e}")
            self.failed_tests += 1

    def test_client_management(self):
        """Test client management operations"""
        print_test("Test 8: Client Management Operations")
        self.total_tests += 1

        try:
            # Test list clients
            clients = oauth_config.list_clients()
            if self.test_client_id not in clients:
                print_error("Test client not in list")
                self.failed_tests += 1
                return

            print_success("Client listing works correctly")

            # Create a second client for deletion test
            temp_client = oauth_config.create_client(
                client_id="temp_test_client",
                client_name="Temporary Test Client"
            )

            # Test delete client
            if oauth_config.delete_client("temp_test_client"):
                print_success("Client deletion works correctly")
            else:
                print_error("Client deletion failed")
                self.failed_tests += 1
                return

            # Verify deletion
            clients = oauth_config.load_clients()
            if "temp_test_client" in clients:
                print_error("Deleted client still exists")
                self.failed_tests += 1
                return

            print_success("Client management operations work correctly")
            self.passed_tests += 1

        except Exception as e:
            print_error(f"Client management test failed: {e}")
            self.failed_tests += 1

    def test_auth_decorator(self):
        """Test authentication decorator"""
        print_test("Test 9: Authentication Decorator")
        self.total_tests += 1

        try:
            from pydantic import BaseModel, Field

            # Create a test input model
            class TestInput(BaseModel):
                access_token: str = Field(..., min_length=20)
                data: str = "test data"

            # Create a test function with auth decorator
            @require_auth
            async def test_function(params: TestInput):
                # Note: _client_id is no longer passed in kwargs due to Pydantic compatibility
                # The decorator validates the token but doesn't inject client_id to avoid
                # conflicts with Pydantic models that have extra='forbid'
                return f"Success: {params.data}"

            # Test with valid token
            import asyncio
            test_input = TestInput(access_token=self.test_token, data="test")
            result = asyncio.run(test_function(test_input))

            if "Success" in result:
                print_success("Authentication decorator works with valid token")
            else:
                print_error(f"Unexpected result: {result}")
                self.failed_tests += 1
                return

            # Test with invalid token
            try:
                test_input_invalid = TestInput(access_token="invalid_token_12345678901234567890", data="test")
                result = asyncio.run(test_function(test_input_invalid))
                print_error("Invalid token was accepted by decorator")
                self.failed_tests += 1
                return
            except AuthenticationError:
                print_success("Authentication decorator rejects invalid tokens")

            self.passed_tests += 1

        except Exception as e:
            print_error(f"Auth decorator test failed: {e}")
            self.failed_tests += 1

    def print_summary(self):
        """Print test summary"""
        print_header("Test Summary")

        total = self.total_tests
        passed = self.passed_tests
        failed = self.failed_tests

        print(f"Total Tests:  {total}")
        print(f"{Colors.GREEN}Passed:       {passed}{Colors.RESET}")
        if failed > 0:
            print(f"{Colors.RED}Failed:       {failed}{Colors.RESET}")
        else:
            print(f"Failed:       {failed}")

        success_rate = (passed / total * 100) if total > 0 else 0
        print(f"\nSuccess Rate: {success_rate:.1f}%")

        if failed == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}[OK] ALL TESTS PASSED!{Colors.RESET}\n")
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}[X] SOME TESTS FAILED{Colors.RESET}\n")

    def cleanup(self):
        """Clean up test data"""
        print_test("Cleanup: Removing test client")

        try:
            if self.test_client_id:
                oauth_config.delete_client(self.test_client_id)
                print_success(f"Removed test client: {self.test_client_id}")
        except Exception as e:
            print_error(f"Cleanup failed: {e}")


def main():
    """Main test entry point"""
    tester = OAuthTester()
    tester.run_all_tests()

    # Return exit code based on test results
    return 0 if tester.failed_tests == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
