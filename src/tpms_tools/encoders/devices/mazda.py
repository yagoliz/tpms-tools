from ..base import TPMSEncoder
from ..manchester import manchester_encode
from ...utils.bitutils import bytes_to_bits, bitbuffer_invert, xor_bytes


class MazdaTPMSEncoder(TPMSEncoder):
    """Encoder for Mazda/Abarth-124 TPMS protocol."""

    PREAMBLE = bytes_to_bits([0x55, 0x55, 0x56])
    BIT_DURATION = 52
    SHORT_WIDTH = 1
    LONG_WIDTH = 1

    @property
    def protocol_name(self) -> str:
        return "Mazda"

    @property
    def default_frequency(self) -> float:
        return 433.92e6  # 433.92 MHz

    @property
    def required_parameters(self) -> list[str]:
        return ["sensor_id", "pressure_kpa", "temperature_c"]

    def create_packet(self, fields: dict) -> str:
        """
        Encodes a TPMS Mazda/Abarth message into a Manchester-encoded bit string.

        Expected keys in fields:
        - id            : integer (32-bit stored b[0] to b[3] big endian)
        - flags         : unknown value (stored in b[4])
        - pressure_raw  : integer (stored in b[5] divided by 1.38)
        - temp_c        : integer (stored as value+50 in b[6])
        - status        : unknown value (stored in b[7])
        - checksum      : 8 bit checksum (xor_bytes 0 to 7)

        Computes CRC8 over the first 8 bytes and stores it in b[8].

        Returns Manchester-encoded bit string.
        """
        b = [0] * 9
        b[0] = (fields["id"] >> 24) & 0xFF
        b[1] = (fields["id"] >> 16) & 0xFF
        b[2] = (fields["id"] >> 8) & 0xFF
        b[3] = fields["id"] & 0xFF
        b[4] = fields["flags"] & 0xFF
        b[5] = int(fields["pressure_raw"] / 1.38) & 0xFF
        b[6] = (fields["temp_c"] + 50) & 0xFF
        b[7] = fields["unknown"] & 0xFF
        b[8] = xor_bytes(b[0:8])
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
    ) -> list[int]:
        """Create a complete TPMS message including preamble and Manchester encoding."""

        # Create the basic packet
        new_packet = {
            "flags": 80 if flags is None else flags,
            "id": sensor_id,
            "pressure_raw": int(pressure_kpa),
            "temp_c": temperature_c,
            "unknown": 1 if extra is None else extra,
        }

        encoded = self.create_packet(new_packet)

        # Invert the full message
        transmitted = bitbuffer_invert(encoded)
        return self.PREAMBLE + transmitted
    

    def pulse_encode_message(
        self,
        tpms_bits: list[int]
    ) -> list[tuple[int, int]]:
        return self.pcm.encode_pcm_signal([int(b) for b in tpms_bits])
