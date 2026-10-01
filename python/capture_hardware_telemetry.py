"""
=============================================================================
Non-Destructive Physical Hardware Telemetry Capture Script for STM32G474RE
Edge-IoMT Wearable Telemetry Obfuscation & Parity Verification (M-4DCHS / HC1)
=============================================================================
Safely streams binary telemetry packets from STM32 Virtual COM port:
  - Configures DTR and RTS low before opening to reduce reset risk; hardware-driver behavior must still be observed.
  - Synchronizes to framing header (0xAA 0x55)
  - Enforces strict packet flags requirement (default: flags == 0x05)
  - Computes and verifies CRC-16-CCITT for every received frame
  - Tracks sequence continuity and detects sequence gaps
  - Calculates physical timestamp advancement and actual sampling rate
  - Preserves exact raw wire bytes to binary output file
  - Supports --dry-run mode for safe offline testing without opening COM ports
=============================================================================
"""

import os
import sys
import time
import json
import struct
import argparse
from typing import Dict, List, Optional, Tuple
from collections import Counter

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "python"))

from stm32_telemetry_receiver import (
    SYNC_BYTE_0,
    SYNC_BYTE_1,
    FRAME_SIZE,
    FRAME_STRUCT,
    compute_crc16,
    build_c_packet
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Non-destructive physical telemetry packet capture for STM32G474RE HC1."
    )
    parser.add_argument(
        "--port",
        type=str,
        default="COM10",
        help="Serial COM port for ST-LINK Virtual COM Port (default: COM10)"
    )
    parser.add_argument(
        "--baud",
        type=int,
        default=115200,
        help="Baud rate (default: 115200)"
    )
    parser.add_argument(
        "--packets",
        type=int,
        default=10000,
        help="Number of packets to capture (default: 10000)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=os.path.join(PROJECT_ROOT, "results", "verification", "hc1_hardware_hil", "hardware_raw_packets.bin"),
        help="Path to save captured raw binary wire bytes"
    )
    parser.add_argument(
        "--meta-output",
        type=str,
        default=None,
        help="Optional path to save JSON capture metadata (default: <output>_meta.json)"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=35.0,
        help="Total capture timeout in seconds (default: 35.0s)"
    )
    parser.add_argument(
        "--require-flags",
        type=lambda x: int(x, 0),
        default=0x05,
        help="Required packet flags byte (default: 0x05 = Encrypted | 4D Chaos)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate packet capture locally without opening any physical serial port"
    )
    return parser.parse_args()


