import pytest
from tpms_tools.encoders.manchester import manchester_encode, manchester_decode

@pytest.fixture
def test_manchester_encode():
    """Test Manchester encoding of a simple bit sequence"""
    input_bits = "1011"
    expected = "10011010"
    assert manchester_encode(input_bits) == expected

def test_manchester_decode():
    """Test Manchester decoding of a valid sequence"""
    encoded = "10011010"
    expected = "0100"
    assert manchester_decode(encoded)[0] == expected

def test_invalid_manchester_sequence():
    """Test handling of invalid Manchester sequences"""
    invalid_sequence = "1100"  # Invalid Manchester coding
    assert manchester_decode(invalid_sequence)[0] == ""