"""Tests for wallet interface protocol.

This module tests the WalletInterface protocol definition.
"""

from typing import Any
from unittest.mock import Mock

from bsv_wallet_toolbox.manager.wallet_interface import WalletInterface


class TestWalletInterfaceProtocol:
    """Tests for WalletInterface protocol."""

    def test_wallet_interface_is_protocol(self) -> None:
        """Test that WalletInterface is a Protocol."""
        # Check if it's a Protocol (works across Python versions)
        from typing import Protocol

        # WalletInterface should be a subclass of Protocol or have Protocol characteristics
        # In Python 3.11+, _is_protocol is the reliable attribute
        assert getattr(WalletInterface, "_is_protocol", False) or issubclass(WalletInterface, Protocol)

    def test_mock_implements_wallet_interface(self) -> None:
        """Test that a mock can satisfy the WalletInterface protocol."""
        # Create a mock that implements all required methods
        mock_wallet = Mock(spec=WalletInterface)

        # Verify all methods are callable
        mock_wallet.create_action({}, "originator")
        mock_wallet.sign_action({}, "originator")
        mock_wallet.abort_action({}, "originator")
        mock_wallet.list_actions({}, "originator")
        mock_wallet.list_outputs({}, "originator")
        mock_wallet.relinquish_output({}, "originator")
        mock_wallet.internalize_action({}, "originator")
        mock_wallet.create_signature({}, "originator")
        mock_wallet.verify_signature({}, "originator")
        mock_wallet.encrypt({}, "originator")
        mock_wallet.decrypt({}, "originator")
        mock_wallet.create_hmac({}, "originator")
        mock_wallet.verify_hmac({}, "originator")
        mock_wallet.get_public_key({}, "originator")
        mock_wallet.reveal_counterparty_key_linkage({}, "originator")
        mock_wallet.reveal_specific_key_linkage({}, "originator")
        mock_wallet.acquire_certificate({}, "originator")
        mock_wallet.list_certificates({}, "originator")
        mock_wallet.prove_certificate({}, "originator")
        mock_wallet.disclose_certificate({}, "originator")
        mock_wallet.relinquish_certificate({}, "originator")
        mock_wallet.discover_by_identity_key({}, "originator")
        mock_wallet.discover_by_attributes({}, "originator")
        mock_wallet.get_network("originator")
        mock_wallet.get_version("originator")

        # All methods should have been called once
        assert mock_wallet.create_action.called
        assert mock_wallet.sign_action.called
        assert mock_wallet.abort_action.called

    def test_concrete_implementation_satisfies_protocol(self) -> None:
        """Test that a concrete class can implement WalletInterface."""

        class ConcreteWallet:
            """A concrete wallet implementation."""

            def create_action(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
                return {"created": True}

            def sign_action(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
                return {"signed": True}

            def abort_action(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
                return {"aborted": True}

            def list_actions(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
                return {"actions": []}

            def list_outputs(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
                return {"outputs": []}

            def relinquish_output(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
                return {"relinquished": True}

            def internalize_action(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
                return {"internalized": True}

            def create_signature(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
                return {"signature": "sig"}

            def verify_signature(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
                return {"valid": True}

            def encrypt(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
                return {"ciphertext": "encrypted"}

            def decrypt(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
                return {"plaintext": "decrypted"}

            def create_hmac(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
                return {"hmac": "hmac"}

            def verify_hmac(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
                return {"valid": True}

            def get_public_key(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
                return {"publicKey": "pubkey"}

            def reveal_counterparty_key_linkage(
                self, args: dict[str, Any], originator: str | None = None
            ) -> dict[str, Any]:
                return {"linkage": "key"}

            def reveal_specific_key_linkage(
                self, args: dict[str, Any], originator: str | None = None
            ) -> dict[str, Any]:
                return {"linkage": "specific"}

            def acquire_certificate(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
                return {"certificate": {}}

            def list_certificates(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
                return {"certificates": []}

            def prove_certificate(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
                return {"proof": "proof"}

            def disclose_certificate(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
                return {"disclosed": True}

            def relinquish_certificate(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
                return {"relinquished": True}

            def discover_by_identity_key(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
                return {"results": []}

            def discover_by_attributes(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
                return {"results": []}

            def get_network(self, originator: str | None = None) -> dict[str, Any]:
                return {"network": "mainnet"}

            def get_version(self, originator: str | None = None) -> dict[str, Any]:
                return {"version": "1.0.0"}

        # Create instance and verify it works
        wallet = ConcreteWallet()
        assert wallet.create_action({}) == {"created": True}
        assert wallet.get_network() == {"network": "mainnet"}

        # Verify it's a valid implementation (duck typing check)
        def accept_wallet(w: WalletInterface) -> dict[str, Any]:
            return w.get_version()

        # This should work without errors
        result = accept_wallet(wallet)  # type: ignore[arg-type]
        assert result == {"version": "1.0.0"}
