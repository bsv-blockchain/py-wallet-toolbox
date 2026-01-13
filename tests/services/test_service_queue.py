"""Tests for service queue pattern."""

from unittest.mock import AsyncMock

import pytest

from bsv_wallet_toolbox.services.service_queue import EmptyResultError, NamedService, NoServicesError, ServiceQueue


class TestServiceQueue:
    """Test ServiceQueue functionality."""

    @pytest.mark.asyncio
    async def test_one_by_one_success_first_service(self):
        """Test one_by_one returns first successful result."""
        service1 = AsyncMock(return_value="result1")
        service2 = AsyncMock(return_value="result2")

        queue = ServiceQueue("test", [NamedService("svc1", service1), NamedService("svc2", service2)])

        result = await queue.one_by_one()

        assert result == "result1"
        service1.assert_called_once()
        service2.assert_not_called()

    @pytest.mark.asyncio
    async def test_one_by_one_success_after_failure(self):
        """Test one_by_one tries multiple services until success."""
        service1 = AsyncMock(return_value=None)  # Empty result
        service2 = AsyncMock(return_value="result2")

        queue = ServiceQueue("test", [NamedService("svc1", service1), NamedService("svc2", service2)])

        result = await queue.one_by_one()

        assert result == "result2"
        service1.assert_called_once()
        service2.assert_called_once()

    @pytest.mark.asyncio
    async def test_one_by_one_all_fail_empty(self):
        """Test one_by_one raises EmptyResultError when all services return empty."""
        service1 = AsyncMock(return_value=None)
        service2 = AsyncMock(return_value=None)

        queue = ServiceQueue("test", [NamedService("svc1", service1), NamedService("svc2", service2)])

        with pytest.raises(EmptyResultError):
            await queue.one_by_one()

    @pytest.mark.asyncio
    async def test_one_by_one_all_fail_exceptions(self):
        """Test one_by_one raises last exception when all services fail."""
        service1 = AsyncMock(side_effect=Exception("Service 1 failed"))
        service2 = AsyncMock(side_effect=Exception("Service 2 failed"))

        queue = ServiceQueue("test", [NamedService("svc1", service1), NamedService("svc2", service2)])

        with pytest.raises(Exception, match="Service 2 failed"):
            await queue.one_by_one()

    @pytest.mark.asyncio
    async def test_all_parallel(self):
        """Test all_parallel executes all services concurrently."""
        service1 = AsyncMock(return_value="result1")
        service2 = AsyncMock(return_value="result2")

        queue = ServiceQueue("test", [NamedService("svc1", service1), NamedService("svc2", service2)])

        results = await queue.all_parallel()

        assert len(results) == 2
        assert results[0].name == "svc1"
        assert results[0].result == "result1"
        assert results[1].name == "svc2"
        assert results[1].result == "result2"

    def test_no_services_error(self):
        """Test that empty service queue raises error."""
        with pytest.raises(NoServicesError):
            ServiceQueue("test", [])

    def test_service_info(self):
        """Test service information methods."""
        service1 = AsyncMock()
        service2 = AsyncMock()

        queue = ServiceQueue("test", [NamedService("svc1", service1), NamedService("svc2", service2)])

        assert queue.get_service_names() == ["svc1", "svc2"]
        assert queue.count_services() == 2
