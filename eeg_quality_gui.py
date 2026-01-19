"""
EEG Quality Check GUI
=====================
Modern PyQt5-based GUI for EEG preprocessing and quality assessment.

Features:
- Multiple preprocessing methods (Traditional, GEDAI, Both)
- Comprehensive quality metrics
- Before/After comparison
- Method comparison
- Interactive visualizations
- Export functionality
"""

import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QRadioButton, QButtonGroup,
    QProgressBar, QTextEdit, QTabWidget, QGroupBox, QScrollArea,
    QGridLayout, QMessageBox, QSplitter, QFrame
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon

import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

import mne
from quality_metrics import EEGQualityMetrics
from preprocessing import preprocess_eeg


class ProcessingThread(QThread):
    """Background thread for EEG processing."""

    progress = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, file_path, method):
        super().__init__()
        self.file_path = file_path
        self.method = method

    def run(self):
        """Run preprocessing and quality analysis."""
        try:
            # Load data
            self.progress.emit(10, "Loading EEG data...")
            raw = mne.io.read_raw_eeglab(self.file_path, preload=True, verbose=False)

            # Calculate quality metrics for original data
            self.progress.emit(20, "Calculating quality metrics for original data...")
            quality_original = EEGQualityMetrics(raw.copy())
            metrics_original = quality_original.calculate_all_metrics()

            # Preprocess
            self.progress.emit(40, f"Preprocessing with {self.method} method...")
            results = preprocess_eeg(raw, method=self.method.lower(), verbose=False)

            # Calculate quality metrics for processed data
            self.progress.emit(70, "Calculating quality metrics for processed data...")
            processed_metrics = {}

            for method_key, result in results.items():
                quality_processed = EEGQualityMetrics(result['data'])
                processed_metrics[method_key] = quality_processed.calculate_all_metrics()

            self.progress.emit(90, "Finalizing results...")

            # Prepare output
            output = {
                'raw': raw,
                'processed': {key: res['data'] for key, res in results.items()},
                'logs': {key: res['log'] for key, res in results.items()},
                'metrics_original': metrics_original,
                'metrics_processed': processed_metrics,
                'method': self.method
            }

            self.progress.emit(100, "Processing complete!")
            self.finished.emit(output)

        except Exception as e:
            self.error.emit(str(e))


class MetricsWidget(QWidget):
    """Widget to display quality metrics."""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Title
        title = QLabel("Quality Metrics")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)

        # Metrics display area
        self.metrics_text = QTextEdit()
        self.metrics_text.setReadOnly(True)
        self.metrics_text.setFont(QFont("Courier", 10))
        layout.addWidget(self.metrics_text)

        self.setLayout(layout)

    def display_metrics(self, metrics, title="Metrics"):
        """Display metrics in text format."""
        quality_calc = EEGQualityMetrics(None)  # Dummy object for report generation
        report = quality_calc.generate_report(metrics)
        self.metrics_text.setPlainText(f"{title}\n\n{report}")


