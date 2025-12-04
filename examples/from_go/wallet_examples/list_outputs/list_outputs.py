import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

"""List Outputs Example.

This example demonstrates how to list outputs for the Alice wallet using default arguments.
It shows the complete flow from wallet creation to output listing with proper error handling.
"""

from internal import setup, show

# DefaultLimit is the default number of outputs to retrieve.
DEFAULT_LIMIT = 100

# DefaultOffset is the default starting position for pagination.
DEFAULT_OFFSET = 0

# DefaultOriginator specifies the originator domain or FQDN used to identify the source of the output listing request.
DEFAULT_ORIGINATOR = "example.com"

# DefaultIncludeLabels is the default value for including labels in the response.
DEFAULT_INCLUDE_LABELS = True

# DefaultBasket is the default basket to list outputs from, if empty it will list from all baskets.
DEFAULT_BASKET = ""

# DefaultTags is the default tags to list outputs from.
DEFAULT_TAGS = []

# DefaultTagQueryMode is the default mode for querying tags (All or Any).
DEFAULT_TAG_QUERY_MODE = "any"


def default_list_outputs_args() -> dict:
    """Create default arguments for listing wallet outputs."""
    return {
        "basket": DEFAULT_BASKET,
        "tags": DEFAULT_TAGS,
        "tagQueryMode": DEFAULT_TAG_QUERY_MODE,
        "limit": DEFAULT_LIMIT,
        "offset": DEFAULT_OFFSET,
        "includeLabels": DEFAULT_INCLUDE_LABELS,
    }


def main() -> None:
    show.process_start("List Outputs")

    alice = setup.create_alice()
    alice_wallet, cleanup = alice.create_wallet()
    try:
        show.step("Alice", "Listing outputs")

        # Configure pagination and filtering parameters
        args = default_list_outputs_args()
        show.info("ListOutputsArgs", args)
        show.separator()

        # Retrieve paginated list of wallet outputs
        # outputs, err := aliceWallet.ListOutputs(ctx, args, DefaultOriginator)
        outputs = alice_wallet.list_outputs(args, DEFAULT_ORIGINATOR)

        show.info("Outputs", outputs)
        show.process_complete("List Outputs")

    finally:
        cleanup()


if __name__ == "__main__":
    main()

