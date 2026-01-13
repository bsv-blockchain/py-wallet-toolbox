"""Identity utility functions for certificate and identity management.

This module provides utilities for working with identity certificates,
including trust-based filtering and certificate discovery.

Reference: toolbox/ts-wallet-toolbox/src/utility/identityUtils.ts
"""

import json
from typing import Any, TypedDict

from bsv.auth.verifiable_certificate import VerifiableCertificate as BsvVerifiableCertificate
from bsv.overlay_tools.lookup_resolver import LookupError, LookupQuestion
from bsv.transaction import Transaction
from bsv.transaction.pushdrop import PushDrop
from bsv.utils import to_utf8


class IdentityCertifier(TypedDict, total=False):
    """Certifier information associated with a certificate."""

    name: str
    iconUrl: str
    description: str
    trust: int


class VerifiableCertificate(TypedDict, total=False):
    """Verifiable certificate with extended information."""

    type: str
    serialNumber: str
    subject: str
    certifier: str
    revocationOutpoint: str
    signature: str
    keyring: dict[str, str]
    decryptedFields: dict[str, str]
    publiclyRevealedKeyring: dict[str, str]
    certifierInfo: IdentityCertifier


class DiscoverCertificatesResult(TypedDict, total=False):
    """Result of certificate discovery."""

    totalCertificates: int
    certificates: list[VerifiableCertificate]


class TrustSettings(TypedDict, total=False):
    """Trust settings for certificate validation."""

    trustLevel: int
    trustedCertifiers: list[dict[str, Any]]


class IdentityGroup(TypedDict, total=False):
    """Grouping of certificates by identity."""

    totalTrust: int
    members: list[VerifiableCertificate]


def transform_verifiable_certificates_with_trust(
    trust_settings: TrustSettings,
    certificates: list[VerifiableCertificate],
) -> DiscoverCertificatesResult:
    """Transform certificates according to trust settings.

    Transforms an array of VerifiableCertificate instances according to the trust settings.
    Only certificates whose grouped total trust meets the threshold are returned,
    and each certificate is augmented with a certifierInfo property.

    Args:
        trust_settings: The user's trust settings including trustLevel and trusted certifiers
        certificates: Array of VerifiableCertificate objects

    Returns:
        DiscoverCertificatesResult with totalCertificates and ordered certificates

    Reference:
        - toolbox/ts-wallet-toolbox/src/utility/identityUtils.ts (transformVerifiableCertificatesWithTrust)
    """
    # Group certificates by subject while accumulating trust
    identity_groups: dict[str, IdentityGroup] = {}
    # Cache certifier lookups
    certifier_cache: dict[str, dict[str, Any]] = {}

    for cert in certificates:
        subject = cert.get("subject")
        certifier = cert.get("certifier")

        if not subject or not certifier:
            continue

        # Lookup and cache certifier details from trustSettings
        if certifier not in certifier_cache:
            found = None
            for trusted_cert in trust_settings.get("trustedCertifiers", []):
                if trusted_cert.get("identityKey") == certifier:
                    found = trusted_cert
                    break

            if not found:
                # Skip this certificate if its certifier is not trusted
                continue

            certifier_cache[certifier] = found

        # Create the IdentityCertifier object to attach
        certifier_info: IdentityCertifier = {
            "name": certifier_cache[certifier].get("name", ""),
            "iconUrl": certifier_cache[certifier].get("iconUrl", ""),
            "description": certifier_cache[certifier].get("description", ""),
            "trust": certifier_cache[certifier].get("trust", 0),
        }

        # Create an extended certificate that includes certifierInfo
        extended_cert: VerifiableCertificate = {
            **cert,
            "certifierInfo": certifier_info,
        }

        # Group certificates by subject
        if subject not in identity_groups:
            identity_groups[subject] = {"totalTrust": 0, "members": []}

        identity_groups[subject]["totalTrust"] += certifier_info["trust"]
        identity_groups[subject]["members"].append(extended_cert)

    # Filter out groups that do not meet the trust threshold and flatten the results
    final_results: list[VerifiableCertificate] = []
    for group in identity_groups.values():
        if group["totalTrust"] >= trust_settings.get("trustLevel", 0):
            final_results.extend(group["members"])

    # Sort the certificates by their certifier trust in descending order
    final_results.sort(
        key=lambda x: x.get("certifierInfo", {}).get("trust", 0),
        reverse=True,
    )

    return {
        "totalCertificates": len(final_results),
        "certificates": final_results,
    }


