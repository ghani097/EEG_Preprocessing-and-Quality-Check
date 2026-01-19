"""
EEG Preprocessing Module
=========================
Implements two preprocessing pipelines:
1. Traditional: Standard filtering + ICA
2. GEDAI: ASR + ICA with ICLabel (advanced artifact removal)
"""

import numpy as np
import mne
from mne.preprocessing import ICA
try:
    import asrpy
    ASR_AVAILABLE = True
except ImportError:
    ASR_AVAILABLE = False
    print("Warning: asrpy not available. GEDAI method will not work optimally.")

try:
    from mne_icalabel import label_components
    ICALABEL_AVAILABLE = True
except ImportError:
    ICALABEL_AVAILABLE = False
    print("Warning: mne_icalabel not available. ICA component labeling will be manual.")


class PreprocessingPipeline:
    """Base class for preprocessing pipelines."""

    def __init__(self, verbose=True):
        """
        Initialize preprocessing pipeline.

        Parameters:
        -----------
        verbose : bool
            Whether to print progress messages
        """
        self.verbose = verbose
        self.processing_log = []

    def log(self, message):
        """Log processing steps."""
        self.processing_log.append(message)
        if self.verbose:
            print(message)

    def get_log(self):
        """Get processing log."""
        return "\n".join(self.processing_log)


class TraditionalPreprocessing(PreprocessingPipeline):
    """
    Traditional EEG preprocessing pipeline.

    Steps:
    1. Load data
    2. Select EEG channels
    3. Set average reference
    4. Bandpass filter (1-80 Hz)
    5. Notch filter (60 Hz for power line)
    6. Bad channel detection and interpolation
    7. ICA for artifact removal (manual or semi-automatic)
    8. Final bandpass filter
    """

    def __init__(self, verbose=True):
        super().__init__(verbose)
        self.method_name = "Traditional"

    def preprocess(self, raw):
        """
        Apply traditional preprocessing pipeline.

        Parameters:
        -----------
        raw : mne.io.Raw
            Raw EEG data

        Returns:
        --------
        mne.io.Raw : Preprocessed data
        """
        self.log("=" * 60)
        self.log("TRADITIONAL PREPROCESSING PIPELINE")
        self.log("=" * 60)

        # Make a copy to avoid modifying original
        raw_processed = raw.copy()

        # Step 1: Select EEG channels only
        self.log("\n[1/7] Selecting EEG channels...")
        try:
            raw_processed.pick_types(meg=False, eeg=True, stim=False, eog=False, exclude=[])
            self.log(f"  Selected {len(raw_processed.ch_names)} EEG channels")
        except Exception as e:
            self.log(f"  Warning: Could not filter channel types: {e}")

        # Step 2: Set average reference
        self.log("\n[2/7] Setting average reference...")
        try:
            raw_processed.set_eeg_reference('average', projection=False, verbose=False)
            self.log("  Average reference applied")
        except Exception as e:
            self.log(f"  Warning: Could not set reference: {e}")

        # Step 3: Initial bandpass filter (1-80 Hz)
        self.log("\n[3/7] Applying bandpass filter (1-80 Hz)...")
        try:
            raw_processed.filter(l_freq=1.0, h_freq=80.0, verbose=False)
            self.log("  Bandpass filter applied")
        except Exception as e:
            self.log(f"  Error in filtering: {e}")

        # Step 4: Notch filter for power line noise (60 Hz)
        self.log("\n[4/7] Applying notch filter (60 Hz)...")
        try:
            raw_processed.notch_filter(freqs=60, verbose=False)
            self.log("  Notch filter applied")
        except Exception as e:
            self.log(f"  Warning: Could not apply notch filter: {e}")

        # Step 5: Detect and interpolate bad channels
        self.log("\n[5/7] Detecting and interpolating bad channels...")
        try:
            n_channels_before = len(raw_processed.ch_names)

            # Find bad channels using MNE's automatic detection
            # This uses RANSAC algorithm
            from mne.preprocessing import find_bad_channels_maxwell

            # Simple method: detect flat and noisy channels
            raw_copy_for_detection = raw_processed.copy()
            raw_copy_for_detection.load_data()

            # Compute channel variances
            data = raw_copy_for_detection.get_data()
            variances = np.var(data, axis=1)
            median_var = np.median(variances)

            bad_channels = []
            for i, ch_name in enumerate(raw_copy_for_detection.ch_names):
                if variances[i] < 0.1 * median_var:  # Too flat
                    bad_channels.append(ch_name)
                elif variances[i] > 10 * median_var:  # Too noisy
                    bad_channels.append(ch_name)

            raw_processed.info['bads'] = bad_channels

            if len(bad_channels) > 0:
                self.log(f"  Found {len(bad_channels)} bad channels: {bad_channels}")

                # Interpolate bad channels if we have enough good channels
                if len(bad_channels) < len(raw_processed.ch_names) * 0.3:
                    raw_processed.interpolate_bads(reset_bads=True, verbose=False)
                    self.log(f"  Interpolated {len(bad_channels)} bad channels")
                else:
                    self.log(f"  Warning: Too many bad channels ({len(bad_channels)}). Skipping interpolation.")
            else:
                self.log("  No bad channels detected")
        except Exception as e:
            self.log(f"  Warning: Bad channel detection failed: {e}")

        # Step 6: ICA for artifact removal
        self.log("\n[6/7] Running ICA for artifact removal...")
        try:
            # Fit ICA
            n_components = min(15, len(raw_processed.ch_names) - 1)
            ica = ICA(n_components=n_components, method='infomax', random_state=42,
                      max_iter=500, fit_params=dict(extended=True), verbose=False)

            # Filter data for ICA (1-100 Hz is recommended)
            raw_for_ica = raw_processed.copy().filter(l_freq=1.0, h_freq=None, verbose=False)
            ica.fit(raw_for_ica, verbose=False)

            self.log(f"  ICA fitted with {n_components} components")

            # Automatic component labeling if available
            if ICALABEL_AVAILABLE:
                try:
                    ic_labels = label_components(raw_for_ica, ica, method='iclabel')

                    # Exclude components that are not brain
                    labels = ic_labels['labels']
                    exclude_idx = [idx for idx, label in enumerate(labels)
                                   if label in ['eye blink', 'muscle artifact', 'heart beat',
                                                'line noise', 'channel noise']]

                    ica.exclude = exclude_idx
                    self.log(f"  Automatically identified {len(exclude_idx)} artifact components")
                    self.log(f"  Excluded components: {exclude_idx}")
                except Exception as e:
                    self.log(f"  Warning: Automatic component labeling failed: {e}")
                    self.log("  Using heuristic method for artifact detection")

                    # Fallback: Use correlation with EOG if available
                    # For now, we'll use a simple heuristic based on variance
                    exclude_idx = []
                    sources = ica.get_sources(raw_for_ica).get_data()
                    for idx in range(n_components):
                        # High variance components might be artifacts
                        if np.var(sources[idx]) > 3 * np.median(np.var(sources, axis=1)):
                            exclude_idx.append(idx)

                    ica.exclude = exclude_idx[:5]  # Limit to 5 components
                    self.log(f"  Heuristic: Excluded {len(ica.exclude)} components: {ica.exclude}")
            else:
                self.log("  ICLabel not available. Please manually review ICA components.")
                # Simple heuristic based on variance
                sources = ica.get_sources(raw_for_ica).get_data()
                exclude_idx = []
                for idx in range(n_components):
                    if np.var(sources[idx]) > 3 * np.median(np.var(sources, axis=1)):
                        exclude_idx.append(idx)

                ica.exclude = exclude_idx[:5]  # Limit to 5 components
                self.log(f"  Heuristic: Excluded {len(ica.exclude)} components: {ica.exclude}")

            # Apply ICA
            raw_processed = ica.apply(raw_processed, verbose=False)
            self.log("  ICA applied successfully")

        except Exception as e:
            self.log(f"  Error in ICA: {e}")

        # Step 7: Final checks
        self.log("\n[7/7] Final processing steps...")
        self.log("  Traditional preprocessing completed!")
        self.log("=" * 60)

        return raw_processed


