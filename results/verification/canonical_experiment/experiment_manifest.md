# Canonical Experiment Manifest: WESAD ECG Stress Detection

**Experiment Identifier:** `EXP-WESAD-ECG-LOSO-CANONICAL-2026`  
**Project:** Personalized Electrocardiographic and HRV Dynamics for Acute Stress Detection  
**Status:** Canonical Reference Specification  
**Timestamp:** 2026-10-02T10:20:00+05:30  
**Storage Location:** `results/verification/canonical_experiment/`  

---

## 1. Authoritative Pipeline Definition

The canonical research pipeline for this project is strictly defined by the following sequential stages:

```
[1. WESAD Raw Lead-II ECG (700 Hz)]
           │
           ▼
[2. MATLAB Signal Preprocessing & R-Peak Detection]
    - Zero-phase 4th-order Butterworth bandpass (0.5 - 40 Hz, filtfilt)
    - MAD adaptive noise-floor peak detection (prominence >= 3.0 * noise floor)
    - Physiological interval gating (300 ms <= RR <= 1500 ms)
           │
           ▼
[3. Canonical Feature Dataset (445 Windows, 15 Subjects)]
    - Segmented into complete 60s windows, 60s hop (0% overlap)
    - 13 computed time-domain / statistical HRV metrics
    - Archived in results/WESAD_HRV_features_expanded.csv
           │
           ▼
[4. Python 15-Fold LOSO Machine Learning Benchmark]
    - 8 core physiological features [MeanHR, SDNN, RMSSD, pNN50, MeanRR, RR_CV, RR_IQR, HR_IQR]
    - Subject-specific relative baseline calibration: delta_x = (x - mu_base) / max(|mu_base|, 1e-6)
    - StandardScaler fitted strictly on training fold (14 subjects)
    - 6 scikit-learn classifiers evaluated across 15 held-out subject folds
           │
           ▼
[5. Canonical Decision Thresholds & Evaluation]
    - Primary Research Benchmark: tau = 0.50 (Acc: 92.13%, F1: 88.29%, Sens: 82.50%, Spec: 97.54%)
    - Exploratory Clinical Point: tau = 0.35 (Acc: 92.36%, F1: 89.03%, Sens: 86.25%, Spec: 95.79%)
           │
           ▼
[6. Bare-Metal STM32 Edge IoMT Deployment & Physical HIL Telemetry]
    - 5-stage Direct Form I Biquad IIR filter (170 MHz SYSCLK, 1.87 us/sample)
    - HC1 4D Coupled Hyperchaotic Encryption (M-4DCHS) with per-packet nonce perturbation
    - Verified physical HIL capture over ST-Link Virtual COM Port (350.02 Hz, 0 CRC errors, 0.0 mV error)
```

---

## 2. Experimental Cohort & Windowing Specifications

| Parameter | Canonical Value | Description / Protocol |
| :--- | :--- | :--- |
| **Total Cohort** | 15 Subjects | S2, S3, S4, S5, S6, S7, S8, S9, S10, S11, S13, S14, S15, S16, S17 |
| **Excluded Subjects** | S1, S12 | Excluded during original WESAD acquisition (*Schmidt et al., 2018*) due to sensor hardware failure |
| **Total Valid Windows** | 445 Windows | Complete non-overlapping analysis windows across all 15 participants |
| **Baseline Windows** | 285 Windows (64.04%) | Seated neutral reading protocol ($\approx 19$ windows per subject) |
| **Stress Windows** | 160 Windows (35.96%) | Trier Social Stress Test (TSST: public speaking + mental arithmetic; 10–12 windows per subject) |
| **Window Duration** | 60.0 Seconds | Standard clinical interval required for stable time-domain HRV estimation |
| **Window Hop Step** | 60.0 Seconds | Hop step equal to window duration enforces **0.0% overlap** (zero temporal autocorrelation) |
| **Raw ECG Sampling Rate** | 700 Hz | RespiBAN Professional single-lead Lead-II chest strap |
| **Telemetry Sampling Rate** | 350 Hz | Nominal timer interrupt rate on STM32 edge processing node |

---

## 3. Signal Processing & Feature Extraction Specifications

### 3.1 Digital Filtering
- **Offline Extraction (MATLAB):** 4th-order zero-phase Butterworth bandpass filter (`filtfilt`) with cutoff frequencies at $0.5\text{ Hz}$ (respiratory/motion baseline wander attenuation) and $40.0\text{ Hz}$ (myoelectric noise attenuation).
- **Online Edge Node (STM32 C Firmware):** 5-stage Direct Form I cascaded Biquad IIR filter ($4\times\text{SOS}$ Butterworth bandpass 0.5–40 Hz $+ 1\times\text{SOS}$ 50 Hz powerline notch filter, $Q=30$). Estimated execution time: $\approx 318$ CPU cycles ($\approx 1.87~\mu\text{s}$ at 170 MHz SYSCLK, consuming 0.065% of the $2.857\text{ ms}$ inter-sample budget).

