from PyQt5.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QRadioButton, QComboBox,
    QLabel, QDoubleSpinBox, QSpinBox, QLineEdit, QFormLayout, QButtonGroup
)
from PyQt5.QtCore import pyqtSignal
from ..transmission.base import TransmitterFactory


class TransmissionPanel(QGroupBox):
    """Panel for configuring transmission settings."""

    settings_changed = pyqtSignal()  # Emitted when settings change

    def __init__(self):
        super().__init__("Transmission Settings")
        self.available_types = TransmitterFactory.get_available_types()
        self._setup_ui()
        self._connect_signals()
        self._set_defaults()

    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Transmitter type selection
        type_group = QButtonGroup(self)
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Backend:"))
        
        self.uhd_radio = QRadioButton("UHD/USRP")
        self.soapy_radio = QRadioButton("SoapySDR")
        
        type_group.addButton(self.soapy_radio)
        type_group.addButton(self.uhd_radio)
        
        type_layout.addWidget(self.soapy_radio)
        type_layout.addWidget(self.uhd_radio)
        type_layout.addStretch()
        
        layout.addLayout(type_layout)
        
        # Enable/disable based on availability
        self.uhd_radio.setEnabled("uhd" in self.available_types)
        self.soapy_radio.setEnabled("soapy" in self.available_types)
        
        # Device settings form
        form_layout = QFormLayout()
        
        # Device arguments
        self.device_args_edit = QLineEdit()
        self.device_args_edit.setPlaceholderText("e.g., driver=hackrf or type=b200")
        form_layout.addRow("Device Args:", self.device_args_edit)
        
        # Center frequency
        self.freq_spin = QDoubleSpinBox()
        self.freq_spin.setRange(1, 6000)
        self.freq_spin.setValue(433.92)
        self.freq_spin.setSuffix(" MHz")
        self.freq_spin.setDecimals(3)
        form_layout.addRow("Center Freq:", self.freq_spin)
        
        # Sample rate
        self.sample_rate_spin = QDoubleSpinBox()
        self.sample_rate_spin.setRange(0.1, 100)
        self.sample_rate_spin.setValue(2.0)
        self.sample_rate_spin.setSuffix(" MHz")
        self.sample_rate_spin.setDecimals(1)
        form_layout.addRow("Sample Rate:", self.sample_rate_spin)
        
        # Gain
        self.gain_spin = QSpinBox()
        self.gain_spin.setRange(0, 100)
        self.gain_spin.setValue(60)
        self.gain_spin.setSuffix(" dB")
        form_layout.addRow("Gain:", self.gain_spin)
        
        # Channel
        self.channel_spin = QSpinBox()
        self.channel_spin.setRange(0, 7)
        self.channel_spin.setValue(0)
        form_layout.addRow("Channel:", self.channel_spin)
        
        # Antenna (optional)
        self.antenna_edit = QLineEdit()
        self.antenna_edit.setPlaceholderText("Optional antenna selection")
        form_layout.addRow("Antenna:", self.antenna_edit)
        
        layout.addLayout(form_layout)
        
        # RF Parameters section
        rf_group = QGroupBox("RF Parameters")
        rf_layout = QFormLayout(rf_group)
        
        # Signal scaling
        self.scale_spin = QDoubleSpinBox()
        self.scale_spin.setRange(0.1, 1.0)
        self.scale_spin.setValue(0.8)
        self.scale_spin.setDecimals(2)
        self.scale_spin.setSingleStep(0.1)
        rf_layout.addRow("Signal Scale:", self.scale_spin)
        
        layout.addWidget(rf_group)

    def _connect_signals(self):
        """Connect signals and slots."""
        self.soapy_radio.toggled.connect(self.settings_changed.emit)
        self.uhd_radio.toggled.connect(self.settings_changed.emit)
        self.device_args_edit.textChanged.connect(self.settings_changed.emit)
        self.freq_spin.valueChanged.connect(self.settings_changed.emit)
        self.sample_rate_spin.valueChanged.connect(self.settings_changed.emit)
        self.gain_spin.valueChanged.connect(self.settings_changed.emit)
        self.channel_spin.valueChanged.connect(self.settings_changed.emit)
        self.antenna_edit.textChanged.connect(self.settings_changed.emit)
        self.scale_spin.valueChanged.connect(self.settings_changed.emit)

    def _set_defaults(self):
        """Set default values."""
        # Select first available transmitter type
        if "soapy" in self.available_types:
            self.soapy_radio.setChecked(True)
        elif "uhd" in self.available_types:
            self.uhd_radio.setChecked(True)
        
        # Set common device args based on type
        self._update_device_args_placeholder()

    def _update_device_args_placeholder(self):
        """Update device args placeholder based on selected type."""
        if self.soapy_radio.isChecked():
            self.device_args_edit.setPlaceholderText("e.g., driver=hackrf")
        elif self.uhd_radio.isChecked():
            self.device_args_edit.setPlaceholderText("e.g., type=b200")

    def get_transmitter_config(self) -> dict:
        """Get current transmitter configuration."""
        config = {
            "type": "soapy" if self.soapy_radio.isChecked() else "uhd",
            "center_freq": self.freq_spin.value() * 1e6,  # Convert MHz to Hz
            "sample_rate": self.sample_rate_spin.value() * 1e6,  # Convert MHz to Hz
            "gain": self.gain_spin.value(),
            "device_args": self.device_args_edit.text().strip(),
            "channel": self.channel_spin.value(),
            "antenna": self.antenna_edit.text().strip() or None,
            "scale": self.scale_spin.value(),
        }
        return config

    def set_transmitter_config(self, config: dict):
        """Set transmitter configuration."""
        if config.get("type") == "soapy":
            self.soapy_radio.setChecked(True)
        elif config.get("type") == "uhd":
            self.uhd_radio.setChecked(True)
        
        if "center_freq" in config:
            self.freq_spin.setValue(config["center_freq"] / 1e6)
        
        if "sample_rate" in config:
            self.sample_rate_spin.setValue(config["sample_rate"] / 1e6)
        
        if "gain" in config:
            self.gain_spin.setValue(config["gain"])
        
        if "device_args" in config:
            self.device_args_edit.setText(config["device_args"])
        
        if "channel" in config:
            self.channel_spin.setValue(config["channel"])
        
        if "antenna" in config:
            self.antenna_edit.setText(config["antenna"] or "")
        
        if "scale" in config:
            self.scale_spin.setValue(config["scale"])

    def validate_config(self) -> tuple[bool, str]:
        """Validate current configuration."""
        if not self.soapy_radio.isChecked() and not self.uhd_radio.isChecked():
            return False, "No transmitter type selected"
        
        selected_type = "soapy" if self.soapy_radio.isChecked() else "uhd"
        if selected_type not in self.available_types:
            return False, f"{selected_type.upper()} not available on this system"
        
        if self.freq_spin.value() <= 0:
            return False, "Invalid frequency"
        
        if self.sample_rate_spin.value() <= 0:
            return False, "Invalid sample rate"
        
        return True, "Configuration valid"

    def set_frequency_from_encoder(self, encoder):
        """Set frequency based on encoder default."""
        if encoder and hasattr(encoder, 'default_frequency'):
            freq_mhz = encoder.default_frequency / 1e6
            self.freq_spin.setValue(freq_mhz)