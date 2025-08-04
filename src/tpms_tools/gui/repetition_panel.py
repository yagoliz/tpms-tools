from PyQt5.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QCheckBox, QDoubleSpinBox,
    QSpinBox, QLabel, QFormLayout, QRadioButton, QButtonGroup
)
from PyQt5.QtCore import pyqtSignal


class RepetitionPanel(QGroupBox):
    """Panel for configuring repetition settings."""

    settings_changed = pyqtSignal()  # Emitted when settings change

    def __init__(self):
        super().__init__("Repetition Control")
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Enable repetition checkbox
        self.enable_repeat_cb = QCheckBox("Enable Repetition")
        layout.addWidget(self.enable_repeat_cb)
        
        # Repetition mode
        mode_group = QButtonGroup(self)
        mode_layout = QHBoxLayout()
        
        self.continuous_radio = QRadioButton("Continuous")
        self.count_radio = QRadioButton("Count:")
        
        mode_group.addButton(self.continuous_radio)
        mode_group.addButton(self.count_radio)
        
        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, 9999)
        self.count_spin.setValue(10)
        self.count_spin.setEnabled(False)
        
        mode_layout.addWidget(self.continuous_radio)
        mode_layout.addWidget(self.count_radio)
        mode_layout.addWidget(self.count_spin)
        mode_layout.addStretch()
        
        layout.addLayout(mode_layout)
        
        # Timing settings
        timing_form = QFormLayout()
        
        # Interval between transmissions
        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setRange(0.1, 3600.0)  # 0.1 second to 1 hour
        self.interval_spin.setValue(5.0)
        self.interval_spin.setSuffix(" sec")
        self.interval_spin.setDecimals(1)
        timing_form.addRow("Interval:", self.interval_spin)
        
        # Initial delay
        self.delay_spin = QDoubleSpinBox()
        self.delay_spin.setRange(0.0, 60.0)
        self.delay_spin.setValue(0.0)
        self.delay_spin.setSuffix(" sec")
        self.delay_spin.setDecimals(1)
        timing_form.addRow("Initial Delay:", self.delay_spin)
        
        layout.addLayout(timing_form)
        
        # Status and control
        self.status_label = QLabel("Repetition disabled")
        layout.addWidget(self.status_label)
        
        # Initially disable repetition controls
        self._update_repetition_controls()

    def _connect_signals(self):
        """Connect signals and slots."""
        self.enable_repeat_cb.toggled.connect(self._update_repetition_controls)
        self.enable_repeat_cb.toggled.connect(self.settings_changed.emit)
        
        self.continuous_radio.toggled.connect(self._update_count_control)
        self.continuous_radio.toggled.connect(self.settings_changed.emit)
        
        self.count_radio.toggled.connect(self._update_count_control)
        self.count_radio.toggled.connect(self.settings_changed.emit)
        
        self.count_spin.valueChanged.connect(self.settings_changed.emit)
        self.interval_spin.valueChanged.connect(self.settings_changed.emit)
        self.delay_spin.valueChanged.connect(self.settings_changed.emit)

    def _update_repetition_controls(self):
        """Update repetition control state."""
        enabled = self.enable_repeat_cb.isChecked()
        
        self.continuous_radio.setEnabled(enabled)
        self.count_radio.setEnabled(enabled)
        self.interval_spin.setEnabled(enabled)
        self.delay_spin.setEnabled(enabled)
        
        if enabled:
            self.continuous_radio.setChecked(True)
            self.status_label.setText("Repetition enabled")
        else:
            self.status_label.setText("Repetition disabled")
        
        self._update_count_control()

    def _update_count_control(self):
        """Update count spinbox state."""
        count_enabled = (self.enable_repeat_cb.isChecked() and 
                        self.count_radio.isChecked())
        self.count_spin.setEnabled(count_enabled)

    def is_repeat_enabled(self) -> bool:
        """Check if repetition is enabled."""
        return self.enable_repeat_cb.isChecked()

    def is_continuous_mode(self) -> bool:
        """Check if continuous mode is selected."""
        return self.continuous_radio.isChecked()

    def get_count(self) -> int:
        """Get repetition count."""
        return self.count_spin.value()

    def get_interval(self) -> float:
        """Get interval between transmissions in seconds."""
        return self.interval_spin.value()

    def get_initial_delay(self) -> float:
        """Get initial delay in seconds."""
        return self.delay_spin.value()

    def get_repetition_config(self) -> dict:
        """Get complete repetition configuration."""
        return {
            "enabled": self.is_repeat_enabled(),
            "continuous": self.is_continuous_mode(),
            "count": self.get_count(),
            "interval": self.get_interval(),
            "initial_delay": self.get_initial_delay(),
        }

    def set_repetition_config(self, config: dict):
        """Set repetition configuration."""
        if "enabled" in config:
            self.enable_repeat_cb.setChecked(config["enabled"])
        
        if "continuous" in config:
            if config["continuous"]:
                self.continuous_radio.setChecked(True)
            else:
                self.count_radio.setChecked(True)
        
        if "count" in config:
            self.count_spin.setValue(config["count"])
        
        if "interval" in config:
            self.interval_spin.setValue(config["interval"])
        
        if "initial_delay" in config:
            self.delay_spin.setValue(config["initial_delay"])

    def update_status(self, message: str):
        """Update status label."""
        self.status_label.setText(message)