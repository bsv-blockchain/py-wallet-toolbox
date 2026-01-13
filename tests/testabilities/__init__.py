"""Test abilities for py-wallet-toolbox E2E testing.

This module provides:
- tsgenerated: TS-generated test fixtures for cross-implementation compatibility
- testusers: Fixed test users (Alice, Bob) matching Go/TS implementations
- testservices: Mock services with script verification (MockARC, MockBHS)

Reference: go-wallet-toolbox/pkg/internal/testabilities/
"""

from . import testservices, testusers, tsgenerated

__all__ = ["testservices", "testusers", "tsgenerated"]
