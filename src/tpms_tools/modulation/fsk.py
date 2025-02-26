import numpy as np


class FSKModulator:
    def __init__(
        self,
        mark: float = 35000,
        space: float = -35000,
        sample_rate: float = 1000000,
        symbol_duration: float = 52,
    ):
        self.f1 = mark
        self.f2 = space
        self.sample_rate = sample_rate
        self.symbol_duration = symbol_duration

    def generate_fsk_iq(
        self, pulse_data: list[tuple[int, int]], padding: int = 4
    ) -> np.ndarray:
        """
        Generate IQ samples from FSK pulse timing data

        Args:
            pulse_data: List of tuples (pulse_width, gap_width) in samples
            sample_rate: Sample rate in Hz
        t = []
        signal = []

        Returns:
            iq_data: np.ndarray: Complex array of IQ samples
        """
        # Calculate samples per symbol
        samples_per_symbol = self.sample_rate * self.symbol_duration * 1e-6

        t = []
        signal = []

        for pulse_width, gap_width in pulse_data:
            # Generate time points for this pulse-gap pair
            pulse_t = np.arange(samples_per_symbol * pulse_width) / self.sample_rate
            gap_t = np.arange(samples_per_symbol * gap_width) / self.sample_rate
            pulse = np.exp(2j * np.pi * self.f1 * pulse_t)
            gap = np.exp(2j * np.pi * self.f2 * gap_t)

            # Add to total signal
            t.extend(pulse_t)
            t.extend(gap_t)
            signal.extend(pulse)
            signal.extend(gap)

        # Convert lists to arrays
        t = np.array(t)
        signal = np.array(signal)

        # Apply raised cosine pulse shaping
        alpha = 0.35  # Roll-off factor
        num_taps = 101
        t_rc = np.arange(-num_taps // 2, num_taps // 2) / self.sample_rate
        h_rc = (
            np.sinc(t_rc * self.sample_rate)
            * np.cos(np.pi * alpha * t_rc * self.sample_rate)
            / (1 - (2 * alpha * t_rc * self.sample_rate) ** 2)
        )

        # Filter the signal
        shaped_signal = np.convolve(signal, h_rc, mode="same")

        # Add 4 seconds of zero signal at the end to allow the signal to decay naturally
        # and prevent abrupt cut-off which can cause spectral leakage.
        # Add some seconds of 0 signal at the end to allow for signal to decay
        signal_end = np.zeros(int(self.sample_rate * padding))
        shaped_signal = np.concatenate([shaped_signal, signal_end])

        return shaped_signal
