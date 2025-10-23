"""Unit tests for Wallet Services integration.

Ported from TypeScript implementation to ensure compatibility.

Reference: toolbox/ts-wallet-toolbox/test/services/Services.test.ts

Note: All tests are currently skipped as the Services API is not yet implemented.
"""

import pytest
import hashlib

from bsv_wallet_toolbox import Wallet


class TestServices:
    """Test suite for Wallet Services integration.
    
    Reference: toolbox/ts-wallet-toolbox/test/services/Services.test.ts
               Wallet services tests
    """
    
    @pytest.mark.skip(reason="Waiting for Services API implementation")
    @pytest.mark.asyncio
    async def test_getutxostatus(self) -> None:
        """Given: Wallet with services configured on mainnet
           When: Call getUtxoStatus with script
           Then: Returns success status and is_utxo True
           
        Reference: toolbox/ts-wallet-toolbox/test/services/Services.test.ts
                   test('0 getUtxoStatus')
        """
        # Given
        wallet = Wallet(chain="main")
        # Wallet needs to be set up with services
        script = "4104eca750b68551fb5aa893acb428b6a7d2d673498fd055cf2a8d402211b9500bdc27936846c2aa45cf82afe2f566b69cd7f7298154b0ffb25fbfa4fef8986191c4ac"
        
        # When
        us = await wallet.services.get_utxo_status(script, "script")
        
        # Then
        assert us["status"] == "success"
        assert us["is_utxo"] is True
    
    @pytest.mark.skip(reason="Waiting for Services API implementation")
    @pytest.mark.asyncio
    async def test_getutxostatus_hashle(self) -> None:
        """Given: Wallet with services configured on mainnet
           When: Call getUtxoStatus with hash (LE format, default)
           Then: Returns success status and is_utxo True
           
        Reference: toolbox/ts-wallet-toolbox/test/services/Services.test.ts
                   test('0a getUtxoStatus hashLE')
        """
        # Given
        wallet = Wallet(chain="main")
        script = "4104eca750b68551fb5aa893acb428b6a7d2d673498fd055cf2a8d402211b9500bdc27936846c2aa45cf82afe2f566b69cd7f7298154b0ffb25fbfa4fef8986191c4ac"
        hash_value = hashlib.sha256(bytes.fromhex(script)).hex()
        
        # When
        us = await wallet.services.get_utxo_status(hash_value)  # Default is hashLE
        
        # Then
        assert us["status"] == "success"
        assert us["is_utxo"] is True
    
    @pytest.mark.skip(reason="Waiting for Services API implementation")
    @pytest.mark.asyncio
    async def test_getutxostatus_hashbe(self) -> None:
        """Given: Wallet with services configured on mainnet
           When: Call getUtxoStatus with hash (BE format)
           Then: Returns success status and is_utxo True
           
        Reference: toolbox/ts-wallet-toolbox/test/services/Services.test.ts
                   test('0b getUtxoStatus hashBE')
        """
        # Given
        wallet = Wallet(chain="main")
        script = "4104eca750b68551fb5aa893acb428b6a7d2d673498fd055cf2a8d402211b9500bdc27936846c2aa45cf82afe2f566b69cd7f7298154b0ffb25fbfa4fef8986191c4ac"
        hash_value = hashlib.sha256(bytes.fromhex(script))[::-1].hex()
        
        # When
        us = await wallet.services.get_utxo_status(hash_value, "hashBE")
        
        # Then
        assert us["status"] == "success"
        assert us["is_utxo"] is True
    
    @pytest.mark.skip(reason="Waiting for Services API implementation")
    @pytest.mark.asyncio
    async def test_getutxostatus_hashoutputscript_method(self) -> None:
        """Given: Wallet with services configured on mainnet
           When: Call getUtxoStatus with hash from hashOutputScript method
           Then: Returns success status and is_utxo True
           
        Reference: toolbox/ts-wallet-toolbox/test/services/Services.test.ts
                   test('0c getUtxoStatus hashOutputScript method')
        """
        # Given
        wallet = Wallet(chain="main")
        script = "4104eca750b68551fb5aa893acb428b6a7d2d673498fd055cf2a8d402211b9500bdc27936846c2aa45cf82afe2f566b69cd7f7298154b0ffb25fbfa4fef8986191c4ac"
        
        # When
        hash_value = wallet.services.hash_output_script(script)
        us = await wallet.services.get_utxo_status(hash_value)
        
        # Then
        assert us["status"] == "success"
        assert us["is_utxo"] is True
    
    @pytest.mark.skip(reason="Waiting for Services API implementation")
    @pytest.mark.asyncio
    async def test_getutxostatus_outpoint(self) -> None:
        """Given: Wallet with services configured on mainnet
           When: Call getUtxoStatus with hash and specific outpoint
           Then: Returns success status and is_utxo True
           
        Reference: toolbox/ts-wallet-toolbox/test/services/Services.test.ts
                   test('0d getUtxoStatus outpoint')
        """
        # Given
        wallet = Wallet(chain="main")
        script = "4104eca750b68551fb5aa893acb428b6a7d2d673498fd055cf2a8d402211b9500bdc27936846c2aa45cf82afe2f566b69cd7f7298154b0ffb25fbfa4fef8986191c4ac"
        hash_value = wallet.services.hash_output_script(script)
        outpoint = "e4154d8ab6993addc9b8705318cc8e971dfc0780e233038ecf44c601229d93ce.0"
        
        # When
        us = await wallet.services.get_utxo_status(hash_value, None, outpoint)
        
        # Then
        assert us["status"] == "success"
        assert us["is_utxo"] is True
    
    @pytest.mark.skip(reason="Waiting for Services API implementation")
    @pytest.mark.asyncio
    async def test_getutxostatus_invalid_outpoint(self) -> None:
        """Given: Wallet with services configured on mainnet
           When: Call getUtxoStatus with hash and invalid outpoint
           Then: Returns success status and is_utxo False
           
        Reference: toolbox/ts-wallet-toolbox/test/services/Services.test.ts
                   test('0e getUtxoStatus invalid outpoint')
        """
        # Given
        wallet = Wallet(chain="main")
        script = "4104eca750b68551fb5aa893acb428b6a7d2d673498fd055cf2a8d402211b9500bdc27936846c2aa45cf82afe2f566b69cd7f7298154b0ffb25fbfa4fef8986191c4ac"
        hash_value = wallet.services.hash_output_script(script)
        invalid_outpoint = "e4154d8ab6993addc9b8705318cc8e971dfc0780e233038ecf44c601229d93ce.1"
        
        # When
        us = await wallet.services.get_utxo_status(hash_value, None, invalid_outpoint)
        
        # Then
        assert us["status"] == "success"
        assert us["is_utxo"] is False
    
    @pytest.mark.skip(reason="Waiting for Services API implementation")
    @pytest.mark.asyncio
    async def test_getfiatexchangerate(self) -> None:
        """Given: Wallet with services configured
           When: Call getFiatExchangeRate for EUR/USD
           Then: Returns positive exchange rate
           
        Reference: toolbox/ts-wallet-toolbox/test/services/Services.test.ts
                   test('2 getFiatExchangeRate')
        """
        # Given
        wallet = Wallet(chain="main")
        
        # When
        eur_per_usd = await wallet.services.get_fiat_exchange_rate("EUR", "USD")
        
        # Then
        assert eur_per_usd > 0
    
    @pytest.mark.skip(reason="Waiting for Services API implementation")
    @pytest.mark.asyncio
    async def test_getchaintracker(self) -> None:
        """Given: Wallet with services configured
           When: Call getChainTracker and get current height
           Then: Returns height greater than 800000
           
        Reference: toolbox/ts-wallet-toolbox/test/services/Services.test.ts
                   test('3 getChainTracker')
        """
        # Given
        wallet = Wallet(chain="main")
        
        # When
        chain_tracker = await wallet.services.get_chain_tracker()
        height = await chain_tracker.current_height()
        
        # Then
        assert height > 800000
    
    @pytest.mark.skip(reason="Waiting for Services API implementation")
    @pytest.mark.asyncio
    async def test_getmerklepath(self) -> None:
        """Given: Wallet with services configured on mainnet
           When: Call getMerklePath for known txid
           Then: Returns merkle path with block height 877599
           
        Reference: toolbox/ts-wallet-toolbox/test/services/Services.test.ts
                   test('4 getMerklePath')
        """
        # Given
        wallet = Wallet(chain="main")
        txid = "9cce99686bc8621db439b7150dd5b3b269e4b0628fd75160222c417d6f2b95e4"
        
        # When
        mp = await wallet.services.get_merkle_path(txid)
        
        # Then
        assert mp["merkle_path"]["block_height"] == 877599
    
    @pytest.mark.skip(reason="Waiting for Services API implementation")
    @pytest.mark.asyncio
    async def test_getrawtx(self) -> None:
        """Given: Wallet with services configured on mainnet
           When: Call getRawTx for known txid
           Then: Returns raw transaction with length 176
           
        Reference: toolbox/ts-wallet-toolbox/test/services/Services.test.ts
                   test('5 getRawTx')
        """
        # Given
        wallet = Wallet(chain="main")
        txid = "9cce99686bc8621db439b7150dd5b3b269e4b0628fd75160222c417d6f2b95e4"
        
        # When
        raw_tx = await wallet.services.get_raw_tx(txid)
        
        # Then
        assert len(raw_tx["raw_tx"]) == 176
    
    @pytest.mark.skip(reason="Waiting for Services API implementation")
    @pytest.mark.asyncio
    async def test_getscripthashhistory(self) -> None:
        """Given: Wallet with services configured on mainnet
           When: Call getScriptHashHistory for known script hash (reversed)
           Then: Returns success status and history with length > 0
           
        Reference: toolbox/ts-wallet-toolbox/test/services/Services.test.ts
                   test('6 getScriptHashHistory')
        """
        # Given
        wallet = Wallet(chain="main")
        hash_le = "86e41f4725135ca0db59d074e7d60daae7c1a87699013498bae52dc95cae1a52"
        hash_be = bytes.fromhex(hash_le)[::-1].hex()
        
        # When
        us = await wallet.services.get_script_hash_history(hash_be)
        
        # Then
        assert us["status"] == "success"
        assert len(us["history"]) > 0

