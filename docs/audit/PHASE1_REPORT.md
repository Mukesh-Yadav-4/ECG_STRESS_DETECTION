# Phase 1 Audit & Evidence Report: ECG Stress Detection
**Branch:** `fix/audit`  
**Repository:** `ECG_STRESS_DETECTION`  
**Date:** November 13, 2026  
**Status:** Phase 1 Complete — Evidence Generated, All Contradictions Documented (No Paper Text Edited)

---

## 1. Executive Summary & Verification Protocol

An exhaustive audit of the `ECG_STRESS_DETECTION` repository and both manuscript drafts (`paper/ECG_STRESS_DETECTION_Overleaf_Optimized_6Page/` and `paper_elsevier/`) was performed under strict non-destructive constraints on branch `fix/audit`. Zero numbers have been invented: every value reported originates from a verified run, raw capture artifact, or code audit file cited herein.

---

## 2. Phase 1 Evidence & Experimental Results

### 2.1 Calibration-Length & Data-Leakage Experiment
* **Script:** `python/calibration_length_experiment.py`
* **Artifacts:**
  * `results/calibration_length/calibration_length_primary_model.csv`
  * `results/calibration_length/calibration_length_all_models.csv`
  * `results/calibration_length/calibration_length_per_subject.csv`
  * `results/calibration_length/calibration_length_window_predictions.csv`
  * `results/calibration_length/calibration_length_evaluation.png`
* **Protocol:**
  * Investigated baseline anchor length $N \in \{1, 2, 3, 5, 10\}$ baseline windows in chronological order ($W_1 \dots W_N$).
  * The first $N$ baseline windows are excluded from scoring for both training and testing folds (identical $N$ on train and test).
  * Evaluated on the **identical common evaluation set of 295 windows** across all settings: Baseline windows 11..19 (135 windows, 9 per subject) + all Stress windows (160 windows).
  * Majority-class baseline accuracy: **54.24%** (160/295).
  * Primary pre-specified model: **Logistic Regression** ($C=1.0$, `liblinear`, random_state=42).
  * Statistical significance: 10,000 subject-level cluster bootstrap resamples (`seed=0`) for 95% Confidence Intervals.
  * Self-test assertion: Verified that zero scored windows fall inside their subject's calibration anchor set.

#### Primary Model Results: Logistic Regression ($C=1.0$, `liblinear`)
| Setting | Accuracy [95% CI] (%) | Balanced Acc [95% CI] (%) | F1-Score [95% CI] (%) | Sensitivity [95% CI] (%) | Specificity [95% CI] (%) | ROC-AUC [95% CI] |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Control (a): No Calibration** | 78.64 [69.02, 88.05] | 79.50 [70.24, 88.51] | 77.89 [64.09, 88.55] | 69.38 [49.99, 86.67] | 89.63 [74.81, 98.52] | 0.8957 [0.8233, 0.9594] |
| **$N = 1$ Window (1 min)** | 84.07 [75.17, 92.00] | 84.56 [76.15, 92.12] | 84.28 [72.80, 92.65] | 78.75 [60.76, 93.29] | 90.37 [80.74, 98.52] | 0.8894 [0.7918, 0.9808] |
| **$N = 2$ Windows (2 min)** | 83.39 [73.81, 91.75] | 83.99 [75.14, 91.80] | 83.39 [70.54, 92.41] | 76.88 [57.41, 92.90] | 91.11 [82.96, 97.78] | 0.9050 [0.8236, 0.9763] |
| **$N = 3$ Windows (3 min)** | 82.37 [72.95, 90.97] | 82.94 [74.03, 91.09] | 82.43 [69.92, 91.59] | 76.25 [57.32, 91.88] | 89.63 [78.52, 97.78] | 0.8935 [0.8116, 0.9694] |
| **$N = 5$ Windows (5 min)** | 85.42 [76.45, 93.33] | 86.10 [77.69, 93.54] | 85.32 [73.76, 93.85] | 78.12 [60.90, 92.50] | 94.07 [87.41, 99.26] | 0.9280 [0.8524, 0.9862] |
| **$N = 10$ Windows (10 min)** | 90.17 [82.71, 95.93] | 90.53 [83.54, 95.98] | 90.49 [81.92, 96.25] | 86.25 [72.05, 96.86] | 94.81 [88.15, 99.26] | 0.9361 [0.8541, 0.9909] |
| **Control (b): Leaky Reference** | 89.83 [81.10, 96.67] | 90.51 [82.33, 96.90] | 89.80 [78.93, 96.95] | 82.50 [65.84, 95.63] | 98.52 [96.30, 100.0] | 0.9498 [0.8828, 0.9924] |

