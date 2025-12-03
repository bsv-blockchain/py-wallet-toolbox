"""Permission-related type definitions.

Shared types used by permission token management components.
"""

from __future__ import annotations

from typing import Any, TypedDict


class PermissionToken(TypedDict, total=False):
    """Permission token data structure.

    Represents a permission token with all its fields.
    Optional fields are marked with total=False.
    """

    # Transaction information
    txid: str
    tx: list[int]
    outputIndex: int
    outputScript: str
    satoshis: int

    # Permission details
    type: str  # "protocol", "basket", "certificate", "spending"
    originator: str
    expiry: int

    # Protocol permission fields (DPACP)
    protocol: str
    securityLevel: int
    counterparty: str | None
    privileged: bool

    # Basket permission fields (DBAP)
    basketName: str

    # Certificate permission fields (DCAP)
    certType: str
    verifier: str
    certFields: list[str]

    # Spending permission fields (DSAP)
    authorizedAmount: int
    tracked_spending: int  # Amount already spent against this token


class PermissionRequest(TypedDict, total=False):
    """Permission request data structure.

    Represents a request for permission from a user/application.
    """

    requestID: str
    type: str  # "protocol", "basket", "certificate", "spending", "grouped"
    originator: str
    reason: str

    # Protocol request fields
    protocolID: dict[str, Any]
    counterparty: str | None

    # Basket request fields
    basket: str

    # Certificate request fields
    certificate: dict[str, Any]

    # Spending request fields
    spending: dict[str, Any]

    # Grouped request fields
    permissions: list[PermissionRequest]
