# TPMS Tools

A Python toolkit for encoding, modulating, and generating TPMS (Tire Pressure Monitoring System) signals for security research and protocol analysis.

## Features

- **Multi-protocol support**: Renault and Mazda/Abarth TPMS protocols
- **Signal generation**: Create WAV files for RF transmission
- **Protocol fuzzing**: Built-in fuzzing framework for security testing
- **Modular architecture**: Extensible encoder system for new protocols

## Quick Start

### Installation

This project uses [uv](https://github.com/astral-sh/uv) for dependency management:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
```

### Generate TPMS Signals

Create WAV files for different TPMS protocols:

```bash
# Renault TPMS signal
python3 scripts/wavfile.py renault --sensor-id 0x123456 --pressure 220 --temperature 25

# Mazda/Abarth TPMS signal  
python3 scripts/wavfile.py mazda --sensor-id 0x123456 --pressure 220 --temperature 25
```

### Protocol Fuzzing

Run security fuzzing tests:

```bash
python3 scripts/fuzzer.py
```

## Supported Protocols

| Protocol | Frequency | Encoding | Status |
|----------|-----------|----------|--------|
| Renault  | 433.92 MHz | Manchester | ✅ Complete |
| Mazda/Abarth | 433.92 MHz | Manchester | ✅ Complete |
| Toyota   | 433.92 MHz | Manchester | 🚧 In progress |

## Development

### Code Quality

```bash
black src/ tests/              # Format code
ruff check src/ tests/ --fix   # Lint and fix issues
pytest                         # Run tests
```

### Architecture

- **Encoders**: Protocol-specific packet encoding (`src/tpms_tools/encoders/devices/`)
- **Modulation**: FSK modulation for RF transmission (`src/tpms_tools/modulation/`)
- **Fuzzing**: Security testing framework (`src/tpms_tools/fuzzing/`)
- **Utils**: Bit manipulation and CRC utilities (`src/tpms_tools/utils/`)

### Adding New Protocols

1. Create encoder in `src/tpms_tools/encoders/devices/`
2. Subclass `TPMSEncoder` and implement required methods
3. The CLI tools will automatically detect your new protocol

## Security Research

This toolkit is designed for:
- TPMS protocol analysis and reverse engineering
- Security vulnerability research
- Educational purposes

**Important**: This tool is for defensive security research only. Use responsibly and in accordance with applicable laws.
