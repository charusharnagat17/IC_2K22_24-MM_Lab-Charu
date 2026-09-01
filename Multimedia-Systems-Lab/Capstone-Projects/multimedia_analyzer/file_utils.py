"""
File Utilities Module
---------------------
Responsible for:
- File existence verification
- File size calculation (raw and formatted)
- File extension extraction
- Media type identification (IMAGE, AUDIO, VIDEO, UNKNOWN)
"""

import os
import mimetypes

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff', '.tif', '.gif'}
AUDIO_EXTENSIONS = {'.mp3', '.wav', '.aac', '.flac', '.ogg', '.m4a', '.wma', '.opus', '.aiff'}
VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv', '.wmv', '.m4v', '.3gp'}


def file_exists(file_path):
    """Check if the specified file exists and is a regular file."""
    return os.path.exists(file_path) and os.path.isfile(file_path)


def get_file_extension(file_path):
    """Extract lowercase file extension including leading dot (e.g. '.mp4')."""
    return os.path.splitext(file_path)[1].lower()


def get_file_size(file_path):
    """Return raw file size in bytes."""
    if not file_exists(file_path):
        return 0
    return os.path.getsize(file_path)


def format_file_size(size_bytes):
    """Format size in bytes to human-readable string (B, KB, MB, GB)."""
    try:
        size = float(size_bytes)
    except (ValueError, TypeError):
        return "N/A"

    if size < 1024:
        return f"{int(size)} bytes"
    elif size < 1024 * 1024:
        return f"{size / 1024:.2f} KB ({int(size):,} bytes)"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.2f} MB ({int(size):,} bytes)"
    else:
        return f"{size / (1024 * 1024 * 1024):.2f} GB ({int(size):,} bytes)"


def identify_file_type(file_path):
    """
    Identifies the media type of the file.
    Returns: 'IMAGE', 'AUDIO', 'VIDEO', or 'UNKNOWN'
    """
    if not file_exists(file_path):
        return 'UNKNOWN'

    ext = get_file_extension(file_path)

    if ext in IMAGE_EXTENSIONS:
        return 'IMAGE'
    elif ext in AUDIO_EXTENSIONS:
        return 'AUDIO'
    elif ext in VIDEO_EXTENSIONS:
        return 'VIDEO'

    # Fallback to MIME type identification if extension is ambiguous
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type:
        if mime_type.startswith('image/'):
            return 'IMAGE'
        elif mime_type.startswith('audio/'):
            return 'AUDIO'
        elif mime_type.startswith('video/'):
            return 'VIDEO'

    return 'UNKNOWN'


def get_file_info(file_path):
    """
    Returns a dictionary of basic file attributes.
    """
    exists = file_exists(file_path)
    size_bytes = get_file_size(file_path) if exists else 0
    ext = get_file_extension(file_path) if exists else ""
    file_type = identify_file_type(file_path) if exists else "UNKNOWN"
    file_name = os.path.basename(file_path) if exists else ""

    return {
        "file_path": os.path.abspath(file_path) if exists else file_path,
        "file_name": file_name,
        "file_exists": exists,
        "file_size_bytes": size_bytes,
        "file_size_formatted": format_file_size(size_bytes),
        "extension": ext,
        "media_type": file_type
    }
