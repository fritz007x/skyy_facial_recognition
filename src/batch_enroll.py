"""
Batch Enrollment Script for MCP Facial Recognition Server

Enrolls all images from a folder into the MCP database using OAuth authentication.
This script uses the MCP server's skyy_register_user tool to batch enroll faces.
"""

import asyncio
import sys
import json
import base64
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from typing import List, Dict, Any

# Add src directory to path for OAuth imports
sys.path.insert(0, str(Path(__file__).parent))
from oauth_config import OAuthConfig


class BatchEnrollmentClient:
    """Client for batch enrolling faces via MCP server."""

    def __init__(self, enrollment_dir: str, skip_existing: bool = True):
        """
        Initialize batch enrollment client.

        Args:
            enrollment_dir: Path to directory containing enrollment images
            skip_existing: If True, skip users already in database
        """
        self.enrollment_dir = Path(enrollment_dir)
        self.skip_existing = skip_existing
        self.access_token = None
        self.session = None

        # Statistics
        self.total_images = 0
        self.success_count = 0
        self.skip_count = 0
        self.fail_count = 0
        self.queued_count = 0
        self.existing_users = set()

    def setup_oauth(self):
        """Setup OAuth client and generate access token."""
        oauth_config = OAuthConfig()

        client_id = "batch_enroll_client"
        clients = oauth_config.load_clients()

        if client_id not in clients:
            print(f"[OAuth] Creating new client: {client_id}")
            credentials = oauth_config.create_client(
                client_id=client_id,
                client_name="Batch Enrollment Client"
            )
        else:
            print(f"[OAuth] Using existing client: {client_id}")

        # Generate access token
        self.access_token = oauth_config.create_access_token(client_id)
        print(f"[OAuth] Access token generated\n")

    def get_mcp_session(self):
        """Create and return an MCP session context manager."""
        # Get the absolute path to the project root
        script_dir = Path(__file__).parent.absolute()
        project_root = script_dir.parent

        # Build absolute paths
        python_path = project_root / "facial_mcp_py311" / "Scripts" / "python.exe"
        server_script = project_root / "src" / "skyy_facial_recognition_mcp.py"

        # Verify paths exist
        if not python_path.exists():
            raise FileNotFoundError(f"Python interpreter not found at: {python_path}")
        if not server_script.exists():
            raise FileNotFoundError(f"MCP server script not found at: {server_script}")

        server_params = StdioServerParameters(
            command=str(python_path),
            args=[str(server_script)],
            env=None
        )

        return stdio_client(server_params)

    def get_image_files(self) -> List[Path]:
        """Get all image files from enrollment directory."""
        if not self.enrollment_dir.exists():
            raise FileNotFoundError(
                f"Enrollment directory not found: {self.enrollment_dir}\n\n"
                f"Create the folder and add images:\n"
                f"  mkdir {self.enrollment_dir}"
            )

        # Get all image files
        image_files = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']:
            image_files.extend(list(self.enrollment_dir.glob(ext)))

        if not image_files:
            raise FileNotFoundError(
                f"No image files found in {self.enrollment_dir}\n"
                f"Supported formats: .jpg, .jpeg, .png"
            )

        return sorted(image_files)

    async def get_existing_users(self, session: ClientSession):
        """Get list of existing users from database."""
        try:
            result = await session.call_tool(
                "skyy_list_users",
                arguments={
                    "params": {
                        "access_token": self.access_token,
                        "limit": 100,
                        "offset": 0,
                        "response_format": "json"
                    }
                }
            )

            if result and result.content:
                content = result.content[0].text
                data = json.loads(content)

                if data.get('status') == 'success':
                    users = data.get('users', [])
                    # Normalize names for comparison
                    for user in users:
                        name = user.get('name', '').lower().replace(' ', '').replace('_', '')
                        self.existing_users.add(name)

                    print(f"[Database] Found {len(users)} existing users")
                    if users and self.skip_existing:
                        print(f"[Database] Existing users will be skipped:")
                        for user in users[:10]:  # Show first 10
                            print(f"  - {user['name']}")
                        if len(users) > 10:
                            print(f"  ... and {len(users) - 10} more")

        except Exception as e:
            print(f"[Warning] Could not retrieve existing users: {e}")
            print(f"[Warning] All images will be attempted for enrollment")

    async def check_health_status(self, session: ClientSession) -> Dict[str, Any]:
        """Check MCP server health status."""
        try:
            result = await session.call_tool(
                "skyy_get_health_status",
                arguments={
                    "params": {
                        "access_token": self.access_token,
                        "response_format": "json"
                    }
                }
            )

            if result and result.content:
                content = result.content[0].text
                health_data = json.loads(content)
                return health_data
            return None

        except Exception as e:
            print(f"[Warning] Could not check health status: {e}")
            return None

    def load_image_as_base64(self, image_path: Path) -> str:
        """Load image file and convert to base64."""
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        return base64.b64encode(image_bytes).decode('utf-8')

    async def enroll_single_user(self, session: ClientSession, image_path: Path, person_name: str) -> Dict[str, Any]:
        """
        Enroll a single user via MCP server.

        Returns:
            Dictionary with enrollment result
        """
        try:
            # Load and encode image
            image_data = self.load_image_as_base64(image_path)

            # Call MCP registration tool
            result = await session.call_tool(
                "skyy_register_user",
                arguments={
                    "params": {
                        "access_token": self.access_token,
                        "name": person_name,
                        "image_data": image_data,
                        "metadata": {
                            "source": "batch_enrollment",
                            "filename": image_path.name
                        },
                        "response_format": "json"
                    }
                }
            )

            if result and result.content:
                content = result.content[0].text
                return json.loads(content)
            else:
                return {"status": "error", "message": "No response from server"}

        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def enroll_all(self):
        """Main enrollment process."""
        print("=" * 80)
        print("BATCH ENROLLMENT - MCP Facial Recognition Server")
        print("=" * 80)
        print(f"\nEnrollment folder: {self.enrollment_dir}")
        print(f"Skip existing users: {self.skip_existing}")
        print()

        # Setup OAuth
        self.setup_oauth()

        # Get image files
        try:
            image_files = self.get_image_files()
            self.total_images = len(image_files)
            print(f"[Found] {self.total_images} image files to process\n")
        except FileNotFoundError as e:
            print(f"[Error] {e}")
            return

        # Connect to MCP server
        print("[MCP] Connecting to server...")
        async with self.get_mcp_session() as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("[MCP] Connected successfully\n")

                # Check health status
                print("[Health] Checking server health...")
                health_data = await self.check_health_status(session)

                if health_data:
                    overall_status = health_data.get('overall_status', 'unknown')
                    print(f"[Health] Server status: {overall_status.upper()}")

                    # Check if registration is available
                    capabilities = health_data.get('capabilities', {})
                    can_register = capabilities.get('register_user', False)

                    if not can_register:
                        print(f"\n[Error] Registration is currently unavailable!")
                        print(f"[Error] Server is in degraded mode")

                        degraded = health_data.get('degraded_mode', {})
                        if degraded.get('active'):
                            print(f"[Info] Registrations will be queued for later processing")
                        else:
                            print(f"[Info] Please check server components")
                            return

                    print()

                # Get existing users if skipping enabled
                if self.skip_existing:
                    await self.get_existing_users(session)
                    print()

                # Enroll each image
                print("-" * 80)
                print("ENROLLING IMAGES")
                print("-" * 80)

                for idx, image_file in enumerate(image_files, 1):
                    # Extract person name from filename
                    person_name = image_file.stem.replace('_', ' ').title()

                    # Check if already enrolled
                    normalized_name = person_name.lower().replace(' ', '').replace('_', '')

                    if self.skip_existing and normalized_name in self.existing_users:
                        print(f"[{idx}/{self.total_images}] [SKIP] {person_name} - Already enrolled")
                        self.skip_count += 1
                        continue

                    print(f"[{idx}/{self.total_images}] Enrolling {person_name}...", end=' ', flush=True)

                    # Enroll via MCP
                    result = await self.enroll_single_user(session, image_file, person_name)

                    # Process result
                    status = result.get('status', 'unknown')

                    if status == 'success':
                        print("[OK]")
                        self.success_count += 1
                        # Add to existing users to prevent duplicates in same run
                        self.existing_users.add(normalized_name)

                    elif status == 'queued':
                        print("[QUEUED]")
                        self.queued_count += 1
                        queue_pos = result.get('user', {}).get('queue_position', '?')
                        print(f"         -> Queued at position {queue_pos} (degraded mode)")
                        # Still count as success for statistics
                        self.existing_users.add(normalized_name)

                    elif status == 'error':
                        message = result.get('message', 'Unknown error')
                        if 'No face detected' in message or 'no faces found' in message.lower():
                            print("[FAIL] No face detected")
                        else:
                            print(f"[ERROR] {message}")
                        self.fail_count += 1

                    else:
                        print(f"[UNKNOWN] Status: {status}")
                        self.fail_count += 1

                # Print summary
                self.print_summary(session)

    async def print_summary(self, session: ClientSession):
        """Print enrollment summary."""
        print("\n" + "=" * 80)
        print("ENROLLMENT SUMMARY")
        print("=" * 80)
        print(f"Total images processed: {self.total_images}")
        print(f"Successfully enrolled: {self.success_count}")
        if self.queued_count > 0:
            print(f"Queued (degraded mode): {self.queued_count}")
        if self.skip_count > 0:
            print(f"Skipped (already enrolled): {self.skip_count}")
        if self.fail_count > 0:
            print(f"Failed: {self.fail_count}")

        # Get final database stats
        try:
            result = await session.call_tool(
                "skyy_get_database_stats",
                arguments={
                    "params": {
                        "access_token": self.access_token,
                        "response_format": "json"
                    }
                }
            )

            if result and result.content:
                content = result.content[0].text
                stats = json.loads(content)

                if stats.get('status') != 'error':
                    total_users = stats.get('total_users', 0)
                    print(f"\nTotal users in database: {total_users}")

        except Exception as e:
            print(f"\n[Warning] Could not retrieve final stats: {e}")

        print("=" * 80)

        # Next steps
        if self.success_count > 0 or self.queued_count > 0:
            print(f"\n✅ Enrollment completed successfully!")

            if self.queued_count > 0:
                print(f"\n⚠️  {self.queued_count} registrations are queued")
                print(f"   They will be processed when the database recovers")

            print("\n" + "=" * 80)
            print("NEXT STEPS")
            print("=" * 80)
            print("Test recognition with:")
            print("  python src/webcam_capture.py")
            print("\nOr run automated tests:")
            print("  python src/tests/test_mcp_client.py")
            print("=" * 80)


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Batch enroll faces into MCP facial recognition database"
    )
    parser.add_argument(
        'enrollment_dir',
        nargs='?',
        default=r'C:\Users\Fritz\Documents\MDC\Advanced NLP\PROJECT\test_dataset\enrollment',
        help='Path to directory containing enrollment images'
    )
    parser.add_argument(
        '--no-skip',
        action='store_true',
        help='Re-enroll users even if they already exist (creates duplicates)'
    )

    args = parser.parse_args()

    # Create client and run enrollment
    client = BatchEnrollmentClient(
        enrollment_dir=args.enrollment_dir,
        skip_existing=not args.no_skip
    )

    try:
        await client.enroll_all()
    except KeyboardInterrupt:
        print("\n\n[!] Enrollment interrupted by user")
    except Exception as e:
        print(f"\n\n[Error] Enrollment failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
