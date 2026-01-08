#!/usr/bin/env python3
"""
OAuth 2.1 Administration CLI

Manage OAuth clients and generate access tokens for the MCP server.
"""

import argparse
import sys
import json
from pathlib import Path
from datetime import datetime

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from oauth_config import oauth_config


def create_client(args):
    """Create a new OAuth client"""
    try:
        credentials = oauth_config.create_client(
            client_id=args.client_id,
            client_name=args.name
        )

        print("\n" + "=" * 60)
        print("✓ OAuth Client Created Successfully")
        print("=" * 60)
        print(f"\nClient ID:     {credentials['client_id']}")
        print(f"Client Secret: {credentials['client_secret']}")
        print("\n⚠️  IMPORTANT: Save these credentials securely!")
        print("   The client secret cannot be retrieved later.\n")
        print("=" * 60 + "\n")

        return 0
    except Exception as e:
        print(f"❌ Error creating client: {e}", file=sys.stderr)
        return 1


def list_clients(args):
    """List all OAuth clients"""
    try:
        clients = oauth_config.list_clients()

        if not clients:
            print("\nNo OAuth clients found.")
            print("Create one with: python oauth_admin.py create-client --name \"My Client\"\n")
            return 0

        print("\n" + "=" * 80)
        print("OAuth Clients")
        print("=" * 80)
        print(f"{'Client ID':<40} {'Name':<25} {'Created':<15}")
        print("-" * 80)

        for client_id, info in clients.items():
            created = datetime.fromisoformat(info['created_at']).strftime('%Y-%m-%d')
            name = info['client_name'][:24]
            print(f"{client_id:<40} {name:<25} {created:<15}")

        print("=" * 80 + "\n")
        return 0
    except Exception as e:
        print(f"❌ Error listing clients: {e}", file=sys.stderr)
        return 1


def delete_client(args):
    """Delete an OAuth client"""
    try:
        if oauth_config.delete_client(args.client_id):
            print(f"\n✓ Client '{args.client_id}' deleted successfully\n")
            return 0
        else:
            print(f"\n❌ Client '{args.client_id}' not found\n", file=sys.stderr)
            return 1
    except Exception as e:
        print(f"❌ Error deleting client: {e}", file=sys.stderr)
        return 1


def get_token(args):
    """Generate an access token for a client"""
    try:
        # Verify client credentials
        if not oauth_config.verify_client(args.client_id, args.client_secret):
            print("\n❌ Invalid client credentials\n", file=sys.stderr)
            return 1

        # Generate token
        token = oauth_config.create_access_token(args.client_id)

        print("\n" + "=" * 60)
        print("✓ Access Token Generated")
        print("=" * 60)
        print(f"\nClient ID: {args.client_id}")
        print(f"Token expires in: {oauth_config.ACCESS_TOKEN_EXPIRE_MINUTES} minutes")
        print("\nAccess Token:")
        print("-" * 60)
        print(token)
        print("-" * 60)

        if args.output:
            output_file = Path(args.output)
            output_file.write_text(json.dumps({
                "access_token": token,
                "token_type": "Bearer",
                "expires_in": oauth_config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "client_id": args.client_id,
                "generated_at": datetime.utcnow().isoformat()
            }, indent=2))
            print(f"\n✓ Token saved to: {output_file}")

        print("\n" + "=" * 60 + "\n")
        return 0
    except Exception as e:
        print(f"❌ Error generating token: {e}", file=sys.stderr)
        return 1


def verify_token(args):
    """Verify a token"""
    try:
        payload = oauth_config.verify_token(args.token)

        if payload:
            print("\n" + "=" * 60)
            print("✓ Token is Valid")
            print("=" * 60)
            print(f"\nClient ID: {payload['sub']}")
            print(f"Issued at: {datetime.fromtimestamp(payload['iat']).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Expires:   {datetime.fromtimestamp(payload['exp']).strftime('%Y-%m-%d %H:%M:%S')}")
            print("\n" + "=" * 60 + "\n")
            return 0
        else:
            print("\n❌ Token is invalid or expired\n", file=sys.stderr)
            return 1
    except Exception as e:
        print(f"❌ Error verifying token: {e}", file=sys.stderr)
        return 1


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="OAuth 2.1 Administration for Skyy Facial Recognition MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a new client
  python oauth_admin.py create-client --name "My Application"

  # List all clients
  python oauth_admin.py list-clients

  # Generate an access token
  python oauth_admin.py get-token --client-id CLIENT_ID --client-secret SECRET

  # Verify a token
  python oauth_admin.py verify-token --token "eyJ..."

  # Delete a client
  python oauth_admin.py delete-client --client-id CLIENT_ID
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Create client command
    create_parser = subparsers.add_parser('create-client', help='Create a new OAuth client')
    create_parser.add_argument('--name', required=True, help='Human-readable name for the client')
    create_parser.add_argument('--client-id', help='Custom client ID (optional, auto-generated if not provided)')
    create_parser.set_defaults(func=create_client)

    # List clients command
    list_parser = subparsers.add_parser('list-clients', help='List all OAuth clients')
    list_parser.set_defaults(func=list_clients)

    # Delete client command
    delete_parser = subparsers.add_parser('delete-client', help='Delete an OAuth client')
    delete_parser.add_argument('--client-id', required=True, help='Client ID to delete')
    delete_parser.set_defaults(func=delete_client)

    # Get token command
    token_parser = subparsers.add_parser('get-token', help='Generate an access token')
    token_parser.add_argument('--client-id', required=True, help='Client ID')
    token_parser.add_argument('--client-secret', required=True, help='Client secret')
    token_parser.add_argument('--output', '-o', help='Save token to file (JSON format)')
    token_parser.set_defaults(func=get_token)

    # Verify token command
    verify_parser = subparsers.add_parser('verify-token', help='Verify an access token')
    verify_parser.add_argument('--token', required=True, help='Access token to verify')
    verify_parser.set_defaults(func=verify_token)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
