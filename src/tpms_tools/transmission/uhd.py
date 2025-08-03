import time
from typing import Optional, Union
import numpy as np
import uhd
from .base import BaseTransmitter


class UHDTransmitterError(Exception):
    """Base exception for UHD transmitter errors."""
    pass


class UHDDeviceError(UHDTransmitterError):
    """Exception raised for device-related errors."""
    pass


class UHDConfigError(UHDTransmitterError):
    """Exception raised for configuration-related errors."""
    pass


class UHDTransmitter(BaseTransmitter):
    """Class for transmitting signals using UHD-compatible USRP devices."""

    def __init__(
        self,
        center_freq: float,
        sample_rate: float,
        gain: float = 60,
        device_args: str = "",
        channel: int = 0,
        antenna: Optional[str] = None,
    ):
        """
        Initialize UHD transmitter.

        Args:
            center_freq: Center frequency in Hz
            sample_rate: Sample rate in Hz
            gain: Transmission gain in dB
            device_args: UHD device arguments (e.g., "type=b200")
            channel: Channel number to use
            antenna: Specific antenna to use (device-dependent)

        Raises:
            UHDDeviceError: If device initialization fails
            UHDConfigError: If device configuration fails
        """
        self.sample_rate = sample_rate
        self.center_freq = center_freq
        self.gain = gain
        self.channel = channel

        try:
            self.usrp = uhd.usrp.MultiUSRP(device_args)
        except ImportError as e:
            raise UHDDeviceError("UHD Python bindings not installed") from e
        except Exception as e:
            raise UHDDeviceError(f"Failed to initialize USRP device: {str(e)}") from e

        try:
            self._configure_device(antenna)
        except Exception as e:
            raise UHDConfigError(f"Failed to configure USRP device: {str(e)}") from e

        self.tx_streamer = None

    def _configure_device(self, antenna: Optional[str]) -> None:
        """Configure USRP device with specified parameters."""
        self.usrp.set_tx_rate(self.sample_rate, self.channel)
        self.usrp.set_tx_freq(self.center_freq, self.channel)
        self.usrp.set_tx_gain(self.gain, self.channel)
        
        if antenna:
            self.usrp.set_tx_antenna(antenna, self.channel)

    def start_streaming(self) -> None:
        """Start the transmission stream."""
        if self.tx_streamer is not None:
            return

        try:
            st_args = uhd.usrp.StreamArgs("fc32", "sc16")
            st_args.channels = [self.channel]
            self.tx_streamer = self.usrp.get_tx_stream(st_args)
        except Exception as e:
            self.tx_streamer = None
            raise UHDDeviceError(f"Failed to start streaming: {str(e)}") from e

    def stop_streaming(self) -> None:
        """Stop the transmission stream."""
        if self.tx_streamer is None:
            return
        
        try:
            self.tx_streamer.send(np.array([], dtype=np.complex64), uhd.types.TXMetadata())
        finally:
            self.tx_streamer = None

    def prepare_samples(
        self, samples: Union[np.ndarray, list[float]], scale: float = 0.8
    ) -> np.ndarray:
        """
        Prepare samples for transmission.

        Args:
            samples: Real-valued samples to transmit
            scale: Scaling factor to prevent clipping

        Returns:
            Complex samples ready for transmission
        """
        if not isinstance(samples, np.ndarray):
            samples = np.array(samples)

        if np.max(np.abs(samples)) > 0:
            samples = samples / np.max(np.abs(samples)) * scale

        if samples.dtype != np.complex64:
            samples = samples.astype(np.complex64)

        return samples

    def transmit_samples(
        self,
        samples: Union[np.ndarray, list[float]],
        repeat: int = 1,
        scale: float = 0.8,
        gap_time: float = 0.1,
    ) -> None:
        """
        Transmit samples using the USRP.

        Args:
            samples: Samples to transmit
            repeat: Number of times to repeat transmission
            scale: Scaling factor to prevent clipping
            gap_time: Gap between repetitions in seconds

        Raises:
            UHDTransmitterError: If transmission fails
        """
        tx_samples = self.prepare_samples(samples, scale)

        if self.tx_streamer is None:
            self.start_streaming()

        try:            
            for i in range(repeat):
                md = uhd.types.TXMetadata()
                md.end_of_burst = True
                
                # UHD expects 2D array format: (num_channels, num_samples)
                samples_2d = tx_samples.reshape(1, -1)
                self.tx_streamer.send(samples_2d, md)
                
                if i < repeat - 1 and gap_time > 0:
                    time.sleep(gap_time)

        except Exception as e:
            raise UHDTransmitterError(f"Transmission failed: {str(e)}") from e
        finally:
            self.stop_streaming()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.stop_streaming()