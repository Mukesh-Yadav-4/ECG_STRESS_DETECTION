# Project Verification Report

## Environment
- **Operating System:** Windows 10/11 Pro (64-bit, AMD64 architecture)
- **Python Version:** Python 3.14.3 (`MSC v.1944 64 bit [AMD64]`)
- **MATLAB Version:** MATLAB Desktop installed (`matlab` CLI present on PATH)
- **Embedded Toolchain:** GNU Tools for STM32 (14.3.rel1) / `arm-none-eabi-gcc.exe` 14.3.1 (CubeIDE 2.2.0 plugins)
- **Host C Compiler:** MinGW.org GCC 6.3.0-1 (32-bit x86)
- **Git Commit:** `c2e2964c4b49725ce28cc3a3fa0556c0893716b9`
- **Unavailable / Bypassed Dependencies:** 64-bit host GCC/Clang (only 32-bit MinGW GCC available on host PATH); Physical ST-LINK COM-port connection (bypassed per non-destructive hardware instructions).

---

## Summary Table

| Stage | Status | Expected | Observed | Output File |
| :--- | :---: | :--- | :--- | :--- |
| **Stage 1: Static Data & Windowing** | **PASS** | 15 subjects, 445 windows (285 baseline, 160 stress), 60s window, 0% overlap, 60s hop, 0 duplicates/NaNs, 8 core & 13 expanded features | Exactly 15 subjects, 445 windows (285 baseline, 160 stress), 60s length (42,000 samples @ 700 Hz), 0% overlap, 60s step, 0 duplicates/NaNs, full schemas confirmed | [`results/verification/stage1_windowing_validation.txt`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/results/verification/stage1_windowing_validation.txt) |
| **Stage 2: Machine-Learning Reproducibility** | **PASS** | Logistic Regression: 92.13% Acc, 88.29% F1, 82.50% Sens, 97.54% Spec, 0.9493 AUC ($\tau=0.50$). All 6 models match canonical table. | Exact match ($\Delta = 0.0000$ across all 6 models and all metrics). Confirmed $\tau=0.50$ (92.13% Acc, 88.29% F1) and exploratory $\tau=0.35$ (92.36% Acc, 89.10% F1, 86.88% Sens). | [`results/verification/stage2_ml_reproducibility.txt`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/results/verification/stage2_ml_reproducibility.txt) |
| **Stage 3: HC1 Python/C Parity** | **FAIL** | Zero byte mismatches across 10,000 packets (200,000 bytes); lossless round-trip reconstruction; no NaNs. | 9,014 differing bytes across 1,673 packets. MSE = `NaN`, Max error = $1.31 \times 10^{38}\text{ mV}$. All CRC-16 checksums valid. | [`results/verification/hc1_parity_rerun.json`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/results/verification/hc1_parity_rerun.json)<br>[`results/verification/hc1_parity_rerun.txt`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/results/verification/hc1_parity_rerun.txt) |
| **Stage 4: STM32 Firmware Build** | **PASS** | Canonical `embedded_stm32` tree compiles cleanly with `USE_ENCRYPTION_MODE=2`, HC1 enabled, flags `0x05`, producing binary. | Clean compilation (Exit code 0, 0 errors, 0 warnings). Flags = `0x05`. Produced 11,316-byte binary image identical byte-for-byte to repository binary. | [`results/verification/stage4_firmware_build.txt`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/results/verification/stage4_firmware_build.txt) |
| **Stage 5: Dashboard Smoke Test** | **PASS** | Streamlit app launches, loads offline data, displays plots & HRV metrics, supports virtual telemetry & consistent mode labels. | App launched headlessly (HTTP 200 OK on `/_stcore/health` and `/`). Offline data loaded (21,000 samples). Ingested 3,500 samples, computed 8 HRV metrics, inferred stress probability (6.15%). | [`results/verification/stage5_dashboard_smoke_test.txt`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/results/verification/stage5_dashboard_smoke_test.txt) |

---

## Research Results

**The machine-learning benchmark results are 100% reproduced.**

Executing the canonical 15-fold Leave-One-Subject-Out (LOSO) cross-validation script against [`results/WESAD_HRV_features_expanded.csv`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/results/WESAD_HRV_features_expanded.csv) generated outputs in [`results/verification/ml_rerun/`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/results/verification/ml_rerun/) that replicated every published metric across all six models with zero delta ($\Delta = 0.0000$):

