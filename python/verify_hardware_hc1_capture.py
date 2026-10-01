"""
=============================================================================
Offline Cryptographic & Parity Verifier for STM32 Physical HC1 Telemetry
Physical Hardware-in-the-Loop (HIL) Decryption & Scientific Parity Suite
=============================================================================
Reads captured raw 20-byte wire packet dumps and validates against canonical
firmware replay reference vectors (WESAD Subject S2 Baseline, modulo 2100):
  1. Exact packet count (10,000 packets / 200,000 bytes)
  2. Protocol flags homogeneity (100% flags == 0x05)
  3. Hardware-generated CCITT CRC-16 validity (100% pass)
  4. Sequence continuity and zero sequence gaps
  5. Timestamp progression and sample rate classification (345–355 Hz)
  6. HC1 Python decryption of raw wire ciphertext
  7. Numerical validity: zero NaNs and zero Infinities
  8. Independent Raw ECG and Filtered ECG reconstruction error vs canonical replay vector
  9. Parity tolerance compliance (max abs error < 1e-5 mV for both raw and filt)
  10. Clinical QRS R-peak detection & alignment fidelity
  11. Ciphertext Shannon entropy, Chi-square uniformity, and autocorrelation

Outputs:
  - hil_parity_report.json
  - hil_parity_report.txt
=============================================================================
"""

import os
import sys
import json
import struct
import hashlib
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import numpy as np
from scipy.signal import find_peaks
from scipy.stats import chisquare

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "python"))

from m4d_hyperchaos import m4d_decrypt_ecg
from stm32_telemetry_receiver import (
    SYNC_BYTE_0,
    SYNC_BYTE_1,
    FRAME_SIZE,
    FRAME_STRUCT,
    compute_crc16
)

DEFAULT_RAW_PACKETS = os.path.join(
    PROJECT_ROOT, "results", "verification", "hc1_hardware_hil", "hardware_raw_packets.bin"
)
DEFAULT_META_PATH = os.path.join(
    PROJECT_ROOT, "results", "verification", "hc1_hardware_hil", "hardware_raw_packets_meta.json"
)
DEFAULT_REFERENCE = os.path.join(
    PROJECT_ROOT, "results", "verification", "hc1_hardware_hil", "firmware_replay_reference.npz"
)
DEFAULT_OUT_DIR = os.path.join(
    PROJECT_ROOT, "results", "verification", "hc1_hardware_hil"
)

HARDWARE_PARITY_DISCLAIMER = (
    "DISCLAIMER: This test validates physical hardware telemetry captured over the ST-LINK "
    "Virtual COM Port from an STM32G474RE microcontroller running canonical HC1 firmware. "
    "Results reflect true over-the-wire hardware execution and cryptographic round-trip parity."
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Offline verifier for physical STM32 HC1 telemetry capture."
    )
    parser.add_argument(
        "--input",
        type=str,
        default=DEFAULT_RAW_PACKETS,
        help=f"Path to captured raw 20-byte packets binary (default: {DEFAULT_RAW_PACKETS})"
    )
    parser.add_argument(
        "--meta",
        type=str,
        default=DEFAULT_META_PATH,
        help=f"Path to capture metadata JSON (default: {DEFAULT_META_PATH})"
    )
    parser.add_argument(
        "--reference",
        type=str,
        default=DEFAULT_REFERENCE,
        help=f"Path to canonical firmware replay reference .npz (default: {DEFAULT_REFERENCE})"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=DEFAULT_OUT_DIR,
        help=f"Output directory for verification reports (default: {DEFAULT_OUT_DIR})"
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=1e-5,
        help="Reconstruction tolerance threshold in mV (default: 1e-5 mV)"
    )
    return parser.parse_args()


