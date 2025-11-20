"""
Skyy Facial Recognition MCP Server

This MCP server provides facial recognition capabilities using InsightFace,
enabling personalized user interactions through visual identification. All processing
and storage is done locally to maintain privacy.

Features:
- Register new users with facial data
- Recognize registered users
- Retrieve user profiles
- Manage facial recognition database
- Uses InsightFace for production-grade facial recognition
"""

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from enum import Enum
import json
import base64
import hashlib
from datetime import datetime
from pathlib import Path
import asyncio
import numpy as np
from io import BytesIO
from PIL import Image
import insightface
from insightface.app import FaceAnalysis
import chromadb
from chromadb.config import Settings

# OAuth 2.1 Authentication
from oauth_middleware import require_auth, AuthenticationError, create_auth_error_response

# Initialize FastMCP server
mcp = FastMCP("skyy_facial_recognition_mcp")

# Constants
CHARACTER_LIMIT = 25000
DATABASE_PATH = Path("./skyy_face_data")
IMAGES_PATH = DATABASE_PATH / "images"
INDEX_FILE = DATABASE_PATH / "index.json"
CHROMA_PATH = DATABASE_PATH / "chroma_db"
MIN_CONFIDENCE_THRESHOLD = 0.25  # InsightFace similarity threshold (0.0-1.0, lower is stricter)

# Ensure directories exist
DATABASE_PATH.mkdir(parents=True, exist_ok=True)
IMAGES_PATH.mkdir(parents=True, exist_ok=True)
CHROMA_PATH.mkdir(parents=True, exist_ok=True)

# Initialize InsightFace
# Using buffalo_l model for good balance of speed and accuracy
face_app = None

def initialize_face_app():
    """Initialize InsightFace face analysis app lazily."""
    global face_app
    if face_app is None:
        face_app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
        face_app.prepare(ctx_id=0, det_size=(640, 640))
    return face_app


# Initialize ChromaDB
# Using persistent client with cosine similarity for face embeddings
chroma_client = None
chroma_collection = None

