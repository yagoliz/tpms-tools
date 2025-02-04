from abc import ABC, abstractmethod
from typing import List

class TPMSEncoder(ABC):
    """Base class for TPMS encoders."""
    
    @abstractmethod
    def create_packet(self, **kwargs) -> bytes:
        """Create a raw TPMS packet.
        
        Returns:
            bytes: Raw packet data
        """
        pass
    
    @abstractmethod
    def encode_message(self, **kwargs) -> List[int]:
        """Create a complete TPMS message including any encoding and preamble.
        
        Returns:
            List[int]: Binary sequence ready for modulation
        """
        pass
    
    @property
    @abstractmethod
    def protocol_name(self) -> str:
        """Get the name of the TPMS protocol."""
        pass
    
    @property
    @abstractmethod
    def default_frequency(self) -> float:
        """Get the default transmission frequency in Hz."""
        pass
    
    @property
    def required_parameters(self) -> List[str]:
        """Get the list of required parameters for this encoder."""
        pass

class ManchesterTPMSEncoder(TPMSEncoder):
    """Base class for TPMS encoders that use Manchester encoding."""
    
    def manchester_encode(self, data: bytes) -> List[int]:
        """Manchester encode the data.
        
        Args:
            data: Bytes to encode
            
        Returns:
            List[int]: Manchester encoded bits
        """
        encoded = []
        for byte in data:
            for i in range(7, -1, -1):
                bit = (byte >> i) & 1
                if bit:
                    encoded.extend([1, 0])
                else:
                    encoded.extend([0, 1])
        return encoded