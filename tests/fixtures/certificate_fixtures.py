"""Certificate test fixtures and utilities."""

from datetime import UTC, datetime
from typing import Any


def create_test_certificate(
    *,
    user_id: int = 1,
    certificate_type: bytes | None = None,
    subject: bytes | None = None,
    serial_number: bytes | None = None,
    certifier: bytes | None = None,
    revocation_outpoint: str | None = None,
    signature: bytes | None = None,
    fields: dict[str, bytes] | None = None,
) -> dict[str, Any]:
    """Create a test certificate dict for insertion into storage.

    Args:
        user_id: User ID for the certificate
        certificate_type: Certificate type bytes
        subject: Subject identifier bytes
        serial_number: Certificate serial number bytes
        certifier: Certifier identifier bytes
        revocation_outpoint: Revocation outpoint string
        signature: Certificate signature bytes
        fields: Additional certificate fields

    Returns:
        Dictionary ready for storage.insert_certificate()
    """
    if certificate_type is None:
        # Default test type
        certificate_type = b"test_type"

    if subject is None:
        subject = b"test_subject"

    if serial_number is None:
        serial_number = b"test_serial"

    if certifier is None:
        certifier = b"test_certifier"

    if signature is None:
        signature = b"test_signature"

    now = datetime.now(UTC)

    cert_data = {
        "userId": user_id,
        "type": certificate_type,
        "subject": subject,
        "serialNumber": serial_number,
        "certifier": certifier,
        "revocationOutpoint": revocation_outpoint or "pending",
        "signature": signature,
        "isDeleted": False,
        "createdAt": now,
        "updatedAt": now,
    }

    return cert_data


def seed_certificate(storage: Any, cert_data: dict[str, Any]) -> int:
    """Seed a certificate into storage safely.

    Args:
        storage: StorageProvider instance
        cert_data: Certificate data dict from create_test_certificate()

    Returns:
        Certificate ID from database
    """
    return storage.insert_certificate(cert_data)
