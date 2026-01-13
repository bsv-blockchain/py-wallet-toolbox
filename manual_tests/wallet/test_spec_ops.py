"""Manual tests for spec ops (special operations).

These tests require a configured wallet with test data and network access.
Run manually, not in automated CI/CD.

Reference: wallet-toolbox/test/Wallet/specOps/specOps.man.test.ts
"""

import json
import logging
import os
from pathlib import Path

import pytest

logger = logging.getLogger(__name__)

# Manual test - requires environment setup
pytestmark = pytest.mark.manual


async def create_setup(chain: str):
    """Create test setup with wallet and storage.

    This function:
    1. Gets environment configuration (testIdentityKey, testFilePath, devKeys)
    2. Creates test wallet with SQLite local storage
    3. Adds client storage (StorageClient or MySQL)
    4. Sets active storage (local by default)
    5. Ensures wallet has sufficient balance and UTXOs

    Args:
        chain: 'main' or 'test'

    Returns:
        Setup object with:
            - wallet: Wallet instance
            - storage: WalletStorageManager
            - activeStorage: Active storage provider
            - userId: Active user ID
            - localStorageIdentityKey: Local storage identity key
            - clientStorageIdentityKey: Client storage identity key

    Reference: wallet-toolbox/test/Wallet/specOps/specOps.man.test.ts
               async function createSetup()
               wallet-toolbox/test/utils/TestUtilsWalletStorage.ts
               static async createTestWallet()
    """
    # Get environment configuration
    test_identity_key = os.getenv(f"{chain.upper()}_TEST_IDENTITY_KEY")
    test_file_path = os.getenv(f"{chain.upper()}_TEST_FILE_PATH")

    if not test_identity_key:
        raise ValueError(f"env.testIdentityKey must be valid for chain '{chain}'")
    if not test_file_path:
        raise ValueError(f"env.testFilePath must be valid for chain '{chain}'")

    # Get root key hex from dev keys
    dev_keys_json = os.getenv("DEV_KEYS")
    if not dev_keys_json:
        raise ValueError("DEV_KEYS environment variable must be set")

    dev_keys = json.loads(dev_keys_json)
    root_key_hex = dev_keys.get(test_identity_key)
    if not root_key_hex:
        raise ValueError(f"devKeys[{test_identity_key}] must be valid")

    # Import required modules
    try:
        from bsv_wallet_toolbox.storage import StorageClient, StorageMySQL, WalletStorageManager

        from bsv_wallet_toolbox.errors import InsufficientFundsError
        from bsv_wallet_toolbox.wallet import Wallet
    except ImportError as e:
        logger.warning(f"Required modules not yet implemented: {e}")
        logger.warning("Skipping manual test setup")
        raise NotImplementedError(
            "Manual test setup requires Wallet, WalletStorageManager, "
            "StorageSQLite, StorageMySQL, StorageClient implementation."
        ) from e

    # Create SQLite test wallet
    database_name = Path(test_file_path).stem
    setup = await create_sqlite_test_wallet(
        file_path=test_file_path, root_key_hex=root_key_hex, database_name=database_name, chain=chain
    )
    setup["localStorageIdentityKey"] = setup["storage"].get_active_store()

    # Add client storage
    use_mysql_connection_for_client = False  # Default from args
    if use_mysql_connection_for_client:
        cloud_mysql_connection = os.getenv("CLOUD_MYSQL_CONNECTION")
        if not cloud_mysql_connection:
            raise ValueError("env.cloudMySQLConnection must be valid")
        connection = json.loads(cloud_mysql_connection)
        client = StorageMySQL(connection=connection, chain=chain)
    else:
        endpoint_url = (
            "https://storage.babbage.systems" if chain == "main" else "https://staging-storage.babbage.systems"
        )
        client = StorageClient(setup["wallet"], endpoint_url)

    client_result = await client.make_available()
    setup["clientStorageIdentityKey"] = client_result["storageIdentityKey"]
    await setup["wallet"].storage.add_wallet_storage_provider(client)

    # Set active storage (local by default)
    set_active_client = False  # Default from args
    active_key = setup["clientStorageIdentityKey"] if set_active_client else setup["localStorageIdentityKey"]
    log = await setup["storage"].set_active(active_key)
    logger.info(log)

    # Ensure sufficient balance and UTXOs
    needs_backup = False
    if setup["storage"].get_active_store() == setup["localStorageIdentityKey"]:
        baskets = await setup["activeStorage"].find_output_baskets(
            partial={"userId": setup["storage"].get_active_user()["userId"], "name": "default"}
        )
        basket = baskets[0]  # verifyOne
        if basket["minimumDesiredUTXOValue"] != 5 or basket["numberOfDesiredUTXOs"] < 32:
            needs_backup = True
            await setup["activeStorage"].update_output_basket(
                basket["basketId"], {"minimumDesiredUTXOValue": 5, "numberOfDesiredUTXOs": 32}
            )

    balance = await setup["wallet"].balance_and_utxos()
    if balance["total"] < 1000:
        raise InsufficientFundsError(1000, 1000 - balance["total"])

    if len(balance["utxos"]) <= 10:
        await setup["wallet"].create_action({"description": "spread change"})
        needs_backup = True

    if needs_backup:
        log2 = await setup["storage"].update_backups()
        logger.info(log2)

    logger.info(f"ACTIVE STORAGE: {setup['storage'].get_active_store_name()}")

    return setup