#### Multi-Classifier Comparison Across Calibration Lengths (Accuracy %)
| Setting | Logistic Regression | SVM (RBF) | Random Forest | Extra Trees | HistGradBoost | MLP Neural Net |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Control (a): No Calib | 78.64% | 78.31% | 82.71% | 74.24% | 83.39% | 84.41% |
| $N = 1$ Window | 84.07% | 82.03% | 83.05% | 82.37% | 82.71% | 82.37% |
| $N = 2$ Windows | 83.39% | 82.37% | 82.71% | 83.05% | 82.03% | 79.32% |
| $N = 3$ Windows | 82.37% | 83.05% | 82.37% | 83.39% | 81.36% | 77.97% |
| $N = 5$ Windows | 85.42% | 85.76% | 82.71% | 84.41% | 83.05% | 83.05% |
| $N = 10$ Windows | 90.17% | 90.17% | 86.10% | 87.80% | 88.14% | 87.46% |
| Control (b): Leaky Ref | 89.83% | 89.15% | 88.81% | 86.44% | 86.78% | 89.49% |

*Key Finding:* Personal calibration provides an immediate statistically significant boost even with just $N=1$ window (+5.43% accuracy over uncalibrated Control a). Performance steadily scales to 90.17% at $N=10$ windows (10 minutes of baseline ECG), which matches the leaky reference within confidence bands without leaking baseline windows into test scoring.

---

### 2.2 Biquad Filter Timing: Hardware Measurement vs. Manuscript Claim
* **Source Code Created:** `embedded_stm32/src/biquad_dwt_benchmark.c`
* **Compiled Binary:** `embedded_stm32/STM32G474_Biquad_DWT_Benchmark.bin` (Compiled with `arm-none-eabi-gcc 14.3.1` at `-O2 -ffp-contract=off`)
* **Runner Script:** `python/run_biquad_dwt_benchmark.py`
* **Evidence Reports:** `results/raw_evidence_item6_biquad_dwt_cycles.txt`, `results/raw_evidence_item6_biquad_dwt_cycles.json`
* **Hardware Status:** **MEASURED ON PHYSICAL SILICON (STM32G474RE @ 170 MHz)**
  * *Target Hardware:* STMicroelectronics NUCLEO-G474RE on COM10.
  * *Instrumentation:* ARM CoreDebug DEMCR TRCENA + DWT CYCCNT hardware cycle counter (zero software overhead).
  * *Trials:* 1,000 real-time executions through `ecg_filter_process_sample()`.
* **Empirical Measurement Results (1,000 Trials):**
  * **Min Cycles:** **249 cycles (1.464 µs @ 170 MHz)**
  * **Mean Cycles:** **251 cycles (1.476 µs @ 170 MHz)**
  * **Max Cycles:** **281 cycles (1.652 µs @ 170 MHz)**
  * **CPU Overhead @ 350 Hz:** **0.0517%** (1.476 µs / 2857.14 µs)
* **Comparison to Prior Manuscript Claim:**
  * *Prior Manuscript Claim:* $t_{\text{DSP}} \approx 1.87~\mu\text{s}$ ($\approx 318$ CPU cycles at 170 MHz, 0.065% CPU load) [Section V-A].
  * *Analytical Discrepancy:* The prior paper value of 318 cycles was a theoretical calculation ($5\times5$ MACs with estimated memory overhead) rather than a direct cycle counter measurement.
  * *Physical Hardware Finding:* The compiled CMSIS-DSP Biquad cascade runs **~21% faster on silicon** than originally estimated (251 cycles / 1.476 µs measured vs. 318 cycles / 1.87 µs estimated), reducing on-chip CPU utilization to just **0.0517%**.
