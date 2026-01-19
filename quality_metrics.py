"""
EEG Quality Metrics Module
===========================
This module implements comprehensive quality metrics for EEG data analysis.
Includes industry-standard metrics used in research and clinical applications.
"""

import numpy as np
from scipy import signal, stats
from scipy.stats import kurtosis, skew
import mne


class EEGQualityMetrics:
    """Comprehensive EEG quality assessment metrics."""

    def __init__(self, raw):
        """
        Initialize quality metrics calculator.

        Parameters:
        -----------
        raw : mne.io.Raw
            MNE Raw object containing EEG data
        """
        self.raw = raw
        self.sfreq = raw.info['sfreq']
        self.data = raw.get_data()
        self.ch_names = raw.ch_names

    def calculate_all_metrics(self):
        """
        Calculate all quality metrics.

        Returns:
        --------
        dict : Dictionary containing all quality metrics
        """
        metrics = {
            'snr': self.calculate_snr(),
            'variance': self.calculate_variance(),
            'psd_slope': self.calculate_psd_slope(),
            'kurtosis': self.calculate_kurtosis(),
            'bad_channels': self.detect_bad_channels(),
            'artifact_percentage': self.estimate_artifact_percentage(),
            'frequency_bands': self.calculate_band_powers(),
            'channel_correlation': self.calculate_channel_correlation(),
            'data_quality_score': None,  # Will be calculated at the end
            'quality_grade': None  # Will be assigned at the end
        }

        # Calculate overall quality score
        metrics['data_quality_score'] = self._calculate_overall_score(metrics)
        metrics['quality_grade'] = self._assign_quality_grade(metrics['data_quality_score'])

        return metrics

    def calculate_snr(self):
        """
        Calculate Signal-to-Noise Ratio (SNR).
        Uses signal variance in alpha band vs. high-frequency noise.

        Returns:
        --------
        float : SNR in dB
        """
        try:
            # Filter data for signal (8-13 Hz, alpha band) and noise (50-100 Hz)
            signal_band = self.raw.copy().filter(l_freq=8, h_freq=13, verbose=False)
            noise_band = self.raw.copy().filter(l_freq=50, h_freq=None, verbose=False)

            signal_power = np.var(signal_band.get_data())
            noise_power = np.var(noise_band.get_data())

            if noise_power == 0:
                return 100.0  # Very high SNR

            snr_db = 10 * np.log10(signal_power / noise_power)
            return float(snr_db)
        except Exception as e:
            print(f"Error calculating SNR: {e}")
            return 0.0

    def calculate_variance(self):
        """
        Calculate variance statistics across channels.

        Returns:
        --------
        dict : Mean, std, min, max variance across channels
        """
        variances = np.var(self.data, axis=1)
        return {
            'mean': float(np.mean(variances)),
            'std': float(np.std(variances)),
            'min': float(np.min(variances)),
            'max': float(np.max(variances))
        }

    def calculate_psd_slope(self):
        """
        Calculate PSD slope (1/f noise characteristic).
        Steeper negative slope indicates better quality.

        Returns:
        --------
        dict : Slope statistics
        """
        try:
            psd, freqs = mne.time_frequency.psd_array_welch(
                self.data, sfreq=self.sfreq, fmin=1, fmax=80, n_fft=2048, verbose=False
            )

            # Calculate slope for each channel
            slopes = []
            for ch_psd in psd:
                # Convert to dB
                psd_db = 10 * np.log10(ch_psd)
                # Fit linear regression
                slope, intercept, r_value, p_value, std_err = stats.linregress(freqs, psd_db)
                slopes.append(slope)

            slopes = np.array(slopes)
            mean_slope = float(np.mean(slopes))

            # Classify based on slope (from original implementation)
            if mean_slope >= 0:
                quality = "Garbage"
            elif mean_slope >= -0.1:
                quality = "Poor"
            elif mean_slope >= -0.2:
                quality = "Fair"
            elif mean_slope >= -0.3:
                quality = "Good"
            else:
                quality = "Excellent"

            return {
                'mean_slope': mean_slope,
                'std_slope': float(np.std(slopes)),
                'quality': quality,
                'slopes_per_channel': slopes.tolist()
            }
        except Exception as e:
            print(f"Error calculating PSD slope: {e}")
            return {'mean_slope': 0, 'std_slope': 0, 'quality': 'Unknown', 'slopes_per_channel': []}

    def calculate_kurtosis(self):
        """
        Calculate kurtosis (tailedness of distribution).
        High kurtosis indicates presence of artifacts/outliers.

        Returns:
        --------
        dict : Kurtosis statistics
        """
        kurt_values = kurtosis(self.data, axis=1, fisher=True)

        # Fisher=True means excess kurtosis (normal distribution = 0)
        # High positive values indicate heavy tails (artifacts)
        return {
            'mean': float(np.mean(kurt_values)),
            'std': float(np.std(kurt_values)),
            'max': float(np.max(kurt_values)),
            'channels_with_high_kurtosis': int(np.sum(kurt_values > 5))  # Threshold of 5
        }

    def detect_bad_channels(self):
        """
        Detect bad channels using multiple criteria.

        Returns:
        --------
        dict : Information about bad channels
        """
        bad_channels = []
        reasons = {}

        # Criterion 1: Channels with very low or high variance
        variances = np.var(self.data, axis=1)
        median_var = np.median(variances)

        for i, (ch_name, var) in enumerate(zip(self.ch_names, variances)):
            if var < 0.1 * median_var:  # Too low variance (flat channel)
                bad_channels.append(ch_name)
                reasons[ch_name] = "Low variance (flat)"
            elif var > 10 * median_var:  # Too high variance (noisy)
                bad_channels.append(ch_name)
                reasons[ch_name] = "High variance (noisy)"

        # Criterion 2: Channels with poor correlation to neighbors
        # This is computationally intensive for many channels, so we'll skip for now
        # Can be added if needed

        return {
            'bad_channels': bad_channels,
            'count': len(bad_channels),
            'percentage': (len(bad_channels) / len(self.ch_names)) * 100,
            'reasons': reasons
        }

    def estimate_artifact_percentage(self):
        """
        Estimate percentage of data affected by artifacts.
        Uses amplitude threshold and gradient methods.

        Returns:
        --------
        dict : Artifact statistics
        """
        # Method 1: Amplitude-based detection
        # Threshold at 100 microvolts (common EEG threshold)
        threshold = 100e-6  # Assuming data is in Volts

        # Scale threshold based on actual data range
        data_std = np.std(self.data)
        threshold = max(threshold, 5 * data_std)  # Adaptive threshold

        artifact_samples_amplitude = np.sum(np.abs(self.data) > threshold)
        total_samples = self.data.size

        # Method 2: Gradient-based detection (sudden jumps)
        gradients = np.abs(np.diff(self.data, axis=1))
        gradient_threshold = 5 * np.median(gradients)
        artifact_samples_gradient = np.sum(gradients > gradient_threshold)

        percentage_amplitude = (artifact_samples_amplitude / total_samples) * 100
        percentage_gradient = (artifact_samples_gradient / (total_samples - len(self.ch_names))) * 100

        # Combined estimate
        combined_percentage = max(percentage_amplitude, percentage_gradient)

        return {
            'amplitude_based': float(percentage_amplitude),
            'gradient_based': float(percentage_gradient),
            'estimated_total': float(combined_percentage)
        }

    def calculate_band_powers(self):
        """
        Calculate power in standard EEG frequency bands.

        Returns:
        --------
        dict : Power in each frequency band
        """
        bands = {
            'delta': (1, 4),
            'theta': (4, 8),
            'alpha': (8, 13),
            'beta': (13, 30),
            'gamma': (30, 80)
        }

        band_powers = {}

        try:
            psd, freqs = mne.time_frequency.psd_array_welch(
                self.data, sfreq=self.sfreq, fmin=0.5, fmax=80, verbose=False
            )

            for band_name, (fmin, fmax) in bands.items():
                # Find frequency indices
                freq_idx = np.logical_and(freqs >= fmin, freqs <= fmax)
                # Calculate mean power in band
                band_power = np.mean(psd[:, freq_idx])
                band_powers[band_name] = float(band_power)

            # Calculate band power ratios (useful for quality assessment)
            total_power = sum(band_powers.values())
            band_powers['ratios'] = {
                band: (power / total_power) * 100 for band, power in band_powers.items()
                if band != 'ratios'
            }

            # Alpha/Delta ratio (indicator of alertness and data quality)
            if band_powers['delta'] > 0:
                band_powers['alpha_delta_ratio'] = band_powers['alpha'] / band_powers['delta']
            else:
                band_powers['alpha_delta_ratio'] = 0.0

        except Exception as e:
            print(f"Error calculating band powers: {e}")
            for band_name in bands.keys():
                band_powers[band_name] = 0.0
            band_powers['ratios'] = {}
            band_powers['alpha_delta_ratio'] = 0.0

        return band_powers

    def calculate_channel_correlation(self):
        """
        Calculate average correlation between channels.
        Low correlation may indicate noisy or bad channels.

        Returns:
        --------
        dict : Correlation statistics
        """
        # Calculate correlation matrix
        corr_matrix = np.corrcoef(self.data)

        # Remove diagonal (self-correlation)
        mask = ~np.eye(corr_matrix.shape[0], dtype=bool)
        correlations = corr_matrix[mask]

        return {
            'mean': float(np.mean(correlations)),
            'std': float(np.std(correlations)),
            'min': float(np.min(correlations)),
            'max': float(np.max(correlations)),
            'median': float(np.median(correlations))
        }

    def _calculate_overall_score(self, metrics):
        """
        Calculate overall quality score (0-100).

        Parameters:
        -----------
        metrics : dict
            Dictionary of calculated metrics

        Returns:
        --------
        float : Overall quality score
        """
        score = 0.0
        weights = 0.0

        # SNR contribution (weight: 0.25)
        if metrics['snr'] is not None:
            snr_normalized = np.clip(metrics['snr'] / 20, 0, 1)  # Normalize to 0-1
            score += snr_normalized * 25
            weights += 25

        # PSD slope contribution (weight: 0.20)
        slope = metrics['psd_slope']['mean_slope']
        if slope < -0.3:
            slope_score = 1.0
        elif slope < -0.2:
            slope_score = 0.8
        elif slope < -0.1:
            slope_score = 0.6
        elif slope < 0:
            slope_score = 0.4
        else:
            slope_score = 0.2
        score += slope_score * 20
        weights += 20

        # Artifact percentage contribution (weight: 0.20)
        artifact_pct = metrics['artifact_percentage']['estimated_total']
        artifact_score = np.clip(1 - (artifact_pct / 50), 0, 1)  # 50% artifacts = score 0
        score += artifact_score * 20
        weights += 20

        # Bad channels contribution (weight: 0.15)
        bad_ch_pct = metrics['bad_channels']['percentage']
        bad_ch_score = np.clip(1 - (bad_ch_pct / 30), 0, 1)  # 30% bad = score 0
        score += bad_ch_score * 15
        weights += 15

        # Kurtosis contribution (weight: 0.10)
        mean_kurt = abs(metrics['kurtosis']['mean'])
        kurt_score = np.clip(1 - (mean_kurt / 10), 0, 1)  # Kurtosis > 10 = score 0
        score += kurt_score * 10
        weights += 10

        # Channel correlation contribution (weight: 0.10)
        corr = metrics['channel_correlation']['mean']
        corr_score = np.clip(corr / 0.5, 0, 1)  # Normalize, assuming good correlation ~0.5
        score += corr_score * 10
        weights += 10

        # Normalize to 0-100
        if weights > 0:
            score = (score / weights) * 100

        return float(score)

    def _assign_quality_grade(self, score):
        """
        Assign quality grade based on overall score.

        Parameters:
        -----------
        score : float
            Overall quality score (0-100)

        Returns:
        --------
        str : Quality grade
        """
        if score >= 90:
            return "Excellent (A+)"
        elif score >= 80:
            return "Very Good (A)"
        elif score >= 70:
            return "Good (B)"
        elif score >= 60:
            return "Fair (C)"
        elif score >= 50:
            return "Poor (D)"
        else:
            return "Very Poor (F)"

    def generate_report(self, metrics):
        """
        Generate a human-readable quality report.

        Parameters:
        -----------
        metrics : dict
            Dictionary of calculated metrics

        Returns:
        --------
        str : Formatted quality report
        """
        report = []
        report.append("=" * 60)
        report.append("EEG DATA QUALITY REPORT")
        report.append("=" * 60)
        report.append("")

        # Overall Score
        report.append(f"Overall Quality Score: {metrics['data_quality_score']:.1f}/100")
        report.append(f"Quality Grade: {metrics['quality_grade']}")
        report.append("")

        # SNR
        report.append(f"Signal-to-Noise Ratio: {metrics['snr']:.2f} dB")
        report.append("")

        # PSD Slope
        psd = metrics['psd_slope']
        report.append(f"PSD Slope: {psd['mean_slope']:.4f} ± {psd['std_slope']:.4f}")
        report.append(f"PSD Quality Classification: {psd['quality']}")
        report.append("")

        # Artifacts
        art = metrics['artifact_percentage']
        report.append(f"Estimated Artifact Content: {art['estimated_total']:.2f}%")
        report.append(f"  - Amplitude-based: {art['amplitude_based']:.2f}%")
        report.append(f"  - Gradient-based: {art['gradient_based']:.2f}%")
        report.append("")

        # Bad Channels
        bad_ch = metrics['bad_channels']
        report.append(f"Bad Channels: {bad_ch['count']} ({bad_ch['percentage']:.1f}%)")
        if bad_ch['bad_channels']:
            report.append(f"  Channels: {', '.join(bad_ch['bad_channels'][:5])}")
            if len(bad_ch['bad_channels']) > 5:
                report.append(f"  ... and {len(bad_ch['bad_channels']) - 5} more")
        report.append("")

        # Kurtosis
        kurt = metrics['kurtosis']
        report.append(f"Kurtosis (artifact indicator): {kurt['mean']:.2f} ± {kurt['std']:.2f}")
        report.append(f"Channels with high kurtosis: {kurt['channels_with_high_kurtosis']}")
        report.append("")

        # Frequency Bands
        bands = metrics['frequency_bands']
        report.append("Frequency Band Powers:")
        report.append(f"  Delta (1-4 Hz):   {bands['delta']:.2e}")
        report.append(f"  Theta (4-8 Hz):   {bands['theta']:.2e}")
        report.append(f"  Alpha (8-13 Hz):  {bands['alpha']:.2e}")
        report.append(f"  Beta (13-30 Hz):  {bands['beta']:.2e}")
        report.append(f"  Gamma (30-80 Hz): {bands['gamma']:.2e}")
        report.append(f"  Alpha/Delta Ratio: {bands['alpha_delta_ratio']:.2f}")
        report.append("")

        # Channel Correlation
        corr = metrics['channel_correlation']
        report.append(f"Channel Correlation: {corr['mean']:.3f} ± {corr['std']:.3f}")
        report.append(f"  Range: [{corr['min']:.3f}, {corr['max']:.3f}]")
        report.append("")

        report.append("=" * 60)

        return "\n".join(report)
