"""Tracing utility for debug logging.

This module provides a trace function for structured debug logging throughout
the wallet toolbox.
"""

import logging
from typing import Any


def trace(logger: logging.Logger, event: str, **kwargs: Any) -> None:
    """Log a trace event with optional context information.

    Args:
        logger: The logger instance to use for logging
        event: The event name/identifier
        **kwargs: Optional context information to include in the log message
    """
    if logger.isEnabledFor(logging.DEBUG):
        if kwargs:
            # Format kwargs as key=value pairs
            context_parts = []
            for key, value in kwargs.items():
                if isinstance(value, (str, int, float, bool)):
                    context_parts.append(f"{key}={value}")
                elif value is None:
                    context_parts.append(f"{key}=None")
                else:
                    # For complex objects, just show the type and a truncated repr
                    value_repr = repr(value)
                    if len(value_repr) > 100:
                        value_repr = value_repr[:97] + "..."
                    context_parts.append(f"{key}={value_repr}")

            context = " ".join(context_parts)
            logger.debug(f"[{event}] {context}")
        else:
            logger.debug(f"[{event}]")
