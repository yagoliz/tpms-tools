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
    def required_parameters(self) -> list[str]:
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
        target_length: int = None,
        padding_method: str = "repeat",
        padding_data: list = None,
    ) -> list[int]:
        """Create a complete TPMS message including preamble and Manchester encoding.
        
        Args:
            sensor_id: TPMS sensor ID
            pressure_kpa: Tire pressure in kPa
            temperature_c: Temperature in Celsius
            flags: Optional flags field (default: 54)
            extra: Optional extra/unknown field (default: 48153)
            target_length: Optional target packet length in bytes (default: 9 for standard packet)
            padding_method: Method for extending packet ("repeat", "zero", "random", "custom")
            padding_data: Custom padding data when using "custom" method
            
        Returns:
            Complete TPMS message ready for transmission
        """
        
        # If target_length is specified, use extended message functionality
        if target_length is not None:
            return self.encode_extended_message(
                sensor_id, pressure_kpa, temperature_c, target_length,
                flags, extra, padding_method, padding_data
            )

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

    def create_extended_packet(self, fields: dict, target_length: int) -> str:
        """
        Create an extended packet of arbitrary length.
        
        Args:
            fields: Dictionary containing packet fields
            target_length: Target length in bytes for the packet data
            
        Returns:
            Manchester-encoded bit string of extended packet
        """
        if target_length < 9:
            raise ValueError("Extended packet must be at least 9 bytes (original packet size)")
        
        # Create the original 9-byte packet
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
        
        # Extend the packet to target length
        extended_packet = b.copy()
        
        # Add padding/repeated data to reach target length
        padding_method = fields.get("padding_method", "repeat")
        
        if padding_method == "repeat":
            # Repeat the original packet data (excluding CRC)
            original_data = b[:8]
            while len(extended_packet) < target_length - 1:  # -1 for final CRC
                bytes_to_add = min(8, target_length - 1 - len(extended_packet))
                extended_packet.extend(original_data[:bytes_to_add])
        elif padding_method == "zero":
            # Pad with zeros
            while len(extended_packet) < target_length - 1:
                extended_packet.append(0x00)
        elif padding_method == "random":
            # Pad with pseudo-random data based on sensor ID
            import random
            random.seed(fields["id"])
            while len(extended_packet) < target_length - 1:
                extended_packet.append(random.randint(0, 255))
        elif padding_method == "custom":
            # Use custom padding data if provided
            custom_data = fields.get("padding_data", [0x00])
            custom_idx = 0
            while len(extended_packet) < target_length - 1:
                extended_packet.append(custom_data[custom_idx % len(custom_data)])
                custom_idx += 1
        
        # Recalculate CRC for the extended packet
        if len(extended_packet) == target_length - 1:
            extended_packet.append(crc8(extended_packet, len(extended_packet), polynomial=0x07, init=0x00))
        
        # Convert to bits and Manchester encode
        packet_bit_str = bytes_to_bits(extended_packet)
        encoded = manchester_encode(packet_bit_str)
        return encoded

    def encode_extended_message(
        self,
        sensor_id: int,
        pressure_kpa: float,
        temperature_c: int,
        target_length: int,
        flags: int = None,
        extra: int = None,
        padding_method: str = "repeat",
        padding_data: list = None,
    ) -> list[int]:
        """Create an extended TPMS message of arbitrary length."""
        
        # Create the extended packet
        new_packet = {
            "flags": 54 if flags is None else flags,
            "id": sensor_id,
            "pressure_raw": int(pressure_kpa / 0.75),
            "temp_c": temperature_c,
            "unknown": 48153 if extra is None else extra,
            "padding_method": padding_method,
            "padding_data": padding_data or [0x00],
        }

        encoded = self.create_extended_packet(new_packet, target_length)

        # Invert the full message
        transmitted = bitbuffer_invert(encoded)
        return self.PREAMBLE + transmitted

    def get_packet_length_info(self, bit_sequence: list[int]) -> dict:
        """Get information about the packet length and structure.
        
        Args:
            bit_sequence: The complete bit sequence including preamble
            
        Returns:
            Dictionary with packet length information
        """
        preamble_len = len(self.PREAMBLE)
        if len(bit_sequence) <= preamble_len:
            return {"error": "Bit sequence too short"}
        
        # Remove preamble and calculate packet info
        packet_bits = bit_sequence[preamble_len:]
        # Manchester encoding doubles the bit count
        packet_bytes = len(packet_bits) // 16  # 8 bits per byte * 2 for Manchester
        
        return {
            "total_bits": len(bit_sequence),
            "preamble_bits": preamble_len,
            "packet_bits": len(packet_bits),
            "packet_bytes": packet_bytes,
            "is_extended": packet_bytes > 9,
            "extension_bytes": max(0, packet_bytes - 9)
        }

    @staticmethod
    def calculate_target_length_for_duration(duration_ms: float, bit_duration_us: int = 52) -> int:
        """Calculate target packet length needed for specific transmission duration.
        
        Args:
            duration_ms: Desired transmission duration in milliseconds
            bit_duration_us: Bit duration in microseconds (default: 52 for Renault)
            
        Returns:
            Target packet length in bytes
        """
        # Convert duration to microseconds
        duration_us = duration_ms * 1000
        
        # Calculate total bits needed
        total_bits_needed = duration_us / bit_duration_us
        
        # Account for preamble (32 bits) and Manchester encoding (doubles bits)
        preamble_bits = 32
        packet_bits_needed = total_bits_needed - preamble_bits
        packet_bytes_needed = packet_bits_needed / 16  # 8 bits per byte * 2 for Manchester
        
        # Round up to nearest byte and ensure minimum size
        return max(9, int(packet_bytes_needed) + 1)
