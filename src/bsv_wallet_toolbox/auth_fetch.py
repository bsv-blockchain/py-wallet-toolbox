"""AuthFetch - Authenticated HTTP client for BSV wallet operations.

Provides BRC-104 compliant authenticated HTTP requests using wallet-based authentication.
This module wraps py-sdk's AuthFetch implementation.

Reference:
  - py-sdk/bsv/auth/clients/auth_fetch.py
  - wallet-toolbox/src/storage/remoting/StorageClient.ts
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

# Re-export from py-sdk for full BRC-104 authentication
from bsv.auth.clients.auth_fetch import (
    AuthFetch as _AuthFetch,
    AuthPeer,
    SimplifiedFetchRequestOptions,
    p2pkh_locking_script_from_pubkey,
)
from bsv.auth.session_manager import DefaultSessionManager
from bsv.auth.requested_certificate_set import RequestedCertificateSet
from bsv.keys import PublicKey

logger = logging.getLogger(__name__)


class WalletAdapter:
    """Adapter to convert py-wallet-toolbox Wallet to py-sdk compatible interface.
    
    py-sdk's Peer expects wallet methods to return objects with specific attributes,
    while py-wallet-toolbox's Wallet returns dictionaries.
    
    This adapter converts:
    - get_public_key: dict -> object with public_key attribute
    - create_signature: dict -> object with signature attribute
    """
    
    def __init__(self, wallet: Any):
        self._wallet = wallet
    
    def get_public_key(self, args: Dict[str, Any], originator: str = "") -> Any:
        """Convert dict response to object with public_key attribute."""
        result = self._wallet.get_public_key(args, originator)
        
        if isinstance(result, dict):
            pub_key_hex = result.get('publicKey') or result.get('public_key')
            if pub_key_hex:
                # Create an object with the expected attributes
                class PublicKeyResult:
                    def __init__(self, hex_key: str):
                        self.publicKey = hex_key
                        self.public_key = PublicKey(hex_key)
                        self.hex = hex_key
                
                return PublicKeyResult(pub_key_hex)
        
        return result
    
    def create_signature(self, args: Dict[str, Any], originator: str = "") -> Any:
        """Convert dict response to object with signature attribute.
        
        Also transforms py-sdk's encryption_args format to py-wallet-toolbox's flat format.
        """
        # Transform encryption_args to flat format
        enc_args = args.get('encryption_args', {})
        if enc_args:
            # Extract protocol_id and convert to protocolID format
            protocol_id = enc_args.get('protocol_id', {})
            if isinstance(protocol_id, dict):
                security_level = protocol_id.get('securityLevel', 2)
                protocol = protocol_id.get('protocol', 'auth')
                protocol_id_list = [security_level, protocol]
            else:
                protocol_id_list = protocol_id
            
            # Extract counterparty
            counterparty_arg = enc_args.get('counterparty')
            counterparty_hex = None
            if isinstance(counterparty_arg, dict):
                cp_value = counterparty_arg.get('counterparty')
                if cp_value:
                    if hasattr(cp_value, 'hex'):
                        counterparty_hex = cp_value.hex()
                    elif isinstance(cp_value, str):
                        counterparty_hex = cp_value
            elif counterparty_arg:
                if hasattr(counterparty_arg, 'hex'):
                    counterparty_hex = counterparty_arg.hex()
                else:
                    counterparty_hex = str(counterparty_arg)
            
            # Build flat args for py-wallet-toolbox
            args = {
                'protocolID': protocol_id_list,
                'keyID': enc_args.get('key_id', '1'),
                'counterparty': counterparty_hex,
                'data': args.get('data'),
            }
        
        result = self._wallet.create_signature(args, originator)
        
        if isinstance(result, dict):
            signature = result.get('signature')
            if signature:
                class SignatureResult:
                    def __init__(self, sig: bytes):
                        self.signature = sig
                
                return SignatureResult(signature)
        
        return result
    
    def create_action(self, args: Dict[str, Any], originator: str = "") -> Any:
        """Pass through to wallet's create_action."""
        return self._wallet.create_action(args, originator)
    
    def create_hmac(self, args: Dict[str, Any], originator: str = "") -> Any:
        """Convert encryption_args format for create_hmac.
        
        py-sdk uses:
            encryption_args.protocol_id = {securityLevel: 1, protocol: 'server hmac'}
            encryption_args.key_id = string
            encryption_args.counterparty = {type: 1}
        
        py-wallet-toolbox expects:
            protocolID = [securityLevel, protocol]
            keyID = string
            counterparty = 'anyone' or hex_string
        """
        enc_args = args.get('encryption_args', {})
        data = args.get('data')
        
        if enc_args:
            # Extract protocol_id
            protocol_id = enc_args.get('protocol_id', {})
            if isinstance(protocol_id, dict):
                security_level = protocol_id.get('securityLevel', 1)
                protocol = protocol_id.get('protocol', 'server hmac')
                protocol_id_list = [security_level, protocol]
            else:
                protocol_id_list = protocol_id
            
            # Extract counterparty - for create_nonce it's {type: 1} which means ANYONE
            counterparty_arg = enc_args.get('counterparty')
            if isinstance(counterparty_arg, dict):
                cp_type = counterparty_arg.get('type', 1)
                if cp_type == 1:  # ANYONE
                    counterparty = 'anyone'
                else:
                    counterparty = counterparty_arg.get('counterparty')
            else:
                counterparty = counterparty_arg
            
            # Build flat args - convert bytes to list for py-wallet-toolbox
            args = {
                'protocolID': protocol_id_list,
                'keyID': enc_args.get('key_id', ''),
                'counterparty': counterparty,
                'data': list(data) if isinstance(data, bytes) else data,
            }
        
        result = self._wallet.create_hmac(args, originator)
        
        # Convert hmac list back to bytes for py-sdk compatibility
        if isinstance(result, dict) and 'hmac' in result:
            hmac_value = result['hmac']
            if isinstance(hmac_value, list):
                result['hmac'] = bytes(hmac_value)
        
        return result
    
    def verify_hmac(self, args: Dict[str, Any], originator: str = "") -> Any:
        """Convert encryption_args format for verify_hmac."""
        enc_args = args.get('encryption_args', {})
        data = args.get('data')
        hmac_value = args.get('hmac')
        
        if enc_args:
            protocol_id = enc_args.get('protocol_id', {})
            if isinstance(protocol_id, dict):
                security_level = protocol_id.get('securityLevel', 1)
                protocol = protocol_id.get('protocol', 'server hmac')
                protocol_id_list = [security_level, protocol]
            else:
                protocol_id_list = protocol_id
            
            counterparty_arg = enc_args.get('counterparty')
            if isinstance(counterparty_arg, dict):
                cp_type = counterparty_arg.get('type', 1)
                if cp_type == 1:
                    counterparty = 'anyone'
                else:
                    counterparty = counterparty_arg.get('counterparty')
            else:
                counterparty = counterparty_arg
            
            # Convert hmac bytes to list if needed
            if isinstance(hmac_value, bytes):
                hmac_value = list(hmac_value)
            
            args = {
                'protocolID': protocol_id_list,
                'keyID': enc_args.get('key_id', ''),
                'counterparty': counterparty,
                'data': list(data) if isinstance(data, bytes) else data,
                'hmac': hmac_value,
            }
        
        result = self._wallet.verify_hmac(args, originator)
        return result
    
    def verify_signature(self, args: Dict[str, Any], originator: str = "") -> Any:
        """Convert encryption_args format for verify_signature.
        
        py-sdk uses:
            encryption_args.protocol_id = {securityLevel: 2, protocol: 'auth'}
            encryption_args.key_id = 'nonce1 nonce2'
            encryption_args.counterparty = {type: 3, counterparty: PublicKey}
        
        py-wallet-toolbox expects:
            protocolID = [securityLevel, protocol]
            keyID = 'nonce1 nonce2'
            counterparty = hex_string
        """
        enc_args = args.get('encryption_args', {})
        data = args.get('data')
        signature = args.get('signature')
        
        if enc_args:
            protocol_id = enc_args.get('protocol_id', {})
            if isinstance(protocol_id, dict):
                security_level = protocol_id.get('securityLevel', 2)
                protocol = protocol_id.get('protocol', 'auth')
                protocol_id_list = [security_level, protocol]
            else:
                protocol_id_list = protocol_id
            
            counterparty_arg = enc_args.get('counterparty')
            counterparty_hex = None
            if isinstance(counterparty_arg, dict):
                cp_value = counterparty_arg.get('counterparty')
                if cp_value:
                    if hasattr(cp_value, 'hex'):
                        counterparty_hex = cp_value.hex()
                    elif isinstance(cp_value, str):
                        counterparty_hex = cp_value
            elif counterparty_arg:
                if hasattr(counterparty_arg, 'hex'):
                    counterparty_hex = counterparty_arg.hex()
                else:
                    counterparty_hex = str(counterparty_arg)
            
            # Convert signature to list if needed
            if isinstance(signature, bytes):
                signature = list(signature)
            
            args = {
                'protocolID': protocol_id_list,
                'keyID': enc_args.get('key_id', '1'),
                'counterparty': counterparty_hex,
                'data': list(data) if isinstance(data, bytes) else data,
                'signature': signature,
            }
        
        result = self._wallet.verify_signature(args, originator)
        
        # Convert result to object with valid attribute
        if isinstance(result, dict):
            class VerifyResult:
                def __init__(self, valid: bool):
                    self.valid = valid
            return VerifyResult(result.get('valid', False))
        
        return result
    
    def __getattr__(self, name: str) -> Any:
        """Forward any other attribute access to the underlying wallet."""
        return getattr(self._wallet, name)