async def create_sqlite_test_wallet(file_path: str, root_key_hex: str, database_name: str, chain: str):
    """Create SQLite test wallet.

    Args:
        file_path: Path to SQLite database file
        root_key_hex: Root key in hex format
        database_name: Database name
        chain: 'main' or 'test'

    Returns:
        Setup dict with wallet, storage, and related objects

    Reference: wallet-toolbox/test/utils/TestUtilsWalletStorage.ts
               static async createSQLiteTestWallet()
    """
    try:
        from bsv_wallet_toolbox.storage import StorageSQLite, WalletStorageManager

        from bsv_wallet_toolbox.wallet import Wallet
    except ImportError as e:
        raise NotImplementedError("createSQLiteTestWallet requires Wallet and Storage implementation") from e

    # Create local SQLite storage (Python uses SQLAlchemy, not Knex)
    storage_sqlite = StorageSQLite(file_path=file_path, chain=chain)

    # Migrate and make available
    await storage_sqlite.migrate(database_name, root_key_hex)
    storage_identity_result = await storage_sqlite.make_available()

    # Create wallet with storage
    wallet = Wallet(chain=chain, root_key_hex=root_key_hex)
    await wallet.storage.add_wallet_storage_provider(storage_sqlite)

    # Get active storage and user
    active_storage = wallet.storage.get_active_storage()
    active_user = wallet.storage.get_active_user()

    return {
        "wallet": wallet,
        "storage": wallet.storage,
        "activeStorage": active_storage,
        "userId": active_user["userId"],
        "storageIdentityKey": storage_identity_result["storageIdentityKey"],
    }


