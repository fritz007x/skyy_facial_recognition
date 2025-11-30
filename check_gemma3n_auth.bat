@echo off
REM Quick authentication check for Gemma 3n models
REM Run this to verify your Hugging Face authentication is working

echo ======================================================================
echo GEMMA 3N AUTHENTICATION QUICK CHECK
echo ======================================================================
echo.

REM Check if virtual environment exists
if not exist "facial_mcp_py311\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found!
    echo Please create it first:
    echo     python -m venv facial_mcp_py311
    echo.
    pause
    exit /b 1
)

echo [System] Using virtual environment: facial_mcp_py311
echo.

REM Run the test script
"facial_mcp_py311\Scripts\python.exe" test_hf_auth.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ======================================================================
    echo [SUCCESS] Authentication check passed!
    echo You can now run the Gemma 3n assistant.
    echo ======================================================================
) else (
    echo.
    echo ======================================================================
    echo [ERROR] Authentication check failed.
    echo Please follow the instructions above to set up authentication.
    echo.
    echo For detailed help, see: GEMMA3N_HUGGINGFACE_AUTH.md
    echo ======================================================================
)

echo.
pause
