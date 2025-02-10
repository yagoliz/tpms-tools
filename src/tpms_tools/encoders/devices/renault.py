from typing import List
from ..base import TPMSEncoder
from ..manchester import manchester_encode
from ...utils.crc8 import crc8
from ...utils.bitutils import bytes_to_bits, bitbuffer_invert


class RenaultTPMSEncoder(TPMSEncoder):
    """Encoder for Renault TPMS protocol."""

    PREAMBLE = bytes_to_bits([0x55, 0x55, 0x55, 0x56])
    BIT_DURATION = 52
    SHORT_WIDTH = 1
    LONG_WIDTH = 1

    @property
    def protocol_name(self) -> str:
        return "Renault"

    @property
    def default_frequency(self) -> float:
        return 433.92e6  # 433.92 MHz

    @property
    def required_parameters(self) -> List[str]:
        return ["sensor_id", "pressure_kpa", "temperature_c"]

    def create_packet(self, fields: dict) -> str:
        """
        Encodes a TPMS Renault message into a Manchester-encoded bit string.

        Expected keys in fields:
        - flags         : integer (upper 6 bits stored in b[0])
        - id            : integer (stored little-endian in b[3], b[4], b[5])
        - pressure_raw  : integer (stored using b[0] lower 2 bits and b[1])
        - temp_c        : integer (stored as value+30 in b[2])
        - unknown       : integer (little-endian in b[6], b[7])

        Computes CRC8 over the first 8 bytes and stores it in b[8].

        Returns Manchester-encoded bit string.
        """
        b = [0] * 9
        b[0] = ((fields["flags"] & 0xFF) << 2) | ((fields["pressure_raw"] >> 8) & 0x03)
        b[1] = fields["pressure_raw"] & 0xFF
        b[2] = (fields["temp_c"] + 30) & 0xFF
        b[3] = fields["id"] & 0xFF
        b[4] = (fields["id"] >> 8) & 0xFF
        b[5] = (fields["id"] >> 16) & 0xFF
        b[6] = fields["unknown"] & 0xFF
        b[7] = (fields["unknown"] >> 8) & 0xFF
        b[8] = crc8(b, 8, polynomial=0x07, init=0x00)
        packet_bit_str = bytes_to_bits(b)
        encoded = manchester_encode(packet_bit_str)
        return encoded

    def encode_message(
        self,
        sensor_id: int,
        pressure_kpa: float,
        temperature_c: int,
        flags: int = None,
        extra: int = None,
    ) -> List[int]:
        """Create a complete TPMS message including preamble and Manchester encoding."""

        # Create the basic packet
        new_packet = {
            "flags": 54 if flags is None else flags,
            "id": sensor_id,
            "pressure_raw": int(pressure_kpa / 0.75),
            "temp_c": temperature_c,
            "unknown": 48153 if extra is None else extra,
        }

        encoded = self.create_packet(new_packet)

        # Invert the full message
        transmitted = bitbuffer_invert(encoded)
        return self.PREAMBLE + transmitted