def run_capture(
    port: str,
    baud: int,
    target_packets: int,
    output_path: str,
    meta_path: Optional[str] = None,
    timeout_sec: float = 35.0,
    required_flags: int = 0x05,
    dry_run: bool = False
) -> Dict:
    """Captures and validates binary telemetry packets non-destructively."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    if meta_path is None:
        meta_path = os.path.splitext(output_path)[0] + "_meta.json"

    print("=" * 76)
    print("STM32G474RE TELEMETRY CAPTURE & INTEGRITY VERIFICATION ENGINE")
    print("=" * 76)
    print(f"Target Packets:        {target_packets:,} packets ({target_packets * FRAME_SIZE:,} bytes)")
    print(f"Required Packet Flags: 0x{required_flags:02X}")
    print(f"Output Binary File:    {output_path}")
    print(f"Metadata Output File:  {meta_path}")

    raw_packets_buffer = bytearray()
    flags_counter = Counter()
    timestamps: List[int] = []
    seq_ids: List[int] = []

    sync_losses = 0
    crc_errors = 0
    sequence_gaps = 0
    dropped_packets = 0
    last_seq: Optional[int] = None

    start_wall_time = time.time()

    if dry_run:
        print("\n[MODE: DRY-RUN SIMULATION] Generating synthetic packets locally from canonical firmware replay reference...")
        import numpy as np
        ref_npz_path = os.path.join(PROJECT_ROOT, "results", "verification", "hc1_hardware_hil", "firmware_replay_reference.npz")
        if os.path.exists(ref_npz_path):
            r_data = np.load(ref_npz_path)
            raw_ref_2100 = r_data["raw_ecg_2100"]
            filt_ref_10k = r_data["runtime_filt_10k"]
            sim_raw = [float(raw_ref_2100[i % 2100]) for i in range(target_packets)]
            sim_filt = [float(filt_ref_10k[i]) for i in range(target_packets)]
        else:
            sample_path = os.path.join(PROJECT_ROOT, "demo", "sample_data", "ecg_samples.npz")
            if os.path.exists(sample_path):
                s_data = np.load(sample_path)
                s2_base_raw = s_data["S2_Baseline_raw"][:2100]
                sim_raw = [float(s2_base_raw[i % 2100]) for i in range(target_packets)]
                sim_filt = [-0.450] * target_packets
            else:
                sim_raw = [1.025] * target_packets
                sim_filt = [-0.450] * target_packets

        for i in range(target_packets):
            ts = int((i / 350.0) * 1000)
            pkt_bytes = build_c_packet(
                seq_id=i % 65536,
                timestamp_ms=ts,
                raw_val=sim_raw[i],
                filt_val=sim_filt[i],
                flags=required_flags
            )
            raw_packets_buffer.extend(pkt_bytes)
            sync, ver, flg, seq, ts_ms, r_val, f_val, rx_crc = FRAME_STRUCT.unpack(pkt_bytes)
            flags_counter[flg] += 1
            timestamps.append(ts_ms)
            seq_ids.append(seq)
            if last_seq is not None:
                expected_seq = (last_seq + 1) & 0xFFFF
                if seq != expected_seq:
                    gap = (seq - expected_seq) & 0xFFFF
                    sequence_gaps += 1
                    dropped_packets += gap
            last_seq = seq
        elapsed_time = time.time() - start_wall_time
    else:
        import serial

        print(f"\nOpening serial port {port} @ {baud} baud (dtr=False, rts=False, timeout=0.1s)...")
        ser = serial.Serial()
        ser.port = port
        ser.baudrate = baud
        ser.timeout = 0.1
        # Configures DTR and RTS low before opening to reduce reset risk; hardware-driver behavior must still be observed.
        ser.dtr = False
        ser.rts = False

        try:
            ser.open()
        except Exception as e:
            raise RuntimeError(f"Failed to open {port}: {e}. Ensure device is connected and port is not in use.")

        print(f"Serial port {port} opened successfully. Capturing stream...")

        stream_buffer = bytearray()
        packets_captured = 0

        try:
            while packets_captured < target_packets:
                if (time.time() - start_wall_time) > timeout_sec:
                    raise TimeoutError(
                        f"Capture timed out after {timeout_sec:.1f}s! Captured {packets_captured}/{target_packets} packets."
                    )

                chunk = ser.read(max(1, min(4096, (target_packets - packets_captured) * FRAME_SIZE)))
                if not chunk:
                    continue
                stream_buffer.extend(chunk)

                while len(stream_buffer) >= FRAME_SIZE and packets_captured < target_packets:
                    # Search for sync header
                    if stream_buffer[0] != SYNC_BYTE_0 or stream_buffer[1] != SYNC_BYTE_1:
                        stream_buffer.pop(0)
                        sync_losses += 1
                        continue

                    frame_bytes = bytes(stream_buffer[:FRAME_SIZE])
                    sync, ver, flg, seq, ts_ms, r_val, f_val, rx_crc = FRAME_STRUCT.unpack(frame_bytes)

                    # CRC check over payload bytes [2..17]
                    expected_crc = compute_crc16(frame_bytes[2:18])
                    if rx_crc != expected_crc:
                        crc_errors += 1
                        stream_buffer.pop(0)
                        continue

                    # Frame is valid
                    stream_buffer = stream_buffer[FRAME_SIZE:]
                    raw_packets_buffer.extend(frame_bytes)
                    packets_captured += 1

                    flags_counter[flg] += 1
                    timestamps.append(ts_ms)
                    seq_ids.append(seq)

                    # Check required flags
                    if flg != required_flags:
                        raise ValueError(
                            f"Packet {packets_captured} flag violation: Expected 0x{required_flags:02X}, got 0x{flg:02X}!"
                        )

                    # Sequence check
                    if last_seq is not None:
                        expected_seq = (last_seq + 1) & 0xFFFF
                        if seq != expected_seq:
                            gap = (seq - expected_seq) & 0xFFFF
                            sequence_gaps += 1
                            dropped_packets += gap
                    last_seq = seq

        finally:
            try:
                ser.close()
                print(f"Serial port {port} closed cleanly.")
            except Exception:
                pass

        elapsed_time = time.time() - start_wall_time

    # Compute sampling metrics
    total_captured = len(timestamps)
    assert total_captured == target_packets, f"Incomplete capture: {total_captured} != {target_packets}"
    assert len(raw_packets_buffer) == target_packets * FRAME_SIZE, "Byte count mismatch!"

    if total_captured > 1:
        ts_span_ms = timestamps[-1] - timestamps[0]
        actual_fs = (total_captured - 1) / (ts_span_ms / 1000.0) if ts_span_ms > 0 else 0.0
    else:
        ts_span_ms = 0
        actual_fs = 0.0

    sampling_rate_pass = (345.0 <= actual_fs <= 355.0)
    sampling_rate_status = "PASS" if sampling_rate_pass else "FAIL"

    # Save raw wire packets
    with open(output_path, "wb") as f:
        f.write(raw_packets_buffer)

    meta_data = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "port": port if not dry_run else "DRY_RUN_SYNTHETIC",
        "baud": baud,
        "dry_run": dry_run,
        "target_packets": target_packets,
        "captured_packets": total_captured,
        "captured_bytes": len(raw_packets_buffer),
        "capture_elapsed_sec": round(elapsed_time, 3),
        "hardware_timestamp_span_ms": ts_span_ms,
        "calculated_sampling_rate_hz": round(actual_fs, 2),
        "sampling_rate_classification": sampling_rate_status,
        "sampling_rate_pass": sampling_rate_pass,
        "sync_losses": sync_losses,
        "crc_errors": crc_errors,
        "sequence_gaps": sequence_gaps,
        "dropped_packets": dropped_packets,
        "required_flags": f"0x{required_flags:02X}",
        "flags_histogram": {f"0x{k:02X}": v for k, v in flags_counter.items()},
        "all_flags_match_required": (len(flags_counter) == 1 and required_flags in flags_counter),
        "raw_binary_path": os.path.abspath(output_path)
    }

    with open(meta_path, "w") as f:
        json.dump(meta_data, f, indent=2)

    print("\n" + "=" * 76)
    print("CAPTURE COMPLETE & INTEGRITY VERIFIED")
    print("=" * 76)
    print(f"Captured Packets:          {total_captured:,} / {target_packets:,}")
    print(f"Captured Wire Bytes:       {len(raw_packets_buffer):,} Bytes")
    print(f"Capture Duration:          {elapsed_time:.2f} s")
    print(f"Hardware Sampling Rate:    {actual_fs:.2f} Hz (Expected ~350 Hz)")
    print(f"CRC Errors:                {crc_errors}")
    print(f"Sync Losses:               {sync_losses}")
    print(f"Sequence Gaps:             {sequence_gaps} (Dropped packets: {dropped_packets})")
    print(f"Flags Distribution:        {meta_data['flags_histogram']}")
    print(f"Flags Integrity:           {'PASS (100% 0x05)' if meta_data['all_flags_match_required'] else 'FAIL'}")
    print(f"Raw Wire Data Saved:       {output_path}")
    print(f"Metadata Saved:            {meta_path}")
    print("=" * 76 + "\n")

    return meta_data


if __name__ == "__main__":
    args = parse_args()
    run_capture(
        port=args.port,
        baud=args.baud,
        target_packets=args.packets,
        output_path=args.output,
        meta_path=args.meta_output,
        timeout_sec=args.timeout,
        required_flags=args.require_flags,
        dry_run=args.dry_run
    )
