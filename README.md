# TPMS Tools

Tools for encoding and transmitting TPMS (Tire Pressure Monitoring System) signals.

## Setup

This project uses [uv](https://github.com/astral-sh/uv) for dependency management. Make sure you have uv installed:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yagoliz/tpms_tools.git
cd tpms_tools
```

2. Create and activate a virtual environment using uv:
```bash
uv venv
source .venv/bin/activate 
```

3. Install dependencies including development tools:
```bash
uv pip install -e ".[dev]"
```

### Usage

Transmit a TPMS signal:
```bash
tpms-transmit renault --sensor-id 0x123456 --pressure 220 --temperature 25
```

### Development

Format code:
```bash
black src/ tests/
ruff check src/ tests/ --fix
```

Run tests:
```bash
pytest
```

### Project Structure

```
tpms_tools/
├── src/
│   └── tpms_tools/      # Main package
│       ├── encoders/    # TPMS protocol encoders
│       ├── modulation/  # Signal modulation
│       └── transmission/# SDR transmission
├── tests/              # Test suite
└── pyproject.toml      # Project configuration
```

### Adding a New TPMS Protocol

1. Create a new encoder in `src/tpms_tools/encoders/`
2. Subclass `TPMSEncoder` or `ManchesterTPMSEncoder`
3. Implement the required methods
4. The CLI will automatically detect your new encoder

Example:
```python
from tpms_tools.encoders.base import TPMSEncoder

class MyTPMSEncoder(TPMSEncoder):
    @property
    def protocol_name(self) -> str:
        return "MyProtocol"
    
    # Implement other required methods
```