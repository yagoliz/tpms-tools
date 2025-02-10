from typing import List


def crc8(data: List[int], nbytes: int, polynomial: int = 0x07, init: int = 0x00) -> int:
    crc = init
    for byte in data[:nbytes]:
        crc ^= byte
        for _ in range(8):
            crc = ((crc << 1) & 0xFF) ^ polynomial if crc & 0x80 else (crc << 1) & 0xFF
    return crc
