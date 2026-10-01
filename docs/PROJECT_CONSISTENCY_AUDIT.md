# ECG Stress Detection — Project Consistency Audit

## 1. Executive Summary

This consistency audit provides an evidence-based assessment of the **ECG Stress Detection** project, evaluating source code, hardware firmware, machine learning pipelines, and documentation. The project addresses automated detection of acute psychological stress from single-lead electrocardiography (Lead-II ECG) using the public **WESAD** dataset ($N=15$). Its core scientific innovation is **Subject-Specific Relative Baseline Calibration** ($X^* = (X - B_s) / (|B_s| + \epsilon)$) evaluated under **15-Fold Leave-One-Subject-Out Cross-Validation (LOSO-CV)**, which resolves inter-individual resting autonomic heterogeneity and elevates classification accuracy from 81.57% to 92.13% (+10.56% at primary $\tau=0.50$, F1: 73.03% $\rightarrow$ 88.29%); exploratory $\tau = 0.35$ reaches 92.36% accuracy (Python canonical: 89.10% F1; MATLAB historical: 89.03% F1).

The engineering pipeline couples this physiological model with a bare-metal ARM Cortex-M4 microcontroller deployment (**STM32G474RE**) featuring an on-chip **5-stage Direct Form I Biquad IIR filter** ($1.87\ \mu\text{s}$ latency at 170 MHz) and lightweight telemetry obfuscation via a **4-Dimensional Coupled Hyperchaotic System (HC1 M-4DCHS)** streaming 20-byte binary packets over UART at 115,200 baud.

**Key Findings:** While the core scientific data pipeline (445 non-overlapping 60s windows) and primary ML benchmark are mathematically sound and reproducible, significant inconsistencies exist across documentation, firmware versions, and archived evidence:
1. **Window Segmentation Contradiction:** Secondary execution guides claim 50% overlap (30s hop), whereas the actual codebase, dataset, and paper strictly implement 0% overlap (non-overlapping 60s windows).
2. **Divergent Firmware Trees:** Two separate STM32 projects exist: `embedded_stm32/` (170 MHz PLL, TIM2, HC1 M-4DCHS mode, flag `0x05`) versus `STM32G474_ECG_Telemetry/` (16 MHz HSI, SysTick, legacy 32-bit scrambler, flag `0x01`). The systematic guide refers to an obsolete external path and describes the 16 MHz tree.
3. **Stale Parity Failure Artifact:** `results/raw_evidence_item4_parity_check.json` records a `FAIL` verdict with 9,377 byte mismatches; HC1 Python/C parity is currently failed and unverified; the latest test produced cross-language mismatches and NaN reconstruction values.
4. **Physical HIL Verification Discrepancy:** The 15,505-packet endurance test on COM10 was captured while running the legacy 32-bit scrambler (`flags = 0x01`), conflicting with the paper's claim that 5,000 packets were verified with active HC1 hyperchaos (`flags = 0x05`).
5. **Numerical Statistic Discrepancy:** `README.md` reports $\chi^2 = 202.07$ ($p = 0.9938$), whereas raw evidence and the manuscript report $\chi^2 = 302.03$ ($p = 0.0230$).

A prioritized cleanup plan is established to synchronize documentation, deprecate the legacy firmware tree, re-verify parity evidence, and clarify threshold reporting.

---

## 2. Project Architecture

The repository is organized into seven functional components:

| Component | Directory | Description & Key Files |
| :--- | :--- | :--- |
| **MATLAB Suite** | `matlab/` | Multi-stage signal processing pipeline: `01_data_inspection/` (raw data ingestion), `02_preprocessing/` (`TEN_process_all_subjects.m` 60s segmentation & filtering), `03_hrv_extraction/` (Pan-Tompkins R-peak detection & time-domain HRV), `04_analysis/` (statistical hypothesis testing), `05_modeling/` (`TWENTY_TWO_calibrated_stress_detection.m` 15-fold LOSO Logistic Regression), `06_final_results/` (metrics exports), and `DEMO_stress_detection.m` (interactive GUI visualizer). |
| **Python Suite** | `python/` | Machine learning benchmark and host communications: `train_loso_ml_benchmark.py` (canonical 15-fold LOSO benchmark for 6 classifiers), `explainability_feature_importance.py` (30-repeat permutation importance & odds ratios), `m4d_hyperchaos.py` (HC1 dynamical system & RK4 solver), `verify_m4d_parity.py` (cryptographic parity & entropy suite), `compute_lyapunov_spectrum.py` (Lyapunov exponents & Kaplan-Yorke dimension), `stm32_telemetry_receiver.py` (serial packet parser, descrambler & live inference), and `simulate_stm32_stream.py` (virtual telemetry streamer). |
| **Streamlit Web UI** | `demo/` | Web dashboard (`app.py`) providing: (1) IoMT Hardware Telemetry (virtual replay or physical COM10 streaming with dual authorized decrypted vs eavesdropper intercept views and a WebGL 3D phase-space attractor), (2) Interactive Waveform & Calibration Engine, (3) HRV Biomarkers & Baseline Formula, and (4) Multi-Model Benchmark & Threshold Sweep. |
| **STM32 Firmware** | `embedded_stm32/` & `STM32G474_ECG_Telemetry/` | Bare-metal C firmware for NUCLEO-G474RE. `embedded_stm32/` is the active production tree containing `main_stm32.c`, `ecg_dsp_filter.c` (5-stage Direct Form I Biquad IIR), `telemetry_protocol.c` (HC1 M-4DCHS cipher), standalone `Makefile`, and `build_and_flash.bat`. |
| **Dataset Storage** | `data/` | `data/raw/WESAD/` contains raw multimodal recordings for 15 subjects (`S2`–`S17`, excluding `S12`). `data/processed/` contains 15 standardized MAT files (`S*_ECG_labels.mat`). |
| **Results & Audits** | `results/` | Canonical tabular data (`WESAD_HRV_features_expanded.csv`, `ML_Model_Benchmark_LOSO.csv`, `FINAL_Model_Metrics.csv`), high-res figures (`results/figures/`), and raw execution audit artifacts (`raw_evidence_item1` to `item5`, `independent_reproducibility_audit.json`). |
| **Manuscript** | `paper/` | LaTeX source (`main.tex`, `references.bib`), publication figures, and compiled IEEE preprint PDF (`Personalized_ECG_HRV_Stress_Detection_LOSO_STM32_4D_Hyperchaotic_Telemetry_v3.pdf`). |