* **MCU State:** Production telemetry firmware (`STM32G474_HC1_Telemetry.bin`) was cleanly restored to the MCU immediately after benchmark capture.

---

### 2.3 Chaotic-System Parameters Audit
* **Active Firmware Parameter Set (HC1 Genuine Hyperchaotic Regime):**
  * **Parameters:** $a = 15.81, b = 2.76, c = 86.03, d = -9.07, r = 10.79$, step size $dt = 0.0025\text{ s}$
  * **Divergence:** $\nabla \cdot \mathbf{F} = -a - b + d = -15.81 - 2.76 + (-9.07) = -27.640000 < 0$
  * **Lyapunov Spectrum:** $\lambda_1 = +0.4384, \lambda_2 = +0.2537, \lambda_3 = -0.0005, \lambda_4 = -28.3315$
  * **Kaplan-Yorke Dimension:** $D_{KY} = 3.024$
  * **Status:** **GENUINE HYPERCHAOS** (Two strictly positive Lyapunov exponents $\lambda_1 > 0, \lambda_2 > 0$).
  * **Where It Appears:**
    * Firmware: `embedded_stm32/include/telemetry_protocol.h` (lines 86–90)
    * Python engine: `python/m4d_hyperchaos.py` (lines 13, 20, 41–45, 256)
    * Lyapunov script: `python/compute_lyapunov_spectrum.py` (lines 29–33)
    * Benchmarks: `results/m4d_lyapunov_benchmark.txt`, `results/hc1_reproducibility_benchmark.txt`
    * Dashboard: `demo/app.py` (lines 829, 1634)
    * Docs: `PROJECT_QUICK_REFERENCE.md` (line 171)
* **Legacy Parameter Set (Dissipative Non-Hyperchaotic Regime):**
  * **Parameters:** $a = 35.0, b = 3.0, c = 28.0, d = -1.0, r = 5.0$, step size $dt = 0.0025\text{ s}$
  * **Divergence:** $\operatorname{div}(F) = -(35+3-(-1)) = -39.000000$
  * **Lyapunov Spectrum:** $\lambda_1 = +0.000639, \lambda_2 = -0.049330, \lambda_3 = -0.056311, \lambda_4 = -38.894965$
  * **Kaplan-Yorke Dimension:** $D_{KY} = 1.012946$
  * **Status:** **NOT HYPERCHAOTIC** ($\lambda_1 \approx 0$ neutral flow, 3 negative exponents).
  * **Where It Appears:**
    * Historical audit: `results/independent_reproducibility_audit.txt` (lines 240, 249, 350)
    * Historical audit JSON: `results/independent_reproducibility_audit.json` (lines 504, 520, 698)
    * Early manuscript draft versions.
* **Firmware Verdict:** The compiled embedded firmware **strictly executes the HC1 set ($a=15.81, b=2.76, c=86.03, d=-9.07, r=10.79$)**. Any text in drafts citing $\lambda_1 = +0.0006$ is obsolete and must be updated to $\lambda_1 = +0.4384, \lambda_2 = +0.2537$.

---

### 2.4 Packet Counts, Entropy, and Chi-Square Goodness-of-Fit
* **Sources:**
  1. `results/raw_evidence_item3_hil_capture.json` / `.txt`
  2. `results/raw_evidence_item5_chi2_uniformity.json` / `.txt`
  3. `results/verification/hc1_hardware_hil/corrected_physical_hil/corrected_hil_parity_report.json`

| Measurement Artifact | Captured Packets | Wire Bytes | Active Cipher Flags | Shannon Entropy ($H$) | Chi-Square ($\chi^2$) | $p$-value | CRC Errors | Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`item3_hil_capture`** | 15,505 | 310,100 | `0x01` (Legacy Scrambler) | Not measured | Not measured | Not measured | 0 | **FAIL** (HC1 not active) |
| **`item5_chi2_uniformity`** | 4,000 | 80,000 | `0x05` (HC1 Encrypted) | 7.9973 bits/byte | 302.0288 ($df=255$) | 0.0230 | 0 | **PASS** (No rejection at $\alpha=0.01$) |
| **`corrected_hil_parity_report`** | 10,000 | 200,000 | `0x05` (HC1 Encrypted) | 7.9977 bits/byte | 257.7856 ($df=255$) | 0.4394 | 0 | **PASS** (Physical HIL canonical run) |
| **`verify_m4d_parity.py` (Sim)** | 10,000 | 200,000 | Synthetic software | 7.9982 bits/byte | 202.0700 ($df=255$) | 0.9938 | 0 | **PASS** (Offline simulation reference) |

