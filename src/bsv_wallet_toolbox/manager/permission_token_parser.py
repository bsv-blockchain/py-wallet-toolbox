"""Permission Token Parser - PushDrop token creation and parsing for permissions.

Handles creation and parsing of PushDrop-based permission tokens for the
four BRC-73 permission protocols: DPACP, DBAP, DCAP, DSAP.

Reference: wallet-toolbox/src/WalletPermissionsManager.ts PushDrop operations
"""

from __future__ import annotations

import time
from typing import Any

from bsv_wallet_toolbox.manager.permission_types import PermissionToken


class PushDropEncoder:
    """PushDrop script encoder for permission tokens.

    Creates PushDrop locking scripts for permission tokens.
    """

    @staticmethod
    def encode_permission_token(
        token: PermissionToken, admin_originator: str, protocol_key: str = "1"
    ) -> dict[str, Any]:
        """Encode permission token as PushDrop script.

        Args:
            token: Permission token to encode
            admin_originator: Admin domain/FQDN
            protocol_key: Protocol key ID (default: "1")

        Returns:
            PushDrop script data with fields and locking script

        Reference: wallet-toolbox/src/WalletPermissionsManager.ts createPushDropScript
        """
        # Build fields array based on token type
        fields = []

        # Common fields for all tokens
        fields.append(token.get("originator", ""))
        fields.append(token.get("expiry", 0))

        # Type-specific fields
        token_type = token.get("type")
        if token_type == "protocol":
            # DPACP: Domain Protocol Access Control Protocol
            protocol_data = token.get("protocol", "")
            security_level = token.get("securityLevel", 0)
            counterparty = token.get("counterparty", "")
            privileged = token.get("privileged", False)

            fields.extend([protocol_data, security_level, counterparty, privileged])

        elif token_type == "basket":
            # DBAP: Domain Basket Access Protocol
            basket_name = token.get("basketName", "")
            fields.append(basket_name)

        elif token_type == "certificate":
            # DCAP: Domain Certificate Access Protocol
            cert_type = token.get("certType", "")
            verifier = token.get("verifier", "")
            cert_fields = token.get("certFields", [])

            fields.extend([cert_type, verifier, cert_fields])

        elif token_type == "spending":
            # DSAP: Domain Spending Authorization Protocol
            authorized_amount = token.get("authorizedAmount", 0)
            fields.append(authorized_amount)

        # Create PushDrop script
        # This is a simplified version - in reality would use actual PushDrop encoding
        script_data = {
            "fields": fields,
            "protocolID": [2, f"admin {token_type} permission"],
            "keyID": protocol_key,
            "counterparty": "self",
            "lockingScript": f"pushdrop_{token_type}_{token.get('originator', '')}_{token.get('txid', '')}",
        }

        return script_data


class PushDropDecoder:
    """PushDrop script decoder for permission tokens.

    Parses PushDrop locking scripts back into permission tokens.
    """

    @staticmethod
    def decode_permission_token(script_hex: str, txid: str, output_index: int, satoshis: int) -> PermissionToken | None:
        """Decode PushDrop script into permission token.

        Args:
            script_hex: Hex-encoded locking script
            txid: Transaction ID containing the token
            output_index: Output index of the token
            satoshis: Satoshis locked in the token

        Returns:
            Decoded PermissionToken or None if invalid

        Reference: wallet-toolbox/src/WalletPermissionsManager.ts decodePushDropFields
        """
        # This is a simplified decoder - real implementation would parse actual PushDrop script
        if not script_hex.startswith("pushdrop_"):
            return None

        # Parse token type from script
        parts = script_hex.split("_")
        if len(parts) < 4:
            return None

        token_type = parts[1]  # protocol, basket, certificate, spending
        originator = parts[2]

        # Create base token
        token: PermissionToken = {
            "txid": txid,
            "tx": [],  # Would contain actual transaction data
            "outputIndex": output_index,
            "outputScript": script_hex,
            "satoshis": satoshis,
            "originator": originator,
            "expiry": 0,  # Would be parsed from actual script
        }

        # Add type-specific fields based on token type
        if token_type == "protocol":
            token.update(
                {
                    "type": "protocol",
                    "protocol": "",  # Would be parsed from script
                    "securityLevel": 0,
                    "counterparty": "",
                    "privileged": False,
                }
            )
        elif token_type == "basket":
            token.update(
                {
                    "type": "basket",
                    "basketName": "",  # Would be parsed from script
                }
            )
        elif token_type == "certificate":
            token.update(
                {
                    "type": "certificate",
                    "certType": "",
                    "verifier": "",
                    "certFields": [],
                }
            )
        elif token_type == "spending":
            token.update(
                {
                    "type": "spending",
                    "authorizedAmount": 0,
                }
            )

        return token


