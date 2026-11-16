# Phase 2 Verification Report (PART A)

**Document:** `PHASE2_VERIFY.md`  
**Repository Branch:** `fix/audit`  
**Status:** Verification Complete — All Empirical Evidence Sourced from Verifiable Runs and Hardware Measurements  

---

## 1. Paired Contrasts & Bootstrap Inference

### 1.1 Methodology & Evaluation Protocol
* **Evaluation Window Set:** Evaluated on the exact same **295 non-anchor windows** across 15 WESAD subjects (135 Baseline windows, Windows 11–19; 160 Stress windows, Windows 1–12).
* **Primary Pre-specified Classifier:** Logistic Regression ($C=1.0$, solver `liblinear`, `random_state=42`) under 15-fold Leave-One-Subject-Out Cross-Validation (LOSO-CV). Pre-specified prior to test evaluation; no model selected on test results.
* **Inference Method:** Subject-level paired cluster bootstrap (10,000 resamples, seed 0). For each bootstrap replication $b$, the exact same resampled multiset of subjects is evaluated across both conditions to compute the paired difference:
  $$\Delta^{(b)} = \text{Metric}_A^{(b)} - \text{Metric}_B^{(b)}$$
* **Rule on Statistical Significance:** The term **significant** is used strictly if and only if the 95% bootstrap confidence interval excludes zero.

### 1.2 Point Estimates on 295-Window Common Evaluation Set
* **Control (a) [No Calibration, StandardScaler only]:** Accuracy = **78.64%**, Balanced Accuracy = **79.50%**
* **$N=1$ Baseline Window (1 minute):** Accuracy = **84.07%**, Balanced Accuracy = **84.56%**
* **$N=2$ Baseline Windows (2 minutes):** Accuracy = **83.39%**, Balanced Accuracy = **83.99%**
* **$N=3$ Baseline Windows (3 minutes):** Accuracy = **82.37%**, Balanced Accuracy = **82.94%**
* **$N=5$ Baseline Windows (5 minutes):** Accuracy = **85.42%**, Balanced Accuracy = **86.10%**
* **$N=10$ Baseline Windows (10 minutes):** Accuracy = **90.17%**, Balanced Accuracy = **90.53%**
* **Control (b) [Leaky Reference, All 19 Windows]:** Accuracy = **89.83%**, Balanced Accuracy = **90.51%**

### 1.3 Paired Contrasts Table (10,000 Resamples, Seed 0)
*Evidence file:* [`results/calibration_length/paired_contrasts_bootstrap.csv`](results/calibration_length/paired_contrasts_bootstrap.csv)

| Contrast | Point $\Delta$ Accuracy | 95% Bootstrap CI (Acc) | Statistically Significant? | Point $\Delta$ Balanced Acc | 95% Bootstrap CI (Bal Acc) | Statistically Significant? |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **$N=1$ minus Control (a)** | $+5.42\text{ pp}$ | $[-2.70, +13.40]\text{ pp}$ | **No** (CI spans 0) | $+5.06\text{ pp}$ | $[-2.81, +12.71]\text{ pp}$ | **No** (CI spans 0) |
| **$N=2$ minus Control (a)** | $+4.75\text{ pp}$ | $[-3.06, +12.72]\text{ pp}$ | **No** (CI spans 0) | $+4.49\text{ pp}$ | $[-3.09, +12.13]\text{ pp}$ | **No** (CI spans 0) |
| **$N=3$ minus Control (a)** | $+3.73\text{ pp}$ | $[-4.05, +11.56]\text{ pp}$ | **No** (CI spans 0) | $+3.44\text{ pp}$ | $[-3.95, +10.72]\text{ pp}$ | **No** (CI spans 0) |
| **$N=5$ minus Control (a)** | $+6.78\text{ pp}$ | $[+0.68, +13.22]\text{ pp}$ | **Yes** (excludes 0) | $+6.60\text{ pp}$ | $[+0.67, +12.98]\text{ pp}$ | **Yes** (excludes 0) |
| **$N=10$ minus Control (a)**| $+11.53\text{ pp}$ | $[+5.07, +18.06]\text{ pp}$ | **Yes** (excludes 0) | $+11.03\text{ pp}$ | $[+4.81, +17.47]\text{ pp}$ | **Yes** (excludes 0) |
| **$N=10$ minus $N=5$** | $+4.75\text{ pp}$ | $[+0.68, +9.52]\text{ pp}$ | **Yes** (excludes 0) | $+4.43\text{ pp}$ | $[+0.74, +8.87]\text{ pp}$ | **Yes** (excludes 0) |
| **$N=10$ minus Control (b)**| $+0.34\text{ pp}$ | $[-3.36, +4.79]\text{ pp}$ | **No** (CI spans 0) | $+0.02\text{ pp}$ | $[-3.76, +4.39]\text{ pp}$ | **No** (CI spans 0) |