---

## 3. Canonical Data and ML Pipeline

### 3.1 Dataset & Segmentation Specifications
* **Cohort:** Exactly 15 healthy adult subjects ($S2$ through $S17$, excluding non-existent $S12$).
* **Input Signal:** Single-lead chest ECG (modified Lead-II orientation) acquired via RespiBAN chest strap at $700\text{ Hz}$ (downsampled to $350\text{ Hz}$ for microcontroller deployment).
* **Window Duration & Overlap:** Exactly **60.0 seconds**, strictly **non-overlapping (0% overlap, 60.0s hop)**.
* **Window Counts:** Exactly **445 complete analysis windows**:
  * **Baseline (Label 1):** 285 windows (exactly 19 windows per subject across all 15 subjects).
  * **Acute Stress / TSST (Label 2):** 160 windows (range: 10 to 12 windows per subject).
  * *Amusement (Label 3) & Meditation (Label 4):* Excluded from binary stress classification.

### 3.2 Extracted Feature Representation
From clean NN intervals, 13 time-domain and statistical biomarkers are extracted (`results/WESAD_HRV_features_expanded.csv`):
* **Primary 8-Feature Modeling Subset:** `MeanHR`, `MeanRR`, `SDNN`, `RMSSD`, `pNN50`, `RR_CV`, `RR_IQR`, `HR_IQR`.
* **Ablation-Only Features (5):** `MedianHR`, `StdHR`, `MinHR`, `MaxHR`, `MedianRR`.

### 3.3 Subject-Specific Baseline Normalization
Every feature $X$ is centered around the subject's resting baseline centroid $B_s$:
$$X^* = \frac{X - B_s}{|B_s| + \epsilon}, \quad \text{with } \epsilon = 10^{-6}$$
* **Centroid $B_s$:** Computed strictly from the 19 resting baseline windows of subject $s$.
* **Leakage Safeguard:** Zero test stress windows are exposed during centroid calculation.

### 3.4 Canonical Machine Learning Validation Protocol
* **Canonical Machine-Learning Source of Truth:**
  - Script: [`python/train_loso_ml_benchmark.py`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/python/train_loso_ml_benchmark.py)
  - Benchmark Table: [`results/ML_Model_Benchmark_LOSO.csv`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/results/ML_Model_Benchmark_LOSO.csv)
  - Out-of-Fold Predictions: [`results/ML_Predictions_LOSO.csv`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/results/ML_Predictions_LOSO.csv)
* **Secondary/Historical Classifier (MATLAB):** Secondary/historical classifier implementation using custom unregularized gradient descent. Its τ=0.35 metrics differ slightly from the Python implementation because the optimization and regularization methods differ.
* **Live Dashboard Inference Engine (`demo/app.py` / `stm32_telemetry_receiver.py`):** Pooled deployment inference engine with threshold τ=0.35, streaming safety floors, feature clipping, and optional subject-specific baseline calibration. It is not the same as the 15-fold LOSO evaluation model.
* **Validation Strategy:** Strict **15-Fold Leave-One-Subject-Out Cross-Validation (LOSO-CV)**.
* **Leakage Safeguard:** `StandardScaler` is fitted strictly on the 14 training subjects per fold and applied out-of-fold to the held-out subject.
* **Classifier Configuration:** Logistic Regression with $L2$ regularization ($C = 1.0$, `liblinear` solver, `max_iter=1000`).

