# ECG_STRESS_DETECTION — Quick Reference Guide

> **Purpose:** Master reference document for the entire project. Consult this file to understand the architecture, algorithms, dataset, firmware, benchmarks, and scripts without needing to re-read every individual source file.

---

## 1. Project Overview & Core Problem

### The Clinical & Engineering Challenge
* **Domain:** Wearable Internet of Medical Things (IoMT), Biosignal Processing, Affective State Recognition.
* **Objective:** Real-time detection of acute psychological stress from single-lead electrocardiography (ECG) on an ultra-low-power ARM Cortex-M4 microcontroller.
* **The Core Problem — Inter-Individual Baseline Heterogeneity:**
  * Resting autonomic tone (heart rate, HRV) varies dramatically across subjects (e.g., an athlete's resting HR may be 52 BPM while a sedentary person's is 80 BPM).
  * Fixed global thresholds (e.g., classifying stress if $\text{HR} > 80\text{ BPM}$) fail to generalize across unseen subjects.
* **The Solution — Relative Baseline Normalization:**
  * Each feature is transformed into a fractional deviation relative to the subject's resting baseline ($B_s$):
    $$X^* = \frac{X - B_s}{|B_s| + \epsilon}, \quad \text{with } \epsilon = 10^{-6}$$
  * Evaluated strictly under **15-Fold Leave-One-Subject-Out Cross-Validation (LOSO-CV)**.
  * Boosts classification accuracy from **81.57% to 92.13% (+10.56%)** and stress F1-score from **73.03% to 88.29% (+15.26%)** at primary $\tau = 0.50$.
  * Exploratory threshold ($\tau = 0.35$) reaches **92.36% accuracy**:
    * **Python canonical pipeline:** 92.36% accuracy, 89.10% F1, 86.88% sensitivity, 95.44% specificity.
    * **MATLAB historical pipeline:** 92.36% accuracy, 89.03% F1, 86.25% sensitivity, 95.79% specificity.

---

## 2. End-to-End System Architecture

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             PHYSICAL HARDWARE TIER                               │
│              STM32G474RE Nucleo-64 (ARM Cortex-M4 @ 16 MHz HSI / 170 MHz PLL)     │
│                                                                                  │
│   WESAD Flash ECG Data ──► 350 Hz SysTick ──► 5-Stage Direct Form I Biquad IIR  │
│                                                            │                     │
│                                                            ▼                     │
│   Software CRC-16 ◄── Telemetry Scrambler/Cipher ◄── 20-Byte Frame Packer        │
│          │            (HC1 M-4DCHS or 32b Xorshift32)                            │
└──────────┼───────────────────────────────────────────────────────────────────────┘
           │ USB-UART (115,200 baud, 8-N-1) @ 350 Hz
           ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                          HOST INGESTION & PARSER TIER                            │
│                  Python 3.10+ (python/stm32_telemetry_receiver.py)               │
│                                                                                  │
│   Byte Stream ──► Frame Sync (0xAA 0x55) ──► CRC-16 Check                        │
│                                                   │                              │
│                                                   ├──► Authorized Descrambler    │
│                                                   │           │                  │
│                                                   ▼           ▼                  │
│                                           Cipher Wire     Clean ECG Trace        │
│                                             Buffer            │                  │
└───────────────────────────────────────────────┬───────────────┼──────────────────┘
                                                │               ▼
                                                │      Adaptive R-Peak Detection   │
                                                │      (find_peaks + Refractory)   │
                                                │               │                  │
                                                │               ▼                  │
                                                │      HRV Feature Extraction      │
                                                │      (8 to 13 biomarkers)        │
                                                │               │                  │
                                                │               ▼                  │
                                                │      Relative Normalization      │
                                                │      X* = (X - Bs) / (|Bs| + eps)│
                                                │               │                  │
                                                │               ▼                  │
                                                │      Calibrated Classifier       │
                                                │      (tau = 0.35 / 0.50)         │
                                                ▼               ▼                  │
┌──────────────────────────────────────────────────────────────────────────────────┐
│                         CLINICAL & SECURITY DASHBOARD                            │
│                              Streamlit (demo/app.py)                             │
│                                                                                  │
│   🟢 Authorized Clinical View: Decrypted Lead-II ECG, Stress Gauge, HRV Cards    │
│   🕵️ Eavesdropper Intercept View: Wire Static (H ~ 7.998 b/B), Locked Metrics    │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Dataset & Signal Processing Pipeline

