from PyQt5.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QComboBox, QLabel,
    QLineEdit, QSpinBox, QDoubleSpinBox, QFormLayout, QWidget
)
from PyQt5.QtCore import pyqtSignal
from ..encoders.devices.renault import RenaultTPMSEncoder
from ..encoders.devices.mazda import MazdaTPMSEncoder
from ..encoders.devices.toyota import ToyotaTPMSEncoder


class EncoderPanel(QGroupBox):
    """Panel for configuring TPMS encoder settings."""

    encoder_changed = pyqtSignal()  # Emitted when encoder selection changes
    parameters_changed = pyqtSignal()  # Emitted when parameters change

    def __init__(self):
        super().__init__("Encoder Configuration")
        self.encoders = {
            "Renault": RenaultTPMSEncoder(),
            "Mazda": MazdaTPMSEncoder(),
            "Toyota": ToyotaTPMSEncoder(),
        }
        self.current_encoder = None
        self.parameter_widgets = {}
        
        self._setup_ui()
        self._connect_signals()
        
        # Set default encoder
        self.encoder_combo.setCurrentText("Renault")
        self._on_encoder_changed()

    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Encoder selection
        encoder_layout = QHBoxLayout()
        encoder_layout.addWidget(QLabel("Protocol:"))
        
        self.encoder_combo = QComboBox()
        self.encoder_combo.addItems(list(self.encoders.keys()))
        encoder_layout.addWidget(self.encoder_combo)
        encoder_layout.addStretch()
        
        layout.addLayout(encoder_layout)
        
        # Parameter form
        self.param_form = QFormLayout()
        self.param_widget = QWidget()
        self.param_widget.setLayout(self.param_form)
        layout.addWidget(self.param_widget)
        
        # Info display
        self.info_label = QLabel("Select encoder to see parameters")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

    def _connect_signals(self):
        """Connect signals and slots."""
        self.encoder_combo.currentTextChanged.connect(self._on_encoder_changed)

    def _on_encoder_changed(self):
        """Handle encoder selection change."""
        encoder_name = self.encoder_combo.currentText()
        if encoder_name not in self.encoders:
            return
        
        self.current_encoder = self.encoders[encoder_name]
        self._update_parameter_form()
        self.encoder_changed.emit()

    def _update_parameter_form(self):
        """Update the parameter form based on current encoder."""
        # Clear existing widgets
        while self.param_form.count():
            child = self.param_form.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        self.parameter_widgets.clear()
        
        if not self.current_encoder:
            return
        
        # Add parameter widgets based on encoder requirements
        required_params = self.current_encoder.required_parameters
        
        for param in required_params:
            widget = self._create_parameter_widget(param)
            if widget:
                self.parameter_widgets[param] = widget
                self.param_form.addRow(self._format_label(param), widget)
        
        # Add optional parameters for some encoders
        if hasattr(self.current_encoder, '__class__') and 'Renault' in self.current_encoder.__class__.__name__:
            flags_widget = QSpinBox()
            flags_widget.setRange(0, 255)
            flags_widget.setValue(54)
            self.parameter_widgets['flags'] = flags_widget
            self.param_form.addRow("Flags (optional):", flags_widget)
            
            extra_widget = QSpinBox()
            extra_widget.setRange(0, 65535)
            extra_widget.setValue(48153)
            self.parameter_widgets['extra'] = extra_widget
            self.param_form.addRow("Extra (optional):", extra_widget)
        
        # Update info
        freq_mhz = self.current_encoder.default_frequency / 1e6
        info_text = (f"Protocol: {self.current_encoder.protocol_name}\n"
                    f"Default frequency: {freq_mhz:.2f} MHz\n"
                    f"Required parameters: {', '.join(required_params)}")
        self.info_label.setText(info_text)

    def _create_parameter_widget(self, param_name: str):
        """Create appropriate widget for parameter."""
        if param_name == "sensor_id":
            widget = QLineEdit()
            widget.setPlaceholderText("0x123456")
            widget.textChanged.connect(self.parameters_changed.emit)
            return widget
        
        elif param_name in ["pressure_kpa", "pressure"]:
            widget = QDoubleSpinBox()
            widget.setRange(0, 1000)
            widget.setValue(220)
            widget.setSuffix(" kPa")
            widget.valueChanged.connect(self.parameters_changed.emit)
            return widget
        
        elif param_name in ["temperature_c", "temperature"]:
            widget = QSpinBox()
            widget.setRange(-50, 150)
            widget.setValue(25)
            widget.setSuffix(" °C")
            widget.valueChanged.connect(self.parameters_changed.emit)
            return widget
        
        return None

    def _format_label(self, param_name: str) -> str:
        """Format parameter name for display."""
        formatters = {
            "sensor_id": "Sensor ID:",
            "pressure_kpa": "Pressure:",
            "pressure": "Pressure:",
            "temperature_c": "Temperature:",
            "temperature": "Temperature:",
        }
        return formatters.get(param_name, param_name.replace("_", " ").title() + ":")

    def get_encoder(self):
        """Get the currently selected encoder."""
        return self.current_encoder

    def get_parameters(self) -> dict:
        """Get current parameter values."""
        if not self.current_encoder:
            return {}
        
        params = {}
        
        for param_name, widget in self.parameter_widgets.items():
            try:
                if param_name == "sensor_id":
                    text = widget.text().strip()
                    if text.startswith("0x"):
                        params[param_name] = int(text, 16)
                    else:
                        params[param_name] = int(text)
                elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                    params[param_name] = widget.value()
                elif isinstance(widget, QLineEdit):
                    params[param_name] = widget.text()
            except (ValueError, AttributeError):
                continue
        
        return params

    def set_parameters(self, params: dict):
        """Set parameter values."""
        for param_name, value in params.items():
            if param_name in self.parameter_widgets:
                widget = self.parameter_widgets[param_name]
                if param_name == "sensor_id" and isinstance(widget, QLineEdit):
                    if isinstance(value, int):
                        widget.setText(f"0x{value:06X}")
                    else:
                        widget.setText(str(value))
                elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                    widget.setValue(value)

    def validate_parameters(self) -> tuple[bool, str]:
        """Validate current parameters."""
        if not self.current_encoder:
            return False, "No encoder selected"
        
        params = self.get_parameters()
        required = self.current_encoder.required_parameters
        
        for param in required:
            if param not in params or params[param] is None:
                return False, f"Missing required parameter: {param}"
            
            # Additional validation
            if param == "sensor_id":
                try:
                    value = params[param]
                    if not (0 <= value <= 0xFFFFFF):
                        return False, "Sensor ID must be between 0x000000 and 0xFFFFFF"
                except (ValueError, TypeError):
                    return False, "Invalid sensor ID format"
        
        return True, "Parameters valid"