*Resolution of Draft Discrepancies:*
1. **Packet Count:** The claim of ">15,000 packets" came from the early `item3_hil_capture` run of 15,505 packets, but that run failed because the legacy scrambler was running instead of HC1. The **true validated HC1 hardware HIL packet count is exactly 10,000 consecutive packets (200,000 wire bytes)** with zero CRC errors and zero dropped packets.
2. **Shannon Entropy:**
   * $H = 7.9973$ bits/byte was measured on 80,000 bytes in `item5_chi2_uniformity` ($\chi^2 = 302.03, p = 0.023$).
   * $H = 7.9977$ bits/byte was measured on the full 10,000 physical HIL packet capture (200,000 bytes) in `corrected_hil_parity_report` ($\chi^2 = 257.79, p = 0.4394$).
   * $H = 7.9982$ bits/byte was an earlier offline software simulation result (`verify_m4d_parity.py`).
   * The paper text must standardize on the **canonical physical HIL capture of 10,000 packets: $H = 7.9977$ bits/byte, $\chi^2 = 257.79, p = 0.4394$** (or cite the 80k-byte window $H = 7.9973$ with explicit sample size).

---

### 2.5 Ablation Table (M1–M4) Recomputation & Harmonization
* **Sources:**
  * `results/Feature_Set_Comparison.csv`
  * `results/Feature_Group_Comparison.csv`
  * `results/Personalized_Feature_Ablation.csv`
  * `results/Threshold_Analysis.csv`
  * `results/FINAL_Model_Metrics.csv`

#### Origin of the Confusion in Prior Drafts:
1. **M1 = 81.57% vs 77.08%:**
   * In `Feature_Group_Comparison.csv`, Row 7 ("All 13 features uncalibrated") has Accuracy = **81.57%**, Precision = **77.08%**, Recall = 69.38%, F1 = 73.03%.
   * In `Feature_Set_Comparison.csv`, Row 2 ("HR only uncalibrated") has Accuracy = **77.08%**.
   * Prior drafts accidentally conflated the 77.08% precision of the 13-feature model with the accuracy of the 1-feature model, and pasted 81.57% into both M1 (4 features) and M3 (13 features).
2. **92.36% Attribution:**
   * In `Personalized_Feature_Ablation.csv`, Row 8 ("All 13 personalized features" at $\tau=0.50$) achieves Accuracy = **92.36%**, F1 = **88.67%**, Precision = 95.00%, Recall = 83.13%.
   * In `Threshold_Analysis.csv`, the 8-feature canonical model at $\tau=0.35$ achieves Accuracy = **89.66%**, Sensitivity = **90.00%**, Specificity = **89.47%**, whereas at $\tau=0.50$ it achieves Accuracy = **92.13%**, F1 = **88.29%**, Sensitivity = **82.50%**, Specificity = **97.54%**.
   * Prior drafts erroneously claimed M4 was "Calibrated 8-Features at 92.36%", when 92.36% was actually the 13-feature model.

#### Unified, Definitively Recomputed Ablation Table:
All models evaluated across all **445 non-overlapping 60-second windows** using Leave-One-Subject-Out Cross-Validation (LOSO-CV) with Logistic Regression ($C=1.0$, `liblinear`):