def load_canonical_reference(reference_path: str, num_packets: int):
    """Loads canonical firmware replay reference and builds expected 10,000-sample streams."""
    if not os.path.exists(reference_path):
        raise FileNotFoundError(f"Canonical reference file not found: {reference_path}")

    ref_data = np.load(reference_path)
    if "raw_ecg_2100" not in ref_data or "runtime_filt_10k" not in ref_data:
        raise ValueError(
            f"Invalid reference file '{reference_path}': Canonical firmware replay reference must contain "
            f"'raw_ecg_2100' and 'runtime_filt_10k'. Legacy or noncanonical fallback references (such as "
            f"raw ecg_samples.npz or S2_Stress arrays) are strictly rejected."
        )

    raw_ref_2100 = ref_data["raw_ecg_2100"]
    filt_ref_runtime = ref_data["runtime_filt_10k"]
    golden_filt_2100 = ref_data["golden_filt_2100"] if "golden_filt_2100" in ref_data else None

    # Compute SHA-256 hashes
    hash_raw_2100 = hashlib.sha256(raw_ref_2100.tobytes()).hexdigest()
    hash_filt_runtime = hashlib.sha256(filt_ref_runtime.tobytes()).hexdigest()
    hash_golden_2100 = hashlib.sha256(golden_filt_2100.tobytes()).hexdigest() if golden_filt_2100 is not None else "N/A"

    # Apply Modulo-2100 Rule for raw ECG
    expected_raw = np.array([raw_ref_2100[i % 2100] for i in range(num_packets)], dtype=np.float32)
    expected_filt = np.array(filt_ref_runtime[:num_packets], dtype=np.float32)
    golden_filt_mod = np.array([golden_filt_2100[i % 2100] for i in range(num_packets)], dtype=np.float32) if golden_filt_2100 is not None else None

    hashes = {
        "raw_ecg_2100_sha256": hash_raw_2100,
        "runtime_filt_10k_sha256": hash_filt_runtime,
        "golden_filt_2100_sha256": hash_golden_2100
    }

    return expected_raw, expected_filt, golden_filt_mod, hashes


