"""Manual tests for ARC (Atomic Router and Cache) service.

These tests require:
- Network access to ARC API endpoints
- TAAL API key (optional, for higher rate limits)
- Real blockchain transactions (testnet/mainnet)

Reference: toolbox/ts-wallet-toolbox/src/services/__tests/ARC.man.test.ts
"""

import os
import asyncio
import pytest
from typing import Optional
from bsv_wallet_toolbox.services import ARC
from bsv_wallet_toolbox.sdk.types import Chain


# Helper function stubs - to be implemented
async def create_no_send_tx_pair(chain: Chain):
    """Create a pair of transactions for testing (Do and Undo).
    
    Reference: toolbox/ts-wallet-toolbox/test/utils/TestUtilsWalletStorage.ts
               createNoSendTxPair method
    
    Raises:
        NotImplementedError: This helper is not yet implemented
    """
    raise NotImplementedError(
        "create_no_send_tx_pair helper not implemented yet. "
        "This requires porting TestUtilsWalletStorage from TypeScript."
    )


def get_taal_api_key() -> Optional[str]:
    """Get TAAL API key from environment variable.
    
    Returns:
        API key if set, None otherwise
    """
    return os.getenv("TAAL_API_KEY")


def get_arc_url(chain: Chain) -> str:
    """Get ARC URL for the specified chain.
    
    Args:
        chain: 'main' or 'test'
        
    Returns:
        ARC API URL
    """
    if chain == "main":
        return os.getenv("ARC_MAIN_URL", "https://api.taal.com/arc")
    else:
        return os.getenv("ARC_TEST_URL", "https://api.taal.com/arc/testnet")


