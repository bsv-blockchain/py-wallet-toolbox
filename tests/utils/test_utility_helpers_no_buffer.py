"""Unit tests for utilityHelpers.noBuffer utility functions.

This module tests asString and asUint8Array conversion functions.

Reference: wallet-toolbox/src/utility/__tests/utilityHelpers.noBuffer.test.ts
"""

try:
    from bsv_wallet_toolbox.utils import as_string
    from bsv_wallet_toolbox.utils import as_uint8array as as_uint8_array

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


class TestUtilityHelpersNoBuffer:
    """Test suite for utilityHelpers.noBuffer utility functions.

    Reference: wallet-toolbox/src/utility/__tests/utilityHelpers.noBuffer.test.ts
               describe('utilityHelpers.noBuffer tests')
    """

    def test_convert_from_uint8array(self) -> None:
        """Given: Uint8Array [1, 2, 3, 4]
           When: Convert using asUint8Array and asString with various encodings
           Then: Returns correct conversions for each encoding

        Reference: wallet-toolbox/src/utility/__tests/utilityHelpers.noBuffer.test.ts
                   test('0 convert from Uint8Array')
        """
        # Given
        a = bytes([1, 2, 3, 4])

        # When/Then - asUint8Array
        r = as_uint8_array(a)
        assert len(r) == 4
        assert all(r[i] == a[i] for i in range(len(a)))

        # When/Then - asString (default hex)
        r = as_string(a)
        assert r == "01020304"

        # When/Then - asString with 'hex'
        r = as_string(a, "hex")
        assert r == "01020304"

        # When/Then - asString with 'utf8'
        r = as_string(a, "utf8")
        assert r == "\x01\x02\x03\x04"

        # When/Then - asString with 'base64'
        r = as_string(a, "base64")
        assert r == "AQIDBA=="

    def test_convert_from_number_array(self) -> None:
        """Given: number[] [1, 2, 3, 4]
           When: Convert using asUint8Array and asString with various encodings
           Then: Returns correct conversions for each encoding

        Reference: wallet-toolbox/src/utility/__tests/utilityHelpers.noBuffer.test.ts
                   test('1 convert from number[]')
        """
        # Given
        a = [1, 2, 3, 4]

        # When/Then - asUint8Array
        r = as_uint8_array(a)
        assert len(r) == 4
        assert all(r[i] == a[i] for i in range(len(a)))

        # When/Then - asString (default hex)
        r = as_string(a)
        assert r == "01020304"

        # When/Then - asString with 'hex'
        r = as_string(a, "hex")
        assert r == "01020304"

        # When/Then - asString with 'utf8'
        r = as_string(a, "utf8")
        assert r == "\x01\x02\x03\x04"

        # When/Then - asString with 'base64'
        r = as_string(a, "base64")
        assert r == "AQIDBA=="

    def test_convert_from_hex_string(self) -> None:
        """Given: hex string '01020304'
           When: Convert using asUint8Array and asString with various input/output encodings
           Then: Returns correct conversions for each encoding combination

        Reference: wallet-toolbox/src/utility/__tests/utilityHelpers.noBuffer.test.ts
                   test('2 convert from hex string')
        """
        # Given
        a = "01020304"

        # When/Then - asUint8Array
        r = as_uint8_array(a)
        assert len(r) == 4
        assert all(r[i] == int(a[i * 2 : i * 2 + 2], 16) for i in range(len(r)))

        # When/Then - asString (default hex)
        r = as_string(a)
        assert r == "01020304"

        # When/Then - asString with 'hex'
        r = as_string(a, "hex")
        assert r == "01020304"

        # When/Then - asString with 'hex' input and 'hex' output
        r = as_string(a, "hex", "hex")
        assert r == "01020304"

        # When/Then - asString with 'hex' input and 'utf8' output
        r = as_string(a, "hex", "utf8")
        assert r == "\x01\x02\x03\x04"

        # When/Then - asString with 'hex' input and 'base64' output
        r = as_string(a, "hex", "base64")
        assert r == "AQIDBA=="

    def test_convert_from_utf8_string(self) -> None:
        """Given: utf8 string '\x01\x02\x03\x04'
           When: Convert using asUint8Array and asString with various output encodings
           Then: Returns correct conversions for each encoding

        Reference: wallet-toolbox/src/utility/__tests/utilityHelpers.noBuffer.test.ts
                   test('3 convert from utf8 string')
        """
        # Given
        a = "\x01\x02\x03\x04"

        # When/Then - asUint8Array with 'utf8' input
        r = as_uint8_array(a, "utf8")
        assert len(r) == 4
        assert all(r[i] == i + 1 for i in range(len(r)))

        # When/Then - asString with 'utf8' input and 'hex' output
        r = as_string(a, "utf8", "hex")
        assert r == "01020304"

        # When/Then - asString with 'utf8' input (default utf8 output)
        r = as_string(a, "utf8")
        assert r == "\x01\x02\x03\x04"

        # When/Then - asString with 'utf8' input and 'utf8' output
        r = as_string(a, "utf8", "utf8")
        assert r == "\x01\x02\x03\x04"

        # When/Then - asString with 'utf8' input and 'base64' output
        r = as_string(a, "utf8", "base64")
        assert r == "AQIDBA=="
