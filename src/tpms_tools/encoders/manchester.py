from typing import Tuple


def manchester_encode(data: str) -> str:
    """
    Manchester encodes a bit string. For each input bit:
    - '0' is encoded as "10"
    - '1' is encoded as "01"

    Args:
        data_str: A string of '1' and '0' representing the data bits.

    Returns:
        A Manchester-encoded bit string.
    """
    encoded = []
    for bit in data:
        if bit == "0":
            encoded.append("10")
        elif bit == "1":
            encoded.append("01")
        else:
            raise ValueError(f"Invalid bit: {bit}")
    return "".join(encoded)


def manchester_decode(bits: str, start: int = 0, max_bits: int = 0) -> Tuple[str, int]:
    """
    Decodes a Manchester-encoded bit string starting from 'start'.

    Manchester encoding represents each bit using a pair of bits (with the two bits complementary).
    The decoded bit is taken as the second bit in the pair.

    Args:
        bit_str: A string of '1' and '0' representing Manchester-encoded bits.
        start: The starting bit index for decoding.
        max_bits: If non-zero, limits decoding to max_bits output bits (i.e. max_bits pairs).

    Returns:
        A tuple (decoded_str, ipos) where:
        - decoded_str is the Manchester-decoded bit string.
        - ipos is the final bit index processed in the input.

    Decoding stops if a pair with identical bits is encountered.
    """
    decoded = []
    ipos = start
    length = len(bits)
    # If max_bits is specified, limit the length to the required number of pairs.
    if max_bits and length > start + (max_bits * 2):
        length = start + (max_bits * 2)

    while ipos <= length - 2:  # require at least 2 bits for a pair
        bit1 = bits[ipos]
        bit2 = bits[ipos + 1]
        ipos += 2

        # If both bits are the same, it's an error or termination condition.
        if bit1 == bit2:
            break

        decoded.append(bit2)

    return "".join(decoded), ipos
