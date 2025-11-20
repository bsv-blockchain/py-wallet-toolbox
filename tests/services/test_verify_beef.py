"""Unit tests for verifyBeef service.

This module tests BEEF verification functionality.

Reference: wallet-toolbox/src/services/__tests/verifyBeef.test.ts
"""

import pytest

try:
    from bsv.transaction import Beef
    from bsv_wallet_toolbox.services import Services
    from tests.test_utils import TestUtils

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


# Sample BEEF hex string for testing
BEEF_HEX = "0200beef01fe7c830d000a02a0021d4ca6c031db7f6334c08ddfda43cbde3800c7fa27892f8e80a5218ca8493918a10081788ac8d8267d409b6258a6a6f5d28317ee65b5b25892def4f6cbf44f92571d01510027c2382032711033d0a1e2724b9eefcf257e27bce28e37b7472877860570ee6e0129008e15879954392f322efdd32376077a3323db02501926a697f5db6b68862f67ce01150061dcb195186d564d754a056d9ad90d65ece5bfa5ddccebd24b64d25df3780b15010b00bcd8f2c9c62b4fbbefad9640f9f6dccf21246fa08a6e1cab2c052666dee4182001040018ad6a5739749e27c191a5ef7442d861e5b8d204d36c91e08bf8015811851dbe010300f47047d1c4582eb02349eabcdafc7f4573e93ed687718275475d6f528783d16201000039a5fa5dbbbcd4a1754c250a7879ae1ad2eeb189d87d3614c2a2d9519a7a47af0101001670fc6a8d40adbd3f8a84ae35f0a702695f19f19a8feddcfd1de6249cc164e901010092a689a4cda27aea3552a98a7441ffbaed8566ae31e0a1a67e67647e2f3b8fda05025a8b77e1c82cfcfda197fec3f805a6b7000737a583e45833df6721975fe8bad102448f38860c45d33c87041c0fda51befb1c90853d3141a0df3ac737ccb9b5e61b01000100000001f7ddf439a165bf63a7d6c144b4bd8882ff45dc35a3ca3e75517fa56482fed6bd000000006b4830450221008106bc7164333415bc485ae1d12acd72bbc536f1f03b25aa42d92971565b329902202d484d09935be7fa49bbd5806148dbfdb90cc86516537351acf20655c03fa656412102b53b5339d6241c4271a07e7b09035966defe37c1a3edd60b8a427d5a5b488cb5ffffffff021d00000000000000c421029664d9baa433b4ded47ce151d348fda7ed30df597b93bf5f321ec2fe742b0faaac2131546f446f44744b7265457a6248594b466a6d6f42756475466d53585855475a4734aba7171082ff009628f6d1abea57bc1ffcdb6c2b45a5e17219eaf6bc6b6e093b5243036565505084548f9715a440b6c03e73427d4730450221008e4964dc5e8f3cc6f41da7508cba05babb2ce211fa47fe91ae9c06903d95fde902206cb21d6c188f302fccedbbcd80459561dbabcabe3da16853371fede9f5d027d06d75c8030000000000001976a914f8a84c2bef6eed4eb3270c8605a8063202ed25cb88ac000000000001000000015a8b77e1c82cfcfda197fec3f805a6b7000737a583e45833df6721975fe8bad1010000006b483045022100fb62de36ac2930029b1397931c3f30bf6df5166f2e82bed6b2ef1d23491f8e450220730105461dc12236439ee568709ee72c345bb6748efe8656a0e96e4cc5eaecfb412102c6b33e96f3b635ebd71bcedd9bcb90b4c098b9b38730f58984e23615e0864833ffffffff042800000000000000c521029664d9baa433b4ded47ce151d348fda7ed30df597b93bf5f321ec2fe742b0faaac2131546f446f44744b7265457a6248594b466a6d6f42756475466d53585855475a47361c08d47822cb0806cd17af298948641db6bd36440da9a988af0f6600cba6dabfcfe5c7fe086b7a08e8feef3a9d21d8b0126c2f4a260b46304402204f418ece238fb0587f887c1e0ea6beb4ebcefa6749d1b523195bd65dc9971374022009d0b21c669a72a8a01808d394c55de730a3a4d287b3bb209697b2e79a9787ce6d7516050000000000001976a914803a2e1d2ca2373c21129a7075f1a42587f16c8188acec030000000000001976a91441cb6381a584c464df4b6dd75b91fb0ab6c4b7a688acd0040000000000001976a914e08fbd92ba37c1d84bba8439c55793ea60c0dd6b88ac00000000000100000001448f38860c45d33c87041c0fda51befb1c90853d3141a0df3ac737ccb9b5e61b020000006a4730440220411ab1f23f747899bf71185fbb4ab03defc6e215fb1ee3d24060b14256d2dc40022035669cd13b5c5fd399a402862b4e6bc001d0cbf56660bac37b1563eeaf49a700412103b20f91159733fd69817cc4d4f9ed0cf4340f63b482e0a0a7f233885c61d1b044ffffffff020a00000000000000c421029664d9baa433b4ded47ce151d348fda7ed30df597b93bf5f321ec2fe742b0faaac2131546f446f44744b7265457a6248594b466a6d6f42756475466d53585855475a47343c32fe905bb02e70c0a9779048c921b1e26a2684c498ab44759ac25bcdfafa95309c59d1c3ac12f056ad8d10dabe777d1d57dd934730450221009a64cdc81a0ada12d329463db24260a15ad56bdc3523613c0fae2fb64762d20e022021b942e859749fc23585fdb0395585d6ea52dcf0a310cc989a38ff0483c8717e6d75b7150000000000001976a91468cce1214ccbd14d9dfd813d8490daadaa96b39288ac00000000"


