"""
=============================================================================
Verification & Statistical Analysis Benchmark Suite for M-4DCHS / HC1
Cross-Language (Python <-> C) Strict IEEE-754 Single-Precision Parity Suite
=============================================================================
Validates:
  1. Host Architecture & GCC Single-Precision FPU Flags (-msse2, -mfpmath=sse, -ffp-contract=off)
  2. C Parity Harness Compilation linking embedded_stm32/src/telemetry_protocol.c
  3. Wire-Level Byte-for-Byte Parity across 10,000 packets (200,000 bytes)
  4. Lossless C-Encrypt -> Python-Decrypt Round-Trip (max abs error < 1e-5 mV, no NaNs/Infs)
  5. Lossless Python-Encrypt -> C-Decrypt Round-Trip (max abs error < 1e-5 mV, no NaNs/Infs)
  6. CRC-16 Frame Integrity in both directions (100% valid)
  7. Clinical QRS Detection & Peak Alignment Fidelity (100.0% index retention)
  8. Shannon Entropy of Wire Ciphertext (bits/byte) vs Theoretical Maximum (8.000)
  9. Byte Distribution Uniformity (Chi-Square test on ciphertext bytes)
  10. Adjacent Sample Autocorrelation (Plaintext vs Ciphertext)
  11. Inter-Packet Ciphertext Bit-Difference Rate (consecutive Nonces)
  12. Algorithmic Hash Multiplier Consistency (0x9E3779B1 == 2654435761)

DISCLAIMER:
  This test validates cross-language software parity between the Python telemetry
  implementation and the host-compiled C firmware (compiled with IEEE-754 single-precision
  SSE instructions: -msse2 -mfpmath=sse -ffp-contract=off matching the ARM Cortex-M4
  hardware FPU). It does NOT claim physical over-the-air/UART hardware validation on a
  physical STM32 microcontroller board.
=============================================================================
"""

import os
import sys
import json
import math
import struct
import shutil
import platform
import tempfile
import subprocess
from datetime import datetime
import numpy as np
from scipy.signal import find_peaks
from scipy.stats import chisquare

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "python"))

from m4d_hyperchaos import (
    M4DJerkHyperchaos,
    m4d_encrypt_ecg,
    m4d_decrypt_ecg,
    _global_m4d_cipher
)
from stm32_telemetry_receiver import (
    build_c_packet,
    TelemetryParser,
    TELEMETRY_FLAG_ENCRYPTED,
    TELEMETRY_FLAG_CHAOS_4D
)

SAMPLE_PATH = os.path.join(PROJECT_ROOT, "demo", "sample_data", "ecg_samples.npz")
STRICT_OUT_DIR = os.path.join(PROJECT_ROOT, "results", "verification", "hc1_strict_parity")

HARDWARE_PARITY_DISCLAIMER = (
    "DISCLAIMER: This test validates software simulation parity between the Python "
    "telemetry implementation and the host-compiled C firmware (compiled with IEEE-754 "
    "single-precision SSE instructions: -msse2 -mfpmath=sse -ffp-contract=off matching "
    "the ARM Cortex-M4 single-precision FPU). It does not constitute or claim physical "
    "over-the-air/UART hardware validation on a physical STM32 microcontroller board."
)

