# Preflight Verification Report: Physical STM32 HC1 HIL Test

**Date:** 2026-10-01  
**Project:** ECG Stress Detection IoMT Pipeline  
**Target Hardware:** STMicroelectronics NUCLEO-G474RE (STM32G474RET6, ARM Cortex-M4 @ 170 MHz)  
**Target Interface:** `COM10` (`STMicroelectronics STLink Virtual COM Port`, USB PID `0x374E`)  
**Report Path:** `results/verification/hc1_hardware_hil/final_hil_preflight.md`  
**Execution Status:** PREFLIGHT PASSED — HARDWARE UNTOUCHED — AWAITING EXPLICIT USER APPROVAL  

---

## 1. Preflight Verification Checklist

| Item | Requirement | Verification Command / Method | Observed Result | Status |
|:---:|---|---|---|:---:|
| **1** | Target binary exists & SHA-256 recorded | `os.path.exists()` & `hashlib.sha256()` | `embedded_stm32/STM32G474_HC1_Telemetry.bin`<br>`ed4b97b3e7279dc0f6d2add3a21b1ddf45347dbc9e8bfa21f1f48ac86657edc1` | **PASS** |
| **2** | Target binary size = 11,316 bytes | `os.path.getsize()` | **11,316 bytes** (exact match) | **PASS** |
| **3** | Canonical reference file exists & contains valid keys | `np.load('results/verification/hc1_hardware_hil/firmware_replay_reference.npz')` | Keys: `raw_ecg_2100` (2100,) `float32`<br>`runtime_filt_10k` (10000,) `float32`<br>`golden_filt_2100` (2100,) `float32` | **PASS** |
| **4** | Capture & verifier scripts compile and import cleanly | `py_compile` & Python module import | `python/capture_hardware_telemetry.py`<br>`python/verify_hardware_hc1_capture.py`<br>Zero syntax errors; all dependencies imported. | **PASS** |
| **5** | CubeProgrammer CLI command is valid | `STM32_Programmer_CLI.exe --version` | Version: **2.23.0**<br>Path: `C:\ST\STM32CubeIDE_2.2.0\STM32CubeIDE\plugins\com.st.stm32cube.ide.mcu.externaltools.cubeprogrammer.win32_2.2.500.202603051304\tools\bin\STM32_Programmer_CLI.exe` | **PASS** |
| **6** | COM10 is present (without opening port) | `Win32_PnPEntity` & `SerialPort.GetPortNames()` | `STMicroelectronics STLink Virtual COM Port (COM10)`<br>DeviceID: `USB\VID_0483&PID_374E&MI_02\6&119284EA&0&0002`<br>Port was not opened. | **PASS** |
| **7** | No process currently owns COM10 | Read-only process inspection (`Get-Process`) | 0 Python / terminal / serial monitoring processes running. COM10 is completely unheld. | **PASS** |
| **8** | Output paths strictly within `results/verification/hc1_hardware_hil/` | Path validation | All 5 target outputs strictly reside under `results/verification/hc1_hardware_hil/`. Zero historical files touched. | **PASS** |
| **9** | Confirmation that flashing alters hardware & requires approval | Hardware safety policy check | **Confirmed:** Flashing writes physical MCU Flash and resets CPU. Requires explicit user authorization. | **PASS** |

---

## 2. Detailed Findings

### 2.1 Target Binary Metadata
- **File:** `embedded_stm32/STM32G474_HC1_Telemetry.bin`
- **File Size:** `11,316` Bytes
- **SHA-256:** `ed4b97b3e7279dc0f6d2add3a21b1ddf45347dbc9e8bfa21f1f48ac86657edc1`
- **Compiled Parameters:**
  - `USE_ENCRYPTION_MODE = 2` (M-4DCHS / HC1 4D Memristive Hyperchaos)
  - `USE_LIVE_AD8232_ADC = 0` (Replay from internal Flash array `WESAD_S2_RAW_ECG[2100]` modulo 2100)
  - `ECG_SAMPLE_RATE_HZ = 350` Hz (Timer TIM2 periodic interrupt @ 350.017 Hz)
  - Wire Packet Flags: `0x05` (`TELEMETRY_FLAG_ENCRYPTED | TELEMETRY_FLAG_CHAOS_4D`)

### 2.2 Canonical Reference Vector Status
- **File:** `results/verification/hc1_hardware_hil/firmware_replay_reference.npz`
- **Array 1:** `raw_ecg_2100` — shape `(2100,)`, dtype `float32`, SHA-256 `106fbd7d56a678c10aa60541b697326de3a761456dded54c3e1fa6443eb866db`.
- **Array 2:** `runtime_filt_10k` — shape `(10000,)`, dtype `float32`, SHA-256 `d4e252a8536377ace9140c303f0fee43339cc589ad1fbb271d70623fa65f32d8`.
- **Enforcement:** Noncanonical or legacy fallback datasets (such as `demo/sample_data/ecg_samples.npz` or `S2_Stress`) are rejected with a fatal `ValueError`.

### 2.3 Script Compilation & Toolchain Readiness
Both dedicated tools passed static compilation and dependency resolution:
- `python/capture_hardware_telemetry.py` (Streams wire packets, gates flags `0x05`, checks CRC-16, tracks sequence gaps, calculates empirical sampling rate, outputs raw binary).
- `python/verify_hardware_hc1_capture.py` (Decrypts wire ciphertext, validates absence of NaNs/infs, checks float32 parity vs canonical vectors, tests QRS peak alignment, computes Shannon entropy and Chi-square uniformity).

### 2.4 Interface & Port Status
- **Device Description:** `STMicroelectronics STLink Virtual COM Port (COM10)`
- **Device ID:** `USB\VID_0483&PID_374E&MI_02\6&119284EA&0&0002`
- **Port State:** Present, active in Windows Device Manager, but **unopened and untouched**.
- **Process Lock Inspection:** No active process or serial terminal holds `COM10`.

### 2.5 Planned Output Directory & Isolation
All generated artifacts will be saved exclusively under `results/verification/hc1_hardware_hil/`:
1. `hardware_flash_log.txt` (Step A: Flashing log)
2. `hardware_raw_packets.bin` (Step B: 200,000 raw wire bytes)
3. `hardware_raw_packets_meta.json` (Step B: Ingestion metadata and sampling rate classification)
4. `hil_parity_report.json` (Steps C–E: Machine-readable parity metrics and final verdict)
5. `hil_parity_report.txt` (Steps C–E: Formatted audit verification report)

Historical evidence files (`results/raw_evidence_item4_parity_check.*`, `results/verification/hc1_strict_parity/*`) remain completely untouched.

---

## 3. Physical State & Authorization Notice

> [!CAUTION]
> **FLASHING ALTERS PHYSICAL HARDWARE STATE:**  
> Executing the CubeProgrammer CLI command erases Sector 0 of the physical microcontroller Flash memory, writes the new 11,316-byte HC1 telemetry binary, and performs a hardware MCU reset (`-rst`).  
> **Physical hardware execution is on strict hold.**  
> Neither flashing nor port opening will be initiated without explicit user instructions.