### 3.1 Dataset: WESAD (Wearable Stress and Affect Detection)
* **Cohort:** 15 subjects ($S2$ through $S17$, excluding non-existent $S12$, 12 males, 3 females).
* **Modality:** Single-lead chest ECG (modified Lead-II orientation) via RespiBAN chest strap ($f_s = 700\text{ Hz}$, downsampled to $350\text{ Hz}$ for microcontroller).
* **Phases:** Baseline resting (20 min), TSST acute cognitive stress (10 min), Amusement (10 min), Meditation (20 min).
* **Standardized Segments:** 445 complete, non-overlapping 60-second windows (**160 Stress** vs. **285 Calm/Resting**).

### 3.2 Filtering Pipeline
1. **Offline (MATLAB / Python):**
   * 4th-order zero-phase Butterworth bandpass ($0.5 - 40\text{ Hz}$) via forward-backward `filtfilt`.
   * 50 Hz digital notch filter ($Q = 30$) to remove powerline interference.
2. **Online Embedded (STM32 Cortex-M4):**
   * Causal 5-stage Direct Form I Biquad IIR cascade at $350\text{ Hz}$:
     * Stages 1–4: Four 2nd-order sections (SOS) synthesizing 8-pole 4th-order Butterworth bandpass ($0.5 - 40\text{ Hz}$).
     * Stage 5: 2nd-order notch filter ($f_0 = 50\text{ Hz}$, $Q = 30$).
   * State memory: 4 floats per stage; executes in $\approx 1.87\ \mu\text{s}$ per sample at 170 MHz ($\approx 4.4\ \mu\text{s}$ at 16 MHz HSI).

### 3.3 Adaptive R-Peak Detection
* Noise floor estimation: $\text{Noise Floor} = 1.4826 \cdot \text{MAD}(|x - \text{median}(x)|)$.
* Prominence threshold: $\ge 3.0 \cdot \text{Noise Floor}$ (offline) or $\max(0.15\text{ mV},\, 1.8 \cdot \text{MAD})$ (real-time).
* Refractory period: Min distance $= 350\text{ ms}$ (max detectable $\text{HR} \approx 171\text{ BPM}$).
* Physiological interval gating: $300\text{ ms} \le RR_i \le 1500\text{ ms}$ ($40 - 200\text{ BPM}$).

### 3.4 Primary HRV Biomarkers (8 Core Features)
1. **`MeanHR`**: Average heart rate in BPM.
2. **`SDNN`**: Standard deviation of NN intervals in ms (total autonomic regulation).
3. **`RMSSD`**: Root mean square of successive differences in ms (parasympathetic vagal tone).
4. **`pNN50`**: Percentage of adjacent NN intervals differing by $>50\text{ ms}$ (vagal modulation reserve).
5. **`MeanRR`**: Average NN interval in ms.
6. **`RR_CV`**: Coefficient of variation ($\text{SDNN} / \text{MeanRR}$).
7. **`RR_IQR`**: Interquartile range of NN intervals in ms.
8. **`HR_IQR`**: Interquartile range of heart rate in BPM.

---

## 4. Machine Learning & Benchmarking Results

### 4.1 Strict 15-Fold LOSO-CV Protocol
* **Canonical ML Source of Truth:** Python ([`python/train_loso_ml_benchmark.py`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/python/train_loso_ml_benchmark.py)), generating [`results/ML_Model_Benchmark_LOSO.csv`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/results/ML_Model_Benchmark_LOSO.csv) and [`results/ML_Predictions_LOSO.csv`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/results/ML_Predictions_LOSO.csv).
* **MATLAB Status:** Secondary/historical classifier implementation using custom unregularized gradient descent. Its τ=0.35 metrics differ slightly from the Python implementation because the optimization and regularization methods differ.
* **Live Dashboard Model:** Pooled deployment inference engine with threshold τ=0.35, streaming safety floors, feature clipping, and optional subject-specific baseline calibration. It is not the same as the 15-fold LOSO evaluation model.
* In each fold $k$, all data from subject $S_k$ is withheld.
* Model and scaler train strictly on the other 14 subjects.
* For the test subject, resting baseline windows establish $B_{S_k}$; no stress labels are ever leaked during training.

### 4.2 Multi-Model Performance Comparison (15-Fold LOSO)

