# Physical Hardware-in-the-Loop (HIL) Verification Plan: M-4DCHS / HC1

**Date:** 2026-10-01  
**Project:** ECG Stress Detection IoMT Pipeline  
**Target Hardware:** STMicroelectronics NUCLEO-G474RE (STM32G474RET6, ARM Cortex-M4 @ 170 MHz)  
**Output Directory:** `results/verification/hc1_hardware_hil/`  
**Execution Status:** PLAN READY — WAITING FOR EXPLICIT USER APPROVAL BEFORE FLASHING  

---

## 1. Binary & Source Verification

- **Binary to Be Flashed:** `embedded_stm32/STM32G474_HC1_Telemetry.bin` (11,316 Bytes, Flash base address `0x08000000`).
- **Source Code Origin:** Built from `embedded_stm32/src/main_stm32.c` with CMSIS-DSP filter (`ecg_dsp_filter.c`), HC1 chaos encryption (`telemetry_protocol.c`), and WESAD Subject S2 benchmark samples (`wesad_test_samples.c`). In Stage 4 build verification, recompilation using official GNU ARM Embedded Toolchain (`arm-none-eabi-gcc 14.3.1`) produced a 100% byte-for-byte SHA-256 match.
- **Expected Firmware Configuration:**
  - `USE_ENCRYPTION_MODE = 2` (Mode 2: 4D Memristive Hyperchaos M-4DCHS / HC1)
  - `USE_LIVE_AD8232_ADC = 0` (WESAD dataset replay from internal Flash array `WESAD_S2_RAW_ECG[2100]`, repeated continuously via modulo indexing `g_sample_idx = (g_sample_idx + 1) % 2100` from `S2_Baseline_raw`)
  - `ECG_SAMPLE_RATE_HZ = 350` Hz (Timer TIM2 periodic interrupt @ $350.017\text{ Hz}$, interval $2.857\text{ ms}$)
  - Wire Packet Flags: `0x05` (`TELEMETRY_FLAG_ENCRYPTED | TELEMETRY_FLAG_CHAOS_4D`)
  - Frame Format: 20 bytes/frame (`0xAA 0x55` sync header, CCITT CRC-16 over bytes 2..17)
- **Target Interface:** `COM10` (`STMicroelectronics STLink Virtual COM Port`, USB PID `0x374E`) @ `115200` baud (`8N1`).

---

## 2. Five-Stage HIL Execution Workflow

The HIL verification is split into 5 distinct, decoupled steps:

```
[ Step A: Flash HC1 Firmware ]
              │
              ▼
[ Step B: Capture Raw Packets ] ──> hardware_raw_packets.bin + hardware_raw_packets_meta.json
              │
              ▼
[ Step C: Verify Packet Integrity & Flags ]
              │
              ▼
[ Step D: Decrypt & Compare against Golden Reference ]
              │
              ▼
[ Step E: Generate Final HIL Verdict ] ──> hil_parity_report.json + hil_parity_report.txt
```

---

### Step A: Flash HC1 Firmware to STM32G474RE

Flashing uses the official STMicroelectronics CLI programmer via the onboard ST-LINK SWD interface:

```cmd
"C:\ST\STM32CubeIDE_2.2.0\STM32CubeIDE\plugins\com.st.stm32cube.ide.mcu.externaltools.cubeprogrammer.win32_2.2.500.202603051304\tools\bin\STM32_Programmer_CLI.exe" -c port=SWD -w "C:\Users\YASH\Desktop\projects\RESEARCH PROJECTS\ECG_STRESS_DETECTION\embedded_stm32\STM32G474_HC1_Telemetry.bin" 0x08000000 -v -rst
```

**Parameters Explained:**
- `-c port=SWD`: Connects via Serial Wire Debug protocol.
- `-w <path> 0x08000000`: Programs binary image into Flash sector 0.
- `-v`: Reads back Flash memory and verifies byte-for-byte against the local binary.
- `-rst`: Issues hardware reset to boot the newly flashed firmware.
- Output log saved to: `results/verification/hc1_hardware_hil/hardware_flash_log.txt`.

