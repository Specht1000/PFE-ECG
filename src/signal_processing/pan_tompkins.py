import numpy as np
from scipy.signal import butter, filtfilt, find_peaks


def bandpass_filter(signal: np.ndarray, fs: int, lowcut: float = 5.0, highcut: float = 15.0, order: int = 2) -> np.ndarray:
    nyquist = 0.5 * fs
    low = lowcut / nyquist
    high = highcut / nyquist

    b, a = butter(order, [low, high], btype="band")
    return filtfilt(b, a, signal)


def moving_window_integration(signal: np.ndarray, window_size: int) -> np.ndarray:
    if window_size < 1:
        window_size = 1

    window = np.ones(window_size) / window_size
    return np.convolve(signal, window, mode="same")


def detect_r_peaks(signal: np.ndarray, fs: int):
    """
    Simplified Pan-Tompkins-like pipeline:
    1. Bandpass filter
    2. Derivative
    3. Squaring
    4. Moving window integration
    5. Peak detection
    """

    filtered = bandpass_filter(signal, fs=fs, lowcut=5.0, highcut=15.0, order=2)

    derivative = np.diff(filtered, prepend=filtered[0])
    squared = derivative ** 2

    integration_window = int(0.150 * fs)  # 150 ms
    integrated = moving_window_integration(squared, integration_window)

    threshold = np.mean(integrated) + 0.5 * np.std(integrated)
    min_distance = int(0.250 * fs)  # 250 ms refractory period

    peaks, properties = find_peaks(
        integrated,
        height=threshold,
        distance=min_distance
    )

    return {
        "filtered": filtered,
        "derivative": derivative,
        "squared": squared,
        "integrated": integrated,
        "r_peaks": peaks,
        "peak_heights": properties.get("peak_heights", np.array([])),
    }


def compute_rr_intervals(r_peaks: np.ndarray, fs: int) -> np.ndarray:
    """
    Compute RR intervals in seconds from R peak sample indices.
    """
    if len(r_peaks) < 2:
        return np.array([])

    rr_samples = np.diff(r_peaks)
    rr_seconds = rr_samples / fs
    return rr_seconds