### 3.5 Operating Thresholds & Reported Performance
* **Pre-specified Default Operating Point ($\tau = 0.50$):** Unbiased, out-of-fold primary benchmark:
  * Accuracy: **92.13%** (410 / 445 windows)
  * Stress F1-Score: **88.29%**
  * Sensitivity (Recall): **82.50%** (132 / 160 stress windows)
  * Specificity: **97.54%** (278 / 285 calm windows)
  * Precision: **94.96%** (132 / 139)
  * Balanced Accuracy: **90.02%**
  * ROC-AUC: **0.9493** | PR-AUC: **0.9467**
  * Confusion Matrix $[TN, FP, FN, TP]$: $[278, 7, 28, 132]$
* **Exploratory Sensitivity-Prioritized Operating Point ($\tau = 0.35$):** Post-hoc sweep across pooled predictions:
  * **Python canonical pipeline:**
    * Accuracy: **92.36%** (411 / 445 windows)
    * Stress F1-Score: **89.10%**
    * Sensitivity (Recall): **86.88%** (139 / 160 stress windows, +7 stress windows caught)
    * Specificity: **95.44%** (272 / 285 calm windows)
    * Precision: **91.45%** (139 / 152)
    * Confusion Matrix $[TN, FP, FN, TP]$: $[272, 13, 21, 139]$
  * **MATLAB historical pipeline:**
    * Accuracy: **92.36%** (411 / 445 windows)
    * Stress F1-Score: **89.03%**
    * Sensitivity (Recall): **86.25%** (138 / 160 stress windows, +6 stress windows caught)
    * Specificity: **95.79%** (273 / 285 calm windows, -5 baseline windows lost)
    * Precision: **92.00%** (138 / 150)
    * Confusion Matrix $[TN, FP, FN, TP]$: $[273, 12, 22, 138]$

---

## 4. Telemetry and Encryption Audit

### 4.1 Binary Packet Framing (20 Bytes)
```
[0xAA 0x55] [Ver: 0x01] [Flags: 1B] [Seq: 2B] [Timestamp: 4B] [Raw ECG: 4B] [Filt ECG: 4B] [CRC16: 2B]
```
* **Bytes 0–1:** Frame synchronization header (`0xAA`, `0x55`).
* **Byte 2:** Protocol version (`0x01`).
* **Byte 3:** Status flags: Bit 0 = Encrypted (`0x01`), Bit 1 = Live ADC (`0x02`), Bit 2 = 4D Chaos (`0x04`).
* **Bytes 4–5:** `uint16_t` sequence ID (little-endian, loss tracking).
* **Bytes 6–9:** `uint32_t` millisecond hardware timestamp.
* **Bytes 10–13 & 14–17:** `float32_t` raw and filtered ECG voltages (scrambled/encrypted in-place).
* **Bytes 18–19:** `uint16_t` CRC-16-CCITT computed over bytes 2 through 17 (polynomial `0x1021`, initial value `0xFFFF`).

### 4.2 Stream Obfuscation Modes
1. **Mode 1 — 32-Bit Discrete Stream Scrambler:**
   * Algorithm: Marsaglia Xorshift32 combined with additive Golden Ratio Weyl sequence (`+0x61C88647`) and Cipher Block Chaining (CBC) diffusion:
     $$C_i = P_i \oplus (S_n \ \&\ 0\text{xFF}) \oplus C_{i-1}$$
   * Per-Packet Nonce: $S_0 = \text{KEY} \oplus (\text{seq\_id} \cdot 0\text{x}45D9F3B) \oplus \text{timestamp\_ms}$.
   * Execution Cost: $\approx 32$ CPU clock cycles ($\approx 2.0\ \mu\text{s}$ at 16 MHz).
   * Status: **Functionally verified on physical hardware** across 15,505 packets (`raw_evidence_item3`).
   * Security Level: **Not cryptographically secure.** Wire entropy $H \approx 7.25 - 7.62\text{ bits/byte}$. Fails $\chi^2$ uniformity ($\chi^2 = 1,281.8$). Serves strictly as a visual line scrambler.
2. **Mode 2 — 4D Coupled Hyperchaotic System (HC1 M-4DCHS):**
   * Continuous Formulation:
     $$\dot{x} = a(y-x) + w, \quad \dot{y} = cx - xz + dy, \quad \dot{z} = xy - bz, \quad \dot{w} = -rx$$
   * Parameters: $a = 15.81, b = 2.76, c = 86.03, d = -9.07, r = 10.79$, integration step $dt = 0.0025\text{ s}$ via single-precision RK4.
   * Dynamical Spectrum: Verified in `results/hc1_reproducibility_benchmark.json`: $\lambda_1 \approx +0.438, \lambda_2 \approx +0.254, \lambda_3 \approx -0.0005, \lambda_4 \approx -28.332$, $\sum \lambda_i = -27.640$ (identically matches divergence $\nabla \cdot \mathbf{F} = -27.64$), $D_{KY} \approx 3.024$.
   * Keystream Generation: Nonlinear hash on state variables $x$ and $z$ with multiplier `0x9E3779B1` (2654435761).
   * Hardware Cost: Measured via `DWT->CYCCNT` on STM32G474RE @ 170 MHz (`raw_evidence_item2`): mean $177$ cycles ($1.04\ \mu\text{s}$) per RK4 step, mean $224$ cycles ($1.32\ \mu\text{s}$) per keystream byte.
   * Statistical Properties: Wire entropy $H = 7.9973\text{ bits/byte}$, $\chi^2 = 302.03, p = 0.0230, \text{df}=255$ (no rejection of uniformity at $\alpha = 0.01$).
   * Security Level: **Not accredited cryptographic security.** Demonstrates operational wiretap obfuscation and mathematical recovery under real hardware timing constraints; does not claim resistance against algebraic cryptanalysis, chosen-ciphertext, or side-channel attacks.