**Conclusion on Calibration Length:**
At $N \le 3$ minutes, baseline calibration yields point improvements of $+3.7$ to $+5.4\text{ pp}$, but none are statistically distinguishable from zero as their 95% confidence intervals cross zero. A statistically significant performance improvement requires at least **$N=5$ minutes of resting calibration** ($+6.78\text{ pp}$ [$0.68, 13.22]$), while **$N=10$ minutes** yields a significant additional gain of $+4.75\text{ pp}$ over $N=5$ ($+11.53\text{ pp}$ [$5.07, 18.06$] over uncalibrated). Furthermore, $N=10$ achieves statistical parity with the leaky all-baseline reference ($\Delta = +0.34\text{ pp}$ [$-3.36, +4.79$]), confirming that personal normalization can be deployed without test data leakage.

---

## 2. Leak-Free Ablation Study

*Evidence files:* [`results/calibration_length/leak_free_ablation_results.csv`](results/calibration_length/leak_free_ablation_results.csv) & [`python/leak_free_ablation_experiment.py`](python/leak_free_ablation_experiment.py)

### 2.1 Leak-Free Table (Common 295 Evaluation Windows, LOSO-CV, Logistic Regression)
Each training subject anchors on its first $N$ baseline windows, and those $N$ windows are excluded from training. The test subject anchors strictly on its first $N$ baseline windows, and scoring occurs solely on the remaining non-anchor windows (Windows 11–19 for Baseline + all Stress windows).

| Model ID | Feature Representation | Calibration Setting | Accuracy (%) | 95% Bootstrap CI | F1-Score (%) | 95% Bootstrap CI | Sens (%) | Spec (%) |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **A1** | 1-feature (MeanHR) | Raw (StandardScaler only) | 72.20 | [61.9, 82.9] | 69.63 | [52.1, 83.0] | 58.75 | 88.15 |
| **A2** | 1-feature (MeanHR) | Calibrated ($N=5$) | 83.73 | [73.2, 92.9] | 83.10 | [68.3, 93.2] | 73.75 | 95.56 |
| **A3** | 1-feature (MeanHR) | Calibrated ($N=10$) | 84.41 | [74.7, 93.2] | 84.25 | [71.3, 93.5] | 76.88 | 93.33 |
| **B1** | 4-feature (Classical Time-Domain) | Raw (StandardScaler only) | 75.25 | [64.4, 86.1] | 73.26 | [55.1, 86.3] | 62.50 | 90.37 |
| **B2** | 4-feature (Classical Time-Domain) | Calibrated ($N=5$) | 85.76 | [76.8, 93.6] | 85.42 | [73.4, 94.0] | 76.88 | 96.30 |
| **B3** | 4-feature (Classical Time-Domain) | Calibrated ($N=10$) | 88.81 | [81.0, 95.2] | 88.96 | [79.6, 95.5] | 83.12 | 95.56 |
| **C1** | **8-feature (Core Physiological)** | Raw (StandardScaler only) | 78.64 | [69.0, 88.1] | 77.89 | [64.1, 88.5] | 69.38 | 89.63 |
| **C2** | **8-feature (Core Physiological)** | Calibrated ($N=5$) | 85.42 | [76.5, 93.3] | 85.32 | [73.8, 93.9] | 78.12 | 94.07 |
| **C3** | **8-feature (Primary Canonical)** | **Calibrated ($N=10$)** | **90.17** | **[82.7, 95.9]** | **90.49** | **[81.9, 96.2]** | **86.25** | **94.81** |
| **D1** | 13-feature (Full Expanded) | Raw (StandardScaler only) | 78.31 | [69.3, 87.3] | 77.78 | [64.8, 87.9] | 70.00 | 88.15 |
| **D2** | 13-feature (Full Expanded) | Calibrated ($N=5$) | 86.10 | [77.5, 93.7] | 86.10 | [75.2, 94.2] | 79.38 | 94.07 |
| **D3** | 13-feature (Full Expanded) | Calibrated ($N=10$) | 89.49 | [81.9, 95.6] | 89.84 | [81.2, 95.9] | 85.62 | 94.07 |

