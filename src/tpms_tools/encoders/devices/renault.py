from ..base import TPMSEncoder
from ..manchester import manchester_encode
from ..pcm import PCMEncoder
from ...utils.crc8 import crc8
from ...utils.bitutils import bytes_to_bits, bitbuffer_invert


class RenaultTPMSEncoder(TPMSEncoder):
    """Encoder for Renault TPMS protocol."""

    PREAMBLE = bytes_to_bits([0x55, 0x55, 0x55, 0x56])
    BIT_DURATION = 52
    SHORT_WIDTH = 1
    LONG_WIDTH = 1

    pcm = PCMEncoder(short=1, long=1)

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
    ) -> list[int]:
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
        full_message = self.PREAMBLE + transmitted
        # Convert to list of integers for consistency
        return [int(bit) for bit in full_message]
    
    def pulse_encode_message(
        self,
        tpms_bits: list[int]
    ) -> list[tuple[int, int]]:
        return self.pcm.encode_pcm_signal([int(b) for b in tpms_bits])
    
    def encode_message_with_length(
        self,
        sensor_id: int,
        pressure_kpa: float,
        temperature_c: int,
        target_length: int,
        padding_method: str = "repeat",
        padding_data: list = None,
        flags: int = None,
        extra: int = None,
    ) -> list[int]:
        """Create a TPMS message with specified length using padding/truncation."""
        
        # First create the normal message
        base_message = self.encode_message(
            sensor_id=sensor_id,
            pressure_kpa=pressure_kpa,
            temperature_c=temperature_c,
            flags=flags,
            extra=extra
        )
        
        current_length = len(base_message)
        
        if current_length == target_length:
            return base_message
        elif current_length < target_length:
            # Need to pad the message
            padding_needed = target_length - current_length
            
            if padding_method == "zero":
                padding = [0] * padding_needed
            elif padding_method == "random":
                import random
                padding = [random.randint(0, 1) for _ in range(padding_needed)]
            elif padding_method == "custom" and padding_data:
                # Repeat the custom padding data as needed
                padding = []
                for i in range(padding_needed):
                    bit_val = padding_data[i % len(padding_data)]
                    # Ensure we have integer values 0 or 1
                    padding.append(1 if bit_val else 0)
            else:  # "repeat" method (default)
                # Repeat the last bit pattern
                if current_length > 0:
                    last_bit = base_message[-1]
                    padding = [last_bit] * padding_needed
                else:
                    padding = [0] * padding_needed
            
            return base_message + padding
        else:
            # Need to truncate the message
            return base_message[:target_length]
    
    def get_packet_length_info(self, encoded_bits: list) -> dict:
        """Get information about the packet length and timing."""
        if not encoded_bits:
            return {'length': 0, 'duration': 0.0}
        
        length = len(encoded_bits)
        duration_ms = length * self.BIT_DURATION / 1000.0
        
        return {
            'length': length,
            'duration': duration_ms,
            'bit_duration_us': self.BIT_DURATION,
            'preamble_length': len(self.PREAMBLE),
            'data_length': length - len(self.PREAMBLE) if length > len(self.PREAMBLE) else 0
        }
    
    def calculate_target_length_for_duration(self, duration_ms: float) -> int:
        """Calculate target packet length for a given duration in milliseconds."""
        return int(duration_ms * 1000 / self.BIT_DURATION)
