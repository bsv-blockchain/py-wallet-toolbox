"""Service queue pattern for advanced service orchestration.

Provides service failover, parallel execution, and result aggregation
following the Go servicequeue pattern but adapted for Python.

Reference: go-wallet-toolbox/pkg/services/internal/servicequeue/
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Generic, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")
ServiceFunc = Callable[[], Awaitable[T]]


@dataclass
class NamedService(Generic[T]):
    """A named service with its implementation function."""

    name: str
    service: ServiceFunc[T]


@dataclass
class NamedResult(Generic[T]):
    """Result from a named service call."""

    name: str
    result: T | None = None
    error: Exception | None = None

    def is_success(self) -> bool:
        """Check if the service call was successful."""
        return self.error is None

    def is_error(self) -> bool:
        """Check if the service call failed."""
        return self.error is not None


class ServiceQueueError(Exception):
    """Base exception for service queue operations."""


class EmptyResultError(ServiceQueueError):
    """Raised when service returns an empty result."""


class NoServicesError(ServiceQueueError):
    """Raised when no services are registered."""


class ServiceQueue(Generic[T]):
    """Advanced service orchestration with failover and parallel execution.

    Provides service failover (one-by-one until success), parallel execution (all services),
    and result aggregation following the Go servicequeue pattern.

    Reference: go-wallet-toolbox/pkg/services/internal/servicequeue/queues.go
    """

    def __init__(self, method_name: str, services: list[NamedService[T]]):
        """Initialize service queue.

        Args:
            method_name: Name of the service method (for logging)
            services: List of named services to orchestrate
        """
        self.method_name = method_name
        self.services = services
        self.logger = logging.getLogger(f"{__name__}.{method_name}")

        # Validate service names are unique
        names = [s.name for s in services]
        if len(names) != len(set(names)):
            self.logger.warning(f"Duplicate service names in {method_name}: {names}")

        if not services:
            raise NoServicesError(f"No services registered for {method_name}")

    async def one_by_one(self) -> T:
        """Call services one by one until a successful result is obtained.

        Returns:
            First successful result from any service

        Raises:
            EmptyResultError: If all services return empty results
            Exception: If the last service fails
        """
        if not self.services:
            raise NoServicesError(f"No services registered for {self.method_name}")

        last_error = None

        for service in self.services:
            try:
                self.logger.debug(f"Trying service {service.name} for {self.method_name}")
                result = await service.service()

                if result is not None:
                    self.logger.debug(f"Service {service.name} succeeded for {self.method_name}")
                    return result
                else:
                    self.logger.debug(f"Service {service.name} returned empty result for {self.method_name}")

            except Exception as e:
                last_error = e
                self.logger.debug(f"Service {service.name} failed for {self.method_name}: {e}")
                continue

        # All services failed
        if last_error:
            raise last_error
        else:
            raise EmptyResultError(f"All services returned empty results for {self.method_name}")

    async def all_parallel(self) -> list[NamedResult[T]]:
        """Call all services in parallel and return all results.

        Returns:
            List of NamedResult objects for all services
        """
        if not self.services:
            return []

        async def call_service(service: NamedService[T]) -> NamedResult[T]:
            try:
                result = await service.service()
                return NamedResult(name=service.name, result=result)
            except Exception as e:
                return NamedResult(name=service.name, error=e)

        # Execute all services in parallel
        tasks = [call_service(service) for service in self.services]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        return results

    def get_service_names(self) -> list[str]:
        """Get names of all registered services."""
        return [s.name for s in self.services]

    def count_services(self) -> int:
        """Get count of registered services."""
        return len(self.services)


# Convenience functions for creating service queues
def named_service(name: str, service: ServiceFunc[T]) -> NamedService[T]:
    """Create a named service."""
    return NamedService(name=name, service=service)


def create_service_queue(method_name: str, services: list[NamedService[T]]) -> ServiceQueue[T]:
    """Create a service queue with the given services."""
    return ServiceQueue(method_name, services)
