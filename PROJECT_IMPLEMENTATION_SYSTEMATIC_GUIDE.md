# Systematic Implementation Guide: End-to-End Cyber-Physical IoMT ECG Stress Detection & Lightweight Edge Telemetry Obfuscation System

**Author & Developer:** Mukesh Yadav  
**Platform Architecture:** ARM Cortex-M4 (STM32G474RE @ 16 MHz HSI) + Python 3.10+ / Streamlit Real-Time Telemetry Engine  
**Clinical Dataset Benchmark:** WESAD (Wearable Stress and Affect Detection, N=15, 15-Fold LOSO-CV)  
**Target Research Group / Prospective Faculty Outreach:** Prof. Noriyasu Homma & Dr. Norihiro Sugita (Tohoku University, Graduate School of Engineering & Biomedical Engineering)  
**Verification Status:** Validated on Physical Hardware (NUCLEO-G474RE on COM10 @ 350 Hz continuous streaming)

---

## Table of Contents
1. [Executive Summary & High-Level Architecture](#1-executive-summary--high-level-architecture)
2. [Physiological Signal Processing & WESAD Dataset Pipeline](#2-physiological-signal-processing--wesad-dataset-pipeline)
3. [Personalized Baseline Calibration & Machine Learning Benchmark](#3-personalized-baseline-calibration--machine-learning-benchmark)
4. [Embedded Edge Firmware Architecture (STM32G474RE)](#4-embedded-edge-firmware-architecture-stm32g474re)
5. [32-Bit Discrete Lightweight Telemetry Scrambling (IoMT Obfuscation Layer)](#5-32-bit-discrete-lightweight-telemetry-scrambling-iomt-obfuscation-layer)
6. [Host Telemetry Ingestion Engine & Python Protocol](#6-host-telemetry-ingestion-engine--python-protocol)
7. [Interactive Clinical & Eavesdropper Security Dashboard](#7-interactive-clinical--eavesdropper-security-dashboard)
8. [Empirical Verification & Hardware Benchmarks](#8-empirical-verification--hardware-benchmarks)
9. [Step-by-Step Reproduction & Build Guide](#9-step-by-step-reproduction--build-guide)
10. [Academic References & Notation](#10-academic-references--notation)

---

## 1. Executive Summary & High-Level Architecture

This project implements a complete, edge-to-cloud **Cyber-Physical Internet of Medical Things (IoMT)** framework for real-time acute psychological stress detection from continuous electrocardiographic (ECG) telemetry. The system addresses three core engineering and clinical objectives:

1. **The Inter-Individual Baseline Heterogeneity Problem**: Resting autonomic parameters vary widely across human populations. Fixed decision boundaries fail to generalize. We address this using **Subject-Specific Relative Baseline Normalization** evaluated strictly under **15-Fold Leave-One-Subject-Out Cross-Validation (LOSO-CV)**.
2. **Hard Real-Time Edge Processing**: Continuous biopotential streaming requires deterministic, sample-by-sample filtering on resource-constrained microcontrollers. We implement a **5-stage cascaded Biquad IIR digital filter (Direct Form I)** running inside a **350 Hz SysTick interrupt** on an ARM Cortex-M4 microcontroller.
3. **Biometric Privacy & Visual Eavesdropping Prevention**: ECG waveforms carry unique biometric signatures and sensitive mental health indicators. We deploy an on-chip **32-Bit Discrete Stream Scrambler (Marsaglia Xorshift32 + Golden Ratio Weyl Sequence with per-packet Nonce CBC diffusion)** executing in **32 CPU clock cycles ($\approx 2.0\ \mu\text{s}$ at 16 MHz)** with zero dynamic memory overhead, masking the signal into high-entropy pseudo-random noise ($H \approx 7.98\text{ bits/byte}$) to prevent visual snooping on open serial lines.

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    PHYSICAL HARDWARE TIER                                       │
│                                 (STM32G474RE @ 16 MHz HSI Core)                                 │
│                                                                                                 │
│  [WESAD S2 Lead-II ECG (Flash)] ──▶ [350 Hz SysTick Loop] ──▶ [5-Stage Direct Form I Biquad]   │
│                                                                           │                     │
│                                                                           ▼                     │
│  [Software CRC-16-CCITT] ◀── [32b Xorshift32+Weyl Scrambler] ◀── [Biometric Voltage Framing]    │
│            │                                                                                    │
└────────────┼────────────────────────────────────────────────────────────────────────────────────┘
             │ 20-Byte Binary Frame @ 350 Hz (115,200 Baud / Polled UART)
             ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   HOST TELEMETRY INGESTION TIER                                 │
│                                  (Python 3.10+ / stm32_telemetry_receiver)                      │
│                                                                                                 │
│  [Thread-Safe Serial Connection] ──▶ [Frame Sync: 0xAA 0x55] ──▶ [CRC-16 Verification]          │
│                                                                            │                    │
│                                                                            ▼                    │
│  [Eavesdropper Intercept View] ◀── [Cipher Buffer]           [Keystream Descrambling]           │
│  (Scrambled Static, LOCKED)                                                │                    │
│                                                                            ▼                    │
│                                      [QRS Peak Detection (SciPy find_peaks) & HRV Engine]       │
│                                                                            │                    │
│                                                                            ▼                    │
│                                      [Personalized Baseline Calibrated Stress Classifier]       │
└────────────────────────────────────────────┼────────────────────────────────────────────────────┘
                                             │
                                             ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                  CLINICAL MONITORING DASHBOARD                                  │
│                                  (Streamlit / demo/app.py)                                      │
│                                                                                                 │
│  • 🟢 Authorized Clinical View: Decrypted Lead-II Tracing, Calibrated Stress Dial, 6 HRV Cards  │
│  • 🕵️ Eavesdropper Intercept View: Scrambled Wire Static, Entropy Gauge, KEY LOCKED Protocol    │
│  • Dual-Link: Physical NUCLEO-G474RE COM10 Stream OR Simulated Multi-Subject WESAD Replay        │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Physiological Signal Processing & WESAD Dataset Pipeline

### 2.1 Dataset Specifications
* **Dataset**: WESAD (Wearable Stress and Affect Detection), public reference benchmark.
* **Subjects**: $N = 15$ healthy adult participants ($S2$ through $S17$, excluding $S1$ due to sensor malfunction).
* **Sensor & Placement**: RespiBAN chest-worn bio-instrumentation rig.
* **Signal Channel**: Single-lead chest electrocardiography (modified Lead-II orientation).
* **Acquisition Sampling Rate**: 700 Hz (standardized to 350 Hz for edge microcontroller deployment).
* **Experimental Protocol Conditions**:
  - `Baseline`: 20-minute quiet resting period in sitting/reading position.
  - `Stress`: Trier Social Stress Test (TSST), combining public speaking and mental arithmetic challenges under interpersonal evaluation.
  - `Amusement`: Passive video-watching relaxation period.
* **Standardized Epochs**: 445 standardized 60-second windows with 50% overlap ($N = 285$ Baseline/Calm, $N = 160$ Stress).

### 2.2 Digital Pre-Processing
1. **Offline Preprocessing (MATLAB & Python Training)**:
   - A zero-phase 4th-order Butterworth bandpass filter ($0.5 - 40.0\text{ Hz}$) removes baseline wander ($<0.5\text{ Hz}$) and muscle tremor ($>40\text{ Hz}$) using `filtfilt` forward-backward filtering.
   - An offline notch filter at $50.0\text{ Hz}$ ($Q = 30$) eliminates alternating current (AC) power grid hum.
2. **Online Embedded Preprocessing (STM32 Edge Firmware)**:
   - Embedded real-time processing cannot run non-causal zero-phase filtering. Instead, a **causal 5-stage Direct Form I Biquad IIR filter** is executed sample-by-sample at 350 Hz.

### 2.3 R-Peak Detection & NN Interval Conditioning
Ventricular depolarizations (R-peaks) are extracted using adaptive prominence thresholding:
1. **Adaptive Prominence Floor**:
   - **MATLAB Offline Pipeline** (`process_ecg_window.m`):
     $$\text{Noise Floor} = 1.4826 \cdot \text{median}(|x - \text{median}(x)|) = 1.4826 \cdot \text{MAD}$$
     $$\text{Min Prominence} = 3.0 \cdot \text{Noise Floor} \approx 4.45 \cdot \text{MAD}$$
   - **Python Real-Time Telemetry Pipeline** (`stm32_telemetry_receiver.py`):
     $$\text{Min Prominence} = \max(0.15\text{ mV},\, 1.8 \cdot \text{MAD})$$
2. **Physiological Refractory Blanking**: A minimum temporal separation of $350\text{ ms}$ (corresponding to a maximum physiological heart rate of $\approx 171\text{ BPM}$) prevents dual-triggering on elevated T-waves.
3. **Physiological RR Interval Filtering**: Inter-beat intervals outside physiological limits are discarded:
   $$0.30\text{ s} \le RR_i \le 1.50\text{ s} \quad (40\text{ to } 200\text{ BPM})$$
   Clean normal-to-normal ($NN$) intervals are preserved directly without synthetic interpolation.

### 2.4 Extracted Time-Domain & Statistical HRV Features
From each standardized analysis window, 13 morphological and statistical biomarkers are computed:

| Feature Symbol | Definition | Physiological Correlate |
| :--- | :--- | :--- |
| **`MeanHR`** | Average Heart Rate (BPM) | Overall cardiovascular exertion & chronotropic state |
| **`MedianHR`** | Median Heart Rate (BPM) | Robust measure of central heart rate tendency |
| **`StdHR`** | Standard Deviation of Heart Rate | Broad autonomic dynamic spread |
| **`MinHR` / `MaxHR`** | Extrema of Heart Rate | Dynamic cardiovascular dynamic range |
| **`MeanRR`** | Average $NN$ Interval (ms) | Cardiac cycle period |
| **`MedianRR`** | Median $NN$ Interval (ms) | Non-parametric beat interval center |
| **`SDNN`** | Standard Deviation of $NN$ intervals (ms) | Total autonomic regulatory capacity |
| **`RMSSD`** | Root Mean Square of Successive Differences (ms) | **Primary marker of parasympathetic (vagal) tone** |
| **`pNN50`** | Percentage of intervals differing by $>50\text{ ms}$ | Vagal parasympathetic braking reserve |
| **`RR_CV`** | Coefficient of Variation of $NN$ ($\frac{\text{SDNN}}{\text{MeanRR}}$) | Normalized autonomic variance |
| **`RR_IQR`** | Interquartile Range of $NN$ intervals (ms) | Robust non-parametric interval dispersion |
| **`HR_IQR`** | Interquartile Range of Heart Rate (BPM) | Robust non-parametric rate dispersion |

---

## 3. Personalized Baseline Calibration & Machine Learning Benchmark

### 3.1 The Inter-Individual Baseline Problem
In uncalibrated physiological computing, global thresholds produce unacceptable misclassifications due to broad inter-individual variance:
* A naturally athletic individual (resting HR = 52 BPM) under severe stress may reach 75 BPM.
* An individual with elevated basal tone (resting HR = 80 BPM) is calm at 80 BPM.
* A static global threshold (e.g., classifying stress whenever $\text{HR} > 75\text{ BPM}$) would misclassify the athletic patient as calm during panic, while permanently misdiagnosing the second patient as stressed at rest.

### 3.2 Mathematical Formulation of Relative Normalization
Let $X \in \mathbb{R}^{D}$ denote an uncalibrated feature vector from subject $s$. Let $\mathcal{W}_{\text{base}}^{(s)}$ denote the set of resting baseline windows for that subject. The individual's personal reference baseline vector $B_s$ is:

$$B_s = \frac{1}{|\mathcal{W}_{\text{base}}^{(s)}|} \sum_{k \in \mathcal{W}_{\text{base}}^{(s)}} X_k^{(s)}$$

Every subsequent analysis window is normalized relative to this baseline:

$$X^* = \frac{X - B_s}{|B_s| + \epsilon}$$

where $\epsilon = 10^{-6}$ prevents numerical division singularities.

```
       [Uncalibrated Features: X]
                   │
                   ▼
       [Compute Delta: X - B_s]
                   │
                   ▼
     [Divide by Basal Scale: |B_s|]
                   │
                   ▼
   [Normalized Feature Vector: X*] ──▶ Decoupled from resting physiology!
```

> **Methodological Note on Baseline Pooling:** In the current experimental setup, $B_s$ is computed by pooling all baseline windows across the 20-minute resting session for each subject. While this strictly prevents cross-subject training leakage under LOSO-CV, clinical deployments should compute $B_s$ strictly from an initial 3–5 minute intake calibration phase before classifying subsequent unknown time epochs.

### 3.3 Strict 15-Fold Leave-One-Subject-Out Cross-Validation (LOSO-CV)
To evaluate generalizability to unseen patients:
1. In each fold $k \in \{1, \dots, 15\}$, all windows belonging to subject $S_k$ are completely withheld as the test set.
2. The feature scaler and classifier are fitted strictly on the remaining 14 subjects.
3. The model predicts the held-out subject $S_k$ using their baseline $B_{S_k}$.
4. Predictions from all 15 folds are pooled to calculate overall benchmark metrics.

### 3.4 Ground-Truth Multi-Model Benchmark Results
The table below reflects the exact experimental results recorded in [`results/ML_Model_Benchmark_LOSO.csv`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/results/ML_Model_Benchmark_LOSO.csv) and [`results/FINAL_Model_Metrics.csv`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/results/FINAL_Model_Metrics.csv):

| Model Architecture | Hyperparameters | Accuracy | Stress F1 | ROC-AUC | Sensitivity | Specificity | PR-AUC |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Calibrated Logistic Reg. (MATLAB)** | `C=1.0, τ=0.35` | **92.36 %** | **89.03 %** | 0.9494 | **86.25 %** | 95.79 % | 0.9467 |
| **Logistic Regression (Python)** | `C=1.0, liblinear, τ=0.5` | 92.13 % | 88.29 % | 0.9493 | 82.50 % | **97.54 %** | **0.9467** |
| **MLP Neural Net** | `hidden=(32, 16), lr=0.005, α=0.01` | 91.69 % | 87.87 % | 0.9375 | 83.75 % | 96.14 % | 0.9327 |
| **SVM (RBF Kernel)** | `C=1.5, gamma=scale` | 91.46 % | 87.42 % | **0.9524** | 82.50 % | 96.49 % | 0.9441 |
| **Random Forest** | `n_trees=100, max_depth=6` | 90.34 % | 85.90 % | 0.9426 | 81.88 % | 95.09 % | 0.9301 |
| **Extra Trees** | `n_trees=100, max_depth=6` | 89.89 % | 84.43 % | 0.9494 | 76.25 % | **97.54 %** | 0.9391 |
| **HistGradientBoosting** | `max_iter=100, max_depth=4, lr=0.08` | 89.21 % | 84.31 % | 0.9459 | 80.62 % | 94.04 % | 0.9375 |
| *Uncalibrated Baseline Logistic Reg.* | *Default unscaled features* | *81.57 %* | *73.03 %* | *0.8512* | *68.75 %* | *88.77 %* | *0.7812* |

**Key Observations**:
* **SVM (RBF Kernel) achieved the highest ROC-AUC (0.9524)** of all evaluated classifiers, indicating superior probability calibration across the full decision sweep.
* **Calibrated Logistic Regression achieved the highest overall Accuracy (92.36%) and Stress F1-score (89.03%)** at calibrated decision threshold $\tau = 0.35$.
* Relative baseline normalization provides an absolute improvement of **+10.79% in Accuracy** and **+16.00% in Stress F1** over uncalibrated modeling.

---

## 4. Embedded Edge Firmware Architecture (STM32G474RE)

### 4.1 Target Microcontroller Specifications
* **Target Board**: NUCLEO-G474RE (STMicroelectronics)
* **Microcontroller**: STM32G474RE (ARM Cortex-M4 with single-precision FPU).
* **Active Clock Frequency**: **16 MHz HSI (High-Speed Internal RC Oscillator)**.  
  *(Note: The STM32G4 core supports up to 170 MHz via PLL. The current verified bare-metal firmware runs on the reset default 16 MHz HSI, which simplifies clock tree configuration and minimizes power consumption).*
* **On-Chip Memory**: 512 KB Flash, 128 KB SRAM.
* **SysTick Configuration**: Loaded with $45,713$ counts ($16,000,000 / 350 - 1$) for deterministic 350 Hz interrupt cadence ($2.857\text{ ms}$ period).
* **Toolchain**: ARM GNU Toolchain / STM32CubeIDE bare-metal C compiler.

### 4.2 Firmware Source Code Layout
The verified firmware lives at `C:\Users\YASH\Desktop\projects\STM32_PROJECTS\STM32G474_ECG_Telemetry/`:
```
STM32G474_ECG_Telemetry/
├── Inc/
│   ├── ecg_dsp_filter.h            # Biquad filter structure, coefficient declarations
│   ├── telemetry_protocol.h        # 20-byte packet framing & scrambler prototypes
│   └── wesad_test_samples.h        # WESAD Lead-II test sample buffer declarations
├── Src/
│   ├── ecg_dsp_filter.c            # 5-stage Direct Form I Biquad IIR filter
│   ├── main.c                      # Bare-metal register init, SysTick 350Hz loop, UART
│   ├── syscalls.c / sysmem.c       # Minimal runtime stub support
│   ├── telemetry_protocol.c        # Xorshift32+Weyl stream scrambler & software CRC-16
│   └── wesad_test_samples.c        # 2,100 WESAD Subject S2 Lead-II samples in Flash
├── STM32G474RETX_FLASH.ld          # Memory map linker script
└── flash_firmware.bat              # One-click programming batch script
```

### 4.3 5-Stage Direct Form I Biquad IIR Filter
The embedded conditioning filter is implemented in `ecg_dsp_filter.c` as a 5-stage cascaded Direct Form I Biquad IIR filter:
* **Stages 1–4**: 4th-order Butterworth bandpass ($0.5 - 40.0\text{ Hz}$ at $F_s = 350\text{ Hz}$).
* **Stage 5**: 2nd-order notch filter centered at $50.0\text{ Hz}$ ($Q = 30$).

For each second-order section $k \in \{1, \dots, 5\}$:
$$y_k[n] = b_0 x_k[n] + b_1 x_k[n-1] + b_2 x_k[n-2] + (-a_1) y_k[n-1] + (-a_2) y_k[n-2]$$
State memory maintains 4 historical floats ($x[n-1], x[n-2], y[n-1], y[n-2]$) per stage. Execution takes $\approx 71$ clock cycles ($\approx 4.4\ \mu\text{s}$ at 16 MHz).

### 4.4 Binary Telemetry Framing (20-Byte Packet)
Data is serialized into a deterministic 20-byte binary frame:

```
 0        1        2        3        4        5        6        7        8        9
+--------+--------+--------+--------+--------+--------+--------+--------+--------+--------+
|  0xAA  |  0x55  |  0x01  | Flags  |     seq_id      |          timestamp_ms           |
+--------+--------+--------+--------+--------+--------+--------+--------+--------+--------+
|  Sync Header    | Version| Status |  uint16_t (2B)  |          uint32_t (4B)          |
+-----------------+--------+--------+-----------------+---------------------------------+
 10       11       12       13       14       15       16       17       18       19
+--------+--------+--------+--------+--------+--------+--------+--------+--------+--------+
|            raw_ecg                |           filtered_ecg            |     CRC-16    |
+--------+--------+--------+--------+--------+--------+--------+--------+--------+--------+
|      float32_t (4 Bytes)          |       float32_t (4 Bytes)         |  uint16_t (2B)|
|   🔒 SCRAMBLED PAYLOAD (8B)       |    🔒 SCRAMBLED PAYLOAD (8B)      |   Plaintext   |
+-----------------------------------+-----------------------------------+---------------+
```

* `flags`: `0x01` indicates 32-bit discrete chaotic scrambling is active.
* `raw_ecg` & `filtered_ecg`: Scrambled on-chip prior to transmission.
* `crc16`: CRC-16-CCITT computed via a software bit-shift routine in `telemetry_protocol.c` over bytes 2 through 17.
* **UART Transmission**: Transmitted via polled register writes (`while(!(USART2_ISR & TXE)); USART2_TDR = b;`). At 115,200 baud, sending 20 bytes takes $\approx 1.74\text{ ms}$, operating well within the $2.857\text{ ms}$ SysTick period.

---

## 5. 32-Bit Discrete Lightweight Telemetry Scrambling (IoMT Obfuscation Layer)

### 5.1 Design Goal: Visual Privacy & Edge Feasibility
The goal of this layer is **lightweight signal obfuscation**:
1. Mask the cardiac waveform so that unauthorized serial sniffers or oscilloscope taps see only high-entropy static.
2. Prevent eavesdroppers from running R-peak detection or extracting mental stress states without the key.
3. Operate in microseconds without heavy math libraries, dynamic RAM, or multi-kilobyte code overhead.

> **Cryptographic Disclaimer:** This scheme is an **ultra-lightweight stream scrambler** based on an LFSR/Weyl PRNG with CBC diffusion. It is designed to prevent casual wire sniffing and visual biometric interception on low-power microcontrollers. It is **not** a NIST-certified cryptographic standard (such as AES-128/256 or ChaCha20) and is not intended to resist dedicated algebraic cryptanalysis.

### 5.2 Discrete 32-Bit Scrambler Formulation
The stream generator combines Marsaglia's Xorshift32 algorithm with an additive Golden Ratio Weyl sequence:

$$\text{Xorshift32: } \begin{cases} X_1 = X_0 \oplus (X_0 \ll 13) \\ X_2 = X_1 \oplus (X_1 \gg 17) \\ X_3 = X_2 \oplus (X_2 \ll 5) \end{cases}$$

$$\text{Weyl Addition: } S_{n+1} = (X_3 + 0\text{x}61C88647) \pmod{2^{32}}$$

### 5.3 Dynamic Per-Packet Nonce Seeding & CBC Chaining
To prevent identical voltages from generating identical scrambled bytes:

$$S_0 = \text{SECRET\_KEY} \oplus (\text{seq\_id} \cdot 0\text{x}45D9F3B) \oplus \text{timestamp\_ms}$$

$$\text{IV}_0 = \text{CHAOS\_INIT\_IV} \oplus (\text{seq\_id} \ \&\ 0\text{xFF})$$

where `SECRET_KEY = 0x9E3779B9` and `CHAOS_INIT_IV = 0x5A`.

The 8 biometric payload bytes (raw float + filtered float) undergo Cipher Block Chaining (CBC):
$$C_i = P_i \oplus (S_n \ \&\ 0\text{xFF}) \oplus C_{i-1} \quad \text{(Scrambling)}$$
$$P_i = C_i \oplus (S_n \ \&\ 0\text{xFF}) \oplus C_{i-1} \quad \text{(Descrambling)}$$

* **Execution Cost**: **32 clock cycles ($\approx 2.0\ \mu\text{s}$ at 16 MHz)**.
* **Wire Entropy**: **$H \approx 7.25 - 7.98\text{ bits/byte}$** (uniform byte spread).
* **Descrambling Precision**: **100% Bit-Exact IEEE 754 Floating-Point Identity**.

---

## 6. Host Telemetry Ingestion Engine & Python Protocol

Implemented in `python/stm32_telemetry_receiver.py`:

### 6.1 State-Machine Frame Parser
The `TelemetryParser` maintains an internal byte buffer:
1. **Sync Synchronization**: Locates `[0xAA, 0x55]`. Realigns on byte slip.
2. **CRC Verification**: Evaluates CRC-16-CCITT over the payload. Discards corrupted frames.
3. **Descrambling**: If `flags & 0x01`, derives keystream and descrambles biometric floats with zero precision loss.
4. **Cipher Preservation**: Preserves raw cipher bytes in `cipher_buf` for live eavesdropper visualization.

### 6.2 Thread-Safe Serial Management
To avoid Windows `PermissionError: Access is denied` across Streamlit session reruns:
* A singleton (`get_shared_serial_connection()`) manages port ownership under a threading lock.
* The open port handle is cached in `st.session_state["serial_conn"]` so Streamlit fragments can stream continuously without reopening the port.

---

## 7. Interactive Clinical & Eavesdropper Security Dashboard

Implemented in `demo/app.py` using Streamlit:

### 7.1 High-Speed Fragment Architecture
Using `@st.fragment(run_every="1s")`, the telemetry graph and metric cards refresh smoothly without unmounting UI widgets or resetting sidebar inputs.

### 7.2 Dual Operational Views

#### 1. 🟢 Authorized Clinical View (Decrypted Telemetry)
* **Lead-II Waveform Tracing**: Clean, real-time filtered cardiac waveform showing clear P-wave, QRS-complex, and T-wave morphology.
* **Calibrated Stress Dial ($\tau = 0.35$)**: An SVG needle gauge indicating real-time stress probability ($0\% - 100\%$) calibrated to the patient's individual resting baseline.
* **Live HRV Biomarkers Strip**: Displays real-time `Mean Heart Rate` (BPM), `RMSSD` (ms), `SDNN` (ms), `pNN50` (%), `Mean RR` (ms), and `Detected Beats`.

#### 2. 🕵️ Eavesdropper Intercept View (Raw Wire Ciphertext)
* **Scrambled Wire Waveform**: Displays dense pseudo-random static in pink/red (`#FF3366`) with zero visible cardiac morphology.
* **Security Status Card**: Displays `KEY LOCKED`, the wire Shannon entropy ($H \approx 7.25 - 7.98\text{ bits/byte}$), and cipher configuration.
* **Cryptographically Locked Biomarkers**: All HRV cards display **`🔒 LOCKED`** (*"Signal masked to noise"*, *"Key required for vagal tone"*, *"0 valid QRS complexes detected"*), demonstrating that downstream autonomic features cannot be extracted without the key.

---

## 8. Empirical Verification & Hardware Benchmarks

### 8.1 Memory Footprint (GNU Arm GCC -O2)
Extracted from `STM32G474_ECG_Telemetry.map`:
```
Memory Region         Used Size (Bytes)    Total Region Size    Memory Utilization
----------------------------------------------------------------------------------
FLASH (rx)                18,904 B             512 KB                3.61 %
RAM (xrw)                  1,704 B             128 KB                1.30 %
```
*Note: Flash footprint includes 2,100 pre-loaded Lead-II WESAD samples (`wesad_test_samples.o`, 8,400 bytes).*

### 8.2 Execution Timing Profile (350 Hz / 16 MHz HSI)

| Operation | Clock Cycles @ 16 MHz | Execution Time | % of 2.857 ms Period |
| :--- | :---: | :---: | :---: |
| 5-Stage Direct Form I Biquad | $\approx 71$ cycles | $\approx 4.4\ \mu\text{s}$ | $0.15\%$ |
| 32-Bit Xorshift32+Weyl Scrambler | $\approx 32$ cycles | $\approx 2.0\ \mu\text{s}$ | $0.07\%$ |
| Software CRC-16 Calculation | $\approx 640$ cycles | $\approx 40.0\ \mu\text{s}$ | $1.40\%$ |
| Polled UART Transmission (20 Bytes @ 115.2k) | Busy-Wait Loop | $\approx 1,736.0\ \mu\text{s}$ | $60.76\%$ |
| **Total Interrupt Execution Time** | — | **$\approx 1,782.4\ \mu\text{s}$** | **$62.38\%$** |

*Hardware Optimization Opportunity*: Migrating UART transmission to DMA will reduce CPU utilization from $62.38\%$ down to $<2\%$, freeing the core for power-saving sleep modes (`WFI`).

### 8.3 Hardware Telemetry Serial Verification (`COM10`)
* **Packets Ingested**: $>50,000$ consecutive frames verified.
* **Integrity Rate**: **100% Valid CRC-16-CCITT**.
* **Packet Drop Rate**: **$0.00\%$** under steady-state streaming.
* **Descrambling Precision**: Machine-epsilon identity ($|V_{\text{original}} - V_{\text{descrambled}}| \equiv 0.000000\text{ V}$).

---

## 9. Step-by-Step Reproduction & Build Guide

### 9.1 Hardware Prerequisites
* STM32 NUCLEO-G474RE development board connected via Micro-USB to PC.
* ST-Link Virtual COM Port driver installed (enumerated on `COM10` or similar).

### 9.2 Building & Flashing Firmware
1. Open the project in **STM32CubeIDE** (`File -> Open Projects from File System -> C:\Users\YASH\Desktop\projects\STM32_PROJECTS\STM32G474_ECG_Telemetry`).
2. Build the project (`Project -> Build Project` or `Ctrl + B`).
3. To flash the compiled `.bin` file directly to the board, run the included batch script:
   ```cmd
   cd "C:\Users\YASH\Desktop\projects\STM32_PROJECTS\STM32G474_ECG_Telemetry"
   flash_firmware.bat
   ```
   *(Alternatively, invoke `STM32_Programmer_CLI.exe -c port=SWD -w STM32G474_ECG_Telemetry.bin 0x08000000 -v -rst` directly).*
4. Verify that the green LED (`LD2`) blinks at 1 Hz, confirming active 350 Hz transmission.

### 9.3 Launching the Clinical Dashboard
1. Navigate to the research project root:
   ```powershell
   cd "C:\Users\YASH\Desktop\projects\RESEARCH PROJECTS\ECG_STRESS_DETECTION"
   ```
2. Start the Streamlit application:
   ```powershell
   python -m streamlit run demo/app.py --server.port 8501
   ```
3. Open **`http://localhost:8501`** in any web browser.
4. Select **`Physical USB COM Port`** (set to detected `COM10`).
5. Toggle **`Continuous Live Stream (Hospital Monitor)`** and explore both **`Authorized Clinical View`** and **`Eavesdropper Intercept View`**.

---

## 10. Academic References & Notation

1. **WESAD Dataset Benchmark**:
   > Schmidt, P., Reiss, A., Duerichen, R., Marberger, C., & Van Laerhoven, K. (2018). *Introducing WESAD, a multimodal dataset for wearable stress and affect detection.* Proceedings of the 20th ACM International Conference on Multimodal Interaction (ICMI '18), 400–408.
2. **Discrete Xorshift PRNGs**:
   > Marsaglia, G. (2003). *Xorshift RNGs.* Journal of Statistical Software, 8(14), 1–6.
3. **Heart Rate Variability Standards**:
   > Task Force of the European Society of Cardiology and the North American Society of Pacing and Electrophysiology. (1996). *Heart rate variability: standards of measurement, physiological interpretation, and clinical use.* Circulation, 93(5), 1043–1065.
4. **Prospective Outreach Context**:
   > Research portfolio prepared for academic review by **Prof. Noriyasu Homma** and **Dr. Norihiro Sugita** (Tohoku University, Department of Biomedical Engineering & Cybernetics).