### 4.3 Terminology Variations in Codebase
* `HC1 M-4DCHS`: Canonical title used in paper and README.
* `M-4DJHS` / `4D Memristive Hyperchaos`: Legacy name used in firmware comments (`main_stm32.c`, `telemetry_protocol.h`).
* `M4DJerkHyperchaos`: Python class name in `m4d_hyperchaos.py`.

---

## 5. Duplicate and Conflicting Implementations

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 DUAL FIRMWARE CODE TREES                                     │
├──────────────────────────────────────────────────────────────┬───────────────────────────────┤
│ Active Production Tree: embedded_stm32/                      │ Legacy Eclipse Tree:          │
│ • Path: embedded_stm32/src/main_stm32.c                      │   STM32G474_ECG_Telemetry/   │
│ • Toolchain: Standalone GCC (Makefile / CMakeLists.txt)      │ • Path: STM32G474_.../Src/    │
│ • Clock: 170 MHz PLL SYSCLK                                  │ • Toolchain: STM32CubeIDE     │
│ • Timer: TIM2 Periodic Interrupt @ 350 Hz                    │ • Clock: 16 MHz HSI           │
│ • Security Macro: USE_ENCRYPTION_MODE = 2 (HC1 M-4DCHS)      │ • Timer: SysTick Register @   │
│ • Active Flags: 0x05 (TELEMETRY_FLAG_ENCRYPTED | CHAOS_4D)   │   350 Hz                      │
│ • Binary: STM32G474_HC1_Telemetry.bin                        │ • Security Macro:             │
│ • Status: Matches Paper, README, and flash_firmware.bat      │   USE_CHAOTIC_ENCRYPTION = 1  │
│                                                              │ • Active Flags: 0x01          │
│                                                              │ • Binary: STM32G474_...bin    │
│                                                              │ • Status: Stale, supersceded  │
└──────────────────────────────────────────────────────────────┴───────────────────────────────┘
```

### 5.1 Analysis of Firmware Conflicts
1. **Clock Rates:** `embedded_stm32/src/main_stm32.c` configures `SystemClock_Config()` to **170 MHz PLL**, while `STM32G474_ECG_Telemetry/Src/main.c` relies on default **16 MHz HSI**.
2. **Interrupt Source:** `embedded_stm32` uses **TIM2**, while `STM32G474_ECG_Telemetry` writes directly to **ARM SysTick registers** (`SYSTICK_LOAD = 45713`).
3. **Active Encryption Mode:** `embedded_stm32` sets `USE_ENCRYPTION_MODE 2` (HC1 M-4DCHS, flag `0x05`), while `STM32G474_ECG_Telemetry` sets `USE_CHAOTIC_ENCRYPTION 1` (legacy 32-bit scrambler, flag `0x01`).
4. **Invalid Path in Documentation:** `PROJECT_IMPLEMENTATION_SYSTEMATIC_GUIDE.md` directs the user to open `C:\Users\YASH\Desktop\projects\STM32_PROJECTS\STM32G474_ECG_Telemetry/`, an external path that does not exist in this environment.

### 5.2 Conflicting Dashboard Inference vs. Offline Protocol
* **Offline Scientific Protocol:** Evaluated strictly under 15-fold LOSO-CV. For held-out subject $k$, training is conducted strictly on the remaining 14 subjects. Normalization is strictly $\Delta X = (X - B_s) / (|B_s| + \epsilon)$ without clamping.
* **Live Streaming Inference (Tab 1):** In `stm32_telemetry_receiver.py`, `_fit_from_csv()` fits a single Logistic Regression on ALL 15 subjects pooled together (no out-of-fold separation). Furthermore, `predict()` applies artificial physiological floors (`floors = {"MeanHR": 30.0, ...}`) and hard clamping (`np.clip(..., -5.0, 5.0)`).
* **Static Waveform Demo (Tab 2):** Does not run inference; loads precomputed offline mean stress probabilities from `samples_meta.json` (derived from `Stress_Classifier_Predictions.csv`).

### 5.3 Conflicting Parity Results
* `results/raw_evidence_item4_parity_check.json` records a **FAIL** on 10,000 packets with 9,377 byte mismatches and NaN error.
* `README.md` and `paper/main.tex` claim **100% bit-exact parity** (0 mismatches across 100 test nonces).
* *Root Cause:* A prior commit attempted to address float32 synchronization, but the latest independent parity rerun still fails.

---

## 6. Documentation and Evidence Conflicts

| Issue ID | Severity | File Paths & Locations | Current Conflicting Claims | Recommended Canonical Value | Evidence & Ground Truth | Classification |
| :---: | :---: | :--- | :--- | :--- | :--- | :---: |
| **DOC-01** | **Critical** | [`EXECUTION_GUIDE.md#L22,L117`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/EXECUTION_GUIDE.md#L22), [`PROJECT_IMPLEMENTATION_SYSTEMATIC_GUIDE.md#L87`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/PROJECT_IMPLEMENTATION_SYSTEMATIC_GUIDE.md#L87) vs [`TEN_process_all_subjects.m#L188-L204`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/matlab/02_preprocessing/TEN_process_all_subjects.m#L188-L204), [`README.md#L75`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/README.md#L75) | Guides claim 60s windows with **50% overlap (30s hop)**. Code and paper state **0% overlap (non-overlapping 60s windows)**. | **0% Overlap (non-overlapping 60s windows)** | Loop in `TEN_process_all_subjects.m` steps by `samples_per_window` (60s). Total windows = 445 ($15 \times 19 = 285$ baseline + 160 stress). If 50% overlap were used, window count would be $\approx 890$. | **Verified** |
| **DOC-02** | **Critical** | [`PROJECT_IMPLEMENTATION_SYSTEMATIC_GUIDE.md#L4,L196-L205`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/PROJECT_IMPLEMENTATION_SYSTEMATIC_GUIDE.md#L4) vs [`embedded_stm32/src/main_stm32.c#L21-L22`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/embedded_stm32/src/main_stm32.c#L21-L22), [`README.md#L5,L79`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/README.md#L5) | Guide states MCU runs on **16 MHz HSI** using **32-bit scrambler** (`USE_CHAOTIC_ENCRYPTION 1`) at invalid path `C:\...\STM32_PROJECTS\...`. Code and README state **170 MHz PLL**, **HC1 M-4DCHS** (`USE_ENCRYPTION_MODE 2`) in `embedded_stm32/`. | **`embedded_stm32/` @ 170 MHz PLL, HC1 M-4DCHS (`USE_ENCRYPTION_MODE 2`)** | `embedded_stm32/STM32G474_HC1_Telemetry.bin` is the production binary flashed by root `flash_firmware.bat` and verified in `raw_evidence_item1`. | **Contradictory** |
| **DOC-03** | **High** | [`results/raw_evidence_item4_parity_check.json#L4-L8`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/results/raw_evidence_item4_parity_check.json#L4-L8) vs [`README.md#L80,L320`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/README.md#L80), [`paper/main.tex#L430`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/paper/main.tex#L430) | Raw evidence artifact records `"verdict": "FAIL"` with 9,377 byte mismatches. Paper and README claim 100% bit-exact parity across 100 nonces. | **HC1 Python/C parity is currently failed and unverified; the latest test produced cross-language mismatches and NaN reconstruction values.** | A prior commit attempted to address float32 synchronization, but the latest independent parity rerun still fails. | **Contradictory** |
| **DOC-04** | **High** | [`results/raw_evidence_item3_hil_capture.txt#L6-L21`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/results/raw_evidence_item3_hil_capture.txt#L6-L21) vs [`README.md#L81,L350-L364`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/README.md#L81), [`paper/main.tex#L494-L525`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/paper/main.tex#L494) | `raw_evidence_item3` records 15,505 packets on COM10 running legacy scrambler (`flags = 0x01`, `is_hc1_enabled: False`). Paper and README claim 5,000 physical packets with active HC1 (`flags = 0x05`). | **Archive both runs: document 15,505 packets as legacy physical link test and 5,000 packets as HC1 physical test.** | `raw_evidence_item1` confirmed HC1 streaming `0x05` on COM10 for 100 packets; a dedicated 5,000-packet HC1 raw JSON needs to be retained. | **Contradictory** |
| **DOC-05** | **High** | [`README.md#L323-L324`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/README.md#L323-L324) vs [`results/raw_evidence_item5_chi2_uniformity.txt#L10`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/results/raw_evidence_item5_chi2_uniformity.txt#L10), [`paper/main.tex#L453`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/paper/main.tex#L453) | `README.md` reports $\chi^2 = 202.07$ ($p = 0.9938$) and $H = 7.9982$. Raw evidence and paper report $\chi^2 = 302.03$ ($p = 0.0230$) and $H = 7.9973$. | **$\chi^2 = 302.03, p = 0.0230, \text{df}=255, H = 7.9973\text{ bits/byte}$** | Measured directly by `scipy.stats.chisquare` in `raw_evidence_item5_chi2_uniformity.json` across 80,000 bytes. Synchronized in `paper/main.tex`. | **Verified** |
| **DOC-06** | **Medium** | [`README.md#L14`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/README.md#L14) vs [`paper/`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/paper/) directory | `README.md` badge links to `paper/..._Edge_IoMT.pdf` (without version suffix). Only `_v2.pdf` and `_v3.pdf` exist on disk, causing a broken 404 link. | **Link to `paper/Personalized_ECG_HRV_Stress_Detection_LOSO_STM32_4D_Hyperchaotic_Telemetry_v3.pdf`** | File existence check on local disk. | **Verified** |
| **DOC-07** | **Medium** | [`PROJECT_IMPLEMENTATION_SYSTEMATIC_GUIDE.md#L175-L187`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/PROJECT_IMPLEMENTATION_SYSTEMATIC_GUIDE.md#L175-L187) vs [`README.md#L78,L180`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/README.md#L78), [`paper/main.tex#L33,L175`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/paper/main.tex#L33) | Guide presents $\tau = 0.35$ as the headline primary model. Paper and README strictly present $\tau = 0.50$ as pre-specified primary, and $\tau = 0.35$ as exploratory. | **$\tau = 0.50$ (Pre-specified Primary) / $\tau = 0.35$ (Exploratory Tuned)** | Academic peer-review integrity requires post-hoc swept thresholds to be distinguished from unbiased out-of-fold defaults. | **Verified** |
| **DOC-08** | **Medium** | [`README.md#L80,L287`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/README.md#L80), [`demo/app.py#L436-L450`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/demo/app.py#L436-L450) vs [`paper/main.tex#L536`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/paper/main.tex#L536), [`PROJECT_IMPLEMENTATION_SYSTEMATIC_GUIDE.md#L263`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/PROJECT_IMPLEMENTATION_SYSTEMATIC_GUIDE.md#L263) | Marketing copy in README and dashboard uses "Encryption" and "Cryptographically Locked" without immediate caveat. Paper explicitly disclaims cryptographic security. | **"Lightweight IoMT Telemetry Obfuscation / Stream Scrambler"** with consistent disclaimer. | The algorithms are custom PRNGs/continuous dynamical flows, not NIST-certified ciphers (AES/ChaCha20). | **Verified** |
| **DOC-09** | **Medium** | [`python/stm32_telemetry_receiver.py#L311-L389`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/python/stm32_telemetry_receiver.py#L311-L389) vs [`python/train_loso_ml_benchmark.py#L82-L115`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/python/train_loso_ml_benchmark.py#L82-L115) | Live receiver trains a single model on all 15 subjects pooled with clamping (`floors`, `np.clip(-5,5)`). Research suite evaluates out-of-fold without clamping. | **Document deployed edge model behavior vs out-of-fold research evaluation in guides.** | Source code inspection of `stm32_telemetry_receiver.py`. | **Verified** |
| **DOC-10** | **Low** | [`ECG_STRESS_DETECTION_RUN.txt#L25-L27,L83`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/ECG_STRESS_DETECTION_RUN.txt#L25-L27) | Line 25 is blank; line 27 has an orphaned comment missing `python/plot_ml_evaluation.py`. Line 83 cites non-existent `results/feature_importance_ranking.csv`. | **Fix command and correct path to `results/ML_Feature_Importance_Permutation.csv`.** | Inspection of text file and `results/` folder contents. | **Verified** |

---

## 7. Top Ten Problems

1. **Window Segmentation Contradiction (50% Overlap vs. 0% Overlap):** `EXECUTION_GUIDE.md` and `PROJECT_IMPLEMENTATION_SYSTEMATIC_GUIDE.md` claim 50% overlap, directly contradicting the MATLAB processing code (`TEN_process_all_subjects.m`), the 445-row dataset, the audit report, and the paper.
2. **Divergent Firmware Trees & Invalid External Path:** `embedded_stm32/` (170 MHz PLL, HC1 M-4DCHS `0x05`) coexists with `STM32G474_ECG_Telemetry/` (16 MHz HSI, legacy scrambler `0x01`). The systematic guide directs users to an external non-existent path.
3. **Stale Parity Failure Artifact in `results/`:** `raw_evidence_item4_parity_check.json` contains a `FAIL` verdict with 9,377 mismatches; HC1 Python/C parity is currently failed and unverified; the latest test produced cross-language mismatches and NaN reconstruction values.
4. **Physical HIL Verification Discrepancy:** `raw_evidence_item3_hil_capture.txt` documents a 15,505-packet run that ran with legacy scrambler flags (`0x01`), leaving the paper's claim of 5,000 HC1 physical packets without an isolated matching raw evidence file.
5. **Numerical Discrepancy in Chi-Square ($\chi^2$) and Entropy:** `README.md` reports $\chi^2 = 202.07$ and $H = 7.9982$, whereas raw evidence artifact 5 and `paper/main.tex` report $\chi^2 = 302.03$ and $H = 7.9973$.
6. **Live Inference Discrepancy vs. LOSO Benchmark:** `stm32_telemetry_receiver.py` fits a pooled global model with heuristic floors and clipping, differing from the unclipped out-of-fold LOSO models reported in the scientific paper.
7. **Threshold Hierarchy Inconsistency ($\tau = 0.50$ vs. $\tau = 0.35$):** `PROJECT_IMPLEMENTATION_SYSTEMATIC_GUIDE.md` headlines $\tau = 0.35$ without clearly distinguishing it from the unbiased out-of-fold default of $\tau = 0.50$.
8. **Broken Paper PDF Download Badge:** `README.md` line 14 links to a non-existent filename, generating a 404 error when clicking the PDF download badge.
9. **Duplicate Dataset CSVs in `demo/sample_data/`:** `demo/sample_data/` contains duplicate 106 KB CSV files identical to those in `results/`, creating multiple sources of truth.
10. **Terminology Ambiguity (Encryption vs. Obfuscation):** Inconsistent usage of "Encryption" versus "Obfuscation" across README, UI, and documentation without immediate disclaimer.

---

## 8. Recommended Canonical Decisions

| Decision Topic | Recommended Canonical Value | Status / Approval Requirement |
| :--- | :--- | :---: |
| **Canonical Firmware Tree** | **`embedded_stm32/`** (deprecate `STM32G474_ECG_Telemetry/`) | **Requires Human Approval** |
| **Microcontroller Clock** | **170 MHz PLL SYSCLK** | Canonical (Matches paper & production binary) |
| **Sampling & Telemetry Rate** | **350 Hz** ($T_s = 2.857\text{ ms}$, downsampled from 700 Hz raw) | Canonical |
| **Binary Packet Format** | **20-Byte Frame** (`[0xAA 0x55] [0x01] [Flags] [Seq:2B] [TS:4B] [Raw:4B] [Filt:4B] [CRC16:2B]`) | Canonical |
| **Active Encryption Mode** | **Mode 2: HC1 M-4DCHS** (`USE_ENCRYPTION_MODE 2`, flags = `0x05`) | Canonical (Matches paper & production binary) |
| **Canonical Obfuscation Name** | **4-Dimensional Coupled Hyperchaotic System (HC1 M-4DCHS)** | Canonical |
| **Primary Scientific Threshold** | **$\tau = 0.50$** (Pre-specified Primary) / **$\tau = 0.35$** (Exploratory Tuned) | Canonical |
| **Primary Scientific Metric** | **92.13% Accuracy, 88.29% F1 at $\tau = 0.50$**; 13-feat ablation gain **+10.79% Acc, +15.64% F1** | Canonical |
| **Canonical ML Source of Truth** | **Python (`python/train_loso_ml_benchmark.py`)**; `results/ML_Model_Benchmark_LOSO.csv`, `results/ML_Predictions_LOSO.csv` | Canonical (MATLAB documented as secondary/historical) |
| **Dashboard Operating Mode** | **Pooled deployment inference engine with threshold τ=0.35, streaming safety floors, feature clipping, and optional subject-specific baseline calibration. It is not the same as the 15-fold LOSO evaluation model.** | Canonical Architecture |

---

## 9. Cleanup Plan

### Phase 1: Documentation Corrections (Pure Text, Zero Regression Risk)
* **Objective:** Correct "50% overlap" to "0% overlap (non-overlapping 60s windows)" in all markdown and text guides.
* **Files Allowed to Change:** `EXECUTION_GUIDE.md`, `PROJECT_IMPLEMENTATION_SYSTEMATIC_GUIDE.md`, `PROJECT_QUICK_REFERENCE.md`.
* **Files That Must Not Change:** All MATLAB scripts, Python scripts, datasets, and results CSVs.
* **Tests Required:** Verify that documented window count (445) matches $285 + 160 = 445$.
* **Expected Result:** Complete consistency between documented windowing and ground-truth code.

### Phase 2: Firmware Documentation & Path Harmonization
* **Objective:** Update `PROJECT_IMPLEMENTATION_SYSTEMATIC_GUIDE.md` and `HOW_TO_RESTORE_ECG_PROJECT.txt` to point to `embedded_stm32/` @ 170 MHz PLL and remove references to the invalid `STM32_PROJECTS` path.
* **Files Allowed to Change:** `PROJECT_IMPLEMENTATION_SYSTEMATIC_GUIDE.md`, `HOW_TO_RESTORE_ECG_PROJECT.txt`.
* **Files That Must Not Change:** Source code in `embedded_stm32/` or `STM32G474_ECG_Telemetry/`.
* **Tests Required:** Verify that all referenced file paths exist within the repository root.
* **Expected Result:** A developer can build and flash firmware using the documented commands without path errors.

### Phase 3: README Numerical & Link Synchronization
* **Objective:** Synchronize $\chi^2 = 302.03$ ($p = 0.0230$) and $H = 7.9973\text{ bits/byte}$ in `README.md` Section 8.2; update research paper PDF link to `_v3.pdf`.
* **Files Allowed to Change:** `README.md`.
* **Files That Must Not Change:** `paper/main.tex`, `results/raw_evidence_item5_chi2_uniformity.*`.
* **Tests Required:** Inspect rendered markdown; test PDF link resolution.
* **Expected Result:** Zero numerical divergence between README, raw evidence, and LaTeX paper.

### Phase 4: Parity Evidence Re-Execution
* **Objective:** Run `python/verify_m4d_parity.py` and record the actual result in `results/raw_evidence_item4_parity_check.json` and `.txt`. A prior commit attempted to address float32 synchronization, but the latest independent parity rerun still fails.
* **Files Allowed to Change:** `results/raw_evidence_item4_parity_check.json`, `results/raw_evidence_item4_parity_check.txt`.
* **Files That Must Not Change:** `python/m4d_hyperchaos.py`, `embedded_stm32/src/telemetry_protocol.c`.
* **Tests Required:** Run the parity test and record the actual result; passing requires 0 coordinate mismatches, 0 keystream mismatches, no NaNs, and lossless round-trip reconstruction.
* **Expected Result:** Evidence artifact reflects the verified state of Python/C parity.

### Phase 5: Legacy Tree Deprecation
* **Objective:** Archive or deprecate `STM32G474_ECG_Telemetry/` and update root `flash_firmware.bat` to eliminate fallback ambiguity.
* **Files Allowed to Change:** `flash_firmware.bat`, `STM32G474_ECG_Telemetry/` (relocate to `archive/` upon approval).
* **Files That Must Not Change:** `embedded_stm32/`.
* **Tests Required:** Verify `flash_firmware.bat` successfully targets `embedded_stm32/STM32G474_HC1_Telemetry.bin`.
* **Expected Result:** Single source of truth for embedded firmware.

---

## 10. Required Verification Tests

1. **Dataset Integrity & Windowing Test:** Verify that `results/WESAD_HRV_features_expanded.csv` contains exactly 445 rows ($285\text{ baseline} + 160\text{ stress}$) across 15 subjects with 0 missing/NaN entries, confirming $0\%$ overlap across non-overlapping 60s windows.
2. **15-Fold LOSO ML Reproducibility Test:** Execute `python python/train_loso_ml_benchmark.py` and verify:
   * Logistic Regression achieves **$92.13\%$ Accuracy, $88.29\%$ F1 at primary $\tau = 0.50$** (identical across both pipelines). At exploratory $\tau = 0.35$: Python canonical achieves **$92.36\%$ Accuracy, $89.10\%$ F1** ($86.88\%$ sensitivity, $95.44\%$ specificity), while MATLAB historical achieved **$92.36\%$ Accuracy, $89.03\%$ F1** ($86.25\%$ sensitivity, $95.79\%$ specificity).
   * All 6 classifiers achieve $\text{ROC-AUC} \ge 0.937$.
3. **Zero Data Leakage Test:** Confirm that in each fold $k$, the test subject's baseline centroid $B_s$ uses strictly Label 1 windows, test stress labels are never exposed during training, and `StandardScaler` is fitted solely on $N-1$ subjects.
4. **Packet Layout & CRC-16 Verification Test:** Verify that `compute_crc16()` in Python and `telemetry_crc16()` in C compute identical checksums over bytes 2–17 for 1,000 pseudo-random payloads.
5. **C $\leftrightarrow$ Python Parity Test:** Execute `python python/verify_m4d_parity.py` to run the parity test and record the actual result; passing requires 0 coordinate mismatches, 0 keystream mismatches, no NaNs, and lossless round-trip reconstruction.
6. **Numerical Stability / NaN / Inf Test:** Confirm that RK4 integration over 200,000 steps ($dt = 0.0025\text{ s}$) produces bounded state coordinates without numerical underflow or overflow.
7. **Hardware Telemetry Flags Verification Test:** Confirm that incoming UART packets on COM10 have Byte 3 equal to `0x05` (`TELEMETRY_FLAG_ENCRYPTED | TELEMETRY_FLAG_CHAOS_4D`).
8. **Streamlit Smoke Test:** Launch `streamlit run demo/app.py --server.headless true` and confirm clean rendering across all 4 navigation tabs.

---

## 11. Final Recommendation

**The single safest first code change to make is:**  
**Correct the window segmentation description in [`EXECUTION_GUIDE.md`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/EXECUTION_GUIDE.md) and [`PROJECT_IMPLEMENTATION_SYSTEMATIC_GUIDE.md`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/PROJECT_IMPLEMENTATION_SYSTEMATIC_GUIDE.md) from "50% overlap (30s hop)" to "0% overlap (non-overlapping 60s windows, 60s hop)".**

**Why:**  
This is a documentation-only correction that modifies zero executable logic, incurs zero regression risk, requires no compilation or hardware flashing, and immediately resolves the most glaring factual contradiction between the written guides and the ground-truth 445-window dataset and MATLAB DSP code.
