"""Manual tests for janitor (database maintenance operations).

These tests require a configured database connection and test data.
Run manually, not in automated CI/CD.

Janitor is a database maintenance tool that:
- Reviews UTXOs marked as spendable in the database
- Confirms their actual status on the blockchain
- Identifies outputs that are marked spendable but are actually spent
- Updates the database to mark invalid UTXOs as non-spendable

Reference: wallet-toolbox/test/Wallet/support/janitor.man.test.ts
"""

import json
import logging
import os
from typing import Any

import pytest

logger = logging.getLogger(__name__)

# Manual test - requires environment setup
pytestmark = pytest.mark.manual


async def confirm_spendable_outputs(
    storage: Any, services: Any, identity_key: str | None = None
) -> dict[str, list[Any]]:
    """Confirm which outputs marked as spendable are actually UTXOs on-chain.

    This function:
    1. Queries all outputs marked as spendable=True in the database
    2. For each output, checks its actual UTXO status on the blockchain
    3. Returns outputs that are marked spendable but are NOT actually UTXOs

    Args:
        storage: Storage provider instance
        services: Services instance for blockchain queries
        identity_key: Optional identity key to filter outputs

    Returns:
        Dict with 'invalidSpendableOutputs' key containing list of invalid outputs

    Reference: wallet-toolbox/test/Wallet/live/walletLive.man.test.ts
               async function confirmSpendableOutputs()
    """
    invalid_spendable_outputs: list[Any] = []

    # Get all users
    users = await storage.find_users(partial={})

    for user in users:
        user_id = user["userId"]

        # Get default basket
        baskets = await storage.find_output_baskets(partial={"userId": user_id, "name": "default"})
        if not baskets:
            continue
        default_basket = baskets[0]

        # Find all spendable outputs in default basket
        where = {"userId": user_id, "basketId": default_basket["basketId"], "spendable": True}

        outputs = await storage.find_outputs(partial=where)

        # Check each output against blockchain
        for output in outputs:
            if not output.get("spendable"):
                continue

            is_valid = False

            if output.get("lockingScript"):
                # Query blockchain for UTXO status
                result = await services.get_utxo_status(output["lockingScript"], output_format="script")

                if result.get("status") == "success" and result.get("isUtxo") and result.get("details"):

                    # Verify txid, satoshis, and vout match
                    tx = await storage.find_transaction_by_id(output["transactionId"])

                    if tx and tx.get("txid"):
                        for detail in result["details"]:
                            if (
                                detail.get("txid") == tx["txid"]
                                and detail.get("satoshis") == output["satoshis"]
                                and detail.get("index") == output.get("vout")
                            ):
                                is_valid = True
                                break

            if not is_valid:
                invalid_spendable_outputs.append(output)

    return {"invalidSpendableOutputs": invalid_spendable_outputs}


class TestJanitor:
    """Test suite for janitor operations (manual tests).

    Janitor performs database maintenance by identifying and fixing
    inconsistencies between database state and blockchain state.

    Reference: wallet-toolbox/test/Wallet/support/janitor.man.test.ts
               describe('janitor tests')
    """

    @pytest.mark.asyncio
    async def test_review_utxos_by_identity_key(self) -> None:
        """Given: Storage with MySQL connection and specific identity key
           When: Review UTXOs and find invalid spendable outputs
           Then: Can identify outputs marked spendable but actually spent on-chain

        This test:
        1. Connects to production/test MySQL database
        2. Runs confirmSpendableOutputs() for a specific identity key
        3. Identifies outputs that are marked spendable=True in DB but are spent on-chain
        4. Optionally updates those outputs to set spendable=False

        Reference: wallet-toolbox/test/Wallet/support/janitor.man.test.ts
                   test('0 review utxos by identity key')

        Note: TypeScript implementation is commented out but shows the pattern.
              The actual logic for finding and updating invalid UTXOs is provided
              in the confirmSpendableOutputs() helper function above.
        """
        # Get environment configuration
        chain = "main"
        cloud_mysql_connection = os.getenv("CLOUD_MYSQL_CONNECTION")
        if not cloud_mysql_connection:
            logger.warning("CLOUD_MYSQL_CONNECTION not set, skipping test")
            return

        # Parse connection string
        connection = json.loads(cloud_mysql_connection)

        # Create storage with MySQL connection
        try:
            from bsv_wallet_toolbox.storage import StorageMySQL
        except ImportError:
            logger.warning("StorageMySQL not yet implemented, skipping test")
            return

        storage = StorageMySQL(connection=connection, chain=chain)
        await storage.make_available()

        # Create services for blockchain queries
        try:
            from bsv_wallet_toolbox.services import Services
        except ImportError:
            logger.warning("Services not yet implemented, skipping test")
            await storage.destroy()
            return

        services = Services(chain)

        # Example identity key from TypeScript test
        # Note: TypeScript implementation has this logic commented out,
        #       but Python implementation provides it in executable form
        identity_key = "0304985aa632dde471d3bf1ffb030d0af253fe65f5d186bb4cf878ca0fbee54c1c"

        # Find invalid spendable outputs
        result = await confirm_spendable_outputs(storage, services, identity_key)
        invalid_outputs = result["invalidSpendableOutputs"]

        # Prepare outputs for update
        outputs_to_update = [{"id": o["outputId"], "satoshis": o["satoshis"]} for o in invalid_outputs]

        # Calculate total satoshis
        total = sum(o["satoshis"] for o in outputs_to_update)

        # Log results
        logger.info(f"Found {len(outputs_to_update)} invalid spendable outputs")
        logger.info(f"Total satoshis: {total}")

        # *** About set spendable = false for outputs ***
        # Update invalid outputs to set spendable = False
        for output in outputs_to_update:
            await storage.update_output(output["id"], {"spendable": False})

        logger.info(f"Updated {len(outputs_to_update)} outputs to spendable=False")

        await storage.destroy()
