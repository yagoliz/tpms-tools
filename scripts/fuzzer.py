#!/usr/bin/env python3

import argparse
import importlib
from pathlib import Path

import numpy as np
from scipy.io import wavfile

from tpms_tools.fuzzing.base_fuzzer import FuzzStrategy
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
    parser.add_argument("--boundary-count", type=int, default=0, help="Number of boundary value test cases")
    parser.add_argument("--random-count", type=int, default=0, help="Number of random semantic test cases")
    parser.add_argument("--protocol-count", type=int, default=0, help="Number of protocol-aware test cases")
    parser.add_argument("--mutation-count", type=int, default=0, help="Number of mutation-based test cases")
    parser.add_argument("--edge-count", type=int, default=0, help="Number of edge case test cases")
    parser.add_argument("--length-count", type=int, default=0, help="Number of packet length fuzzing test cases")
    
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
        print(f"Error: No fuzzer available for protocol '{args.protocol}'. Available protocols: {list(fuzzers.keys())}")
        return  # Stop execution if no fuzzer is available
    
    # Run different fuzzing strategies
    strategies = [
        (FuzzStrategy.BOUNDARY_VALUES, args.boundary_count),
        (FuzzStrategy.RANDOM_SEMANTIC, args.random_count),
        (FuzzStrategy.PROTOCOL_AWARE, args.protocol_count),
        (FuzzStrategy.MUTATION_BASED, args.mutation_count),
        (FuzzStrategy.EDGE_CASES, args.edge_count),
        (FuzzStrategy.PACKET_LENGTH_FUZZING, args.length_count),
    ]
    
    total_generated = 0
    
    for strategy, count in strategies:
        print(f"\nRunning {strategy.value} strategy with {count} test cases...")
        results = fuzzer.run_fuzz_campaign(strategy, count)
        
        # Generate WAV files for each result
        for i, result in enumerate(results):
            if result.encoded_bits is not None:
                filename = generate_filename(args.protocol, strategy, i, result, args)
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
                
                # Print packet length info if available
                if result.packet_info:
                    print(f"    Packet Length: {result.packet_info.get('length', 'N/A')} bits")
                    print(f"    Duration: {result.packet_info.get('duration', 'N/A')} ms")
                
                # Print packet length fuzzing details if present
                if 'target_length' in result.test_case:
                    print(f"    Target Length: {result.test_case['target_length']} bits")
                    print(f"    Padding Method: {result.test_case.get('padding_method', 'N/A')}")
            else:
                error_msg = result.error if result.error else "Unknown encoding error"
                print(f"  Failed to encode test case {i}: {error_msg}")
    
    print("\nFuzzing campaign complete!")
    print(f"Total WAV files generated: {total_generated}")
    print(f"Files saved to: {output_path.absolute()}")


def generate_filename(protocol, strategy, index, result, args):
    """Generate a descriptive filename for the WAV file."""
    test_case = result.test_case
    
    # Base filename components
    filename_parts = [
        protocol,
        strategy.value,
        f"{index:03d}",
        f"sensor_{test_case['sensor_id']:06x}",
        f"p{test_case['pressure_kpa']:.0f}kpa",
        f"t{test_case['temperature_c']}c"
    ]
    
    # Add packet length info if available
    if result.packet_info:
        length = result.packet_info.get('length')
        if length:
            filename_parts.append(f"len{length}b")
    
    # Add packet length fuzzing details
    if 'target_length' in test_case:
        filename_parts.append(f"target{test_case['target_length']}b")
        if 'padding_method' in test_case:
            filename_parts.append(f"pad{test_case['padding_method']}")
    
    # Add flags and extra if they're non-default
    if test_case.get('flags') is not None:
        filename_parts.append(f"flags{test_case['flags']:02x}")
    
    if test_case.get('extra') is not None:
        filename_parts.append(f"extra{test_case['extra']:04x}")
    
    # Add frequency info
    filename_parts.append(f"freq{args.frequency/1e6:.2f}mhz")
    
    return "_".join(filename_parts) + ".wav"


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