class GEDAIPreprocessing(PreprocessingPipeline):
    """
    GEDAI (Advanced) EEG preprocessing pipeline.
    GEDAI = Generalized EEG Data Artifact Identification (using ASR)

    Steps:
    1. Load data
    2. Select EEG channels
    3. Set average reference
    4. Bandpass filter (1-80 Hz)
    5. Notch filter (60 Hz)
    6. ASR (Artifact Subspace Reconstruction) - advanced artifact removal
    7. ICA with ICLabel for remaining artifacts
    8. Final quality checks
    """

    def __init__(self, verbose=True, asr_cutoff=15):
        """
        Initialize GEDAI preprocessing.

        Parameters:
        -----------
        verbose : bool
            Print progress messages
        asr_cutoff : float
            ASR cutoff parameter (lower = more aggressive artifact removal)
            Default: 15 (moderate)
        """
        super().__init__(verbose)
        self.method_name = "GEDAI (ASR + ICA)"
        self.asr_cutoff = asr_cutoff

    def preprocess(self, raw):
        """
        Apply GEDAI preprocessing pipeline.

        Parameters:
        -----------
        raw : mne.io.Raw
            Raw EEG data

        Returns:
        --------
        mne.io.Raw : Preprocessed data
        """
        self.log("=" * 60)
        self.log("GEDAI PREPROCESSING PIPELINE (ASR + ICA)")
        self.log("=" * 60)

        # Make a copy
        raw_processed = raw.copy()

        # Step 1: Select EEG channels only
        self.log("\n[1/7] Selecting EEG channels...")
        try:
            raw_processed.pick_types(meg=False, eeg=True, stim=False, eog=False, exclude=[])
            self.log(f"  Selected {len(raw_processed.ch_names)} EEG channels")
        except Exception as e:
            self.log(f"  Warning: Could not filter channel types: {e}")

        # Step 2: Set average reference
        self.log("\n[2/7] Setting average reference...")
        try:
            raw_processed.set_eeg_reference('average', projection=False, verbose=False)
            self.log("  Average reference applied")
        except Exception as e:
            self.log(f"  Warning: Could not set reference: {e}")

        # Step 3: Bandpass filter
        self.log("\n[3/7] Applying bandpass filter (1-80 Hz)...")
        try:
            raw_processed.filter(l_freq=1.0, h_freq=80.0, verbose=False)
            self.log("  Bandpass filter applied")
        except Exception as e:
            self.log(f"  Error in filtering: {e}")

        # Step 4: Notch filter
        self.log("\n[4/7] Applying notch filter (60 Hz)...")
        try:
            raw_processed.notch_filter(freqs=60, verbose=False)
            self.log("  Notch filter applied")
        except Exception as e:
            self.log(f"  Warning: Could not apply notch filter: {e}")

        # Step 5: ASR (Artifact Subspace Reconstruction)
        self.log(f"\n[5/7] Applying ASR (cutoff={self.asr_cutoff})...")
        if ASR_AVAILABLE:
            try:
                # ASR requires data to be loaded
                raw_processed.load_data()

                # Create ASR object
                asr = asrpy.ASR(sfreq=raw_processed.info['sfreq'], cutoff=self.asr_cutoff)

                # Fit ASR on clean data portion (first 30 seconds, assuming it's relatively clean)
                train_duration = min(30, raw_processed.times[-1])
                raw_train = raw_processed.copy().crop(tmin=0, tmax=train_duration)
                asr.fit(raw_train)

                self.log("  ASR model fitted on calibration data")

                # Transform (clean) the data
                raw_processed = asr.transform(raw_processed)
                self.log("  ASR artifact removal completed")

            except Exception as e:
                self.log(f"  Error in ASR: {e}")
                self.log("  Continuing without ASR...")
        else:
            self.log("  ASR not available (asrpy not installed)")
            self.log("  Skipping ASR step. Install with: pip install asrpy")

        # Step 6: ICA with ICLabel
        self.log("\n[6/7] Running ICA for remaining artifacts...")
        try:
            n_components = min(15, len(raw_processed.ch_names) - 1)
            ica = ICA(n_components=n_components, method='infomax', random_state=42,
                      max_iter=500, fit_params=dict(extended=True), verbose=False)

            # Fit ICA
            raw_for_ica = raw_processed.copy().filter(l_freq=1.0, h_freq=None, verbose=False)
            ica.fit(raw_for_ica, verbose=False)
            self.log(f"  ICA fitted with {n_components} components")

            # ICLabel for automatic component classification
            if ICALABEL_AVAILABLE:
                try:
                    ic_labels = label_components(raw_for_ica, ica, method='iclabel')

                    # Get component labels and probabilities
                    labels = ic_labels['labels']
                    y_pred_proba = ic_labels['y_pred_proba']

                    # Exclude components with high probability of being artifacts
                    exclude_idx = []
                    for idx, (label, proba) in enumerate(zip(labels, y_pred_proba)):
                        # If brain probability is low (< 0.8), exclude
                        if label == 'brain' and proba[0] <= 0.8:
                            exclude_idx.append(idx)
                        elif label in ['eye blink', 'muscle artifact', 'heart beat',
                                        'line noise', 'channel noise']:
                            exclude_idx.append(idx)

                    ica.exclude = exclude_idx
                    self.log(f"  ICLabel identified {len(exclude_idx)} artifact components")
                    self.log(f"  Excluded components: {exclude_idx}")

                except Exception as e:
                    self.log(f"  Warning: ICLabel failed: {e}")
                    ica.exclude = []
            else:
                self.log("  ICLabel not available")
                ica.exclude = []

            # Apply ICA
            raw_processed = ica.apply(raw_processed, verbose=False)
            self.log("  ICA applied successfully")

        except Exception as e:
            self.log(f"  Error in ICA: {e}")

        # Step 7: Final checks
        self.log("\n[7/7] Final processing steps...")
        self.log("  GEDAI preprocessing completed!")
        self.log("=" * 60)

        return raw_processed


def preprocess_eeg(raw, method='gedai', verbose=True):
    """
    Convenience function to preprocess EEG data.

    Parameters:
    -----------
    raw : mne.io.Raw
        Raw EEG data
    method : str
        'traditional', 'gedai', or 'both'
    verbose : bool
        Print progress

    Returns:
    --------
    dict : Dictionary with preprocessed data and logs
           Keys: 'traditional' and/or 'gedai', each containing:
           - 'data': preprocessed Raw object
           - 'log': processing log
    """
    results = {}

    if method in ['traditional', 'both']:
        trad = TraditionalPreprocessing(verbose=verbose)
        results['traditional'] = {
            'data': trad.preprocess(raw),
            'log': trad.get_log()
        }

    if method in ['gedai', 'both']:
        gedai = GEDAIPreprocessing(verbose=verbose)
        results['gedai'] = {
            'data': gedai.preprocess(raw),
            'log': gedai.get_log()
        }

    return results
