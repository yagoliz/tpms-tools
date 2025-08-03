import time
from typing import Optional, Union
import numpy as np
import SoapySDR
from SoapySDR import SOAPY_SDR_TX, SOAPY_SDR_CF32
from .base import BaseTransmitter


class SDRTransmitterError(Exception):
    """Base exception for SDR transmitter errors."""

    pass


class SDRDeviceError(SDRTransmitterError):
    """Exception raised for device-related errors."""

    pass


class SDRConfigError(SDRTransmitterError):
    """Exception raised for configuration-related errors."""

    pass


class SDRTransmitter(BaseTransmitter):
    """Class for transmitting signals using SoapySDR-compatible devices."""

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
        Initialize SDR transmitter.

        Args:
            center_freq: Center frequency in Hz
            sample_rate: Sample rate in Hz
            gain: Transmission gain in dB
            device_args: SoapySDR device arguments (e.g., "driver=hackrf")
            channel: Channel number to use
            antenna: Specific antenna to use (device-dependent)

        Raises:
            SDRDeviceError: If device initialization fails
            SDRConfigError: If device configuration fails
        """
        self.sample_rate = sample_rate
        self.center_freq = center_freq
        self.gain = gain
        self.channel = channel

        try:
            # Create device instance
            self.sdr = SoapySDR.Device(device_args)
        except Exception as e:
            raise SDRDeviceError(f"Failed to initialize SDR device: {str(e)}") from e

        try:
            # Configure device
            self._configure_device(antenna)
        except Exception as e:
            self.sdr = None
            raise SDRConfigError(f"Failed to configure SDR device: {str(e)}") from e

        self.tx_stream = None

    def _configure_device(self, antenna: Optional[str]) -> None:
        """Configure SDR device with specified parameters."""
        # Set sample rate
        self.sdr.setSampleRate(SOAPY_SDR_TX, self.channel, self.sample_rate)

        # Set center frequency
        self.sdr.setFrequency(SOAPY_SDR_TX, self.channel, self.center_freq)

        # Set gain
        self.sdr.setGain(SOAPY_SDR_TX, self.channel, self.gain)

        # Set antenna if specified
        if antenna:
            self.sdr.setAntenna(SOAPY_SDR_TX, self.channel, antenna)

    def start_streaming(self) -> None:
        """Start the transmission stream.

        Raises:
            SDRDeviceError: If stream setup fails
        """
        if self.tx_stream is not None:
            return

        try:
            self.tx_stream = self.sdr.setupStream(SOAPY_SDR_TX, SOAPY_SDR_CF32)
            self.sdr.activateStream(self.tx_stream)
        except Exception as e:
            self.tx_stream = None
            raise SDRDeviceError(f"Failed to start streaming: {str(e)}") from e

    def stop_streaming(self) -> None:
        """Stop the transmission stream."""
        if self.tx_stream is None:
            return

        try:
            self.sdr.deactivateStream(self.tx_stream)
            self.sdr.closeStream(self.tx_stream)
        finally:
            self.tx_stream = None

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
        # Convert to numpy array if needed
        if not isinstance(samples, np.ndarray):
            samples = np.array(samples)

        # Normalize
        if np.max(np.abs(samples)) > 0:
            samples = samples / np.max(np.abs(samples)) * scale

        # Convert to complex samples if real
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
        Transmit samples using the SDR.

        Args:
            samples: Samples to transmit
            repeat: Number of times to repeat transmission
            scale: Scaling factor to prevent clipping
            gap_time: Gap between repetitions in seconds

        Raises:
            SDRTransmitterError: If transmission fails
        """
        # Prepare samples
        tx_samples = self.prepare_samples(samples, scale)

        # Start streaming if needed
        if self.tx_stream is None:
            self.start_streaming()

        try:
            # Transmit desired number of times
            for i in range(repeat):
                # Send samples in chunks to avoid buffer issues
                chunk_size = 32768  # Adjust based on device
                for j in range(0, len(tx_samples), chunk_size):
                    chunk = tx_samples[j : j + chunk_size]
                    rc = self.sdr.writeStream(
                        self.tx_stream, [chunk], len(chunk), timeoutUs=1000000
                    )
                    if rc.ret != len(chunk):
                        raise SDRTransmitterError(
                            f"Failed to write all samples: {rc.ret} != {len(chunk)}"
                        )

                # Wait between repetitions
                if i < repeat - 1 and gap_time > 0:
                    time.sleep(gap_time)

        except Exception as e:
            raise SDRTransmitterError(f"Transmission failed: {str(e)}") from e

        finally:
            self.stop_streaming()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.stop_streaming()
        if hasattr(self, "sdr") and self.sdr is not None:
            self.sdr = None


# Example usage
if __name__ == "__main__":
    # Create a simple test signal
    t = np.linspace(0, 1, 1000)
    test_signal = np.sin(2 * np.pi * 1000 * t)

    # Create transmitter and send signal
    with SDRTransmitter(
        center_freq=433.92e6,  # 433.92 MHz
        sample_rate=2e6,  # 2 MHz
        gain=60,
        device_args="driver=hackrf",
    ) as transmitter:
        transmitter.transmit_samples(test_signal, repeat=3)
