"""
Skyy Facial Recognition - Web Admin Dashboard

Flask-based web application for managing the facial recognition system.
Provides admin interface for:
- User management (list, view, delete)
- Database statistics
- System health monitoring
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from functools import wraps
import json
import re
import secrets
from datetime import datetime, timedelta

# Import from MCP server modules
from oauth_config import oauth_config
from health_checker import health_checker, HealthStatus, ComponentType
from audit_logger import audit_logger, AuditOutcome, AuditEventType

# ChromaDB for data access
import chromadb
from chromadb.config import Settings

# Initialize Flask app
app = Flask(__name__)

# Security: Use environment variable for secret key, generate random fallback for development
_secret_key = os.environ.get('FLASK_SECRET_KEY')
if not _secret_key:
    print("[WARNING] FLASK_SECRET_KEY not set. Using random key (sessions won't persist across restarts)")
    _secret_key = secrets.token_hex(32)
app.secret_key = _secret_key

# Security: Configure secure session cookies
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,  # Prevent JavaScript access to session cookie
    SESSION_COOKIE_SAMESITE='Lax',  # CSRF protection for cookies
    PERMANENT_SESSION_LIFETIME=timedelta(hours=1)  # Session expiration
)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
DATABASE_PATH = PROJECT_ROOT / "skyy_face_data"
CHROMA_PATH = DATABASE_PATH / "chroma_db"
INDEX_FILE = DATABASE_PATH / "index.json"


# Input validation helpers
def validate_user_id(user_id: str) -> str:
    """Validate user ID format to prevent injection attacks."""
    if not user_id or not isinstance(user_id, str):
        raise ValueError("Invalid user ID")
    # Allow alphanumeric, underscores, hyphens
    if not re.match(r'^[a-zA-Z0-9_-]{1,100}$', user_id):
        raise ValueError("Invalid user ID format")
    return user_id


def validate_path_in_directory(file_path: str, allowed_base: Path) -> Path:
    """Validate that a file path is within the allowed directory (prevent path traversal)."""
    if not file_path:
        return None
    resolved_path = Path(file_path).resolve()
    allowed_base_resolved = allowed_base.resolve()
    if not str(resolved_path).startswith(str(allowed_base_resolved)):
        raise ValueError("Invalid file path - path traversal detected")
    return resolved_path


# Security headers
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response


# Initialize ChromaDB
chroma_client = None
chroma_collection = None


def get_chroma_collection():
    """Get or create ChromaDB collection."""
    global chroma_client, chroma_collection
    if chroma_client is None:
        chroma_client = chromadb.PersistentClient(
            path=str(CHROMA_PATH),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        chroma_collection = chroma_client.get_or_create_collection(
            name="face_embeddings",
            metadata={
                "hnsw:space": "cosine",
                "hnsw:construction_ef": 200,
                "hnsw:search_ef": 50,
                "hnsw:M": 32,
                "hnsw:num_threads": 4
            }
        )
    return chroma_collection


def extract_user_data_from_chroma_metadata(chroma_metadata: dict) -> dict:
    """Extract user data from ChromaDB metadata format."""
    user_data = {
        "user_id": chroma_metadata.get("user_id", "unknown"),
        "name": chroma_metadata.get("name", "Unknown"),
        "image_path": chroma_metadata.get("image_path", ""),
        "registration_timestamp": chroma_metadata.get("registration_timestamp", ""),
        "recognition_count": chroma_metadata.get("recognition_count", 0),
        "last_recognized": chroma_metadata.get("last_recognized"),
        "metadata": {},
        "facial_features": {}
    }

    # Extract custom metadata (prefixed with "custom_")
    for key, value in chroma_metadata.items():
        if key.startswith("custom_"):
            clean_key = key[7:]  # Remove "custom_" prefix
            try:
                user_data["metadata"][clean_key] = json.loads(value) if isinstance(value, str) and value.startswith('{') else value
            except (json.JSONDecodeError, TypeError):
                user_data["metadata"][clean_key] = value

    # Extract facial features
    facial_feature_keys = ["bbox", "detection_score", "extraction_timestamp",
                          "landmark_quality", "face_size_ratio", "num_faces_detected"]
    for key in facial_feature_keys:
        if key in chroma_metadata:
            user_data["facial_features"][key] = chroma_metadata[key]

    return user_data


def load_database():
    """Load the JSON database (for stats that aren't in ChromaDB)."""
    if INDEX_FILE.exists():
        with open(INDEX_FILE, 'r') as f:
            return json.load(f)
    return {"metadata": {}, "users": {}}


# Authentication decorator
def login_required(f):
    """Decorator to require authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'access_token' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))

        # Verify token is still valid
        token_data = oauth_config.verify_token(session['access_token'])
        if token_data is None:
            session.pop('access_token', None)
            session.pop('client_id', None)
            flash('Your session has expired. Please log in again.', 'warning')
            return redirect(url_for('login'))

        return f(*args, **kwargs)
    return decorated_function


# Routes
@app.route('/')
def index():
    """Redirect to dashboard or login."""
    if 'access_token' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page."""
    if request.method == 'POST':
        client_id = request.form.get('client_id', '').strip()
        client_secret = request.form.get('client_secret', '').strip()

        if not client_id or not client_secret:
            flash('Please provide both Client ID and Client Secret.', 'danger')
            return render_template('login.html')

        # Verify credentials
        if oauth_config.verify_client(client_id, client_secret):
            # Create access token
            access_token = oauth_config.create_access_token(client_id)
            session['access_token'] = access_token
            session['client_id'] = client_id

            # Get client name
            clients = oauth_config.load_clients()
            session['client_name'] = clients.get(client_id, {}).get('client_name', client_id)

            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials. Please check your Client ID and Secret.', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    """Logout and clear session."""
    session.pop('access_token', None)
    session.pop('client_id', None)
    session.pop('client_name', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard with overview."""
    try:
        # Get database stats
        collection = get_chroma_collection()
        result = collection.get(include=["metadatas"])
        total_users = len(result["ids"]) if result["ids"] else 0

        # Calculate total recognitions
        total_recognitions = 0
        most_active_user = None
        max_recognitions = 0

        if result["metadatas"]:
            for meta in result["metadatas"]:
                count = meta.get("recognition_count", 0)
                total_recognitions += count
                if count > max_recognitions:
                    max_recognitions = count
                    most_active_user = {
                        "name": meta.get("name", "Unknown"),
                        "user_id": meta.get("user_id", ""),
                        "recognition_count": count
                    }

        # Get health status
        health_summary = health_checker.get_health_summary()

        stats = {
            "total_users": total_users,
            "total_recognitions": total_recognitions,
            "most_active_user": most_active_user,
            "health": health_summary
        }

        return render_template('dashboard.html', stats=stats)
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'danger')
        return render_template('dashboard.html', stats={
            "total_users": 0,
            "total_recognitions": 0,
            "most_active_user": None,
            "health": {"overall_status": "error", "components": {}}
        })


@app.route('/users')
@login_required
def users():
    """User list page with pagination."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '', type=str).strip()[:100]  # Limit search length

        # Clamp per_page
        per_page = max(5, min(per_page, 100))

        collection = get_chroma_collection()
        result = collection.get(include=["metadatas"])

        if not result["ids"]:
            return render_template('users.html', users=[], total=0, page=1, per_page=per_page, total_pages=1, search=search)

        # Extract user data
        users_list = []
        for i, user_id in enumerate(result["ids"]):
            meta = result["metadatas"][i] if result["metadatas"] and i < len(result["metadatas"]) else {}
            user_data = extract_user_data_from_chroma_metadata(meta)

            # Apply search filter
            if search:
                search_lower = search.lower()
                if search_lower not in user_data["name"].lower() and search_lower not in user_data["user_id"].lower():
                    continue

            users_list.append(user_data)

        # Sort by registration date (newest first)
        users_list.sort(key=lambda x: x.get("registration_timestamp", ""), reverse=True)

        # Pagination
        total = len(users_list)
        total_pages = max(1, (total + per_page - 1) // per_page)
        page = max(1, min(page, total_pages))
        offset = (page - 1) * per_page
        paginated_users = users_list[offset:offset + per_page]

        return render_template('users.html',
                             users=paginated_users,
                             total=total,
                             page=page,
                             per_page=per_page,
                             total_pages=total_pages,
                             search=search)
    except Exception as e:
        flash(f'Error loading users: {str(e)}', 'danger')
        return render_template('users.html', users=[], total=0, page=1, per_page=10, total_pages=1, search='')


@app.route('/users/<user_id>')
@login_required
def user_profile(user_id):
    """User profile detail page."""
    try:
        # Validate user_id to prevent injection
        user_id = validate_user_id(user_id)

        collection = get_chroma_collection()
        result = collection.get(ids=[user_id], include=["metadatas"])

        if not result["ids"]:
            flash(f'User "{user_id}" not found.', 'warning')
            return redirect(url_for('users'))

        meta = result["metadatas"][0] if result["metadatas"] else {}
        user_data = extract_user_data_from_chroma_metadata(meta)

        # Log profile access
        audit_logger.log_profile_access(
            client_id=session.get('client_id', 'web_admin'),
            outcome=AuditOutcome.SUCCESS,
            user_id=user_id,
            user_name=user_data["name"]
        )

        return render_template('user_profile.html', user=user_data)
    except Exception as e:
        flash(f'Error loading user profile: {str(e)}', 'danger')
        return redirect(url_for('users'))


@app.route('/users/<user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    """Delete a user."""
    try:
        # Validate user_id to prevent injection
        user_id = validate_user_id(user_id)

        collection = get_chroma_collection()

        # Get user info before deletion
        result = collection.get(ids=[user_id], include=["metadatas"])

        if not result["ids"]:
            flash(f'User "{user_id}" not found.', 'warning')
            return redirect(url_for('users'))

        meta = result["metadatas"][0] if result["metadatas"] else {}
        user_name = meta.get("name", "Unknown")
        image_path = meta.get("image_path", "")

        # Delete image file if exists (with path traversal protection)
        if image_path:
            try:
                safe_path = validate_path_in_directory(image_path, DATABASE_PATH)
                if safe_path and safe_path.exists():
                    safe_path.unlink()
            except ValueError as e:
                app.logger.warning(f"Skipping image deletion due to path validation: {e}")

        # Delete from ChromaDB
        collection.delete(ids=[user_id])

        # Log deletion
        audit_logger.log_deletion(
            client_id=session.get('client_id', 'web_admin'),
            outcome=AuditOutcome.SUCCESS,
            user_id=user_id,
            user_name=user_name
        )

        flash(f'User "{user_name}" has been deleted.', 'success')
        return redirect(url_for('users'))
    except Exception as e:
        # Log failure
        audit_logger.log_deletion(
            client_id=session.get('client_id', 'web_admin'),
            outcome=AuditOutcome.FAILURE,
            user_id=user_id,
            error_message=str(e)
        )
        flash(f'Error deleting user: {str(e)}', 'danger')
        return redirect(url_for('users'))


@app.route('/health')
@login_required
def health():
    """System health status page."""
    try:
        health_summary = health_checker.get_health_summary()

        # Log health check
        audit_logger.log_health_event(
            event_type=AuditEventType.HEALTH_CHECK,
            component="system",
            status=health_summary["overall_status"],
            message="Health status viewed via web admin",
            client_id=session.get('client_id', 'web_admin')
        )

        return render_template('health.html', health=health_summary)
    except Exception as e:
        flash(f'Error loading health status: {str(e)}', 'danger')
        return render_template('health.html', health={
            "overall_status": "error",
            "components": {},
            "capabilities": {},
            "degraded_mode": {"active": False}
        })


@app.route('/stats')
@login_required
def stats():
    """Database statistics page."""
    try:
        collection = get_chroma_collection()
        result = collection.get(include=["metadatas"])

        total_users = len(result["ids"]) if result["ids"] else 0
        total_recognitions = 0
        most_active_user = None
        max_recognitions = 0
        recent_users = []

        if result["metadatas"]:
            users_list = []
            for i, user_id in enumerate(result["ids"]):
                meta = result["metadatas"][i] if i < len(result["metadatas"]) else {}
                user_data = extract_user_data_from_chroma_metadata(meta)
                users_list.append(user_data)

                count = meta.get("recognition_count", 0)
                total_recognitions += count
                if count > max_recognitions:
                    max_recognitions = count
                    most_active_user = user_data

            # Sort by registration date and get recent
            users_list.sort(key=lambda x: x.get("registration_timestamp", ""), reverse=True)
            recent_users = users_list[:5]

        # Get database metadata
        db = load_database()
        db_metadata = db.get("metadata", {})

        stats_data = {
            "total_users": total_users,
            "total_recognitions": total_recognitions,
            "most_active_user": most_active_user,
            "recent_users": recent_users,
            "database_version": db_metadata.get("version", "1.0"),
            "database_created": db_metadata.get("created", "Unknown"),
            "storage_location": str(DATABASE_PATH)
        }

        # Log stats access
        audit_logger.log_database_operation(
            client_id=session.get('client_id', 'web_admin'),
            outcome=AuditOutcome.SUCCESS,
            operation_type="get_stats",
            additional_info={"total_users": total_users}
        )

        return render_template('stats.html', stats=stats_data)
    except Exception as e:
        flash(f'Error loading statistics: {str(e)}', 'danger')
        return render_template('stats.html', stats={
            "total_users": 0,
            "total_recognitions": 0,
            "most_active_user": None,
            "recent_users": [],
            "database_version": "Unknown",
            "database_created": "Unknown",
            "storage_location": str(DATABASE_PATH)
        })


# API Endpoints (for AJAX calls)
@app.route('/api/users')
@login_required
def api_list_users():
    """API endpoint to list users."""
    try:
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)

        # Enforce limits for API as well
        limit = max(1, min(limit, 100))
        offset = max(0, offset)

        collection = get_chroma_collection()
        result = collection.get(include=["metadatas"])

        if not result["ids"]:
            return jsonify({
                "total": 0,
                "count": 0,
                "offset": offset,
                "limit": limit,
                "has_more": False,
                "users": []
            })

        # Extract and sort users
        users_list = []
        for i, user_id in enumerate(result["ids"]):
            meta = result["metadatas"][i] if result["metadatas"] and i < len(result["metadatas"]) else {}
            user_data = extract_user_data_from_chroma_metadata(meta)
            users_list.append({
                "user_id": user_data["user_id"],
                "name": user_data["name"],
                "registration_timestamp": user_data["registration_timestamp"],
                "recognition_count": user_data.get("recognition_count", 0),
                "last_recognized": user_data.get("last_recognized")
            })

        users_list.sort(key=lambda x: x.get("registration_timestamp", ""), reverse=True)

        # Pagination
        total = len(users_list)
        paginated = users_list[offset:offset + limit]
        has_more = total > offset + len(paginated)

        return jsonify({
            "total": total,
            "count": len(paginated),
            "offset": offset,
            "limit": limit,
            "has_more": has_more,
            "next_offset": offset + len(paginated) if has_more else None,
            "users": paginated
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/users/<user_id>')
@login_required
def api_get_user(user_id):
    """API endpoint to get user profile."""
    try:
        # Validate user_id
        user_id = validate_user_id(user_id)

        collection = get_chroma_collection()
        result = collection.get(ids=[user_id], include=["metadatas"])

        if not result["ids"]:
            return jsonify({"status": "error", "message": "User not found"}), 404

        meta = result["metadatas"][0] if result["metadatas"] else {}
        user_data = extract_user_data_from_chroma_metadata(meta)

        return jsonify({
            "user_id": user_data["user_id"],
            "name": user_data["name"],
            "metadata": user_data.get("metadata", {}),
            "registration_timestamp": user_data["registration_timestamp"],
            "recognition_count": user_data.get("recognition_count", 0),
            "last_recognized": user_data.get("last_recognized")
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/users/<user_id>', methods=['DELETE'])
@login_required
def api_delete_user(user_id):
    """API endpoint to delete user."""
    try:
        # Validate user_id
        user_id = validate_user_id(user_id)

        collection = get_chroma_collection()
        result = collection.get(ids=[user_id], include=["metadatas"])

        if not result["ids"]:
            return jsonify({"status": "error", "message": "User not found"}), 404

        meta = result["metadatas"][0] if result["metadatas"] else {}
        user_name = meta.get("name", "Unknown")
        image_path = meta.get("image_path", "")

        # Delete image (with path traversal protection)
        if image_path:
            try:
                safe_path = validate_path_in_directory(image_path, DATABASE_PATH)
                if safe_path and safe_path.exists():
                    safe_path.unlink()
            except ValueError:
                pass  # Skip invalid paths silently for API

        # Delete from ChromaDB
        collection.delete(ids=[user_id])

        # Log deletion
        audit_logger.log_deletion(
            client_id=session.get('client_id', 'web_admin'),
            outcome=AuditOutcome.SUCCESS,
            user_id=user_id,
            user_name=user_name
        )

        return jsonify({
            "status": "success",
            "message": "User deleted successfully",
            "deleted_user_id": user_id,
            "deleted_user_name": user_name
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/stats')
@login_required
def api_stats():
    """API endpoint for database statistics."""
    try:
        collection = get_chroma_collection()
        result = collection.get(include=["metadatas"])

        total_users = len(result["ids"]) if result["ids"] else 0
        total_recognitions = 0
        most_active_user = None
        max_recognitions = 0

        if result["metadatas"]:
            for meta in result["metadatas"]:
                count = meta.get("recognition_count", 0)
                total_recognitions += count
                if count > max_recognitions:
                    max_recognitions = count
                    most_active_user = {
                        "name": meta.get("name", "Unknown"),
                        "user_id": meta.get("user_id", ""),
                        "recognition_count": count
                    }

        db = load_database()

        return jsonify({
            "total_users": total_users,
            "total_recognitions": total_recognitions,
            "database_version": db.get("metadata", {}).get("version", "unknown"),
            "database_created": db.get("metadata", {}).get("created"),
            "storage_location": str(DATABASE_PATH),
            "most_active_user": most_active_user
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/health')
@login_required
def api_health():
    """API endpoint for health status."""
    try:
        return jsonify(health_checker.get_health_summary())
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# Template filters
@app.template_filter('datetime')
def format_datetime(value):
    """Format datetime string for display."""
    if not value:
        return 'Never'
    try:
        if isinstance(value, str):
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        else:
            dt = value
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        return value


@app.template_filter('relative_time')
def relative_time(value):
    """Format datetime as relative time."""
    if not value:
        return 'Never'
    try:
        if isinstance(value, str):
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        else:
            dt = value

        now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
        diff = now - dt

        if diff.days > 365:
            return f"{diff.days // 365} year(s) ago"
        elif diff.days > 30:
            return f"{diff.days // 30} month(s) ago"
        elif diff.days > 0:
            return f"{diff.days} day(s) ago"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600} hour(s) ago"
        elif diff.seconds > 60:
            return f"{diff.seconds // 60} minute(s) ago"
        else:
            return "Just now"
    except (ValueError, TypeError):
        return value


if __name__ == '__main__':
    print("=" * 60)
    print("Skyy Facial Recognition - Web Admin Dashboard")
    print("=" * 60)
    print(f"Database path: {DATABASE_PATH}")
    print(f"ChromaDB path: {CHROMA_PATH}")
    print()
    print("Starting server on http://127.0.0.1:5000")
    print("Press Ctrl+C to stop")
    print("=" * 60)

    # Note: debug=False for security. Use run_web_admin.py --debug for development
    app.run(debug=False, host='127.0.0.1', port=5000)
