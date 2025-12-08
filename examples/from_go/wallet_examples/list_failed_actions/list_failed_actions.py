import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

"""List Failed Actions Example.

This example demonstrates how to list failed actions for the Alice wallet.
"""

from internal import setup, show

# DefaultLimit is the default number of actions to retrieve
DEFAULT_LIMIT = 100

# DefaultOffset is the default starting position for pagination
DEFAULT_OFFSET = 0

# DefaultIncludeLabels determines whether to include labels in the response
DEFAULT_INCLUDE_LABELS = True

# DefaultUnfail determines whether to request unfail processing for returned failed actions
DEFAULT_UNFAIL = False


def default_list_failed_actions_args() -> dict:
    """Create default arguments for listing failed wallet actions."""
    return {
        "limit": DEFAULT_LIMIT,
        "offset": DEFAULT_OFFSET,
        "includeLabels": DEFAULT_INCLUDE_LABELS,
    }


def main() -> None:
    show.process_start("List Failed Actions")

    alice = setup.create_alice()
    alice_wallet, cleanup = alice.create_wallet()
    try:
        show.step("Alice", "Listing failed actions")

        # Configure pagination and filtering parameters
        args = default_list_failed_actions_args()
        show.info("ListFailedActionsArgs", args)
        show.info("Unfail", DEFAULT_UNFAIL)
        show.separator()

        # Retrieve paginated list of failed wallet actions
        actions = alice_wallet.list_failed_actions(args, DEFAULT_UNFAIL)

        show.info("FailedActions", actions)
        show.process_complete("List Failed Actions")

    finally:
        cleanup()


if __name__ == "__main__":
    main()