class AuthFetch:
    """Authenticated HTTP client using py-sdk BRC-104 implementation.

    This class wraps py-sdk's AuthFetch to provide authenticated HTTP requests
    for BSV wallet operations, following the same pattern as TypeScript StorageClient.

    Reference: wallet-toolbox/src/storage/remoting/StorageClient.ts

    Usage:
        >>> from bsv_wallet_toolbox import AuthFetch, Wallet
        >>> wallet = Wallet(...)
        >>> auth_client = AuthFetch(wallet)
        >>> response = auth_client.fetch("https://api.example.com/data", options)
    """

    def __init__(
        self,
        wallet: Any,
        requested_certificates: Optional[RequestedCertificateSet] = None,
        session_manager: Optional[DefaultSessionManager] = None,
    ):
        """Initialize AuthFetch.

        Args:
            wallet: Wallet instance implementing BRC-100 WalletInterface.
                    Must have get_public_key(), create_signature(), and create_action() methods.
            requested_certificates: Optional certificate requirements for mutual auth.
            session_manager: Optional session manager for auth sessions (defaults to DefaultSessionManager).
        """
        # Wrap wallet in adapter to convert response formats
        adapted_wallet = WalletAdapter(wallet)
        
        self._impl = _AuthFetch(
            wallet=adapted_wallet,
            requested_certs=requested_certificates,
            session_manager=session_manager,
        )

    async def fetch(
        self,
        url: str,
        config: Optional[SimplifiedFetchRequestOptions] = None,
    ):
        """Make authenticated HTTP request.

        Handles BRC-104 mutual authentication and 402 Payment Required responses
        automatically when the wallet supports create_action().

        Args:
            url: Request URL
            config: Request options (method, headers, body)

        Returns:
            requests.Response object

        Raises:
            Exception: On request failure or authentication error
        """
        import logging
        logger = logging.getLogger(__name__)

        logger.debug(f"AuthFetch.fetch called: url={url}, method={config.method if config else 'GET'}")

        try:
            response = await self._impl.fetch(url, config)
            logger.debug(f"AuthFetch.fetch succeeded: status={response.status_code}")
            return response
        except Exception as e:
            logger.error(f"AuthFetch.fetch failed: {e}")
            raise

    def send_certificate_request(
        self,
        base_url: str,
        certificates_to_request: Any,
    ):
        """Request certificates from a peer.

        Args:
            base_url: Base URL of the peer
            certificates_to_request: Certificate requirements

        Returns:
            List of received certificates
        """
        return self._impl.send_certificate_request(base_url, certificates_to_request)

    def consume_received_certificates(self):
        """Consume and return certificates received during fetch operations.

        Returns:
            List of VerifiableCertificate objects received since last call
        """
        return self._impl.consume_received_certificates()

    @property
    def certificates_received(self):
        """Access list of received certificates."""
        return self._impl.certificates_received

    @property
    def peers(self):
        """Access peer connections."""
        return self._impl.peers


# Re-export for convenience
__all__ = [
    "AuthFetch",
    "AuthPeer",
    "SimplifiedFetchRequestOptions",
    "RequestedCertificateSet",
    "DefaultSessionManager",
    "p2pkh_locking_script_from_pubkey",
]
