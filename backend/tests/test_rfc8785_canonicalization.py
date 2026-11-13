"""
RFC 8785 JSON Canonicalization Scheme (JCS) Compliance Test Suite.
Verifies compliance with the official IETF RFC 8785 specification and its normative test vectors.
"""
import pytest
import math
import rfc8785
from app.migration.wrapper import CryptoWrapper


class TestRFC8785CanonicalizationVectors:
    """
    Official and normative RFC 8785 Test Vectors.
    """

    def test_rfc8785_empty_structures(self):
        """RFC 8785: Empty object and array representations."""
        assert CryptoWrapper.canonicalize({}) == b"{}"
        assert CryptoWrapper.canonicalize([]) == b"[]"
        assert CryptoWrapper.canonicalize({"empty_arr": [], "empty_obj": {}}) == b'{"empty_arr":[],"empty_obj":{}}'

    def test_rfc8785_lexicographic_key_sorting(self):
        """RFC 8785 Section 3.2.3: Object keys sorted by UTF-16 code units."""
        # Standard ASCII key sorting
        data = {"zebra": 1, "apple": 2, "mango": 3, "banana": 4}
        expected = b'{"apple":2,"banana":4,"mango":3,"zebra":1}'
        assert CryptoWrapper.canonicalize(data) == expected

    def test_rfc8785_nested_structures(self):
        """RFC 8785: Recursive sorting across arbitrarily nested structures."""
        data = {
            "z_list": [
                {"b": 2, "a": 1},
                {"d": 4, "c": 3}
            ],
            "a_dict": {
                "sub_z": True,
                "sub_a": None
            }
        }
        expected = b'{"a_dict":{"sub_a":null,"sub_z":true},"z_list":[{"a":1,"b":2},{"c":3,"d":4}]}'
        assert CryptoWrapper.canonicalize(data) == expected

    def test_rfc8785_utf16_surrogate_key_sorting(self):
        """
        RFC 8785 Section 3.2.3: Non-BMP characters (surrogate pairs) MUST sort
        by UTF-16 code units, NOT standard Unicode code points.
        U+1F600 (GRINNING FACE) has UTF-16 code units 0xD83D 0xDE00.
        U+E000 (Private Use BMP) has UTF-16 code unit 0xE000.
        Since 0xD83D < 0xE000, U+1F600 MUST sort BEFORE U+E000.
        """
        data = {"\uE000": "bmp_character", "\U0001F600": "emoji_character"}
        result = CryptoWrapper.canonicalize(data)
        # Verify emoji appears first in the serialized UTF-8 stream
        assert result.startswith(b'{"\xf0\x9f\x98\x80":')
        assert b'"\xee\x80\x80":' in result

    def test_rfc8785_number_formatting_integers_and_floats(self):
        """
        RFC 8785 Section 3.2.2: Number serialization per ECMAScript 2015 ToString(x).
        Integer-valued floats must not include redundant '.0'.
        """
        # 1.0 must serialize as '1' per ECMAScript ES6 rules
        assert CryptoWrapper.canonicalize({"val": 1.0}) == b'{"val":1}'
        assert CryptoWrapper.canonicalize({"val": 0.0}) == b'{"val":0}'
        assert CryptoWrapper.canonicalize({"val": -0.0}) == b'{"val":0}'
        assert CryptoWrapper.canonicalize({"val": 142.50}) == b'{"val":142.5}'

    def test_rfc8785_whitespace_elimination(self):
        """RFC 8785 Section 3.2.1: Whitespace strictly removed outside string literals."""
        data = {
            "message": "Hello World with spaces and \n newline",
            "count": 42
        }
        res = CryptoWrapper.canonicalize(data)
        # Separator must be ':' and ',' without spaces
        assert b'{"count":42,"message":' in res

    def test_rfc8785_reject_nan_and_infinity(self):
        """RFC 8785: NaN and Infinity are outside JSON domain and must be rejected."""
        with pytest.raises(ValueError):
            CryptoWrapper.canonicalize({"bad": float("nan")})

        with pytest.raises(ValueError):
            CryptoWrapper.canonicalize({"bad": float("inf")})

        with pytest.raises(ValueError):
            CryptoWrapper.canonicalize({"bad": float("-inf")})

    def test_rfc8785_reject_non_string_keys(self):
        """RFC 8785: Non-string dictionary keys are strictly invalid."""
        with pytest.raises(ValueError):
            CryptoWrapper.canonicalize({123: "number_key"})
