from abc import ABC, abstractmethod
from typing import List, ClassVar


class TPMSEncoder(ABC):
    """Base class for TPMS encoders."""

    PREAMBLE: ClassVar[str]
    BIT_DURATION: ClassVar[int]

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
