"""各機能モジュールを外部からインポート可能にするための __init__.py"""

from .address_management import display_wallet_info, get_wallet_address
from .key_management import demo_get_public_key, demo_sign_data
from .action_management import demo_create_action, demo_list_actions
from .certificate_management import demo_acquire_certificate, demo_list_certificates
from .identity_discovery import demo_discover_by_identity_key, demo_discover_by_attributes
from .config import get_key_deriver, get_network, print_network_info
from .crypto_operations import (
    demo_create_hmac,
    demo_verify_hmac,
    demo_verify_signature,
    demo_encrypt_decrypt,
)
from .key_linkage import (
    demo_reveal_counterparty_key_linkage,
    demo_reveal_specific_key_linkage,
)
from .advanced_management import (
    demo_list_outputs,
    demo_relinquish_output,
    demo_abort_action,
    demo_relinquish_certificate,
)
from .blockchain_info import (
    demo_get_height,
    demo_get_header_for_height,
    demo_wait_for_authentication,
)

__all__ = [
    # アドレス管理
    "display_wallet_info",
    "get_wallet_address",
    # 鍵管理
    "demo_get_public_key",
    "demo_sign_data",
    # アクション管理
    "demo_create_action",
    "demo_list_actions",
    "demo_abort_action",
    # 証明書管理
    "demo_acquire_certificate",
    "demo_list_certificates",
    "demo_relinquish_certificate",
    # ID 検索
    "demo_discover_by_identity_key",
    "demo_discover_by_attributes",
    # 設定
    "get_key_deriver",
    "get_network",
    "print_network_info",
    # 暗号化機能
    "demo_create_hmac",
    "demo_verify_hmac",
    "demo_verify_signature",
    "demo_encrypt_decrypt",
    # 鍵リンケージ
    "demo_reveal_counterparty_key_linkage",
    "demo_reveal_specific_key_linkage",
    # 高度な管理
    "demo_list_outputs",
    "demo_relinquish_output",
    # ブロックチェーン情報
    "demo_get_height",
    "demo_get_header_for_height",
    "demo_wait_for_authentication",
]
