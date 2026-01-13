"""SQLAlchemy implementation of Chaintracks storage queries.

Provides SQLAlchemy-based implementation of the StorageQueries interface
for live blockchain header operations.

Reference: go-wallet-toolbox/pkg/services/chaintracks/gormstorage/storage_queries.go
"""

import logging

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from ...chaintracks_storage import LiveHeadersModel
from ..models import HeightRange, LiveBlockHeader

logger = logging.getLogger(__name__)


class SQLAlchemyStorageQueries:
    """SQLAlchemy implementation of StorageQueries interface.

    Provides transactional database operations for live blockchain headers.
    """

    def __init__(self, session: Session):
        """Initialize with SQLAlchemy session.

        Args:
            session: SQLAlchemy session for database operations
        """
        self.session = session
        self._transaction_session: Session | None = None

    def _get_session(self) -> Session:
        """Get the current session (transactional if active)."""
        return self._transaction_session or self.session

    def begin(self) -> None:
        """Begin a database transaction."""
        if self._transaction_session is not None:
            raise RuntimeError("Transaction already started")
        self._transaction_session = self.session.begin()

    def rollback(self) -> Exception | None:
        """Rollback the current transaction.

        Returns:
            Exception if rollback fails, None otherwise
        """
        if self._transaction_session is None:
            raise RuntimeError("No transaction to rollback")

        try:
            self._transaction_session.rollback()
            return None
        except Exception as e:
            logger.error(f"Failed to rollback transaction: {e}")
            return e
        finally:
            self._transaction_session = None

    def commit(self) -> Exception | None:
        """Commit the current transaction.

        Returns:
            Exception if commit fails, None otherwise
        """
        if self._transaction_session is None:
            raise RuntimeError("No transaction to commit")

        try:
            self._transaction_session.commit()
            return None
        except Exception as e:
            logger.error(f"Failed to commit transaction: {e}")
            return e
        finally:
            self._transaction_session = None

    def live_header_exists(self, hash_str: str) -> tuple[bool, Exception | None]:
        """Check if a live header exists by hash.

        Args:
            hash_str: Block hash

        Returns:
            Tuple of (exists, error)
        """
        try:
            session = self._get_session()
            count = (
                session.query(func.count(LiveHeadersModel.header_id)).filter(LiveHeadersModel.hash == hash_str).scalar()
            )
            return count > 0, None
        except Exception as e:
            logger.error(f"Failed to check live header existence: {e}")
            return False, e

    def get_live_header_by_hash(self, hash_str: str) -> tuple[LiveBlockHeader | None, Exception | None]:
        """Get live header by hash.

        Args:
            hash_str: Block hash

        Returns:
            Tuple of (header, error)
        """
        try:
            session = self._get_session()
            model = session.query(LiveHeadersModel).filter(LiveHeadersModel.hash == hash_str).first()

            if model is None:
                return None, None

            return self._model_to_live_header(model), None
        except Exception as e:
            logger.error(f"Failed to get live header by hash: {e}")
            return None, e

    def get_active_tip_live_header(self) -> tuple[LiveBlockHeader | None, Exception | None]:
        """Get the active chain tip live header.

        Returns:
            Tuple of (header, error)
        """
        try:
            session = self._get_session()
            model = (
                session.query(LiveHeadersModel)
                .filter(and_(LiveHeadersModel.is_active.is_(True), LiveHeadersModel.is_chain_tip.is_(True)))
                .first()
            )

            if model is None:
                return None, None

            return self._model_to_live_header(model), None
        except Exception as e:
            logger.error(f"Failed to get active tip live header: {e}")
            return None, e

    def set_chain_tip_by_id(self, header_id: int, is_chain_tip: bool) -> Exception | None:
        """Set chain tip status for header by ID.

        Args:
            header_id: Header database ID
            is_chain_tip: Whether this is the chain tip

        Returns:
            Exception if operation fails
        """
        try:
            session = self._get_session()
            session.query(LiveHeadersModel).filter(LiveHeadersModel.header_id == header_id).update(
                {"isChainTip": is_chain_tip}
            )
            return None
        except Exception as e:
            logger.error(f"Failed to set chain tip by ID: {e}")
            return e

    def set_active_by_id(self, header_id: int, is_active: bool) -> Exception | None:
        """Set active status for header by ID.

        Args:
            header_id: Header database ID
            is_active: Whether this header is on active chain

        Returns:
            Exception if operation fails
        """
        try:
            session = self._get_session()
            session.query(LiveHeadersModel).filter(LiveHeadersModel.header_id == header_id).update(
                {"isActive": is_active}
            )
            return None
        except Exception as e:
            logger.error(f"Failed to set active by ID: {e}")
            return e

    def insert_new_live_header(self, header: LiveBlockHeader) -> Exception | None:
        """Insert a new live header.

        Args:
            header: LiveBlockHeader to insert

        Returns:
            Exception if insertion fails
        """
        try:
            session = self._get_session()
            model = self._live_header_to_model(header)
            session.add(model)
            session.flush()  # Get the ID back
            header.header_id = model.header_id
            return None
        except Exception as e:
            logger.error(f"Failed to insert new live header: {e}")
            return e

    def count_live_headers(self) -> tuple[int, Exception | None]:
        """Count total live headers.

        Returns:
            Tuple of (count, error)
        """
        try:
            session = self._get_session()
            count = session.query(func.count(LiveHeadersModel.header_id)).scalar()
            return int(count), None
        except Exception as e:
            logger.error(f"Failed to count live headers: {e}")
            return 0, e

    def get_live_header_by_height(self, height: int) -> tuple[LiveBlockHeader | None, Exception | None]:
        """Get live header by height.

        Args:
            height: Block height

        Returns:
            Tuple of (header, error)
        """
        try:
            session = self._get_session()
            model = (
                session.query(LiveHeadersModel)
                .filter(and_(LiveHeadersModel.height == height, LiveHeadersModel.is_active.is_(True)))
                .first()
            )

            if model is None:
                return None, None

            return self._model_to_live_header(model), None
        except Exception as e:
            logger.error(f"Failed to get live header by height: {e}")
            return None, e

    def find_live_height_range(self) -> tuple[HeightRange, Exception | None]:
        """Find the height range covered by live headers.

        Returns:
            Tuple of (height_range, error)
        """
        try:
            session = self._get_session()

            # Get min and max heights
            result = session.query(func.min(LiveHeadersModel.height), func.max(LiveHeadersModel.height)).first()

            min_height, max_height = result

            if min_height is None or max_height is None:
                return HeightRange.new_empty_height_range(), None

            return HeightRange.new_height_range(min_height, max_height), None
        except Exception as e:
            logger.error(f"Failed to find live height range: {e}")
            return HeightRange.new_empty_height_range(), e

    def find_headers_for_height_less_than_or_equal_sorted(
        self, height: int, limit: int
    ) -> tuple[list[LiveBlockHeader], Exception | None]:
        """Find headers with height <= specified height, sorted.

        Args:
            height: Maximum height
            limit: Maximum number of headers to return

        Returns:
            Tuple of (headers_list, error)
        """
        try:
            session = self._get_session()
            models = (
                session.query(LiveHeadersModel)
                .filter(LiveHeadersModel.height <= height)
                .order_by(LiveHeadersModel.height.asc())
                .limit(limit)
                .all()
            )

            headers = [self._model_to_live_header(model) for model in models]
            return headers, None
        except Exception as e:
            logger.error(f"Failed to find headers for height less than or equal: {e}")
            return [], e

    def delete_live_headers_by_ids(self, ids: list[int]) -> Exception | None:
        """Delete live headers by their IDs.

        Args:
            ids: List of header IDs to delete

        Returns:
            Exception if deletion fails
        """
        try:
            session = self._get_session()
            session.query(LiveHeadersModel).filter(LiveHeadersModel.header_id.in_(ids)).delete()
            return None
        except Exception as e:
            logger.error(f"Failed to delete live headers by IDs: {e}")
            return e

    def _model_to_live_header(self, model: LiveHeadersModel) -> LiveBlockHeader:
        """Convert database model to LiveBlockHeader.

        Args:
            model: Database model

        Returns:
            LiveBlockHeader instance
        """
        # Convert boolean ints back to booleans
        is_active = bool(model.is_active) if model.is_active is not None else False
        is_chain_tip = bool(model.is_chain_tip) if model.is_chain_tip is not None else False

        # Create block header dict
        block_header = {
            "version": model.version or 1,
            "previousHash": model.previous_hash or "",
            "merkleRoot": model.merkle_root or "",
            "time": model.time or 0,
            "bits": model.bits or 0,
            "nonce": model.nonce or 0,
            "height": model.height or 0,
            "hash": model.hash or "",
        }

        return LiveBlockHeader(
            chain_block_header=block_header,
            chain_work=model.chain_work or "",
            is_chain_tip=is_chain_tip,
            is_active=is_active,
            header_id=model.header_id,
            previous_header_id=model.previous_header_id,
        )

    def _live_header_to_model(self, header: LiveBlockHeader) -> LiveHeadersModel:
        """Convert LiveBlockHeader to database model.

        Args:
            header: LiveBlockHeader instance

        Returns:
            Database model instance
        """
        return LiveHeadersModel(
            previous_header_id=header.previous_header_id,
            previous_hash=header.previous_hash,
            height=header.height,
            is_active=header.is_active,
            is_chain_tip=header.is_chain_tip,
            hash=header.hash,
            chain_work=header.chain_work,
            version=header.chain_block_header.get("version", 1),
            merkle_root=header.chain_block_header.get("merkleRoot", ""),
            time=header.chain_block_header.get("time", 0),
            bits=header.chain_block_header.get("bits", 0),
            nonce=header.chain_block_header.get("nonce", 0),
        )