---

### Step B: Capture Raw Wire Packets (`capture_hardware_telemetry.py`)

A dedicated streaming capture utility captures the physical wire telemetry over `COM10`:

```powershell
python python/capture_hardware_telemetry.py --port COM10 --baud 115200 --packets 10000 --output results/verification/hc1_hardware_hil/hardware_raw_packets.bin
```

**Safety & Ingestion Mechanics:**
1. Wait 2.5 seconds after flashing for the ST-LINK USB Virtual COM port to stabilize.
2. In `python/capture_hardware_telemetry.py`, configures DTR and RTS low before opening to reduce reset risk; hardware-driver behavior must still be observed.
3. Synchronizes to 2-byte frame header `0xAA 0x55`.
4. Streams exactly 10,000 packets ($200,000\text{ bytes}$) @ $350\text{ Hz}$ ($\approx 28.57\text{ seconds}$, timeout 35.0s).
5. Writes raw wire stream to `results/verification/hc1_hardware_hil/hardware_raw_packets.bin`.
6. Writes capture manifest to `results/verification/hc1_hardware_hil/hardware_raw_packets_meta.json`.

---

### Step C: Verify Packet Integrity, Flags & Sampling Rate

Executed by `python/verify_hardware_hc1_capture.py`:
1. **Frame Header & Size Validation:**
   - Confirm exactly 10,000 packets of 20 bytes each ($200,000\text{ bytes}$).
   - Verify every frame begins with sync bytes `0xAA 0x55` and version `0x01`.
2. **Protocol Flags Verification:**
   - Verify all 10,000 packets have `flags == 0x05`. Zero flag violations permitted.
3. **CRC-16-CCITT Verification:**
   - Independently compute CRC-16 over bytes 2..17 of each packet and compare with transmitted bytes 18..19.
   - Acceptance: 0 CRC errors across all 10,000 packets.
4. **Sequence Continuity:**
   - Confirm $(seq_{i} - seq_{i-1}) \pmod{65536} == 1$. Zero sequence gaps permitted.
5. **Sampling Rate Result Classification:**
   - Compute empirical hardware sampling rate from hardware timestamps:
     $$f_s = \frac{10000 - 1}{(t_{9999} - t_{0}) \times 10^{-3}}\text{ Hz}$$
   - **PASS**: $345.0\text{ Hz} \le f_s \le 355.0\text{ Hz}$.
   - **FAIL**: $f_s < 345.0\text{ Hz}$ or $f_s > 355.0\text{ Hz}$.

---

### Step D: Decrypt & Compare against Golden Reference

Executed by `python/verify_hardware_hc1_capture.py`:
1. **Physical Ciphertext Decryption:**
   - Extract ciphertext payload bytes 10..17 from each packet.
   - Decrypt using host Python `m4d_decrypt_ecg(payload, seq_id, timestamp_ms)`.
2. **Numerical Validity:**
   - Check decrypted float arrays: Zero NaNs and zero Infinities permitted.
3. **Reconstruction Parity vs. Canonical Firmware Replay Reference:**
   - Compare decrypted raw ECG against `results/verification/hc1_hardware_hil/firmware_replay_reference.npz` (`raw_ecg_2100[i % 2100]` derived from `S2_Baseline_raw`).
   - Compare decrypted filtered ECG against the canonical runtime filtered signal (`runtime_filt_10k` from `firmware_replay_reference.npz`, reflecting real-time 5-stage Biquad IIR state continuity across 10,000 samples).
   - Compute metrics:
     - Maximum Absolute Reconstruction Error: Must be $< 1.0 \times 10^{-5}\text{ mV}$ for both raw and filtered channels.
     - Mean Squared Error (MSE): Must be $< 1.0 \times 10^{-10}\text{ mV}^2$.
     - Mean Absolute Error (MAE): Must be $< 1.0 \times 10^{-6}\text{ mV}$.