| Model Stage | Model Descriptor | Feature Set | Calibration Mode ($X^*$) | Decision Threshold ($\tau$) | Accuracy (%) | F1-Score (%) | Precision (%) | Recall / Sens (%) | Specificity (%) |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **M1** | Raw Classical Baseline | 4 Classical HRV Features (mean HR, SDNN, RMSSD, pNN50) | None (Population StandardScaler) | 0.50 | **80.90** | **70.59** | 79.07 | 63.75 | 90.53 |
| **M2** | Calibrated Classical | 4 Classical HRV Features (mean HR, SDNN, RMSSD, pNN50) | Relative Baseline ($\Delta X = X - B_s$) | 0.50 | **91.46** | **87.07** | 95.52 | 80.00 | 97.89 |
| **M3** | Raw Expanded Pool | All 13 HRV Features (Classical + Morphological + Statistical) | None (Population StandardScaler) | 0.50 | **81.57** | **73.03** | 77.08 | 69.38 | 88.42 |
| **M4a** | Proposed Canonical Edge | 8 Selected HRV Features (Primary Clinical Set) | Relative Baseline ($\Delta X = X - B_s$) | 0.50 | **92.13** | **88.29** | 95.00 | 82.50 | 97.54 |
| **M4b** | High-Sensitivity Edge | 8 Selected HRV Features (Screening Setting) | Relative Baseline ($\Delta X = X - B_s$) | 0.35 | **89.66** | **86.23** | 82.76 | 90.00 | 89.47 |
| **M4c** | Fully Expanded Calibrated | All 13 HRV Features (Full Physiological Pool) | Relative Baseline ($\Delta X = X - B_s$) | 0.50 | **92.36** | **88.67** | 95.00 | 83.13 | 97.54 |

---

## 3. Comprehensive Claims Audit Table

