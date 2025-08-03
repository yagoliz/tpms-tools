import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QGroupBox, QPushButton, QTextEdit, QSplitter
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from .encoder_panel import EncoderPanel
from .transmission_panel import TransmissionPanel
from .repetition_panel import RepetitionPanel
from ..transmission.base import TransmitterFactory
from ..modulation.fsk import FSKModulator


class TPMSMainWindow(QMainWindow):
    """Main window for TPMS signal generator and transmitter."""

    signal_generated = pyqtSignal(list)  # Emitted when signal is generated
    transmission_started = pyqtSignal()  # Emitted when transmission starts
    transmission_stopped = pyqtSignal()  # Emitted when transmission stops

    def __init__(self):
        super().__init__()
        self.setWindowTitle("TPMS Signal Generator & Transmitter")
        self.setGeometry(100, 100, 900, 600)
        
        # Initialize timers and state
        self.repeat_timer = QTimer()
        self.repeat_timer.timeout.connect(self._transmit_once)
        self.is_transmitting = False
        self.current_signal = None
        self.current_transmitter = None
        self.current_transmitter_config = None
        
        self._setup_ui()
        self._connect_signals()
        
        # Connect encoder changes to transmission panel
        self.encoder_panel.encoder_changed.connect(
            lambda: self.transmission_panel.set_frequency_from_encoder(
                self.encoder_panel.get_encoder()
            )
        )

    def _setup_ui(self):
        """Set up the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Create splitter for panels and log
        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter)
        
        # Control panels widget
        control_widget = QWidget()
        control_layout = QHBoxLayout(control_widget)
        
        # Left column: Encoder and Transmission settings
        left_column = QVBoxLayout()
        self.encoder_panel = EncoderPanel()
        self.transmission_panel = TransmissionPanel()
        left_column.addWidget(self.encoder_panel)
        left_column.addWidget(self.transmission_panel)
        
        # Right column: Repetition control and actions
        right_column = QVBoxLayout()
        self.repetition_panel = RepetitionPanel()
        right_column.addWidget(self.repetition_panel)
        
        # Action buttons
        self.action_group = QGroupBox("Actions")
        action_layout = QVBoxLayout(self.action_group)
        
        self.generate_btn = QPushButton("Generate Signal")
        self.transmit_btn = QPushButton("Transmit Once")
        self.start_repeat_btn = QPushButton("Start Repeat")
        self.stop_btn = QPushButton("Stop")
        
        self.transmit_btn.setEnabled(False)
        self.start_repeat_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        
        action_layout.addWidget(self.generate_btn)
        action_layout.addWidget(self.transmit_btn)
        action_layout.addWidget(self.start_repeat_btn)
        action_layout.addWidget(self.stop_btn)
        action_layout.addStretch()
        
        right_column.addWidget(self.action_group)
        right_column.addStretch()
        
        # Add columns to control layout
        control_layout.addLayout(left_column, 2)
        control_layout.addLayout(right_column, 1)
        
        # Log area
        self.log_area = QTextEdit()
        self.log_area.setMaximumHeight(150)
        self.log_area.setReadOnly(True)
        
        # Add to splitter
        splitter.addWidget(control_widget)
        splitter.addWidget(self.log_area)
        splitter.setSizes([400, 150])

    def _connect_signals(self):
        """Connect signals and slots."""
        self.generate_btn.clicked.connect(self.generate_signal)
        self.transmit_btn.clicked.connect(self.transmit_once)
        self.start_repeat_btn.clicked.connect(self.start_repeat_transmission)
        self.stop_btn.clicked.connect(self.stop_transmission)
        
        # Connect internal signals
        self.signal_generated.connect(self._on_signal_generated)
        self.transmission_started.connect(self._on_transmission_started)
        self.transmission_stopped.connect(self._on_transmission_stopped)

    def generate_signal(self):
        """Generate TPMS signal based on current settings."""
        try:
            encoder = self.encoder_panel.get_encoder()
            params = self.encoder_panel.get_parameters()
            
            if not encoder or not params:
                self.log("Please configure encoder parameters")
                return
            
            # Generate the signal
            signal_bits = encoder.encode_message(**params)
            signal_pulse = encoder.pulse_encode_message(signal_bits)
            self.current_signal = signal_pulse
            
            self.log(f"Generated {len(signal_bits)} bit signal for {encoder.protocol_name}")
            self.signal_generated.emit(signal_pulse)
            
        except Exception as e:
            self.log(f"Error generating signal: {str(e)}")

    def transmit_once(self):
        """Transmit the current signal once."""
        if not self.current_signal:
            self.log("No signal generated. Please generate signal first.")
            return
        
        self._perform_transmission()

    def start_repeat_transmission(self):
        """Start repeated transmission."""
        if not self.current_signal:
            self.log("No signal generated. Please generate signal first.")
            return
        
        if not self.repetition_panel.is_repeat_enabled():
            self.transmit_once()
            return
        
        self.is_transmitting = True
        interval_ms = int(self.repetition_panel.get_interval() * 1000)
        self.repeat_timer.start(interval_ms)
        
        self.transmission_started.emit()
        self.log(f"Started repeat transmission every {self.repetition_panel.get_interval():.1f}s")
        
        # Transmit immediately
        self._transmit_once()

    def stop_transmission(self):
        """Stop repeat transmission."""
        if self.repeat_timer.isActive():
            self.repeat_timer.stop()
        
        self.is_transmitting = False
        
        # Clean up transmitter when stopping
        if self.current_transmitter is not None:
            try:
                self.current_transmitter.__exit__(None, None, None)
            except:
                pass
            self.current_transmitter = None
            self.current_transmitter_config = None
        
        self.transmission_stopped.emit()
        self.log("Transmission stopped")

    def _transmit_once(self):
        """Internal method to perform one transmission."""
        if self.current_signal:
            self._perform_transmission()

    def _perform_transmission(self):
        """Perform the actual transmission."""
        try:
            transmitter_config = self.transmission_panel.get_transmitter_config()
            
            # Validate configuration
            is_valid, error_msg = self.transmission_panel.validate_config()
            if not is_valid:
                self.log(f"Transmission config error: {error_msg}")
                return
            
            # Create modulated signal
            encoder = self.encoder_panel.get_encoder()
            if not encoder:
                self.log("No encoder selected")
                return
            
            # Create FSK modulated samples
            modulator = FSKModulator(
                mark=35000,
                space=-35000,
                sample_rate=transmitter_config['sample_rate'],
                symbol_duration=encoder.BIT_DURATION,
            )
            
            iq_samples = modulator.generate_fsk_iq(self.current_signal, padding=0)
            
            # Check if we need to create a new transmitter or can reuse existing one
            if (self.current_transmitter is None or 
                self.current_transmitter_config != transmitter_config):
                
                # Clean up old transmitter if it exists
                if self.current_transmitter is not None:
                    try:
                        self.current_transmitter.__exit__(None, None, None)
                    except:
                        pass
                
                # Create new transmitter
                self.current_transmitter = TransmitterFactory.create_transmitter(
                    transmitter_type=transmitter_config['type'],
                    center_freq=transmitter_config['center_freq'],
                    sample_rate=transmitter_config['sample_rate'],
                    gain=transmitter_config['gain'],
                    device_args=transmitter_config['device_args'],
                    channel=transmitter_config['channel'],
                    antenna=transmitter_config['antenna']
                )
                self.current_transmitter_config = transmitter_config.copy()
                self.log(f"Initialized {transmitter_config['type'].upper()} transmitter")
            
            # Transmit using existing transmitter (no context manager)
            self.current_transmitter.transmit_samples(
                iq_samples, 
                repeat=1, 
                scale=transmitter_config['scale']
            )
            
            self.log(f"Transmitted via {transmitter_config['type'].upper()} "
                    f"on {transmitter_config['center_freq']/1e6:.3f} MHz")
            
        except Exception as e:
            self.log(f"Transmission error: {str(e)}")
            # Clean up transmitter on error
            if self.current_transmitter is not None:
                try:
                    self.current_transmitter.__exit__(None, None, None)
                except:
                    pass
                self.current_transmitter = None
                self.current_transmitter_config = None

    def _on_signal_generated(self, signal_bits):
        """Handle signal generation completion."""
        self.transmit_btn.setEnabled(True)
        self.start_repeat_btn.setEnabled(True)

    def _on_transmission_started(self):
        """Handle transmission start."""
        self.generate_btn.setEnabled(False)
        self.transmit_btn.setEnabled(False)
        self.start_repeat_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def _on_transmission_stopped(self):
        """Handle transmission stop."""
        self.generate_btn.setEnabled(True)
        if self.current_signal:
            self.transmit_btn.setEnabled(True)
            self.start_repeat_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def log(self, message: str):
        """Add message to log area."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_area.append(f"[{timestamp}] {message}")

    def closeEvent(self, event):
        """Handle window close event."""
        self.stop_transmission()
        
        # Final cleanup of transmitter
        if self.current_transmitter is not None:
            try:
                self.current_transmitter.__exit__(None, None, None)
            except:
                pass
        
        event.accept()


def main():
    """Run the GUI application."""
    app = QApplication(sys.argv)
    window = TPMSMainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()