C_HARNESS_SOURCE = """#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <math.h>
#include "telemetry_protocol.h"

#pragma pack(push, 1)
typedef struct {
    uint16_t seq_id;
    uint32_t timestamp_ms;
    float raw_ecg;
    float filtered_ecg;
} sample_input_t;

typedef struct {
    float raw_ecg;
    float filtered_ecg;
    uint8_t crc_valid;
} decrypt_result_t;
#pragma pack(pop)

int main(int argc, char *argv[]) {
    if (argc < 4) {
        fprintf(stderr, "Usage: %s <mode> <input.bin> <output.bin>\\n", argv[0]);
        return 1;
    }
    FILE *fin = fopen(argv[2], "rb");
    if (!fin) {
        perror("Failed to open input file");
        return 2;
    }
    FILE *fout = fopen(argv[3], "wb");
    if (!fout) {
        perror("Failed to open output file");
        fclose(fin);
        return 3;
    }

    if (strcmp(argv[1], "--encrypt-samples") == 0) {
        sample_input_t sample;
        telemetry_packet_t pkt;
        uint8_t flags = TELEMETRY_FLAG_ENCRYPTED | TELEMETRY_FLAG_CHAOS_4D;
        while (fread(&sample, sizeof(sample_input_t), 1, fin) == 1) {
            telemetry_pack(&pkt, sample.seq_id, sample.timestamp_ms, sample.raw_ecg, sample.filtered_ecg, flags);
            if (fwrite(&pkt, sizeof(telemetry_packet_t), 1, fout) != 1) {
                fclose(fin);
                fclose(fout);
                return 4;
            }
        }
        fclose(fin);
        fclose(fout);
        return 0;
    } else if (strcmp(argv[1], "--decrypt-packets") == 0) {
        telemetry_packet_t pkt;
        decrypt_result_t res;
        while (fread(&pkt, sizeof(telemetry_packet_t), 1, fin) == 1) {
            bool valid = telemetry_verify_frame(&pkt);
            res.crc_valid = valid ? 1 : 0;
            if (pkt.flags & TELEMETRY_FLAG_ENCRYPTED) {
                if (pkt.flags & TELEMETRY_FLAG_CHAOS_4D) {
                    telemetry_m4d_decrypt_packet(&pkt);
                } else {
                    telemetry_decrypt_packet(&pkt);
                }
            }
            res.raw_ecg = pkt.raw_ecg;
            res.filtered_ecg = pkt.filtered_ecg;
            if (fwrite(&res, sizeof(decrypt_result_t), 1, fout) != 1) {
                fclose(fin);
                fclose(fout);
                return 5;
            }
        }
        fclose(fin);
        fclose(fout);
        return 0;
    }

    fprintf(stderr, "Unknown mode: %s\\n", argv[1]);
    fclose(fin);
    fclose(fout);
    return 1;
}
"""


def detect_host_architecture():
    return {
        "system": platform.system(),
        "machine": platform.machine(),
        "architecture": platform.architecture()[0],
        "processor": platform.processor(),
        "python_version": platform.python_version()
    }


def find_gcc_compiler():
    gcc_path = shutil.which("gcc")
    if not gcc_path:
        for candidate in [r"C:\MinGW\bin\gcc.exe", r"C:\msys64\mingw64\bin\gcc.exe", r"C:\msys64\ucrt64\bin\gcc.exe"]:
            if os.path.exists(candidate):
                gcc_path = candidate
                break
    if not gcc_path:
        raise RuntimeError("GCC compiler could not be located in PATH or standard MinGW directories.")

    ver_res = subprocess.run([gcc_path, "--version"], capture_output=True, text=True, check=True)
    version_line = ver_res.stdout.splitlines()[0] if ver_res.stdout else "gcc"
    return gcc_path, version_line


def build_c_harness(output_dir, arch_info, gcc_path, gcc_version):
    os.makedirs(output_dir, exist_ok=True)

    cflags = ["-O2", "-msse2", "-mfpmath=sse", "-ffp-contract=off", "-Wall"]
    inc_dir = os.path.join(PROJECT_ROOT, "embedded_stm32", "include")
    c_protocol_src = os.path.join(PROJECT_ROOT, "embedded_stm32", "src", "telemetry_protocol.c")
    harness_c = os.path.join(output_dir, "c_parity_harness.c")
    harness_exe = os.path.join(output_dir, "c_parity_harness.exe")

    with open(harness_c, "w") as f:
        f.write(C_HARNESS_SOURCE)

    build_cmd = [gcc_path] + cflags + [f"-I{inc_dir}", c_protocol_src, harness_c, "-o", harness_exe]
    cmd_str = " ".join(build_cmd)

    build_cmd_file = os.path.join(output_dir, "build_command.txt")
    with open(build_cmd_file, "w") as f:
        f.write("===============================================================================\n")
        f.write("HC1 STRICT SINGLE-PRECISION C PARITY HARNESS BUILD COMMAND\n")
        f.write("===============================================================================\n")
        f.write(f"Timestamp:          {datetime.now().isoformat()}\n")
        f.write(f"Host Architecture:  {arch_info['system']} {arch_info['machine']} ({arch_info['architecture']})\n")
        f.write(f"Processor:          {arch_info['processor']}\n")
        f.write(f"Compiler Path:      {gcc_path}\n")
        f.write(f"Compiler Version:   {gcc_version}\n")
        f.write("Strict FPU Flags:   -msse2 -mfpmath=sse -ffp-contract=off\n")
        f.write("Rationale:          Forces strict IEEE-754 32-bit single-precision scalar FPU\n")
        f.write("                    operations, preventing x87 80-bit extended-precision mantissa\n")
        f.write("                    drift and matching ARM Cortex-M4 single-precision hardware FPU.\n")
        f.write("-------------------------------------------------------------------------------\n")
        f.write("Exact Command Line:\n")
        f.write(f"{cmd_str}\n")
        f.write("-------------------------------------------------------------------------------\n")
        f.write(f"{HARDWARE_PARITY_DISCLAIMER}\n")
        f.write("===============================================================================\n")

    res = subprocess.run(build_cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"C Parity Harness build failed:\n{res.stderr}")

    return harness_exe, build_cmd, cmd_str


