# EEG Quality Check & Preprocessing - Professional Edition

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-green.svg)
![MNE](https://img.shields.io/badge/MNE-Latest-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

**A modern, GUI-based EEG preprocessing and quality assessment tool with comprehensive metrics and method comparison.**

</div>

---

## 🌟 Features

### ✨ Modern GUI Interface
- **Intuitive PyQt5-based interface** with professional styling
- **Real-time progress tracking** with detailed status updates
- **Interactive visualizations** with matplotlib integration
- **Tabbed results display** for easy navigation

### 🔬 Comprehensive Quality Metrics
Industry-standard EEG quality metrics including:
- **Signal-to-Noise Ratio (SNR)** - Measures data quality
- **PSD Slope Analysis** - 1/f noise characteristics
- **Artifact Detection** - Amplitude and gradient-based
- **Bad Channel Detection** - Variance-based identification
- **Kurtosis Analysis** - Outlier and artifact indicator
- **Frequency Band Powers** - Delta, Theta, Alpha, Beta, Gamma
- **Channel Correlation** - Inter-channel relationship analysis
- **Overall Quality Score** - Weighted composite score (0-100)
- **Quality Grade** - Letter grade from F to A+

### 🛠️ Two Preprocessing Methods

#### 1️⃣ **Traditional Method**
Standard EEG preprocessing pipeline used in most research:
- Channel selection and referencing
- Bandpass filtering (1-80 Hz)
- Notch filtering (60 Hz power line)
- Bad channel detection and interpolation
- ICA (Independent Component Analysis)
- Artifact component removal

#### 2️⃣ **GEDAI Method** (Advanced)
State-of-the-art preprocessing with ASR:
- Channel selection and referencing
- Bandpass filtering (1-80 Hz)
- Notch filtering (60 Hz)
- **ASR (Artifact Subspace Reconstruction)** - Advanced artifact removal
- ICA with **ICLabel** - Automatic component classification
- Brain vs. artifact component separation

### 📊 Before/After Comparison
- **Visual comparison** of raw vs. cleaned signals
- **PSD (Power Spectral Density)** plots
- **Frequency band analysis** with visual markers
- **Side-by-side metrics** comparison

### ⚖️ Method Comparison
When "Both" methods are selected:
- **Head-to-head comparison** of Traditional vs. GEDAI
- **Detailed metric-by-metric analysis**
- **Winner determination** based on quality scores
- **Improvement percentages** and recommendations

---

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/EEG_Preprocessing-and-Quality-Check.git
cd EEG_Preprocessing-and-Quality-Check
```

### Step 2: Create Virtual Environment (Recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Required Packages
- **mne** - EEG data processing
- **PyQt5** - GUI framework
- **numpy** - Numerical computations
- **scipy** - Scientific computing
- **matplotlib** - Visualization
- **asrpy** - ASR artifact removal (for GEDAI method)
- **mne-icalabel** - Automatic ICA component labeling

---

## 🚀 Usage

### Launch the GUI
```bash
python eeg_quality_gui.py
```

### Step-by-Step Guide

1. **Select EEG Data File**
   - Click "Browse..." button
   - Select an EEGLAB `.set` file
   - File path will be displayed

2. **Choose Preprocessing Method**
   - **Traditional**: Standard filtering + ICA
   - **GEDAI**: ASR + ICA with ICLabel (Recommended)
   - **Both**: Compare both methods side-by-side

3. **Start Processing**
   - Click "🚀 Start Processing" button
   - Monitor progress bar and status messages
   - Processing time varies based on data size and method

4. **View Results**
   - **Original Data Metrics**: Quality assessment of raw data
   - **Processed Metrics**: Quality assessment after cleaning
   - **Visualizations**: Before/after signal and PSD plots
   - **Processing Logs**: Detailed step-by-step logs
   - **Method Comparison** (if "Both" selected): Side-by-side analysis

---

## 📊 Understanding Quality Metrics

### Overall Quality Score (0-100)
A weighted composite score based on multiple metrics:
- **90-100**: Excellent (A+) - Research-grade data
- **80-89**: Very Good (A) - High quality, minimal artifacts
- **70-79**: Good (B) - Acceptable for most analyses
- **60-69**: Fair (C) - May require additional cleaning
- **50-59**: Poor (D) - Significant artifacts present
- **0-49**: Very Poor (F) - Consider data re-collection

### Key Metrics Explained

#### Signal-to-Noise Ratio (SNR)
- Measures signal quality vs. high-frequency noise
- **Higher is better** (>10 dB is good)
- Low SNR indicates noisy data

#### PSD Slope
- Characterizes 1/f noise properties
- **More negative is better** (steeper slope)
- Slope ≥ 0: Garbage quality
- Slope < -0.3: Excellent quality

#### Artifact Percentage
- Estimates data contaminated by artifacts
- **Lower is better** (<10% is excellent)
- Based on amplitude and gradient analysis

#### Bad Channels
- Channels with abnormal variance
- **Fewer is better** (<10% channels)
- Automatically detected and interpolated

#### Kurtosis
- Measures distribution tailedness
- **Lower absolute value is better**
- High kurtosis indicates outliers/artifacts

#### Frequency Band Powers
- Power in standard EEG bands
- **Alpha/Delta Ratio**: Alertness indicator
- Helps identify data quality issues

---

## 🔧 Advanced Usage

### Command-Line API
You can also use the preprocessing modules programmatically:

```python
import mne
from preprocessing import preprocess_eeg
from quality_metrics import EEGQualityMetrics

# Load data
raw = mne.io.read_raw_eeglab('your_file.set', preload=True)

# Preprocess with GEDAI method
results = preprocess_eeg(raw, method='gedai', verbose=True)
cleaned_data = results['gedai']['data']

# Calculate quality metrics
metrics_calc = EEGQualityMetrics(cleaned_data)
metrics = metrics_calc.calculate_all_metrics()

# Generate report
report = metrics_calc.generate_report(metrics)
print(report)
```

### Batch Processing
Process multiple files programmatically:

```python
import glob
from preprocessing import preprocess_eeg

# Get all .set files
files = glob.glob('data/*.set')

for file_path in files:
    raw = mne.io.read_raw_eeglab(file_path, preload=True)
    results = preprocess_eeg(raw, method='both', verbose=False)

    # Save results
    output_name = file_path.replace('.set', '_cleaned.fif')
    results['gedai']['data'].save(output_name, overwrite=True)
```

---

## 📁 File Structure

```
EEG_Preprocessing-and-Quality-Check/
├── eeg_quality_gui.py           # Main GUI application
├── preprocessing.py              # Preprocessing pipelines
├── quality_metrics.py            # Quality metrics calculation
├── requirements.txt              # Python dependencies
├── README.md                     # This file
├── Test.png                      # Example visualization
├── Pre-processing and Quality check  # Original script (legacy)
└── processed/                    # Output directory
```

---

## 🎯 Quality Metrics Technical Details

### Calculation Methods

#### SNR Calculation
```
SNR (dB) = 10 × log₁₀(Signal Power / Noise Power)
Signal: 8-13 Hz (Alpha band)
Noise: 50-100 Hz (High-frequency noise)
```

#### PSD Slope Calculation
```
1. Compute PSD using Welch method (1-80 Hz)
2. Convert to dB: PSD_dB = 10 × log₁₀(PSD)
3. Fit linear regression: slope = Δ(PSD_dB) / Δ(frequency)
4. Mean slope across all channels
```

#### Artifact Detection
- **Amplitude-based**: Threshold at 5× standard deviation
- **Gradient-based**: Detect sudden jumps >5× median gradient
- **Combined estimate**: Maximum of both methods

#### Bad Channel Detection
- **Low variance**: <10% of median variance (flat channel)
- **High variance**: >10× median variance (noisy channel)
- **Correlation-based**: Can be enabled for detailed analysis

---

## 🐛 Troubleshooting

### Common Issues

#### 1. "ASR not available" Warning
```bash
# Install asrpy
pip install asrpy
```

#### 2. "ICLabel not available" Warning
```bash
# Install mne-icalabel
pip install mne-icalabel
```

#### 3. Qt Platform Plugin Error
```bash
# On Linux, install Qt dependencies
sudo apt-get install python3-pyqt5
```

#### 4. Memory Error with Large Files
- Close other applications
- Process files individually
- Reduce data length (crop before processing)

#### 5. Slow Processing
- GEDAI method with ASR is computationally intensive
- Traditional method is faster
- Processing time varies: 30s to 5 minutes depending on file size

---

## 📚 References

### Methods and Algorithms

1. **ASR (Artifact Subspace Reconstruction)**
   - Mullen, T. R., et al. (2015). Real-time neuroimaging and cognitive monitoring using wearable dry EEG. IEEE Transactions on Biomedical Engineering.

2. **ICLabel**
   - Pion-Tonachini, L., et al. (2019). ICLabel: An automated electroencephalographic independent component classifier, dataset, and website. NeuroImage.

3. **MNE-Python**
   - Gramfort, A., et al. (2013). MEG and EEG data analysis with MNE-Python. Frontiers in Neuroscience.

4. **ICA (Independent Component Analysis)**
   - Makeig, S., et al. (1996). Independent component analysis of electroencephalographic data. Advances in Neural Information Processing Systems.

5. **Power Spectral Density Analysis**
   - Welch, P. (1967). The use of fast Fourier transform for the estimation of power spectra. IEEE Transactions on Audio and Electroacoustics.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

### Development Setup
```bash
git clone https://github.com/yourusername/EEG_Preprocessing-and-Quality-Check.git
cd EEG_Preprocessing-and-Quality-Check
pip install -r requirements.txt
pip install -e .  # Editable installation
```

---

## 📄 License

This project is licensed under the MIT License. See LICENSE file for details.

---

## 👨‍💻 Author

**Your Name**
- GitHub: [@yourusername](https://github.com/yourusername)
- Email: your.email@example.com

---

## 🙏 Acknowledgments

- MNE-Python team for excellent EEG processing tools
- SCCN (Swartz Center for Computational Neuroscience) for EEGLAB and related tools
- ASR developers for artifact removal algorithms
- ICLabel team for automatic component classification
- PyQt5 developers for the GUI framework

---

## 📊 Screenshots

### Main Interface
![Main GUI](docs/screenshot_main.png)

### Quality Metrics Display
![Quality Metrics](docs/screenshot_metrics.png)

### Method Comparison
![Method Comparison](docs/screenshot_comparison.png)

### Visualizations
![Visualizations](Test.png)

---

## 🔮 Future Enhancements

- [ ] Support for more file formats (BDF, EDF, FIF)
- [ ] Real-time EEG processing
- [ ] Export to PDF/HTML reports
- [ ] Custom preprocessing pipelines
- [ ] Machine learning-based artifact detection
- [ ] Multi-file batch processing GUI
- [ ] Cloud processing support
- [ ] Plugin system for custom metrics

---

## 📞 Support

If you encounter any issues or have questions:
1. Check the [Troubleshooting](#-troubleshooting) section
2. Search existing [GitHub Issues](https://github.com/yourusername/EEG_Preprocessing-and-Quality-Check/issues)
3. Create a new issue with:
   - Python version
   - Operating system
   - Error message
   - Steps to reproduce

---

<div align="center">

**Made with ❤️ for the EEG research community**

⭐ Star this repo if you find it useful!

</div>
