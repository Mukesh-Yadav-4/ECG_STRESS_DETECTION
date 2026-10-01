# Physical Hardware-in-the-Loop Telemetry Capture & Verification Review

**Date:** 2026-10-01  
**Project:** ECG Stress Detection IoMT Pipeline  
**Target Hardware:** STMicroelectronics NUCLEO-G474RE (`COM10` @ 115200 baud)  
**Document Path:** `results/verification/hc1_hardware_hil/capture_script_review.md`  
**Execution Status:** SCRIPTS READY & VALIDATED IN DRY-RUN — HARDWARE UNTOUCHED  

---

## 1. Architectural Separation: Capture vs. Verification

In accordance with strict verification audit principles, the physical HIL workflow strictly separates wire packet capture from cryptographic/clinical verification:
- **Wire Capture (`python/capture_hardware_telemetry.py`)**:  
  Responsible solely for safe, non-destructive streaming from `COM10`, enforcing framing sync (`0xAA 0x55`), validating packet flags (`0x05`), checking on-chip CRC-16, monitoring sequence continuity, classifying sampling rate, and saving exact 200,000 raw wire bytes to disk with JSON metadata. **It does not perform decryption, signal filtering, or plaintext parity checks.**
- **Offline Cryptographic & Parity Verifier (`python/verify_hardware_hc1_capture.py`)**:  
  Consumes the captured raw packet file, capture metadata, and canonical firmware replay reference (`firmware_replay_reference.npz`, derived from WESAD Subject S2 Baseline modulo 2100). It performs HC1 Python decryption, verifies the absence of NaNs/infinities, evaluates reconstruction parity (Max Abs Error, MAE, MSE against `raw_ecg_2100[i % 2100]` and `runtime_filt_10k`), tests R-peak alignment fidelity, and computes wire Shannon entropy and Chi-square uniformity before issuing the final HIL verdict.

---

## 2. Evaluation of Options & Selection

### Inspection of Existing Receiver (`python/stm32_telemetry_receiver.py`)
`stm32_telemetry_receiver.py` is the live dashboard inference engine and streaming receiver. It uses default `serial.Serial()` settings without explicitly setting DTR/RTS lines low prior to opening, and lacks dedicated CLI flags for dumping unparsed wire bytes, classifying sampling rate, or recording sequence gap statistics.

### Selected Option: Option B (Dedicated Narrowly Scoped Tools)
- `python/capture_hardware_telemetry.py` (dedicated physical capture)
- `python/verify_hardware_hc1_capture.py` (dedicated offline cryptographic and clinical verifier)

### Key Characteristics:
1. **Zero Impact on Production Code:** Existing files (`stm32_telemetry_receiver.py`, `app.py`, `train_loso_ml_benchmark.py`, firmware) remain completely untouched.
2. **Explicit DTR/RTS Configuration:** Configures DTR and RTS low before opening to reduce reset risk; hardware-driver behavior must still be observed.
3. **Strict Flag Gating:** Aborts capture and flags an error if any received packet has `flags != 0x05`.
4. **CRC-16 Validation:** Computes CCITT CRC-16 over bytes 2..17 for each packet and rejects corrupted frames.
5. **Sequence-Gap Analytics:** Monitors sequence monotonicity (`(seq[i] - seq[i-1]) == 1`) and flags sequence gaps.
6. **Sampling Rate Result Classification:**  
   - **PASS**: Empirical sampling rate is between $345.0\text{ Hz}$ and $355.0\text{ Hz}$.  
   - **FAIL**: Empirical sampling rate is outside $[345.0, 355.0]\text{ Hz}$.
7. **Lossless Raw Capture:** Appends exact wire bytes directly to disk for downstream offline validation.
8. **Safe Dry-Run Testing:** Supports `--dry-run` to validate capture, parsing, and metadata logging using synthetic reference data without accessing COM ports.

---

## 3. Exact Commands to Run Later

### Step B: Hardware Wire Capture (Run upon user approval)
```powershell
python python/capture_hardware_telemetry.py --port COM10 --baud 115200 --packets 10000 --output results/verification/hc1_hardware_hil/hardware_raw_packets.bin
```

