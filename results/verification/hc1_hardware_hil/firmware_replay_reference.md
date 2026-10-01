# Canonical Firmware Replay Reference Artifact: M-4DCHS / HC1

**Date:** 2026-10-01  
**Project:** ECG Stress Detection IoMT Pipeline  
**Target Hardware:** STMicroelectronics NUCLEO-G474RE  
**Artifact Directory:** `results/verification/hc1_hardware_hil/`  
**Artifact Files:**
- `firmware_replay_reference.npz` (Binary compressed numpy array)
- `firmware_replay_reference.json` (Machine-readable manifest)
- `firmware_replay_reference.md` (Specification and documentation)

---

## 1. Executive Summary & Root Cause Analysis

Prior verification workflows erroneously assumed that the STM32 firmware replayed `S2_Stress_raw[:10000]`. In-depth inspection of the embedded firmware source code (`embedded_stm32/include/wesad_test_samples.h`, `embedded_stm32/src/wesad_test_samples.c`, and `embedded_stm32/src/main_stm32.c`) reveals the exact hardware reality:

1. **Source Signal:**  
   The compiled array `WESAD_S2_RAW_ECG` comes from **`S2_Baseline_raw[:2100]`** (WESAD Subject S2, Baseline resting condition), **NOT** `S2_Stress`.
2. **Sample Count:**  
   The embedded array contains exactly **2,100 samples** (representing $6.00\text{ seconds}$ at $350\text{ Hz}$).
3. **Hardware Modulo Repetition:**  
   In `main_stm32.c` (line 98), the MCU fetches samples using:
   ```c
   raw_ecg_val = WESAD_S2_RAW_ECG[g_sample_idx];
   g_sample_idx = (g_sample_idx + 1) % WESAD_BENCHMARK_NUM_SAMPLES;
   ```
   For any stream longer than 2,100 packets (such as the standard 10,000-packet capture), the hardware wraps back to index 0 every 2,100 ticks:
   $$\text{expected\_raw}[i] = \text{WESAD\_S2\_RAW\_ECG}[i \pmod{2100}]$$
4. **Runtime Filtered Signal:**  
   The transmitted filtered ECG (`g_tx_packet.filtered_ecg`) is produced by feeding the repeating raw stream into the causal 5-stage CMSIS-DSP Biquad IIR filter (`ecg_filter_process_sample`) sample-by-sample starting from zero state buffer at power-on.
   `WESAD_S2_GOLDEN_FILT_ECG` in `wesad_test_samples.c` corresponds to offline-filtered `S2_Baseline_filt[:2100]`. Due to filter initial transient settling, the real-time causal filter output converges to steady-state periodic behavior, achieving Pearson correlation $r = 0.999$ vs. `WESAD_S2_GOLDEN_FILT_ECG`.

---

## 2. Source Files & Generation Method

- **Original Dataset:** `demo/sample_data/ecg_samples.npz` (keys: `S2_Baseline_raw`, `S2_Baseline_filt`).
- **Generation Script:** `python/export_embedded_constants.py` (`generate_test_vectors()`).
- **Embedded C Source Files:**
  - `embedded_stm32/include/wesad_test_samples.h` (macro `WESAD_BENCHMARK_NUM_SAMPLES = 2100`)
  - `embedded_stm32/src/wesad_test_samples.c` (`WESAD_S2_RAW_ECG[2100]` and `WESAD_S2_GOLDEN_FILT_ECG[2100]`)
  - `embedded_stm32/src/ecg_dsp_filter.c` (5-stage Biquad IIR Direct Form I filter @ 350 Hz)
  - `embedded_stm32/src/main_stm32.c` (runtime replay loop with modulo 2100)

---

## 3. Cryptographic Hashes (SHA-256)

All arrays are single-precision 32-bit IEEE-754 floats (`float32`, little-endian):

| Array Name | Dimensions | Byte Length | SHA-256 Checksum | Description |
|---|:---:|:---:|---|---|
| `raw_ecg_2100` | 2,100 | 8,400 B | `106fbd7d56a678c10aa60541b697326de3a761456dded54c3e1fa6443eb866db` | Embedded `WESAD_S2_RAW_ECG[2100]` array |
| `golden_filt_2100` | 2,100 | 8,400 B | `6976019e5aa5601d7966d020ac9642cca3854f102e69f60c0c5427fb1df0b8cd` | Embedded `WESAD_S2_GOLDEN_FILT_ECG[2100]` array |
| `runtime_filt_10k` | 10,000 | 40,000 B | `d4e252a8536377ace9140c303f0fee43339cc589ad1fbb271d70623fa65f32d8` | Exact causal 10,000-sample runtime filter output |

---

## 4. Modulo Indexing & Repetition Rule

For a capture of $N = 10,000$ packets ($i = 0, 1, 2, \dots, 9999$):

1. **Raw ECG Expected Stream:**
   $$\text{expected\_raw}[i] = \text{raw\_ecg\_2100}[i \pmod{2100}]$$
2. **Filtered ECG Expected Stream:**
   - **Primary Parity Target (Exact Causal DSP Output):**
     $$\text{expected\_filt}[i] = \text{runtime\_filt\_10k}[i]$$
     (Derived from `ecg_filter_process_sample` on `expected_raw[i]` starting from zero state).
     Tolerance: $\max |\text{decrypted\_filt}[i] - \text{runtime\_filt\_10k}[i]| < 1.0 \times 10^{-5}\text{ mV}$.
   - **Secondary Benchmark Target (Offline Golden Vector):**
     $$\text{golden\_filt\_ref}[i] = \text{golden\_filt\_2100}[i \pmod{2100}]$$
     Evaluated via Pearson correlation ($r \ge 0.90$) and RMSE, matching `embedded_stm32/main_bench.c`.

---

## 5. Summary Table for Verification

```text
Replay Vector Name:   WESAD_S2_RAW_ECG (Baseline condition)
Base Vector Length:   2,100 samples (6.00 s @ 350 Hz)
Total HIL Evaluation: 10,000 packets (4.76 full repetitions)
Repetition 0:         Samples     0 ..  2099
Repetition 1:         Samples  2100 ..  4199
Repetition 2:         Samples  4200 ..  6299
Repetition 3:         Samples  6300 ..  8399
Repetition 4 (part):  Samples  8400 ..  9999
Parity Tolerance:     < 1.0e-5 mV (for both raw and causal filtered streams)
```
