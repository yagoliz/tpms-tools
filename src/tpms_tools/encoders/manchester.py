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


def differential_manchester_encode(data: str) -> str:
    """
    Encode a binary string using differential Manchester encoding.
    Returns the encoded signal as a string of '1's and '0's.
    """
    if not data:
        return ""
        
    result = []
    last_level = 1  # Start with high level
    
    for bit in data:
        if bit == '1':
            # For 1, maintain the same level at transition
            result.append(str(last_level))
            result.append(str(1 - last_level))
            last_level = 1 - last_level
        else:  # bit == '0'
            # For 0, change the level at transition
            result.append(str(1 - last_level))
            result.append(str(last_level))
            
    return ''.join(result)


def differential_manchester_decode(bits: str, start: int = 0, max_bits: int = 0) -> Tuple[str, int]:
    """
    Decodes a Differential Manchester-encoded bit string starting from 'start'.

    Differential Manchester encoding represents each bit using a pair of bits (with the two bits complementary).
    The decoded bit is taken as the second bit in the pair.

    Args:
        bit_str: A string of '1' and '0' representing Differential Manchester-encoded bits.
        start: The starting bit index for decoding.
        max_bits: If non-zero, limits decoding to max_bits output bits (i.e. max_bits pairs).

    Returns:
        A tuple (decoded_str, ipos) where:
        - decoded_str is the Differential Manchester-decoded bit string.
        - ipos is the final bit index processed in the input.

    Decoding stops if a pair with different bits is encountered.
    """
    if not bits or len(bits) < 2:
        return ""
    
    result = []
    ipos = start
    bit2 = None  # Previous bit state

    # If max_bits is specified, limit the length to the required number of pairs.
    length = len(bits)
    if max_bits and length > start + (max_bits * 2):
        length = start + (max_bits * 2)
    
    # Find initial synchronization
    while ipos < length - 2:
        bit1 = int(bits[ipos])
        bit2 = int(bits[ipos + 1])
        bit3 = int(bits[ipos + 2])
        
        if bit1 != bit2:  # Found transition
            if bit2 != bit3:  # Another transition
                result.append('0')
                ipos += 2
            else:
                bit2 = bit1
                ipos += 1
                break
        else:
            bit2 = 1 - bit1
            break
    
    # Decode the rest of the bits
    while ipos < len(bits) - 1:
        bit1 = int(bits[ipos])
        if bit1 == bit2:
            break  # Clock missing, abort
            
        bit2 = int(bits[ipos + 1])
        result.append('1' if bit1 == bit2 else '0')
        ipos += 2
        
    return ''.join(result)


