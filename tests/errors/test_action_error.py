"""Unit tests for action error types.

Ported from Go implementation to ensure compatibility.

Reference: go-wallet-toolbox/pkg/errors/action_error_test.go

Note: All tests are currently skipped as the error API is not yet implemented.
"""


class TestTransactionError:
    """Test suite for TransactionError.

    Reference: go-wallet-toolbox/pkg/errors/action_error_test.go
               TestTransactionError_Success / TestTransactionError_ErrorCases
    """

    def test_success(self) -> None:
        """Given: Root cause error and transaction ID
           When: Create TransactionError with wrapped cause
           Then: Returns error with correct message and unwrap behavior

        Reference: go-wallet-toolbox/pkg/errors/action_error_test.go
                   TestTransactionError_Success
        """
        # Given
        # from bsv_wallet_toolbox.errors import TransactionError
        # root_cause = Exception("root cause")
        # txid = "0" * 64

        # When
        # err = TransactionError(txid).wrap(root_cause)

        # Then
        # assert err is not None
        # assert str(err) == f"transaction error (txID: {txid})"
        # assert err.unwrap() is root_cause
        # assert err.is_error(err)

    def test_error_without_cause(self) -> None:
        """Given: Transaction ID without root cause
           When: Create TransactionError without wrapping
           Then: Returns error with no unwrap

        Reference: go-wallet-toolbox/pkg/errors/action_error_test.go
                   TestTransactionError_ErrorCases
                   t.Run("error without cause")
        """
        # Given
        # from bsv_wallet_toolbox.errors import TransactionError
        # txid = "0" * 64

        # When
        # err = TransactionError(txid)

        # Then
        # assert err is not None
        # assert err.unwrap() is None
        # assert not err.is_error(None)


class TestCreateActionError:
    """Test suite for CreateActionError.

    Reference: go-wallet-toolbox/pkg/errors/action_error_test.go
               TestCreateActionError_Success / TestCreateActionError_ErrorCases
    """

    def test_success(self) -> None:
        """Given: Reference ID and root cause
           When: Create CreateActionError with wrapped cause
           Then: Returns error with correct message and unwrap behavior

        Reference: go-wallet-toolbox/pkg/errors/action_error_test.go
                   TestCreateActionError_Success
        """
        # Given
        # from bsv_wallet_toolbox.errors import CreateActionError
        # root_cause = Exception("build failure")
        # reference = "ref1"

        # When
        # err = CreateActionError(reference).wrap(root_cause)

        # Then
        # assert err is not None
        # assert f"create action failed (reference: {reference})" in str(err)
        # assert err.unwrap() is root_cause
        # assert err.is_error(err)
        # assert not err.is_error(None)

    def test_error_without_cause(self) -> None:
        """Given: Reference ID without root cause
           When: Create CreateActionError without wrapping
           Then: Returns error with no unwrap

        Reference: go-wallet-toolbox/pkg/errors/action_error_test.go
                   TestCreateActionError_ErrorCases
                   t.Run("error without cause")
        """
        # Given
        # from bsv_wallet_toolbox.errors import CreateActionError
        # reference = "ref2"

        # When
        # err = CreateActionError(reference)

        # Then
        # assert err is not None
        # assert err.unwrap() is None
        # assert not err.is_error(None)


class TestProcessActionError:
    """Test suite for ProcessActionError.

    Reference: go-wallet-toolbox/pkg/errors/action_error_test.go
               TestProcessActionError_Success / TestProcessActionError_ErrorCases
    """

    def test_with_success_and_failed_txs(self) -> None:
        """Given: Send results with various statuses
           When: Create ProcessActionError
           Then: Error message contains correct counts

        Reference: go-wallet-toolbox/pkg/errors/action_error_test.go
                   TestProcessActionError_Success
                   tests["with success and failed txs"]
        """
        # Given
        # from bsv_wallet_toolbox.errors import ProcessActionError
        # send_results = [
        #     {"status": "unproven"},
        #     {"status": "failed"},
        #     {"status": "sending"}
        # ]

        # When
        # err = ProcessActionError(send_results=send_results, review_results=None)

        # Then
        # assert err is not None
        # message = str(err)
        # assert "process action failed" in message
        # assert "3 total" in message
        # assert "1 succeeded" in message
        # assert "1 sending" in message
        # assert "1 failed" in message

    def test_with_review_results_and_cause(self) -> None:
        """Given: Review results and root cause
           When: Create ProcessActionError with wrapped cause
           Then: Error message contains review count and underlying error

        Reference: go-wallet-toolbox/pkg/errors/action_error_test.go
                   TestProcessActionError_Success
                   tests["with review results and cause"]
        """
        # Given
        # from bsv_wallet_toolbox.errors import ProcessActionError
        # review_results = [{}, {}]
        # root_cause = Exception("root processing issue")

        # When
        # err = ProcessActionError(send_results=None, review_results=review_results).wrap(root_cause)

        # Then
        # assert err is not None
        # message = str(err)
        # assert "process action failed" in message
        # assert "review results: 2 require review" in message
        # assert "underlying error: root processing issue" in message
        # assert err.unwrap() is root_cause
        # assert err.is_error(err)

    def test_nil_cause_and_no_results(self) -> None:
        """Given: No send results, no review results, no cause
           When: Create ProcessActionError
           Then: Returns minimal error message

        Reference: go-wallet-toolbox/pkg/errors/action_error_test.go
                   TestProcessActionError_ErrorCases
                   t.Run("nil cause and no results")
        """
        # Given
        # from bsv_wallet_toolbox.errors import ProcessActionError

        # When
        # err = ProcessActionError(send_results=None, review_results=None)

        # Then
        # assert err is not None
        # assert str(err) == "process action failed"
        # assert not err.is_error(None)
        # assert err.unwrap() is None
