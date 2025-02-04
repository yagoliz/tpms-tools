from typing import List
from .base import ManchesterTPMSEncoder
from ..modulation.utils import crc8

class RenaultTPMSEncoder(ManchesterTPMSEncoder):
    """Encoder for Renault TPMS protocol."""
    
    PREAMBLE = bytes([0xaa, 0xaa, 0xaa, 0xa9])
    
    @property
    def protocol_name(self) -> str:
        return "Renault"
    
    @property
    def default_frequency(self) -> float:
        return 433.92e6  # 433.92 MHz
    
    @property
    def required_parameters(self) -> List[str]:
        return ["sensor_id", "pressure_kpa", "temperature_c"]
    
    def create_packet(self, sensor_id: int, pressure_kpa: float, 
                     temperature_c: float, flags: int = 0xd0) -> bytes:
        """Create a TPMS packet with the given parameters."""
        # Convert pressure to raw value (pressure_kpa / 0.75)
        pressure_raw = int(pressure_kpa / 0.75)
        pressure_msb = (pressure_raw >> 8) & 0x03
        pressure_lsb = pressure_raw & 0xFF
        
        # Convert temperature (offset +30)
        temp_raw = int(temperature_c + 30) & 0xFF
        
        # Create the packet (9 bytes)
        packet = bytearray(9)
        packet[0] = (flags << 2) | pressure_msb
        packet[1] = pressure_lsb
        packet[2] = temp_raw
        packet[3] = sensor_id & 0xFF
        packet[4] = (sensor_id >> 8) & 0xFF
        packet[5] = (sensor_id >> 16) & 0xFF
        packet[6] = 0xFF
        packet[7] = 0xFF
        
        # Calculate and append CRC
        packet[8] = crc8(packet[:8])
        
        return bytes(packet)
    
    def encode_message(self, sensor_id: int, pressure_kpa: float, 
                      temperature_c: float, flags: int = 0xd0) -> List[int]:
        """Create a complete TPMS message including preamble and Manchester encoding."""
        # Create the basic packet
        packet = self.create_packet(sensor_id, pressure_kpa, temperature_c, flags)
        
        # Convert preamble to bits
        preamble_bits = []
        for byte in self.PREAMBLE:
            for i in range(7, -1, -1):
                preamble_bits.append((byte >> i) & 1)
        
        # Manchester encode the packet
        packet_bits = self.manchester_encode(packet)
        
        # Combine preamble and packet
        return preamble_bits + packet_bits