### Steps C, D, E: Offline Cryptographic & Parity Verification
```powershell
# Using default canonical reference (results/verification/hc1_hardware_hil/firmware_replay_reference.npz):
python python/verify_hardware_hc1_capture.py --input results/verification/hc1_hardware_hil/hardware_raw_packets.bin --meta results/verification/hc1_hardware_hil/hardware_raw_packets_meta.json --output-dir results/verification/hc1_hardware_hil
```

---

## 4. Files Changed or Added

- **Files Modified:** None (zero existing files modified).
- **Files Added:**
  - `python/capture_hardware_telemetry.py` (hardware packet capture script)
  - `python/verify_hardware_hc1_capture.py` (offline cryptographic and parity verification script)
  - `results/verification/hc1_hardware_hil/capture_script_review.md` (this review document)
  - `results/verification/hc1_hardware_hil/hil_verification_plan.md` (updated 5-step HIL plan)

---

## 5. Safety Behavior

1. **Board Reset Risk Reduction:**  
   In `python/capture_hardware_telemetry.py`:
   ```python
   ser = serial.Serial()
   ser.port = port
   ser.baudrate = baud
   ser.timeout = 0.1
   # Configures DTR and RTS low before opening to reduce reset risk; hardware-driver behavior must still be observed.
   ser.dtr = False
   ser.rts = False
   ser.open()
   ```
2. **Read Timeout & Non-Blocking Graceful Exit:**  
   The read loop uses a total capture timeout (default 35.0s for a 28.57s stream). If hardware halts or disconnects, the script raises `TimeoutError` and cleanly executes `ser.close()`.
3. **Exception Safety:**  
   The serial handle is wrapped in a `try...finally` block to ensure the OS COM handle is released even upon unhandled errors or user interrupts (Ctrl+C).

---

## 6. Validation Checks & Classification Rules

| Check | Failure Condition | Classification / Action |
|---|---|---|
| **Framing Sync Header** | First 2 bytes $\neq$ `[0xAA, 0x55]` | Slides buffer by 1 byte; increments `sync_losses`. |
| **CRC-16-CCITT** | Computed CRC $\neq$ frame `crc16` | Increments `crc_errors`; discards candidate header. |
| **Security Flags** | Frame `flags != 0x05` | Raises `ValueError`; aborts capture immediately. |
| **Sequence Continuity** | `seq != (prev_seq + 1) & 0xFFFF` | Records sequence gap and calculates dropped packet count. |
| **Sampling Rate Classification** | $f_s < 345.0\text{ Hz}$ or $f_s > 355.0\text{ Hz}$ | Classifies sampling rate as **FAIL**; **PASS** if within $[345, 355]\text{ Hz}$. |
| **Numerical Validity** | Any NaN or Inf in decrypted floats | Classifies numerical check as **FAIL**. |
| **Reconstruction Parity** | Max Abs Error $\ge 1.0 \times 10^{-5}\text{ mV}$ | Classifies reconstruction parity as **FAIL**. |
| **R-Peak Alignment** | Detected peaks $\neq$ golden reference | Classifies clinical alignment as **FAIL**. |

---

## 7. Expected Output Files

All HIL artifacts are preserved under `results/verification/hc1_hardware_hil/`:
1. `hardware_flash_log.txt`: ST-LINK Programmer CLI flash output (Step A).
2. `hardware_raw_packets.bin`: Exactly 200,000 raw wire bytes ($10,000\text{ packets} \times 20\text{ bytes/packet}$) (Step B).
3. `hardware_raw_packets_meta.json`: Capture metadata including hardware timestamp span, sampling rate classification, and flag histogram (Step B).
4. `hil_parity_report.json`: Machine-readable verification metrics, error tolerances, and final HIL verdict (Steps C, D, E).
5. `hil_parity_report.txt`: Human-readable HIL audit report (Steps C, D, E).

---

## 8. Status & Hold Notice

- Script implementation: **COMPLETE**
- Offline dry-run verification: **PASSED** (10,000 synthetic loopback reference packets verified with 0.000000000 mV error, 350.01 Hz PASS, and 100% R-peak alignment).  
  *Notice:* **A dry-run PASS is strictly a software and toolchain sanity check and does NOT constitute physical hardware validation.**
- Hardware COM10 access: **PAUSED / UNTOUCHED**
- STM32 flashing: **PAUSED / UNTOUCHED**
- Awaiting explicit user instruction before issuing hardware flash and capture commands.
