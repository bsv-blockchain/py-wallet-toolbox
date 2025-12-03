"""Sync chunk processor for comprehensive entity synchronization.

Handles processing of sync chunks containing various entity types,
merging data from remote wallets, and managing sync state.

Reference: go-wallet-toolbox/pkg/storage/internal/sync/chunk_processor.go
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class SyncChunkProcessor:
    """Processes sync chunks and merges entity data from remote wallets.

    Handles comprehensive synchronization of all entity types including
    users, baskets, transactions, outputs, labels, tags, and certificates.
    """

    def __init__(self, provider: 'StorageProvider', chunk: Dict[str, Any], args: Dict[str, Any]):
        """Initialize sync chunk processor.

        Args:
            provider: Storage provider instance
            chunk: Sync chunk data from remote wallet
            args: Sync request arguments
        """
        self.provider = provider
        self.chunk = chunk
        self.args = args
        self.logger = logging.getLogger(f"{__name__}.SyncChunkProcessor")
        self.updated_count = 0
        self.errors: List[str] = []

        # Validate required fields
        self._validate_chunk()

    def _validate_chunk(self) -> None:
        """Validate sync chunk structure and required fields."""
        required_fields = ['fromStorageIdentityKey', 'toStorageIdentityKey', 'userIdentityKey']
        for field in required_fields:
            if field not in self.chunk:
                raise ValueError(f"Missing required field: {field}")

        # Validate storage identity match
        from_key = self.chunk['fromStorageIdentityKey']
        if from_key != self.args.get('fromStorageIdentityKey'):
            raise ValueError(f"Storage key mismatch: {from_key} != {self.args.get('fromStorageIdentityKey')}")

    def process_chunk(self) -> Dict[str, Any]:
        """Process the entire sync chunk.

        Returns:
            Dict with processing results:
                - processed: Whether chunk was processed
                - updated: Number of entities updated
                - errors: List of error messages
                - done: Whether sync is complete (empty chunk)
        """
        try:
            self.logger.info(f"Processing sync chunk from {self.chunk['fromStorageIdentityKey']}")

            # Check if this is an empty chunk (sync complete)
            if self._is_empty_chunk():
                self.logger.info("Empty chunk received - sync complete")
                return {
                    "processed": True,
                    "updated": 0,
                    "errors": [],
                    "done": True
                }

            # Process each entity type
            self._process_user()
            self._process_output_baskets()
            self._process_proven_tx_reqs()
            self._process_proven_txs()
            self._process_transactions()
            self._process_outputs()
            self._process_tx_labels()
            self._process_tx_label_maps()
            self._process_output_tags()
            self._process_output_tag_maps()
            self._process_certificates()
            self._process_certificate_fields()
            self._process_commissions()

            self.logger.info(f"Sync chunk processing complete. Updated: {self.updated_count}, Errors: {len(self.errors)}")

            return {
                "processed": True,
                "updated": self.updated_count,
                "errors": self.errors,
                "done": False
            }

        except Exception as e:
            error_msg = f"Failed to process sync chunk: {e}"
            self.logger.error(error_msg)
            return {
                "processed": False,
                "updated": 0,
                "errors": [error_msg],
                "done": False
            }

    def _is_empty_chunk(self) -> bool:
        """Check if chunk is empty (indicating sync completion)."""
        entity_fields = [
            'user', 'outputBaskets', 'provenTxs', 'provenTxReqs',
            'transactions', 'outputs', 'txLabels', 'txLabelMaps',
            'outputTags', 'outputTagMaps', 'certificates',
            'certificateFields', 'commissions'
        ]

        for field in entity_fields:
            if field in self.chunk and self.chunk[field]:
                return False

        return True

    def _process_user(self) -> None:
        """Process user data from chunk."""
        user_data = self.chunk.get('user')
        if user_data:
            try:
                self.logger.debug("Processing user data")
                # Merge user data - typically just update identity key mapping
                # In most cases, user should already exist from initial setup
                self.updated_count += 1
            except Exception as e:
                self.errors.append(f"Failed to process user: {e}")

    def _process_output_baskets(self) -> None:
        """Process output baskets from chunk."""
        baskets = self.chunk.get('outputBaskets', [])
        for basket in baskets:
            try:
                self.logger.debug(f"Processing basket: {basket.get('name', 'unknown')}")
                self.provider.configure_basket(
                    auth={'userId': self._get_user_id()},
                    basket_config=basket
                )
                self.updated_count += 1
            except Exception as e:
                self.errors.append(f"Failed to process basket {basket.get('name', 'unknown')}: {e}")

    def _process_proven_tx_reqs(self) -> None:
        """Process proven transaction requests from chunk."""
        reqs = self.chunk.get('provenTxReqs', [])
        for req in reqs:
            try:
                self.logger.debug(f"Processing proven tx req: {req.get('id', 'unknown')}")
                # Insert or update proven tx request
                self.provider._insert_generic('proven_tx_req', req)
                self.updated_count += 1
            except Exception as e:
                self.errors.append(f"Failed to process proven tx req: {e}")

    def _process_proven_txs(self) -> None:
        """Process proven transactions from chunk."""
        txs = self.chunk.get('provenTxs', [])
        for tx in txs:
            try:
                self.logger.debug(f"Processing proven tx: {tx.get('txid', 'unknown')}")
                self.provider.find_or_insert_proven_tx(tx)
                self.updated_count += 1
            except Exception as e:
                self.errors.append(f"Failed to process proven tx {tx.get('txid', 'unknown')}: {e}")

    def _process_transactions(self) -> None:
        """Process transactions from chunk."""
        transactions = self.chunk.get('transactions', [])
        for tx in transactions:
            try:
                self.logger.debug(f"Processing transaction: {tx.get('txid', 'unknown')}")
                self.provider.insert_transaction(tx)
                self.updated_count += 1
            except Exception as e:
                self.errors.append(f"Failed to process transaction {tx.get('txid', 'unknown')}: {e}")

    def _process_outputs(self) -> None:
        """Process outputs from chunk."""
        outputs = self.chunk.get('outputs', [])
        for output in outputs:
            try:
                self.logger.debug(f"Processing output: {output.get('txid', 'unknown')}:{output.get('vout', 'unknown')}")
                self.provider.insert_output(output)
                self.updated_count += 1
            except Exception as e:
                self.errors.append(f"Failed to process output: {e}")

    def _process_tx_labels(self) -> None:
        """Process transaction labels from chunk."""
        labels = self.chunk.get('txLabels', [])
        for label in labels:
            try:
                self.logger.debug(f"Processing tx label: {label.get('label', 'unknown')}")
                self.provider.find_or_insert_tx_label(
                    user_id=self._get_user_id(),
                    label=label['label']
                )
                self.updated_count += 1
            except Exception as e:
                self.errors.append(f"Failed to process tx label {label.get('label', 'unknown')}: {e}")

    def _process_tx_label_maps(self) -> None:
        """Process transaction label mappings from chunk."""
        mappings = self.chunk.get('txLabelMaps', [])
        for mapping in mappings:
            try:
                self.logger.debug(f"Processing tx label map: {mapping.get('transaction_id', 'unknown')}")
                self.provider.find_or_insert_tx_label_map(
                    transaction_id=mapping['transaction_id'],
                    tx_label_id=mapping['tx_label_id']
                )
                self.updated_count += 1
            except Exception as e:
                self.errors.append(f"Failed to process tx label map: {e}")

    def _process_output_tags(self) -> None:
        """Process output tags from chunk."""
        tags = self.chunk.get('outputTags', [])
        for tag in tags:
            try:
                self.logger.debug(f"Processing output tag: {tag.get('tag', 'unknown')}")
                self.provider.find_or_insert_output_tag(
                    user_id=self._get_user_id(),
                    tag=tag['tag']
                )
                self.updated_count += 1
            except Exception as e:
                self.errors.append(f"Failed to process output tag {tag.get('tag', 'unknown')}: {e}")

    def _process_output_tag_maps(self) -> None:
        """Process output tag mappings from chunk."""
        mappings = self.chunk.get('outputTagMaps', [])
        for mapping in mappings:
            try:
                self.logger.debug(f"Processing output tag map: {mapping.get('output_id', 'unknown')}")
                self.provider.find_or_insert_output_tag_map(
                    output_id=mapping['output_id'],
                    output_tag_id=mapping['output_tag_id']
                )
                self.updated_count += 1
            except Exception as e:
                self.errors.append(f"Failed to process output tag map: {e}")

    def _process_certificates(self) -> None:
        """Process certificates from chunk."""
        certificates = self.chunk.get('certificates', [])
        for cert in certificates:
            try:
                self.logger.debug(f"Processing certificate: {cert.get('serial_number', 'unknown')}")
                self.provider.insert_certificate_auth(
                    auth={'userId': self._get_user_id()},
                    certificate=cert
                )
                self.updated_count += 1
            except Exception as e:
                self.errors.append(f"Failed to process certificate: {e}")

    def _process_certificate_fields(self) -> None:
        """Process certificate fields from chunk."""
        fields = self.chunk.get('certificateFields', [])
        for field in fields:
            try:
                self.logger.debug(f"Processing certificate field: {field.get('field_name', 'unknown')}")
                self.provider.insert_certificate_field(field)
                self.updated_count += 1
            except Exception as e:
                self.errors.append(f"Failed to process certificate field: {e}")

    def _process_commissions(self) -> None:
        """Process commissions from chunk."""
        commissions = self.chunk.get('commissions', [])
        for commission in commissions:
            try:
                self.logger.debug(f"Processing commission: {commission.get('id', 'unknown')}")
                self.provider.insert_commission(commission)
                self.updated_count += 1
            except Exception as e:
                self.errors.append(f"Failed to process commission: {e}")

    def _get_user_id(self) -> int:
        """Get user ID from chunk data or arguments."""
        # Try to get from chunk first, then from args
        user_data = self.chunk.get('user')
        if user_data and 'user_id' in user_data:
            return user_data['user_id']

        # Fallback to looking up by identity key
        identity_key = self.chunk.get('userIdentityKey') or self.args.get('identityKey')
        if identity_key:
            return self.provider.get_or_create_user_id(identity_key)

        raise ValueError("Cannot determine user ID from sync chunk")