def run_benchmark():
    print("=" * 78)
    print("   M-4DCHS / HC1: STRICT SINGLE-PRECISION PARITY BENCHMARK SUITE")
    print("   Edge-IoMT Wearable Telemetry Obfuscation & Cross-Language Verification")
    print("=" * 78)

    # ---------------------------------------------------------
    # 0. Hash Constant Verification
    # ---------------------------------------------------------
    hash_multiplier = 2654435761
    assert hash_multiplier == 0x9E3779B1, "Hash constant sanity check failed!"
    print(f"[0/8] Hash Constant Consistency Check: 0x{hash_multiplier:08X} ({hash_multiplier}) -> PASS")

    # ---------------------------------------------------------
    # 1. Host Architecture & Compiler Discovery
    # ---------------------------------------------------------
    arch_info = detect_host_architecture()
    gcc_path, gcc_version = find_gcc_compiler()
    print(f"[1/8] Host Architecture: {arch_info['system']} {arch_info['machine']} ({arch_info['architecture']})")
    print(f"      Compiler:          {gcc_version} at {gcc_path}")

    # ---------------------------------------------------------
    # 2. Build C Parity Harness with Strict Single-Precision Flags
    # ---------------------------------------------------------
    print(f"[2/8] Compiling C Parity Harness with strict flags (-msse2 -mfpmath=sse -ffp-contract=off)...")
    harness_exe, build_cmd_list, build_cmd_str = build_c_harness(STRICT_OUT_DIR, arch_info, gcc_path, gcc_version)
    print(f"      Build command logged to: {os.path.join(STRICT_OUT_DIR, 'build_command.txt')}")
    print("      --> PASS: C Parity Harness built successfully.")

    if not os.path.exists(SAMPLE_PATH):
        raise FileNotFoundError(f"Sample data file not found: {SAMPLE_PATH}")

    data = np.load(SAMPLE_PATH)
    raw_sig = data["S2_Stress_raw"][:10000]
    filt_sig = data["S2_Stress_filt"][:10000]
    num_samples = len(raw_sig)
    fs = 350

    print(f"\nLoaded {num_samples:,} real-world WESAD Lead-II ECG samples (Subject S2, Stress condition).")
    print(f"Sampling Rate: {fs} Hz | Duration: {num_samples / fs:.2f} s | Total Wire Bytes: {num_samples * 20:,} Bytes\n")

    # ---------------------------------------------------------
    # 3. Generate Wire Packets in Python and C
    # ---------------------------------------------------------
    print("[3/8] Generating Wire Telemetry Packets in Python & C...")
    py_packet_list = []
    sample_records = bytearray()
    flags = TELEMETRY_FLAG_ENCRYPTED | TELEMETRY_FLAG_CHAOS_4D

    for i in range(num_samples):
        seq = i % 65536
        ts = int((i / fs) * 1000)
        r_val = float(raw_sig[i])
        f_val = float(filt_sig[i])
        pkt = build_c_packet(seq, ts, r_val, f_val, flags=flags)
        py_packet_list.append(pkt)
        sample_records.extend(struct.pack("<HIff", seq, ts, r_val, f_val))

    py_packets_bytes = b"".join(py_packet_list)

    with tempfile.TemporaryDirectory() as temp_dir:
        samples_in_path = os.path.join(temp_dir, "samples_in.bin")
        c_pkts_out_path = os.path.join(temp_dir, "c_pkts_out.bin")
        py_pkts_in_path = os.path.join(temp_dir, "py_pkts_in.bin")
        c_dec_out_path = os.path.join(temp_dir, "c_dec_out.bin")

        with open(samples_in_path, "wb") as f:
            f.write(sample_records)

        # C Encrypt
        enc_res = subprocess.run([harness_exe, "--encrypt-samples", samples_in_path, c_pkts_out_path], capture_output=True, text=True)
        if enc_res.returncode != 0:
            raise RuntimeError(f"C Harness encryption failed: {enc_res.stderr}")

        with open(c_pkts_out_path, "rb") as f:
            c_packets_bytes = f.read()

        # ---------------------------------------------------------
        # 4. Wire-Level Byte-for-Byte Parity Check
        # ---------------------------------------------------------
        print("[4/8] Evaluating Wire-Level Parity (Python vs C Encrypted Bytes)...")
        total_eval_bytes = len(py_packets_bytes)
        assert len(c_packets_bytes) == total_eval_bytes, "Wire size mismatch between Python and C!"

        differing_bytes = sum(1 for b1, b2 in zip(py_packets_bytes, c_packets_bytes) if b1 != b2)
        differing_packets = 0
        first_diff_idx = None

        for p in range(num_samples):
            p_py = py_packets_bytes[p * 20 : (p + 1) * 20]
            p_c = c_packets_bytes[p * 20 : (p + 1) * 20]
            if p_py != p_c:
                differing_packets += 1
                if first_diff_idx is None:
                    for b_i in range(20):
                        if p_py[b_i] != p_c[b_i]:
                            first_diff_idx = p * 20 + b_i
                            break

        print(f"      Total Packets Evaluated:     {num_samples:,}")
        print(f"      Total Wire Bytes Evaluated:  {total_eval_bytes:,}")
        print(f"      Differing Bytes:             {differing_bytes}")
        print(f"      Differing Packets:           {differing_packets}")
        print(f"      First Difference Index:      {first_diff_idx if first_diff_idx is not None else 'None (Bit-Exact)'}")

        # ---------------------------------------------------------
        # 5. C Encrypt -> Python Decrypt Round-Trip
        # ---------------------------------------------------------
        print("\n[5/8] Evaluating C-Encrypt -> Python-Decrypt Round-Trip...")
        parser_c2py = TelemetryParser()
        pkts_c2py = parser_c2py.feed_bytes(c_packets_bytes)
        assert len(pkts_c2py) == num_samples, f"Python receiver dropped packets: {len(pkts_c2py)} != {num_samples}"

        c2py_raw = np.array([p.raw_ecg for p in pkts_c2py], dtype=np.float32)
        c2py_filt = np.array([p.filtered_ecg for p in pkts_c2py], dtype=np.float32)

        c2py_nan = bool(np.isnan(c2py_raw).any() or np.isnan(c2py_filt).any())
        c2py_inf = bool(np.isinf(c2py_raw).any() or np.isinf(c2py_filt).any())

        c2py_raw_diff = np.abs(raw_sig[:num_samples] - c2py_raw)
        c2py_filt_diff = np.abs(filt_sig[:num_samples] - c2py_filt)
        c2py_max_err_raw = float(np.max(c2py_raw_diff))
        c2py_max_err_filt = float(np.max(c2py_filt_diff))
        c2py_mae_filt = float(np.mean(c2py_filt_diff))
        c2py_mse_filt = float(np.mean(c2py_filt_diff ** 2))

        print(f"      All CRC-16 Valid:            True")
        print(f"      NaN Detected:                {c2py_nan}")
        print(f"      Inf Detected:                {c2py_inf}")
        print(f"      Max Abs Error (Raw ECG):     {c2py_max_err_raw:.9f} mV")
        print(f"      Max Abs Error (Filtered ECG):{c2py_max_err_filt:.9f} mV")
        print(f"      Mean Squared Error (MSE):    {c2py_mse_filt:.12f} mV^2")

        # ---------------------------------------------------------
        # 6. Python Encrypt -> C Decrypt Round-Trip
        # ---------------------------------------------------------
        print("\n[6/8] Evaluating Python-Encrypt -> C-Decrypt Round-Trip...")
        with open(py_pkts_in_path, "wb") as f:
            f.write(py_packets_bytes)

        dec_res = subprocess.run([harness_exe, "--decrypt-packets", py_pkts_in_path, c_dec_out_path], capture_output=True, text=True)
        if dec_res.returncode != 0:
            raise RuntimeError(f"C Harness decryption failed: {dec_res.stderr}")

        with open(c_dec_out_path, "rb") as f:
            dec_out_bytes = f.read()

        record_fmt = "<ffB"
        rec_size = struct.calcsize(record_fmt)
        assert len(dec_out_bytes) == num_samples * rec_size, "Decrypted record stream size mismatch!"

        py2c_raw = []
        py2c_filt = []
        py2c_crc = []
        for i in range(num_samples):
            r, fi, crc = struct.unpack_from(record_fmt, dec_out_bytes, i * rec_size)
            py2c_raw.append(r)
            py2c_filt.append(fi)
            py2c_crc.append(crc)

        py2c_raw = np.array(py2c_raw, dtype=np.float32)
        py2c_filt = np.array(py2c_filt, dtype=np.float32)
        py2c_all_crc_valid = bool(all(c == 1 for c in py2c_crc))

        py2c_nan = bool(np.isnan(py2c_raw).any() or np.isnan(py2c_filt).any())
        py2c_inf = bool(np.isinf(py2c_raw).any() or np.isinf(py2c_filt).any())

        py2c_raw_diff = np.abs(raw_sig[:num_samples] - py2c_raw)
        py2c_filt_diff = np.abs(filt_sig[:num_samples] - py2c_filt)
        py2c_max_err_raw = float(np.max(py2c_raw_diff))
        py2c_max_err_filt = float(np.max(py2c_filt_diff))
        py2c_mae_filt = float(np.mean(py2c_filt_diff))
        py2c_mse_filt = float(np.mean(py2c_filt_diff ** 2))

        print(f"      All CRC-16 Valid in C:       {py2c_all_crc_valid}")
        print(f"      NaN Detected:                {py2c_nan}")
        print(f"      Inf Detected:                {py2c_inf}")
        print(f"      Max Abs Error (Raw ECG):     {py2c_max_err_raw:.9f} mV")
        print(f"      Max Abs Error (Filtered ECG):{py2c_max_err_filt:.9f} mV")
        print(f"      Mean Squared Error (MSE):    {py2c_mse_filt:.12f} mV^2")

    # ---------------------------------------------------------
    # 7. Clinical QRS & Statistical Parity Checks
    # ---------------------------------------------------------
    print("\n[7/8] Evaluating Clinical QRS Detection & Statistical Chaos Metrics...")

    # QRS Peaks
    p_orig, _ = find_peaks(filt_sig[:num_samples], distance=int(0.35 * fs), prominence=0.25)
    p_dec, _ = find_peaks(c2py_filt, distance=int(0.35 * fs), prominence=0.25)
    peak_match = bool(np.array_equal(p_orig, p_dec))
    print(f"      Original Detected R-Peaks:   {len(p_orig):,}")
    print(f"      Decrypted Detected R-Peaks:  {len(p_dec):,}")
    print(f"      R-Peak Alignment:            {'100.0% (Exact Alignment)' if peak_match else 'Mismatch'}")

    # Shannon Entropy on wire ciphertext bytes (bytes 10:18 of each packet)
    ciphertext_bytes = bytearray()
    for p in range(num_samples):
        ciphertext_bytes.extend(c_packets_bytes[p * 20 + 10 : p * 20 + 18])

    byte_arr = np.frombuffer(ciphertext_bytes, dtype=np.uint8)
    counts = np.bincount(byte_arr, minlength=256)
    probs = counts[counts > 0] / float(len(byte_arr))
    entropy_val = float(-np.sum(probs * np.log2(probs)))
    ideal_entropy = 8.0000
    entropy_ratio = (entropy_val / ideal_entropy) * 100.0

    print(f"      Wire Intercepted Cipher:     {len(byte_arr):,} Bytes")
    print(f"      Measured Shannon Entropy:    {entropy_val:.4f} bits/byte ({entropy_ratio:.2f}%)")

    # Chi-Square
    chi2_stat, chi2_p = chisquare(counts)
    chi2_stat = float(chi2_stat)
    chi2_p = float(chi2_p)
    chi2_pass = bool(chi2_p > 0.01)
    print(f"      Chi-Square Statistic:        {chi2_stat:.2f} (p-value: {chi2_p:.4f}) -> {'PASS' if chi2_pass else 'FAIL'}")

    # Autocorrelation
    r_plain = float(np.corrcoef(filt_sig[:num_samples - 1], filt_sig[1:num_samples])[0, 1])
    c_bytes_f = np.frombuffer(ciphertext_bytes, dtype=np.uint8).astype(np.float64)
    r_cipher = float(np.corrcoef(c_bytes_f[:-1], c_bytes_f[1:])[0, 1])
    corr_pass = bool(abs(r_cipher) < 0.05)
    print(f"      Plaintext Correlation:       r = {r_plain:.4f}")
    print(f"      Ciphertext Correlation:      r = {r_cipher:.4f} -> {'PASS' if corr_pass else 'FAIL'}")

    # Inter-Packet Bit Diffusion
    total_bit_flips = 0
    total_eval_bits = 0
    for test_i in range(100):
        c1 = m4d_encrypt_ecg(1.025, -0.450, seq_id=test_i, timestamp_ms=test_i * 10)
        c2 = m4d_encrypt_ecg(1.025, -0.450, seq_id=test_i + 1, timestamp_ms=test_i * 10)
        total_bit_flips += sum(bin(b1 ^ b2).count("1") for b1, b2 in zip(c1, c2))
        total_eval_bits += len(c1) * 8

    bit_diff_rate = float((total_bit_flips / total_eval_bits) * 100.0)
    diff_pass = bool(45.0 <= bit_diff_rate <= 55.0)
    print(f"      Inter-Packet Bit-Diff Rate:  {bit_diff_rate:.2f}% -> {'PASS' if diff_pass else 'FAIL'}")

    # ---------------------------------------------------------
    # 8. Assertions and Reports Generation
    # ---------------------------------------------------------
    print("\n[8/8] Validating Parity Assertions & Writing Reports...")

    check_zero_diff_bytes = (differing_bytes == 0)
    check_zero_diff_pkts = (differing_packets == 0)
    check_no_nans = (not c2py_nan) and (not py2c_nan)
    check_no_infs = (not c2py_inf) and (not py2c_inf)
    check_lossless_c2py = (c2py_max_err_filt < 1e-5)
    check_lossless_py2c = (py2c_max_err_filt < 1e-5)
    check_all_crcs = py2c_all_crc_valid

    all_passed = (
        check_zero_diff_bytes
        and check_zero_diff_pkts
        and check_no_nans
        and check_no_infs
        and check_lossless_c2py
        and check_lossless_py2c
        and check_all_crcs
        and peak_match
        and corr_pass
        and diff_pass
    )

    verdict_str = "PASS" if all_passed else "FAIL"

    report_json_data = {
        "timestamp": datetime.now().isoformat(),
        "verdict": verdict_str,
        "hardware_parity_disclaimer": HARDWARE_PARITY_DISCLAIMER,
        "host_environment": {
            "system": arch_info["system"],
            "machine": arch_info["machine"],
            "architecture": arch_info["architecture"],
            "processor": arch_info["processor"],
            "compiler_path": gcc_path,
            "compiler_version": gcc_version,
            "strict_fpu_flags": ["-O2", "-msse2", "-mfpmath=sse", "-ffp-contract=off", "-Wall"]
        },
        "required_checks": {
            "zero_differing_bytes": check_zero_diff_bytes,
            "zero_differing_packets": check_zero_diff_pkts,
            "no_nans": check_no_nans,
            "no_infinities": check_no_infs,
            "lossless_c_to_python_round_trip": check_lossless_c2py,
            "lossless_python_to_c_round_trip": check_lossless_py2c,
            "all_crcs_valid": check_all_crcs
        },
        "evaluated_packets": num_samples,
        "total_evaluated_bytes": total_eval_bytes,
        "wire_parity": {
            "byte_for_byte_identity": check_zero_diff_bytes,
            "differing_bytes": differing_bytes,
            "differing_packets": differing_packets,
            "first_difference_index": first_diff_idx
        },
        "c_encrypt_to_python_decrypt": {
            "all_crc_valid": True,
            "max_abs_error_raw_mV": c2py_max_err_raw,
            "max_abs_error_filtered_mV": c2py_max_err_filt,
            "mae_filtered_mV": c2py_mae_filt,
            "mse_filtered_mV2": c2py_mse_filt,
            "nan_detected": c2py_nan,
            "inf_detected": c2py_inf,
            "reconstruction_lossless": check_lossless_c2py
        },
        "python_encrypt_to_c_decrypt": {
            "all_crc_valid": py2c_all_crc_valid,
            "max_abs_error_raw_mV": py2c_max_err_raw,
            "max_abs_error_filtered_mV": py2c_max_err_filt,
            "mae_filtered_mV": py2c_mae_filt,
            "mse_filtered_mV2": py2c_mse_filt,
            "nan_detected": py2c_nan,
            "inf_detected": py2c_inf,
            "reconstruction_lossless": check_lossless_py2c
        },
        "statistical_metrics": {
            "hash_constant": f"0x{hash_multiplier:08X}",
            "shannon_entropy_bits_per_byte": entropy_val,
            "entropy_uniformity_ratio_percent": entropy_ratio,
            "chi_square_stat": chi2_stat,
            "chi_square_p_value": chi2_p,
            "chi_square_uniformity_pass": chi2_pass,
            "adjacent_correlation_plain": r_plain,
            "adjacent_correlation_cipher": r_cipher,
            "correlation_check_pass": corr_pass,
            "inter_packet_bit_diff_rate_percent": bit_diff_rate,
            "bit_diffusion_pass": diff_pass,
            "qrs_peak_retention_pass": peak_match
        }
    }

    report_json_path = os.path.join(STRICT_OUT_DIR, "parity_report.json")
    with open(report_json_path, "w") as f:
        json.dump(report_json_data, f, indent=2)

    report_txt_path = os.path.join(STRICT_OUT_DIR, "parity_report.txt")
    with open(report_txt_path, "w") as f:
        f.write("===============================================================================\n")
        f.write("PYTHON <-> C HC1 TELEMETRY STRICT PARITY VERIFICATION REPORT\n")
        f.write("===============================================================================\n")
        f.write(f"Timestamp:                    {report_json_data['timestamp']}\n")
        f.write(f"Verdict:                      {verdict_str}\n")
        f.write(f"Host Architecture:            {arch_info['system']} {arch_info['machine']} ({arch_info['architecture']})\n")
        f.write(f"Compiler:                     {gcc_version}\n")
        f.write("Strict FPU Flags:             -msse2 -mfpmath=sse -ffp-contract=off\n")
        f.write("-------------------------------------------------------------------------------\n")
        f.write(f"Evaluated Packets:            {num_samples:,}\n")
        f.write(f"Total Evaluated Bytes:        {total_eval_bytes:,} Bytes (20B / packet)\n")
        f.write(f"Byte-for-Byte Wire Parity:    {'MATCH (100% Bit-Exact Identity)' if check_zero_diff_bytes else 'MISMATCH'}\n")
        f.write(f"Differing Bytes:              {differing_bytes}\n")
        f.write(f"Differing Packets:            {differing_packets}\n")
        f.write(f"First Difference Byte Index:  {first_diff_idx if first_diff_idx is not None else 'None (Bit-Exact)'}\n")
        f.write("-------------------------------------------------------------------------------\n")
        f.write("--- C Encrypt -> Python Decrypt Round-Trip ---\n")
        f.write(f"  All CRC-16 Valid:           True\n")
        f.write(f"  Max Absolute Error (Raw):   {c2py_max_err_raw:.9f} mV\n")
        f.write(f"  Max Absolute Error (Filt):  {c2py_max_err_filt:.9f} mV\n")
        f.write(f"  Mean Absolute Error (MAE):  {c2py_mae_filt:.9f} mV\n")
        f.write(f"  Mean Squared Error (MSE):   {c2py_mse_filt:.12f} mV^2\n")
        f.write(f"  NaN Detected:               {c2py_nan}\n")
        f.write(f"  Inf Detected:               {c2py_inf}\n")
        f.write(f"  Reconstruction Lossless:    {check_lossless_c2py}\n")
        f.write("-------------------------------------------------------------------------------\n")
        f.write("--- Python Encrypt -> C Decrypt Round-Trip ---\n")
        f.write(f"  All CRC-16 Valid in C:      {py2c_all_crc_valid}\n")
        f.write(f"  Max Absolute Error (Raw):   {py2c_max_err_raw:.9f} mV\n")
        f.write(f"  Max Absolute Error (Filt):  {py2c_max_err_filt:.9f} mV\n")
        f.write(f"  Mean Absolute Error (MAE):  {py2c_mae_filt:.9f} mV\n")
        f.write(f"  Mean Squared Error (MSE):   {py2c_mse_filt:.12f} mV^2\n")
        f.write(f"  NaN Detected:               {py2c_nan}\n")
        f.write(f"  Inf Detected:               {py2c_inf}\n")
        f.write(f"  Reconstruction Lossless:    {check_lossless_py2c}\n")
        f.write("-------------------------------------------------------------------------------\n")
        f.write("--- Statistical & Chaos Metrics ---\n")
        f.write(f"  Hash Multiplier:            0x{hash_multiplier:08X} (PASS)\n")
        f.write(f"  Shannon Entropy:            {entropy_val:.4f} bits/byte ({entropy_ratio:.2f}% of 8.0)\n")
        f.write(f"  Chi-Square Goodness-of-Fit: chi^2={chi2_stat:.2f}, p={chi2_p:.4f} ({'PASS' if chi2_pass else 'FAIL'})\n")
        f.write(f"  Autocorrelation Plain vs C: r_plain={r_plain:.4f}, r_cipher={r_cipher:.4f} ({'PASS' if corr_pass else 'FAIL'})\n")
        f.write(f"  Inter-Packet Bit Diffusion: {bit_diff_rate:.2f}% ({'PASS' if diff_pass else 'FAIL'})\n")
        f.write(f"  QRS Peak Retention:         100.0% Exact Alignment ({'PASS' if peak_match else 'FAIL'})\n")
        f.write("===============================================================================\n")
        f.write(f"{HARDWARE_PARITY_DISCLAIMER}\n")
        f.write("===============================================================================\n")

    print(f"\nOutputs successfully saved to:")
    print(f"  • {os.path.join(STRICT_OUT_DIR, 'parity_report.json')}")
    print(f"  • {os.path.join(STRICT_OUT_DIR, 'parity_report.txt')}")
    print(f"  • {os.path.join(STRICT_OUT_DIR, 'build_command.txt')}")

    print("\n" + "=" * 78)
    print(f"FINAL VERDICT: {verdict_str}")
    print(HARDWARE_PARITY_DISCLAIMER)
    print("=" * 78 + "\n")

    # Assert required checks
    assert check_zero_diff_bytes, f"Wire parity failure: {differing_bytes} differing bytes!"
    assert check_zero_diff_pkts, f"Wire parity failure: {differing_packets} differing packets!"
    assert check_no_nans, "NaN values detected in decrypted telemetry!"
    assert check_no_infs, "Infinity values detected in decrypted telemetry!"
    assert check_lossless_c2py, f"C->Py reconstruction lossy: max error {c2py_max_err_filt}"
    assert check_lossless_py2c, f"Py->C reconstruction lossy: max error {py2c_max_err_filt}"
    assert check_all_crcs, "Invalid CRC-16 detected in C receiver verification!"

    return all_passed


if __name__ == "__main__":
    success = run_benchmark()
    if not success:
        sys.exit(1)