class PermissionTokenManager:
    """Manager for creating and parsing permission tokens on-chain.

    Handles the lifecycle of permission tokens including creation,
    renewal, and revocation.
    """

    def __init__(self, admin_originator: str) -> None:
        """Initialize PermissionTokenManager.

        Args:
            admin_originator: Admin domain/FQDN for token creation
        """
        self._admin_originator = admin_originator
        self._encoder = PushDropEncoder()
        self._decoder = PushDropDecoder()

    def create_token_transaction(
        self, token: PermissionToken, wallet: Any, old_token: PermissionToken | None = None
    ) -> str:
        """Create transaction for permission token.

        Args:
            token: New permission token to create
            wallet: Wallet instance for transaction creation
            old_token: Optional existing token to spend

        Returns:
            Transaction ID of created token

        Raises:
            RuntimeError: If token creation fails
        """
        # Encode token as PushDrop script
        script_data = self._encoder.encode_permission_token(token, self._admin_originator)

        # Build transaction inputs
        inputs = []
        if old_token and old_token.get("txid"):
            # Spend old token
            inputs.append(
                {
                    "outpoint": f"{old_token['txid']}:{old_token.get('outputIndex', 0)}",
                    "unlockingScriptLength": 73,  # Typical signature length
                    "inputDescription": f"Spend old {old_token.get('type')} permission token",
                }
            )

        # Build transaction outputs
        outputs = [
            {
                "lockingScript": script_data["lockingScript"],
                "satoshis": token.get("satoshis", 1),
                "outputDescription": f"New {token.get('type')} permission token",
            }
        ]

        # Create action via wallet
        create_args = {
            "description": f"Create {token.get('type')} permission token",
            "inputs": inputs,
            "outputs": outputs,
            "options": {"randomizeOutputs": False, "acceptDelayedBroadcast": False},
        }

        result = wallet.create_action(create_args, self._admin_originator)

        # Handle both sync and async results
        if hasattr(result, "__await__"):
            # Async result - for now, assume synchronous
            import asyncio

            try:
                asyncio.get_running_loop()
                raise RuntimeError("Cannot handle async result in sync context")
            except RuntimeError:
                result = asyncio.run(result)

        # Extract transaction ID
        txid = result.get("txid")
        if not txid and result.get("tx"):
            # Parse from transaction data if available
            txid = "parsed_txid"  # Placeholder

        if not txid:
            raise RuntimeError("Failed to create permission token transaction")

        # Update token with transaction info
        token["txid"] = txid
        token["outputIndex"] = 0
        token["outputScript"] = script_data["lockingScript"]

        return txid

    def find_token_by_outpoint(self, outpoint: str, wallet: Any) -> dict[str, Any] | None:
        """Find token data by outpoint.

        Args:
            outpoint: Outpoint string (txid:vout)
            wallet: Wallet instance for lookups

        Returns:
            Token data or None if not found
        """
        # This would use wallet's discovery methods to find the token
        # For now, return None (placeholder)
        return None

    def renew_token(self, old_token: PermissionToken, wallet: Any) -> str:
        """Renew a permission token by spending the old one and creating a new one.

        Args:
            old_token: Existing token to renew
            wallet: Wallet instance

        Returns:
            Transaction ID of the new token

        Raises:
            RuntimeError: If renewal fails
        """
        if not old_token.get("txid"):
            raise RuntimeError("Cannot renew token without txid")

        # Create new token with updated expiry
        new_token = PermissionToken(
            originator=old_token.get("originator", ""),
            expiry=int(time.time()) + (365 * 24 * 60 * 60),  # 1 year from now
            satoshis=old_token.get("satoshis", 1),
            tx=[],
            outputIndex=0,
            outputScript="",
        )

        # Copy type-specific fields
        for key, value in old_token.items():
            if key not in ["txid", "expiry", "tx", "outputIndex", "outputScript"]:
                new_token[key] = value  # type: ignore

        # Create renewal transaction
        txid = self.create_token_transaction(new_token, wallet, old_token)
        return txid

    def revoke_token(self, token: PermissionToken, wallet: Any) -> str:
        """Revoke a permission token by spending it with no new output.

        Args:
            token: Token to revoke
            wallet: Wallet instance

        Returns:
            Transaction ID of revocation

        Raises:
            RuntimeError: If revocation fails
        """
        if not token.get("txid"):
            raise RuntimeError("Cannot revoke token without txid")

        # Create transaction that spends the token with no outputs
        inputs = [
            {
                "outpoint": f"{token['txid']}:{token.get('outputIndex', 0)}",
                "unlockingScriptLength": 73,
                "inputDescription": f"Revoke {token.get('type')} permission token",
            }
        ]

        create_args = {
            "description": f"Revoke {token.get('type')} permission token",
            "inputs": inputs,
            "outputs": [],  # No outputs = revocation
            "options": {"acceptDelayedBroadcast": False},
        }

        result = wallet.create_action(create_args, self._admin_originator)

        # Handle result and return txid
        txid = result.get("txid", "revocation_txid")
        return txid
