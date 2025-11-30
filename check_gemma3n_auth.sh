#!/bin/bash
# Quick authentication check for Gemma 3n models
# Run this to verify your Hugging Face authentication is working

echo "======================================================================"
echo "GEMMA 3N AUTHENTICATION QUICK CHECK"
echo "======================================================================"
echo

# Check if virtual environment exists
if [ ! -f "facial_mcp_py311/bin/python" ]; then
    echo "[ERROR] Virtual environment not found!"
    echo "Please create it first:"
    echo "    python3.11 -m venv facial_mcp_py311"
    echo
    exit 1
fi

echo "[System] Using virtual environment: facial_mcp_py311"
echo

# Run the test script
facial_mcp_py311/bin/python test_hf_auth.py

if [ $? -eq 0 ]; then
    echo
    echo "======================================================================"
    echo "[SUCCESS] Authentication check passed!"
    echo "You can now run the Gemma 3n assistant."
    echo "======================================================================"
else
    echo
    echo "======================================================================"
    echo "[ERROR] Authentication check failed."
    echo "Please follow the instructions above to set up authentication."
    echo
    echo "For detailed help, see: GEMMA3N_HUGGINGFACE_AUTH.md"
    echo "======================================================================"
fi

echo
