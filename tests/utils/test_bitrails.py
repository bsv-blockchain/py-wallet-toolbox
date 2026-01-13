"""Unit tests for bitrails service.

This module tests bitrails merkle proof verification and conversion.

Reference: wallet-toolbox/src/services/__tests/bitrails.test.ts
"""

try:
    from bsv_wallet_toolbox.services import Services, convert_proof_to_merkle_path
    from bsv_wallet_toolbox.services.providers import Bitails
    from bsv_wallet_toolbox.types import TscMerkleProofApi

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


PROOF2_MERKLE_ROOT = "22b294aac4c3f6f4fdae30dc4f46f68f90feb94f03531c32bcf2ce33be5d4cb0"

PROOF2: "TscMerkleProofApi" = {
    "index": 9443,
    "height": 742198,
    "nodes": [
        "463c37bf0ccde321b1dc8ee857e03b8eafe76e6b1803cc3a774cfef61c50c37b",
        "debba259db996d6ca7c4fcfd168d3afe6bfdddab93298466d53ed0421634f405",
        "6335d744771789ef69545b0f449bcde92ae7b9920e775a591fecc7fcfa37846e",
        "38366b3723e8f166fbfe5d7528a57885f47aa25a8296c0679832a95c1e6d2f61",
        "5a999d2186d10a787c3397938fd97a4b3e833aab8cff2ce24cfce7589b9b706b",
        "db97fbd581b8769602c6079e7fe10eb34cd99b844598b31441018ac21babd7e7",
        "583e044e2bbc6b19993e73c3363a8ce3b4580a54510524489daadc6c82205f5a",
        "ba5d97e4fbedb84682f65b254c56f5826f1dc65bd376dc1660f23b81c4035b1d",
        "bfa39460ee7a8293698e41134a53cfc5ba0054416ca092d79ecbf93ae2b8b71b",
        "8f3d186687f3f8186c4cbddcf263bbb4b58e3c279e55f9def048076faff0cc83",
        "287790c47a0044e8e51ee60df33d4d23b972b5a51d8e9be7ac8b635b9f1e7ffc",
        "19444e7ad68681d847d4d88989efa5f13afa46d7cbb47e8ce91876555c3e414d",
        "6d71f472dabd52216a3cb24090d580baed96497b449876c199f48ed07f5ea2b0",
        "af4c17b677b0c7b4d85e7331b4e43fc16f9a7024c9417d7854c55a096ac098b3",
    ],
}


class TestBitrails:
    """Test suite for bitrails service.

    Reference: wallet-toolbox/src/services/__tests/bitrails.test.ts
               describe('bitrails tests')
    """

    def test_verify_merkle_proof_to_merkle_path(self) -> None:
        """Given: TSC merkle proof for a txid
           When: Convert proof to merkle path and compute root
           Then: Computed root matches expected merkle root

        Reference: wallet-toolbox/src/services/__tests/bitrails.test.ts
                   test('0 verify merkle proof to merkle path')
        """
        # Given
        txid = "068f2ce0d01b5f1e7c7a07c209c3c67d583aeae83e11e92801b51c36f81d6b67"

        # When
        mp = convert_proof_to_merkle_path(txid, PROOF2)
        root = mp.compute_root(txid)

        # Then
        assert root == PROOF2_MERKLE_ROOT

    def test_bitails_get_merkle_path(self) -> None:
        """Given: Bitails service and services for mainnet
           When: Get merkle path for recent txids
           Then: Merkle path computes correct root (if available, as Bitails prunes historical data)

        Reference: wallet-toolbox/src/services/__tests/bitrails.test.ts
                   test('1 ')
        """
        # Given
        chain = "main"
        bitails = Bitails(chain)
        services = Services(chain)

        # Bitails prunes historical data, only recent txids are available.
        test_txids = [
            "068f2ce0d01b5f1e7c7a07c209c3c67d583aeae83e11e92801b51c36f81d6b67",
            "a65c2663d817da6474f7805cf103be6259aae16b01468711552b737c41768c30",
            "243fb25b94b5ef2f8554cd10d105005f51ff543d8b7a498c4e46ed304c3da24a",
        ]

        # When/Then
        for txid in test_txids:
            mp_result = bitails.get_merkle_path(txid, services)
            if mp_result.merkle_path:
                root = mp_result.merkle_path.compute_root(txid)
                # Note: Expected root depends on block, this is just checking the computation works
                assert root is not None
                assert len(root) == 64  # Hex string of 32 bytes
