"""Stamp log utilities for debugging and tracing.

This module provides utilities for stamping logs with timestamps and
formatting log output for debugging purposes.
"""

from typing import Any, Dict
from datetime import datetime


def stamp_log(log: Dict[str, Any] | None, message: str) -> None:
    """Add a timestamped message to a log dictionary.
    
    Args:
        log: Log dictionary (can be None for no-op).
        message: Message to log.
    """
    if log is None:
        return
    
    if not isinstance(log, dict):
        return
    
    if 'entries' not in log:
        log['entries'] = []
    
    timestamp = datetime.utcnow().isoformat()
    log['entries'].append({'timestamp': timestamp, 'message': message})


def stamp_log_format(log: Dict[str, Any] | None) -> str:
    """Format a log dictionary for display.
    
    Args:
        log: Log dictionary (can be None).
    
    Returns:
        Formatted log string.
    """
    if log is None or not isinstance(log, dict):
        return ""
    
    entries = log.get('entries', [])
    if not entries:
        return ""
    
    lines = []
    for entry in entries:
        timestamp = entry.get('timestamp', 'unknown')
        message = entry.get('message', '')
        lines.append(f"[{timestamp}] {message}")
    
    return '\n'.join(lines)