class TestARCPostBeef:
    """Test suite for ARC.postBeef method.
    
    Reference: toolbox/ts-wallet-toolbox/src/services/__tests/ARC.man.test.ts
    """
    
    @pytest.mark.skip(reason="Requires network access, ARC API, and funded test wallet - run manually")
    @pytest.mark.asyncio
    async def test_post_beef_testnet(self) -> None:
        """Given: Valid BEEF transaction for testnet
           When: Call postBeef to submit to ARC testnet
           Then: Returns success status with txid results
           
        Note: Requires TAAL_API_KEY environment variable for authentication.
              Requires test wallet setup to create BEEF transactions.
              
        Reference: toolbox/ts-wallet-toolbox/src/services/__tests/ARC.man.test.ts
                   test('9 postBeef testnet')
        """
        # Given
        api_key = get_taal_api_key()
        arc_url = get_arc_url("test")
        arc = ARC(arc_url, api_key=api_key)
        
        # Create BEEF transaction (requires wallet setup with _tu.createNoSendTxPair)
        tx_pair = await create_no_send_tx_pair("test")
        txids = [tx_pair.txid_do, tx_pair.txid_undo]
        
        # When
        result = await arc.post_beef(tx_pair.beef, txids)
        
        # Then
        assert result["status"] == "success"
        for txid in txids:
            tx_result = next((tr for tr in result["txidResults"] if tr["txid"] == txid), None)
            assert tx_result is not None
            assert tx_result["status"] == "success"
        
        # When - Test double spend detection
        beef2 = tx_pair.beef.clone()
        beef2.txs[-1] = tx_pair.double_spend_tx
        txids2 = [tx_pair.txid_do, tx_pair.double_spend_tx.id_hex()]
        
        result2 = await arc.post_beef(beef2, txids2)
        
        # Then
        assert result2["status"] == "error"
        for txid in txids2:
            tr = next((t for t in result2["txidResults"] if t["txid"] == txid), None)
            assert tr is not None
            if txid == tx_pair.txid_do:
                assert tr["status"] == "success"
            else:
                assert tr["status"] == "error"
                assert tr["doubleSpend"] is True
                assert tx_pair.txid_undo in tr["competingTxs"]
    
    @pytest.mark.skip(reason="Requires network access, ARC API, and funded wallet - run manually")
    @pytest.mark.asyncio
    async def test_post_beef_mainnet(self) -> None:
        """Given: Valid BEEF transaction for mainnet
           When: Call postBeef to submit to ARC mainnet
           Then: Returns success status with txid results
           
        Note: Requires TAAL_API_KEY environment variable for authentication.
              Requires main wallet setup to create BEEF transactions.
              USE WITH CAUTION: Submits real transactions to mainnet!
              
        Reference: toolbox/ts-wallet-toolbox/src/services/__tests/ARC.man.test.ts
                   test('10 postBeef mainnet')
        """
        # Given
        api_key = get_taal_api_key()
        arc_url = get_arc_url("main")
        arc = ARC(arc_url, api_key=api_key)
        
        # Create BEEF transaction (requires wallet setup)
        tx_pair = await create_no_send_tx_pair("main")
        txids = [tx_pair.txid_do, tx_pair.txid_undo]
        
        # When
        result = await arc.post_beef(tx_pair.beef, txids)
        
        # Then
        assert result["status"] == "success"
        for txid in txids:
            tx_result = next((tr for tr in result["txidResults"] if tr["txid"] == txid), None)
            assert tx_result is not None
            assert tx_result["status"] == "success"
    
    @pytest.mark.skip(reason="Requires network access and ARC API - run manually")
    @pytest.mark.asyncio
    async def test_double_spend_detection(self) -> None:
        """Given: BEEF with double spend transaction
           When: Call postBeef with conflicting transactions
           Then: Returns error status with doubleSpend flag and competing txids
           
        Note: Requires TAAL_API_KEY environment variable for authentication.
              Tests double spend detection by submitting conflicting transactions.
              
        Reference: toolbox/ts-wallet-toolbox/src/services/__tests/ARC.man.test.ts
                   test('0 double spend')
        """
        # Given
        api_key = get_taal_api_key()
        arc_url = get_arc_url("test")
        arc = ARC(arc_url, api_key=api_key)
        
        # Known testnet BEEF with double spend
        testnet_double_spend_beef = (
            "0100beef01fe65631900020200009df812619ae232d2363d91516ab3e811211192933526bbc2aee71b54ccb236d1"
            "0102462876eec65d9aa26d957421c5cc8dd9119b61177242b9dd814fb190fd0a361801010076a3297928f6841bcb"
            "656e91225540e87c65f67d8ec12bc768d7656eb7561b3d02010000000159617a9d17562f7c9765e5dfa6a9a393aa"
            "2809ca6166a3d7a31c09efcc5070141f0000006a47304402200a528145a67ba1879b88a093cb711f79f04413a81d"
            "5678f314302e36a7f59e43022010bc4bb3c2574052c50bbdc8a05c31fb39e69280656b34f5dc22e2ceadc3bb4a41"
            "2102fd4200bf389d16479b3d06f97fee0752f2c3b9dc29fb3ddce2b327d851b8902bffffffff0204000000000000"
            "001976a9140df1a69c834bb7d9bb5b2b7d6a34e5a401db3e1688ac01000000000000001976a91423f2562a8092ed"
            "24eddc77c74387b44c561692a188ac0000000001000100000001462876eec65d9aa26d957421c5cc8dd9119b6117"
            "7242b9dd814fb190fd0a3618000000006a47304402204183bbfdcf11d50907b91f5e70ea8f81228501ce84e24af7"
            "5c8d984682d094dc022029caa8f7e5acb4990bbeafee523a3c4a99b78e98b9e5c41349147b099679d4ae412103b7"
            "6389eea6494c2c30443cba9d59b9dba05fb04e467bc94272629615b87a429fffffffff0202000000000000001976"
            "a91476d851e59fcb4ee0ebe6947496db3a393b08e49c88ac01000000000000001976a91423f2562a8092ed24eddc"
            "77c74387b44c561692a188ac0000000000"
        )
        
        # When
        from bsv.sdk import Beef
        beef = Beef.from_string(testnet_double_spend_beef)
        txids = [beef.txs[-1].txid]
        result = await arc.post_beef(beef, txids)
        
        # Then
        assert result["status"] == "error"
        assert result["txidResults"][0]["doubleSpend"] is True