class ComparisonWidget(QWidget):
    """Widget to compare metrics between methods."""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Title
        title = QLabel("Method Comparison")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)

        # Comparison display
        self.comparison_text = QTextEdit()
        self.comparison_text.setReadOnly(True)
        self.comparison_text.setFont(QFont("Courier", 10))
        layout.addWidget(self.comparison_text)

        self.setLayout(layout)

    def display_comparison(self, metrics_dict):
        """Display comparison between methods."""
        report = []
        report.append("=" * 70)
        report.append("METHOD COMPARISON REPORT")
        report.append("=" * 70)
        report.append("")

        # Get method names
        methods = list(metrics_dict.keys())

        if len(methods) < 2:
            report.append("Need at least 2 methods to compare.")
            self.comparison_text.setPlainText("\n".join(report))
            return

        # Overall scores
        report.append("OVERALL QUALITY SCORES:")
        report.append("-" * 70)
        scores = {}
        for method in methods:
            score = metrics_dict[method]['data_quality_score']
            grade = metrics_dict[method]['quality_grade']
            scores[method] = score
            report.append(f"{method.upper():15s} : {score:6.2f}/100  ({grade})")

        # Determine winner
        best_method = max(scores, key=scores.get)
        report.append("")
        report.append(f"BEST METHOD: {best_method.upper()} (Score: {scores[best_method]:.2f})")
        report.append("")

        # Detailed comparison
        report.append("DETAILED METRIC COMPARISON:")
        report.append("-" * 70)

        # SNR
        report.append("\n1. Signal-to-Noise Ratio (SNR):")
        for method in methods:
            snr = metrics_dict[method]['snr']
            report.append(f"   {method:15s}: {snr:8.2f} dB")

        # PSD Slope
        report.append("\n2. PSD Slope (Quality Indicator):")
        for method in methods:
            slope = metrics_dict[method]['psd_slope']['mean_slope']
            quality = metrics_dict[method]['psd_slope']['quality']
            report.append(f"   {method:15s}: {slope:8.4f} ({quality})")

        # Artifacts
        report.append("\n3. Artifact Percentage:")
        for method in methods:
            artifact_pct = metrics_dict[method]['artifact_percentage']['estimated_total']
            report.append(f"   {method:15s}: {artifact_pct:7.2f}%")

        # Bad channels
        report.append("\n4. Bad Channels:")
        for method in methods:
            bad_ch = metrics_dict[method]['bad_channels']['count']
            bad_ch_pct = metrics_dict[method]['bad_channels']['percentage']
            report.append(f"   {method:15s}: {bad_ch:3d} channels ({bad_ch_pct:.1f}%)")

        # Kurtosis
        report.append("\n5. Kurtosis (Artifact Indicator):")
        for method in methods:
            kurt = metrics_dict[method]['kurtosis']['mean']
            report.append(f"   {method:15s}: {kurt:8.2f}")

        # Alpha/Delta Ratio
        report.append("\n6. Alpha/Delta Ratio:")
        for method in methods:
            ratio = metrics_dict[method]['frequency_bands']['alpha_delta_ratio']
            report.append(f"   {method:15s}: {ratio:8.2f}")

        # Channel Correlation
        report.append("\n7. Channel Correlation:")
        for method in methods:
            corr = metrics_dict[method]['channel_correlation']['mean']
            report.append(f"   {method:15s}: {corr:8.3f}")

        report.append("")
        report.append("=" * 70)

        # Score improvements
        report.append("\nIMPROVEMENT SUMMARY:")
        report.append("-" * 70)

        if 'traditional' in methods and 'gedai' in methods:
            trad_score = scores['traditional']
            gedai_score = scores['gedai']
            improvement = gedai_score - trad_score
            pct_improvement = (improvement / trad_score) * 100 if trad_score > 0 else 0

            if improvement > 0:
                report.append(f"GEDAI outperformed Traditional by {improvement:.2f} points ({pct_improvement:.1f}%)")
            elif improvement < 0:
                report.append(f"Traditional outperformed GEDAI by {abs(improvement):.2f} points ({abs(pct_improvement):.1f}%)")
            else:
                report.append("Both methods achieved similar quality scores")

        report.append("")
        report.append("=" * 70)

        self.comparison_text.setPlainText("\n".join(report))


