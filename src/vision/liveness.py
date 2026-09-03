"""
Liveness and Deepfake Detection Module

This module utilizes frequency-domain forensics (2D Fast Fourier Transform)
to analyze the spectral power decay of an image. Synthetic images (GANs,
Diffusion models) often exhibit anomalous high-frequency signatures or
periodic grid artifacts that deviate from natural $1/f^\\alpha$ decay.
"""

import cv2
import numpy as np


class FrequencyForensics:
    """
    Analyzes the frequency spectrum of an image to detect synthetic generation artifacts.
    """

    def __init__(self, high_freq_threshold: float = 0.85):
        """
        Initializes the FrequencyForensics analyzer.

        Args:
            high_freq_threshold (float): The threshold for the high-frequency anomaly
                score. Scores above this are flagged as deepfakes.
        """
        self.threshold = high_freq_threshold

    def get_azimuthal_average(self, magnitude_spectrum: np.ndarray) -> np.ndarray:
        """
        Calculates the 1D azimuthal (radial) average of the 2D magnitude spectrum.
        """
        y, x = np.indices(magnitude_spectrum.shape)
        center = np.array([(y.max() - y.min()) / 2.0, (x.max() - x.min()) / 2.0])
        r = np.hypot(x - center[1], y - center[0])

        # Bin the radii
        r = r.astype(int)

        # Calculate the mean magnitude per radius bin
        tbin = np.bincount(r.ravel(), magnitude_spectrum.ravel())
        nr = np.bincount(r.ravel())
        radial_profile = tbin / nr

        return radial_profile

    def analyze_liveness(self, image: np.ndarray) -> tuple[bool, float]:
        """
        Analyzes an image and returns a boolean flag (is_deepfake) and a score.

        Args:
            image (np.ndarray): The BGR input image.

        Returns:
            tuple[bool, float]: (is_deepfake, anomaly_score)
        """
        if image is None or image.size == 0:
            return False, 0.0

        # 1. Convert to Grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 2. Compute 2D Fast Fourier Transform
        f = np.fft.fft2(gray)
        fshift = np.fft.fftshift(f)  # Shift zero frequency to center

        # 3. Calculate Magnitude Spectrum
        # We add 1e-8 to avoid log(0)
        magnitude_spectrum = 20 * np.log(np.abs(fshift) + 1e-8)

        # 4. Get 1D Radial Profile
        radial_profile = self.get_azimuthal_average(magnitude_spectrum)

        # 5. Detect high-frequency anomalies
        # Natural images have a smooth decay. Synthetic images often have spikes
        # in the extreme high frequencies (the tail of the radial profile).
        # We'll analyze the last 20% of the frequency bins.
        tail_length = int(len(radial_profile) * 0.2)
        if tail_length == 0:
            return False, 0.0

        tail = radial_profile[-tail_length:]
        mid = radial_profile[
            int(len(radial_profile) * 0.4) : int(len(radial_profile) * 0.8)
        ]

        # A simple heuristic: if the extreme high frequencies (tail) are unnaturally strong
        # compared to the mid frequencies, it's highly suspect.
        mean_tail = np.mean(tail)
        mean_mid = np.mean(mid)

        if mean_mid == 0:
            return False, 0.0

        anomaly_score = float(mean_tail / mean_mid)

        # Normal images usually decay heavily so tail/mid is very small.
        # Deepfakes often flatten out or spike, raising this ratio.
        is_deepfake = anomaly_score > self.threshold

        return is_deepfake, anomaly_score
