import pytest
from tpms_tools.encoders.manchester import manchester_encode, manchester_decode, differential_manchester_encode, differential_manchester_decode


# Regular Manchester Encoding
def test_manchester_encode():
    """Test Manchester encoding of a simple bit sequence"""
    input_bits = "1011"
    expected = "01100101"
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


def test_manchester_decode_max_bits():
    """Test Manchester decoding with a max_bits limit"""
    encoded = "100110101010"
    assert manchester_decode(encoded, max_bits=2)[0] == "01"


def test_manchester_decode_start():
    """Test Manchester decoding with a start index"""
    encoded = "100101101001"
    assert manchester_decode(encoded, start=4)[0] == "1001"


# Differential Manchester Encoding
def test_differential_manchester_encode():
    """Test differential Manchester encoding of a simple bit sequence"""
    input_bits = "1011"
    expected = "10100110"
    assert differential_manchester_encode(input_bits) == expected


def test_differential_manchester_decode():
    """Test differential Manchester decoding of a valid sequence"""
    encoded = "10100110"
    expected = "1011"
    assert differential_manchester_decode(encoded)[0] == expected