class TestARCPostRawTx:
    """Test suite for ARC.postRawTx method.
    
    Reference: toolbox/ts-wallet-toolbox/src/services/__tests/ARC.man.test.ts
    """
    
    @pytest.mark.skip(reason="Requires network access, ARC API, and funded test wallet - run manually")
    @pytest.mark.asyncio
    async def test_post_raw_tx_testnet(self) -> None:
        """Given: Valid raw transaction hex for testnet
           When: Call postRawTx to submit to ARC testnet
           Then: Returns success status with txid
           
        Note: Requires TAAL_API_KEY environment variable for authentication.
              Requires test wallet setup to create transactions.
              
        Reference: toolbox/ts-wallet-toolbox/src/services/__tests/ARC.man.test.ts
                   test('7 postRawTx testnet')
        """
        # Given
        api_key = get_taal_api_key()
        arc_url = get_arc_url("test")
        arc = ARC(arc_url, api_key=api_key)
        
        # Create raw transactions (requires wallet setup)
        tx_pair = await create_no_send_tx_pair("test")
        raw_tx_do = tx_pair.beef.find_txid(tx_pair.txid_do).tx.to_hex()
        raw_tx_undo = tx_pair.beef.find_txid(tx_pair.txid_undo).tx.to_hex()
        
        # When - Submit first transaction
        result_do = await arc.post_raw_tx(raw_tx_do)
        
        # Then
        assert result_do["status"] == "success"
        assert result_do["txid"] == tx_pair.txid_do
        
        # Wait for confirmation
        await asyncio.sleep(1)
        
        # When - Submit second transaction
        result_undo = await arc.post_raw_tx(raw_tx_undo)
        
        # Then
        assert result_undo["status"] == "success"
        assert result_undo["txid"] == tx_pair.txid_undo
        assert result_undo.get("doubleSpend") is not True
        
        # Wait
        await asyncio.sleep(1)
        
        # When - Submit same transaction again (should succeed - idempotent)
        result_undo_2 = await arc.post_raw_tx(raw_tx_undo)
        
        # Then
        assert result_undo_2["status"] == "success"
        assert result_undo_2["txid"] == tx_pair.txid_undo
        assert result_undo_2.get("doubleSpend") is not True
        
        # Wait
        await asyncio.sleep(1)
        
        # When - Submit double spend transaction
        result_double = await arc.post_raw_tx(tx_pair.double_spend_tx.to_hex())
        
        # Then
        assert result_double["status"] == "error"
        assert result_double["doubleSpend"] is True
        assert tx_pair.txid_undo in result_double["competingTxs"]
    
    @pytest.mark.skip(reason="Requires network access, ARC API, and funded wallet - run manually")
    @pytest.mark.asyncio
    async def test_post_raw_tx_mainnet(self) -> None:
        """Given: Valid raw transaction hex for mainnet
           When: Call postRawTx to submit to ARC mainnet
           Then: Returns success status with txid
           
        Note: Requires TAAL_API_KEY environment variable for authentication.
              Requires main wallet setup to create transactions.
              USE WITH CAUTION: Submits real transactions to mainnet!
              
        Reference: toolbox/ts-wallet-toolbox/src/services/__tests/ARC.man.test.ts
                   test('8 postRawTx mainnet')
        """
        # Given
        api_key = get_taal_api_key()
        arc_url = get_arc_url("main")
        arc = ARC(arc_url, api_key=api_key)
        
        # Create raw transactions (requires wallet setup)
        tx_pair = await create_no_send_tx_pair("main")
        raw_tx_do = tx_pair.beef.find_txid(tx_pair.txid_do).tx.to_hex()
        
        # When
        result = await arc.post_raw_tx(raw_tx_do)
        
        # Then
        assert result["status"] == "success"
        assert result["txid"] == tx_pair.txid_do

