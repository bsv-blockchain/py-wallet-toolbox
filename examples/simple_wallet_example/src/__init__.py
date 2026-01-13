"""Re-export helper modules so wallet_demo.py stays tidy."""

from .action_management import demo_create_action, demo_list_actions
from .address_management import display_wallet_info, get_wallet_address
from .advanced_management import (
    demo_abort_action,
    demo_list_outputs,
    demo_relinquish_certificate,
    demo_relinquish_output,
)
from .blockchain_info import (
    demo_get_header_for_height,
    demo_get_height,
    demo_wait_for_authentication,
)
from .certificate_management import demo_acquire_certificate, demo_list_certificates
from .config import get_key_deriver, get_network, get_storage_provider, print_network_info
from .crypto_operations import (
    demo_create_hmac,
    demo_encrypt_decrypt,
    demo_verify_hmac,
    demo_verify_signature,
)
from .identity_discovery import demo_discover_by_attributes, demo_discover_by_identity_key
from .key_linkage import (
    demo_reveal_counterparty_key_linkage,
    demo_reveal_specific_key_linkage,
)
from .key_management import demo_get_public_key, demo_sign_data
from .transaction_management import demo_internalize_action

__all__ = [
    # address & wallet info
    "display_wallet_info",
    "get_wallet_address",
    # key management
    "demo_get_public_key",
    "demo_sign_data",
    # actions
    "demo_create_action",
    "demo_list_actions",
    "demo_abort_action",
    # certificates
    "demo_acquire_certificate",
    "demo_list_certificates",
    "demo_relinquish_certificate",
    # identity discovery
    "demo_discover_by_identity_key",
    "demo_discover_by_attributes",
    # configuration
    "get_key_deriver",
    "get_network",
    "get_storage_provider",
    "print_network_info",
    # crypto primitives
    "demo_create_hmac",
    "demo_verify_hmac",
    "demo_verify_signature",
    "demo_encrypt_decrypt",
    # key linkage
    "demo_reveal_counterparty_key_linkage",
    "demo_reveal_specific_key_linkage",
    # outputs and storage helpers
    "demo_list_outputs",
    "demo_relinquish_output",
    "demo_relinquish_certificate",
    "demo_internalize_action",
    # blockchain info
    "demo_get_height",
    "demo_get_header_for_height",
    "demo_wait_for_authentication",
]
