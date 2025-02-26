def crc8(data: list[int], nbytes: int, polynomial: int = 0x07, init: int = 0x00) -> int:
    """
    Calculate CRC-8 checksum of data bytes using polynomial division.

    Args:
        data: list of bytes to calculate CRC for
        nbytes: Number of bytes to process from data
        polynomial: CRC polynomial to use (default: 0x07)
        init: Initial value for CRC calculation (default: 0x00)

    Returns:
        Calculated 8-bit CRC value
    
    """
    crc = init
    for byte in data[:nbytes]:
        crc ^= byte
        for _ in range(8):
            crc = ((crc << 1) & 0xFF) ^ polynomial if crc & 0x80 else (crc << 1) & 0xFF
    return crc
