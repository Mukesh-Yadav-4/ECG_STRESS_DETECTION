# Read-Only Consistency Audit: HC1 HIL Reference Workflow

**Date:** 2026-10-01  
**Project:** ECG Stress Detection IoMT Pipeline  
**Target Hardware:** STMicroelectronics NUCLEO-G474RE (`COM10` @ 115200 baud)  
**Report Path:** `results/verification/hc1_hardware_hil/reference_consistency_review.md`  
**Execution Status:** AUDIT COMPLETE — HARDWARE UNTOUCHED — AWAITING USER APPROVAL TO FLASH  

---

## Executive Summary

A comprehensive consistency audit was conducted on the Hardware-in-the-Loop (HIL) verification plan, telemetry capture documentation, offline verification script, and reference vectors for the STM32 M-4DCHS / HC1 chaos telemetry pipeline.

All documentation, CLI invocations, and script validations have been harmonized with the exact hardware reality of the compiled STM32 firmware binary:
1. **Replay Buffer & Modulo Rule:** The firmware binary (`embedded_stm32/STM32G474_HC1_Telemetry.bin`) compiles a 2,100-sample array (`WESAD_S2_RAW_ECG[2100]`) sourced from `S2_Baseline_raw[:2100]`, repeated indefinitely via `g_sample_idx = (g_sample_idx + 1) % 2100`.
2. **Filter State Continuity:** The CMSIS-DSP 5-stage Biquad IIR filter executes continuously in real time across the repeated signal; verification matches the exact causal state sequence (`runtime_filt_10k`).
3. **Strict Reference Protection:** The offline verifier strictly requires the canonical reference artifact (`firmware_replay_reference.npz`) and fatally rejects any legacy fallback or stress datasets.
4. **Hardware Disclaimer Enforced:** Dry-run executions are explicitly tagged with a disclaimer stating that dry-run results are simulation sanity checks and do not constitute physical hardware validation.

---

## Question 1: List of Modified Files

The consistency audit updated three files:

| File Path | Nature of Edits |
|---|---|
| `results/verification/hc1_hardware_hil/hil_verification_plan.md` | • Replaced `WESAD_S2_RAW_ECG[10000]` with `WESAD_S2_RAW_ECG[2100]`.<br>• Specified continuous modulo indexing `(g_sample_idx + 1) % 2100` from `S2_Baseline_raw`.<br>• Replaced `S2_Stress_raw[:10000]` and `S2_Stress_filt[:10000]` with canonical `firmware_replay_reference.npz` (`raw_ecg_2100` and `runtime_filt_10k`).<br>• Added prominent dry-run disclaimer warning in Section 5. |
| `results/verification/hc1_hardware_hil/capture_script_review.md` | • Replaced legacy `ecg_samples.npz` verification command with canonical default command pointing to `firmware_replay_reference.npz`.<br>• Identified `S2 Baseline` as the sole firmware source signal in Section 1.<br>• Added dry-run disclaimer clarification in Section 8. |
| `python/verify_hardware_hc1_capture.py` | • Removed legacy fallback that allowed loading `ecg_samples.npz` or unverified baseline slices.<br>• Added explicit rejection: raises `ValueError` if `raw_ecg_2100` or `runtime_filt_10k` are absent.<br>• Dynamically switches between `DRY-RUN SANITY CHECK` disclaimer and physical `HARDWARE_PARITY_DISCLAIMER` based on `dry_run` metadata.<br>• Confirmed default reference path is `firmware_replay_reference.npz`. |

---

## Question 2: Audit of Remaining Stale References

A static search was executed across all documentation, markdown files, JSON descriptors, and Python scripts in the HIL suite:

1. **`WESAD_S2_RAW_ECG[10000]` References:**
   - **Status:** **0 occurrences** remaining in the HIL suite.
   - All references now accurately specify `WESAD_S2_RAW_ECG[2100]` matching `embedded_stm32/include/wesad_test_samples.h` (`WESAD_BENCHMARK_NUM_SAMPLES 2100`).