class TestSpecOps:
    """Test suite for special operations (manual tests).

    Reference: wallet-toolbox/test/Wallet/specOps/specOps.man.test.ts
               describe('specOps tests')
    """

    def test_placeholder(self) -> None:
        """Placeholder test.

        Reference: wallet-toolbox/test/Wallet/specOps/specOps.man.test.ts
                   test('00')
        """

    @pytest.mark.asyncio
    async def test_wallet_balance_specop(self) -> None:
        """Given: Wallet with test data
           When: List outputs with specOpWalletBalance basket
           Then: Returns total outputs > 0 but empty outputs list

        Reference: wallet-toolbox/test/Wallet/specOps/specOps.man.test.ts
                   test('0 wallet balance specOp')
        """
        # Given
        setup = await create_setup("test")

        try:
            # When
            r = await setup.wallet.list_outputs(basket="specOpWalletBalance")

            # Then
            assert r["totalOutputs"] > 0
            assert len(r["outputs"]) == 0
        finally:
            await setup.wallet.destroy()

    @pytest.mark.asyncio
    async def test_wallet_balance_method(self) -> None:
        """Given: Wallet with test data
           When: Call balance() method
           Then: Returns balance > 0

        Reference: wallet-toolbox/test/Wallet/specOps/specOps.man.test.ts
                   test('0a wallet balance method')
        """
        # Given
        setup = await create_setup("test")

        try:
            # When
            r = await setup.wallet.balance()

            # Then
            assert r > 0
        finally:
            await setup.wallet.destroy()

    @pytest.mark.asyncio
    async def test_wallet_balanceandutxos_method(self) -> None:
        """Given: Wallet with test data
           When: Call balanceAndUtxos('default')
           Then: Returns total > 0 but empty utxos list

        Reference: wallet-toolbox/test/Wallet/specOps/specOps.man.test.ts
                   test('0b wallet balanceAndUtxos method')
        """
        # Given
        setup = await create_setup("test")

        try:
            # When
            r = await setup.wallet.balance_and_utxos("default")

            # Then
            assert r["total"] > 0
            assert len(r["utxos"]) == 0
        finally:
            await setup.wallet.destroy()

    @pytest.mark.asyncio
    async def test_wallet_invalid_change_outputs_specop(self) -> None:
        """Given: Wallet with test data
           When: List outputs with specOpInvalidChange basket
           Then: Returns 0 total outputs and empty outputs list

        Reference: wallet-toolbox/test/Wallet/specOps/specOps.man.test.ts
                   test('1 wallet invalid change outputs specOp')
        """
        # Given
        setup = await create_setup("test")

        try:
            # When
            r = await setup.wallet.list_outputs(basket="specOpInvalidChange")

            # Then
            assert r["totalOutputs"] == 0
            assert len(r["outputs"]) == 0
        finally:
            await setup.wallet.destroy()

    @pytest.mark.asyncio
    async def test_wallet_reviewspendableoutputs_method(self) -> None:
        """Given: Wallet with test data
           When: Call reviewSpendableOutputs(False, False, {})
           Then: Returns 0 total outputs and empty outputs list

        Reference: wallet-toolbox/test/Wallet/specOps/specOps.man.test.ts
                   test('1a wallet reviewSpendableOutputs method')
        """
        # Given
        setup = await create_setup("test")

        try:
            # When
            r = await setup.wallet.review_spendable_outputs(False, False, {})

            # Then
            assert r["totalOutputs"] == 0
            assert len(r["outputs"]) == 0
        finally:
            await setup.wallet.destroy()

    @pytest.mark.asyncio
    async def test_update_default_basket_params_specop(self) -> None:
        """Given: Wallet with default basket
           When: Update basket params via specOpSetWalletChangeParams with tags ['33', '6']
           Then: Basket params are updated to numberOfDesiredUTXOs=33, minimumDesiredUTXOValue=6

        Reference: wallet-toolbox/test/Wallet/specOps/specOps.man.test.ts
                   test('2 update default basket params specOp')
        """
        # Given
        setup = await create_setup("test")

        try:
            # Get original basket params
            before = await setup.active_storage.find_output_baskets(
                partial={"userId": setup.user_id, "name": "default"}
            )
            before = before[0]  # verifyOne

            # When
            r = await setup.wallet.list_outputs(basket="specOpSetWalletChangeParams", tags=["33", "6"])

            # Then
            after = await setup.active_storage.find_output_baskets(partial={"userId": setup.user_id, "name": "default"})
            after = after[0]  # verifyOne

            assert r["totalOutputs"] == 0
            assert len(r["outputs"]) == 0
            assert after["minimumDesiredUTXOValue"] == 6
            assert after["numberOfDesiredUTXOs"] == 33

            # Restore original values
            await setup.wallet.list_outputs(
                basket="specOpSetWalletChangeParams",
                tags=[str(before["numberOfDesiredUTXOs"]), str(before["minimumDesiredUTXOValue"])],
            )
        finally:
            await setup.wallet.destroy()

    @pytest.mark.asyncio
    async def test_update_default_basket_params_method(self) -> None:
        """Given: Wallet with default basket
           When: Call setWalletChangeParams(33, 6)
           Then: Basket params are updated to numberOfDesiredUTXOs=33, minimumDesiredUTXOValue=6

        Reference: wallet-toolbox/test/Wallet/specOps/specOps.man.test.ts
                   test('2a update default basket params specOp')
        """
        # Given
        setup = await create_setup("test")

        try:
            # Get original basket params
            before = await setup.active_storage.find_output_baskets(
                partial={"userId": setup.user_id, "name": "default"}
            )
            before = before[0]  # verifyOne

            # When
            await setup.wallet.set_wallet_change_params(33, 6)

            # Then
            after = await setup.active_storage.find_output_baskets(partial={"userId": setup.user_id, "name": "default"})
            after = after[0]  # verifyOne

            assert after["minimumDesiredUTXOValue"] == 6
            assert after["numberOfDesiredUTXOs"] == 33

            # Restore original values
            await setup.wallet.set_wallet_change_params(
                before["numberOfDesiredUTXOs"], before["minimumDesiredUTXOValue"]
            )
        finally:
            await setup.wallet.destroy()

    @pytest.mark.asyncio
    async def test_wallet_listnosendactions_method(self) -> None:
        """Given: Wallet with test data
           When: Call listNoSendActions({})
           Then: Returns totalActions >= 0 and actions list length equals totalActions

        Reference: wallet-toolbox/test/Wallet/specOps/specOps.man.test.ts
                   test('3 wallet listNoSendActions method')
        """
        # Given
        setup = await create_setup("test")

        try:
            # When
            r = await setup.wallet.list_no_send_actions(labels=[])

            # Then
            assert r["totalActions"] >= 0
            assert len(r["actions"]) == r["totalActions"]
        finally:
            await setup.wallet.destroy()

    @pytest.mark.asyncio
    async def test_wallet_listfailedactions_method(self) -> None:
        """Given: Wallet with test data
           When: Call listFailedActions({})
           Then: Returns totalActions >= 0 and actions list length equals totalActions

        Reference: wallet-toolbox/test/Wallet/specOps/specOps.man.test.ts
                   test('4 wallet listFailedActions method')
        """
        # Given
        setup = await create_setup("test")

        try:
            # When
            r = await setup.wallet.list_failed_actions(labels=[])

            # Then
            assert r["totalActions"] >= 0
            assert len(r["actions"]) == r["totalActions"]
        finally:
            await setup.wallet.destroy()

    @pytest.mark.asyncio
    async def test_wallet_specopthrowreviewactions(self) -> None:
        """Given: Wallet with test data
           When: List outputs with specOpThrowReviewActions basket
           Then: Raises ProcessActionError with reviewActions

        Reference: wallet-toolbox/test/Wallet/specOps/specOps.man.test.ts
                   test('5 Wallet specOpThrowReviewActions')
        """
        # Given
        setup = await create_setup("test")

        try:
            # When/Then
            with pytest.raises(Exception) as exc_info:  # ProcessActionError
                await setup.wallet.list_outputs(basket="specOpThrowReviewActions")

            # Verify exception contains reviewActions
            error = exc_info.value
            assert hasattr(error, "reviewActions") or "reviewActions" in str(error)
        finally:
            await setup.wallet.destroy()

    @pytest.mark.asyncio
    async def test_walletclient_specopthrowreviewactions(self) -> None:
        """Given: WalletClient with test data
           When: List outputs with specOpThrowReviewActions basket
           Then: Raises ProcessActionError with reviewActions

        Reference: wallet-toolbox/test/Wallet/specOps/specOps.man.test.ts
                   test('6 WalletClient specOpThrowReviewActions')
        """
        # Given
        # TODO: Create WalletClient setup instead of Wallet
        # Background: WalletClient is the client-side interface for remote wallet
        # communication (JSON-RPC over HTTPS). TypeScript has WalletClient in
        # ts-wallet-toolbox/src/WalletClient.ts which connects to StorageServer.
        # Python's JsonRpcClient (planned) will serve a similar purpose but is not
        # yet implemented. For now, use direct Wallet instance for testing.
        # See memory ID 11080878 for Python JSON-RPC implementation plan.
        setup = await create_setup("test")

        try:
            # When/Then
            with pytest.raises(Exception) as exc_info:  # ProcessActionError
                await setup.wallet.list_outputs(basket="specOpThrowReviewActions")

            # Verify exception contains reviewActions
            error = exc_info.value
            assert hasattr(error, "reviewActions") or "reviewActions" in str(error)
        finally:
            await setup.wallet.destroy()