class TestVerifyBeef:
    """Test suite for BEEF verification.

    Reference: wallet-toolbox/src/services/__tests/verifyBeef.test.ts
               describe('verifyBeef tests')
    """

    @pytest.mark.skip(reason="Beef.from_string not available, needs parse_beef integration")
    def test_verify_beef_from_hex(self) -> None:
        """Given: BEEF hex string and mainnet services
           When: Parse BEEF and verify with chaintracker
           Then: BEEF verifies successfully

        Reference: wallet-toolbox/src/services/__tests/verifyBeef.test.ts
                   test('0_')
        
        Note: bsv.transaction.Beef doesn't have from_string method.
              Need to use parse_beef from bsv.transaction.beef module.
        """
        # Given
        from bsv.transaction.beef import parse_beef
        beef = parse_beef(bytes.fromhex(BEEF_HEX))
        chaintracker = Services("main").get_chain_tracker()

        # When
        ok = beef.verify(chaintracker, True)

        # Then
        assert ok is True

    def test_verify_beef_from_storage(self) -> None:
        """Given: Wallet storage with mainnet setup
           When: Get BEEF for txid from services and storage, then verify both
           Then: Both BEEFs verify successfully

        Reference: wallet-toolbox/src/services/__tests/verifyBeef.test.ts
                   test('1_')
        """
        # Given

        if TestUtils.no_env("main"):
            return

        setup = TestUtils.create_main_review_setup()
        setup["env"]
        storage = setup["storage"]
        services = setup["services"]

        get_beef_for_txid = "4d9a1eff26bac99c7524cb7b2e808b77935d3d890562db2fefc6cb8cb92a6b16"

        # When/Then - Get BEEF from services
        beef = services.get_beef_for_txid(get_beef_for_txid)
        chaintracker = services.get_chain_tracker()
        ok = beef.verify(chaintracker, True)
        assert ok is True

        # When/Then - Get BEEF from storage
        beef = verify_truthy(storage.get_valid_beef_for_txid(get_beef_for_txid, None, None, None, None, 1))
        chaintracker = services.get_chain_tracker()
        ok = beef.verify(chaintracker, True)
        assert ok is True
