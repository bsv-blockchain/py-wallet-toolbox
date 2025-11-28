"""
ServiceCollection for multi-provider service management and failover strategy.

This module implements a generic service collection pattern supporting multiple
providers with round-robin failover, performance tracking, and call history.

Key Features:
    - Multiple provider registration and prioritization
    - Round-robin failover strategy (next provider on failure)
    - Per-provider call history and statistics
    - Performance metrics (success, failure, error counts and timing)
    - Service health monitoring

Typical Usage:
    from bsv_wallet_toolbox.services.service_collection import ServiceCollection

    # Create a service collection
    services = ServiceCollection('getMerklePath')
    services.add({'name': 'Bitails', 'service': bitails.get_merkle_path})
    services.add({'name': 'WhatsOnChain', 'service': woc.get_merkle_path})

    # Get current service and make a call
    stc = services.service_to_call
    try:
        result = stc['service'](txid)
        services.add_service_call_success(stc, result)
    except Exception as e:
        services.add_service_call_error(stc, e)
        services.next()  # Move to next provider

Reference Implementation: ts-wallet-toolbox/src/services/ServiceCollection.ts
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Generic, TypeVar

T = TypeVar("T")

MAX_RESET_COUNTS = 32
MAX_CALL_HISTORY = 32


@dataclass
class ServiceCall:
    """Individual service call record."""

    when: datetime
    """Timestamp of the call."""
    msecs: int
    """Duration of the call in milliseconds."""
    success: bool
    """True iff service provider successfully processed the request."""
    result: str | None = None
    """Simple text summary of result (e.g., 'valid utxo')."""
    error: dict[str, Any] | None = None
    """Error code and message if exception was thrown."""


@dataclass
class ResetCount:
    """Statistics for a time interval."""

    success: int = 0
    failure: int = 0
    error: int = 0
    since: datetime = field(default_factory=lambda: datetime.now(UTC))
    until: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ProviderCallHistory:
    """Call history and statistics for a specific provider."""

    service_name: str
    provider_name: str
    calls: list[ServiceCall] = field(default_factory=list)
    total_counts: ResetCount | None = None
    reset_counts: list[ResetCount] = field(default_factory=list)


@dataclass
class ServiceCallHistoryEntry:
    """Serialized service call record."""

    when: str
    msecs: int
    success: bool
    result: str | None = None
    error: dict[str, Any] | None = None


@dataclass
class ResetCountEntry:
    """Serialized statistics interval."""

    success: int
    failure: int
    error: int
    since: str
    until: str


@dataclass
class ProviderCallHistoryEntry:
    """Serialized provider call history."""

    service_name: str
    provider_name: str
    calls: list[ServiceCallHistoryEntry] = field(default_factory=list)
    total_counts: dict[str, Any] | None = None
    reset_counts: list[ResetCountEntry] = field(default_factory=list)


@dataclass
class ServiceCallHistory:
    """Complete call history for a service."""

    service_name: str
    history_by_provider: dict[str, ProviderCallHistoryEntry] = field(default_factory=dict)


@dataclass
class ServiceToCall(Generic[T]):
    """Descriptor for a service provider to call."""

    service_name: str
    provider_name: str
    service: T
    call: ServiceCall


class ServiceCollection(Generic[T]):
    """Generic service collection with multi-provider failover.

    Manages multiple provider instances (e.g., WhatsOnChain, Bitails) with
    round-robin failover, call history tracking, and performance metrics.

    Attributes:
        service_name: Name of the service (e.g., 'getMerklePath').
        services: List of providers with name and service callable.
        _index: Current active provider index.
        since: Collection creation timestamp.
    """

    def __init__(
        self,
        service_name: str,
        services: list[dict[str, Any]] | None = None,
    ) -> None:
        """Initialize ServiceCollection.

        Args:
            service_name: Name of the service for tracking.
            services: Optional list of initial services with 'name' and 'service' keys.
        """
        self.service_name = service_name
        self.services: list[dict[str, Any]] = services or []
        self._index = 0
        self.since = datetime.now(UTC)
        self._history_by_provider: dict[str, ProviderCallHistory] = {}

    def add(self, service_entry: dict[str, Any]) -> ServiceCollection[T]:
        """Add a provider to the collection.

        Args:
            service_entry: Dict with 'name' and 'service' keys.

        Returns:
            Self for method chaining.
        """
        self.services.append(service_entry)
        return self

    def remove(self, name: str) -> None:
        """Remove a provider by name.

        Args:
            name: Provider name to remove.
        """
        self.services = [s for s in self.services if s.get("name") != name]

    @property
    def name(self) -> str:
        """Get current provider name."""
        return self.services[self._index].get("name", "unknown")

    @property
    def service(self) -> T:
        """Get current provider service."""
        return self.services[self._index].get("service")

    def get_service_to_call(self, index: int) -> ServiceToCall[T]:
        """Get service descriptor for a provider at index.

        Args:
            index: Provider index.

        Returns:
            ServiceToCall descriptor.
        """
        provider_name = self.services[index].get("name", "unknown")
        service = self.services[index].get("service")
        call = ServiceCall(
            when=datetime.now(UTC),
            msecs=0,
            success=False,
            result=None,
            error=None,
        )
        return ServiceToCall(
            service_name=self.service_name,
            provider_name=provider_name,
            service=service,
            call=call,
        )

    @property
    def service_to_call(self) -> ServiceToCall[T]:
        """Get service descriptor for current provider."""
        return self.get_service_to_call(self._index)

    @property
    def all_services_to_call(self) -> list[ServiceToCall[T]]:
        """Get service descriptors for all providers."""
        return [self.get_service_to_call(i) for i in range(len(self.services))]

    def move_service_to_last(self, stc: ServiceToCall[T]) -> None:
        """Move a provider to the end (de-prioritize).

        Args:
            stc: Service to call descriptor.
        """
        for i, service in enumerate(self.services):
            if service.get("name") == stc.provider_name:
                self.services.append(self.services.pop(i))
                break

    @property
    def all_services(self) -> list[T]:
        """Get all service instances."""
        return [s.get("service") for s in self.services]

    @property
    def count(self) -> int:
        """Get number of providers."""
        return len(self.services)

    @property
    def index(self) -> int:
        """Get current provider index."""
        return self._index

    def reset(self) -> None:
        """Reset to first provider."""
        self._index = 0

    def next(self) -> int:
        """Move to next provider (round-robin).

        Returns:
            New provider index.
        """
        self._index = (self._index + 1) % self.count
        return self._index

    def clone(self) -> ServiceCollection[T]:
        """Create a copy of this collection.

        Returns:
            New ServiceCollection with same providers.
        """
        return ServiceCollection(self.service_name, [dict(s) for s in self.services])

    def _add_service_call(
        self,
        provider_name: str,
        call: ServiceCall,
    ) -> ProviderCallHistory:
        """Record a service call.

        Args:
            provider_name: Provider name.
            call: Service call record.

        Returns:
            Updated provider call history.
        """
        now = datetime.now(UTC)
        history = self._history_by_provider.get(provider_name)

        if not history:
            history = ProviderCallHistory(
                service_name=self.service_name,
                provider_name=provider_name,
                calls=[],
                total_counts=ResetCount(since=self.since, until=now),
                reset_counts=[ResetCount(since=self.since, until=now)],
            )
            self._history_by_provider[provider_name] = history

        # Add call to history (most recent first)
        history.calls.insert(0, call)
        history.calls = history.calls[:MAX_CALL_HISTORY]

        # Update timestamps
        if history.total_counts:
            history.total_counts.until = now
        if history.reset_counts:
            history.reset_counts[0].until = now

        return history

    def get_duration(self, since: datetime) -> int:
        """Calculate duration in milliseconds.

        Args:
            since: Start timestamp.

        Returns:
            Duration in milliseconds.
        """
        now = datetime.now(UTC)
        delta = now - since
        return int(delta.total_seconds() * 1000)

    def add_service_call_success(
        self,
        stc: ServiceToCall[T],
        result: str | None = None,
    ) -> None:
        """Record a successful service call.

        Args:
            stc: Service to call descriptor.
            result: Optional result summary.
        """
        call = stc.call
        call.success = True
        call.result = result
        call.error = None
        call.msecs = self.get_duration(call.when)

        history = self._add_service_call(stc.provider_name, call)
        if history.total_counts:
            history.total_counts.success += 1
        if history.reset_counts:
            history.reset_counts[0].success += 1

    def add_service_call_failure(
        self,
        stc: ServiceToCall[T],
        result: str | None = None,
    ) -> None:
        """Record a failed service call.

        Args:
            stc: Service to call descriptor.
            result: Optional result summary.
        """
        call = stc.call
        call.success = False
        call.result = result
        call.error = None
        call.msecs = self.get_duration(call.when)

        history = self._add_service_call(stc.provider_name, call)
        if history.total_counts:
            history.total_counts.failure += 1
        if history.reset_counts:
            history.reset_counts[0].failure += 1

    def add_service_call_error(
        self,
        stc: ServiceToCall[T],
        error: Exception,
    ) -> None:
        """Record a service call with error.

        Args:
            stc: Service to call descriptor.
            error: Exception that was raised.
        """
        call = stc.call
        call.success = False
        call.result = None
        call.error = {
            "message": str(error),
            "code": type(error).__name__,
        }
        call.msecs = self.get_duration(call.when)

        history = self._add_service_call(stc.provider_name, call)
        if history.total_counts:
            history.total_counts.failure += 1
            history.total_counts.error += 1
        if history.reset_counts:
            history.reset_counts[0].failure += 1
            history.reset_counts[0].error += 1

    def get_service_call_history(self, reset: bool = False) -> ServiceCallHistory:
        """Get complete call history with optional reset.

        Args:
            reset: If true, start new history interval.

        Returns:
            ServiceCallHistory with serialized records.
        """
        now = datetime.now(UTC)
        history = ServiceCallHistory(service_name=self.service_name)

        for provider_name, prov_history in self._history_by_provider.items():
            # Serialize calls
            call_entries = [
                ServiceCallHistoryEntry(
                    when=call.when.isoformat(),
                    msecs=call.msecs,
                    success=call.success,
                    result=call.result,
                    error=call.error,
                )
                for call in prov_history.calls
            ]

            # Serialize total counts
            total_counts_dict = None
            if prov_history.total_counts:
                total_counts_dict = {
                    "success": prov_history.total_counts.success,
                    "failure": prov_history.total_counts.failure,
                    "error": prov_history.total_counts.error,
                    "since": prov_history.total_counts.since.isoformat(),
                    "until": prov_history.total_counts.until.isoformat(),
                }

            # Serialize reset counts
            reset_count_entries = [
                ResetCountEntry(
                    success=rc.success,
                    failure=rc.failure,
                    error=rc.error,
                    since=rc.since.isoformat(),
                    until=rc.until.isoformat(),
                )
                for rc in prov_history.reset_counts
            ]

            entry = ProviderCallHistoryEntry(
                service_name=prov_history.service_name,
                provider_name=prov_history.provider_name,
                calls=call_entries,
                total_counts=total_counts_dict,
                reset_counts=reset_count_entries,
            )

            history.history_by_provider[provider_name] = entry

            if reset:
                # End current interval
                if prov_history.reset_counts:
                    prov_history.reset_counts[0].until = now
                    # Start new interval
                    prov_history.reset_counts.insert(
                        0,
                        ResetCount(since=now, until=now),
                    )
                    # Limit history
                    prov_history.reset_counts = prov_history.reset_counts[:MAX_CALL_HISTORY]

        return history