2. **`S2_Stress` References:**
   - **Status:** **Purged from all execution workflows.**
   - The only remaining mention of `S2_Stress` in `results/verification/hc1_hardware_hil/` is the historical contextual clarification in `firmware_replay_reference.md` explaining why prior workflows were incorrect.
   - No verification script, plan, or command accepts or references `S2_Stress`.

3. **Dry-Run Status Clarification:**
   - Both `hil_verification_plan.md` and `capture_script_review.md` now explicitly state:
     > *"A dry-run PASS is strictly a software and toolchain sanity check and does NOT constitute physical hardware validation or physical STM32 HC1 parity."*
   - `python/verify_hardware_hc1_capture.py` includes this disclaimer directly in its console output and generated JSON/TXT reports when executing against dry-run data.

---

## Question 3: Confirmation that Stress Reference Cannot Be Accidentally Used

The offline verification script `python/verify_hardware_hc1_capture.py` enforces three layers of defense against accidental use of noncanonical reference datasets:

1. **Fatal Schema Validation in `load_canonical_reference()`:**
   ```python
   ref_data = np.load(reference_path)
   if "raw_ecg_2100" not in ref_data or "runtime_filt_10k" not in ref_data:
       raise ValueError(
           f"Invalid reference file '{reference_path}': Canonical firmware replay reference must contain "
           f"'raw_ecg_2100' and 'runtime_filt_10k'. Legacy or noncanonical fallback references (such as "
           f"raw ecg_samples.npz or S2_Stress arrays) are strictly rejected."
       )
   ```
2. **Empirical Static Validation:**
   - When attempting to pass `demo/sample_data/ecg_samples.npz` (which contains `S2_Stress_raw` and `S2_Baseline_raw`):
     ```
     ValueError: Invalid reference file 'demo/sample_data/ecg_samples.npz': Canonical firmware replay reference
     must contain 'raw_ecg_2100' and 'runtime_filt_10k'. Legacy or noncanonical fallback references (such as
     raw ecg_samples.npz or S2_Stress arrays) are strictly rejected.
     ```
3. **Rigid Array Binding:**
   - Raw ECG is strictly bound to `raw_ecg_2100[i % 2100]` with SHA-256 `106fbd7d56a678c10aa60541b697326de3a761456dded54c3e1fa6443eb866db`.
   - Filtered ECG is strictly bound to `runtime_filt_10k` with SHA-256 `d4e252a8536377ace9140c303f0fee43339cc589ad1fbb271d70623fa65f32d8`.

---

## Question 4: Final Physical HIL Readiness Assessment

| Component | Status | Verification Summary |
|---|---|---|
| **Binary Integrity** | **READY** | `STM32G474_HC1_Telemetry.bin` (11,316 B) validated; byte-for-byte SHA-256 match with clean toolchain rebuild. |
| **Flash Command** | **READY** | ST-LINK CLI flashing command specified with `-c port=SWD -v -rst`. Output directed to `hardware_flash_log.txt`. |
| **Wire Capture Tool** | **READY** | `python/capture_hardware_telemetry.py` configured with `dtr=False`, `rts=False`, flags gating (`0x05`), CRC-16 check, sequence tracking, and sample rate classification. |
| **Parity Verifier Tool** | **READY** | `python/verify_hardware_hc1_capture.py` configured with canonical reference binding, modulo indexing, float32 tolerance ($\max |\text{err}| < 10^{-5}\text{ mV}$), R-peak alignment, and Shannon entropy. |
| **Reference Artifacts** | **READY** | `firmware_replay_reference.npz` validated with 10,000-sample runtime filter continuity. |
| **Physical Hardware** | **UNTOUCHED** | NUCLEO-G474RE has **NOT** been flashed; `COM10` has **NOT** been opened. |

### Final Readiness Verdict:
**THE SUITE IS FULLY CONSISTENT AND READY FOR PHYSICAL HARDWARE EXECUTION.**  
All automated checks, dry-run validations, and documentation audits are complete. Execution is paused on strict hold pending explicit user approval to flash the STM32 board and open `COM10`.
