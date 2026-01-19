# Quick Start Guide

## 🎯 Purpose

This application compares **two EEG preprocessing methods**:

1. **Traditional: Your ASR + ICA Method** (well-established)
2. **GEDAI: New Eigenvalue-Based Method** (novel approach)

Use comprehensive quality metrics to determine which method works better for your data!

---

## 🚀 Installation & Launch

### 1. Install Dependencies
```bash
cd /home/user/EEG_Preprocessing-and-Quality-Check
pip install -r requirements.txt
```

### 2. Launch GUI
```bash
python run_gui.py
```

Or directly:
```bash
python eeg_quality_gui.py
```

---

## 📋 How to Use

### Step 1: Select File
- Click "Browse..." button
- Select your EEGLAB `.set` file
- Example files in `processed/` directory

### Step 2: Choose Method
- **Traditional**: Your ASR + ICA + ICLabel method
- **GEDAI**: New eigenvalue-based denoising
- **Both**: Compare them side-by-side ✅ (Recommended!)

### Step 3: Process
- Click "🚀 Start Processing"
- Wait for completion (30s - 5min depending on file size)

### Step 4: View Results
Navigate through tabs:
- **Original Data Metrics**: Quality before cleaning
- **Traditional Metrics**: Quality after ASR+ICA
- **GEDAI Metrics**: Quality after eigenvalue method
- **Method Comparison**: Which one won? ⭐
- **Visualizations**: See the difference visually
- **Processing Logs**: Detailed step-by-step logs

---

## 📊 Understanding Results

### Quality Score (0-100)
- **90-100**: Excellent (A+)
- **80-89**: Very Good (A)
- **70-79**: Good (B)
- **60-69**: Fair (C)
- **50-59**: Poor (D)
- **0-49**: Very Poor (F)

### Method Comparison
When you select "Both", the app will:
1. Run both methods on your data
2. Calculate quality metrics for each
3. Compare them metric-by-metric
4. Declare a winner based on overall score
5. Show improvement percentages

---

## 🔍 What Each Method Does

### Traditional (ASR + ICA)
Your original method:
1. Filter data (1-80 Hz)
2. Remove power line noise (60 Hz)
3. **ASR**: Removes artifact subspaces
4. **ICA**: Separates independent components
5. **ICLabel**: Automatically identifies artifacts
6. Removes: eye blinks, muscle, heartbeat, noise

**Pros:**
- Well-validated in research
- Fast and reliable
- Good for standard artifacts

### GEDAI (Eigenvalue-Based)
New method:
1. Filter data (1-80 Hz)
2. Remove power line noise (60 Hz)
3. **Compute two covariance matrices:**
   - Signal matrix (1-40 Hz brain activity)
   - Noise matrix (high-freq + derivatives)
4. **Solve eigenvalue problem:** S * v = λ * R * v
5. **Keep brain components**, remove artifact components
6. Automatic threshold selection

**Pros:**
- Uses EEG physics knowledge
- Better signal preservation
- Outperforms ASR/ICA in many cases (per research)

---

## 🎯 Decision Guide

### Use Traditional when:
- ✅ You have standard artifacts (eye blinks, muscle)
- ✅ You want proven, established methods
- ✅ Processing speed is important

### Use GEDAI when:
- ✅ You want to preserve subtle brain signals
- ✅ You have complex artifact patterns
- ✅ You want to try cutting-edge methods

### Use Both when:
- ✅ You want to make a data-driven decision
- ✅ You're not sure which method is better
- ✅ You want to validate your preprocessing choice

---

## 📈 Quality Metrics Explained

The app calculates **10 comprehensive metrics**:

1. **SNR** - Signal-to-Noise Ratio (higher is better)
2. **PSD Slope** - 1/f noise (more negative is better)
3. **Artifacts** - Percentage contaminated (lower is better)
4. **Bad Channels** - Number of problematic channels
5. **Kurtosis** - Outlier indicator (lower is better)
6. **Band Powers** - Delta, Theta, Alpha, Beta, Gamma
7. **Channel Correlation** - Inter-channel relationship
8. **Overall Score** - Weighted composite (0-100)
9. **Quality Grade** - Letter grade (F to A+)
10. **Before/After** - Visual comparison

---

## 🛠️ Troubleshooting

### "ASR not available" warning
```bash
pip install asrpy
```

### "ICLabel not available" warning
```bash
pip install mne-icalabel
```

### Qt Platform Error (Linux)
```bash
sudo apt-get install python3-pyqt5
```

### Memory Error
- Close other applications
- Process smaller files
- Use one method at a time instead of "Both"

---

## 📚 Learn More

- **Full Documentation**: See [README.md](README.md)
- **GEDAI GitHub**: https://github.com/neurotuning/GEDAI-master
- **GED Tutorial**: arXiv:2104.12356
- **ASR Paper**: Mullen et al. (2015)

---

## 💡 Tips

1. **Always compare both methods first** - Don't assume one is better
2. **Look at visualizations** - Numbers don't tell the whole story
3. **Check processing logs** - Understand what each method did
4. **Save your results** - Take screenshots of comparison
5. **Try multiple files** - Method performance may vary by dataset

---

## 🎉 That's It!

You're ready to compare ASR+ICA vs. GEDAI on your EEG data!

**Question:** Which method will work better for your data?
**Answer:** Run the app and find out! 🚀

---

## 📞 Need Help?

- Check [README.md](README.md) for detailed documentation
- Review processing logs for error details
- Verify all dependencies are installed
- Check that your .set files are valid EEGLAB format

**Happy preprocessing!** 🧠✨