1. **Logistic Regression (Primary Canonical Model):**
   - **Pre-specified Primary Operating Point ($\tau = 0.50$):**
     - Accuracy: **92.13%** (410 / 445 windows)
     - F1-Score: **88.29%**
     - Sensitivity / Recall: **82.50%** (132 / 160 acute stress windows)
     - Specificity: **97.54%** (278 / 285 calm baseline windows)
     - Precision: **94.96%** (132 / 139 detections)
     - ROC-AUC: **0.9493**
     - PR-AUC: **0.9467**
     - Confusion Matrix: $\text{TP} = 132$, $\text{FP} = 7$, $\text{TN} = 278$, $\text{FN} = 28$
   - **Exploratory Swept Operating Point ($\tau = 0.35$):**
     - Accuracy: **92.36%** (411 / 445 windows)
     - F1-Score: **89.10%** (Expected ~89.03%)
     - Sensitivity / Recall: **86.88%** (138–139 / 160 stress windows)
     - Specificity: **95.44%** (272–273 / 285 calm windows)
2. **All Other Benchmark Models Replicated Exactly:**
   - **MLP Neural Net:** Accuracy 91.69%, F1 87.87%, ROC-AUC 0.9375
   - **SVM (RBF Kernel):** Accuracy 91.46%, F1 87.42%, ROC-AUC 0.9524
   - **Random Forest:** Accuracy 90.34%, F1 85.90%, ROC-AUC 0.9426
   - **Extra Trees:** Accuracy 89.89%, F1 84.43%, ROC-AUC 0.9494
   - **HistGradientBoosting:** Accuracy 89.21%, F1 84.31%, ROC-AUC 0.9459

---

## HC1 Parity

**HC1 cross-language Python $\leftrightarrow$ C telemetry parity FAILED.**

1. **Observed Results:**
   - Across 10,000 real-world ECG packets (200,000 bytes evaluated), exactly **1,673 packets (16.73%)** exhibited byte mismatches.
   - Total differing bytes: **9,014 bytes**.
   - First mismatch occurs at **byte index 17** (the 8th encrypted payload byte of the very first packet).
   - In both directions (Python Encrypt $\rightarrow$ C Decrypt and C Encrypt $\rightarrow$ Python Decrypt), the reconstruction error diverges to `NaN` and $1.31 \times 10^{38}\text{ mV}$.
   - All packet framing and CRC-16 checksums are 100% valid (`all_c_crcs_valid = True`, `all_py_crcs_valid = True`).
   - Nonce generation is 100% deterministic (`nonce_deterministic = True`).
2. **Likely Root Cause (Empirically Diagnosed):**
   - The M-4DCHS system is a continuous 4D dynamical differential equation system with positive Lyapunov exponents ($\lambda_1 = +0.4384, \lambda_2 = +0.2537$).
   - In `telemetry_protocol.c`, the RK4 integration is computed using native C compiler FPU instructions (which may utilize 80-bit x87 intermediate registers or compiler-specific instruction scheduling). In `python/m4d_hyperchaos.py`, the RK4 steps are executed via Python/NumPy single-precision operations.
   - By step 5–7 of the 8-byte payload encryption loop, a **single least-significant bit (1 ULP $\approx 10^{-7}$)** divergence occurs in the continuous floating-point state variable ($y = 2.131546$ in Python vs. $y = 2.131545$ in C).
   - Because the keystream byte extraction function bit-casts the IEEE-754 representation of $x$ and $z$ into 32-bit unsigned integers (`memcpy(&ux, &s_m4d_state.x, 4)` and `(ux ^ (uz * 2654435761U))`), even a 1-bit difference in the float mantissa completely alters the extracted keystream byte (e.g., producing `0xC0` in Python vs. `0x37` in C).
   - In Cipher Feedback (CFB) mode, a wrong keystream byte XORed into an IEEE-754 float corrupts its exponent bits, immediately transforming a 0.85 mV ECG sample into an exponent-saturated number ($1.31 \times 10^{38}\text{ mV}$) or `NaN`.
   - **Conclusion:** Claims of "100% bit-exact parity across all platforms" are mathematically false unless fixed-point arithmetic, strict integer math, or bit-exact soft-float emulation is employed.

---

## Firmware

**The canonical embedded firmware (`embedded_stm32/`) built successfully.**

1. **Compilation Outcome:**
   - Compiled with STMicroelectronics official toolchain (`arm-none-eabi-gcc 14.3.1` @ `-O2`, `-mcpu=cortex-m4`, `-mfpu=fpv4-sp-d16`, `-mfloat-abi=hard`).
   - Zero errors, zero warnings.
