#!/usr/bin/env python3

import argparse
import importlib
from pathlib import Path

import numpy as np
from tpms_tools.modulation.fsk import generate_tpms_signal

def get_available_encoders():
    """Dynamically find all available TPMS encoders."""
    encoder_path = Path(__file__).parent.parent / "src" / "tpms_tools" / "encoders"
    encoders = {}
    
    for file in encoder_path.glob("*.py"):
        if file.stem in ["__init__", "base", "utils"]:
            continue
            
        module = importlib.import_module(f"tpms_tools.encoders.{file.stem}")
        for attr_name in dir(module):
            if attr_name.endswith("TPMSEncoder"):
                encoder_class = getattr(module, attr_name)
                try:
                    encoder = encoder_class()
                    encoders[encoder.protocol_name.lower()] = encoder_class
                except TypeError:
                    # Skip abstract base classes
                    continue
    
    return encoders

def main():
    # Get available encoders
    encoders = get_available_encoders()
    
    # Create argument parser
    parser = argparse.ArgumentParser(description='Save TPMS signal to WAV file')
    parser.add_argument('protocol', choices=list(encoders.keys()),
                       help='TPMS protocol to use')
    
    # Add common arguments
    parser.add_argument('--sensor-id', type=lambda x: int(x, 0), required=True,
                       help='Sensor ID (hex or decimal)')
    parser.add_argument('--pressure', type=float, required=True,
                       help='Tire pressure in kPa')
    parser.add_argument('--temperature', type=float, required=True,
                       help='Temperature in Celsius')
    
    # Add transmission arguments
    parser.add_argument('--frequency', type=float,
                       help='Center frequency in Hz')
    parser.add_argument('--samplerate', type=int, default=250000,
                       help='Sample rate in Hz')
    parser.add_argument('--gain', type=float, default=60,
                       help='Transmission gain in dB')
    parser.add_argument('--repeat', type=int, default=3,
                       help='Number of times to repeat transmission')
    parser.add_argument('--device', type=str, default="",
                       help='SoapySDR device arguments')
    
    args = parser.parse_args()
    
    # Create encoder instance
    encoder_class = encoders[args.protocol.lower()]
    encoder = encoder_class()
    
    # Generate TPMS message
    tpms_bits = encoder.encode_message(
        sensor_id=args.sensor_id,
        pressure_kpa=args.pressure,
        temperature_c=args.temperature
    )
    
    # Generate signal
    signal, modulator = generate_tpms_signal(tpms_bits, sample_rate=args.samplerate)
    
    print(f"Transmitting {args.protocol} TPMS signal...")
    print(f"Sensor ID: 0x{args.sensor_id:06x}")
    print(f"Pressure: {args.pressure:.1f} kPa")
    print(f"Temperature: {args.temperature:.1f}°C")

    # Save signal to WAV file
    filename = f"playground/{args.protocol}_tpms_signal.wav"
    
    # Add a few seconds of data before and after the signal
    padding = int(args.samplerate) * 4
    signal = np.concatenate([np.zeros(padding), signal, np.zeros(padding)])
    modulator.save_wav(signal, filename)
    

if __name__ == "__main__":
    main()