def initialize_chroma():
    """Initialize ChromaDB client and collection lazily."""
    global chroma_client, chroma_collection
    if chroma_client is None:
        chroma_client = chromadb.PersistentClient(
            path=str(CHROMA_PATH),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        # Get or create collection with HNSW optimization for 512-d face embeddings
        chroma_collection = chroma_client.get_or_create_collection(
            name="face_embeddings",
            metadata={
                "hnsw:space": "cosine",           # Cosine similarity for face embeddings
                "hnsw:construction_ef": 200,      # Build quality (default: 100) - better index quality
                "hnsw:search_ef": 50,             # Search quality (default: 10) - more accurate queries
                "hnsw:M": 32,                     # Connections per element (default: 16) - better recall
                "hnsw:num_threads": 4             # Parallel threads for batch operations
            }
        )
    return chroma_collection


# ============================================================================
# Enums and Models
# ============================================================================

class ResponseFormat(str, Enum):
    """Output format for tool responses."""
    MARKDOWN = "markdown"
    JSON = "json"


class RecognitionStatus(str, Enum):
    """Status codes for recognition operations."""
    RECOGNIZED = "recognized"
    NOT_RECOGNIZED = "not_recognized"
    LOW_CONFIDENCE = "low_confidence"
    ERROR = "error"


# ============================================================================
# Input Models
# ============================================================================

class RegisterUserInput(BaseModel):
    """Input model for registering a new user with facial data."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    access_token: str = Field(
        ...,
        description="OAuth 2.1 access token for authentication",
        min_length=20
    )
    name: str = Field(
        ...,
        description="User's full name (e.g., 'John Smith', 'Jane Doe')",
        min_length=1,
        max_length=100
    )
    image_data: str = Field(
        ...,
        description="Base64-encoded image data containing the user's face (JPEG or PNG format)",
        min_length=100
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Optional additional metadata about the user (e.g., {'department': 'Engineering', 'employee_id': '12345'})"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()


class RecognizeFaceInput(BaseModel):
    """Input model for recognizing a face from an image."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    access_token: str = Field(
        ...,
        description="OAuth 2.1 access token for authentication",
        min_length=20
    )
    image_data: str = Field(
        ...,
        description="Base64-encoded image data to analyze (JPEG or PNG format)",
        min_length=100
    )
    confidence_threshold: Optional[float] = Field(
        default=MIN_CONFIDENCE_THRESHOLD,
        description="Maximum distance for recognition (0.0 to 1.0). Lower values are stricter. Default is 0.25",
        ge=0.0,
        le=1.0
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


class GetUserProfileInput(BaseModel):
    """Input model for retrieving a user profile."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    access_token: str = Field(
        ...,
        description="OAuth 2.1 access token for authentication",
        min_length=20
    )
    user_id: str = Field(
        ...,
        description="Unique identifier for the user (e.g., 'user_abc123')",
        min_length=1,
        max_length=100
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


class ListUsersInput(BaseModel):
    """Input model for listing registered users."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    access_token: str = Field(
        ...,
        description="OAuth 2.1 access token for authentication",
        min_length=20
    )
    limit: Optional[int] = Field(
        default=20,
        description="Maximum number of users to return",
        ge=1,
        le=100
    )
    offset: Optional[int] = Field(
        default=0,
        description="Number of users to skip for pagination",
        ge=0
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


class UpdateUserInput(BaseModel):
    """Input model for updating user information."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    access_token: str = Field(
        ...,
        description="OAuth 2.1 access token for authentication",
        min_length=20
    )
    user_id: str = Field(
        ...,
        description="Unique identifier for the user to update",
        min_length=1,
        max_length=100
    )
    name: Optional[str] = Field(
        default=None,
        description="Updated name for the user",
        min_length=1,
        max_length=100
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Updated metadata (replaces existing metadata)"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


class DeleteUserInput(BaseModel):
    """Input model for deleting a user."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    access_token: str = Field(
        ...,
        description="OAuth 2.1 access token for authentication",
        min_length=20
    )
    user_id: str = Field(
        ...,
        description="Unique identifier for the user to delete",
        min_length=1,
        max_length=100
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


class GetDatabaseStatsInput(BaseModel):
    """Input model for getting database statistics."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    access_token: str = Field(
        ...,
        description="OAuth 2.1 access token for authentication",
        min_length=20
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


# ============================================================================
# Database Helper Functions
# ============================================================================

def migrate_json_to_chroma(db: Dict[str, Any]) -> None:
    """
    Migrate existing JSON database to ChromaDB.

    This function checks if embeddings exist in the JSON database but not in ChromaDB,
    and migrates them with ALL metadata fields. It marks the database as migrated once complete.

    Args:
        db: The JSON database dictionary
    """
    # Check if migration is already done
    if db.get("metadata", {}).get("chroma_migrated", False):
        return

    # Initialize ChromaDB
    collection = initialize_chroma()

    users = db.get("users", {})
    if not users:
        # No users to migrate, mark as done
        if "metadata" not in db:
            db["metadata"] = {}
        db["metadata"]["chroma_migrated"] = True
        return

    migrated_count = 0
    for user_id, user_data in users.items():
        # Check if user has facial features with embeddings
        facial_features = user_data.get("facial_features", {})
        if "feature_vector" in facial_features:
            # Check if already in ChromaDB
            try:
                existing = collection.get(ids=[user_id])
                if not existing["ids"]:  # User not in ChromaDB
                    # Build comprehensive metadata for ChromaDB
                    chroma_metadata = {
                        "user_id": user_id,
                        "name": user_data.get("name", ""),
                        "image_path": user_data.get("image_path", ""),
                        "registration_timestamp": user_data.get("registration_timestamp", ""),
                        "recognition_count": user_data.get("recognition_count", 0),
                        "last_recognized": user_data.get("last_recognized", ""),
                        # Face detection metadata
                        "bbox": json.dumps(facial_features.get("bbox", [])),
                        "detection_score": facial_features.get("detection_score", 0.0),
                        "extraction_timestamp": facial_features.get("extraction_timestamp", ""),
                        "landmark_quality": facial_features.get("landmark_quality", 0.0),
                        "face_size_ratio": facial_features.get("face_size_ratio", 0.0),
                        "num_faces_detected": facial_features.get("num_faces_detected", 1),
                    }

                    # Add custom user metadata fields with prefix to avoid conflicts
                    custom_metadata = user_data.get("metadata", {})
                    for key, value in custom_metadata.items():
                        # ChromaDB metadata values must be strings, ints, or floats
                        if isinstance(value, (str, int, float, bool)):
                            chroma_metadata[f"custom_{key}"] = value
                        else:
                            # Serialize complex types as JSON strings
                            chroma_metadata[f"custom_{key}"] = json.dumps(value)

                    # Add to ChromaDB
                    collection.add(
                        ids=[user_id],
                        embeddings=[facial_features["feature_vector"]],
                        metadatas=[chroma_metadata]
                    )
                    migrated_count += 1
            except Exception as e:
                print(f"Warning: Failed to migrate user {user_id} to ChromaDB: {e}")

    # Mark as migrated
    if "metadata" not in db:
        db["metadata"] = {}
    db["metadata"]["chroma_migrated"] = True

    if migrated_count > 0:
        print(f"Migrated {migrated_count} users from JSON to ChromaDB")


def load_system_config() -> Dict[str, Any]:
    """
    Load system configuration (NOT user data).

    User data is stored in ChromaDB. This function only loads system-level
    configuration like version, migration status, etc.

    Returns:
        Dict containing system configuration
    """
    if INDEX_FILE.exists():
        with open(INDEX_FILE, 'r') as f:
            config = json.load(f)
            # Ensure we have the metadata section
            if "metadata" not in config:
                config["metadata"] = {"version": "1.0", "created": datetime.utcnow().isoformat()}
            # Check for old format with users (for migration)
            if "users" in config and not config.get("metadata", {}).get("chroma_migrated", False):
                # Old database format - trigger migration
                migrate_json_to_chroma(config)
                # After migration, remove users from JSON
                del config["users"]
                save_system_config(config)
    else:
        config = {"metadata": {"version": "1.0", "created": datetime.utcnow().isoformat(), "chroma_migrated": True}}
        save_system_config(config)

    # Initialize ChromaDB
    initialize_chroma()

    return config


def save_system_config(config: Dict[str, Any]) -> None:
    """
    Save system configuration to disk (NOT user data).

    User data is saved to ChromaDB separately.

    Args:
        config: System configuration dictionary to save
    """
    with open(INDEX_FILE, 'w') as f:
        json.dump(config, f, indent=2)


# Backward compatibility aliases
def load_database() -> Dict[str, Any]:
    """Load system config (backward compatibility alias)."""
    return load_system_config()


def save_database(db: Dict[str, Any]) -> None:
    """Save system config (backward compatibility alias)."""
    save_system_config(db)


def generate_user_id(name: str) -> str:
    """Generate a unique user ID based on name and timestamp."""
    timestamp = datetime.utcnow().isoformat()
    unique_string = f"{name}_{timestamp}"
    hash_object = hashlib.sha256(unique_string.encode())
    return f"user_{hash_object.hexdigest()[:12]}"


def extract_user_data_from_chroma_metadata(chroma_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract user data from ChromaDB metadata format.

    Converts ChromaDB metadata format back into user data structure,
    separating custom metadata from system fields.

    Args:
        chroma_metadata: Metadata dictionary from ChromaDB

    Returns:
        Dict containing user data with separated custom metadata
    """
    # Parse bbox from JSON if present
    bbox = chroma_metadata.get("bbox", "[]")
    if isinstance(bbox, str):
        try:
            bbox = json.loads(bbox)
        except:
            bbox = []

    # Build user data structure
    user_data = {
        "user_id": chroma_metadata.get("user_id", ""),
        "name": chroma_metadata.get("name", ""),
        "image_path": chroma_metadata.get("image_path", ""),
        "registration_timestamp": chroma_metadata.get("registration_timestamp", ""),
        "recognition_count": chroma_metadata.get("recognition_count", 0),
        "last_recognized": chroma_metadata.get("last_recognized", None) or None,
        "facial_features": {
            "bbox": bbox,
            "detection_score": chroma_metadata.get("detection_score", 0.0),
            "extraction_timestamp": chroma_metadata.get("extraction_timestamp", ""),
            "landmark_quality": chroma_metadata.get("landmark_quality", 0.0),
            "face_size_ratio": chroma_metadata.get("face_size_ratio", 0.0),
            "num_faces_detected": chroma_metadata.get("num_faces_detected", 1),
        },
        "metadata": {}
    }

    # Extract custom metadata (fields with "custom_" prefix)
    for key, value in chroma_metadata.items():
        if key.startswith("custom_"):
            actual_key = key[7:]  # Remove "custom_" prefix
            # Try to parse JSON strings back to original types
            if isinstance(value, str):
                try:
                    user_data["metadata"][actual_key] = json.loads(value)
                except:
                    user_data["metadata"][actual_key] = value
            else:
                user_data["metadata"][actual_key] = value

    return user_data


def save_image(user_id: str, image_data: str) -> str:
    """Save base64 image data to disk and return the file path."""
    # Decode base64 data
    try:
        # Remove data URL prefix if present
        if ',' in image_data:
            image_data = image_data.split(',', 1)[1]
        
        image_bytes = base64.b64decode(image_data)
        
        # Save to file
        image_path = IMAGES_PATH / f"{user_id}.jpg"
        with open(image_path, 'wb') as f:
            f.write(image_bytes)
        
        return str(image_path)
    except Exception as e:
        raise ValueError(f"Failed to save image: {str(e)}")


def decode_base64_image(image_data: str) -> np.ndarray:
    """
    Decode base64 image data to numpy array.
    
    Args:
        image_data: Base64-encoded image string (with or without data URL prefix)
    
    Returns:
        numpy array in BGR format (OpenCV format)
    """
    try:
        # Remove data URL prefix if present
        if ',' in image_data:
            image_data = image_data.split(',', 1)[1]
        
        # Decode base64
        image_bytes = base64.b64decode(image_data)
        
        # Load image using PIL
        pil_image = Image.open(BytesIO(image_bytes))
        
        # Convert to RGB if needed
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        
        # Convert to numpy array (RGB)
        image_array = np.array(pil_image)
        
        # Convert RGB to BGR for InsightFace (OpenCV format)
        image_bgr = image_array[:, :, ::-1]
        
        return image_bgr
    except Exception as e:
        raise ValueError(f"Failed to decode image: {str(e)}")


def extract_facial_features(image_data: str) -> Dict[str, Any]:
    """
    Extract facial features from image data using InsightFace.
    
    Uses InsightFace's buffalo_l model to detect faces and extract 512-dimensional
    embeddings. The embedding is a normalized vector that represents the facial features.
    
    Args:
        image_data: Base64-encoded image string
    
    Returns:
        Dictionary containing:
            - feature_vector: 512-dimensional face embedding (list of floats)
            - bbox: Face bounding box [x, y, width, height]
            - detection_score: Confidence of face detection (0-1)
            - extraction_timestamp: ISO timestamp
            - landmark_quality: Quality score based on landmark detection
    
    Raises:
        ValueError: If no face is detected or image processing fails
    """
    try:
        # Initialize InsightFace
        app = initialize_face_app()
        
        # Decode image
        image = decode_base64_image(image_data)
        
        # Detect faces and extract features
        faces = app.get(image)
        
        if not faces or len(faces) == 0:
            raise ValueError("No face detected in the image. Please ensure the image contains a clear, front-facing face.")
        
        if len(faces) > 1:
            # If multiple faces detected, use the largest one
            faces = sorted(faces, key=lambda x: (x.bbox[2] - x.bbox[0]) * (x.bbox[3] - x.bbox[1]), reverse=True)
            print(f"Warning: Multiple faces detected ({len(faces)}). Using the largest face.")
        
        # Get the primary face
        face = faces[0]
        
        # Extract embedding (512-dimensional vector)
        embedding = face.embedding
        
        # Get bounding box
        bbox = face.bbox.tolist()  # [x1, y1, x2, y2]
        
        # Get detection score
        det_score = float(face.det_score)
        
        # Calculate a quality score based on face size and detection confidence
        face_area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
        image_area = image.shape[0] * image.shape[1]
        size_ratio = face_area / image_area
        
        # Quality score combines detection confidence and face size
        # Ideal face size is 10-50% of image
        size_quality = min(1.0, size_ratio / 0.1) if size_ratio < 0.5 else max(0.5, 1.0 - (size_ratio - 0.5))
        landmark_quality = (det_score * 0.7) + (size_quality * 0.3)
        
        return {
            "feature_vector": embedding.tolist(),  # Convert numpy array to list for JSON serialization
            "bbox": bbox,
            "detection_score": det_score,
            "extraction_timestamp": datetime.utcnow().isoformat(),
            "landmark_quality": float(landmark_quality),
            "face_size_ratio": float(size_ratio),
            "num_faces_detected": len(faces)
        }
    except ValueError:
        # Re-raise ValueError with original message
        raise
    except Exception as e:
        raise ValueError(f"Failed to extract facial features: {str(e)}")


def compare_faces(features1: Dict[str, Any], features2: Dict[str, Any]) -> float:
    """
    Compare two sets of facial features using cosine distance.
    
    InsightFace embeddings are normalized, so we can use cosine similarity
    (or equivalently, Euclidean distance) to compare faces.
    
    Args:
        features1: First face features dictionary
        features2: Second face features dictionary
    
    Returns:
        Distance score between 0.0 and 2.0 (lower means more similar)
        - 0.0 = identical faces
        - < 0.25 = very likely same person
        - 0.25-0.50 = possibly same person
        - > 0.50 = likely different people
    """
    try:
        # Extract feature vectors
        embedding1 = np.array(features1["feature_vector"])
        embedding2 = np.array(features2["feature_vector"])
        
        # Normalize embeddings (InsightFace embeddings should already be normalized)
        embedding1 = embedding1 / np.linalg.norm(embedding1)
        embedding2 = embedding2 / np.linalg.norm(embedding2)
        
        # Calculate cosine distance (1 - cosine similarity)
        # For normalized vectors, this is equivalent to Euclidean distance / 2
        cosine_sim = np.dot(embedding1, embedding2)
        distance = 1.0 - cosine_sim
        
        return float(distance)
    except Exception as e:
        raise ValueError(f"Failed to compare faces: {str(e)}")


# ============================================================================
# Response Formatting Functions
# ============================================================================

def format_user_profile_markdown(user_data: Dict[str, Any]) -> str:
    """Format user profile data as markdown."""
    output = f"# User Profile: {user_data['name']}\n\n"
    output += f"**User ID:** {user_data['user_id']}\n"
    output += f"**Registered:** {user_data['registration_timestamp']}\n"
    output += f"**Recognition Count:** {user_data.get('recognition_count', 0)}\n\n"
    
    # Show face detection quality if available
    facial_features = user_data.get('facial_features', {})
    if facial_features.get('landmark_quality'):
        output += f"**Face Quality Score:** {facial_features['landmark_quality']:.2%}\n"
    if facial_features.get('detection_score'):
        output += f"**Detection Confidence:** {facial_features['detection_score']:.2%}\n\n"
    
    if user_data.get('metadata'):
        output += "## Metadata\n"
        for key, value in user_data['metadata'].items():
            output += f"- **{key}:** {value}\n"
        output += "\n"
    
    if user_data.get('last_recognized'):
        output += f"**Last Recognized:** {user_data['last_recognized']}\n"
    
    return output


def format_recognition_result_markdown(result: Dict[str, Any]) -> str:
    """Format recognition result as markdown."""
    if result['status'] == RecognitionStatus.RECOGNIZED.value:
        output = f"# ✅ User Recognized\n\n"
        output += f"**Name:** {result['user']['name']}\n"
        output += f"**User ID:** {result['user']['user_id']}\n"
        output += f"**Distance:** {result['distance']:.4f}\n"
        output += f"**Threshold:** {result['threshold']:.4f}\n\n"
        output += f"*Lower distance means better match. Distance < {result['threshold']:.4f} indicates same person.*\n"
    
    elif result['status'] == RecognitionStatus.NOT_RECOGNIZED.value:
        output = "# ❌ User Not Recognized\n\n"
        output += "This face does not match any registered users in the database.\n"
        output += "Use the `skyy_register_user` tool to register new users.\n"
    
    elif result['status'] == RecognitionStatus.LOW_CONFIDENCE.value:
        output = f"# ⚠️ Low Confidence Match\n\n"
        output += f"**Possible Match:** {result.get('user', {}).get('name', 'Unknown')}\n"
        output += f"**Distance:** {result['distance']:.4f}\n"
        output += f"**Threshold:** {result['threshold']:.4f}\n\n"
        output += "The match distance is above the threshold. Consider:\n"
        output += "- Using a clearer image with better lighting\n"
        output += "- Increasing the threshold (less strict matching)\n"
        output += "- Re-registering the user with updated images\n"
        output += "- Ensuring the face is front-facing and clearly visible\n"
    
    else:
        output = "# ❌ Recognition Error\n\n"
        output += f"Error: {result.get('message', 'Unknown error')}\n"
    
    return output


def format_user_list_markdown(users: List[Dict[str, Any]], total: int, offset: int, limit: int) -> str:
    """Format user list as markdown."""
    output = f"# Registered Users ({total} total)\n\n"
    
    if not users:
        output += "No users found.\n"
        return output
    
    for i, user in enumerate(users, start=offset + 1):
        output += f"## {i}. {user['name']}\n"
        output += f"- **User ID:** {user['user_id']}\n"
        output += f"- **Registered:** {user['registration_timestamp']}\n"
        output += f"- **Recognition Count:** {user.get('recognition_count', 0)}\n"
        if user.get('last_recognized'):
            output += f"- **Last Seen:** {user['last_recognized']}\n"
        output += "\n"
    
    # Pagination info
    has_more = total > offset + len(users)
    if has_more:
        next_offset = offset + len(users)
        output += f"\n---\n"
        output += f"Showing {offset + 1}-{offset + len(users)} of {total} users.\n"
        output += f"To see more, use offset={next_offset}\n"
    
    return output


# ============================================================================
# MCP Tools
# ============================================================================

@mcp.tool(
    name="skyy_register_user",
    annotations={
        "title": "Register New User with Facial Recognition",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False
    }
)
@require_auth
async def register_user(params: RegisterUserInput) -> str:
    """Register a new user in the Skyy facial recognition system using InsightFace.
    
    This tool captures and stores a user's facial data using production-grade InsightFace
    facial recognition. The data is stored locally to maintain privacy. Use this when
    registering a new user.
    
    Args:
        params (RegisterUserInput): Validated input containing:
            - name (str): User's full name
            - image_data (str): Base64-encoded facial image
            - metadata (Optional[Dict]): Additional metadata
            - response_format (ResponseFormat): Output format
    
    Returns:
        str: Registration confirmation with user details in the specified format.
             JSON format includes: user_id, name, registration_timestamp, face_quality, metadata
             Markdown format includes: formatted profile with all details
    
    Example Usage:
        To register a new user:
        1. Capture or load image from camera/file
        2. Convert to base64
        3. Call this tool with user's name and image data
        4. Facial features extracted using InsightFace buffalo_l model
        5. Store the registration data locally
    
    Note:
        - Each registration creates a unique user_id
        - Uses InsightFace for robust 512-dimensional face embeddings
        - All data is stored locally (no cloud storage)
        - Images should contain a clear, front-facing face
        - Only one face should be visible in the image
        - Good lighting improves recognition accuracy
    """
    try:
        # Load system config (no user data)
        load_system_config()

        # Generate unique user ID
        user_id = generate_user_id(params.name)

        # Extract facial features using InsightFace
        facial_features = extract_facial_features(params.image_data)

        # Save image to disk
        image_path = save_image(user_id, params.image_data)

        # Current timestamp
        registration_timestamp = datetime.utcnow().isoformat()

        # Build comprehensive metadata for ChromaDB
        chroma_metadata = {
            "user_id": user_id,
            "name": params.name,
            "image_path": image_path,
            "registration_timestamp": registration_timestamp,
            "recognition_count": 0,
            "last_recognized": "",
            # Face detection metadata
            "bbox": json.dumps(facial_features["bbox"]),
            "detection_score": facial_features["detection_score"],
            "extraction_timestamp": facial_features["extraction_timestamp"],
            "landmark_quality": facial_features["landmark_quality"],
            "face_size_ratio": facial_features["face_size_ratio"],
            "num_faces_detected": facial_features["num_faces_detected"],
        }

        # Add custom user metadata fields with prefix to avoid conflicts
        custom_metadata = params.metadata or {}
        for key, value in custom_metadata.items():
            # ChromaDB metadata values must be strings, ints, or floats
            if isinstance(value, (str, int, float, bool)):
                chroma_metadata[f"custom_{key}"] = value
            else:
                # Serialize complex types as JSON strings
                chroma_metadata[f"custom_{key}"] = json.dumps(value)

        # Add embedding AND all metadata to ChromaDB
        collection = initialize_chroma()
        collection.add(
            ids=[user_id],
            embeddings=[facial_features["feature_vector"]],
            metadatas=[chroma_metadata]
        )
        
        # Format response
        if params.response_format == ResponseFormat.JSON:
            response = {
                "status": "success",
                "message": "User registered successfully",
                "user": {
                    "user_id": user_id,
                    "name": params.name,
                    "registration_timestamp": registration_timestamp,
                    "face_quality": {
                        "detection_score": facial_features.get("detection_score"),
                        "landmark_quality": facial_features.get("landmark_quality"),
                        "face_size_ratio": facial_features.get("face_size_ratio")
                    },
                    "metadata": params.metadata
                }
            }
            return json.dumps(response, indent=2)
        else:
            output = f"# Registration Successful\n\n"
            output += f"**User ID:** {user_id}\n"
            output += f"**Name:** {params.name}\n"
            output += f"**Registered:** {registration_timestamp}\n\n"

            output += "## Face Detection Quality\n"
            output += f"- **Detection Confidence:** {facial_features.get('detection_score', 0):.2%}\n"
            output += f"- **Overall Quality:** {facial_features.get('landmark_quality', 0):.2%}\n"
            output += f"- **Face Size:** {facial_features.get('face_size_ratio', 0):.2%} of image\n\n"

            if facial_features.get('num_faces_detected', 1) > 1:
                output += f"Note: {facial_features['num_faces_detected']} faces detected. Using the largest face.\n\n"

            if params.metadata:
                output += "## Metadata\n"
                for key, value in params.metadata.items():
                    output += f"- **{key}:** {value}\n"
                output += "\n"

            output += f"The user has been registered and can now be recognized.\n"
            output += f"Facial data is stored locally at: {DATABASE_PATH}\n"

            return output
    
    except Exception as e:
        error_response = {
            "status": "error",
            "message": f"Registration failed: {str(e)}",
            "suggestion": "Ensure the image contains a clear, front-facing face with good lighting"
        }
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps(error_response, indent=2)
        else:
            return f"# Registration Failed\n\n**Error:** {str(e)}\n\nPlease ensure the image contains a clear, front-facing face."


@mcp.tool(
    name="skyy_recognize_face",
    annotations={
        "title": "Recognize User from Facial Image",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
@require_auth
async def recognize_face(params: RecognizeFaceInput) -> str:
    """Recognize a registered user from a facial image using InsightFace.
    
    This tool analyzes an image using InsightFace to identify if it matches any registered
    user in the database. It returns the user's information if a match is found with
    sufficient confidence (distance below threshold).
    
    Args:
        params (RecognizeFaceInput): Validated input containing:
            - image_data (str): Base64-encoded image to analyze
            - confidence_threshold (Optional[float]): Maximum distance (default 0.25, lower is stricter)
            - response_format (ResponseFormat): Output format
    
    Returns:
        str: Recognition result with matched user details or no-match notification.
             JSON format includes: status, distance, user details (if matched)
             Markdown format includes: formatted result with user profile
    
    Example Usage:
        When user approaches:
        1. Capture image from camera
        2. Call this tool with the image data
        3. If recognized, greet user by name
        4. If not recognized, use standard greeting
    
    Recognition Status:
        - RECOGNIZED: User matched with distance below threshold
        - NOT_RECOGNIZED: No matching user found
        - LOW_CONFIDENCE: Match found but distance above threshold
        - ERROR: Processing error occurred
    
    Distance Interpretation (InsightFace):
        - < 0.20: Very strong match (same person)
        - 0.20-0.25: Strong match (likely same person)
        - 0.25-0.40: Weak match (possibly same person)
        - > 0.40: No match (different people)
    
    Note:
        - Lower distance threshold = stricter matching (fewer false positives)
        - Higher distance threshold = looser matching (may have false positives)
        - Default threshold of 0.25 balances accuracy and usability
        - Image quality and lighting affect recognition accuracy
    """
    try:
        # Load system config
        load_system_config()

        # Query ChromaDB for nearest neighbor
        collection = initialize_chroma()

        # Check if collection has any items
        collection_count = collection.count()
        if collection_count == 0:
            result = {
                "status": RecognitionStatus.NOT_RECOGNIZED.value,
                "message": "No users registered in the database",
                "distance": 1.0
            }

            if params.response_format == ResponseFormat.JSON:
                return json.dumps(result, indent=2)
            else:
                return "# No Users Registered\n\nThere are no users in the database yet. Use `skyy_register_user` to register users."

        # Extract features from input image
        input_features = extract_facial_features(params.image_data)

        # Query ChromaDB with the input embedding
        # ChromaDB returns cosine distance (0 = identical, 2 = opposite)
        results = collection.query(
            query_embeddings=[input_features["feature_vector"]],
            n_results=1,  # Get the closest match
            include=["metadatas", "distances"]
        )

        # Extract results
        if not results["ids"] or not results["ids"][0]:
            result = {
                "status": RecognitionStatus.NOT_RECOGNIZED.value,
                "message": "No matching user found in database",
                "distance": 1.0
            }

            if params.response_format == ResponseFormat.JSON:
                return json.dumps(result, indent=2)
            else:
                return format_recognition_result_markdown(result)

        # Get the best match
        best_user_id = results["ids"][0][0]
        best_distance = results["distances"][0][0]  # ChromaDB cosine distance
        best_metadata = results["metadatas"][0][0] if results["metadatas"] and results["metadatas"][0] else {}

        # Extract user data from ChromaDB metadata
        best_match = extract_user_data_from_chroma_metadata(best_metadata)

        # Determine recognition status based on distance
        # Lower distance = better match
        if best_distance <= params.confidence_threshold:
            # Update recognition stats in ChromaDB
            new_count = best_match.get("recognition_count", 0) + 1
            last_recognized = datetime.utcnow().isoformat()

            # Update metadata in ChromaDB
            updated_metadata = best_metadata.copy()
            updated_metadata["recognition_count"] = new_count
            updated_metadata["last_recognized"] = last_recognized

            try:
                collection.update(
                    ids=[best_user_id],
                    metadatas=[updated_metadata]
                )
            except Exception as e:
                print(f"Warning: Failed to update recognition stats: {e}")

            result = {
                "status": RecognitionStatus.RECOGNIZED.value,
                "distance": best_distance,
                "threshold": params.confidence_threshold,
                "user": {
                    "user_id": best_match["user_id"],
                    "name": best_match["name"],
                    "metadata": best_match.get("metadata", {}),
                    "recognition_count": new_count
                }
            }
        elif best_distance < 0.50:  # Close but not quite
            result = {
                "status": RecognitionStatus.LOW_CONFIDENCE.value,
                "distance": best_distance,
                "threshold": params.confidence_threshold,
                "user": {
                    "user_id": best_match["user_id"],
                    "name": best_match["name"]
                },
                "message": f"Match found but distance ({best_distance:.4f}) is above threshold ({params.confidence_threshold:.4f})"
            }
        else:
            result = {
                "status": RecognitionStatus.NOT_RECOGNIZED.value,
                "distance": best_distance,
                "message": "No matching user found in database"
            }

        # Format response
        if params.response_format == ResponseFormat.JSON:
            return json.dumps(result, indent=2)
        else:
            return format_recognition_result_markdown(result)
    
    except Exception as e:
        error_result = {
            "status": RecognitionStatus.ERROR.value,
            "message": f"Recognition failed: {str(e)}",
            "distance": 1.0
        }
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps(error_result, indent=2)
        else:
            return f"# Recognition Error\n\n**Error:** {str(e)}\n\nPlease ensure the image contains a clear face and try again."


@mcp.tool(
    name="skyy_get_user_profile",
    annotations={
        "title": "Get User Profile Details",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
@require_auth
async def get_user_profile(params: GetUserProfileInput) -> str:
    """Retrieve detailed profile information for a registered user.
    
    This tool fetches complete profile data for a specific user, including their
    metadata and recognition history.
    
    Args:
        params (GetUserProfileInput): Validated input containing:
            - user_id (str): Unique identifier for the user
            - response_format (ResponseFormat): Output format
    
    Returns:
        str: Complete user profile with all stored information.
             JSON format includes: user_id, name, metadata, timestamps, recognition_count
             Markdown format includes: formatted profile with all details
    
    Example Usage:
        After recognizing a user, fetch their profile to:
        - View their interaction history
        - Retrieve custom metadata
        - Check recognition statistics
    
    Error Handling:
        Returns error if user_id not found, suggesting to check registered users
        with `skyy_list_users` tool.
    """
    try:
        # Load system config
        load_system_config()

        # Get user from ChromaDB
        collection = initialize_chroma()

        try:
            result = collection.get(
                ids=[params.user_id],
                include=["metadatas"]
            )

            if not result["ids"] or not result["ids"]:
                error = {
                    "status": "error",
                    "message": f"User ID '{params.user_id}' not found",
                    "suggestion": "Use skyy_list_users to see all registered users"
                }

                if params.response_format == ResponseFormat.JSON:
                    return json.dumps(error, indent=2)
                else:
                    return f"# User Not Found\n\n**User ID:** {params.user_id}\n\nThis user is not registered. Use `skyy_list_users` to see all registered users."

            # Extract user data from ChromaDB metadata
            chroma_metadata = result["metadatas"][0] if result["metadatas"] else {}
            user_data = extract_user_data_from_chroma_metadata(chroma_metadata)

            # Format response
            if params.response_format == ResponseFormat.JSON:
                # Return sanitized user data (without internal paths)
                response = {
                    "user_id": user_data["user_id"],
                    "name": user_data["name"],
                    "metadata": user_data.get("metadata", {}),
                    "registration_timestamp": user_data["registration_timestamp"],
                    "recognition_count": user_data.get("recognition_count", 0),
                    "last_recognized": user_data.get("last_recognized")
                }
                return json.dumps(response, indent=2)
            else:
                return format_user_profile_markdown(user_data)
        except Exception as e:
            error = {
                "status": "error",
                "message": f"User ID '{params.user_id}' not found",
                "suggestion": "Use skyy_list_users to see all registered users"
            }

            if params.response_format == ResponseFormat.JSON:
                return json.dumps(error, indent=2)
            else:
                return f"# User Not Found\n\n**User ID:** {params.user_id}\n\nThis user is not registered. Use `skyy_list_users` to see all registered users."
    
    except Exception as e:
        error = {
            "status": "error",
            "message": f"Failed to retrieve profile: {str(e)}"
        }

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(error, indent=2)
        else:
            return f"# Error\n\n{str(e)}"


@mcp.tool(
    name="skyy_list_users",
    annotations={
        "title": "List All Registered Users",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
@require_auth
async def list_users(params: ListUsersInput) -> str:
    """List all users registered in the facial recognition system.
    
    This tool retrieves a paginated list of all registered users with their basic
    information and recognition statistics. Useful for system administration and
    user management.
    
    Args:
        params (ListUsersInput): Validated input containing:
            - limit (Optional[int]): Maximum users to return (default 20, max 100)
            - offset (Optional[int]): Number of users to skip (default 0)
            - response_format (ResponseFormat): Output format
    
    Returns:
        str: List of registered users with pagination information.
             JSON format includes: total count, users array, pagination info
             Markdown format includes: formatted list with user details
    
    Example Usage:
        - View all registered users
        - Check registration status before adding new users
        - Monitor system usage through recognition counts
        - Navigate through large user lists with pagination
    
    Pagination:
        For large user bases, use offset and limit to paginate through results.
        The response includes has_more and next_offset for easy pagination.
    """
    try:
        # Load system config
        load_system_config()

        # Get all users from ChromaDB
        collection = initialize_chroma()

        # Get all users
        result = collection.get(
            include=["metadatas"]
        )

        if not result["ids"]:
            # No users in database
            if params.response_format == ResponseFormat.JSON:
                response = {
                    "total": 0,
                    "count": 0,
                    "offset": 0,
                    "limit": params.limit,
                    "has_more": False,
                    "next_offset": None,
                    "users": []
                }
                return json.dumps(response, indent=2)
            else:
                return "# Registered Users (0 total)\n\nNo users found.\n"

        # Extract user data from ChromaDB metadata
        users_list = []
        for i, user_id in enumerate(result["ids"]):
            chroma_metadata = result["metadatas"][i] if result["metadatas"] and i < len(result["metadatas"]) else {}
            user_data = extract_user_data_from_chroma_metadata(chroma_metadata)
            users_list.append(user_data)

        # Sort by registration date (newest first)
        users_list.sort(key=lambda x: x.get("registration_timestamp", ""), reverse=True)

        # Pagination
        total = len(users_list)
        paginated_users = users_list[params.offset:params.offset + params.limit]

        # Format response
        if params.response_format == ResponseFormat.JSON:
            has_more = total > params.offset + len(paginated_users)
            response = {
                "total": total,
                "count": len(paginated_users),
                "offset": params.offset,
                "limit": params.limit,
                "has_more": has_more,
                "next_offset": params.offset + len(paginated_users) if has_more else None,
                "users": [
                    {
                        "user_id": user["user_id"],
                        "name": user["name"],
                        "registration_timestamp": user["registration_timestamp"],
                        "recognition_count": user.get("recognition_count", 0),
                        "last_recognized": user.get("last_recognized")
                    }
                    for user in paginated_users
                ]
            }
            return json.dumps(response, indent=2)
        else:
            return format_user_list_markdown(paginated_users, total, params.offset, params.limit)
    
    except Exception as e:
        error = {
            "status": "error",
            "message": f"Failed to list users: {str(e)}"
        }

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(error, indent=2)
        else:
            return f"# Error\n\n{str(e)}"


@mcp.tool(
    name="skyy_update_user",
    annotations={
        "title": "Update User Information",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
@require_auth
async def update_user(params: UpdateUserInput) -> str:
    """Update information for an existing registered user.
    
    This tool allows modification of user details including name and metadata.
    Useful for correcting information or updating user metadata over time.
    
    Args:
        params (UpdateUserInput): Validated input containing:
            - user_id (str): ID of user to update
            - name (Optional[str]): New name
            - metadata (Optional[Dict]): New metadata (replaces existing)
            - response_format (ResponseFormat): Output format
    
    Returns:
        str: Updated user profile confirmation.
             JSON format includes: updated user data
             Markdown format includes: formatted updated profile
    
    Example Usage:
        - Correct misspelled names
        - Add or modify custom metadata
    
    Note:
        - Only provided fields are updated; others remain unchanged
        - Metadata is replaced entirely, not merged
        - Facial data and recognition history are not affected
    
    Error Handling:
        Returns error if user_id not found or if update fails.
    """
    try:
        # Load system config
        load_system_config()

        # Get user from ChromaDB
        collection = initialize_chroma()

        # Check if user exists
        try:
            result = collection.get(
                ids=[params.user_id],
                include=["metadatas"]
            )

            if not result["ids"] or not result["ids"]:
                error = {
                    "status": "error",
                    "message": f"User ID '{params.user_id}' not found",
                    "suggestion": "Use skyy_list_users to see all registered users"
                }

                if params.response_format == ResponseFormat.JSON:
                    return json.dumps(error, indent=2)
                else:
                    return f"# User Not Found\n\n**User ID:** {params.user_id}\n\nThis user is not registered."

            # Get existing metadata
            existing_metadata = result["metadatas"][0] if result["metadatas"] else {}

            # Update fields
            updated_metadata = existing_metadata.copy()

            if params.name is not None:
                updated_metadata["name"] = params.name

            if params.metadata is not None:
                # Remove old custom metadata
                keys_to_remove = [k for k in updated_metadata.keys() if k.startswith("custom_")]
                for key in keys_to_remove:
                    del updated_metadata[key]

                # Add new custom metadata
                for key, value in params.metadata.items():
                    # ChromaDB metadata values must be strings, ints, or floats
                    if isinstance(value, (str, int, float, bool)):
                        updated_metadata[f"custom_{key}"] = value
                    else:
                        # Serialize complex types as JSON strings
                        updated_metadata[f"custom_{key}"] = json.dumps(value)

            # Save changes to ChromaDB
            collection.update(
                ids=[params.user_id],
                metadatas=[updated_metadata]
            )

            # Extract updated user data for response
            user_data = extract_user_data_from_chroma_metadata(updated_metadata)

            # Format response
            if params.response_format == ResponseFormat.JSON:
                response = {
                    "status": "success",
                    "message": "User updated successfully",
                    "user": {
                        "user_id": user_data["user_id"],
                        "name": user_data["name"],
                        "metadata": user_data.get("metadata", {})
                    }
                }
                return json.dumps(response, indent=2)
            else:
                output = f"# User Updated\n\n"
                output += format_user_profile_markdown(user_data)
                return output
        except Exception as e:
            error = {
                "status": "error",
                "message": f"User ID '{params.user_id}' not found",
                "suggestion": "Use skyy_list_users to see all registered users"
            }

            if params.response_format == ResponseFormat.JSON:
                return json.dumps(error, indent=2)
            else:
                return f"# User Not Found\n\n**User ID:** {params.user_id}\n\nThis user is not registered."
    
    except Exception as e:
        error = {
            "status": "error",
            "message": f"Failed to update user: {str(e)}"
        }

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(error, indent=2)
        else:
            return f"# Error\n\n{str(e)}"


@mcp.tool(
    name="skyy_delete_user",
    annotations={
        "title": "Delete Registered User",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False
    }
)
@require_auth
async def delete_user(params: DeleteUserInput) -> str:
    """Delete a user from the facial recognition system.
    
    This tool permanently removes a user's profile, facial data, and associated
    images from the system. This operation cannot be undone.
    
    Args:
        params (DeleteUserInput): Validated input containing:
            - user_id (str): ID of user to delete
            - response_format (ResponseFormat): Output format
    
    Returns:
        str: Deletion confirmation.
             JSON format includes: status and deleted user_id
             Markdown format includes: formatted confirmation
    
    Example Usage:
        - Remove users who no longer need access
        - Clean up test data
        - Comply with data deletion requests
    
    Warning:
        This is a destructive operation that cannot be undone. All user data,
        including facial images and recognition history, will be permanently deleted.
    
    Error Handling:
        Returns error if user_id not found or deletion fails.
    """
    try:
        # Load system config
        load_system_config()

        # Get user from ChromaDB
        collection = initialize_chroma()

        try:
            result = collection.get(
                ids=[params.user_id],
                include=["metadatas"]
            )

            if not result["ids"] or not result["ids"]:
                error = {
                    "status": "error",
                    "message": f"User ID '{params.user_id}' not found",
                    "suggestion": "Use skyy_list_users to see all registered users"
                }

                if params.response_format == ResponseFormat.JSON:
                    return json.dumps(error, indent=2)
                else:
                    return f"# User Not Found\n\n**User ID:** {params.user_id}\n\nThis user is not registered."

            # Extract user data
            chroma_metadata = result["metadatas"][0] if result["metadatas"] else {}
            user_data = extract_user_data_from_chroma_metadata(chroma_metadata)
            user_name = user_data["name"]
            image_path = user_data.get("image_path", "")

            # Delete image file if exists
            if image_path:
                image_path_obj = Path(image_path)
                if image_path_obj.exists():
                    image_path_obj.unlink()

            # Remove from ChromaDB
            try:
                collection.delete(ids=[params.user_id])
            except Exception as e:
                print(f"Warning: Failed to delete user from ChromaDB: {e}")

            # Format response
            if params.response_format == ResponseFormat.JSON:
                response = {
                    "status": "success",
                    "message": "User deleted successfully",
                    "deleted_user_id": params.user_id,
                    "deleted_user_name": user_name
                }
                return json.dumps(response, indent=2)
            else:
                return f"# User Deleted\n\n**User ID:** {params.user_id}\n**Name:** {user_name}\n\nThe user has been permanently removed from the system."
        except Exception as e:
            error = {
                "status": "error",
                "message": f"User ID '{params.user_id}' not found",
                "suggestion": "Use skyy_list_users to see all registered users"
            }

            if params.response_format == ResponseFormat.JSON:
                return json.dumps(error, indent=2)
            else:
                return f"# User Not Found\n\n**User ID:** {params.user_id}\n\nThis user is not registered."
    
    except Exception as e:
        error = {
            "status": "error",
            "message": f"Failed to delete user: {str(e)}"
        }

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(error, indent=2)
        else:
            return f"# Error\n\n{str(e)}"


@mcp.tool(
    name="skyy_get_database_stats",
    annotations={
        "title": "Get Database Statistics",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
@require_auth
async def get_database_stats(params: GetDatabaseStatsInput) -> str:
    """Get statistics about the facial recognition database.
    
    This tool provides overview statistics about the system including total users,
    recognition counts, and database metadata.
    
    Args:
        params (GetDatabaseStatsInput): Input parameters including access_token and response_format

    Returns:
        str: Database statistics and system information.
             JSON format includes: total_users, total_recognitions, most_active_user, etc.
             Markdown format includes: formatted statistics report
    
    Example Usage:
        - Monitor system usage
        - Generate usage reports
        - Verify system health
        - Track recognition patterns
    """
    try:
        db = load_database()
        users = db.get("users", {})
        
        total_users = len(users)
        total_recognitions = sum(user.get("recognition_count", 0) for user in users.values())
        
        # Find most recognized user
        most_active_user = None
        max_recognitions = 0
        for user in users.values():
            count = user.get("recognition_count", 0)
            if count > max_recognitions:
                max_recognitions = count
                most_active_user = user
        
        stats = {
            "total_users": total_users,
            "total_recognitions": total_recognitions,
            "database_version": db.get("metadata", {}).get("version", "unknown"),
            "database_created": db.get("metadata", {}).get("created"),
            "storage_location": str(DATABASE_PATH)
        }
        
        if most_active_user:
            stats["most_active_user"] = {
                "name": most_active_user["name"],
                "user_id": most_active_user["user_id"],
                "recognition_count": most_active_user.get("recognition_count", 0)
            }
        
        # Format response
        if params.response_format == ResponseFormat.JSON:
            return json.dumps(stats, indent=2)
        else:
            output = "# 📊 Database Statistics\n\n"
            output += f"**Total Users:** {stats['total_users']}\n"
            output += f"**Total Recognitions:** {stats['total_recognitions']}\n"
            output += f"**Database Version:** {stats['database_version']}\n"
            output += f"**Storage Location:** {stats['storage_location']}\n\n"
            
            if most_active_user:
                output += "## Most Active User\n"
                output += f"**Name:** {most_active_user['name']}\n"
                output += f"**Recognitions:** {most_active_user.get('recognition_count', 0)}\n"
            
            return output
    
    except Exception as e:
        error = {
            "status": "error",
            "message": f"Failed to get statistics: {str(e)}"
        }

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(error, indent=2)
        else:
            return f"# ❌ Error\n\n{str(e)}"


# ============================================================================
# Server Entry Point
# ============================================================================

if __name__ == "__main__":
    # Run the MCP server with stdio transport
    mcp.run()
