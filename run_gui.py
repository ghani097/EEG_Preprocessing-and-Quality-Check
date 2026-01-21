#!/usr/bin/env python3
"""
Quick Start Script for EEG Quality Check GUI
=============================================
This script launches the EEG Quality Check GUI application.

Usage:
    python run_gui.py

or on Linux/Mac:
    ./run_gui.py
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Check for required dependencies
def check_dependencies():
    """Check if all required dependencies are installed."""
    missing = []

    try:
        import PyQt6
    except ImportError:
        missing.append("PyQt6")

    try:
        import mne
    except ImportError:
        missing.append("mne")

    try:
        import numpy
    except ImportError:
        missing.append("numpy")

    try:
        import scipy
    except ImportError:
        missing.append("scipy")

    try:
        import matplotlib
    except ImportError:
        missing.append("matplotlib")

    if missing:
        print("=" * 70)
        print("ERROR: Missing required dependencies!")
        print("=" * 70)
        print("\nThe following packages are not installed:")
        for pkg in missing:
            print(f"  - {pkg}")
        print("\nPlease install dependencies using:")
        print("  pip install -r requirements.txt")
        print("\n" + "=" * 70)
        sys.exit(1)

    # Check optional dependencies
    optional_missing = []

    try:
        import asrpy
    except ImportError:
        optional_missing.append("asrpy (for GEDAI/ASR method)")

    try:
        import mne_icalabel
    except ImportError:
        optional_missing.append("mne-icalabel (for automatic ICA labeling)")

    if optional_missing:
        print("=" * 70)
        print("WARNING: Optional dependencies not installed")
        print("=" * 70)
        print("\nThe following optional packages are missing:")
        for pkg in optional_missing:
            print(f"  - {pkg}")
        print("\nThe application will work, but some features may be limited.")
        print("To install optional dependencies:")
        print("  pip install asrpy mne-icalabel")
        print("\n" + "=" * 70)
        print()

# Check dependencies
check_dependencies()

# Import and run GUI
try:
    from eeg_quality_gui import main

    print("=" * 70)
    print("EEG Quality Check GUI - Professional Edition")
    print("=" * 70)
    print("\nLaunching application...")
    print()

    main()

except Exception as e:
    print("=" * 70)
    print("ERROR: Failed to launch GUI")
    print("=" * 70)
    print(f"\nError message: {e}")
    print("\nPlease check that all dependencies are correctly installed.")
    print("=" * 70)
    sys.exit(1)
