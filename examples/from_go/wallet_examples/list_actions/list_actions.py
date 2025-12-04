import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

"""List Actions Example.

This example demonstrates how to list actions for the Alice wallet.
"""

from internal import setup, show

# DefaultLimit is the default number of actions to retrieve
DEFAULT_LIMIT = 100

# DefaultOffset is the default starting position for pagination
DEFAULT_OFFSET = 0

# DefaultOriginator specifies the originator domain or FQDN used to identify the source of the action listing request.
DEFAULT_ORIGINATOR = "example.com"

# DefaultIncludeLabels determines whether to include labels in the response
DEFAULT_INCLUDE_LABELS = True


def default_list_actions_args() -> dict:
    """Create default arguments for listing wallet actions."""
    return {
        "limit": DEFAULT_LIMIT,
        "offset": DEFAULT_OFFSET,
        "includeLabels": DEFAULT_INCLUDE_LABELS,
    }


def main() -> None:
    show.process_start("List Actions")

    alice = setup.create_alice()
    alice_wallet, cleanup = alice.create_wallet()
    try:
        show.step("Alice", "Listing actions")

        # Configure pagination and filtering parameters
        args = default_list_actions_args()
        show.info("ListActionsArgs", args)
        show.separator()

        # Retrieve paginated list of wallet actions
        # actions, err := aliceWallet.ListActions(ctx, args, DefaultOriginator)
        actions = alice_wallet.list_actions(args, DEFAULT_ORIGINATOR)

        show.info("Actions", actions)
        show.process_complete("List Actions")

    finally:
        cleanup()


if __name__ == "__main__":
    main()