| Model Architecture | Accuracy | Balanced Acc | Stress F1 | Sensitivity (Recall) | Specificity | Precision | ROC-AUC | PR-AUC |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Logistic Regression (Primary $\tau = 0.50$)** | 92.13% | 90.02% | 88.29% | 82.50% | **97.54%** | **94.96%** | 0.9493 | **0.9467** |
| **Logistic Reg. (Python canonical, $\tau = 0.35$)** | **92.36%** | **91.16%** | **89.10%** | **86.88%** | 95.44% | 91.45% | 0.9493 | 0.9467 |
| *Logistic Reg. (MATLAB historical, $\tau = 0.35$)* | *92.36%* | *91.02%* | *89.03%* | *86.25%* | *95.79%* | *92.00%* | *0.9494* | *0.9467* |
| **MLP Neural Net (32, 16)** | 91.69% | 89.95% | 87.87% | 83.75% | 96.14% | 92.41% | 0.9375 | 0.9327 |
| **SVM (RBF Kernel)** | 91.46% | 89.50% | 87.42% | 82.50% | 96.49% | 92.96% | **0.9524** | 0.9441 |
| **Random Forest (100 Trees)** | 90.34% | 88.48% | 85.90% | 81.88% | 95.09% | 90.34% | 0.9426 | 0.9301 |
| **Extra Trees Classifier** | 89.89% | 86.90% | 84.43% | 76.25% | **97.54%** | 94.57% | 0.9494 | 0.9391 |
| **HistGradientBoosting** | 89.21% | 87.33% | 84.31% | 80.62% | 94.04% | 88.36% | 0.9459 | 0.9375 |
| *Uncalibrated Baseline LR* | *81.57%* | *78.76%* | *73.03%* | *68.75%* | *88.77%* | *77.46%* | *0.8512* | *0.7812* |

### 4.3 Feature Importance & Physiological Explainability
* **Dominant Stress Drivers:**
  * $\Delta\text{MeanRR}$: Largest degradation upon permutation ($\Delta\text{AUC} = 0.1766$, $\text{OR} = 0.0645$, showing interval shortening is the strongest marker).
  * $\Delta\text{MeanHR}$: Strongest positive odds multiplier ($\text{OR} = 5.65$, reflecting sympathetic chronotropic acceleration).
  * $\Delta\text{pNN50}$: High predictive importance ($\text{OR} = 4.08$, vagal withdrawal).
* **Calm / Protective Marker:**
  * $\Delta\text{SDNN}$: Protective odds ratio ($\text{OR} = 0.46 < 1.0$), reflecting preserved autonomic variability at rest.
* **Non-Responder Analysis (Subject S2):**
  * S2 achieved 0.0% stress recall (0/10) because their physiological heart rate showed almost zero reactivity during TSST ($\Delta\text{MeanHR} \approx 0$). Highlights need for multimodal sensing (ECG + EDA + Respiration) for edge cases.

---

## 5. Embedded Firmware & IoMT Security Layer

### 5.1 Microcontroller Specifications (STM32G474RE)
* **Core:** ARM Cortex-M4 with single-precision hardware FPU.
* **Clock:** Runs on default 16 MHz HSI (or 170 MHz with PLL).
* **Interrupt Cadence:** SysTick at $350\text{ Hz}$ ($2.857\text{ ms}$ period, $45,713$ counts @ 16 MHz).
* **Flash / RAM Footprint:** $18.9\text{ KB}$ Flash ($3.61\%$), $1.7\text{ KB}$ RAM ($1.30\%$).

### 5.2 Telemetry Packet Framing (20 Bytes)
```
[0xAA 0x55] [Ver: 0x01] [Flags: 0x05] [Seq: 2B] [Timestamp: 4B] [Raw ECG: 4B] [Filt ECG: 4B] [CRC16: 2B]
```
* **Flags:** `0x01` = Encrypted, `0x04` = 4D Hyperchaos (`0x05` = both active).
* **Payload:** Bytes 10–17 (raw float + filtered float) encrypted in-place.
* **Checksum:** CRC-16-CCITT over bytes 2–17.

### 5.3 Encryption Modes
1. **Mode 2: 4D Coupled Hyperchaotic System (HC1 M-4DCHS)**
   $$\dot{x} = a(y-x) + w, \quad \dot{y} = cx - xz + dy, \quad \dot{z} = xy - bz, \quad \dot{w} = -rx$$
   * Parameters: $a = 15.81, b = 2.76, c = 86.03, d = -9.07, r = 10.79$, step size $dt = 0.0025\text{ s}$.
   * Two positive Lyapunov exponents: $\lambda_1 \approx +0.438, \lambda_2 \approx +0.254$; Kaplan-Yorke dimension $D_{KY} \approx 3.024$.
   * Single-precision RK4 numerical integration on ARM Cortex-M4.
   * Per-packet Nonce perturbation + Cipher Feedback (CFB) diffusion.
   * Parity: **HC1 Python/C parity is currently failed and unverified; the latest test produced cross-language mismatches and NaN reconstruction values.**
