def bytes_to_bits(byte_arr: list[int]) -> str:
    """
    Converts a list of integer bytes to a bit string (MSB first for each byte).
    """
    return "".join(format(b, "08b") for b in byte_arr)


def bits_to_bytes(bit_str: str) -> list[int]:
    """
    Converts a bit string (whose length is a multiple of 8) into a list of integer bytes.
    """
    if len(bit_str) % 8 != 0:
        raise ValueError("Bit string length must be a multiple of 8")
    return [int(bit_str[i : i + 8], 2) for i in range(0, len(bit_str), 8)]


def bitbuffer_search(bit_str: str, pattern: str, start: int = 0) -> int:
    """
    Searches for a given bit pattern within a bit string starting from 'start'.

    Args:
        bit_str: The bit string to search in (composed of '0' and '1').
        pattern: The bit pattern to search for (also a string of '0' and '1').
        start: The index in bit_str to start searching from.

    Returns:
        The starting index where the pattern is found, or -1 if not found.
    """
    return bit_str.find(pattern, start)


def bitbuffer_invert(bit_str: str) -> str:
    """
    Inverts a bit string: '0' becomes '1', and '1' becomes '0'.

    Args:
        bit_str: A string of '1' and '0'.

    Returns:
        A new string with each bit inverted.
    """
    return "".join("1" if b == "0" else "0" for b in bit_str)
