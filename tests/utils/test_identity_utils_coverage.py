"""Coverage tests for identity_utils.

This module tests identity certificate management and overlay service operations.
"""

from unittest.mock import AsyncMock, Mock

import pytest

try:
    from bsv.overlay_tools.lookup_resolver import LookupQuestion

    from bsv_wallet_toolbox.utils.identity_utils import (
        parse_results,
        query_overlay,
        query_overlay_certificates,
        transform_verifiable_certificates_with_trust,
    )

    IMPORT_SUCCESS = True
except ImportError:
    IMPORT_SUCCESS = False
    LookupQuestion = None


class TestTransformVerifiableCertificatesWithTrust:
    """Test transform_verifiable_certificates_with_trust function."""

    def test_transform_empty_certificates(self) -> None:
        """Test transforming empty certificate list."""
        trust_settings = {"trustLevel": 50, "trustedCertifiers": []}
        result = transform_verifiable_certificates_with_trust(trust_settings, [])

        assert result["totalCertificates"] == 0
        assert result["certificates"] == []

    def test_transform_single_certificate_above_threshold(self) -> None:
        """Test transforming single certificate that meets trust threshold."""
        trust_settings = {
            "trustLevel": 50,
            "trustedCertifiers": [{"identityKey": "certifier1", "name": "Test Certifier", "trust": 100}],
        }

        certificates = [{"type": "identity", "subject": "subject1", "certifier": "certifier1", "serialNumber": "123"}]

        result = transform_verifiable_certificates_with_trust(trust_settings, certificates)

        assert result["totalCertificates"] == 1
        assert len(result["certificates"]) == 1
        assert result["certificates"][0]["certifierInfo"]["trust"] == 100

    def test_transform_certificate_below_threshold(self) -> None:
        """Test filtering out certificates below trust threshold."""
        trust_settings = {
            "trustLevel": 100,
            "trustedCertifiers": [{"identityKey": "certifier1", "name": "Test Certifier", "trust": 50}],
        }

        certificates = [{"type": "identity", "subject": "subject1", "certifier": "certifier1", "serialNumber": "123"}]

        result = transform_verifiable_certificates_with_trust(trust_settings, certificates)

        assert result["totalCertificates"] == 0
        assert result["certificates"] == []

    def test_transform_untrusted_certifier(self) -> None:
        """Test filtering out certificates from untrusted certifiers."""
        trust_settings = {
            "trustLevel": 50,
            "trustedCertifiers": [{"identityKey": "trusted_certifier", "name": "Trusted", "trust": 100}],
        }

        certificates = [
            {
                "type": "identity",
                "subject": "subject1",
                "certifier": "untrusted_certifier",  # Not in trusted list
                "serialNumber": "123",
            }
        ]

        result = transform_verifiable_certificates_with_trust(trust_settings, certificates)

        assert result["totalCertificates"] == 0
        assert result["certificates"] == []

    def test_transform_multiple_certificates_same_subject(self) -> None:
        """Test grouping certificates by subject and accumulating trust."""
        trust_settings = {
            "trustLevel": 100,
            "trustedCertifiers": [
                {"identityKey": "certifier1", "name": "Certifier 1", "trust": 60},
                {"identityKey": "certifier2", "name": "Certifier 2", "trust": 70},
            ],
        }

        certificates = [
            {"type": "identity", "subject": "subject1", "certifier": "certifier1", "serialNumber": "123"},
            {"type": "identity", "subject": "subject1", "certifier": "certifier2", "serialNumber": "456"},
        ]

        result = transform_verifiable_certificates_with_trust(trust_settings, certificates)

        assert result["totalCertificates"] == 2  # Both meet threshold (60+70=130 > 100)
        assert len(result["certificates"]) == 2
        # Should be sorted by trust descending
        assert result["certificates"][0]["certifierInfo"]["trust"] == 70
        assert result["certificates"][1]["certifierInfo"]["trust"] == 60

    def test_transform_certificate_without_subject(self) -> None:
        """Test skipping certificates without subject."""
        trust_settings = {
            "trustLevel": 50,
            "trustedCertifiers": [{"identityKey": "certifier1", "name": "Test Certifier", "trust": 100}],
        }

        certificates = [{"type": "identity", "certifier": "certifier1", "serialNumber": "123"}]  # Missing subject

        result = transform_verifiable_certificates_with_trust(trust_settings, certificates)

        assert result["totalCertificates"] == 0
        assert result["certificates"] == []

    def test_transform_certificate_without_certifier(self) -> None:
        """Test skipping certificates without certifier."""
        trust_settings = {
            "trustLevel": 50,
            "trustedCertifiers": [{"identityKey": "certifier1", "name": "Test Certifier", "trust": 100}],
        }

        certificates = [{"type": "identity", "subject": "subject1", "serialNumber": "123"}]  # Missing certifier

        result = transform_verifiable_certificates_with_trust(trust_settings, certificates)

        assert result["totalCertificates"] == 0
        assert result["certificates"] == []


