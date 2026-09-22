"""
STM32G474 IoMT Telemetry Receiver & Real-Time Stress Inference Engine.
Synchronizes with STM32 binary packets, extracts real-time HRV metrics,
and evaluates acute stress using the calibrated Logistic Regression model.
"""

import os
import time
import struct
import threading
from collections import deque
from typing import Optional, Dict, Tuple, List, Callable
import numpy as np
import pandas as pd
from scipy.signal import find_peaks
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

# Constants matching embedded protocol (telemetry_protocol.h)
SYNC_BYTE_0 = 0xAA
SYNC_BYTE_1 = 0x55
PROTOCOL_VERSION = 0x01
FRAME_SIZE = 20  # Total bytes per packet

# Telemetry frame format:
# sync[2] (2B), version (1B), flags (1B), seq_id (2B), timestamp_ms (4B), raw (4B), filt (4B), crc (2B)
FRAME_STRUCT = struct.Struct("<2sBBHIffH")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")


def compute_crc16(data: bytes) -> int:
    """Computes CRC-16-CCITT matching telemetry_protocol.c (poly: 0x1021, init: 0xFFFF)."""
    crc = 0xFFFF
    for byte in data:
        crc ^= (byte << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


CHAOS_SECRET_KEY = 0x9E3779B9
CHAOS_INIT_IV = 0x5A
CHAOS_WEYL_CONST = 0x61C88647


def encrypt_ecg_sample(raw_f: float, filt_f: float, seq_id: int, timestamp_ms: int, key: int = CHAOS_SECRET_KEY) -> bytes:
    """Encrypts 8 bytes (raw_ecg + filtered_ecg) using per-packet Nonce-seeded chaotic stream."""
    state = (key ^ ((seq_id * 0x45D9F3B) & 0xFFFFFFFF) ^ timestamp_ms) & 0xFFFFFFFF
    prev_cipher = (CHAOS_INIT_IV ^ (seq_id & 0xFF)) & 0xFF
    payload = bytearray(struct.pack("<ff", raw_f, filt_f))
    for i in range(len(payload)):
        state = (state ^ ((state << 13) & 0xFFFFFFFF)) & 0xFFFFFFFF
        state = (state ^ (state >> 17)) & 0xFFFFFFFF
        state = (state ^ ((state << 5) & 0xFFFFFFFF)) & 0xFFFFFFFF
        state = (state + CHAOS_WEYL_CONST) & 0xFFFFFFFF
        s = state & 0xFF
        c = payload[i] ^ s ^ prev_cipher
        prev_cipher = c
        payload[i] = c
    return bytes(payload)


def decrypt_ecg_sample(cipher_raw_bytes: bytes, seq_id: int, timestamp_ms: int, key: int = CHAOS_SECRET_KEY) -> Tuple[float, float]:
    """Decrypts 8 bytes (raw_ecg + filtered_ecg) using per-packet Nonce-seeded chaotic stream."""
    state = (key ^ ((seq_id * 0x45D9F3B) & 0xFFFFFFFF) ^ timestamp_ms) & 0xFFFFFFFF
    prev_cipher = (CHAOS_INIT_IV ^ (seq_id & 0xFF)) & 0xFF
    payload = bytearray(cipher_raw_bytes)
    for i in range(len(payload)):
        state = (state ^ ((state << 13) & 0xFFFFFFFF)) & 0xFFFFFFFF
        state = (state ^ (state >> 17)) & 0xFFFFFFFF
        state = (state ^ ((state << 5) & 0xFFFFFFFF)) & 0xFFFFFFFF
        state = (state + CHAOS_WEYL_CONST) & 0xFFFFFFFF
        s = state & 0xFF
        c = payload[i]
        p = c ^ s ^ prev_cipher
        prev_cipher = c
        payload[i] = p
    return struct.unpack("<ff", payload)


def build_c_packet(seq_id: int, timestamp_ms: int, raw_val: float, filt_val: float, flags: int = 0) -> bytes:
    """Builds a 20-byte binary frame matching telemetry_protocol.c."""
    sync = bytes([SYNC_BYTE_0, SYNC_BYTE_1])
    if flags & 0x01:
        enc_samples = encrypt_ecg_sample(raw_val, filt_val, seq_id, timestamp_ms)
        payload = struct.pack("<BBHI", PROTOCOL_VERSION, flags, seq_id & 0xFFFF, timestamp_ms) + enc_samples
    else:
        payload = struct.pack("<BBHIff", PROTOCOL_VERSION, flags, seq_id & 0xFFFF, timestamp_ms, raw_val, filt_val)
    crc = compute_crc16(payload)
    return sync + payload + struct.pack("<H", crc)


# ==============================================================================
# Global Shared Hardware Serial Port Manager (Singleton across Streamlit reruns)
# ==============================================================================
_GLOBAL_SERIAL_LOCK = threading.Lock()
_GLOBAL_SERIAL_CONN = None
_GLOBAL_SERIAL_PORT = None


def get_shared_serial_connection(port: str, baud: int = 115200):
    """Returns an open serial connection to `port`, reusing an existing instance
    across Streamlit reruns/sessions to avoid WinError 5: Access is denied."""
    global _GLOBAL_SERIAL_CONN, _GLOBAL_SERIAL_PORT
    with _GLOBAL_SERIAL_LOCK:
        if _GLOBAL_SERIAL_CONN is not None and getattr(_GLOBAL_SERIAL_CONN, "is_open", False):
            if _GLOBAL_SERIAL_PORT == port:
                return _GLOBAL_SERIAL_CONN
            else:
                try:
                    _GLOBAL_SERIAL_CONN.close()
                except Exception:
                    pass
                _GLOBAL_SERIAL_CONN = None

        import serial
        _GLOBAL_SERIAL_CONN = serial.Serial(port, baud, timeout=0.05)
        _GLOBAL_SERIAL_PORT = port
        return _GLOBAL_SERIAL_CONN


def release_shared_serial_connection():
    """Safely closes the shared hardware serial connection."""
    global _GLOBAL_SERIAL_CONN, _GLOBAL_SERIAL_PORT
    with _GLOBAL_SERIAL_LOCK:
        if _GLOBAL_SERIAL_CONN is not None:
            try:
                _GLOBAL_SERIAL_CONN.close()
            except Exception:
                pass
            _GLOBAL_SERIAL_CONN = None
            _GLOBAL_SERIAL_PORT = None


class TelemetryPacket:
    __slots__ = ("version", "flags", "seq_id", "timestamp_ms", "raw_ecg", "filtered_ecg", "cipher_filt_ecg", "is_valid")

    def __init__(self, version: int, flags: int, seq_id: int, timestamp_ms: int,
                 raw_ecg: float, filtered_ecg: float, cipher_filt_ecg: float = 0.0, is_valid: bool = True):
        self.version = version
        self.flags = flags
        self.seq_id = seq_id
        self.timestamp_ms = timestamp_ms
        self.raw_ecg = raw_ecg
        self.filtered_ecg = filtered_ecg
        self.cipher_filt_ecg = cipher_filt_ecg
        self.is_valid = is_valid

    @property
    def is_encrypted(self) -> bool:
        return bool(self.flags & 0x01)

    @property
    def is_live_sensor(self) -> bool:
        return bool(self.flags & 0x02)


class TelemetryParser:
    """Byte-level stream parser with auto-sync, CRC16 verification, and hardware decryption."""
    def __init__(self):
        self._buffer = bytearray()
        self.total_packets_received = 0
        self.valid_packets = 0
        self.crc_errors = 0
        self.sync_losses = 0
        self.dropped_packets = 0
        self._last_seq: Optional[int] = None
        self.is_stream_encrypted = False

    def feed_bytes(self, chunk: bytes) -> List[TelemetryPacket]:
        self._buffer.extend(chunk)
        packets = []

        while len(self._buffer) >= FRAME_SIZE:
            # Search for sync header
            if self._buffer[0] != SYNC_BYTE_0 or self._buffer[1] != SYNC_BYTE_1:
                # Discard 1 byte and realign
                self._buffer.pop(0)
                self.sync_losses += 1
                continue

            # Full frame candidate available
            frame_bytes = bytes(self._buffer[:FRAME_SIZE])
            sync, ver, flags, seq_id, ts_ms, raw, filt, rx_crc = FRAME_STRUCT.unpack(frame_bytes)

            # CRC is computed over bytes [2..17] (version through filtered_ecg)
            payload_to_check = frame_bytes[2:18]
            expected_crc = compute_crc16(payload_to_check)

            if rx_crc != expected_crc:
                self.crc_errors += 1
                # Sync header might have been a false positive; advance 1 byte
                self._buffer.pop(0)
                continue

            # Valid frame confirmed
            self._buffer = self._buffer[FRAME_SIZE:]
            self.total_packets_received += 1
            self.valid_packets += 1

            # Sequence tracking for packet loss
            if self._last_seq is not None:
                expected_seq = (self._last_seq + 1) & 0xFFFF
                if seq_id != expected_seq:
                    gap = (seq_id - expected_seq) & 0xFFFF
                    self.dropped_packets += gap
            self._last_seq = seq_id

            if flags & 0x01:
                self.is_stream_encrypted = True
                # Decrypt biometric samples (raw_ecg, filtered_ecg) using per-packet Nonce
                plain_raw, plain_filt = decrypt_ecg_sample(frame_bytes[10:18], seq_id, ts_ms)
                cipher_filt = float((struct.unpack("<i", frame_bytes[14:18])[0] / 2147483648.0) * 1.5)
                packets.append(TelemetryPacket(ver, flags, seq_id, ts_ms, plain_raw, plain_filt, cipher_filt, True))
            else:
                packets.append(TelemetryPacket(ver, flags, seq_id, ts_ms, raw, filt, filt, True))

        return packets


class StressInferenceEngine:
    """Trains on WESAD HRV dataset and evaluates real-time stress probability."""
    FEATURE_COLS = [
        "MeanHR", "SDNN", "RMSSD", "pNN50", "MeanRR", "RR_CV", "RR_IQR", "HR_IQR"
    ]

    def __init__(self, threshold: float = 0.35):
        self.threshold = threshold
        self.scaler = StandardScaler()
        self.model = LogisticRegression(C=1.0, max_iter=1000, random_state=42)
        self.baseline_ref: Optional[Dict[str, float]] = None
        self._is_trained = False
        self._train_default_model()

    def _train_default_model(self):
        """Loads expanded WESAD features and fits relative baseline classifier."""
        feat_path = os.path.join(RESULTS_DIR, "WESAD_HRV_features_expanded.csv")
        if not os.path.isfile(feat_path):
            return

        df = pd.read_csv(feat_path)
        if "Label" not in df.columns and "Condition" in df.columns:
            df["Label"] = (df["Condition"] == "Stress").astype(int)
        df_clean = df[df["Label"].isin([0, 1])].copy()

        # Subject-relative normalization
        X_list, y_list = [], []
        eps = 1e-6
        for subj in df_clean["Subject"].unique():
            s_df = df_clean[df_clean["Subject"] == subj]
            s_base = s_df[s_df["Label"] == 0]
            if len(s_base) == 0:
                continue
            s_mean = s_base[self.FEATURE_COLS].mean().values
            denom = np.where(np.abs(s_mean) < eps, eps, np.abs(s_mean))

            for _, row in s_df.iterrows():
                vals = row[self.FEATURE_COLS].values
                delta_x = (vals - s_mean) / denom
                X_list.append(delta_x)
                y_list.append(row["Label"])

        X = np.array(X_list)
        y = np.array(y_list)

        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        self._is_trained = True

    def set_subject_baseline(self, baseline_metrics: Dict[str, float]):
        """Sets individual baseline metrics for personalized relative shifting."""
        self.baseline_ref = baseline_metrics

    def predict(self, hrv_metrics: Dict[str, float]) -> Tuple[float, int]:
        """Returns (stress_probability, binary_prediction)."""
        if not self._is_trained or self.baseline_ref is None:
            return 0.5, 0

        # Physiological minimum denominator floors to prevent division-by-near-zero
        floors = {
            "MeanHR": 30.0,
            "SDNN": 5.0,
            "RMSSD": 5.0,
            "pNN50": 5.0,
            "MeanRR": 0.3,
            "RR_CV": 0.02,
            "RR_IQR": 0.02,
            "HR_IQR": 1.0,
        }
        raw_vals = np.array([hrv_metrics.get(c, 0.0) for c in self.FEATURE_COLS], dtype=np.float64)
        base_vals = np.array([max(floors.get(c, 1.0), self.baseline_ref.get(c, 1.0)) for c in self.FEATURE_COLS], dtype=np.float64)
        denom = base_vals

        delta_x = np.clip((raw_vals - base_vals) / denom, -5.0, 5.0)
        x_scaled = self.scaler.transform(delta_x.reshape(1, -1))
        prob = float(self.model.predict_proba(x_scaled)[0, 1])
        label = 1 if prob >= self.threshold else 0
        return prob, label


class LiveTelemetryStream:
    """Manages circular buffers, real-time HRV extraction, and stress telemetry."""
    def __init__(self, fs: int = 350, window_sec: int = 60):
        self.fs = fs
        self.window_sec = window_sec
        self.buffer_len = fs * window_sec

        self.time_buf = deque(maxlen=self.buffer_len)
        self.raw_buf = deque(maxlen=self.buffer_len)
        self.filt_buf = deque(maxlen=self.buffer_len)
        self.cipher_buf = deque(maxlen=self.buffer_len)

        self.parser = TelemetryParser()
        self.classifier = StressInferenceEngine(threshold=0.35)

        self.last_hrv: Dict[str, float] = {}
        self.last_stress_prob: float = 0.0
        self.last_stress_label: int = 0
        self._lock = threading.Lock()

    def add_packet(self, pkt: TelemetryPacket):
        with self._lock:
            self.time_buf.append(pkt.timestamp_ms / 1000.0)
            self.raw_buf.append(pkt.raw_ecg)
            self.filt_buf.append(pkt.filtered_ecg)
            self.cipher_buf.append(pkt.cipher_filt_ecg)

    def get_eavesdropper_entropy(self) -> float:
        """Computes Shannon entropy of wire ciphertext in bits/byte."""
        with self._lock:
            if len(self.cipher_buf) < 100:
                return 0.0
            data = np.array(self.cipher_buf, dtype=np.float32).tobytes()
        counts = np.bincount(np.frombuffer(data, dtype=np.uint8), minlength=256)
        probs = counts[counts > 0] / float(len(data))
        return float(-np.sum(probs * np.log2(probs)))

    def extract_current_hrv(self) -> Optional[Dict[str, float]]:
        """Extracts 8 core HRV metrics from current sliding buffer."""
        with self._lock:
            if len(self.filt_buf) < (self.fs * 5):  # Need at least 5s to compute HRV
                return None
            sig = np.array(self.filt_buf, dtype=np.float32)

        # Adaptive MAD peak thresholding
        mad = np.median(np.abs(sig - np.median(sig)))
        min_prominence = max(0.15, 1.8 * mad)
        min_dist = int(0.35 * self.fs)

        peaks, _ = find_peaks(sig, distance=min_dist, prominence=min_prominence)
        if len(peaks) < 4:
            return None

        peak_times = peaks / float(self.fs)
        rr_sec = np.diff(peak_times)

        # Physiological gating (300 ms to 1500 ms)
        valid_rr = rr_sec[(rr_sec >= 0.3) & (rr_sec <= 1.5)]
        if len(valid_rr) < 3:
            return None

        hr = 60.0 / valid_rr
        diff_rr_ms = np.abs(np.diff(valid_rr)) * 1000.0

        sdnn = float(np.std(valid_rr, ddof=1) * 1000.0)
        rmssd = float(np.sqrt(np.mean(diff_rr_ms ** 2)))
        pnn50 = float(np.sum(diff_rr_ms > 50.0) / len(diff_rr_ms) * 100.0)
        mean_rr = float(np.mean(valid_rr))
        mean_hr = float(np.mean(hr))

        rr_sorted = np.sort(valid_rr)
        hr_sorted = np.sort(hr)
        rr_iqr = float(np.percentile(rr_sorted, 75) - np.percentile(rr_sorted, 25))
        hr_iqr = float(np.percentile(hr_sorted, 75) - np.percentile(hr_sorted, 25))

        metrics = {
            "MeanHR": round(mean_hr, 1),
            "SDNN": round(sdnn, 2),
            "RMSSD": round(rmssd, 2),
            "pNN50": round(pnn50, 1),
            "MeanRR": round(mean_rr, 3),
            "RR_CV": round(sdnn / (mean_rr * 1000.0 + 1e-6), 4),
            "RR_IQR": round(rr_iqr, 3),
            "HR_IQR": round(hr_iqr, 1),
            "NumBeats": int(len(peaks)),
        }

        prob, label = self.classifier.predict(metrics)
        with self._lock:
            self.last_hrv = metrics
            self.last_stress_prob = prob
            self.last_stress_label = label

        return metrics

    def get_snapshot(self) -> Dict:
        """Returns snapshot of current rolling waveform and metrics for UI."""
        with self._lock:
            t = list(self.time_buf)
            raw = list(self.raw_buf)
            filt = list(self.filt_buf)
            hrv = dict(self.last_hrv)
            prob = self.last_stress_prob
            label = self.last_stress_label
            stats = {
                "total_packets": self.parser.total_packets_received,
                "valid_packets": self.parser.valid_packets,
                "crc_errors": self.parser.crc_errors,
                "dropped_packets": self.parser.dropped_packets,
            }
        return {
            "time": t,
            "raw": raw,
            "filtered": filt,
            "cipher": list(self.cipher_buf),
            "is_encrypted": self.parser.is_stream_encrypted,
            "entropy": round(self.get_eavesdropper_entropy(), 3),
            "hrv": hrv,
            "stress_prob": prob,
            "stress_label": label,
            "stats": stats,
        }
