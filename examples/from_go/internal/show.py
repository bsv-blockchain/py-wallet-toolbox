"""Console output formatting utilities.

Replicates the functionality of Go's internal/show package for consistent output.
"""

import sys
from typing import Any, Dict, List, Optional

# ANSI color codes
COLOR_RESET = "\033[0m"
COLOR_RED = "\033[31m"
COLOR_GREEN = "\033[32m"
COLOR_YELLOW = "\033[33m"
COLOR_BLUE = "\033[34m"
COLOR_PURPLE = "\033[35m"
COLOR_CYAN = "\033[36m"
COLOR_WHITE = "\033[37m"
COLOR_BOLD = "\033[1m"


def step(actor: str, description: str) -> None:
    """Display a formatted step in the process with an actor and description."""
    print(f"\n{COLOR_BLUE}{COLOR_BOLD}=== STEP ==={COLOR_RESET}")
    print(f"{COLOR_GREEN}{actor}{COLOR_RESET} is performing: {description}")
    print("-" * 50)


def success(message: str) -> None:
    """Display a success message."""
    print(f"{COLOR_GREEN}{COLOR_BOLD}✅ SUCCESS:{COLOR_RESET} {message}")


def error(message: str) -> None:
    """Display an error message."""
    print(f"{COLOR_RED}{COLOR_BOLD}❌ ERROR:{COLOR_RESET} {message}")


def transaction(txid: str) -> None:
    """Display transaction information."""
    print(f"\n{COLOR_PURPLE}{COLOR_BOLD}🔗 TRANSACTION:{COLOR_RESET}")
    print(f"   TxID: {txid}")


def separator() -> None:
    """Print a visual separator."""
    print("=" * 60)


def header(title: str) -> None:
    """Display a section header."""
    print(f"\n{'=' * 60}")
    print(f"{COLOR_BOLD}{title.upper()}{COLOR_RESET}")
    print(f"{'=' * 60}")


def info(label: str, value: Any) -> None:
    """Display general information."""
    print(f"{COLOR_CYAN}{label}:{COLOR_RESET} {value}")


def process_start(process_name: str) -> None:
    """Indicate the beginning of a process."""
    print(f"\n{COLOR_GREEN}{COLOR_BOLD}🚀 STARTING:{COLOR_RESET} {process_name}")
    separator()


def process_complete(process_name: str) -> None:
    """Indicate the completion of a process."""
    separator()
    print(f"{COLOR_GREEN}{COLOR_BOLD}🎉 COMPLETED:{COLOR_RESET} {process_name}\n")


def wallet_success(method_name: str, args: Any, result: Any) -> None:
    """Display a successful wallet method call with its arguments and result."""
    print(f"\n{COLOR_BLUE}{COLOR_BOLD} WALLET CALL:{COLOR_RESET} {COLOR_GREEN}{method_name}{COLOR_RESET}")
    print(f"{COLOR_CYAN}Args:{COLOR_RESET} {args}")
    print(f"{COLOR_GREEN}{COLOR_BOLD}✅ Result:{COLOR_RESET} {result}")


def wallet_error(method_name: str, args: Any, err: Exception) -> None:
    """Display a failed wallet method call with its arguments and error."""
    print(f"\n{COLOR_BLUE}{COLOR_BOLD} WALLET CALL:{COLOR_RESET} {COLOR_RED}{method_name}{COLOR_RESET}")
    print(f"{COLOR_CYAN}Args:{COLOR_RESET} {args}")
    print(f"{COLOR_RED}{COLOR_BOLD}❌ Error:{COLOR_RESET} {err}")


def print_table(title: str, headers: List[str], rows: List[List[str]]) -> None:
    """Print a table with headers and rows."""
    if title:
        print(title)

    col_w = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(col_w):
                col_w[i] = max(col_w[i], len(str(cell)))

    # Print headers
    header_row = "  ".join(f"{h:<{w}}" for h, w in zip(headers, col_w))
    print(header_row)
    print("  ".join("-" * w for w in col_w))

    # Print rows
    for row in rows:
        print("  ".join(f"{str(cell):<{w}}" for cell, w in zip(row, col_w)))


def beef(beef_hex: str) -> None:
    """Display BEEF HEX."""
    header("BEEF HEX")
    print(f'"{beef_hex}"')

