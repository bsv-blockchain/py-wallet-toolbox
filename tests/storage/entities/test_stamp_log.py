"""Unit tests for stampLog utility functions.

Reference: wallet-toolbox/src/storage/schema/entities/__tests/stampLogTests.test.ts
"""

import re

import pytest

from bsv_wallet_toolbox.utils.stamp_log import stamp_log, stamp_log_format


class TeststampLog:
    """Test suite for stampLog and stampLogFormat functions."""

    def test_appends_to_string_log(self) -> None:
        """Given: Initial string log and line to add
           When: Call stamp_log
           Then: Appends timestamped line to log

        Reference: src/storage/schema/entities/__tests/stampLogTests.test.ts
                  test('0_appends_to_string_log')
        """
        # Given

        initial_log = "2025-01-10T10:00:00.000Z Event 1\n"
        line_to_add = "Event 2"

        # When
        updated_log = stamp_log(initial_log, line_to_add)

        # Then

        assert "Event 2" in updated_log
        assert re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z Event 2\n$", updated_log)

    def test_appends_to_object_log(self) -> None:
        """Given: Initial object log with 'log' property and line to add
           When: Call stamp_log
           Then: Appends timestamped line to object's log

        Reference: src/storage/schema/entities/__tests/stampLogTests.test.ts
                  test('1_appends_to_object_log')
        """
        # Given

        initial_log = {"log": "2025-01-10T10:00:00.000Z Event 1\n"}
        line_to_add = "Event 2"

        # When
        updated_log = stamp_log(initial_log, line_to_add)

        # Then

        assert "Event 2" in updated_log
        assert re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z Event 2\n$", updated_log)

    def test_returns_undefined_for_invalid_input(self) -> None:
        """Given: Undefined/None input
           When: Call stamp_log
           Then: Returns None

        Reference: src/storage/schema/entities/__tests/stampLogTests.test.ts
                  test('2_returns_undefined_for_invalid_input')
        """
        # Given

        # When
        updated_log = stamp_log(None, "Event 1")

        # Then
        assert updated_log is None

    def test_formats_valid_log_without_network(self) -> None:
        """Given: Valid log without **NETWORK** entries
           When: Call stamp_log_format
           Then: Returns formatted log with timing information

        Reference: src/storage/schema/entities/__tests/stampLogTests.test.ts
                  test('3_formats_valid_log_without_network')
        """
        # Given

        log = "2025-01-10T10:00:00.000Z Event 1\n2025-01-10T10:00:01.000Z Event 2\n2025-01-10T10:00:03.000Z Event 3"

        # When
        output = stamp_log_format(log)

        # Then
        assert "Total = 3000 msecs" in output
        assert " 1000 Event 2" in output
        assert " 2000 Event 3" in output

    def test_formats_log_with_network_entries(self) -> None:
        """Given: Valid log with **NETWORK** entries
           When: Call stamp_log_format
           Then: Returns formatted log including network entries

        Reference: src/storage/schema/entities/__tests/stampLogTests.test.ts
                  test('4_formats_log_with_network_entries')
        """
        # Given

        log = (
            "2025-01-10T10:00:00.000Z Event 1\n"
            "2025-01-10T10:00:01.000Z **NETWORK**\n"
            "2025-01-10T10:00:02.000Z Event 2\n"
            "2025-01-10T10:00:03.000Z **NETWORK**\n"
            "2025-01-10T10:00:05.000Z Event 3"
        )

        # When
        output = stamp_log_format(log)

        # Then
        assert "Total = 5000 msecs" in output
        assert " 1000 **NETWORK**" in output
        assert " 2000 Event 3" in output

    def test_handles_invalid_log_entries_gracefully(self) -> None:
        """Given: Log with invalid timestamp
           When: Call stamp_log_format
           Then: Raises RangeError

        Reference: src/storage/schema/entities/__tests/stampLogTests.test.ts
                  test('5_handles_invalid_log_entries_gracefully')
        """
        # Given

        log = "Invalid Timestamp Event 1\n2025-01-10T10:00:01.000Z Event 2"

        # When/Then
        with pytest.raises(ValueError):  # Python uses ValueError for invalid date parsing
            stamp_log_format(log)

    def test_handles_non_string_log_gracefully(self) -> None:
        """Given: Non-string inputs (None, int, dict, list, bool)
           When: Call stamp_log_format
           Then: Returns empty string

        Reference: src/storage/schema/entities/__tests/stampLogTests.test.ts
                  test('6_handles_non-string_log_gracefully')
        """
        # Given

        non_string_inputs = [None, 123, {}, [], True]

        # When/Then
        for input_val in non_string_inputs:
            result = stamp_log_format(input_val)
            assert result == ""

    def test_formats_empty_log_string(self) -> None:
        """Given: Empty string log
        When: Call stamp_log_format
        Then: Returns empty string
        """
        # Given
        log = ""

        # When
        result = stamp_log_format(log)

        # Then
        assert result == ""

    def test_formats_log_with_no_spaced_lines(self) -> None:
        """Given: Log string with lines that have no spaces (no timestamps)
        When: Call stamp_log_format
        Then: Returns empty string
        """
        # Given - log with lines that have no spaces, so they are skipped
        log = "Event1\nEvent2\nEvent3"

        # When
        result = stamp_log_format(log)

        # Then
        assert result == ""