2. **Mode 1: 32-Bit Discrete Stream Scrambler**
   * Marsaglia Xorshift32 + Golden Ratio Weyl sequence ($+0\text{x}61C88647$) + CBC diffusion.
   * Execution cost: 32 clock cycles ($\approx 2.0\ \mu\text{s}$ at 16 MHz).
3. **Hardware-in-the-Loop (HIL) Verification:**
   * 5,000 consecutive physical packets captured over USB-UART (COM10 @ 115,200 baud).
   * 0 CRC errors, 0 dropped frames, 100.00% exact plaintext float recovery.
   * Wire Shannon entropy: $H = 7.9982\text{ bits/byte}$ (eavesdroppers see pure high-entropy noise).

---

## 6. Project Directory Map & File Functions

```
ECG_STRESS_DETECTION/
├── README.md                                  # Complete research showcase & documentation
├── PROJECT_QUICK_REFERENCE.md                 # THIS FILE: Master quick-reference guide
├── PROJECT_IMPLEMENTATION_SYSTEMATIC_GUIDE.md # Exhaustive technical reference & build guide
├── EXECUTION_GUIDE.md                         # Operational guide for running all pipelines
├── ROADMAP.md                                 # Project roadmap and future milestones
├── requirements.txt                           # Python dependencies
├── start_dashboard.bat                        # Launcher for Streamlit dashboard
├── flash_firmware.bat                         # Firmware flashing script
│
├── demo/                                      # Interactive Dashboard
│   ├── app.py                                 # Streamlit 4-tab clinical & IoMT dashboard
│   └── sample_data/                           # WESAD sample waveforms & metadata (.npz, .json)
│
├── python/                                    # Machine Learning & Host Telemetry Suite
│   ├── train_loso_ml_benchmark.py             # 15-fold LOSO-CV benchmark across 6 ML models
│   ├── explainability_feature_importance.py   # Permutation importance & odds ratios
│   ├── m4d_hyperchaos.py                      # 4D hyperchaotic dynamical system & RK4 solver
│   ├── verify_m4d_parity.py                   # C-Python cryptographic parity verification
│   ├── stm32_telemetry_receiver.py            # Serial COM port receiver, CRC checker & descrambler
│   ├── simulate_stm32_stream.py               # Virtual telemetry streamer (no hardware required)
│   ├── compute_lyapunov_spectrum.py           # Variational RK4 + QR Lyapunov exponent solver
│   ├── extract_ecg_labels.py                  # WESAD pickle extractor to .mat / .csv
│   └── plot_ml_evaluation.py                  # Generates publication benchmark figures
│
├── matlab/                                    # Signal Processing & Modeling Suite
│   ├── DEMO_stress_detection.m                # Interactive Pan-Tompkins visualizer
│   ├── TWENTY_NINE_project_dashboard.m        # Generates master 6-panel research dashboard
│   ├── 01_data_inspection/                    # Raw signal loading & annotation inspection
│   ├── 02_preprocessing/                      # Filtering, window segmentation (process_ecg_window.m)
│   ├── 03_hrv_extraction/                     # QRS detection & HRV feature computation
│   ├── 04_analysis/                           # Statistical tests, boxplots, QC audits
│   ├── 05_modeling/                           # LOSO cross-validation, feature ablation, ROC
│   └── 06_final_results/                      # Master evaluation & reporting scripts
│
├── embedded_stm32/                            # Bare-Metal STM32 Firmware Source
│   ├── src/
│   │   ├── main_stm32.c                       # SysTick 350 Hz loop, UART register writes
│   │   ├── ecg_dsp_filter.c                   # 5-stage Direct Form I Biquad IIR filter
│   │   └── telemetry_protocol.c               # M-4DCHS hyperchaos, Xorshift32, CRC-16
│   ├── include/                               # Firmware headers & register definitions
│   ├── STM32G474RETX_FLASH.ld                 # Memory linker script
│   └── build_and_flash.bat                    # Compilation and flashing script
│
├── STM32G474_ECG_Telemetry/                   # STM32CubeIDE Project Eclipse Workspace
│   ├── Inc/ & Src/                            # Mirror firmware source for CubeIDE
│   └── flash_firmware.bat                     # STM32 Programmer CLI script
│
├── paper/                                     # Publication Assets & Manuscript
│   ├── Personalized_ECG_HRV_Stress_Detection_LOSO_STM32_4D_Hyperchaotic_Telemetry_v3.pdf # Compiled IEEE research paper PDF
│   ├── figures/                               # Publication vector and PNG figures
│   └── *.pdf                                  # Compiled conference / journal preprints
│
└── results/                                   # Empirical Artifacts & Benchmarks
    ├── FINAL_Model_Metrics.csv                # Calibrated logistic regression scorecard
    ├── ML_Model_Benchmark_LOSO.csv            # 6-classifier comparative benchmark results
    ├── ML_Feature_Importance_Permutation.csv  # Permutation drops & odds ratios
    ├── WESAD_HRV_features_expanded.csv        # 445-window extracted feature matrix
    └── figures/                               # Exported charts & ROC/PR curves
```

