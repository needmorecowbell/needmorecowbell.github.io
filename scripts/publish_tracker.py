#!/usr/bin/env python3
"""
Publish Tracking Module

This module handles tracking which Obsidian notes have been published to the Hugo blog.
It uses a JSON file (.published.json) to record file hashes, preventing duplicate publishing.
"""

import hashlib
import json
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime

# Default location for the tracking file (relative to scripts directory)
DEFAULT_TRACKING_FILE = Path(__file__).parent / '.published.json'


def compute_file_hash(file_path: Path) -> str:
    """
    Compute a SHA-256 hash of a file's contents.

    This hash is used to track whether a note has been modified since
    it was last published. Only the file contents are hashed, not metadata.

    Args:
        file_path: Path to the file to hash

    Returns:
        Hexadecimal string of the SHA-256 hash

    Raises:
        FileNotFoundError: If the file doesn't exist
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hasher = hashlib.sha256()
    content = file_path.read_bytes()
    hasher.update(content)
    return hasher.hexdigest()


def load_publish_state(tracking_file: Path = None) -> Dict[str, Any]:
    """
    Load the publish tracking state from the JSON file.

    Args:
        tracking_file: Path to the tracking file. Defaults to .published.json

    Returns:
        Dict containing publish state, or empty dict if file doesn't exist
    """
    if tracking_file is None:
        tracking_file = DEFAULT_TRACKING_FILE

    tracking_file = Path(tracking_file)
    if not tracking_file.exists():
        return {'published': {}}

    try:
        content = tracking_file.read_text(encoding='utf-8')
        data = json.loads(content)
        # Ensure the expected structure exists
        if 'published' not in data:
            data['published'] = {}
        return data
    except (json.JSONDecodeError, OSError):
        # Return empty state if file is corrupted or unreadable
        return {'published': {}}


def save_publish_state(state: Dict[str, Any], tracking_file: Path = None) -> None:
    """
    Save the publish tracking state to the JSON file.

    Args:
        state: Dict containing publish state
        tracking_file: Path to the tracking file. Defaults to .published.json
    """
    if tracking_file is None:
        tracking_file = DEFAULT_TRACKING_FILE

    tracking_file = Path(tracking_file)

    # Ensure parent directory exists
    tracking_file.parent.mkdir(parents=True, exist_ok=True)

    content = json.dumps(state, indent=2, sort_keys=True)
    tracking_file.write_text(content, encoding='utf-8')


def is_note_published(
    note_path: Path,
    tracking_file: Path = None,
    state: Dict[str, Any] = None
) -> bool:
    """
    Check if a note has been published (and hasn't changed since).

    A note is considered published if:
    1. It exists in the tracking file
    2. Its current content hash matches the recorded hash

    Args:
        note_path: Path to the Obsidian note
        tracking_file: Path to the tracking file. Defaults to .published.json
        state: Optional pre-loaded state dict (to avoid repeated file reads)

    Returns:
        True if the note has been published and hasn't changed, False otherwise
    """
    note_path = Path(note_path).resolve()
    note_key = str(note_path)

    if state is None:
        state = load_publish_state(tracking_file)

    published = state.get('published', {})

    if note_key not in published:
        return False

    # Check if the file hash matches
    try:
        current_hash = compute_file_hash(note_path)
        recorded_hash = published[note_key].get('hash')
        return current_hash == recorded_hash
    except FileNotFoundError:
        return False


def record_published(
    note_path: Path,
    target_path: Path = None,
    tracking_file: Path = None,
    state: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Record that a note has been published.

    Args:
        note_path: Path to the Obsidian note that was published
        target_path: Path to the Hugo post that was written (optional)
        tracking_file: Path to the tracking file. Defaults to .published.json
        state: Optional pre-loaded state dict (to avoid repeated file reads)

    Returns:
        Updated state dict
    """
    note_path = Path(note_path).resolve()
    note_key = str(note_path)

    if state is None:
        state = load_publish_state(tracking_file)

    if 'published' not in state:
        state['published'] = {}

    # Compute the current hash
    current_hash = compute_file_hash(note_path)

    # Record the publish info
    record = {
        'hash': current_hash,
        'published_at': datetime.now().isoformat(),
        'source': str(note_path)
    }

    if target_path:
        record['target'] = str(target_path)

    state['published'][note_key] = record

    # Save the updated state
    save_publish_state(state, tracking_file)

    return state


def get_unpublished_notes(
    notes: list,
    tracking_file: Path = None
) -> list:
    """
    Filter a list of notes to only those that haven't been published yet.

    A note is considered unpublished if:
    1. It doesn't exist in the tracking file, OR
    2. Its content has changed since it was last published

    Args:
        notes: List of note dicts with 'path' key (from find_publishable_notes)
        tracking_file: Path to the tracking file. Defaults to .published.json

    Returns:
        Filtered list containing only unpublished notes
    """
    state = load_publish_state(tracking_file)

    unpublished = []
    for note in notes:
        note_path = note['path']
        if not is_note_published(note_path, state=state):
            unpublished.append(note)

    return unpublished


def clear_publish_record(
    note_path: Path,
    tracking_file: Path = None
) -> bool:
    """
    Remove a note from the publish tracking file.

    This is useful for forcing a note to be re-published.

    Args:
        note_path: Path to the Obsidian note to untrack
        tracking_file: Path to the tracking file. Defaults to .published.json

    Returns:
        True if the note was removed, False if it wasn't tracked
    """
    note_path = Path(note_path).resolve()
    note_key = str(note_path)

    state = load_publish_state(tracking_file)
    published = state.get('published', {})

    if note_key in published:
        del published[note_key]
        save_publish_state(state, tracking_file)
        return True

    return False


def get_publish_info(
    note_path: Path,
    tracking_file: Path = None
) -> Optional[Dict[str, Any]]:
    """
    Get the publish information for a note.

    Args:
        note_path: Path to the Obsidian note
        tracking_file: Path to the tracking file. Defaults to .published.json

    Returns:
        Dict with publish info if note was published, None otherwise
    """
    note_path = Path(note_path).resolve()
    note_key = str(note_path)

    state = load_publish_state(tracking_file)
    published = state.get('published', {})

    return published.get(note_key)
