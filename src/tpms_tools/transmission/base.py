from abc import ABC, abstractmethod
from typing import Union, Optional
import numpy as np


class BaseTransmitter(ABC):
    """Abstract base class for all transmitters."""

    @abstractmethod
    def transmit_samples(
        self,
        samples: Union[np.ndarray, list[float]],
        repeat: int = 1,
        scale: float = 0.8,
        gap_time: float = 0.1,
    ) -> None:
        """Transmit samples."""
        pass

    @abstractmethod
    def prepare_samples(
        self, samples: Union[np.ndarray, list[float]], scale: float = 0.8
    ) -> np.ndarray:
        """Prepare samples for transmission."""
        pass

    @abstractmethod
    def __enter__(self):
        """Context manager entry."""
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        pass


class TransmitterFactory:
    """Factory for creating transmitter instances."""

    @staticmethod
    def create_transmitter(
        transmitter_type: str,
        center_freq: float,
        sample_rate: float,
        gain: float = 60,
        device_args: str = "",
        channel: int = 0,
        antenna: Optional[str] = None,
    ) -> BaseTransmitter:
        """
        Create a transmitter instance.

        Args:
            transmitter_type: "soapy" or "uhd"
            center_freq: Center frequency in Hz
            sample_rate: Sample rate in Hz
            gain: Transmission gain in dB
            device_args: Device-specific arguments
            channel: Channel number
            antenna: Antenna selection

        Returns:
            Transmitter instance

        Raises:
            ValueError: If transmitter type is unsupported
        """
        if transmitter_type.lower() == "soapy":
            from .sdr import SDRTransmitter
            return SDRTransmitter(
                center_freq, sample_rate, gain, device_args, channel, antenna
            )
        elif transmitter_type.lower() == "uhd":
            from .uhd import UHDTransmitter
            return UHDTransmitter(
                center_freq, sample_rate, gain, device_args, channel, antenna
            )
        else:
            raise ValueError(f"Unsupported transmitter type: {transmitter_type}")

    @staticmethod
    def get_available_types() -> list[str]:
        """Get list of available transmitter types."""
        types = []
        
        try:
            import SoapySDR
            types.append("soapy")
        except ImportError:
            pass
            
        try:
            import uhd
            types.append("uhd")
        except ImportError:
            pass
            
        return types