4. **Clinical QRS Alignment:**
   - Detect R-peaks on golden filtered ECG and decrypted filtered ECG (`find_peaks`, distance 122, prominence 0.25).
   - Acceptance: 100.0% exact alignment (zero displaced or omitted peaks).
5. **Wire Statistical Chaos Assessment:**
   - Shannon Entropy on 80,000 intercepted ciphertext bytes: $> 7.99\text{ bits/byte}$.
   - Chi-Square Uniformity: $p > 0.01$.
   - Autocorrelation: Adjacent ciphertext sample correlation $|r| < 0.05$.

---

### Step E: Generate the Final HIL Verdict

`python/verify_hardware_hc1_capture.py` compiles the comprehensive HIL audit reports:
- `results/verification/hc1_hardware_hil/hil_parity_report.json`
- `results/verification/hc1_hardware_hil/hil_parity_report.txt`

#### Mandatory Acceptance Criteria for Final HIL Verdict = PASS:
The final HIL verdict is **PASS** if and only if **all eight (8)** of the following conditions are simultaneously met:
1. Exactly 10,000 packets captured ($200,000\text{ bytes}$).
2. All 10,000 packets have `flags == 0x05` (zero flag violations).
3. Zero CRC errors ($10,000 / 10,000$ valid CRCs).
4. Zero sequence gaps (zero dropped packets).
5. Hardware sampling rate is between $345.0\text{ Hz}$ and $355.0\text{ Hz}$ (**PASS** classification).
6. Zero NaN and zero Infinity values in decrypted signals.
7. Decryption succeeds for all 10,000 packets.
8. Plaintext reconstruction parity meets the declared tolerance:
   $$\max |\text{ECG}_{\text{golden}} - \text{ECG}_{\text{dec}}| < 1.0 \times 10^{-5}\text{ mV}$$

If any single condition fails, the final HIL verdict is recorded as **FAIL**.

---

## 3. Hardware, Environmental & Permission Risks

| Risk | Likelihood | Impact | Mitigation Strategy |
|---|---|---|---|
| **Port Contention / Access Denied** (`WinError 5`) | Medium | High | Verify no background processes or dashboards hold `COM10` prior to capture. |
| **ST-LINK SWD Enumeration Failure** | Low | High | Probe ST-LINK status first (`STM32_Programmer_CLI.exe -c port=SWD`) before writing. |
| **Windows PnP USB Disconnect upon Reset** | Medium | Low | Enforce a 2.5-second settling delay post-flash before opening `COM10`. |
| **Modem Reset Line Glitch** | Low | Low | Configures DTR and RTS low before opening to reduce reset risk; hardware-driver behavior must still be observed. |
| **Flash Endurance / Wear** | Negligible | Low | Flash rated for $\ge 10,000$ cycles. A single write of 11 KB causes zero measurable wear. |

---

## 4. Evidence Preservation Guarantee

- All outputs will be saved exclusively under `results/verification/hc1_hardware_hil/`:
  - `hardware_flash_log.txt` (Step A)
  - `hardware_raw_packets.bin` (Step B)
  - `hardware_raw_packets_meta.json` (Step B)
  - `hil_parity_report.json` (Steps C, D, E)
  - `hil_parity_report.txt` (Steps C, D, E)
- Historical audit evidence files (`results/raw_evidence_item4_parity_check.*`, `results/verification/hc1_strict_parity/*`, etc.) remain completely untouched.

---

## 5. Execution Hold & Status Clarification

> [!WARNING]
> **DRY-RUN DISCLAIMER:** Any dry-run `PASS` achieved using synthetic loopback frames or simulated packets is strictly a software and toolchain sanity check; **a dry-run PASS does NOT constitute physical hardware validation** or physical STM32 HC1 parity. Physical hardware validation requires flashing the physical STM32G474RE board, capturing physical telemetry over COM10, and verifying the physical ciphertext.

**HOLD:** Firmware flashing and physical hardware execution are paused.  
Explicit user authorization is required before executing the flash command and capturing hardware telemetry.
