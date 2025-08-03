from abc import ABC, abstractmethod
from typing import ClassVar


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
    def encode_message(self, **kwargs) -> list[int]:
        """Create a complete TPMS message including any encoding and preamble.

        Returns:
            List[int]: Binary sequence ready for modulation
        """
        pass

    @abstractmethod
    def pulse_encode_message(self, **kwargs) -> list[tuple[int, int]]:
        """Create the pulse encoding (PCM, PPM) before PHY modulation

        Returns:
            List[Tuple(int, int)]: Tuple with long/short pulses
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
    def required_parameters(self) -> list[str]:
        """Get the list of required parameters for this encoder."""
        pass