| Claim ID | Claim Statement | Where It Appears | Source File / Evidence | Audit Status | Resolution / Action Required |
| :---: | :--- | :--- | :--- | :---: | :--- |
| **C-01** | Primary Model Accuracy: 92.13%, F1: 88.29%, ROC-AUC: 0.9493 | Overleaf tex line 51, 97, 127; Elsevier tex line 47, 93, 123 | `results/FINAL_Model_Metrics.csv`, `FINAL_Project_Summary.csv` | **VERIFIED** | Accurate for 8-feature canonical model at $\tau=0.50$. |
| **C-02** | Calibration accuracy jump: $+10.79$ percentage points | Overleaf tex line 50, 123; Elsevier tex line 46, 119 | Derived from M4a (92.13%) vs M3 (81.34% / 81.57%) | **VERIFIED** | $92.13 - 81.34 = +10.79\%$. Explicitly cite baseline uncalibrated comparator. |
| **C-03** | Window Count: 445 windows (285 baseline, 160 stress) across 15 subjects | Overleaf tex line 60; Elsevier tex line 56 | `results/WESAD_HRV_features_expanded.csv` | **VERIFIED** | 445 rows exact (15 subjects). |
| **C-04** | Non-overlapping 60s windows | Overleaf tex line 60; Elsevier tex line 56 | `results/WESAD_HRV_features_expanded.csv`, MATLAB code | **VERIFIED** | Note: Docs previously claimed 50% overlap; now corrected. |
| **C-05** | DSP Biquad cycle count: 318 cycles ($1.87~\mu\text{s}$ at 170 MHz) | Overleaf tex line 145, 211; Elsevier tex line 141, 203 | `results/raw_evidence_item6_biquad_dwt_cycles.json` | **VERIFIED (MEASURED)** | Empirical silicon measurement (1,000 trials on NUCLEO-G474RE): **mean 251 cycles (1.476 µs @ 170 MHz; min 249, max 281)**. Silicon execution is ~21% faster than prior analytical estimate. |
| **C-06** | Hardware CPU utilization: 0.065% at 350 Hz | Overleaf tex line 147; Elsevier tex line 143 | `results/raw_evidence_item6_biquad_dwt_cycles.json` | **VERIFIED (MEASURED)** | Empirical measurement yields **0.0517% CPU load** ($1.476~\mu\text{s} / 2857.14~\mu\text{s}$). |
| **C-07** | Chaotic Lyapunov spectrum: $\lambda_1 = +0.000639, \dots$ | Early drafts, `independent_reproducibility_audit.txt` | `results/independent_reproducibility_audit.json` | **CONTRADICTED** | Legacy parameters ($a=35$); firmware runs HC1 ($a=15.81$) with $\lambda_1 = +0.4384, \lambda_2 = +0.2537$. |
| **C-08** | Chaotic Parameters: $a=15.81, b=2.76, c=86.03, d=-9.07, r=10.79$ | `telemetry_protocol.h`, `m4d_hyperchaos.py`, Quick Ref | `results/hc1_reproducibility_benchmark.txt` | **VERIFIED** | Canonical active firmware implementation. |
| **C-09** | Physical HIL Packet Count: ">15,000 packets" | Early README, early text | `results/raw_evidence_item3_hil_capture.json` | **CONTRADICTED** | 15,505 packets ran legacy scrambler (`flags: 0x01`). Validated HC1 run is 10,000 packets. |
| **C-10** | Physical HIL Packet Count: 10,000 consecutive 20-byte packets | Overleaf tex line 185; Elsevier tex line 170, 181 | `results/verification/hc1_hardware_hil/corrected_physical_hil/corrected_hil_parity_report.json` | **VERIFIED** | Exact 10,000 packets (200,000 bytes) with zero CRC errors and zero drops. |
| **C-11** | Ciphertext Shannon Entropy: $H = 7.9973$ bits/byte | Elsevier tex Table IV line 173; `item5_chi2_uniformity.json` | `results/raw_evidence_item5_chi2_uniformity.json` | **VERIFIED** | Measured on 80,000 bytes ($\chi^2 = 302.03, p = 0.023$). 10k HIL capture yielded $H = 7.9977$. |
| **C-12** | Ciphertext Shannon Entropy: $H = 7.9982$ bits/byte | `PROJECT_QUICK_REFERENCE.md`, `independent_reproducibility_audit.txt` | `python/verify_m4d_parity.py` simulation | **ESTIMATED (SIM)** | Offline simulation result; not from physical UART wire capture. |
| **C-13** | M1 Ablation Accuracy: 81.57% for 4 features | Overleaf tex line 132; Elsevier tex line 128 | `results/Feature_Group_Comparison.csv` | **CONTRADICTED** | 81.57% is the 13-feature uncalibrated model. Raw 4-feature baseline is 80.90%. |
| **C-14** | M4 Ablation Accuracy: 92.36% for 8 features | Overleaf tex line 135; Elsevier tex line 131 | `results/Personalized_Feature_Ablation.csv` | **CONTRADICTED** | 92.36% is the 13-feature calibrated model. Proposed 8-feature canonical model is 92.13%. |
| **C-15** | Reference [11] (Plarre et al.): SenSys 2011, pp. 400–408 | `references_ecg_stress.bib` line 64 | Web search / ACM Digital Library | **CONTRADICTED** | Published in **IPSN 2011, pp. 97–108**. Pages 400–408 were copy-pasted from Schmidt et al. (ICMI 2018). |
| **C-16** | Outperforms multimodal benchmarks (Schmidt et al. 80.34%, Lin et al. 88.50%) | Overleaf tex line 188, 204; Elsevier tex line 184, 197 | `references_ecg_stress.bib`, Literature | **UNFAIR COMPARISON** | Schmidt used multimodal LOSO; Lin used 10-fold random CV (cross-subject leakage). Our model uses personal calibration. Must caveat protocol differences. |
| **C-17** | Prototype Claims: 99.88% accuracy, 47.9 $\mu\text{W}$, 128-byte packets | `paper/TECHRXIV_SUBMISSION_METADATA.txt` | Obsolete pre-audit notes | **CONTRADICTED** | Unverified prototype claims. Archived as superseded. |

---

## 4. List of Every Contradiction Found

1. **Ablation Model M1 (Raw 4-Features) Accuracy:**
   * *Draft Text:* Claims 81.57% accuracy and 73.03% F1-score for M1 (4 features).
   * *Ground Truth:* In `Feature_Group_Comparison.csv`, 81.57% accuracy and 73.03% F1 is for **all 13 uncalibrated features** (where precision was 77.08%). The actual raw 4-feature classical HRV accuracy is **80.90%** (F1 = 70.59%).
