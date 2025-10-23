"""Manual tests for WERR (Wallet Error Review Required) error handling.

These tests verify that special wallet operations (specOps) that require user review
properly raise ReviewActionsError with appropriate action results.

Implementation Intent:
- Verify ReviewActionsError exception is raised for review-required operations
- Ensure error contains review_action_results for user decision making
- Test error handling for specOpThrowReviewActions label

Note: This is a manual test because it requires:
      1. Live wallet connection with proper authentication
      2. Special operation labels (specOps) that trigger review workflow
      3. Real action creation that interacts with wallet services

Reference: wallet-toolbox/test/WalletClient/WERR.man.test.ts
"""

import logging

import pytest

try:
    from bsv_wallet_toolbox.errors import ReviewActionsError
    from bsv_wallet_toolbox.wallet import Wallet

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False

logger = logging.getLogger(__name__)


class TestWERR:
    """Test suite for WERR (Wallet Error Review Required) manual tests.

    These tests verify that wallet operations requiring user review
    properly raise ReviewActionsError with review action results.
    """

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for Wallet, ReviewActionsError implementation")
    @pytest.mark.asyncio
    async def test_werr_review_actions(self) -> None:
        """Given: Wallet instance
           When: Call create_action with specOpThrowReviewActions label
           Then: Raises ReviewActionsError with all required attributes

        Implementation Notes:
        - TypeScript uses WERR_REVIEW_ACTIONS error code with 5 attributes
        - Python uses ReviewActionsError exception class (Pythonic approach)
        - Exception must have: review_action_results, send_with_results, txid, tx, no_send_change
        - This allows wallet UI to prompt user for review/approval

        TypeScript WERR_REVIEW_ACTIONS constructor signature:
        ```typescript
        constructor(
          public reviewActionResults: ReviewActionResult[],
          public sendWithResults: SendWithResult[],
          public txid?: TXIDHexString,
          public tx?: AtomicBEEF,
          public noSendChange?: OutpointString[]
        )
        ```

        Reference: wallet-toolbox/test/WalletClient/WERR.man.test.ts
                   test('0 WERR_REVIEW_ACTIONS')

                   wallet-toolbox/src/sdk/WERR_errors.ts
                   WERR_REVIEW_ACTIONS class (lines 154-169)
        """
        # Given: Wallet instance
        wallet = Wallet(chain="main")  # Assuming default chain for manual tests

        # When/Then: Expect ReviewActionsError to be raised
        with pytest.raises(ReviewActionsError) as exc_info:
            await wallet.create_action({"labels": ["specOpThrowReviewActions"], "description": "must throw"})

        # Verify exception has all required attributes (matching TypeScript)
        error = exc_info.value

        # Required: review_action_results (ReviewActionResult[])
        assert hasattr(error, "review_action_results"), "ReviewActionsError must have review_action_results attribute"
        assert error.review_action_results is not None, "review_action_results must not be None"
        assert isinstance(error.review_action_results, list), "review_action_results must be a list"

        # Required: send_with_results (SendWithResult[])
        assert hasattr(error, "send_with_results"), "ReviewActionsError must have send_with_results attribute"
        assert error.send_with_results is not None, "send_with_results must not be None"
        assert isinstance(error.send_with_results, list), "send_with_results must be a list"

        # Optional: txid (TXIDHexString)
        assert hasattr(error, "txid"), "ReviewActionsError must have txid attribute"
        # txid can be None or string

        # Optional: tx (AtomicBEEF)
        assert hasattr(error, "tx"), "ReviewActionsError must have tx attribute"
        # tx can be None or list[int]

        # Optional: no_send_change (OutpointString[])
        assert hasattr(error, "no_send_change"), "ReviewActionsError must have no_send_change attribute"
        # no_send_change can be None or list[str]

        logger.info(
            f"ReviewActionsError raised correctly with {len(error.review_action_results)} "
            f"review action(s) and {len(error.send_with_results)} send result(s)"
        )