class VisualizationWidget(QWidget):
    """Widget for data visualization."""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Create matplotlib figure
        self.figure = Figure(figsize=(12, 8))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        self.setLayout(layout)

    def plot_comparison(self, raw, processed_dict, method):
        """Plot before/after comparison."""
        self.figure.clear()

        # Number of subplots depends on method
        if method.lower() == 'both':
            n_methods = len(processed_dict)
            self.figure.set_size_inches(14, 4 * (n_methods + 1))

            # Original data
            ax1 = self.figure.add_subplot(n_methods + 1, 2, 1)
            ax2 = self.figure.add_subplot(n_methods + 1, 2, 2)

            self._plot_raw_data(raw, ax1, "Original Signal (First 10s)")
            self._plot_psd(raw, ax2, "Original PSD")

            # Processed data for each method
            for idx, (method_name, processed) in enumerate(processed_dict.items()):
                ax3 = self.figure.add_subplot(n_methods + 1, 2, (idx + 1) * 2 + 1)
                ax4 = self.figure.add_subplot(n_methods + 1, 2, (idx + 1) * 2 + 2)

                self._plot_raw_data(processed, ax3, f"{method_name.capitalize()} - Cleaned Signal")
                self._plot_psd(processed, ax4, f"{method_name.capitalize()} - Cleaned PSD")

        else:
            # Single method
            processed = list(processed_dict.values())[0]
            method_name = list(processed_dict.keys())[0]

            ax1 = self.figure.add_subplot(2, 2, 1)
            ax2 = self.figure.add_subplot(2, 2, 2)
            ax3 = self.figure.add_subplot(2, 2, 3)
            ax4 = self.figure.add_subplot(2, 2, 4)

            self._plot_raw_data(raw, ax1, "Original Signal (First 10s)")
            self._plot_psd(raw, ax2, "Original PSD")
            self._plot_raw_data(processed, ax3, f"{method_name.capitalize()} - Cleaned Signal")
            self._plot_psd(processed, ax4, f"{method_name.capitalize()} - Cleaned PSD")

        self.figure.tight_layout()
        self.canvas.draw()

    def _plot_raw_data(self, raw, ax, title):
        """Plot raw EEG signal."""
        try:
            # Get first 10 seconds of data
            duration = min(10, raw.times[-1])
            data, times = raw[:, :int(duration * raw.info['sfreq'])]

            # Plot first few channels
            n_channels = min(5, len(raw.ch_names))
            for i in range(n_channels):
                # Offset each channel for visibility
                offset = i * np.std(data) * 3
                ax.plot(times, data[i] * 1e6 + offset, linewidth=0.5, label=raw.ch_names[i])

            ax.set_xlabel('Time (s)')
            ax.set_ylabel('Amplitude (µV)')
            ax.set_title(title)
            ax.legend(loc='upper right', fontsize=8)
            ax.grid(True, alpha=0.3)
        except Exception as e:
            ax.text(0.5, 0.5, f"Error plotting: {e}", ha='center', va='center', transform=ax.transAxes)

    def _plot_psd(self, raw, ax, title):
        """Plot Power Spectral Density."""
        try:
            psd, freqs = mne.time_frequency.psd_array_welch(
                raw.get_data(), sfreq=raw.info['sfreq'],
                fmin=0.5, fmax=80, n_fft=2048, verbose=False
            )

            # Average across channels and convert to dB
            psd_mean = np.mean(psd, axis=0)
            psd_db = 10 * np.log10(psd_mean)

            ax.plot(freqs, psd_db, linewidth=2)
            ax.set_xlabel('Frequency (Hz)')
            ax.set_ylabel('Power (dB)')
            ax.set_title(title)
            ax.grid(True, alpha=0.3)

            # Mark frequency bands
            bands = [
                (1, 4, 'Delta', 'lightblue'),
                (4, 8, 'Theta', 'lightgreen'),
                (8, 13, 'Alpha', 'yellow'),
                (13, 30, 'Beta', 'orange'),
                (30, 80, 'Gamma', 'pink')
            ]

            ylim = ax.get_ylim()
            for fmin, fmax, name, color in bands:
                ax.axvspan(fmin, fmax, alpha=0.1, color=color, label=name)

            # Add legend with small font
            ax.legend(loc='upper right', fontsize=7)

        except Exception as e:
            ax.text(0.5, 0.5, f"Error plotting PSD: {e}", ha='center', va='center', transform=ax.transAxes)