### 2.2 Legacy Leaky Reference Table (445 Windows, All-Baseline Anchor)
*Note: Retained strictly as a labelled historical benchmark showing results when each subject is anchored on all 19 baseline windows and scored on those same windows.*

| Model ID | Feature Representation | Calibration Setting | Accuracy (%) | 95% Bootstrap CI | F1-Score (%) | 95% Bootstrap CI | Sens (%) | Spec (%) |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **L1** | 1-feature (MeanHR) | Leaky All-Baseline Anchor | 89.21 | [82.4, 95.3] | 82.98 | [68.8, 93.3] | 73.12 | 98.25 |
| **L2** | 4-feature (Classical Time-Domain) | Leaky All-Baseline Anchor | 91.46 | [85.4, 96.6] | 87.07 | [75.9, 95.3] | 80.00 | 97.89 |
| **L3** | 8-feature (Core Physiological) | Leaky All-Baseline Anchor | 92.13 | [86.4, 97.1] | 88.29 | [77.6, 95.8] | 82.50 | 97.54 |
| **L4** | 13-feature (Full Expanded) | Leaky All-Baseline Anchor | 92.36 | [86.8, 97.1] | 88.67 | [78.6, 95.9] | 83.12 | 97.54 |

---

## 3. Threshold Reconciliation & Recomputation

*Evidence files:* [`results/verification/stage2_threshold_discrepancy.md`](results/verification/stage2_threshold_discrepancy.md), [`results/Threshold_Analysis.csv`](results/Threshold_Analysis.csv), [`results/Personalized_Classifier_Predictions.csv`](results/Personalized_Classifier_Predictions.csv), [`results/ML_Predictions_LOSO.csv`](results/ML_Predictions_LOSO.csv).

### 3.1 Recomputation of $\tau = 0.35$ on Legacy 445 Windows
* **MATLAB Pipeline ([`results/Personalized_Classifier_Predictions.csv`](results/Personalized_Classifier_Predictions.csv) & [`results/Threshold_Analysis.csv`](results/Threshold_Analysis.csv) Row 25):**
  * $\text{Accuracy} = \mathbf{92.36\%}$ ($411/445$)
  * $\text{Sensitivity / Recall} = \mathbf{86.25\%}$ ($138/160$)
  * $\text{Specificity} = \mathbf{95.79\%}$ ($273/285$)
  * $\text{Precision} = 92.00\%$ ($138/150$)
  * $\text{F1-Score} = 89.03\%$
  * Confusion Matrix: $\text{TP}=138, \text{FP}=12, \text{TN}=273, \text{FN}=22$
* **Python Benchmark Pipeline ([`results/ML_Predictions_LOSO.csv`](results/ML_Predictions_LOSO.csv)):**
  * $\text{Accuracy} = \mathbf{92.36\%}$ ($411/445$)
  * $\text{Sensitivity / Recall} = \mathbf{86.88\%}$ ($139/160$)
  * $\text{Specificity} = \mathbf{95.44\%}$ ($272/285$)
  * $\text{Precision} = 91.45\%$ ($139/152$)
  * $\text{F1-Score} = 89.10\%$
  * Confusion Matrix: $\text{TP}=139, \text{FP}=13, \text{TN}=272, \text{FN}=21$
