from ..base import TPMSEncoder
from ..manchester import differential_manchester_encode
from ...utils.crc8 import crc8
from ...utils.bitutils import bytes_to_bits


class ToyotaTPMSEncoder(TPMSEncoder):
    """Encoder for Renault TPMS protocol."""

    PREAMBLE = bytes_to_bits([0x55, 0x3c])
    BIT_DURATION = 52
    SHORT_WIDTH = 1
    LONG_WIDTH = 1

    @property
    def protocol_name(self) -> str:
        return "Toyota"

    @property
    def default_frequency(self) -> float:
        return 433.92e6  # 433.92 MHz

    @property
    def required_parameters(self) -> list[str]:
        return ["sensor_id", "pressure_kpa", "temperature_c"]

    def create_packet(self, fields: dict) -> str:
        """
        Encode Toyota TPMS sensor data into packet bytes.
        
        Args:
            id_hex: 8-character hex string of sensor ID
            status: Status value (7 bits valid data + 1 bit status)
            pressure_psi: Pressure in PSI
            temperature_c: Temperature in Celsius
        
        Returns:
            9-byte packet including CRC
        """
        # Unpacking the values
        id_val = fields["id"]
        pressure_raw = int((fields["pressure_raw"] + 7.0) * 4)  # Reverse of pressure1*0.25-7.0
        temp_raw = int(fields["temp_c"] + 40.0)  # Reverse of temp-40.0
        status = 1

        b = [0] * 9

        # ID bytes (4 bytes)
        b[0] = (id_val >> 24) & 0xFF
        b[1] = (id_val >> 16) & 0xFF
        b[2] = (id_val >> 8) & 0xFF
        b[3] = id_val & 0xFF

        # Status & pressure byte 4
        b[4] = (1 & 0x80) | (pressure_raw >> 1 & 0x7F)

        # Temperature and pressure1 remainder (byte 5)
        b[5] = ((pressure_raw & 0x1) << 7) | (temp_raw >> 1 & 0x7F)
        
        # Status bits and temperature remainder (byte 6)
        b[6] = ((temp_raw & 0x1) << 7) | (status & 0x7F)
        
        # Pressure2 (inverted pressure1) (byte 7)
        b[7] = pressure_raw ^ 0xFF
        
        # Calculate CRC (byte 8)
        b[8] = crc8(b, nbytes=8, polynomial=0x07, init=0x80)

        packet_bit_str = bytes_to_bits(b)

        # We do differential Manchester encoding and return the packet
        encoded = differential_manchester_encode(packet_bit_str)
        return "01" + encoded # Add the start bit as well

    def encode_message(
        self,
        sensor_id: int,
        pressure_kpa: float,
        temperature_c: int,
        flags: int = None,
    ) -> list[int]:
        """Create a complete TPMS message including preamble and differential Manchester encoding."""

        # Create the basic packet
        new_packet = {
            "flags": 54 if flags is None else flags,
            "id": sensor_id,
            "pressure_raw": int(pressure_kpa),
            "temp_c": temperature_c,
        }

        # Let's encode the packet and add the preamble
        encoded = self.create_packet(new_packet)
        return self.PREAMBLE + encoded

    def pulse_encode_message(
        self,
        tpms_bits: list[int]
    ) -> list[tuple[int, int]]:
        return self.pcm.encode_pcm_signal([int(b) for b in tpms_bits])