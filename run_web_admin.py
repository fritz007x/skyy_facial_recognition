#!/usr/bin/env python
"""
Run the Skyy Facial Recognition Web Admin Dashboard

This script starts the Flask web server for the admin dashboard.

Usage:
    python run_web_admin.py [--host HOST] [--port PORT] [--debug]

Example:
    python run_web_admin.py
    python run_web_admin.py --port 8080
    python run_web_admin.py --host 0.0.0.0 --port 5000
"""

import argparse
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from web_admin.app import app


def main():
    parser = argparse.ArgumentParser(
        description="Run the Skyy Facial Recognition Web Admin Dashboard"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port to bind to (default: 5000)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Skyy Facial Recognition - Web Admin Dashboard")
    print("=" * 60)
    print()
    print(f"Starting server at http://{args.host}:{args.port}")
    print()
    print("To log in, you need OAuth credentials.")
    print("Create them with: python src/oauth_admin.py create-client")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 60)

    app.run(
        host=args.host,
        port=args.port,
        debug=args.debug
    )


if __name__ == "__main__":
    main()
