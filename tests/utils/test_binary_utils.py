import pytest
from tpms_tools.utils.bitutils import bits_to_bytes, bytes_to_bits, bitbuffer_search, bitbuffer_invert

def test_bits_to_bytes():
    bits = "11100001"
    expected = [0xE1]

    assert bits_to_bytes(bits) == expected

def test_bits_to_bytes_fail():
    bits = "1110000"
    expected = [0xE1]

    with pytest.raises(ValueError):
        assert bits_to_bytes(bits) == expected