### 3.2 R-Peak Detection & Physiological Gating
- Local noise floor is dynamically estimated via Median Absolute Deviation (MAD):
  $$\text{Noise Floor} = 1.4826 \times \text{median}\left(\left|x - \text{median}(x)\right|\right)$$
- Adaptive prominence threshold: $\text{Prominence} \ge 3.0 \times \text{Noise Floor}$.
- Refractory blanking period: $350\text{ ms}$ ($\text{HR}_{\max} \le 171\text{ BPM}$).
- RR interval boundary gating: $0.30\text{ s} \le RR_i \le 1.50\text{ s}$ ($40\text{--}200\text{ BPM}$). Windows with $< 5$ valid beats are discarded.

### 3.3 Feature Definitions & Core Representation
The expanded feature extraction produces 13 statistical and time-domain features. For the finalized primary machine learning benchmark, an 8-feature representation is evaluated:

$$\mathbf{X} = [\text{MeanHR},\; \text{SDNN},\; \text{RMSSD},\; \text{pNN50},\; \text{MeanRR},\; \text{RR}_{\text{CV}},\; \text{RR}_{\text{IQR}},\; \text{HR}_{\text{IQR}}]$$

Units in canonical CSV: `MeanHR` (BPM), `SDNN` (seconds), `RMSSD` (seconds), `pNN50` (%), `MeanRR` (seconds), `RR_CV` (ratio), `RR_IQR` (seconds), `HR_IQR` (BPM).

---

## 4. Normalization & Zero-Leakage Cross-Validation Protocol

1. **Subject-Specific Relative Transformation:**
   For each physiological feature $x$, the value is expressed as a fractional shift relative to the subject's resting baseline centroid $\mu_{\text{base}}$:
   $$\Delta x = \frac{x - \mu_{\text{base}}}{\max(|\mu_{\text{base}}|, 10^{-6})}$$
2. **Zero-Leakage Training/Test Boundary:**
   - In fold $k \in \{1, \dots, 15\}$, the supervised classifier is trained strictly on data from the remaining 14 subjects.
   - For test subject $k$, baseline calibration $\mu_{\text{base}}^{(k)}$ is computed **strictly from that test subject's own resting baseline windows**. No test stress windows or labels are ever exposed to the training fold.
3. **Z-Score Scaling:**
   `sklearn.preprocessing.StandardScaler` is fitted strictly on the training fold $X_{\text{train}}$ and subsequently applied to transform both $X_{\text{train}}$ and $X_{\text{test}}$.

---

## 5. Machine Learning Architectures & Parameters

All classifiers are seeded with `random_state = 42` to guarantee strict mathematical determinism:

1. **Logistic Regression (Primary Model):**
   - Solver: `liblinear` (Coordinate Descent)
   - Regularization: L2 Ridge penalty, inverse strength $C = 1.0$
   - Tolerance: $10^{-4}$
2. **Support Vector Machine (RBF):**
   - Kernel: Radial Basis Function (`rbf`)
   - Cost: $C = 1.5$, $\gamma = \text{'scale'}$, `probability = True`
3. **Random Forest:**
   - Trees: $N = 100$, `max_depth = 6`, `min_samples_split = 4`
4. **Extra Trees:**
   - Trees: $N = 100$, `max_depth = 6`, `min_samples_split = 4`
5. **HistGradientBoosting:**
   - Iterations: $N = 100$, `max_depth = 4`, `learning_rate = 0.08`
6. **Multi-Layer Perceptron (MLP):**
   - Hidden Layers: $(32, 16)$, `activation = 'relu'`, `solver = 'adam'`
   - Learning Rate: $\alpha = 0.005$, L2 penalty $\alpha = 0.01$, `max_iter = 1000`

---

## 6. Authoritative Primary vs. Exploratory Decision Thresholds

