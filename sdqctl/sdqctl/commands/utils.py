"""
Shared utilities for command implementations.
"""

import asyncio
from typing import Any, Coroutine


def run_async(coro: Coroutine[Any, Any, Any]) -> Any:
    """Execute an async coroutine synchronously.

    Provides consistent async execution across all commands.
    Centralizes error handling and event loop management.

    Usage:
        def my_command(...):
            run_async(_my_command_async(...))
    """
    return asyncio.run(coro)