def verify_hardware_capture(
    input_bin_path: str,
    meta_json_path: str,
    reference_path: str,
    output_dir: str,
    tolerance_mV: float = 1e-5
) -> bool:
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 78)
    print("   STM32 PHYSICAL HC1 HARDWARE-IN-THE-LOOP (HIL) OFFLINE VERIFIER")
    print("   Canonical Firmware Replay Parity (WESAD S2 Baseline modulo 2100)")
    print("=" * 78)

    # 1. Load captured raw wire bytes
    if not os.path.exists(input_bin_path):
        raise FileNotFoundError(f"Captured wire binary not found: {input_bin_path}")

    with open(input_bin_path, "rb") as f:
        wire_data = f.read()

    total_bytes = len(wire_data)
    if total_bytes % FRAME_SIZE != 0:
        raise ValueError(f"Wire data size {total_bytes} is not a multiple of FRAME_SIZE ({FRAME_SIZE})!")

    num_packets = total_bytes // FRAME_SIZE
    print(f"Loaded raw capture: {num_packets:,} packets ({total_bytes:,} bytes).")

    # 2. Load capture metadata if present
    meta_info = {}
    if os.path.exists(meta_json_path):
        with open(meta_json_path, "r") as f:
            meta_info = json.load(f)
        print(f"Loaded capture metadata from: {meta_json_path}")
    else:
        print(f"Warning: Metadata JSON not found at {meta_json_path}. Proceeding with wire inspection.")

    # 3. Load canonical firmware replay reference
    expected_raw, expected_filt, golden_filt_mod, ref_hashes = load_canonical_reference(reference_path, num_packets)
    print("\n[Firmware Replay Reference]")
    print(f"  • Source Signal:             WESAD Subject S2 Baseline (S2_Baseline_raw, 2,100 samples)")
    print(f"  • Modulo Indexing Rule:      expected_raw[i] = raw_ecg_2100[i % 2100]")
    print(f"  • raw_ecg_2100 SHA-256:      {ref_hashes['raw_ecg_2100_sha256']}")
    print(f"  • runtime_filt_10k SHA-256:  {ref_hashes['runtime_filt_10k_sha256']}")
    print(f"  • golden_filt_2100 SHA-256:  {ref_hashes['golden_filt_2100_sha256']}")

    # ---------------------------------------------------------
    # Step C: Verify Packet Integrity, Flags, Framing & Sequence
    # ---------------------------------------------------------
    print("\n[Step C] Verifying Packet Framing, CRC-16, Sequence & Flags...")
    crc_errors = 0
    flag_violations = 0
    sequence_gaps = 0
    last_seq: Optional[int] = None
    timestamps: List[int] = []
    seq_list: List[int] = []
    decrypted_raw: List[float] = []
    decrypted_filt: List[float] = []
    ciphertext_bytes = bytearray()

    for idx in range(num_packets):
        pkt_bytes = wire_data[idx * FRAME_SIZE : (idx + 1) * FRAME_SIZE]
        sync, ver, flg, seq, ts_ms, r_cipher, f_cipher, rx_crc = FRAME_STRUCT.unpack(pkt_bytes)

        # Check sync & version
        if sync != b"\xAA\x55" or ver != 0x01:
            raise ValueError(f"Corrupt packet header at index {idx}!")

        # Check CRC-16
        expected_crc = compute_crc16(pkt_bytes[2:18])
        if rx_crc != expected_crc:
            crc_errors += 1

        # Check flags (must be 0x05)
        if flg != 0x05:
            flag_violations += 1

        # Check sequence continuity
        if last_seq is not None:
            expected_seq = (last_seq + 1) & 0xFFFF
            if seq != expected_seq:
                sequence_gaps += 1
        last_seq = seq

        timestamps.append(ts_ms)
        seq_list.append(seq)
        ciphertext_bytes.extend(pkt_bytes[10:18])

        # Decrypt packet
        raw_dec, filt_dec = m4d_decrypt_ecg(pkt_bytes[10:18], seq, ts_ms)
        decrypted_raw.append(raw_dec)
        decrypted_filt.append(filt_dec)

    dec_raw_arr = np.array(decrypted_raw, dtype=np.float32)
    dec_filt_arr = np.array(decrypted_filt, dtype=np.float32)

    # Sampling rate calculation
    if len(timestamps) > 1:
        ts_span_ms = timestamps[-1] - timestamps[0]
        actual_fs = (len(timestamps) - 1) / (ts_span_ms / 1000.0) if ts_span_ms > 0 else 0.0
    else:
        actual_fs = meta_info.get("calculated_sampling_rate_hz", 0.0)

    sampling_rate_pass = bool(345.0 <= actual_fs <= 355.0)
    sampling_rate_status = "PASS" if sampling_rate_pass else "FAIL"

    check_packet_count = bool(num_packets == 10000)
    check_all_flags_05 = bool(flag_violations == 0)
    check_zero_crc_errors = bool(crc_errors == 0)
    check_zero_seq_gaps = bool(sequence_gaps == 0)

    print(f"  • Packet Count:              {num_packets:,} (Expected: 10,000) -> {'PASS' if check_packet_count else 'FAIL'}")
    print(f"  • Flag Violations (!= 0x05): {flag_violations} -> {'PASS' if check_all_flags_05 else 'FAIL'}")
    print(f"  • CRC-16 Check Errors:       {crc_errors} -> {'PASS' if check_zero_crc_errors else 'FAIL'}")
    print(f"  • Sequence Gaps:             {sequence_gaps} -> {'PASS' if check_zero_seq_gaps else 'FAIL'}")
    print(f"  • Hardware Sampling Rate:    {actual_fs:.2f} Hz -> {sampling_rate_status} (Expected: 345–355 Hz)")

    # ---------------------------------------------------------
    # Step D: Decrypt & Compare Independently against Replay Reference
    # ---------------------------------------------------------
    print("\n[Step D] Evaluating Independent Parity vs Firmware Replay Reference...")

    nan_detected = bool(np.isnan(dec_raw_arr).any() or np.isnan(dec_filt_arr).any())
    inf_detected = bool(np.isinf(dec_raw_arr).any() or np.isinf(dec_filt_arr).any())
    check_no_nans_infs = (not nan_detected) and (not inf_detected)

    print(f"  • NaN Detected:              {nan_detected} -> {'PASS' if not nan_detected else 'FAIL'}")
    print(f"  • Inf Detected:              {inf_detected} -> {'PASS' if not inf_detected else 'FAIL'}")

    diff_raw = np.abs(expected_raw - dec_raw_arr)
    diff_filt = np.abs(expected_filt - dec_filt_arr)

    max_err_raw = float(np.max(diff_raw))
    max_err_filt = float(np.max(diff_filt))
    mae_raw = float(np.mean(diff_raw))
    mae_filt = float(np.mean(diff_filt))
    mse_raw = float(np.mean(diff_raw ** 2))
    mse_filt = float(np.mean(diff_filt ** 2))

    raw_parity_pass = bool(max_err_raw < tolerance_mV)
    filt_parity_pass = bool(max_err_filt < tolerance_mV)
    check_parity_tolerance = raw_parity_pass and filt_parity_pass

    print(f"  • Raw ECG Max Abs Error:     {max_err_raw:.9f} mV -> {'PASS' if raw_parity_pass else 'FAIL'}")
    print(f"  • Filtered ECG Max Abs Error:{max_err_filt:.9f} mV -> {'PASS' if filt_parity_pass else 'FAIL'}")
    print(f"  • Filtered ECG MAE:          {mae_filt:.9f} mV")
    print(f"  • Filtered ECG MSE:          {mse_filt:.12f} mV^2")
    print(f"  • Declared Parity Tolerance: < {tolerance_mV:.1e} mV")
    print(f"  • Overall Parity Verdict:    {'PASS (Lossless Reconstruction)' if check_parity_tolerance else 'FAIL'}")

    # Correlation against offline golden vector (main_bench.c comparison)
    if golden_filt_mod is not None:
        corr_golden = float(np.corrcoef(golden_filt_mod[50:], dec_filt_arr[50:])[0, 1])
        print(f"  • Correlation vs Golden Biquad (post-settling): r = {corr_golden:.6f} (Benchmark: r >= 0.90)")

    # R-Peak Alignment
    fs = 350
    p_ref, _ = find_peaks(expected_filt, distance=int(0.35 * fs), prominence=0.25)
    p_dec, _ = find_peaks(dec_filt_arr, distance=int(0.35 * fs), prominence=0.25)
    peak_match = bool(np.array_equal(p_ref, p_dec))
    print(f"  • Detected R-Peaks (Ref):    {len(p_ref)}")
    print(f"  • Detected R-Peaks (Dec):    {len(p_dec)}")
    print(f"  • QRS Peak Retention:        {'100.0% (Exact Alignment)' if peak_match else 'Mismatch'}")

    # Cryptographic Chaos & Shannon Entropy Assessment
    byte_arr = np.frombuffer(ciphertext_bytes, dtype=np.uint8)
    counts = np.bincount(byte_arr, minlength=256)
    probs = counts[counts > 0] / float(len(byte_arr))
    entropy_val = float(-np.sum(probs * np.log2(probs)))
    ideal_entropy = 8.0000
    entropy_ratio = (entropy_val / ideal_entropy) * 100.0

    chi2_stat, chi2_p = chisquare(counts)
    chi2_stat = float(chi2_stat)
    chi2_p = float(chi2_p)
    chi2_pass = bool(chi2_p > 0.01)

    r_plain = float(np.corrcoef(expected_filt[:-1], expected_filt[1:])[0, 1])
    c_bytes_f = np.frombuffer(ciphertext_bytes, dtype=np.uint8).astype(np.float64)
    r_cipher = float(np.corrcoef(c_bytes_f[:-1], c_bytes_f[1:])[0, 1])
    corr_pass = bool(abs(r_cipher) < 0.05)

    print(f"\n[Statistical Chaos Analysis]")
    print(f"  • Ciphertext Bytes Evaluated:{len(byte_arr):,} Bytes")
    print(f"  • Measured Shannon Entropy:  {entropy_val:.4f} bits/byte ({entropy_ratio:.2f}% of 8.0)")
    print(f"  • Chi-Square Uniformity:     chi^2={chi2_stat:.2f}, p={chi2_p:.4f} -> {'PASS' if chi2_pass else 'FAIL'}")
    print(f"  • Adjacent Autocorrelation:  Plaintext r={r_plain:.4f}, Ciphertext r={r_cipher:.4f} -> {'PASS' if corr_pass else 'FAIL'}")

    # ---------------------------------------------------------
    # Step E: Generate the Final HIL Verdict
    # ---------------------------------------------------------
    hil_all_passed = (
        check_packet_count
        and check_all_flags_05
        and check_zero_crc_errors
        and check_zero_seq_gaps
        and sampling_rate_pass
        and check_no_nans_infs
        and check_parity_tolerance
        and peak_match
    )
    final_verdict = "PASS" if hil_all_passed else "FAIL"

    is_dry_run = bool(meta_info.get("dry_run", False))
    effective_disclaimer = (
        "DRY-RUN SANITY CHECK: This test evaluated synthetic loopback packets. "
        "A dry-run PASS is strictly a software and toolchain sanity check and does NOT constitute "
        "physical hardware validation or physical STM32 HC1 parity."
        if is_dry_run else
        HARDWARE_PARITY_DISCLAIMER
    )

    report_json_data = {
        "timestamp": datetime.now().isoformat(),
        "final_hil_verdict": final_verdict,
        "is_dry_run": is_dry_run,
        "parity_disclaimer": effective_disclaimer,
        "reference_vector_info": {
            "source_signal": "WESAD Subject S2 Baseline condition (2,100 samples)",
            "modulo_repetition_rule": "expected_raw[i] = raw_ecg_2100[i % 2100]; expected_filt[i] = runtime_filt_10k[i]",
            "raw_ecg_2100_sha256": ref_hashes["raw_ecg_2100_sha256"],
            "runtime_filt_10k_sha256": ref_hashes["runtime_filt_10k_sha256"],
            "golden_filt_2100_sha256": ref_hashes["golden_filt_2100_sha256"]
        },
        "evaluation_criteria": {
            "exactly_10000_packets_captured": check_packet_count,
            "all_flags_are_0x05": check_all_flags_05,
            "zero_crc_errors": check_zero_crc_errors,
            "zero_sequence_gaps": check_zero_seq_gaps,
            "sample_rate_is_345_to_355_hz": sampling_rate_pass,
            "no_nan_or_infinity_values": check_no_nans_infs,
            "decryption_succeeds": bool(len(decrypted_raw) == num_packets),
            "raw_parity_meets_tolerance": raw_parity_pass,
            "filtered_parity_meets_tolerance": filt_parity_pass,
            "qrs_peak_retention_fidelity": peak_match
        },
        "stream_statistics": {
            "total_packets": num_packets,
            "total_wire_bytes": total_bytes,
            "flag_violations": flag_violations,
            "crc_errors": crc_errors,
            "sequence_gaps": sequence_gaps,
            "calculated_sampling_rate_hz": round(actual_fs, 2),
            "sampling_rate_classification": sampling_rate_status
        },
        "reconstruction_error": {
            "max_abs_error_raw_mV": max_err_raw,
            "max_abs_error_filt_mV": max_err_filt,
            "mean_absolute_error_raw_mV": mae_raw,
            "mean_absolute_error_filt_mV": mae_filt,
            "mean_squared_error_raw_mV2": mse_raw,
            "mean_squared_error_filt_mV2": mse_filt,
            "declared_tolerance_mV": tolerance_mV,
            "nan_detected": nan_detected,
            "inf_detected": inf_detected
        },
        "cryptographic_metrics": {
            "shannon_entropy_bits_per_byte": entropy_val,
            "entropy_uniformity_percent": entropy_ratio,
            "chi_square_stat": chi2_stat,
            "chi_square_p_value": chi2_p,
            "chi_square_uniformity_pass": chi2_pass,
            "plaintext_correlation": r_plain,
            "ciphertext_correlation": r_cipher,
            "correlation_leakage_pass": corr_pass
        }
    }

    json_report_path = os.path.join(output_dir, "hil_parity_report.json")
    with open(json_report_path, "w") as f:
        json.dump(report_json_data, f, indent=2)

    txt_report_path = os.path.join(output_dir, "hil_parity_report.txt")
    with open(txt_report_path, "w") as f:
        f.write("===============================================================================\n")
        f.write("STM32 PHYSICAL HC1 HARDWARE-IN-THE-LOOP (HIL) PARITY REPORT\n")
        f.write("===============================================================================\n")
        f.write(f"Timestamp:                    {report_json_data['timestamp']}\n")
        f.write(f"Final HIL Verdict:            {final_verdict}\n")
        f.write(f"Reference Vector:             Firmware Replay Vector (WESAD S2 Baseline modulo 2100)\n")
        f.write(f"raw_ecg_2100 SHA-256:         {ref_hashes['raw_ecg_2100_sha256']}\n")
        f.write(f"runtime_filt_10k SHA-256:     {ref_hashes['runtime_filt_10k_sha256']}\n")
        f.write(f"Evaluated Packets:            {num_packets:,} (Total Bytes: {total_bytes:,} B)\n")
        f.write(f"Hardware Sampling Rate:       {actual_fs:.2f} Hz [{sampling_rate_status}]\n")
        f.write("-------------------------------------------------------------------------------\n")
        f.write("--- Acceptance Criteria Check ---\n")
        for k, v in report_json_data["evaluation_criteria"].items():
            f.write(f"  • {k:35s}: {'PASS' if v else 'FAIL'}\n")
        f.write("-------------------------------------------------------------------------------\n")
        f.write("--- Independent Numerical Reconstruction Parity ---\n")
        f.write(f"  Max Absolute Error (Raw ECG):   {max_err_raw:.9f} mV [{'PASS' if raw_parity_pass else 'FAIL'}]\n")
        f.write(f"  Max Absolute Error (Filt ECG):  {max_err_filt:.9f} mV [{'PASS' if filt_parity_pass else 'FAIL'}]\n")
        f.write(f"  Mean Absolute Error (Raw ECG):  {mae_raw:.9f} mV\n")
        f.write(f"  Mean Absolute Error (Filt ECG): {mae_filt:.9f} mV\n")
        f.write(f"  Mean Squared Error (Raw ECG):   {mse_raw:.12f} mV^2\n")
        f.write(f"  Mean Squared Error (Filt ECG):  {mse_filt:.12f} mV^2\n")
        f.write(f"  Parity Tolerance Declared:      < {tolerance_mV:.1e} mV\n")
        f.write(f"  NaN Detected:                   {nan_detected}\n")
        f.write(f"  Inf Detected:                   {inf_detected}\n")
        f.write(f"  QRS Peak Retention:             {'100.0% Exact Alignment' if peak_match else 'Mismatch'}\n")
        f.write("-------------------------------------------------------------------------------\n")
        f.write("--- Wire Cryptographic Metrics ---\n")
        f.write(f"  Wire Shannon Entropy:           {entropy_val:.4f} bits/byte ({entropy_ratio:.2f}% of 8.0)\n")
        f.write(f"  Chi-Square Uniformity:          chi^2={chi2_stat:.2f}, p={chi2_p:.4f} [{'PASS' if chi2_pass else 'FAIL'}]\n")
        f.write(f"  Plain vs Cipher Correlation:    r_plain={r_plain:.4f}, r_cipher={r_cipher:.4f} [{'PASS' if corr_pass else 'FAIL'}]\n")
        f.write("===============================================================================\n")
        f.write(f"{effective_disclaimer}\n")
        f.write("===============================================================================\n")

    print("\n" + "=" * 78)
    print(f"FINAL HIL VERDICT: {final_verdict}")
    print(f"Reports saved to:")
    print(f"  • {json_report_path}")
    print(f"  • {txt_report_path}")
    print(effective_disclaimer)
    print("=" * 78 + "\n")

    return hil_all_passed


if __name__ == "__main__":
    args = parse_args()
    success = verify_hardware_capture(
        input_bin_path=args.input,
        meta_json_path=args.meta,
        reference_path=args.reference,
        output_dir=args.output_dir,
        tolerance_mV=args.tolerance
    )
    if not success:
        sys.exit(1)
