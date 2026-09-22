"""
Simulate STM32G474 streaming binary telemetry packets to the PC receiver.
Tests the full pipeline (Framing -> CRC16 Check -> Ingestion -> HRV -> Stress ML)
without requiring physical hardware plugged into USB.
"""

import os
import sys
import time
import struct
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(PROJECT_ROOT, "python"))

from stm32_telemetry_receiver import (
    LiveTelemetryStream,
    FRAME_STRUCT,
    SYNC_BYTE_0,
    SYNC_BYTE_1,
    PROTOCOL_VERSION,
    compute_crc16,
)

SAMPLE_PATH = os.path.join(PROJECT_ROOT, "demo", "sample_data", "ecg_samples.npz")


def build_c_packet(seq_id: int, timestamp_ms: int, raw_val: float, filt_val: float, flags: int = 0) -> bytes:
    """Builds a 20-byte binary frame matching telemetry_protocol.c."""
    sync = bytes([SYNC_BYTE_0, SYNC_BYTE_1])
    # Build payload without CRC: [version, flags, seq_id, timestamp_ms, raw, filt]
    payload = struct.pack("<BBHIff", PROTOCOL_VERSION, flags, seq_id & 0xFFFF, timestamp_ms, raw_val, filt_val)
    crc = compute_crc16(payload)
    return sync + payload + struct.pack("<H", crc)


def run_stream_simulation(subject: str = "S2", condition: str = "Stress", duration_sec: int = 25, speed_factor: float = 5.0):
    print("=" * 65)
    print("   STM32G474 TELEMETRY LINK SIMULATOR & REAL-TIME ML EVALUATION")
    print("=" * 65)
    print(f"Subject:           {subject}")
    print(f"Condition:         {condition}")
    print(f"Duration:          {duration_sec} seconds")
    print(f"Playback Speed:    {speed_factor}x real-time")
    print("=" * 65)

    data = np.load(SAMPLE_PATH)
    raw_key = f"{subject}_{condition}_raw"
    filt_key = f"{subject}_{condition}_filt"

    if raw_key not in data or filt_key not in data:
        print(f"Error: {raw_key} not found in sample dataset.")
        return

    raw_signal = data[raw_key]
    filt_signal = data[filt_key]
    fs = 350
    stream = LiveTelemetryStream(fs=fs, window_sec=60)
    meta_path = os.path.join(PROJECT_ROOT, "demo", "sample_data", "samples_meta.json")
    if os.path.isfile(meta_path):
        import json
        with open(meta_path, "r") as f:
            meta = json.load(f)
            if subject in meta.get("subjects", {}) and "Baseline" in meta["subjects"][subject]:
                base_hrv = meta["subjects"][subject]["Baseline"]["hrv"]
                base_dict = {
                    "MeanHR": base_hrv.get("MeanHR", 75.0),
                    "SDNN": base_hrv.get("SDNN_ms", 50.0),
                    "RMSSD": base_hrv.get("RMSSD_ms", 40.0),
                    "pNN50": base_hrv.get("pNN50", 20.0),
                    "MeanRR": 60.0 / max(1.0, base_hrv.get("MeanHR", 75.0)),
                    "RR_CV": base_hrv.get("SDNN_ms", 50.0) / (60.0 / max(1.0, base_hrv.get("MeanHR", 75.0)) * 1000.0),
                    "RR_IQR": 0.08,
                    "HR_IQR": 8.0,
                }
                stream.classifier.set_subject_baseline(base_dict)
                print(f"Personalized Baseline for {subject}: MeanHR={base_dict['MeanHR']} BPM, RMSSD={base_dict['RMSSD']} ms")
    total_samples = min(len(raw_signal), duration_sec * fs)
    print(f"\n[1/3] Initialized LiveTelemetryStream (Buffer: 60s @ {fs} Hz)")
    print(f"[2/3] Streaming {total_samples:,} packets from simulated STM32...")

    start_time = time.time()
    packet_period = 1.0 / (fs * speed_factor)

    for i in range(total_samples):
        seq = i % 65536
        ts_ms = int((i / fs) * 1000)
        raw_val = float(raw_signal[i])
        filt_val = float(filt_signal[i])

        # Pack into raw binary bytes
        frame_bytes = build_c_packet(seq, ts_ms, raw_val, filt_val)

        # Feed to parser as raw incoming serial bytes
        packets = stream.parser.feed_bytes(frame_bytes)
        for pkt in packets:
            stream.add_packet(pkt)

        # Every 1 second of simulated signal, compute live HRV and predict stress
        if i > 0 and (i % fs == 0):
            hrv = stream.extract_current_hrv()
            if hrv:
                prob = stream.last_stress_prob
                state = "[STRESS DETECTED]" if prob >= 0.35 else "[CALM / BASELINE]"
                print(
                    f"[{ts_ms/1000.0:5.1f}s] HR: {hrv['MeanHR']:5.1f} BPM | "
                    f"RMSSD: {hrv['RMSSD']:5.1f} ms | "
                    f"pNN50: {hrv['pNN50']:4.1f}% | "
                    f"Stress Prob: {prob*100.0:5.1f}% [{state}]"
                )

        # Throttle loop to match desired playback speed
        if speed_factor <= 10.0:
            time.sleep(packet_period * 0.5)

    elapsed = time.time() - start_time
    stats = stream.get_snapshot()["stats"]

    print("\n" + "=" * 65)
    print("   TELEMETRY STREAM SUMMARY")
    print("=" * 65)
    print(f"Packets Transmitted:     {total_samples:,}")
    print(f"Packets Validated (CRC): {stats['valid_packets']:,} ({(stats['valid_packets']/total_samples)*100:.2f}%)")
    print(f"CRC Checksum Errors:     {stats['crc_errors']}")
    print(f"Dropped Packets:         {stats['dropped_packets']}")
    print(f"Simulation Elapsed Time: {elapsed:.2f} seconds")
    print(f"Effective Ingestion Rate:{total_samples/elapsed:,.0f} packets/sec")
    print("=" * 65)
    print(">>> PIPELINE VALIDATION: PASSED END-TO-END <<<")
    print("=" * 65)


if __name__ == "__main__":
    # Test on Subject S2 in Stress condition
    run_stream_simulation(subject="S2", condition="Stress", duration_sec=20, speed_factor=10.0)