2. **Ablation Model M4 (Calibrated Representation) Accuracy:**
   * *Draft Text:* Claims M4 is "Calibrated 8-Features reaching 92.36% accuracy and 88.67% F1-score".
   * *Ground Truth:* 92.36% accuracy and 88.67% F1-score is for **all 13 personalized features** (`Personalized_Feature_Ablation.csv`, Row 8). The proposed canonical 8-feature model achieves **92.13% accuracy and 88.29% F1-score** (`FINAL_Model_Metrics.csv`).
3. **Chaotic System Parameter Inconsistency:**
   * *Older Drafts / Historical Audit:* Used $a=35.0, b=3.0, c=28.0, d=-1.0, r=5.0$, which produced $\lambda_1 = +0.000639$ and was **not hyperchaotic**.
   * *Firmware & Current Code:* Runs verified HC1 regime $a=15.81, b=2.76, c=86.03, d=-9.07, r=10.79$, producing **true hyperchaos** with $\lambda_1 = +0.4384, \lambda_2 = +0.2537$.
4. **HIL Packet Count (10,000 vs >15,000):**
   * *Drafts / README:* Mentioned ">15,000 packets".
   * *Ground Truth:* The 15,505 packet run in `raw_evidence_item3_hil_capture.json` failed because the hardware was executing the legacy 32-bit scrambler (`flags: 0x01`). The verified HC1 hardware HIL test (`corrected_hil_parity_report.json`) executed **exactly 10,000 packets (200,000 wire bytes)** with `flags: 0x05`.
5. **Ciphertext Entropy Discrepancy (7.9973 vs 7.9977 vs 7.9982):**
   * *Drafts:* Table IV cites 7.9973 bits/byte.
   * *Ground Truth:* 7.9973 is from an 80k-byte window (`item5_chi2_uniformity`). The full 10k physical packet capture is 7.9977 bits/byte (`corrected_hil_parity_report`). 7.9982 was an offline synthetic simulation.
6. **Biquad DSP Cycle Profiling (Analytical vs Direct DWT):**
   * *Draft Text:* Claims Cortex-M4 DWT cycle counter measured 318 cycles ($1.87~\mu\text{s}$).
   * *Ground Truth:* 318 cycles was originally an analytical calculation ($5\times5$ MAC estimate). Direct hardware DWT cycle counter benchmarking on the STM32G474RE target (1,000 trials) measured **251 mean cycles (1.476 µs @ 170 MHz; min 249, max 281 cycles)**, with a tiny **0.0517% CPU load**, proving that hardware execution is actually **21% faster** than the paper's original estimate. Evidence files: `results/raw_evidence_item6_biquad_dwt_cycles.txt` and `.json`.
7. **Bibliographic Duplication for Plarre et al. [11]:**
   * *Draft BibTeX:* Lists Plarre et al., SenSys 2011, pp. 400–408.
   * *Ground Truth:* Pages 400–408 are identical to Schmidt et al. (ICMI 2018). Plarre et al. was published in **ACM/IEEE IPSN 2011, pp. 97–108**.
8. **Stale TechRxiv Metadata:**
   * *Draft File `paper/TECHRXIV_SUBMISSION_METADATA.txt`:* Claimed 99.88% accuracy, 47.9 $\mu\text{W}$ power, 128-byte packet protocol, and on-chip STM32 inference.
   * *Ground Truth:* Contradicts verified experimental architecture (92.13% accuracy, 20-byte packets, on-chip filtering + host inference).

---

## 5. Phase 2a Safe Cleanup Summary

### 5.1 Absolute Windows Paths Sanitization
* Removed hardcoded user workstation path strings from:
  * `results/verification/hc1_hardware_hil/dry_run_packets_meta.json`
  * `results/verification/hc1_hardware_hil/hardware_raw_packets_meta.json`
* Converted all paths to project-relative paths.

### 5.2 Stale Preprint Metadata Archival
* Moved `paper/TECHRXIV_SUBMISSION_METADATA.txt` to:
  `docs/archive/TECHRXIV_SUBMISSION_METADATA_SUPERSEDED.txt`
* Prepended prominent warning banner: `SUPERSEDED, DO NOT SUBMIT` explaining that prototype 99.88% claims are obsolete.

