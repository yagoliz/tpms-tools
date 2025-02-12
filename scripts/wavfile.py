#!/usr/bin/env python3

import argparse
import importlib
from pathlib import Path

import numpy as np
from scipy.io import wavfile

from tpms_tools.modulation.fsk import FSKModulator
from tpms_tools.encoders.pcm import PCMEncoder


def get_available_encoders():
    """Dynamically find all available TPMS encoders."""
    encoder_path = (
        Path(__file__).parent.parent / "src" / "tpms_tools" / "encoders" / "devices"
    )
    encoders = {}

    for file in encoder_path.glob("*.py"):
        if file.stem in ["__init__", "base", "utils"]:
            continue

        module = importlib.import_module(f"tpms_tools.encoders.devices.{file.stem}")
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
    parser = argparse.ArgumentParser(description="Save TPMS signal to WAV file")
    parser.add_argument(
        "protocol", choices=list(encoders.keys()), help="TPMS protocol to use"
    )

    # Add common arguments
    parser.add_argument(
        "--sensor-id",
        type=lambda x: int(x, 0),
        required=True,
        help="Sensor ID (hex or decimal)",
    )
    parser.add_argument(
        "--pressure", type=float, required=True, help="Tire pressure in kPa"
    )
    parser.add_argument(
        "--temperature", type=int, required=True, help="Temperature in Celsius"
    )

    # Add transmission arguments
    parser.add_argument("--frequency", type=float, help="Center frequency in Hz")
    parser.add_argument(
        "--samplerate", type=int, default=250000, help="Sample rate in Hz"
    )
    parser.add_argument("--mark", type=int, default=35000, help="Mark frequency in Hz")
    parser.add_argument(
        "--space", type=int, default=-35000, help="Space frequency in Hz"
    )

    # Filename argument
    parser.add_argument(
        "--filename",
        type=str,
        default="fsk_signal.wav",
        help="Output filename",
    )

    args = parser.parse_args()

    # Create encoder instance
    encoder_class = encoders[args.protocol.lower()]
    encoder = encoder_class()

    # Generate TPMS message
    tpms_bits = encoder.encode_message(
        sensor_id=args.sensor_id,
        pressure_kpa=args.pressure,
        temperature_c=args.temperature,
    )

    # PCM Modulation
    pcm = PCMEncoder(short=1, long=1)
    pulse_data = pcm.encode_pcm_signal([int(b) for b in tpms_bits])

    # FSK Modulation
    fsk = FSKModulator(
        mark=args.mark,
        space=args.space,
        sample_rate=args.samplerate,
        symbol_duration=encoder.BIT_DURATION,
    )
    iq_samples = fsk.generate_fsk_iq(pulse_data, padding=2)

    # Finally saving this to a WAV file
    stereo_data = np.vstack((np.real(iq_samples), np.imag(iq_samples))).T
    wavfile.write(
        args.filename,
        args.samplerate,
        stereo_data.astype(np.float32),
    )


if __name__ == "__main__":
    main()
