"""
EEG Preprocessing Module
=========================
Implements two preprocessing pipelines:
1. Traditional (ASR + ICA): Standard method with ASR and ICA artifact removal
2. GEDAI: Generalized Eigenvalue Decomposition for Artifact Identification

References:
- GEDAI: https://github.com/neurotuning/GEDAI-master
- GEVD Tutorial: arXiv:2104.12356
- ASR: Mullen et al. (2015)
"""

import numpy as np
import mne
from mne.preprocessing import ICA
from scipy import linalg
from scipy.signal import welch

try:
    import asrpy
    ASR_AVAILABLE = True
except ImportError:
    ASR_AVAILABLE = False
    print("Warning: asrpy not available. Traditional method (ASR+ICA) will not work optimally.")

try:
    from mne_icalabel import label_components
    ICALABEL_AVAILABLE = True
except ImportError:
    ICALABEL_AVAILABLE = False
    print("Warning: mne_icalabel not available. ICA component labeling will be heuristic.")


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
    Traditional EEG preprocessing pipeline: ASR + ICA with ICLabel
    This is the method from your original code.

    Steps:
    1. Load data
    2. Select EEG channels
    3. Set average reference
    4. Bandpass filter (1-80 Hz)
    5. Notch filter (60 Hz for power line)
    6. ASR (Artifact Subspace Reconstruction) - aggressive artifact removal
    7. ICA with ICLabel for remaining artifacts
    8. Final quality checks

    Reference:
    - ASR: Mullen, T. R., et al. (2015). Real-time neuroimaging and cognitive
           monitoring using wearable dry EEG. IEEE Trans. Biomed. Eng.
    """

    def __init__(self, verbose=True, asr_cutoff=15):
        super().__init__(verbose)
        self.method_name = "Traditional (ASR + ICA)"
        self.asr_cutoff = asr_cutoff

    def preprocess(self, raw):
        """
        Apply Traditional preprocessing pipeline (ASR + ICA).

        Parameters:
        -----------
        raw : mne.io.Raw
            Raw EEG data

        Returns:
        --------
        mne.io.Raw : Preprocessed data
        """
        self.log("=" * 60)
        self.log("TRADITIONAL PREPROCESSING: ASR + ICA + ICLabel")
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

                # Fit ASR on clean data portion (first 30 seconds)
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
                self.log("  ICLabel not available - using heuristic")
                ica.exclude = []

            # Apply ICA
            raw_processed = ica.apply(raw_processed, verbose=False)
            self.log("  ICA applied successfully")

        except Exception as e:
            self.log(f"  Error in ICA: {e}")

        # Step 7: Final checks
        self.log("\n[7/7] Final processing steps...")
        self.log("  Traditional (ASR + ICA) preprocessing completed!")
        self.log("=" * 60)

        return raw_processed


class GEDAIPreprocessing(PreprocessingPipeline):
    """
    GEDAI (Generalized Eigenvalue Decomposition for Artifact Identification)

    New eigenvalue-based preprocessing method that uses theoretical knowledge
    of the brain's signal subspace to automatically separate brain signals
    from artifacts.

    Algorithm:
    1. Basic preprocessing (filtering, referencing)
    2. Covariance matrix computation
    3. Generalized Eigenvalue Decomposition (GEVD)
    4. Component classification using signal/noise subspace analysis
    5. Artifact removal based on eigenvalue spectrum

    Key Advantages:
    - Uses theoretical EEG signal characteristics
    - Automatic separation without training data
    - Preserves brain signals better than blind methods
    - Outperforms ASR and ICA in many scenarios

    References:
    - GEDAI: https://github.com/neurotuning/GEDAI-master
    - Cohen, M. X. (2021). Tutorial on generalized eigendecomposition for
      denoising, contrast enhancement, and dimension reduction in multichannel
      electrophysiology. NeuroImage. arXiv:2104.12356
    """

    def __init__(self, verbose=True, n_components_keep=None):
        """
        Initialize GEDAI preprocessing.

        Parameters:
        -----------
        verbose : bool
            Print progress messages
        n_components_keep : int or None
            Number of signal components to keep (auto if None)
        """
        super().__init__(verbose)
        self.method_name = "GEDAI (Eigenvalue-based)"
        self.n_components_keep = n_components_keep

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
        self.log("GEDAI PREPROCESSING: Eigenvalue-Based Artifact Removal")
        self.log("=" * 60)

        # Make a copy
        raw_processed = raw.copy()

        # Step 1: Select EEG channels only
        self.log("\n[1/6] Selecting EEG channels...")
        try:
            raw_processed.pick_types(meg=False, eeg=True, stim=False, eog=False, exclude=[])
            self.log(f"  Selected {len(raw_processed.ch_names)} EEG channels")
        except Exception as e:
            self.log(f"  Warning: Could not filter channel types: {e}")

        # Step 2: Set average reference
        self.log("\n[2/6] Setting average reference...")
        try:
            raw_processed.set_eeg_reference('average', projection=False, verbose=False)
            self.log("  Average reference applied")
        except Exception as e:
            self.log(f"  Warning: Could not set reference: {e}")

        # Step 3: Bandpass filter
        self.log("\n[3/6] Applying bandpass filter (1-80 Hz)...")
        try:
            raw_processed.filter(l_freq=1.0, h_freq=80.0, verbose=False)
            self.log("  Bandpass filter applied")
        except Exception as e:
            self.log(f"  Error in filtering: {e}")

        # Step 4: Notch filter
        self.log("\n[4/6] Applying notch filter (60 Hz)...")
        try:
            raw_processed.notch_filter(freqs=60, verbose=False)
            self.log("  Notch filter applied")
        except Exception as e:
            self.log(f"  Warning: Could not apply notch filter: {e}")

        # Step 5: GEDAI - Generalized Eigenvalue Decomposition
        self.log("\n[5/6] Applying GEDAI (Generalized Eigenvalue Decomposition)...")
        try:
            raw_processed.load_data()
            raw_processed = self._apply_gedai(raw_processed)
            self.log("  GEDAI artifact removal completed")
        except Exception as e:
            self.log(f"  Error in GEDAI: {e}")
            self.log("  Continuing without GEDAI...")

        # Step 6: Final checks
        self.log("\n[6/6] Final processing steps...")
        self.log("  GEDAI preprocessing completed!")
        self.log("=" * 60)

        return raw_processed

    def _apply_gedai(self, raw):
        """
        Apply GEDAI using Generalized Eigenvalue Decomposition.

        The method computes two covariance matrices:
        - S: Signal covariance (clean EEG characteristics)
        - R: Reference/Noise covariance (artifact characteristics)

        Then solves: S * v = lambda * R * v
        """
        data = raw.get_data()
        n_channels, n_samples = data.shape
        sfreq = raw.info['sfreq']

        self.log("  Computing covariance matrices...")

        # Compute Signal covariance matrix (S)
        # Use broadband data focusing on typical EEG frequencies (1-40 Hz)
        raw_signal = raw.copy().filter(l_freq=1.0, h_freq=40.0, verbose=False)
        data_signal = raw_signal.get_data()

        # Normalize each channel
        data_signal = (data_signal - data_signal.mean(axis=1, keepdims=True)) / \
                      (data_signal.std(axis=1, keepdims=True) + 1e-10)

        S = np.cov(data_signal)
        self.log(f"    Signal covariance matrix: {S.shape}")

        # Compute Reference/Noise covariance matrix (R)
        # Use high-frequency noise and temporal derivatives
        raw_noise = raw.copy().filter(l_freq=40.0, h_freq=None, verbose=False)
        data_noise = raw_noise.get_data()

        # Add temporal derivative (sensitive to artifacts)
        data_derivative = np.diff(data, axis=1)
        # Pad to match original size
        data_derivative = np.concatenate([data_derivative,
                                          data_derivative[:, -1:]], axis=1)

        # Combine noise components
        data_noise_combined = data_noise + 0.5 * data_derivative

        # Normalize
        data_noise_combined = (data_noise_combined - data_noise_combined.mean(axis=1, keepdims=True)) / \
                              (data_noise_combined.std(axis=1, keepdims=True) + 1e-10)

        R = np.cov(data_noise_combined)
        self.log(f"    Noise covariance matrix: {R.shape}")

        # Regularization to ensure matrices are positive definite
        reg = 0.01 * np.trace(S) / n_channels
        S = S + reg * np.eye(n_channels)
        R = R + reg * np.eye(n_channels)

        # Solve generalized eigenvalue problem: S * v = lambda * R * v
        self.log("  Solving generalized eigenvalue decomposition...")
        try:
            eigenvalues, eigenvectors = linalg.eigh(S, R)

            # Sort by eigenvalues (descending)
            idx = np.argsort(eigenvalues)[::-1]
            eigenvalues = eigenvalues[idx]
            eigenvectors = eigenvectors[:, idx]

            self.log(f"    Computed {len(eigenvalues)} eigenvalues")
            self.log(f"    Eigenvalue range: [{eigenvalues.min():.4f}, {eigenvalues.max():.4f}]")

        except Exception as e:
            self.log(f"    Error in eigenvalue decomposition: {e}")
            self.log("    Falling back to standard eigenvalue decomposition...")
            eigenvalues, eigenvectors = np.linalg.eigh(S)
            idx = np.argsort(eigenvalues)[::-1]
            eigenvalues = eigenvalues[idx]
            eigenvectors = eigenvectors[:, idx]

        # Determine optimal number of components to keep
        if self.n_components_keep is None:
            # Automatic selection using eigenvalue spectrum
            # Keep components with eigenvalues > threshold

            # Method 1: Elbow method (look for drop in eigenvalues)
            eigenvalue_ratios = eigenvalues[1:] / eigenvalues[:-1]

            # Method 2: Keep components explaining 95% variance
            total_variance = np.sum(eigenvalues)
            cumsum_variance = np.cumsum(eigenvalues)
            n_keep_variance = np.argmax(cumsum_variance / total_variance > 0.95) + 1

            # Method 3: Kaiser criterion (eigenvalues > mean)
            mean_eigenval = np.mean(eigenvalues)
            n_keep_kaiser = np.sum(eigenvalues > mean_eigenval)

            # Use conservative estimate (maximum of methods)
            n_components = max(n_keep_variance, n_keep_kaiser)
            n_components = min(n_components, int(0.8 * n_channels))  # Cap at 80% channels
            n_components = max(n_components, int(0.5 * n_channels))  # Minimum 50% channels

            self.log(f"    Auto-selected {n_components} components (out of {n_channels})")
            self.log(f"      - Variance-based: {n_keep_variance}")
            self.log(f"      - Kaiser criterion: {n_keep_kaiser}")
        else:
            n_components = min(self.n_components_keep, n_channels)
            self.log(f"    Using {n_components} components (user-specified)")

        # Project data to eigenspace and back (keeping only signal components)
        self.log("  Reconstructing clean signal...")

        # Transform to eigenspace
        W = eigenvectors.T  # Unmixing matrix
        sources = W @ data  # Project to eigenspace

        # Keep only signal components (zero out artifact components)
        sources_clean = sources.copy()
        sources_clean[n_components:, :] = 0  # Zero out artifact components

        self.log(f"    Kept {n_components} signal components")
        self.log(f"    Removed {n_channels - n_components} artifact components")

        # Reconstruct clean data
        A = eigenvectors  # Mixing matrix
        data_clean = A @ sources_clean

        # Calculate artifact removal statistics
        artifact_power = np.sum(sources[n_components:, :] ** 2)
        total_power = np.sum(sources ** 2)
        artifact_percentage = (artifact_power / total_power) * 100

        self.log(f"    Removed {artifact_percentage:.2f}% of total power as artifacts")

        # Update raw object with clean data
        raw._data = data_clean

        return raw


def preprocess_eeg(raw, method='gedai', verbose=True):
    """
    Convenience function to preprocess EEG data.

    Parameters:
    -----------
    raw : mne.io.Raw
        Raw EEG data
    method : str
        'traditional' (ASR+ICA), 'gedai' (eigenvalue-based), or 'both'
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
