#!/usr/bin/env python3
"""Sync local wallet database to remote storage server.

This script synchronizes data from a local SQLite wallet database
to a remote storage server using the WalletStorageManager.syncToWriter.

Usage:
    1. Start the storage server: python storage_server.py
    2. Run this script: python sync_local_to_remote.py

Reference:
    wallet-toolbox/src/storage/WalletStorageManager.ts (syncToWriter)
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import requests

from bsv_wallet_toolbox.storage.provider import StorageProvider
from bsv_wallet_toolbox.storage.db import create_sqlite_engine
from bsv_wallet_toolbox.storage.wallet_storage_manager import (
    WalletStorageManager,
    AuthId,
)

from internal import show
from internal.setup import load_config, normalize_chain


# Configuration
LOCAL_DB = "wallet.db"
# REMOTE_URL will be loaded from config file


class RemoteStorageClient:
    """Simple remote storage client that implements WalletStorageProvider protocol.
    
    This allows the WalletStorageManager to sync to a remote JSON-RPC server.
    """
    
    def __init__(self, endpoint_url: str, identity_key: str):
        self.endpoint_url = endpoint_url
        self.identity_key = identity_key
        self._settings = None
        self._user = None
        
    def _rpc_call(self, method: str, params: list) -> dict:
        """Make a JSON-RPC call to the remote server."""
        request_body = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1,
        }
        
        response = requests.post(
            self.endpoint_url,
            json=request_body,
            headers={"Content-Type": "application/json"},
            timeout=60,
        )
        response.raise_for_status()
        
        data = response.json()
        if "error" in data and data["error"]:
            raise RuntimeError(f"RPC Error: {data['error']}")
        
        return data.get("result")
    
    def is_storage_provider(self) -> bool:
        return True
    
    def make_available(self) -> dict:
        """Make storage available and return settings."""
        if not self._settings:
            self._settings = {
                "storageIdentityKey": self.identity_key,
                "storageName": f"remote:{self.endpoint_url}",
            }
        return self._settings
    
    def get_settings(self) -> dict:
        return self.make_available()
    
    def find_or_insert_user(self, identity_key: str) -> dict:
        """Find or insert user."""
        result = self._rpc_call("findOrInsertUser", [identity_key])
        self._user = result.get("user", {})
        return result
    
    def get_sync_chunk(self, args: dict) -> dict:
        """Get sync chunk from remote (for sync_from_reader)."""
        return self._rpc_call("getSyncChunk", [args])
    
    def process_sync_chunk(self, args: dict, chunk: dict) -> dict:
        """Process sync chunk on remote (for sync_to_writer)."""
        return self._rpc_call("processSyncChunk", [args, chunk])
    
    def set_services(self, services) -> None:
        """Set services (no-op for remote)."""
        pass
    
    def find_or_insert_sync_state_auth(
        self, auth: dict, storage_identity_key: str, storage_name: str
    ) -> dict:
        """Find or insert sync state."""
        try:
            return self._rpc_call("findOrInsertSyncStateAuth", [auth, storage_identity_key, storage_name])
        except Exception:
            # Return empty sync state if not implemented
            return {"syncState": {}}
    
    def find_or_insert_output_basket(self, user_id: int, name: str) -> dict:
        """Find or insert output basket."""
        return self._rpc_call("findOrInsertOutputBasket", [user_id, name])
    
    def find_or_insert_tx_label(self, user_id: int, label: str) -> dict:
        """Find or insert tx label."""
        return self._rpc_call("findOrInsertTxLabel", [user_id, label])
    
    def list_outputs(self, auth: dict, args: dict) -> dict:
        """List outputs."""
        return self._rpc_call("listOutputs", [auth, args])
    
    def list_actions(self, auth: dict, args: dict) -> dict:
        """List actions."""
        return self._rpc_call("listActions", [auth, args])


def progress_log(msg: str) -> str:
    """Progress logging function."""
    print(f"  {msg}", end="")
    return msg


def main():
    show.process_start("Sync Local to Remote Storage (Using WalletStorageManager)")
    
    # Load config to get identity key and server URL
    config = load_config()
    identity_key = config.alice.identity_key
    remote_url = config.server_url
    
    if not remote_url:
        show.error("No server_url configured in examples-config.yaml")
        print("\nPlease set server_url in examples-config.yaml to use remote storage.")
        return
    
    show.info("Local database", LOCAL_DB)
    show.info("Remote server", remote_url)
    show.info("Identity key", identity_key)
    
    # Check if local database exists
    if not Path(LOCAL_DB).exists():
        show.error(f"Local database not found: {LOCAL_DB}")
        print("\nPlease run some wallet examples first to create the local database.")
        return
    
    # Create local storage provider
    show.step("Alice", "Connecting to local storage")
    engine = create_sqlite_engine(LOCAL_DB)
    chain = normalize_chain(config.network)
    
    local_storage = StorageProvider(
        engine=engine,
        chain=chain,
        storage_identity_key=identity_key,
    )
    
    # Get user from local
    local_user_id = local_storage.get_or_create_user_id(identity_key)
    show.info("Local user ID", str(local_user_id))
    
    # Create remote storage client
    show.step("Alice", "Connecting to remote storage")
    remote_storage = RemoteStorageClient(
        endpoint_url=remote_url,
        identity_key=identity_key,
    )
    
    # Setup remote user
    user_result = remote_storage.find_or_insert_user(identity_key)
    # TS-compatible format: { user: { userId: ... }, isNew: boolean }
    user = user_result.get("user", {})
    remote_user_id = user.get("userId", user.get("user_id", 0))
    show.info("Remote user ID", str(remote_user_id))
    
    # Setup default basket and label on remote with correct user_id
    if remote_user_id > 0:
        try:
            remote_storage.find_or_insert_output_basket(remote_user_id, "default")
            show.info("Created basket", f"default (user_id={remote_user_id})")
        except Exception as e:
            show.info("Basket exists or error", str(e)[:50])
        
        try:
            remote_storage.find_or_insert_tx_label(remote_user_id, "default")
            show.info("Created label", f"default (user_id={remote_user_id})")
        except Exception as e:
            show.info("Label exists or error", str(e)[:50])
    else:
        show.error("Failed to get remote user ID")
    
    # Create WalletStorageManager with local as active
    show.step("Alice", "Creating WalletStorageManager")
    manager = WalletStorageManager(
        identity_key=identity_key,
        active=local_storage,
        backups=[remote_storage],  # Remote as backup
    )
    
    # Make available and show stores
    manager.make_available()
    stores = manager.get_stores()
    show.info("Managed stores", str(len(stores)))
    for store in stores:
        status = "ACTIVE" if store["isActive"] else "BACKUP"
        show.info(f"  {status}", f"{store['storageName']} ({store['storageClass']})")
    
    # Run sync using WalletStorageManager
    show.separator()
    print("\n" + "=" * 60)
    print("STARTING SYNC TO REMOTE (Using WalletStorageManager)")
    print("=" * 60 + "\n")
    
    # Create auth ID
    auth = AuthId(
        identity_key=identity_key,
        user_id=local_user_id,
        is_active=True,
    )
    
    # Sync to remote writer
    show.step("Alice", "Running sync_to_writer")
    result = manager.sync_to_writer(
        auth=auth,
        writer=remote_storage,
        prog_log=progress_log,
    )
    
    show.separator()
    show.info("Total inserts", str(result.inserts))
    show.info("Total updates", str(result.updates))
    
    show.process_complete(f"Sync Local to Remote (inserts: {result.inserts}, updates: {result.updates})")
    
    # Verify sync by checking remote
    show.step("Alice", "Verifying remote storage")
    try:
        auth_dict = {"userId": remote_user_id}
        outputs_result = remote_storage.list_outputs(auth_dict, {"basket": "default", "limit": 100})
        show.info("Remote outputs", str(outputs_result.get("totalOutputs", 0)))
        
        actions_result = remote_storage.list_actions(auth_dict, {"limit": 100})
        show.info("Remote actions", str(actions_result.get("totalActions", 0)))
        
    except Exception as e:
        show.error(f"Verification failed: {e}")
    
    print("\n" + "=" * 60)
    print("SYNC LOG")
    print("=" * 60)
    print(result.log)
    
    # Also demonstrate sync_from_reader (remote -> local)
    print("\n" + "=" * 60)
    print("DEMONSTRATING sync_from_reader (would pull remote -> local)")
    print("=" * 60 + "\n")
    
    show.step("Alice", "Running sync_from_reader (remote -> local)")
    try:
        result_from = manager.sync_from_reader(
            identity_key=identity_key,
            reader=remote_storage,
            prog_log=progress_log,
        )
        show.info("From remote inserts", str(result_from.inserts))
        show.info("From remote updates", str(result_from.updates))
    except Exception as e:
        show.info("sync_from_reader", f"Skipped or error: {e}")
    
    # Demonstrate update_backups
    print("\n" + "=" * 60)
    print("DEMONSTRATING update_backups (sync to all backups)")
    print("=" * 60 + "\n")
    
    show.step("Alice", "Running update_backups")
    try:
        backup_log = manager.update_backups(prog_log=progress_log)
        print(backup_log)
    except Exception as e:
        show.info("update_backups", f"Error: {e}")


if __name__ == "__main__":
    main()
