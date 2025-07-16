#!/usr/bin/env python3

import argparse
import importlib
import os
from pathlib import Path

import numpy as np
from scipy.io import wavfile

from tpms_tools.fuzzing.base_fuzzer import FuzzStrategy, TPMSFuzzer
from tpms_tools.fuzzing.renault_fuzzer import RenaultTPMSFuzzer
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


def get_available_fuzzers():
    """Get available fuzzers - currently only Renault is implemented."""
    return {
        "renault": RenaultTPMSFuzzer
    }


def create_generic_fuzzer(encoder_class, target_sensor_ids=None):
    """Create a generic fuzzer for any encoder that doesn't have a specific fuzzer."""
    
    class GenericTPMSFuzzer(TPMSFuzzer):
        def __init__(self, target_sensor_ids=None):
            super().__init__(encoder_class, target_sensor_ids)
            self.encoder_instance = encoder_class()
            
        def generate_test_cases(self, strategy, count):
            """Generate basic test cases for any encoder."""
            required_params = self.encoder_instance.required_parameters
            
            for i in range(count):
                test_case = {}
                
                # Generate basic values for required parameters
                for param in required_params:
                    if param == "sensor_id":
                        if self.target_sensor_ids:
                            test_case[param] = self.target_sensor_ids[i % len(self.target_sensor_ids)]
                        else:
                            test_case[param] = 0x123456 + i
                    elif param == "pressure_kpa":
                        test_case[param] = 200.0 + (i % 100)
                    elif param == "temperature_c":
                        test_case[param] = 20 + (i % 40)
                    else:
                        test_case[param] = i % 256
                
                yield test_case
    
    return GenericTPMSFuzzer(target_sensor_ids)


def main():
    """Run comprehensive fuzz testing on TPMS protocols."""
    # Get available encoders and fuzzers
    encoders = get_available_encoders()
    fuzzers = get_available_fuzzers()
    
    parser = argparse.ArgumentParser(description="TPMS Fuzzing Campaign with WAV Generation")
    
    # Protocol selection
    parser.add_argument(
        "protocol", 
        choices=list(encoders.keys()), 
        help="TPMS protocol to fuzz"
    )
    
    # Fuzzing parameters
    parser.add_argument(
        "--target-sensors", 
        nargs='+', 
        type=lambda x: int(x, 0),
        default=[0x123456, 0xABCDEF, 0x555555],
        help="Target sensor IDs (hex or decimal)"
    )
    parser.add_argument(
        "--output-dir", 
        type=str, 
        default="fuzz_output",
        help="Output directory for generated WAV files"
    )
    
    # Physical layer parameters
    parser.add_argument("--frequency", type=float, default=433.92e6, help="Center frequency in Hz")
    parser.add_argument("--samplerate", type=int, default=250000, help="Sample rate in Hz")
    parser.add_argument("--mark", type=int, default=35000, help="Mark frequency in Hz")
    parser.add_argument("--space", type=int, default=-35000, help="Space frequency in Hz")
    
    # Strategy control
    parser.add_argument("--boundary-count", type=int, default=10, help="Number of boundary value test cases")
    parser.add_argument("--random-count", type=int, default=20, help="Number of random semantic test cases")
    parser.add_argument("--protocol-count", type=int, default=15, help="Number of protocol-aware test cases")
    parser.add_argument("--mutation-count", type=int, default=15, help="Number of mutation-based test cases")
    parser.add_argument("--edge-count", type=int, default=10, help="Number of edge case test cases")
    
    args = parser.parse_args()
    
    print(f"Starting TPMS Fuzz Testing Campaign for {args.protocol.upper()}...")
    print(f"Target sensor IDs: {[hex(sid) for sid in args.target_sensors]}")
    print(f"Output directory: {args.output_dir}")
    
    # Create output directory
    output_path = Path(args.output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Get the encoder class and create appropriate fuzzer
    encoder_class = encoders[args.protocol.lower()]
    encoder_instance = encoder_class()
    
    # Use specific fuzzer if available, otherwise use generic fuzzer
    if args.protocol.lower() in fuzzers:
        fuzzer = fuzzers[args.protocol.lower()](target_sensor_ids=args.target_sensors)
    else:
        fuzzer = create_generic_fuzzer(encoder_class, target_sensor_ids=args.target_sensors)
    
    # Run different fuzzing strategies
    strategies = [
        (FuzzStrategy.BOUNDARY_VALUES, args.boundary_count),
        (FuzzStrategy.RANDOM_SEMANTIC, args.random_count),
        (FuzzStrategy.PROTOCOL_AWARE, args.protocol_count),
        (FuzzStrategy.MUTATION_BASED, args.mutation_count),
        (FuzzStrategy.EDGE_CASES, args.edge_count),
    ]
    
    total_generated = 0
    
    for strategy, count in strategies:
        print(f"\nRunning {strategy.value} strategy with {count} test cases...")
        results = fuzzer.run_fuzz_campaign(strategy, count)
        
        # Generate WAV files for each result
        for i, result in enumerate(results):
            if result.encoded_bits is not None:
                filename = f"{args.protocol}_{strategy.value}_{i:03d}_sensor_{result.test_case['sensor_id']:06x}.wav"
                filepath = output_path / filename
                
                # Generate WAV file
                generate_wav_file(
                    result.encoded_bits,
                    filepath,
                    args.samplerate,
                    args.mark,
                    args.space,
                    encoder_instance.BIT_DURATION
                )
                
                total_generated += 1
                
                # Print test case details
                print(f"  Generated: {filename}")
                print(f"    Sensor ID: 0x{result.test_case['sensor_id']:06x}")
                print(f"    Pressure: {result.test_case['pressure_kpa']:.1f} kPa")
                print(f"    Temperature: {result.test_case['temperature_c']}°C")
                print(f"    Flags: {result.test_case.get('flags', 'N/A')}")
                print(f"    Extra: {result.test_case.get('extra', 'N/A')}")
            else:
                print(f"  Failed to encode test case {i}")
    
    print("\nFuzzing campaign complete!")
    print(f"Total WAV files generated: {total_generated}")
    print(f"Files saved to: {output_path.absolute()}")


def generate_wav_file(tpms_bits, filepath, sample_rate, mark, space, bit_duration):
    """Generate a WAV file from TPMS bits."""
    # PCM Modulation
    pcm = PCMEncoder(short=1, long=1)
    pulse_data = pcm.encode_pcm_signal([int(b) for b in tpms_bits])
    
    # FSK Modulation
    fsk = FSKModulator(
        mark=mark,
        space=space,
        sample_rate=sample_rate,
        symbol_duration=bit_duration,
    )
    iq_samples = fsk.generate_fsk_iq(pulse_data, padding=2)
    
    # Save to WAV file
    stereo_data = np.vstack((np.real(iq_samples), np.imag(iq_samples))).T
    wavfile.write(
        str(filepath),
        sample_rate,
        stereo_data.astype(np.float32),
    )


if __name__ == "__main__":
    main()