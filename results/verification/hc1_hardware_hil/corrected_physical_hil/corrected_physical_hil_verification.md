# Corrected Physical Hardware-in-the-Loop (HIL) Verification Report: M-4DCHS / HC1

**Date:** 2026-10-01  
**Project:** ECG Stress Detection IoMT Pipeline  
**Target Hardware:** STMicroelectronics NUCLEO-G474RE (ARM Cortex-M4 @ 170 MHz)  
**Input Wire Artifact:** `results/verification/hc1_hardware_hil/hardware_raw_packets.bin` (200,000 Bytes, 10,000 Packets)  
**Input Metadata Artifact:** `results/verification/hc1_hardware_hil/hardware_raw_packets_meta.json`  
**Report Path:** `results/verification/hc1_hardware_hil/corrected_physical_hil/corrected_physical_hil_verification.md`  
**Overall Corrected Physical HIL Result:** **PASS** (100% Bit-Exact Identity, Lossless Reconstruction)  

---

## 1. Executive Summary

This report documents the offline re-evaluation of the preserved physical telemetry capture (`hardware_raw_packets.bin`, 10,000 packets captured over `COM10` at $350.02\text{ Hz}$) using the sequence-aligned physical HIL verification methodology.

In the initial evaluation, the unaligned verifier produced a historical failure verdict (`0.926 mV` error) because it indexed reference buffers from $0$ instead of aligning to the microcontroller's autonomous boot sequence number ($11428$). 

Under the corrected methodology:
1. **Raw ECG Alignment:** The reference sample index is monotonically aligned to each packet's wire sequence number:
   $$\text{expected\_raw}[i] = \text{raw\_ecg\_2100}[\text{seq\_id}[i] \pmod{2100}]$$
2. **Filtered Reference State Continuity:** The CMSIS-DSP Biquad Direct Form I filter is evaluated continuously from firmware boot ($\text{seq} = 0$) through the captured sequence range ($\text{seq} = 11428 \dots 21427$), reflecting the true hardware filter memory.
3. **Independent Cryptographic Initialization:** Each packet's decryption is independently initialized from its wire `seq_id` and `timestamp_ms` using `seed_from_nonce()`, conforming strictly to the protocol specification.

With this sequence alignment, the physical telemetry decrypted on Python achieves **zero numerical error ($0.000000000\text{ mV}$)** across all 10,000 packets for both raw and filtered channels.

---

## 2. Subsystem Verdict Breakdown

| Subsystem / Layer | Evaluated Parameters | Observed Metrics | Criteria | Verdict |
|---|---|---|---|:---:|
| **Physical Transport & Framing** | Frame sync header, packet count, CRC-16, sequence continuity, sampling rate | 10,000 / 10,000 packets<br>0 CRC errors<br>0 sequence gaps (0 dropped)<br>$f_s = 350.02\text{ Hz}$ | $100\%$ valid headers (`0xAA 0x55`, v1, flags `0x05`)<br>$0$ CRC errors<br>$f_s \in [345.0, 355.0]\text{ Hz}$ | **PASS** |
| **Packet Decryption** | IEEE 754 float validity, memory unpack, CFB self-contained inversion | 10,000 / 10,000 decrypted<br>0 NaNs<br>0 Infinities | Zero unpack exceptions<br>Zero NaNs or Infinities | **PASS** |
| **Wire Statistical Checks** | Keystream Shannon entropy, Chi-square uniformity, autocorrelation | Entropy: $7.9977\text{ bits/B}$ ($99.97\%$)<br>$\chi^2 = 257.79, p = 0.4394$<br>Ciphertext $r = 0.0012$ | Entropy $> 7.99\text{ bits/B}$<br>$\chi^2$ $p > 0.01$<br>Autocorrelation $\|r\| < 0.05$ | **PASS** |
| **Raw ECG Parity** | Physical Flash replay vs decrypted raw channel | Max Abs Error: **$0.000000000\text{ mV}$**<br>MAE: $0.000000000\text{ mV}$<br>MSE: $0.000000000\text{ mV}^2$ | $\max \|\text{err}\| < 1.0 \times 10^{-5}\text{ mV}$ | **PASS** |
| **Filtered ECG Parity** | Causal CMSIS-DSP Biquad filter state vs decrypted filtered channel | Max Abs Error: **$0.000000000\text{ mV}$**<br>MAE: $0.000000000\text{ mV}$<br>MSE: $0.000000000\text{ mV}^2$<br>QRS peak retention: $100\%$ (39 / 39) | $\max \|\text{err}\| < 1.0 \times 10^{-5}\text{ mV}$<br>Exact QRS peak retention | **PASS** |
| **Overall Corrected Physical HIL Result** | Simultaneous fulfillment of all subsystem criteria | All 5 subsystems PASS | All criteria met | **PASS** |

---

## 3. Wire Statistical Checks Disclaimer

> [!NOTE]
> **STATISTICAL WIRE CHECKS NOTICE:**  
> Shannon entropy ($7.9977\text{ bits/byte}$) and Chi-Square goodness-of-fit uniformity ($p = 0.4394$) evaluate pseudo-random keystream distribution and byte uniformity across wire frames. These tests verify the absence of trivial keystream collapse or zero-padding on the physical wire; **they do not constitute mathematical proof of cryptographic security.**

---

## 4. Contextual Clarification: Historical vs. Corrected Findings

- **Initial Historical Report (`results/verification/hc1_hardware_hil/hil_parity_report.json`):**  
  Produced a historical `FAIL` verdict with maximum absolute error of $0.926056\text{ mV}$. This result was caused by the unaligned verifier comparing packet index $k$ against reference sample index $k \pmod{2100}$, ignoring the physical microcontroller's autonomous boot sequence number ($11428$). This introduced an artificial 928-sample ($2.651\text{ s}$) phase shift between the transmitted and reference waveforms.
- **Corrected Report (`results/verification/hc1_hardware_hil/corrected_physical_hil/corrected_hil_parity_report.json`):**  
  Accounts for physical hardware progression by evaluating $\text{raw\_ref}[\text{seq}_k \pmod{2100}]$ and advancing the Biquad filter state continuously from sequence 0 to sequence 21427. Decryption recovers the transmitted signal with **bit-exact identity ($0.000000000\text{ mV}$ max error)** across all 10,000 packets.

---

## 5. Artifact Preservation Summary

All historical and corrected artifacts remain strictly isolated:
- Historical unaligned reports preserved:  
  - [`results/verification/hc1_hardware_hil/hil_parity_report.json`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/results/verification/hc1_hardware_hil/hil_parity_report.json)  
  - [`results/verification/hc1_hardware_hil/hil_parity_report.txt`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/results/verification/hc1_hardware_hil/hil_parity_report.txt)  
  - [`results/verification/hc1_hardware_hil/physical_hil_failure_root_cause.md`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/results/verification/hc1_hardware_hil/physical_hil_failure_root_cause.md)
- Corrected aligned outputs generated:  
  - [`results/verification/hc1_hardware_hil/corrected_physical_hil/corrected_hil_parity_report.json`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/results/verification/hc1_hardware_hil/corrected_physical_hil/corrected_hil_parity_report.json)  
  - [`results/verification/hc1_hardware_hil/corrected_physical_hil/corrected_hil_parity_report.txt`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/results/verification/hc1_hardware_hil/corrected_physical_hil/corrected_hil_parity_report.txt)  
  - [`results/verification/hc1_hardware_hil/corrected_physical_hil/corrected_physical_hil_verification.md`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/results/verification/hc1_hardware_hil/corrected_physical_hil/corrected_physical_hil_verification.md)