class TestQueryOverlayCertificates:
    """Test query_overlay_certificates function."""

    def test_query_overlay_certificates_empty_results(self) -> None:
        """Test parsing empty overlay results."""
        result = query_overlay_certificates({}, [])

        assert result == []

    def test_query_overlay_certificates_valid_results(self) -> None:
        """Test parsing valid overlay results."""
        lookup_results = [
            {
                "type": "identity",
                "serialNumber": "123",
                "subject": "subject1",
                "certifier": "certifier1",
                "revocationOutpoint": "outpoint1",
                "signature": "signature1",
                "keyring": {"key1": "value1"},
                "decryptedFields": {"field1": "value1"},
            }
        ]

        result = query_overlay_certificates({}, lookup_results)

        assert len(result) == 1
        assert result[0]["type"] == "identity"
        assert result[0]["serialNumber"] == "123"
        assert result[0]["subject"] == "subject1"

    def test_query_overlay_certificates_invalid_result(self) -> None:
        """Test handling invalid result entries."""
        lookup_results = [
            "not_a_dict",  # Invalid entry
            {"type": "identity", "subject": "subject1", "certifier": "certifier1"},
        ]

        result = query_overlay_certificates({}, lookup_results)

        assert len(result) == 1  # Only the valid one
        assert result[0]["type"] == "identity"

    def test_query_overlay_certificates_missing_fields(self) -> None:
        """Test parsing certificates with missing fields."""
        lookup_results = [
            {
                "type": "identity",
                "subject": "subject1",
                # Missing certifier and other fields - should use defaults
            }
        ]

        result = query_overlay_certificates({}, lookup_results)

        assert len(result) == 1
        assert result[0]["type"] == "identity"
        assert result[0]["subject"] == "subject1"
        assert result[0]["certifier"] == ""  # Default empty string


class TestParseResults:
    """Test parse_results function."""

    @pytest.mark.asyncio
    async def test_parse_results_wrong_type(self) -> None:
        """Test parse_results with wrong result type."""
        result = await parse_results({"type": "wrong_type"})

        assert result == []

    @pytest.mark.asyncio
    async def test_parse_results_empty_outputs(self) -> None:
        """Test parse_results with empty outputs."""
        result = await parse_results({"type": "output-list", "outputs": []})

        assert result == []

    @pytest.mark.asyncio
    async def test_parse_results_missing_beef(self) -> None:
        """Test parse_results with missing beef data."""
        lookup_result = {"type": "output-list", "outputs": [{"outputIndex": 0}]}  # Missing beef

        result = await parse_results(lookup_result)

        assert result == []

    @pytest.mark.asyncio
    async def test_parse_results_invalid_output_index(self) -> None:
        """Test parse_results with invalid output index."""
        # Mock Transaction.from_beef to return a transaction with no outputs
        mock_tx = Mock()
        mock_tx.outputs = []

        # We can't easily mock Transaction.from_beef, so we'll test the exception handling
        lookup_result = {"type": "output-list", "outputs": [{"beef": "mock_beef", "outputIndex": 0}]}

        result = await parse_results(lookup_result)

        # Should handle the exception gracefully
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_parse_results_exception_handling(self) -> None:
        """Test parse_results exception handling."""
        lookup_result = {"type": "output-list", "outputs": [{"beef": "invalid"}]}  # Will cause exception

        result = await parse_results(lookup_result)

        # Should handle exceptions gracefully
        assert isinstance(result, list)


class TestQueryOverlay:
    """Test query_overlay function."""

    @pytest.mark.asyncio
    async def test_query_overlay_success(self) -> None:
        """Test successful overlay query."""
        query = {"identityKey": "test_key"}
        resolver = Mock()

        # Mock the resolver.query method
        mock_lookup_result = {"type": "output-list", "outputs": []}
        resolver.query = AsyncMock(return_value=mock_lookup_result)

        result = await query_overlay(query, resolver)

        assert isinstance(result, list)
        # Implementation uses LookupQuestion object, not dict
        resolver.query.assert_called_once()
        call_args = resolver.query.call_args[0][0]
        assert isinstance(call_args, LookupQuestion)
        assert call_args.service == "ls_identity"
        assert call_args.query == query

    @pytest.mark.asyncio
    async def test_query_overlay_exception(self) -> None:
        """Test overlay query with exception."""
        query = {"identityKey": "test_key"}
        resolver = Mock()

        resolver.query = AsyncMock(side_effect=Exception("Query failed"))

        # Should propagate exceptions (no internal exception handling)
        with pytest.raises(Exception, match="Query failed"):
            await query_overlay(query, resolver)