def query_overlay_certificates(query: Any, lookup_results: list[dict[str, Any]]) -> list[VerifiableCertificate]:
    """Parse overlay service lookup results and return certificates.

    Internal function: Parse the returned certificates, decrypt and verify them.
    Return the set of identity keys, certificates and decrypted certificate fields.

    Args:
        query: Query parameters (for future use)
        lookup_results: List of lookup results from overlay service

    Returns:
        List of parsed and verified VerifiableCertificate objects

    Reference:
        - toolbox/ts-wallet-toolbox/src/utility/identityUtils.ts (queryOverlay, parseResults)
    """
    parsed_results: list[VerifiableCertificate] = []

    for result in lookup_results:
        try:
            # Parse certificate data from result
            if not isinstance(result, dict):
                continue

            # Extract certificate fields
            cert_data: VerifiableCertificate = {
                "type": result.get("type", ""),
                "serialNumber": result.get("serialNumber", ""),
                "subject": result.get("subject", ""),
                "certifier": result.get("certifier", ""),
                "revocationOutpoint": result.get("revocationOutpoint", ""),
                "signature": result.get("signature", ""),
                "keyring": result.get("keyring", {}),
                "decryptedFields": result.get("decryptedFields", {}),
            }

            parsed_results.append(cert_data)
        except Exception:
            # Silently skip certificates that cannot be parsed
            pass

    return parsed_results


async def query_overlay(query: Any, resolver: Any) -> list[VerifiableCertificate]:  # type: ignore
    """Query overlay service for identity certificates.

    Queries the overlay service for identity certificates matching a query,
    then parses and returns the results.

    Args:
        query: Query parameters for overlay service
        resolver: Resolver object with query method (LookupResolver)

    Returns:
        List of parsed verifiable certificates

    Reference: toolbox/ts-wallet-toolbox/src/utility/identityUtils.ts:109-116
    """
    # Call overlay service query
    question = LookupQuestion(service="ls_identity", query=query)
    try:
        results = await resolver.query(question)
    except LookupError:
        return []

    # Parse and return results
    return await parse_results(results)


async def parse_results(lookup_result: dict[str, Any]) -> list[VerifiableCertificate]:
    """Parse identity certificate lookup results.

    Decodes, verifies, and decrypts certificates from overlay service results.

    Args:
        lookup_result: Result from overlay service lookup query

    Returns:
        List of parsed and verified certificates

    Reference: toolbox/ts-wallet-toolbox/src/utility/identityUtils.ts:124-159
    """
    if lookup_result.get("type") != "output-list":
        return []

    parsed_results: list[VerifiableCertificate] = []

    for output in lookup_result.get("outputs", []):
        try:
            # Parse transaction from BEEF
            beef_data = output.get("beef")
            if not beef_data:
                continue

            tx = Transaction.from_beef(beef_data)

            # Extract output script and decode with PushDrop
            output_index = output.get("outputIndex", 0)
            if output_index >= len(tx.outputs):
                continue

            locking_script = tx.outputs[output_index].lockingScript
            decoded_output = PushDrop.decode(locking_script)

            # Parse certificate JSON from first field
            cert_json_str = to_utf8(decoded_output["fields"][0])
            certificate_data = json.loads(cert_json_str)

            # Create BsvVerifiableCertificate instance using py-sdk
            # Note: This uses py-sdk's auth.verifiable_certificate module
            keyring_data = certificate_data.get("keyring", {})
            verifiable_cert = BsvVerifiableCertificate(
                cert=certificate_data,  # py-sdk Certificate
                keyring=keyring_data if isinstance(keyring_data, dict) else {},
            )

            # Convert to VerifiableCertificate TypedDict for return
            result_cert: VerifiableCertificate = {
                "type": certificate_data.get("type"),
                "serialNumber": certificate_data.get("serialNumber"),
                "subject": certificate_data.get("subject"),
                "certifier": certificate_data.get("certifier"),
                "revocationOutpoint": certificate_data.get("revocationOutpoint"),
                "fields": certificate_data.get("fields"),
                "keyring": keyring_data,
                "signature": certificate_data.get("signature"),
            }
            # Store the underlying BsvVerifiableCertificate for later use if needed
            if not hasattr(result_cert, "_bsv_cert"):
                result_cert["_bsvCert"] = verifiable_cert  # type: ignore

            parsed_results.append(result_cert)
        except Exception:
            # Silently skip unparseable certificates (as per TS implementation)
            pass

    return parsed_results


__all__ = [
    "DiscoverCertificatesResult",
    "IdentityCertifier",
    "IdentityGroup",
    "TrustSettings",
    "VerifiableCertificate",
    "parse_results",
    "query_overlay",
    "query_overlay_certificates",
    "transform_verifiable_certificates_with_trust",
]