| Dimension | Primary Research Threshold ($\tau = 0.50$) | Exploratory Clinical Point ($\tau = 0.35$) |
| :--- | :---: | :---: |
| **Role in Study** | **Authoritative Primary Scientific Benchmark** | **Exploratory Sensitivity-Prioritized Point** |
| **Optimization Method** | Uncalibrated theoretical midpoint ($P \ge 0.50$) | Empirical ROC sweep maximizing sensitivity |
| **Accuracy** | **92.13%** (410 / 445 windows) | **92.36%** (411 / 445 windows) |
| **F1-Score** | **88.29%** | **89.03%** (MATLAB) / **89.10%** (Python) |
| **Sensitivity (Recall)** | **82.50%** (132 / 160 stress windows) | **86.25%** (138 / 160) / **86.88%** (139 / 160) |
| **Specificity** | **97.54%** (278 / 285 calm windows) | **95.79%** (273 / 285) / **95.44%** (272 / 285) |
| **Precision** | **94.96%** | **92.00%** (MATLAB) / **91.45%** (Python) |
| **Balanced Accuracy** | **90.02%** | **91.02%** (MATLAB) / **91.16%** (Python) |
| **ROC-AUC** | **0.9493** | **0.9494** |
| **PR-AUC** | **0.9467** | **0.9467** |
| **Confusion Matrix** | $\text{TP}=132, \text{FP}=7, \text{TN}=278, \text{FN}=28$ | $\text{TP}=138, \text{FP}=12, \text{TN}=273, \text{FN}=22$ (MATLAB) |
| **Clinical Rationale** | Minimizes false positive alarms ($\text{FP}=7$) | Increases stress detection sensitivity ($\text{FN}=22$) |

---

## 7. Canonical File Hashes (SHA-256)

All dataset and result files are cryptographically pinned:

```text
0405170bb05f4b597d8ec46eea47c2fbb474144fc5f3fcfbd5027b04c70ac2a7  results/WESAD_HRV_features_expanded.csv
10e68062edaac8a2083917a8397bba2614cdb54a9eccd33c1008355d48210172  results/ML_Model_Benchmark_LOSO.csv
dd469804ea92a7ee4c99149476aeb87095b3cac3a8da34a25cdafb89db3dba9a  results/ML_Predictions_LOSO.csv
3f20ef8f326535aa4b08cd81368a419314254797fa521fa0798dafe5377e9794  results/FINAL_Model_Metrics.csv
65ce699ddefd3235fb344bf8c446207c5e6c73790cfd3b730316a6095ea1823e  results/FINAL_Project_Summary.csv
ff03a00e44eda115699202d574d4074cfdebbc4a75c7df1695c6f5883348ca73  results/Threshold_Analysis.csv
3f138c9d67ea6d805d67f37fd445dbbb035195bfbd9d071acfc8833ba8361316  results/Personalized_Classifier_Predictions.csv
aec81d75c88e75182f413f790680319706df76f5d08cc7c28add2bcf539fae92  results/Stress_Classifier_Predictions.csv
436aa838a1e4b2bff47712b2a874bb83be8d15facb700e8eb10771f2288855cf  results/Feature_Group_Comparison.csv
e9e16bfed05f75706be16fb2a4da7c844985cb4f25cb2482081bc5401335ab91  results/Personalized_Feature_Ablation.csv
6da7ef69d846c95a161c6c6b49a33fe7c6122029fc413bfc8d9dd110c419f11b  results/ML_Feature_Importance_Permutation.csv
ed4b97b3e7279dc0f6d2add3a21b1ddf45347dbc9e8bfa21f1f48ac86657edc1  embedded_stm32/STM32G474_HC1_Telemetry.bin
2c729fc0adcb3b0cd1a41a6ddb0a504783ef741b566a2a5f867318780a716c65  results/verification/hc1_hardware_hil/hardware_raw_packets.bin
151bc7335c607c0a36b0bbc5ee664d492796368d58314a475217e247cdc74155  results/verification/hc1_hardware_hil/firmware_replay_reference.npz
349c6f769d7d9e2def1433a93175857f5e9a35ee0ffa081deaaac6104e5c962e  demo/sample_data/ecg_samples.npz
da0e33abfc395bc93d9d7f80afe353388ab8784cf27e0849a46f0410ca040b29  demo/sample_data/samples_meta.json
```

---

## 8. Verified Software & Compiler Environments

- **MATLAB:** Version 26.1.0.3312084 (R2026a) Update 4
- **Python:** 3.14.3 (tags/v3.14.3:323c59a) AMD64 on Windows 11 Enterprise (Build 10.0.26200-SP0)
- **Scikit-Learn:** 1.8.0
- **NumPy:** 2.4.3
- **Pandas:** 3.0.1
- **SciPy:** 1.17.1
- **Streamlit:** 1.64.0
- **Host C Compiler:** MinGW.org GCC 6.3.0
- **Embedded ARM Toolchain:** GNU Tools for STM32 14.3.1 (`arm-none-eabi-gcc 14.3.rel1.20251027-0700`)