* **Attribution of the "89.66%/90.00%/89.47%" Mix-Up:**
  * The citation of `89.66% Acc / 90.00% Sens / 89.47% Spec` originated as an erroneous threshold lookup in `PHASE1_REPORT.md` (lines 148-152), not in the original paper drafts.
  * An exhaustive audit of `results/Threshold_Analysis.csv` reveals the exact mathematical origin:
    * Row 18 ($\tau = 0.18$): $\text{Acc} = 89.66\%, \text{Sens} = 90.00\%, \text{Spec} = 89.47\%$
    * Row 19 ($\tau = 0.19$): $\text{Acc} = 89.66\%, \text{Sens} = 90.00\%, \text{Spec} = 89.47\%$
  * **Finding:** `PHASE1_REPORT.md` inadvertently copied the metric row corresponding to $\tau = 0.18$ / $0.19$ instead of $\tau = 0.35$ (Row 25). The original paper drafts and source prediction CSVs (`results/Threshold_Analysis.csv`, `results/ML_Predictions_LOSO.csv`, and `results/Personalized_Classifier_Predictions.csv`) correctly reported **$92.36\%$ accuracy**, $86.25\%$ sensitivity, and $95.79\%$ specificity.

### 3.2 Operating Metrics on the Leak-Free Protocol (295 Windows, Logistic Regression)
* **At $N=10$ Baseline Anchor Windows (Primary Model):**
  * $\tau = 0.50$ (Pre-specified default cutoff):
    * $\text{Accuracy} = \mathbf{90.17\%}$ ($266 / 295$)
    * $\text{F1-Score} = \mathbf{90.49\%}$
    * $\text{Sensitivity / Recall} = \mathbf{86.25\%}$ ($138 / 160$)
    * $\text{Specificity} = \mathbf{94.81\%}$ ($128 / 135$)
    * $\text{Precision} = \mathbf{95.17\%}$ ($138 / 145$)
    * $\text{Balanced Accuracy} = 90.53\%$
    * Confusion Matrix: $\text{TP}=138, \text{FP}=7, \text{TN}=128, \text{FN}=22$
  * $\tau = 0.35$ (Exploratory screening cutoff):
    * $\text{Accuracy} = \mathbf{87.80\%}$ ($259 / 295$)
    * $\text{F1-Score} = \mathbf{88.75\%}$
    * $\text{Sensitivity / Recall} = \mathbf{88.75\%}$ ($142 / 160$)
    * $\text{Specificity} = \mathbf{86.67\%}$ ($117 / 135$)
    * $\text{Precision} = \mathbf{88.75\%}$ ($142 / 160$)
    * $\text{Balanced Accuracy} = 87.71\%$
    * Confusion Matrix: $\text{TP}=142, \text{FP}=18, \text{TN}=117, \text{FN}=18$
* **At $N=5$ Baseline Anchor Windows:**
  * $\tau = 0.50$: Accuracy = **85.42%**, F1 = **85.32%**, Sensitivity = **78.12%**, Specificity = **94.07%** ($\text{TP}=125, \text{FP}=8, \text{TN}=127, \text{FN}=35$)
  * $\tau = 0.35$: Accuracy = **86.44%**, F1 = **87.01%**, Sensitivity = **83.75%**, Specificity = **89.63%** ($\text{TP}=134, \text{FP}=14, \text{TN}=121, \text{FN}=26$)

---

## 4. Telemetry Frame Byte Scope for Statistical Wire Checks

*Evidence files:* [`python/verify_hardware_hc1_capture.py`](python/verify_hardware_hc1_capture.py) (line 277) & [`results/verification/hc1_hardware_hil/hardware_raw_packets.bin`](results/verification/hc1_hardware_hil/hardware_raw_packets.bin).

### 4.1 Exact Byte Scope & Code Line
In `python/verify_hardware_hc1_capture.py`, line 277 selects:
```python
ciphertext_bytes.extend(pkt_bytes[10:18])
```
* **Byte Scope:** Strictly Bytes 10 through 17 of each 20-byte packet.
  * Bytes 10–13: Scrambled Raw ECG sample (`float32`, 4 bytes)
  * Bytes 14–17: Scrambled Filtered ECG sample (`float32`, 4 bytes)
