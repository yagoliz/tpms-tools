from typing import Union, Sequence
from functools import lru_cache

@lru_cache(maxsize=256)
def _generate_crc8_table(polynomial: int) -> list[int]:
    """Generate a CRC-8 lookup table for a given polynomial.
    
    Args:
        polynomial: The polynomial to use for CRC calculation
        
    Returns:
        List of 256 pre-calculated CRC values
    """
    table = []
    for i in range(256):
        crc = i
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ polynomial) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
        table.append(crc)
    return table

def crc8(data: Union[bytes, Sequence[int]], polynomial: int = 0x07, init: int = 0x00) -> int:
    """Calculate CRC-8 for given data.
    
    This implementation matches the one used in the rtl_433 project for TPMS decoding.
    
    Args:
        data: Input data as bytes or sequence of integers
        polynomial: CRC polynomial (default 0x07 for TPMS)
        init: Initial CRC value (default 0x00)
        
    Returns:
        Calculated CRC-8 value
        
    Example:
        >>> crc8(b'123')
        113
        >>> crc8([0x01, 0x02, 0x03])
        188
    """
    if isinstance(data, bytes):
        data_bytes = data
    else:
        data_bytes = bytes(data)
    
    table = _generate_crc8_table(polynomial)
    crc = init
    
    for byte in data_bytes:
        crc = table[crc ^ byte]
    
    return crc

class CRC8:
    """Class for calculating CRC-8 with specific parameters.
    
    This class is useful when you need to calculate many CRCs with the same parameters,
    as it caches the lookup table.
    
    Example:
        >>> crc_calc = CRC8(polynomial=0x07, init=0x00)
        >>> crc_calc.calculate(b'123')
        113
    """
    
    def __init__(self, polynomial: int = 0x07, init: int = 0x00):
        """Initialize CRC-8 calculator.
        
        Args:
            polynomial: CRC polynomial
            init: Initial CRC value
        """
        self.polynomial = polynomial
        self.init = init
        self._table = _generate_crc8_table(polynomial)
    
    def calculate(self, data: Union[bytes, Sequence[int]]) -> int:
        """Calculate CRC-8 for given data.
        
        Args:
            data: Input data as bytes or sequence of integers
            
        Returns:
            Calculated CRC-8 value
        """
        return crc8(data, self.polynomial, self.init)
    
    def validate(self, data: Union[bytes, Sequence[int]], expected_crc: int) -> bool:
        """Validate data against expected CRC.
        
        Args:
            data: Input data as bytes or sequence of integers
            expected_crc: Expected CRC-8 value
            
        Returns:
            True if calculated CRC matches expected CRC
        """
        return self.calculate(data) == expected_crc

# Create default TPMS CRC calculator instance
tpms_crc8 = CRC8(polynomial=0x07, init=0x00)