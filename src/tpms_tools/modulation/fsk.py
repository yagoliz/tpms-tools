import numpy as np
from scipy.io import wavfile
import matplotlib.pyplot as plt

class FSKModulator:
    def __init__(self, sample_rate=250000, f_mark=None, f_space=None, bit_duration=52e-6):
        """
        Initialize FSK modulator
        
        Args:
            sample_rate (int): Sample rate in Hz (default 250kHz as per decoder)
            f_mark (float): Frequency for mark/1 in Hz
            f_space (float): Frequency for space/0 in Hz
            bit_duration (float): Duration of each bit in seconds (default 52μs from decoder)
        """
        self.sample_rate = sample_rate
        self.f_mark = f_mark if f_mark is not None else sample_rate / 4  # Default to Fs/4
        self.f_space = f_space if f_space is not None else sample_rate / 8  # Default to Fs/8
        self.bit_duration = bit_duration
        self.samples_per_bit = int(sample_rate * bit_duration)
    
    def generate_fsk(self, bits):
        """
        Generate FSK signal for given bit sequence
        
        Args:
            bits (list): List of bits (0s and 1s)
            
        Returns:
            numpy.ndarray: FSK modulated signal
        """
        # Calculate total number of samples needed
        total_samples = len(bits) * self.samples_per_bit
        
        # Create time array
        t = np.arange(total_samples) / self.sample_rate
        
        # Initialize output signal
        signal = np.zeros_like(t)
        
        # Generate FSK signal
        for i, bit in enumerate(bits):
            start_idx = i * self.samples_per_bit
            end_idx = (i + 1) * self.samples_per_bit
            
            if bit:
                signal[start_idx:end_idx] = np.sin(2 * np.pi * self.f_mark * t[start_idx:end_idx])
            else:
                signal[start_idx:end_idx] = np.sin(2 * np.pi * self.f_space * t[start_idx:end_idx])
        
        return signal
    
    def add_ramp(self, signal, ramp_duration=100e-6):
        """
        Add ramp up and down to avoid spectral splatter
        
        Args:
            signal (numpy.ndarray): Input signal
            ramp_duration (float): Duration of ramp in seconds
            
        Returns:
            numpy.ndarray: Signal with ramps applied
        """
        ramp_samples = int(ramp_duration * self.sample_rate)
        ramp_up = np.linspace(0, 1, ramp_samples)
        ramp_down = np.linspace(1, 0, ramp_samples)
        
        # Apply ramps
        signal[:ramp_samples] *= ramp_up
        signal[-ramp_samples:] *= ramp_down
        
        return signal
    
    def save_wav(self, signal, filename, scale=0.9):
        """
        Save signal to WAV file
        
        Args:
            signal (numpy.ndarray): Signal to save
            filename (str): Output filename
            scale (float): Scale factor to prevent clipping
        """
        # Normalize and scale
        normalized = scale * signal / np.max(np.abs(signal))
        # Convert to 16-bit integers
        int16_data = (normalized * 32767).astype(np.int16)
        wavfile.write(filename, self.sample_rate, int16_data)
    
    def plot_signal(self, signal, duration=None):
        """
        Plot a portion of the signal
        
        Args:
            signal (numpy.ndarray): Signal to plot
            duration (float): Duration in seconds to plot (None for entire signal)
        """
        if duration is not None:
            samples = int(duration * self.sample_rate)
            signal = signal[:samples]
        
        t = np.arange(len(signal)) / self.sample_rate * 1000  # Convert to milliseconds
        
        plt.figure(figsize=(15, 5))
        plt.plot(t, signal)
        plt.xlabel('Time (ms)')
        plt.ylabel('Amplitude')
        plt.title('FSK Signal')
        plt.grid(True)
        plt.show()

def generate_tpms_signal(tpms_bits, f_mark=None, f_space=None):
    """
    Generate complete TPMS signal with FSK modulation
    
    Args:
        tpms_bits (list): Bits to transmit (including preamble and Manchester encoding)
        f_mark (float, optional): Mark frequency in Hz
        f_space (float, optional): Space frequency in Hz
        
    Returns:
        numpy.ndarray: Complete modulated signal
    """
    # Create modulator
    modulator = FSKModulator(f_mark=f_mark, f_space=f_space)
    
    # Generate FSK signal
    signal = modulator.generate_fsk(tpms_bits)
    
    # Add ramps to smooth transitions
    signal = modulator.add_ramp(signal)
    
    return signal, modulator

# Example usage
if __name__ == "__main__":
    # Create sample bits (you would use your encoder's output here)
    sample_bits = [1, 0, 1, 0, 1, 1, 0, 0] * 4  # Just an example pattern
    
    # Generate signal
    signal, modulator = generate_tpms_signal(sample_bits)
    
    # Plot first 1ms of signal
    modulator.plot_signal(signal, duration=0.001)
    
    # Save to WAV file
    modulator.save_wav(signal, "sample.wav")