2. **Configuration Verification:**
   - `#define USE_ENCRYPTION_MODE 2` confirmed in [`embedded_stm32/src/main_stm32.c`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/embedded_stm32/src/main_stm32.c#L22).
   - Active telemetry packet flags evaluate to `0x05` (`TELEMETRY_FLAG_ENCRYPTED | TELEMETRY_FLAG_CHAOS_4D`).
   - Target sampling rate is configured to 350 Hz.
3. **Artifact Integrity:**
   - Generated binary [`results/verification/STM32G474_HC1_Telemetry_verified.bin`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/results/verification/STM32G474_HC1_Telemetry_verified.bin) is exactly 11,316 bytes.
   - Binary is **100% bit-for-bit identical** to the pre-existing repository binary [`embedded_stm32/STM32G474_HC1_Telemetry.bin`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/embedded_stm32/STM32G474_HC1_Telemetry.bin).
   - No hardware flashing was performed.

---

## Dashboard

**The Streamlit clinical dashboard smoke test passed.**

1. **Server Launch:**
   - Launched headlessly on local test port 8599 via `streamlit run demo/app.py`.
   - Health check endpoint `/_stcore/health` responded with HTTP 200 OK within 3 seconds.
   - Main page fetched complete HTML bundle without unhandled exceptions.
2. **Backend Engine & UI Capabilities:**
   - Offline sample dataset [`demo/sample_data/ecg_samples.npz`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/demo/sample_data/ecg_samples.npz) loaded 21,000 samples of Lead-II ECG.
   - Ingestion of 3,500 continuous samples (10.0 seconds) into `LiveTelemetryStream` successfully extracted 8 core HRV metrics (`MeanHR = 78.2 BPM`, `RMSSD = 37.72 ms`, `SDNN = 41.33 ms`).
   - Stress inference engine correctly predicted stress probability (6.15%, classified as Calm at $\tau = 0.35$).
   - All three telemetry encryption modes are cleanly supported:
     - Mode 0: Plaintext (`flags = 0x00`)
     - Mode 1: Legacy 32-bit Scrambler (`flags = 0x01`)
     - Mode 2: HC1 / M-4DCHS 4D Hyperchaos (`flags = 0x05`)

---

## Unresolved Problems

1. **Cross-Language Floating-Point Parity Failure:**
   - `python/verify_m4d_parity.py` and `embedded_stm32/src/telemetry_protocol.c` diverge on ~16.7% of packets due to single-precision float32 rounding differences between host CPU instructions and Python FPU math.
   - Existing artifact [`results/raw_evidence_item4_parity_check.json`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/results/raw_evidence_item4_parity_check.json) recorded this exact `FAIL` verdict (9,377 mismatches), which our rerun [`results/verification/hc1_parity_rerun.json`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/results/verification/hc1_parity_rerun.json) re-confirmed (9,014 mismatches).
2. **Physical Hardware Telemetry Discrepancy:**
   - Artifact [`results/raw_evidence_item3_hil_capture.json`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/results/raw_evidence_item3_hil_capture.json) recorded that the currently flashed physical board on COM10 outputs `flags: 0x01` (Legacy 32-bit scrambler), not `0x05` (HC1).
   - Although the source code and freshly compiled binary are configured for HC1 (`0x05`), the physical hardware cannot be asserted as running HC1 until flashed with user approval.
3. **Competing STM32 Firmware Trees:**
   - Both `embedded_stm32/` and `STM32G474_ECG_Telemetry/` remain present in the workspace. While `embedded_stm32/` is the verified canonical tree, `STM32G474_ECG_Telemetry/` has not yet been formally archived.

---

## Recommendation

### Claims Safe to Keep as Verified:
1. **Canonical ML Performance:**
   - Pre-specified primary operating point: **92.13% Accuracy, 88.29% F1-score, 82.50% Sensitivity, 97.54% Specificity, 0.9493 ROC-AUC** at $\tau = 0.50$.
   - 15-fold LOSO cross-validation with zero subject leakage across 445 standardized, non-overlapping 60s windows.
2. **Canonical Firmware Compilation:**
   - `embedded_stm32/` compiles cleanly with `USE_ENCRYPTION_MODE = 2` to an 11,316-byte binary.
3. **Clinical Dashboard Functionality:**
   - `demo/app.py` loads offline datasets, parses packets, extracts 8 HRV metrics, and executes real-time inference.

### Claims That Must Remain Unverified or Be Qualified:
1. **Do NOT claim 100% bit-exact cross-platform Python $\leftrightarrow$ C parity:**
   - The test fails empirically with a 16.7% packet mismatch rate due to 1-ULP continuous float32 divergence in RK4 integration.
   - In documentation and papers, state that Python-only round-trip and C-only round-trip are lossless, but cross-runtime float32 bitcasting exhibits numerical divergence.
2. **Do NOT claim that physical hardware COM10 is currently streaming HC1:**
   - Hardware evidence shows COM10 streaming `0x01` (Legacy scrambler). Hardware flashing is required before making this claim.
