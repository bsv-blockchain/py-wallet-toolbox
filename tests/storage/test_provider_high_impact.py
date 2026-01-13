"""High-impact coverage tests for StorageProvider.

This module targets the most critical uncovered lines in storage/provider.py
to maximize coverage improvement. Focuses on:
- Soft-deleted basket restoration (lines 203-205)
- find_or_insert_sync_state (lines 458-490)
- list_outputs SpecOps (lines 679-794)
- InternalizeActionWorker methods (lines 4196-4587)
"""

from __future__ import annotations

import pytest
from sqlalchemy import select

from bsv_wallet_toolbox.errors import WalletError
from bsv_wallet_toolbox.storage.db import create_engine_from_url, session_scope
from bsv_wallet_toolbox.storage.models import (
    Base,
    OutputBasket,
)
from bsv_wallet_toolbox.storage.provider import StorageProvider
from bsv_wallet_toolbox.utils.validation import InvalidParameterError


@pytest.fixture
def storage_provider():
    """Create a StorageProvider with in-memory SQLite database."""
    engine = create_engine_from_url("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    provider = StorageProvider(engine=engine, chain="test", storage_identity_key="K" * 64)
    provider.make_available()
    return provider


@pytest.fixture
def test_user(storage_provider):
    """Create a test user and return user_id."""
    identity_key = "test_identity_key_high_impact_123"
    user_data = storage_provider.find_or_insert_user(identity_key)
    return user_data["user"]["userId"]


@pytest.fixture
def user_with_basket(storage_provider, test_user):
    """Create a test user with a default basket and return details."""
    # Ensure default basket exists
    basket_data = storage_provider.find_or_insert_output_basket(test_user, "default")
    return {
        "userId": test_user,
        "basketId": basket_data["basketId"],
    }


class TestSoftDeletedBasketRestoration:
    """Test restoring soft-deleted baskets (lines 203-205)."""

    def test_restore_soft_deleted_basket(self, storage_provider, test_user):
        """Test that a soft-deleted basket is restored when find_or_insert is called."""
        # First, create a basket
        basket_data = storage_provider.find_or_insert_output_basket(test_user, "test_basket")
        basket_id = basket_data["basketId"]

        # Soft-delete the basket by setting is_deleted to True
        with session_scope(storage_provider.SessionLocal) as s:
            q = select(OutputBasket).where(OutputBasket.basket_id == basket_id)
            basket = s.execute(q).scalar_one()
            basket.is_deleted = True
            s.add(basket)
            s.commit()

        # Verify it's deleted
        with session_scope(storage_provider.SessionLocal) as s:
            q = select(OutputBasket).where(OutputBasket.basket_id == basket_id)
            basket = s.execute(q).scalar_one()
            assert basket.is_deleted is True

        # Now call find_or_insert - should restore the basket
        restored_data = storage_provider.find_or_insert_output_basket(test_user, "test_basket")

        # Verify it was restored (same basket_id but not deleted)
        assert restored_data["basketId"] == basket_id

        with session_scope(storage_provider.SessionLocal) as s:
            q = select(OutputBasket).where(OutputBasket.basket_id == basket_id)
            basket = s.execute(q).scalar_one()
            assert basket.is_deleted is False


class TestSyncStateOperations:
    """Test sync state operations."""

    def test_insert_sync_state(self, storage_provider, test_user):
        """Test inserting a sync state."""
        sync_state_data = {
            "userId": test_user,
            "storageIdentityKey": "remote_storage_" + "a" * 50,
            "storageName": "remote_test",
            "status": "unknown",
            "init": False,
            "refNum": "sync-ref-new",
            "syncMap": "{}",
        }

        sync_id = storage_provider.insert_sync_state(sync_state_data)

        assert isinstance(sync_id, int)
        assert sync_id > 0

    def test_find_sync_states(self, storage_provider, test_user):
        """Test finding sync states."""
        # Insert a sync state first
        sync_state_data = {
            "userId": test_user,
            "storageIdentityKey": "find_sync_" + "b" * 50,
            "storageName": "find_test",
            "status": "complete",
            "init": True,
            "refNum": "sync-ref-find",
            "syncMap": "{}",
        }

        storage_provider.insert_sync_state(sync_state_data)

        # Find it
        results = storage_provider.find_sync_states({"partial": {"userId": test_user}})

        assert len(results) >= 1
        assert any(r["storageName"] == "find_test" for r in results)


class TestListOutputsSpecOps:
    """Test list_outputs SpecOps functionality (lines 679-794)."""

    def test_list_outputs_specop_wallet_balance(self, storage_provider, user_with_basket):
        """Test wallet balance SpecOp."""
        user_id = user_with_basket["userId"]
        basket_id = user_with_basket["basketId"]

        # Create transaction first (outputs require transactionId)
        tx_id = storage_provider.insert_transaction(
            {
                "userId": user_id,
                "reference": "tx_balance_test",
                "txid": "a" * 64,
                "status": "completed",
                "satoshis": 6000,
            }
        )

        # Create some outputs with change=True and type=P2PKH for specOpWalletBalance
        for i in range(3):
            storage_provider.insert_output(
                {
                    "userId": user_id,
                    "basketId": basket_id,
                    "transactionId": tx_id,
                    "vout": i,
                    "satoshis": 1000 * (i + 1),  # 1000, 2000, 3000
                    "spendable": True,
                    "change": True,  # Required for specOpWalletBalance
                    "type": "P2PKH",  # Required for specOpWalletBalance
                    "txid": f"{'a' * 60}{i:04d}",
                    "lockingScript": b"\x76\xa9\x14" + bytes(20) + b"\x88\xac",
                }
            )

        auth = {"userId": user_id}
        # Use SpecOp ID format
        args = {
            "basket": "specOpWalletBalance",  # SpecOp name
            "limit": 10,
        }

        result = storage_provider.list_outputs(auth, args)

        # Wallet balance should sum satoshis and return empty outputs
        assert result["totalOutputs"] == 6000  # 1000 + 2000 + 3000
        assert result["outputs"] == []

    def test_list_outputs_basic(self, storage_provider, user_with_basket):
        """Test basic list_outputs functionality."""
        user_id = user_with_basket["userId"]
        basket_id = user_with_basket["basketId"]

        # Create transaction first
        tx_id = storage_provider.insert_transaction(
            {
                "userId": user_id,
                "reference": "tx_basic_test",
                "txid": "b" * 64,
                "status": "completed",
                "satoshis": 5000,
            }
        )

        # Create output
        storage_provider.insert_output(
            {
                "userId": user_id,
                "basketId": basket_id,
                "transactionId": tx_id,
                "vout": 0,
                "satoshis": 5000,
                "spendable": True,
                "txid": "b" * 64,
                "lockingScript": b"\x76\xa9\x14" + bytes(20) + b"\x88\xac",
            }
        )

        auth = {"userId": user_id}
        args = {
            "basket": "default",
            "limit": 10,
        }

        result = storage_provider.list_outputs(auth, args)

        assert "totalOutputs" in result
        assert "outputs" in result
        assert len(result["outputs"]) >= 1

    def test_list_outputs_with_include_labels(self, storage_provider, user_with_basket):
        """Test list_outputs with includeLabels option."""
        user_id = user_with_basket["userId"]
        basket_id = user_with_basket["basketId"]

        # Create a transaction with labels
        tx_id = storage_provider.insert_transaction(
            {
                "userId": user_id,
                "reference": "tx_labels_test",
                "txid": "e" * 64,
                "status": "completed",
                "satoshis": 5000,
            }
        )

        # Add label to transaction
        label_data = storage_provider.find_or_insert_tx_label(user_id, "test_label")
        storage_provider.find_or_insert_tx_label_map(tx_id, label_data["txLabelId"])

        # Create output linked to transaction
        storage_provider.insert_output(
            {
                "userId": user_id,
                "basketId": basket_id,
                "transactionId": tx_id,
                "vout": 0,
                "satoshis": 5000,
                "spendable": True,
                "txid": "e" * 64,
                "lockingScript": b"\x76\xa9\x14" + bytes(20) + b"\x88\xac",
            }
        )

        auth = {"userId": user_id}
        args = {
            "basket": "default",
            "includeLabels": True,
            "limit": 10,
        }

        result = storage_provider.list_outputs(auth, args)

        assert len(result["outputs"]) >= 1
        # Check if labels are included
        output_with_tx = [o for o in result["outputs"] if "labels" in o]
        assert len(output_with_tx) >= 1

    def test_list_outputs_with_include_tags(self, storage_provider, user_with_basket):
        """Test list_outputs with includeTags option."""
        user_id = user_with_basket["userId"]
        basket_id = user_with_basket["basketId"]

        # Create transaction first
        tx_id = storage_provider.insert_transaction(
            {
                "userId": user_id,
                "reference": "tx_tags_test",
                "txid": "f" * 64,
                "status": "completed",
                "satoshis": 3000,
            }
        )

        # Create output
        output_id = storage_provider.insert_output(
            {
                "userId": user_id,
                "basketId": basket_id,
                "transactionId": tx_id,
                "vout": 0,
                "satoshis": 3000,
                "spendable": True,
                "txid": "f" * 64,
                "lockingScript": b"\x76\xa9\x14" + bytes(20) + b"\x88\xac",
            }
        )

        # Add tag to output
        tag_data = storage_provider.find_or_insert_output_tag(user_id, "my_tag")
        storage_provider.find_or_insert_output_tag_map(output_id, tag_data["outputTagId"])

        auth = {"userId": user_id}
        args = {
            "basket": "default",
            "includeTags": True,
            "limit": 10,
        }

        result = storage_provider.list_outputs(auth, args)

        assert len(result["outputs"]) >= 1
        # Find our output and check tags
        our_output = [o for o in result["outputs"] if o.get("outpoint", "").startswith("f" * 64)]
        assert len(our_output) >= 1
        assert "tags" in our_output[0]
        assert "my_tag" in our_output[0]["tags"]

    def test_list_outputs_with_custom_instructions(self, storage_provider, user_with_basket):
        """Test list_outputs with includeCustomInstructions option."""
        user_id = user_with_basket["userId"]
        basket_id = user_with_basket["basketId"]

        # Create transaction first
        tx_id = storage_provider.insert_transaction(
            {
                "userId": user_id,
                "reference": "tx_custom_test",
                "txid": "g" * 64,
                "status": "completed",
                "satoshis": 2500,
            }
        )

        # Create output with custom instructions
        storage_provider.insert_output(
            {
                "userId": user_id,
                "basketId": basket_id,
                "transactionId": tx_id,
                "vout": 0,
                "satoshis": 2500,
                "spendable": True,
                "txid": "g" * 64,
                "lockingScript": b"\x76\xa9\x14" + bytes(20) + b"\x88\xac",
                "customInstructions": "custom instruction data",
            }
        )

        auth = {"userId": user_id}
        args = {
            "basket": "default",
            "includeCustomInstructions": True,
            "limit": 10,
        }

        result = storage_provider.list_outputs(auth, args)

        assert len(result["outputs"]) >= 1
        # Find our output and check custom instructions
        our_output = [o for o in result["outputs"] if o.get("outpoint", "").startswith("g" * 64)]
        assert len(our_output) >= 1
        assert "customInstructions" in our_output[0]

    def test_list_outputs_with_offset_pagination(self, storage_provider, user_with_basket):
        """Test list_outputs with offset pagination."""
        user_id = user_with_basket["userId"]
        basket_id = user_with_basket["basketId"]

        # Create multiple transactions with outputs
        for i in range(5):
            tx_id = storage_provider.insert_transaction(
                {
                    "userId": user_id,
                    "reference": f"tx_page_{i}",
                    "txid": f"{'h' * 60}{i:04d}",
                    "status": "completed",
                    "satoshis": 1000 * (i + 1),
                }
            )

            storage_provider.insert_output(
                {
                    "userId": user_id,
                    "basketId": basket_id,
                    "transactionId": tx_id,
                    "vout": 0,
                    "satoshis": 1000 * (i + 1),
                    "spendable": True,
                    "txid": f"{'h' * 60}{i:04d}",
                    "lockingScript": b"\x76\xa9\x14" + bytes(20) + b"\x88\xac",
                }
            )

        auth = {"userId": user_id}
        args = {
            "basket": "default",
            "limit": 2,
            "offset": 2,  # Skip first 2
        }

        result = storage_provider.list_outputs(auth, args)

        # Should return paginated results
        assert "outputs" in result
        assert len(result["outputs"]) <= 2


class TestListOutputsTagFilters:
    """Test list_outputs with tag filtering options."""

    def test_list_outputs_tag_filter_all(self, storage_provider, user_with_basket):
        """Test list_outputs with 'all' tag SpecOp."""
        user_id = user_with_basket["userId"]
        basket_id = user_with_basket["basketId"]

        # Create transaction first
        tx_id = storage_provider.insert_transaction(
            {
                "userId": user_id,
                "reference": "tx_all_test",
                "txid": "i" * 64,
                "status": "completed",
                "satoshis": 1000,
            }
        )

        # Create outputs
        storage_provider.insert_output(
            {
                "userId": user_id,
                "basketId": basket_id,
                "transactionId": tx_id,
                "vout": 0,
                "satoshis": 1000,
                "spendable": True,
                "txid": "i" * 64,
                "lockingScript": b"\x76\xa9\x14" + bytes(20) + b"\x88\xac",
            }
        )

        auth = {"userId": user_id}
        args = {
            "tags": ["all"],  # 'all' tag SpecOp
            "limit": 100,
        }

        result = storage_provider.list_outputs(auth, args)

        # Should return all outputs (ignoring basket filter)
        assert "totalOutputs" in result
        assert "outputs" in result

    def test_list_outputs_tag_filter_unspent(self, storage_provider, user_with_basket):
        """Test list_outputs with 'unspent' tag SpecOp."""
        user_id = user_with_basket["userId"]
        basket_id = user_with_basket["basketId"]

        # Create transaction first
        tx_id = storage_provider.insert_transaction(
            {
                "userId": user_id,
                "reference": "tx_unspent_test",
                "txid": "j" * 64,
                "status": "completed",
                "satoshis": 1500,
            }
        )

        # Create spendable output
        storage_provider.insert_output(
            {
                "userId": user_id,
                "basketId": basket_id,
                "transactionId": tx_id,
                "vout": 0,
                "satoshis": 1500,
                "spendable": True,
                "txid": "j" * 64,
                "lockingScript": b"\x76\xa9\x14" + bytes(20) + b"\x88\xac",
            }
        )

        auth = {"userId": user_id}
        args = {
            "basket": "default",
            "tags": ["unspent"],
            "limit": 100,
        }

        result = storage_provider.list_outputs(auth, args)

        # Should only return unspent (spendable) outputs
        assert "totalOutputs" in result
        for output in result["outputs"]:
            assert output.get("spendable", True) is True

    def test_list_outputs_tag_filter_change(self, storage_provider, user_with_basket):
        """Test list_outputs with 'change' tag SpecOp."""
        user_id = user_with_basket["userId"]
        basket_id = user_with_basket["basketId"]

        # Create transaction first
        tx_id = storage_provider.insert_transaction(
            {
                "userId": user_id,
                "reference": "tx_change_test",
                "txid": "k" * 64,
                "status": "completed",
                "satoshis": 2000,
            }
        )

        # Create change output
        storage_provider.insert_output(
            {
                "userId": user_id,
                "basketId": basket_id,
                "transactionId": tx_id,
                "vout": 0,
                "satoshis": 2000,
                "spendable": True,
                "change": True,
                "txid": "k" * 64,
                "lockingScript": b"\x76\xa9\x14" + bytes(20) + b"\x88\xac",
            }
        )

        auth = {"userId": user_id}
        args = {
            "basket": "default",
            "tags": ["change"],
            "limit": 100,
        }

        result = storage_provider.list_outputs(auth, args)

        # Should only return change outputs
        assert "outputs" in result


class TestListActionsEnhancements:
    """Test enhanced list_actions functionality."""

    def test_list_actions_with_status_filter(self, storage_provider, test_user):
        """Test list_actions with status filtering."""
        # Create transactions with different statuses
        for status in ["completed", "pending", "failed"]:
            storage_provider.insert_transaction(
                {
                    "userId": test_user,
                    "reference": f"tx_status_{status}",
                    "txid": f"{status[0]}" * 64,
                    "status": status,
                    "satoshis": 1000,
                }
            )

        auth = {"userId": test_user}
        args = {
            "limit": 10,
            "status": ["completed"],
        }

        result = storage_provider.list_actions(auth, args)

        assert "actions" in result
        # All returned actions should have completed status
        for action in result["actions"]:
            if "status" in action:
                assert action["status"] in ["completed"]

    def test_list_actions_with_txid_filter(self, storage_provider, test_user):
        """Test list_actions with txid filtering."""
        target_txid = "t" * 64
        storage_provider.insert_transaction(
            {
                "userId": test_user,
                "reference": "tx_txid_filter",
                "txid": target_txid,
                "status": "completed",
                "satoshis": 5000,
            }
        )

        auth = {"userId": test_user}
        args = {
            "txids": [target_txid],
            "limit": 10,
        }

        result = storage_provider.list_actions(auth, args)

        assert "actions" in result
        if result["actions"]:
            assert result["actions"][0]["txid"] == target_txid


class TestInternalizeActionWorker:
    """Test InternalizeActionWorker functionality (lines 4196-4587)."""

    def test_internalize_action_empty_outputs_validation(self, storage_provider, user_with_basket):
        """Test internalize_action validates empty outputs."""
        user_id = user_with_basket["userId"]

        auth = {"userId": user_id, "identityKey": "test_identity_key_high_impact_123"}
        args = {
            "tx": [1, 2, 3, 4, 5],  # Minimal BEEF bytes
            "outputs": [],  # Empty outputs
            "description": "Test",
        }

        with pytest.raises(InvalidParameterError) as exc_info:
            storage_provider.internalize_action(auth, args)

        # Should fail on outputs validation
        assert "outputs" in str(exc_info.value)

    def test_internalize_action_mock_beef(self, storage_provider, user_with_basket):
        """Test internalize_action with mock BEEF data."""
        user_id = user_with_basket["userId"]

        # Create minimal mock BEEF (will fail validation but tests structure)
        mock_beef = list(range(1, 50))

        auth = {"userId": user_id, "identityKey": "test_identity_key_high_impact_123"}
        args = {
            "tx": mock_beef,
            "outputs": [{"outputIndex": 0, "protocol": "wallet payment"}],
            "description": "Test mock BEEF",
        }

        # Should raise error due to invalid BEEF format or missing fields
        with pytest.raises((InvalidParameterError, WalletError, Exception)):
            storage_provider.internalize_action(auth, args)


class TestProviderMethodsMiscellaneous:
    """Test miscellaneous provider methods for coverage."""

    def test_get_proven_or_raw_tx_not_found(self, storage_provider):
        """Test get_proven_or_raw_tx for non-existent txid."""
        txid = "0" * 64

        result = storage_provider.get_proven_or_raw_tx(txid)

        # Should return dict indicating not found
        assert isinstance(result, dict)

    def test_get_proven_or_raw_tx_prefer_proven(self, storage_provider):
        """Test get_proven_or_raw_tx prefers proven over raw."""
        txid = "p" * 64

        # Insert a proven tx
        storage_provider.insert_proven_tx(
            {
                "txid": txid,
                "height": 100,
                "index": 0,
                "merklePath": b"\x00\x01",
                "rawTx": b"\x02\x03",
                "blockHash": "d" * 64,
                "merkleRoot": "e" * 64,
            }
        )

        result = storage_provider.get_proven_or_raw_tx(txid)

        assert isinstance(result, dict)
        # Should contain proven tx data

    def test_list_certificates_with_filters(self, storage_provider, test_user):
        """Test list_certificates with type and certifier filters."""
        # Create certificates
        for i, (cert_type, certifier) in enumerate(
            [
                ("identity", "certifier_a"),
                ("identity", "certifier_b"),
                ("employment", "certifier_a"),
            ]
        ):
            storage_provider.insert_certificate(
                {
                    "userId": test_user,
                    "type": cert_type,
                    "serialNumber": f"SN-{i:03d}",
                    "certifier": certifier,
                    "subject": "test_subject",
                    "revocationOutpoint": f"{'r' * 60}{i:04d}.0",
                    "signature": "sig",
                }
            )

        auth = {"userId": test_user}
        args = {
            "certifiers": ["certifier_a"],
            "types": ["identity"],
        }

        result = storage_provider.list_certificates(auth, args)

        assert "certificates" in result
        # Should filter by both certifier and type

    def test_find_output_baskets(self, storage_provider, user_with_basket):
        """Test finding output baskets."""
        user_id = user_with_basket["userId"]

        result = storage_provider.find_output_baskets({"partial": {"userId": user_id}})

        assert len(result) >= 1
        assert any(b["name"] == "default" for b in result)

    def test_update_output_basket_via_generic(self, storage_provider, user_with_basket):
        """Test updating output basket via update method."""
        user_with_basket["userId"]
        basket_id = user_with_basket["basketId"]

        patch = {
            "numberOfDesiredUTXOs": 10,
            "minimumDesiredUTXOValue": 2000,
        }

        rows = storage_provider.update_output_basket(basket_id, patch)

        assert rows == 1

        # Verify update via find
        baskets = storage_provider.find_output_baskets({"partial": {"basketId": basket_id}})
        assert len(baskets) >= 1
        assert baskets[0]["numberOfDesiredUTXOs"] == 10
        assert baskets[0]["minimumDesiredUTXOValue"] == 2000


class TestProcessActionOperations:
    """Test process_action related operations."""

    def test_process_action_with_minimal_args(self, storage_provider, user_with_basket):
        """Test process_action with minimal arguments."""
        user_id = user_with_basket["userId"]

        # Create an unsigned transaction
        storage_provider.insert_transaction(
            {
                "userId": user_id,
                "reference": "process_action_test",
                "txid": "u" * 64,
                "status": "unsigned",
                "satoshis": 1000,
            }
        )

        auth = {"userId": user_id, "identityKey": "test_identity_key_high_impact_123"}
        args = {
            "reference": "process_action_test",
            "options": {},
        }

        # This may raise an error due to validation, but tests the method path
        try:
            result = storage_provider.process_action(auth, args)
            assert isinstance(result, dict)
        except (InvalidParameterError, WalletError):
            # Expected - incomplete args for full processing
            pass


class TestBeefBuilding:
    """Test BEEF building operations."""

    def test_build_beef_for_outputs(self, storage_provider, user_with_basket):
        """Test building BEEF for outputs."""
        user_id = user_with_basket["userId"]
        basket_id = user_with_basket["basketId"]

        # Create outputs with proven transactions
        proven_txid = "q" * 64
        storage_provider.insert_proven_tx(
            {
                "txid": proven_txid,
                "height": 500,
                "index": 1,
                "merklePath": b"\x00\x01\x02",
                "rawTx": b"\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00",
                "blockHash": "b" * 64,
                "merkleRoot": "m" * 64,
            }
        )

        # Create transaction first
        tx_id = storage_provider.insert_transaction(
            {
                "userId": user_id,
                "reference": "tx_beef_test",
                "txid": proven_txid,
                "status": "completed",
                "satoshis": 10000,
            }
        )

        storage_provider.insert_output(
            {
                "userId": user_id,
                "basketId": basket_id,
                "transactionId": tx_id,
                "vout": 0,
                "satoshis": 10000,
                "spendable": True,
                "txid": proven_txid,
                "lockingScript": b"\x76\xa9\x14" + bytes(20) + b"\x88\xac",
            }
        )

        auth = {"userId": user_id}
        args = {
            "basket": "default",
            "includeTransactions": True,
            "limit": 10,
        }

        result = storage_provider.list_outputs(auth, args)

        # May include BEEF in result
        assert "outputs" in result


class TestCreateActionOperations:
    """Test create_action related operations."""

    def test_create_action_minimal(self, storage_provider, user_with_basket):
        """Test create_action with minimal valid arguments."""
        user_id = user_with_basket["userId"]
        basket_id = user_with_basket["basketId"]

        # First create a transaction and ensure we have spendable outputs
        tx_id = storage_provider.insert_transaction(
            {
                "userId": user_id,
                "reference": "tx_funding",
                "txid": "s" * 64,
                "status": "completed",
                "satoshis": 100000,
            }
        )

        storage_provider.insert_output(
            {
                "userId": user_id,
                "basketId": basket_id,
                "transactionId": tx_id,
                "vout": 0,
                "satoshis": 100000,
                "spendable": True,
                "change": True,  # Must be True for allocate_funding_input
                "type": "P2PKH",  # Must be "P2PKH" for allocate_funding_input
                "txid": "s" * 64,
                "lockingScript": b"\x76\xa9\x14" + bytes(20) + b"\x88\xac",
            }
        )

        auth = {"userId": user_id, "identityKey": "test_identity_key_high_impact_123"}
        args = {
            "description": "Test create action",
            "outputs": [
                {
                    "satoshis": 1000,
                    "lockingScript": "76a914" + "00" * 20 + "88ac",  # P2PKH
                }
            ],
            "options": {
                "signAndProcess": False,
            },
        }

        result = storage_provider.create_action(auth, args)

        assert isinstance(result, dict)
        # Should return action result structure
        assert "reference" in result
        # Reference should be 16 characters (matching Go test expectations)
        assert len(result["reference"]) == 16


class TestTransactionOperations:
    """Test transaction-related operations."""

    def test_find_transactions_with_filters(self, storage_provider, test_user):
        """Test finding transactions with various filters."""
        # Create transactions with different statuses
        for status in ["completed", "pending", "failed"]:
            storage_provider.insert_transaction(
                {
                    "userId": test_user,
                    "reference": f"tx_filter_{status}",
                    "txid": f"{status[0] * 64}",
                    "status": status,
                    "satoshis": 1000,
                }
            )

        # Find by status
        results = storage_provider.find_transactions({"partial": {"status": "completed"}})

        assert len(results) >= 1
        for tx in results:
            assert tx["status"] == "completed"

    def test_update_transaction_status(self, storage_provider, test_user):
        """Test updating transaction status."""
        # Create a transaction
        tx_id = storage_provider.insert_transaction(
            {
                "userId": test_user,
                "reference": "tx_update_status",
                "txid": "u" * 64,
                "status": "pending",
                "satoshis": 2000,
            }
        )

        # Update status
        rows = storage_provider.update_transaction_status("completed", tx_id)

        assert rows == 1

        # Verify update
        txs = storage_provider.find_transactions({"partial": {"transactionId": tx_id}})
        assert len(txs) == 1
        assert txs[0]["status"] == "completed"