class EEGQualityCheckGUI(QMainWindow):
    """Main GUI application."""

    def __init__(self):
        super().__init__()
        self.file_path = None
        self.results = None
        self.processing_thread = None
        self.init_ui()

    def init_ui(self):
        """Initialize user interface."""
        self.setWindowTitle("EEG Quality Check - Professional Edition")
        self.setGeometry(100, 100, 1400, 900)

        # Set style
        self.set_style()

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Header
        header = self.create_header()
        main_layout.addWidget(header)

        # File selection section
        file_section = self.create_file_section()
        main_layout.addWidget(file_section)

        # Method selection section
        method_section = self.create_method_section()
        main_layout.addWidget(method_section)

        # Process button and progress
        process_section = self.create_process_section()
        main_layout.addWidget(process_section)

        # Results section (tabs)
        self.results_tabs = QTabWidget()
        self.results_tabs.setEnabled(False)
        main_layout.addWidget(self.results_tabs)

        # Create result tabs
        self.create_result_tabs()

        # Status bar
        self.statusBar().showMessage("Ready")

    def set_style(self):
        """Set modern stylesheet."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                text-align: center;
                font-size: 14px;
                border-radius: 5px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QRadioButton {
                font-size: 12px;
                spacing: 5px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
            QLabel#header {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
            }
            QLabel#subheader {
                font-size: 14px;
                color: #7f8c8d;
                padding: 5px;
            }
            QProgressBar {
                border: 2px solid #cccccc;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
            }
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 5px;
                font-family: 'Courier New';
                padding: 5px;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background-color: white;
                border-radius: 5px;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: #4CAF50;
                color: white;
            }
        """)

    def create_header(self):
        """Create header section."""
        header_widget = QWidget()
        header_layout = QVBoxLayout()

        title = QLabel("EEG Quality Check & Preprocessing")
        title.setObjectName("header")
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("Professional Edition - Compare Traditional & GEDAI Methods")
        subtitle.setObjectName("subheader")
        subtitle.setAlignment(Qt.AlignCenter)

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        header_widget.setLayout(header_layout)

        return header_widget

    def create_file_section(self):
        """Create file selection section."""
        group = QGroupBox("1. Select EEG Data File")

        layout = QHBoxLayout()

        self.file_label = QLabel("No file selected")
        self.file_label.setStyleSheet("color: #7f8c8d; font-style: italic;")

        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.browse_file)

        layout.addWidget(QLabel("File:"))
        layout.addWidget(self.file_label, 1)
        layout.addWidget(self.browse_btn)

        group.setLayout(layout)
        return group

    def create_method_section(self):
        """Create method selection section."""
        group = QGroupBox("2. Select Preprocessing Method")

        layout = QVBoxLayout()

        self.method_group = QButtonGroup()

        # Traditional method
        self.trad_radio = QRadioButton("Traditional (Filtering + ICA)")
        self.trad_radio.setToolTip("Standard preprocessing: Filtering, bad channel detection, and ICA")
        self.method_group.addButton(self.trad_radio, 0)

        # GEDAI method
        self.gedai_radio = QRadioButton("GEDAI (ASR + ICA with ICLabel)")
        self.gedai_radio.setToolTip("Advanced preprocessing: ASR artifact removal + ICA with automatic labeling")
        self.gedai_radio.setChecked(True)
        self.method_group.addButton(self.gedai_radio, 1)

        # Both methods
        self.both_radio = QRadioButton("Both (Compare Methods)")
        self.both_radio.setToolTip("Run both methods and compare results")
        self.method_group.addButton(self.both_radio, 2)

        layout.addWidget(self.trad_radio)
        layout.addWidget(self.gedai_radio)
        layout.addWidget(self.both_radio)

        # Add descriptions
        desc_label = QLabel(
            "<b>Traditional:</b> Standard pipeline used in most EEG research<br>"
            "<b>GEDAI:</b> Advanced artifact removal using ASR (Artifact Subspace Reconstruction)<br>"
            "<b>Both:</b> Compare both methods side-by-side to determine which works better for your data"
        )
        desc_label.setStyleSheet("color: #555; font-size: 11px; padding: 10px;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        group.setLayout(layout)
        return group

    def create_process_section(self):
        """Create processing section."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Process button
        self.process_btn = QPushButton("🚀 Start Processing")
        self.process_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                padding: 15px 30px;
                background-color: #2196F3;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.process_btn.clicked.connect(self.start_processing)
        self.process_btn.setEnabled(False)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)

        # Progress label
        self.progress_label = QLabel("")
        self.progress_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.process_btn, alignment=Qt.AlignCenter)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.progress_label)

        widget.setLayout(layout)
        return widget

    def create_result_tabs(self):
        """Create result tabs."""
        # Original Metrics Tab
        self.original_metrics_widget = MetricsWidget()
        self.results_tabs.addTab(self.original_metrics_widget, "📊 Original Data Metrics")

        # Processed Metrics Tabs (will be created dynamically)
        self.processed_metrics_widgets = {}

        # Visualization Tab
        self.viz_widget = VisualizationWidget()
        self.results_tabs.addTab(self.viz_widget, "📈 Visualizations")

        # Processing Logs Tab
        self.logs_widget = QTextEdit()
        self.logs_widget.setReadOnly(True)
        self.logs_widget.setFont(QFont("Courier", 9))
        self.results_tabs.addTab(self.logs_widget, "📝 Processing Logs")

    def browse_file(self):
        """Open file browser."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select EEG Data File",
            "",
            "EEGLAB Files (*.set);;All Files (*)"
        )

        if file_path:
            self.file_path = file_path
            self.file_label.setText(os.path.basename(file_path))
            self.file_label.setStyleSheet("color: #2c3e50; font-weight: bold;")
            self.process_btn.setEnabled(True)
            self.statusBar().showMessage(f"Loaded: {file_path}")

    def start_processing(self):
        """Start processing in background thread."""
        if not self.file_path:
            QMessageBox.warning(self, "No File", "Please select a file first!")
            return

        # Determine method
        if self.trad_radio.isChecked():
            method = "Traditional"
        elif self.gedai_radio.isChecked():
            method = "GEDAI"
        else:
            method = "Both"

        # Disable UI during processing
        self.process_btn.setEnabled(False)
        self.browse_btn.setEnabled(False)
        self.trad_radio.setEnabled(False)
        self.gedai_radio.setEnabled(False)
        self.both_radio.setEnabled(False)

        # Reset progress
        self.progress_bar.setValue(0)
        self.progress_label.setText("Initializing...")

        # Start processing thread
        self.processing_thread = ProcessingThread(self.file_path, method)
        self.processing_thread.progress.connect(self.update_progress)
        self.processing_thread.finished.connect(self.processing_finished)
        self.processing_thread.error.connect(self.processing_error)
        self.processing_thread.start()

    def update_progress(self, value, message):
        """Update progress bar."""
        self.progress_bar.setValue(value)
        self.progress_label.setText(message)
        self.statusBar().showMessage(message)

    def processing_finished(self, results):
        """Handle processing completion."""
        self.results = results

        # Display original metrics
        self.original_metrics_widget.display_metrics(
            results['metrics_original'],
            "Original Data Quality Metrics"
        )

        # Display processed metrics
        # Remove old processed tabs
        for i in range(self.results_tabs.count() - 1, 0, -1):
            widget = self.results_tabs.widget(i)
            if widget not in [self.original_metrics_widget, self.viz_widget, self.logs_widget]:
                self.results_tabs.removeTab(i)

        # Add new processed metrics tabs
        for idx, (method_name, metrics) in enumerate(results['metrics_processed'].items()):
            metrics_widget = MetricsWidget()
            metrics_widget.display_metrics(
                metrics,
                f"{method_name.capitalize()} - Processed Data Quality Metrics"
            )
            # Insert before visualization tab
            self.results_tabs.insertTab(
                1 + idx,
                metrics_widget,
                f"✅ {method_name.capitalize()} Metrics"
            )

        # If both methods, add comparison tab
        if results['method'].lower() == 'both':
            comparison_widget = ComparisonWidget()
            comparison_widget.display_comparison(results['metrics_processed'])
            self.results_tabs.insertTab(
                1 + len(results['metrics_processed']),
                comparison_widget,
                "⚖️ Method Comparison"
            )

        # Display visualizations
        self.viz_widget.plot_comparison(
            results['raw'],
            results['processed'],
            results['method']
        )

        # Display logs
        log_text = []
        for method_name, log in results['logs'].items():
            log_text.append(f"{'=' * 60}")
            log_text.append(f"{method_name.upper()} PROCESSING LOG")
            log_text.append(f"{'=' * 60}")
            log_text.append(log)
            log_text.append("\n")
        self.logs_widget.setPlainText("\n".join(log_text))

        # Enable results tabs
        self.results_tabs.setEnabled(True)

        # Re-enable UI
        self.process_btn.setEnabled(True)
        self.browse_btn.setEnabled(True)
        self.trad_radio.setEnabled(True)
        self.gedai_radio.setEnabled(True)
        self.both_radio.setEnabled(True)

        # Show completion message
        QMessageBox.information(
            self,
            "Processing Complete",
            f"EEG data processing completed successfully!\n\n"
            f"Method: {results['method']}\n"
            f"Original Quality Score: {results['metrics_original']['data_quality_score']:.1f}/100\n"
        )

        self.statusBar().showMessage("Processing complete! View results in tabs above.")

    def processing_error(self, error_msg):
        """Handle processing error."""
        QMessageBox.critical(
            self,
            "Processing Error",
            f"An error occurred during processing:\n\n{error_msg}"
        )

        # Re-enable UI
        self.process_btn.setEnabled(True)
        self.browse_btn.setEnabled(True)
        self.trad_radio.setEnabled(True)
        self.gedai_radio.setEnabled(True)
        self.both_radio.setEnabled(True)

        self.progress_bar.setValue(0)
        self.progress_label.setText("")
        self.statusBar().showMessage("Processing failed")


def main():
    """Main entry point."""
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle('Fusion')

    # Create and show GUI
    gui = EEGQualityCheckGUI()
    gui.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