* **Total Payload Bytes Evaluated:** Across 10,000 consecutive physical packets, $10,000 \times 8 = \mathbf{80,000\text{ bytes}}$.

### 4.2 Recomputation Comparison: Scrambled Payload vs. Full Wire Frame

| Byte Scope | Total Bytes Analyzed | Shannon Entropy | Theoretical Max | Chi-Square ($\chi^2$, $df=255$) | $p$-value | Uniformity Hypothesis ($\alpha=0.01$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Scrambled Payload Only (Bytes 10..17)** | **80,000 B** | **7.997663 bits/byte** | 8.0000 | **257.7856** | **0.439435** | **No rejection of uniformity** ($p > 0.01$) |
| **Full Frame (Bytes 0..19)** | **200,000 B** | **7.070492 bits/byte** | 8.0000 | **999,331.89** | **0.000000** | **Rejected** ($p < 0.0001$) |

**Explanation:**
The full frame includes static transport framing headers: Byte 0 (Sync `0xAA`), Byte 1 (Sync `0x55`), Byte 2 (Version `0x01`), and Byte 3 (Flags `0x05`). Because these 4 bytes repeat identically in every frame, evaluating the entire 20-byte packet artificially degrades Shannon entropy to 7.07 bits/byte and produces massive Chi-square deviation. The scrambled payload alone demonstrates high empirical byte-level uniformity ($H = 7.9977$ bits/byte, $\chi^2 = 257.79, p = 0.4394$).

---

## 5. DWT Benchmark Identity Verification

*Evidence files:* [`embedded_stm32/src/biquad_dwt_benchmark.c`](embedded_stm32/src/biquad_dwt_benchmark.c), [`embedded_stm32/src/main_stm32.c`](embedded_stm32/src/main_stm32.c), [`embedded_stm32/Makefile`](embedded_stm32/Makefile).

* **Filter Implementation:**
  * `biquad_dwt_benchmark.c` includes `#include "ecg_dsp_filter.h"` and directly calls:
    ```c
    ecg_filter_init(&g_filter, g_filter_state, 350);
    volatile float out_sample = ecg_filter_process_sample(&g_filter, in_sample);
    ```
  * Production telemetry firmware (`main_stm32.c`) includes `#include "ecg_dsp_filter.h"` and calls:
    ```c
    ecg_filter_init(&g_ecg_filter, g_filter_state, ECG_SAMPLE_RATE_HZ);
    float filtered_ecg_val = ecg_filter_process_sample(&g_ecg_filter, raw_ecg_val);
    ```
  * Both compile and link the exact same underlying C source file: [`embedded_stm32/src/ecg_dsp_filter.c`](embedded_stm32/src/ecg_dsp_filter.c). It is **not** a reimplementation.
* **Compiler Flags:**
  * Both binaries (`STM32G474_HC1_Telemetry.elf` and `STM32G474_Biquad_DWT_Benchmark.elf`) were compiled with `arm-none-eabi-gcc 14.3.1` using identical flags:
    ```text
    -mcpu=cortex-m4 -mfpu=fpv4-sp-d16 -mfloat-abi=hard -mthumb -O2 -ffp-contract=off
    -Wall -fdata-sections -ffunction-sections -Iinclude
    -T STM32G474RETX_FLASH.ld -Wl,--gc-sections -specs=nano.specs -specs=nosys.specs -lc -lm -lnosys
    ```

---

## 6. Corrected Physical HIL Analysis & Replay Source

*Evidence files:* [`results/verification/hc1_hardware_hil/physical_hil_failure_root_cause.md`](results/verification/hc1_hardware_hil/physical_hil_failure_root_cause.md) & [`results/verification/hc1_hardware_hil/corrected_physical_hil/corrected_hil_parity_report.json`](results/verification/hc1_hardware_hil/corrected_physical_hil/corrected_hil_parity_report.json).

### 6.1 Root Cause & What Was Corrected
* In the initial HIL run, the verification script assumed that captured packet index $k \in [0, 9999]$ corresponded directly to reference sample $k \pmod{2100}$.
* The STM32 board booted 32.65 seconds prior to capture startup, beginning transmission at sequence number $\text{seq\_id} = 11428$.
* The firmware was transmitting sample index $11428 \pmod{2100} = 928$. The initial verifier compared sample $k + 928$ against sample $k$, measuring a phase difference of 928 samples (a $2.651\text{ s}$ ECG waveform shift), causing an apparent $0.926\text{ mV}$ error.
* In `corrected_physical_hil`, the verifier performs **Physical Sequence Monotonic Alignment** using each packet's wire sequence header (`seq_id % 2100`) and evaluates causal Biquad filter state continuously from reset. This reduced reconstruction error across all 10,000 packets to exactly **$0.000000\text{ mV}$** ($0\text{ bit errors}$).

### 6.2 Data Replay Source
* The 10,000 transmitted packets replay **pre-stored WESAD Subject S2 Baseline ECG samples stored in microcontroller flash memory** (`WESAD_S2_RAW_ECG` in [`embedded_stm32/src/wesad_test_samples.c`](embedded_stm32/src/wesad_test_samples.c), 2,100 single-precision float samples looping cyclically).
* It does **not** stream from live analog ADC electrodes.

---

## 7. Numerical Lyapunov Spectrum Statistics for HC1

*Evidence file:* [`results/m4d_lyapunov_benchmark.txt`](results/m4d_lyapunov_benchmark.txt)

* **Dynamical System Parameters:** $a = 15.81, b = 2.76, c = 86.03, d = -9.07, r = 10.79, dt = 0.0025\text{ s}$
* **Theoretical System Divergence:** $\nabla \cdot \mathbf{F} = \frac{\partial \dot{x}}{\partial x} + \frac{\partial \dot{y}}{\partial y} + \frac{\partial \dot{z}}{\partial z} + \frac{\partial \dot{w}}{\partial w} = -a - b + d = -15.81 - 2.76 + (-9.07) = \mathbf{-27.640000}$
* **Empirical Exponent Statistics (Evaluated across 10 distinct runs spanning $dt \in [0.00125, 0.005]$, $T \in [200\text{s}, 1000\text{s}]$, and 3 initial conditions):**
  * $\lambda_1$: Mean = **$+0.4432$** (Min = $+0.4182$, Max = $+0.5282$, Std = $0.0324$)
  * $\lambda_2$: Mean = **$+0.2710$** (Min = $+0.2361$, Max = $+0.2995$, Std = $0.0209$)
  * $\lambda_3$: Mean = $-0.0018$ (Min = $-0.0042$, Max = $+0.0013$)
  * $\lambda_4$: Mean = $-28.3524$ (Min = $-28.4652$, Max = $-28.3004$)
  * Kaplan-Yorke Fractal Dimension ($D_{KY}$): Mean = **$3.0251$** (Min = $3.0233$, Max = $3.0290$, Std = $0.0017$)
  * Numerical divergence convergence: $\sum_{i=1}^4 \lambda_i = -27.639989$ (absolute error $\approx 1.11 \times 10^{-5}$ relative to $-27.640000$).

---

## 8. Claims Audit Resolution

| Claim ID | Prior Claim Statement | Audit Finding | Revised Status | Replacement Value / Action |
| :---: | :--- | :--- | :---: | :--- |
| **C-02** | Baseline normalization accuracy jump: $+10.79\text{ pp}$ | The +10.79 percentage-point value originated from $92.36\% - 81.57\%$ (13-feature calibrated vs raw, all-baseline anchor, documented in `results/Feature_Group_Comparison.csv` and `results/FINAL_Development_Model_Comparison.csv`: $92.35955\% - 81.57303\% = +10.78652\% \approx +10.79\%$). In the leak-free protocol, it is replaced by the pre-specified 8-feature paired contrast between $N=10$ calibrated (90.17%) and uncalibrated Control (a) (78.64%) on the 295-window set, which yields $+11.53\text{ pp}$ [95% CI: $+5.07, +18.06$]. | **RETIRED** | State leak-free gain on 295 windows: $+11.53\text{ pp}$ [95% CI: $+5.07, +18.06$] at $N=10$, or $+6.78\text{ pp}$ [95% CI: $+0.68, +13.22$] at $N=5$. |
| **C-05** | Biquad execution cost: $\approx 318$ CPU cycles ($1.87~\mu\text{s}$) | Analytical $5 \times 5$ MAC estimate from prior draft. | **CONTRADICTED** | Replaced with measured physical DWT value: **251 cycles mean (min 249, max 281), $1.476~\mu\text{s}$ at 170 MHz** (21.1% faster than estimated). |
| **C-06** | Biquad CPU utilization: $0.065\%$ at 350 Hz | Calculated from analytical $1.87~\mu\text{s}$ estimate. | **CONTRADICTED** | Replaced with measured physical DWT value: **$0.0517\%$ CPU load** ($1.476~\mu\text{s} / 2857.14~\mu\text{s}$). |

---

## 9. Literature Protocol Verification & Status

* **Lin et al. (2023):**
  * *Status:* **REMOVED**.
  * *Finding:* Cited in references as "Deep multimodal wearable physiological stress detection on the WESAD dataset", *Biomedical Signal Processing and Control*, vol. 84, 104751 (2023). However, official Elsevier records verify that Article 104751 in Volume 84 corresponds to an unrelated paper on postauricular PPG. Because the cited article does not exist as described, Lin et al. (2023) and its 88.50% figure have been completely removed from Table IV/VI in both manuscripts and the README.
* **Bobade & Vani (2020):**
  * *Status:* **CORRECTED & QUOTED DIRECTLY FROM PAPER**.
  * *Finding:* Published in Proceedings of the Second International Conference on Inventive Research in Computing Applications (ICIRCA 2020), Coimbatore, India, pp. 511-517, IEEE. DOI: 10.1109/ICIRCA48905.2020.9182908 (venue is ICIRCA, not ICACCI or IMWUT).
  * *Paper Results:* Evaluated Multimodal physiological data (Chest + Wrist: EDA, BVP, TEMP, ECG, RESP, EMG, ACC) using an ANN under a random 70-30 train-test split, achieving **84.32% accuracy** for 3-class classification (Amusement vs. Baseline vs. Stress) and **95.21% accuracy** for binary classification (Stress vs. Non-stress). The paper did not report an ECG-only model.
* **Action:**
  * Lin et al. is deleted from Table IV/VI and references.
  * Bobade & Vani is retained with its verified ICIRCA citation and quoted directly with its multimodal paper numbers (84.32% 3-class, 95.21% binary).
  * Schmidt et al. (2018) is retained as the verified foundational WESAD reference (Multimodal Chest, 80.34% 3-class).

---

## 10. Privacy & Sanitization Sweep Report

* **Patterns Checked:** Usernames, absolute filesystem paths, file URL schemes, hardware serial numbers, and telephone numbers.
* **Files Touched and Sanitized:**
  1. [`results/verification/pre_paper_validation/pre_paper_validation_report.md`](results/verification/pre_paper_validation/pre_paper_validation_report.md) (line 278): Replaced hardcoded local python interpreter path with generic environment indicator.
  2. [`PHASE1_REPORT.md`](PHASE1_REPORT.md) (lines 66 and 221): Removed physical ST-Link serial number and sanitized workstation path.
* **Result:** Zero occurrences of private user workstation paths or physical ST-Link hardware serials remain across all code, documentation, and results. Git history was preserved without rewriting.

---

## 11. Documentation & File Link Integrity

* Fixed relative link prefixes in moved documentation guides:
  * [`docs/EXECUTION_GUIDE.md`](docs/EXECUTION_GUIDE.md)
  * [`docs/PROJECT_IMPLEMENTATION_SYSTEMATIC_GUIDE.md`](docs/PROJECT_IMPLEMENTATION_SYSTEMATIC_GUIDE.md)
  * [`docs/PROJECT_QUICK_REFERENCE.md`](docs/PROJECT_QUICK_REFERENCE.md)
* Automated link verification confirmed **100% of internal markdown file links** resolve to valid, existing repository targets.