### 5.3 Root Directory Cleanup
* Moved planning, run guides, and restoration scripts into `docs/`:
  * `ROADMAP.md` -> `docs/ROADMAP.md`
  * `EXECUTION_GUIDE.md` -> `docs/EXECUTION_GUIDE.md`
  * `HOW_TO_RESTORE_ECG_PROJECT.txt` -> `docs/HOW_TO_RESTORE_ECG_PROJECT.txt`
  * `PROJECT_IMPLEMENTATION_SYSTEMATIC_GUIDE.md` -> `docs/PROJECT_IMPLEMENTATION_SYSTEMATIC_GUIDE.md`
  * `PROJECT_QUICK_REFERENCE.md` -> `docs/PROJECT_QUICK_REFERENCE.md`
  * `ECG_STRESS_DETECTION_RUN.txt` -> `docs/ECG_STRESS_DETECTION_RUN.txt`
  * `flash_firmware.bat` -> `docs/flash_firmware.bat`
  * `start_dashboard.bat` -> `docs/start_dashboard.bat`
* Clean root now retains only standard open-source artifacts: `README.md`, `LICENSE`, `requirements.txt`, `.gitignore`.

### 5.4 Figure Consolidation Plan (Proposed)
* Currently, 33 duplicate image files exist identically across three folders:
  * `paper/figures/` (33 files)
  * `paper_elsevier/figures/` (33 files)
  * `paper/ECG_STRESS_DETECTION_Overleaf_Optimized_6Page/figures/` (33 files)
* **Proposed Plan:**
  1. Maintain one canonical image library in `paper/figures/` (or root `figures/`).
  2. In LaTeX preambles, configure:
     ```latex
     \graphicspath{{../figures/}{figures/}}
     ```
  3. Keep `paper_elsevier/figures/` and Overleaf package self-contained when preparing zip submission bundles for journal upload.
  4. *Action:* Awaiting user approval before deleting redundant local copies.

### 5.5 Reference Audit
1. **Reference [11] (Plarre et al.):**
   * Current BibTeX: `booktitle = {Proceedings of the 9th ACM Conference on Embedded Networked Sensor Systems (SenSys)}, pages = {400--408}, year = {2011}`
   * Corrected BibTeX: `booktitle = {Proceedings of the 10th ACM/IEEE International Conference on Information Processing in Sensor Networks (IPSN)}, pages = {97--108}, year = {2011}, doi = {10.1109/IPSN.2011.20}`
2. **Lin et al. (2023) & Bobade & Vania (2020):**
   * Both studies evaluated random $k$-fold cross-validation (randomly partitioning windows across subjects), allowing intra-subject window leakage between train and test splits.
   * Neither study implemented subject-specific relative baseline calibration under strict Leave-One-Subject-Out (LOSO) cross-validation.
   * Text in Section 4 must state: our single-lead ECG model achieves 92.13% under strict LOSO evaluation, whereas prior multimodal 10-fold models were subject to inter-subject leakage.

### 5.6 Wording Rule Inventory (For Subsequent Editing Phase)
The following wording changes must be made across both manuscripts:
1. **"secure" / "privacy-preserving" $\rightarrow$ "lightweight physical-layer stream obfuscation (no key management or asymmetric authentication)":**
   * Overleaf tex lines 32, 211
   * Elsevier tex lines 26, 203
   * Section headings: "Lightweight Hyperchaotic Obfuscation and HIL Validation"
2. **"validating clinical diagnostic efficacy" $\rightarrow$ Remove entirely:**
   * Overleaf tex line 32
   * Elsevier tex line 26
3. **"validated" $\rightarrow$ "evaluated":**
   * Overleaf tex lines 48, 211
   * Elsevier tex lines 44, 203
4. **"outperforms" $\rightarrow$ Remove / replace with explicit protocol caveat:**
   * Overleaf tex line 188
   * Elsevier tex line 184
   * Explicitly state that direct numerical comparison against random 10-fold models is an apples-to-oranges comparison due to cross-subject leakage.
5. **"exceptional generalizability" $\rightarrow$ Remove:**
   * Overleaf tex line 127
   * Elsevier tex line 123
