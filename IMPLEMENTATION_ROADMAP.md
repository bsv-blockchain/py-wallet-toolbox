# WalletServices 実装ロードマップ

## 現状（v0.5.0）

### ✅ 実装済み

- `MockWalletServices`: テスト専用、固定値を返す

### ❌ 未実装

- 本番用の実装（WhatsOnChain API等に接続）

## 将来の実装例

### WhatsOnChain ベースの実装

```python
from bsv.chaintrackers.whatsonchain import WhatsOnChainTracker
from bsv_wallet_toolbox.services import WalletServices

class WhatsOnChainWalletServices(WalletServices, WhatsOnChainTracker):
    """Production-ready WalletServices using WhatsOnChain API.
    
    Extends py-sdk's WhatsOnChainTracker with additional wallet methods.
    """
    
    def __init__(self, network: str = "main", api_key: str | None = None):
        """Initialize services with WhatsOnChain API.
        
        Args:
            network: 'main' or 'test'
            api_key: Optional WhatsOnChain API key for higher rate limits
        """
        chain = "main" if network == "main" else "test"
        WalletServices.__init__(self, chain)
        WhatsOnChainTracker.__init__(self, network, api_key)
    
    async def get_height(self) -> int:
        """Get current blockchain height from WhatsOnChain.
        
        Returns:
            Current blockchain height
        """
        response = await self.http_client.fetch(
            f"{self.URL}/chain/info",
            {"method": "GET", "headers": self.get_headers()}
        )
        if response.ok:
            return response.json()["blocks"]
        else:
            raise RuntimeError(f"Failed to get height: {response.json()}")
    
    async def get_header_for_height(self, height: int) -> bytes:
        """Get block header at specified height from WhatsOnChain.
        
        Args:
            height: Block height
            
        Returns:
            Serialized block header bytes
        """
        if height < 0:
            raise ValueError(f"Height {height} must be a non-negative integer")
        
        response = await self.http_client.fetch(
            f"{self.URL}/block/{height}/header",
            {"method": "GET", "headers": self.get_headers()}
        )
        if response.ok:
            # WhatsOnChain returns hex string, convert to bytes
            header_hex = response.json()["data"]
            return bytes.fromhex(header_hex)
        else:
            raise RuntimeError(f"Failed to get header for height {height}")
```

### 使用例（将来）

```python
from bsv_wallet_toolbox import Wallet
from bsv_wallet_toolbox.services import WhatsOnChainWalletServices

# 本番環境: WhatsOnChain API に接続
services = WhatsOnChainWalletServices(
    network="main",
    api_key="your-api-key-here"  # オプション
)

# Wallet インスタンス作成
wallet = Wallet(chain="main", services=services)

# 実際のブロックチェーンから最新の高さを取得
result = await wallet.get_height({})
print(f"Current blockchain height: {result['height']}")
# Output: Current blockchain height: 876543 (実際の最新高さ)
```

### テスト環境での使い分け

```python
import os

# 環境変数で切り替え
if os.getenv("ENV") == "test":
    # テスト: Mock を使用（高速・安定）
    from bsv_wallet_toolbox.services import MockWalletServices
    services = MockWalletServices(height=850000)
else:
    # 本番: 実際の API に接続
    from bsv_wallet_toolbox.services import WhatsOnChainWalletServices
    services = WhatsOnChainWalletServices(
        network="main",
        api_key=os.getenv("WHATSONCHAIN_API_KEY")
    )

wallet = Wallet(chain="main", services=services)
```

## 実装優先度

1. **Phase 1 (現在)**: MockWalletServices のみ（テスト用）
2. **Phase 2 (Level 2 完了後)**: WhatsOnChainWalletServices 実装
3. **Phase 3 (将来)**: 他のプロバイダ対応（ARC、自前ノード等）

## 参考

- py-sdk WhatsOnChainTracker: `sdk/py-sdk/bsv/chaintrackers/whatsonchain.py`
- TypeScript Services: `toolbox/ts-wallet-toolbox/src/services/Services.ts`