---

## 7. Quick Execution Cheatsheet

### 7.1 Launching the Interactive Web Dashboard
```bash
# Option A: Double-click start_dashboard.bat, or run:
streamlit run demo/app.py --server.port 8501
```
* Access at `http://localhost:8501`.
* Tab 1 lets you stream in real-time from either **Virtual Simulation** (no hardware needed) or **Physical STM32 Nucleo** on COM port.

### 7.2 Running Machine Learning & Benchmark Scripts
```bash
# 1. Run 15-fold LOSO benchmark across all 6 ML classifiers:
python python/train_loso_ml_benchmark.py

# 2. Run feature explainability & permutation importance:
python python/explainability_feature_importance.py

# 3. Verify C <-> Python cryptographic parity:
python python/verify_m4d_parity.py

# 4. Compute Lyapunov exponent spectrum:
python python/compute_lyapunov_spectrum.py
```

### 7.3 Streaming from Physical Hardware via Serial
```bash
# Listen on COM10 @ 115200 baud, decrypt and verify CRC:
python python/stm32_telemetry_receiver.py --port COM10 --baud 115200
```

### 7.4 Flashing STM32 Firmware
```cmd
# Connect STM32G474RE Nucleo-64 via USB, then run:
cd embedded_stm32
flash_firmware.bat
# LD2 (green LED) should blink at 1 Hz indicating active 350 Hz telemetry
```

---

## 8. Key Numbers at a Glance

| Item | Value |
| :--- | :--- |
| **Cohort** | 15 WESAD subjects ($S2 - S17$) |
| **Analysis Windows** | 445 standardized 60s windows (160 stress, 285 calm) |
| **Validation** | Strict 15-fold Leave-One-Subject-Out (LOSO-CV) |
| **Primary Accuracy** | **92.13%** ($\tau = 0.50$, primary) / **92.36%** ($\tau = 0.35$, exploratory) |
| **Stress F1-Score** | Primary ($\tau = 0.50$): **88.29%**<br>• Python canonical ($\tau = 0.35$): **89.10%**<br>• MATLAB historical ($\tau = 0.35$): **89.03%** |
| **ROC-AUC / PR-AUC** | **0.9493** / **0.9467** |
| **Sensitivity / Specificity** | Primary ($\tau = 0.50$): **82.50%** / **97.54%**<br>• Python canonical ($\tau = 0.35$): **86.88%** / **95.44%**<br>• MATLAB historical ($\tau = 0.35$): **86.25%** / **95.79%** |
| **Accuracy Gain from Baseline Calibration** | **+10.56%** ($81.57\% \rightarrow 92.13\%$ at $\tau = 0.50$) / **+10.79%** ($81.57\% \rightarrow 92.36\%$ at $\tau = 0.35$) |
| **Microcontroller** | ARM Cortex-M4 (STM32G474RE @ 16 MHz HSI / 170 MHz PLL) |
| **Sampling Rate / Telemetry Cadence** | 350 Hz ($T_s = 2.857\text{ ms}$) |
| **Filter Execution Time** | $1.87\ \mu\text{s}$ per sample at 170 MHz (0.065% CPU load) |
| **Packet Size & Baud Rate** | 20 bytes @ 115,200 baud (UART 8-N-1) |
| **Physical HIL Verification** | 5,000 packets, 0 CRC errors, 100% exact recovery |
| **Wire Shannon Entropy** | 7.9982 bits/byte (99.98% of 8.000 limit) |
