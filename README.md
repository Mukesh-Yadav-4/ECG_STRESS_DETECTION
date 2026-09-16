# Personalized Electrocardiographic and Heart Rate Variability Dynamics for Acute Stress Detection: A Leave-One-Subject-Out Benchmark on WESAD

[![MATLAB](https://img.shields.io/badge/MATLAB-R2022b%2B-orange.svg?style=flat-square&logo=mathworks)](https://www.mathworks.com/products/matlab.html)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=flat-square&logo=python)](https://www.python.org/)
[![Dataset: WESAD](https://img.shields.io/badge/Dataset-WESAD%20Benchmark-00629B.svg?style=flat-square)](https://archive.ics.uci.edu/dataset/465/wesad+wearable+stress+and+affect+detection)
[![Validation](https://img.shields.io/badge/Validation-15--Fold%20LOSO--CV-purple.svg?style=flat-square)]()
[![ROC-AUC](https://img.shields.io/badge/ROC--AUC-0.9494-007ACC.svg?style=flat-square)]()
[![Sensitivity](https://img.shields.io/badge/Sensitivity-86.25%25-2ea44f.svg?style=flat-square)]()
[![Specificity](https://img.shields.io/badge/Specificity-95.79%25-success.svg?style=flat-square)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-lightgrey.svg?style=flat-square)](LICENSE)

---

## Abstract

**Background:** Automated identification of acute psychosocial stress from non-invasive electrocardiography (ECG) is a fundamental pursuit in digital medicine, autonomic neuroscience, and wearable health diagnostics. However, clinical translation has historically been impeded by substantial inter-individual baseline heterogeneity: resting heart rate and basal vagal tone exhibit pronounced variance across subjects due to genetic, athletic, and circadian factors, inducing acute generalization collapse in standard, uncalibrated cross-subject machine learning classifiers.

**Methods:** This repository provides an end-to-end, reproducible computational framework developed in **MATLAB (R2022b+)** and **Python (3.10+)** to quantify, evaluate, and benchmark acute stress detection across all **15 subjects** ($N = 15$, 445 standardized 60-second windows) of the public **WESAD** (Wearable Stress and Affect Detection) benchmark dataset. Single-lead chest ECG acquired at $700\text{ Hz}$ via RespiBAN undergoes zero-phase 4th-order Butterworth bandpass filtering ($0.5 - 40\text{ Hz}$), Pan-Tompkins QRS detection, physiological RR interval artifact gating ($300 - 1500\text{ ms}$), and multi-domain feature extraction across time, frequency, and nonlinear Poincaré domains. To overcome inter-subject baseline bias, we introduce a **subject-specific differential baseline normalization ($\\Delta$-calibration)** formulation. All models are evaluated using strict **15-Fold Leave-One-Subject-Out Cross-Validation (LOSO-CV)**, ensuring complete independence between training cohorts and unseen test subjects.

**Results:** Baseline normalization yielded a decisive empirical advance, boosting cross-subject classification accuracy from $81.57\%$ to **$92.36\%$** ($+10.79\%$) and stress F1-score from $73.03\%$ to **$89.03\%$** ($+16.00\%$) relative to uncalibrated multi-domain feature baselines. At an operating decision threshold of $\tau = 0.35$, the calibrated detector achieves a receiver operating characteristic area under the curve (**ROC-AUC**) of **$0.9494$**, a precision-recall AUC (**PR-AUC**) of **$0.9467$**, a sensitivity (recall) of **$86.25\%$** ($138/160$ stress windows), and a specificity of **$95.79\%$** ($273/285$ non-stress windows). A comparative benchmark across 6 machine learning paradigms (Logistic Regression, Multilayer Perceptron, Support Vector Machines, Random Forests, Extra Trees, and Histogram Gradient Boosting) confirmed robust generalization with ROC-AUC $> 0.937$ across all architectures on unseen subjects. Permutation importance and standardized odds ratio analyses confirm that beat-to-beat interval compression ($\\Delta\text{MeanRR}$, odds ratio $= 0.065$, AUC drop $= 0.177$) and sympathetic rate elevation ($\\Delta\text{MeanHR}$, odds ratio $= 5.65$) alongside vagal tone withdrawal ($\\Delta\text{RMSSD}$) drive the physiological decision boundary.

---

## Master Project Dashboard

<p align="center">
  <img src="results/figures/FINAL_Project_Dashboard.png" width="98%" alt="Master Project Dashboard" />
  <br>
  <em><b>Figure 1: Comprehensive Research Dashboard.</b> Summary of the end-to-end WESAD study: (A) Four-stage model progression and ablation; (B) Subject-specific stress detection rates across all 15 subjects; (C) Calibrated 15-fold LOSO confusion matrix; (D) Cross-validated ROC curve ($\text{AUC} = 0.9494$); (E) Summary scorecard of clinical validation metrics; (F) Distribution of evaluated test windows per subject ($N = 445$).</em>
</p>

---

## 1. Physiological Foundations & Mathematical Formulation

### 1.1 Autonomic Nervous System Dynamics
Acute psychological and cognitive stress elicits a systemic autonomic response mediated by the autonomic nervous system (ANS):
1. **Sympathetic Nervous System (SNS) Activation:** Triggers systemic catecholamine release (epinephrine and norepinephrine), accelerating sinoatrial node pacing, shortening the cardiac cycle, and elevating low-frequency (LF) cardiac oscillations.
2. **Parasympathetic Nervous System (PNS) Withdrawal:** Mediated via the vagus nerve (cranial nerve X); acute stress induces rapid vagal withdrawal, precipitating an immediate collapse in beat-to-beat variability (RMSSD, pNN50, high-frequency [HF] spectral power).

### 1.2 The Inter-Individual Generalization Dilemma
A primary failure mode of biomedical wearable algorithms is the reliance on absolute, uncalibrated physiological thresholds. For instance, a resting heart rate of $80\text{ BPM}$ may indicate acute sympathetic arousal in an endurance-trained athlete whose baseline is $50\text{ BPM}$, yet represent a relaxed state in a sedentary individual whose baseline is $82\text{ BPM}$:

$$\text{Subject } A: \quad \text{HR}_{\text{rest}} = 54\text{ BPM}, \quad \text{HR}_{\text{stress}} = 74\text{ BPM} \quad (\Delta = +20\text{ BPM})$$
$$\text{Subject } B: \quad \text{HR}_{\text{rest}} = 78\text{ BPM}, \quad \text{HR}_{\text{stress}} = 98\text{ BPM} \quad (\Delta = +20\text{ BPM})$$

An uncalibrated classifier utilizing a static decision boundary (e.g., $\text{HR} > 75\text{ BPM}$) will misclassify Subject B as chronically stressed even at rest, while failing to detect stress in Subject A.

### 1.3 Mathematical Formulation of Differential Normalization
To decouple state-dependent autonomic transitions from tonic inter-subject baseline discrepancies, we formulate a subject-specific differential baseline transformation. Let $\mathbf{x}_i^{(s)} \in \mathbb{R}^D$ denote the $D$-dimensional feature vector extracted from the $i$-th analysis window of subject $s \in \{1, \dots, N\}$. Let $\mathcal{W}_{\text{base}}^{(s)}$ denote the set of indices corresponding exclusively to the resting baseline protocol phase for subject $s$:

$$\bar{\mathbf{x}}_{\text{baseline}}^{(s)} = \frac{1}{|\mathcal{W}_{\text{base}}^{(s)}|} \sum_{k \in \mathcal{W}_{\text{base}}^{(s)}} \mathbf{x}_k^{(s)}$$

The differential feature vector $\Delta \mathbf{x}_i^{(s)}$ is defined as:

$$\Delta \mathbf{x}_i^{(s)} = \mathbf{x}_i^{(s)} - \bar{\mathbf{x}}_{\text{baseline}}^{(s)}$$

Alternatively, when scaling by the intra-subject resting variance $\boldsymbol{\sigma}_{\text{baseline}}^{(s)}$:

$$\mathbf{z}_i^{(s)} = \frac{\mathbf{x}_i^{(s)} - \bar{\mathbf{x}}_{\text{baseline}}^{(s)}}{\boldsymbol{\sigma}_{\text{baseline}}^{(s)} + \boldsymbol{\epsilon}}$$

This mathematical transformation maps each subject's resting physiological state to the coordinate origin $\mathbf{0}$, transforming absolute metrics into relative autonomic perturbation vectors that generalize cleanly across unseen test subjects.

---

## 2. Experimental Cohort & Study Protocol

Experiments were conducted on the peer-reviewed **WESAD** benchmark dataset (*Schmidt et al., 2018*), collected under a strictly controlled laboratory protocol:
- **Cohort:** 15 healthy adult subjects ($S2 - S17$, excluding $S1$ and $S12$ due to sensor malfunction in the original trial; 12 males, 3 females, age: $27.5 \pm 2.4$ years).
- **Acquisition Hardware:** Chest-worn RespiBAN Professional telemetry system recording single-lead Lead-II ECG at a sampling frequency of $f_s = 700\text{ Hz}$.
- **Experimental Protocol Phases:**
  1. **Baseline Condition (20 min):** Neutral, seated relaxation reading neutral magazines.
  2. **Trier Social Stress Test (TSST):** Validated psychosocial laboratory stressor consisting of 5 minutes of public speaking anticipation/delivery facing a stern evaluative committee followed by 5 minutes of mental arithmetic (counting backward from 2,043 in steps of 17 with vocal restart penalties).
  3. **Amusement Condition (10 min):** Exposure to humorous video clips to induce positive valence.
  4. **Guided Meditation (20 min):** Controlled diaphragmatic breathing to re-establish homeostatic recovery.
- **Classification Paradigm:** Binary classification isolating **Acute Stress** ($N = 160$ valid windows) against **Non-Stress / Calm States** (Baseline + Amusement, $N = 285$ valid windows), totaling **445 standardized windows**.

<p align="center">
  <img src="results/figures/DEMO_Protocol_Timeline.png" width="95%" alt="WESAD Protocol Timeline" />
  <br>
  <em><b>Figure 2: Experimental Protocol and Telemetry Timeline.</b> Clinical dark-theme representation illustrating the temporal progression across Baseline, TSST Acute Stress, Amusement, and Meditation recovery phases.</em>
</p>

---

## 3. Digital Biosignal Processing (DSP) Pipeline

The end-to-end signal processing architecture transforms raw $700\text{ Hz}$ single-lead chest ECG into artifact-free Normal-to-Normal (NN) intervals through three modular stages:

```plaintext
Raw Chest ECG (fs = 700 Hz)
  │
  ▼
[Stage 1: Bandpass Conditioning] ──► 4th-Order Zero-Phase Butterworth (0.5 - 40 Hz)
  │                                   Suppresses DC wander, respiration (<0.5 Hz) & EMG/mains noise
  ▼
[Stage 2: Pan-Tompkins QRS Engine]
  │  ├── Five-Point Derivative: H(z) = (1/8T) * (-z^-2 - 2z^-1 + 2z^1 + z^2)
  │  ├── Non-Linear Squaring: y[n] = x^2[n] (accentuates steep QRS complexes)
  │  ├── Moving Window Integration: W = 150 ms (time integration over QRS duration)
  │  └── Adaptive Dual Thresholding + 200 ms Refractory Blanking
  ▼
[Stage 3: Physiological Quality Control]
  │  ├── Physiological Bounds: 300 ms <= NN <= 1500 ms (40 - 200 BPM)
  │  └── Ectopic Beat Gating & Local Median Filtering
  ▼
Clean Normal-to-Normal (NN) Interval Time Series
```

### 3.1 Raw Lead-II Electrocardiogram Morphology
The raw biosignal captures high-fidelity ventricular depolarization and repolarization morphology, with prominent P-waves, narrow QRS complexes, and T-waves:

<p align="center">
  <img src="results/figures/DEMO_Raw_ECG_LeadII.png" width="95%" alt="Raw ECG Lead-II Signal" />
  <br>
  <em><b>Figure 3: Lead-II Electrocardiogram Trace.</b> Clinical telemetry dark theme displaying a representative 10-second segment ($700\text{ Hz}$) with clearly resolved P-QRS-T complexes.</em>
</p>

### 3.2 Pan-Tompkins QRS Waveform Transformation
To reliably detect R-peaks under motion artifacts, the Pan-Tompkins algorithm executes sequential filtering, differentiation, squaring, and moving-window integration:

<p align="center">
  <img src="results/figures/DEMO_Pan_Tompkins_QRS_Detection.png" width="95%" alt="Pan-Tompkins QRS Detection" />
  <br>
  <em><b>Figure 4: Four-Stage Pan-Tompkins Waveform Processing.</b> (Top to Bottom): (1) Raw input ECG; (2) Zero-phase bandpass-filtered signal ($0.5 - 40\text{ Hz}$); (3) Squared 5-point derivative waveform; (4) Moving-window integrated signal ($W = 150\text{ ms}$) with detected fiducial R-peak markers (red circles).</em>
</p>

---

## 4. Feature Extraction Architecture

Standardized **60-second sliding analysis windows** with a **50% overlap (30-second step)** were extracted across each subject's experimental timeline. Within each window, a 13-dimensional multi-domain feature vector was computed:

| Domain | Mathematical Feature | Formal Definition / Physiological Description | Autonomic Mechanism |
| :--- | :--- | :--- | :--- |
| **Time** | **Mean HR** | $\frac{60}{N} \sum_{i=1}^N \frac{1}{NN_i}$ (Beats Per Minute) | Sinoatrial node pacing; sympathetic excitation |
| **Time** | **Mean RR** | $\frac{1}{N} \sum_{i=1}^N NN_i$ (Milliseconds) | Reciprocal cardiac period |
| **Time** | **SDNN** | $\sqrt{\frac{1}{N-1} \sum_{i=1}^N (NN_i - \overline{NN})^2}$ | Total autonomic variability |
| **Time** | **RMSSD** | $\sqrt{\frac{1}{N-1} \sum_{i=1}^{N-1} (NN_{i+1} - NN_i)^2}$ | Parasympathetic / vagal cardiac modulation |
| **Time** | **pNN50** | $\frac{1}{N-1} \sum_{i=1}^{N-1} \mathbb{I}(|NN_{i+1} - NN_i| > 50\text{ ms}) \times 100\%$ | Short-term vagal pulse dispersion |
| **Time** | **RR-IQR** | $\text{IQR}(NN) = Q_3(NN) - Q_1(NN)$ | Robust non-parametric interval spread |
| **Time** | **HR-IQR** | $\text{IQR}(\text{HR}) = Q_3(\text{HR}) - Q_1(\text{HR})$ | Robust heart rate dispersion |
| **Time** | **RR-CV** | $\frac{\text{SDNN}}{\text{Mean RR}}$ | Coefficient of variation (normalized dispersion) |
| **Frequency** | **VLF Power** | $\int_{0.0033}^{0.04} S(f) df$ (Welch PSD, Milliseconds$^2$) | Thermoregulation and renin-angiotensin tone |
| **Frequency** | **LF Power** | $\int_{0.04}^{0.15} S(f) df$ (Welch PSD, Milliseconds$^2$) | Baroreflex modulation; mixed sympathetic/parasympathetic |
| **Frequency** | **HF Power** | $\int_{0.15}^{0.40} S(f) df$ (Welch PSD, Milliseconds$^2$) | Respiratory Sinus Arrhythmia (RSA); pure vagal tone |
| **Frequency** | **LF/HF Ratio** | $\frac{\text{LF Power}}{\text{HF Power}}$ | Classical index of sympathovagal balance |
| **Nonlinear** | **Poincaré $SD_1$** | $\sqrt{\frac{1}{2} \text{Var}(NN_{i+1} - NN_i)}$ | Instantaneous beat-to-beat variability (parasympathetic) |
| **Nonlinear** | **Poincaré $SD_2$** | $\sqrt{2 \text{Var}(NN_i) - \frac{1}{2} \text{Var}(NN_{i+1} - NN_i)}$ | Long-term continuous autonomic variability |
| **Nonlinear** | **$SD_1/SD_2$** | $\frac{SD_1}{SD_2}$ | Nonlinear autonomic balance ratio |

---

## 5. Experimental Validation Protocol: 15-Fold LOSO-CV

To strictly prevent cross-subject data leakage and evaluate real-world generalization, we adopted a **Leave-One-Subject-Out Cross-Validation (LOSO-CV)** design:

```plaintext
Fold k (k = 1, ..., 15):
┌─────────────────────────────────────────────────────────┐
│ Training Cohort: 14 Subjects (All windows except Sub k) │ ──► Supervised Training
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│ Testing Cohort: Subject k (Held-out completely)         │ ──► Unseen Evaluation
└─────────────────────────────────────────────────────────┘
```

- **Zero Leakage:** In each fold $k$, the classifier has never observed biosignals, features, or labels from subject $k$.
- **Decision Threshold Optimization ($\\tau = 0.35$):** In clinical screening, false negatives (failing to detect severe acute stress) are substantially more costly than false positives. We calibrated the global decision threshold from default $\tau = 0.50$ to $\tau = 0.35$, improving sensitivity from $78.13\%$ to **$86.25\%$** while preserving an exceptional specificity of **$95.79\%$**.

---

## 6. Empirical Results & Performance Evaluation

### 6.1 Validated Primary Benchmark Scorecard
Evaluated across **445 independent windows** from all 15 subjects under 15-fold LOSO validation:

| Metric | Validated Empirical Result | Operational Interpretation |
| :--- | :---: | :--- |
| **Accuracy** | **92.36%** | $411$ out of $445$ total windows correctly classified |
| **Sensitivity / Recall** | **86.25%** | Successfully identified **138 of 160** acute stress episodes |
| **Specificity** | **95.79%** | Correctly identified **273 of 285** calm/resting windows |
| **Precision** | **92.00%** | When stress is flagged, probability of true positive is $92.00\%$ ($138/150$) |
| **F1-Score** | **89.03%** | Harmonic mean balancing recall and precision |
| **Balanced Accuracy** | **91.02%** | Unbiased accuracy across imbalanced class distributions |
| **ROC-AUC** | **0.9494** | Outstanding discriminative separability across all operating thresholds |
| **Confusion Matrix** | $\begin{bmatrix} 273 & 12 \\ 22 & 138 \end{bmatrix}$ | $\text{TN}=273, \text{FP}=12, \text{FN}=22, \text{TP}=138$ |

<table align="center">
  <tr>
    <td align="center" width="50%">
      <img src="results/figures/FINAL_Confusion_Matrix.png" width="100%" alt="Final Confusion Matrix" /><br />
      <em><b>Figure 5(a): Calibrated LOSO Confusion Matrix.</b> Demonstrating high true negative retention ($273/285, 95.8\%$) and strong stress capture ($138/160, 86.3\%$).</em>
    </td>
    <td align="center" width="50%">
      <img src="results/figures/FINAL_ROC_Curve.png" width="100%" alt="Final ROC Curve" /><br />
      <em><b>Figure 5(b): Cross-Validated ROC Curve.</b> Area under curve ($\text{AUC} = 0.9494$) with the selected operating threshold point ($\tau = 0.35$) highlighted.</em>
    </td>
  </tr>
</table>

---

## 7. Comparative Machine Learning Benchmark (Python Suite)

To benchmark the physiological features across diverse functional families, we implemented a standardized Python evaluation suite (`scikit-learn 1.3+`) comparing 6 canonical architectures under identical 15-Fold LOSO cross-validation:

| Model Paradigm | Accuracy | Balanced Acc | Sensitivity (Recall) | Specificity | Precision | F1-Score | ROC-AUC | PR-AUC |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Logistic Regression (L2)** | **92.13%** | **90.02%** | $82.50\%$ | **97.54%** | **94.96%** | **88.29%** | **0.9493** | **0.9467** |
| **Multilayer Perceptron (MLP)** | $91.69\%$ | $89.95\%$ | **83.75%** | $96.14\%$ | $92.41\%$ | $87.87\%$ | $0.9375$ | $0.9327$ |
| **Support Vector Machine (RBF)** | $91.46\%$ | $89.50\%$ | $82.50\%$ | $96.49\%$ | $92.96\%$ | $87.42\%$ | **0.9524** | $0.9441$ |
| **Random Forest (100 Trees)** | $90.34\%$ | $88.48\%$ | $81.88\%$ | $95.09\%$ | $90.34\%$ | $85.90\%$ | $0.9426$ | $0.9301$ |
| **Extra Trees Classifier** | $89.89\%$ | $86.90\%$ | $76.25\%$ | **97.54%** | $94.57\%$ | $84.43\%$ | $0.9494$ | $0.9391$ |
| **HistGradientBoosting** | $89.21\%$ | $87.33\%$ | $80.62\%$ | $94.04\%$ | $88.36\%$ | $84.31\%$ | $0.9459$ | $0.9375$ |

<p align="center">
  <img src="results/figures/ML_Model_Benchmark_Bars.png" width="95%" alt="ML Benchmark Bars" />
  <br>
  <em><b>Figure 6: Multi-Model Benchmark Comparison.</b> Grouped performance metrics across all 6 machine learning architectures under 15-fold LOSO cross-validation on unseen subjects.</em>
</p>

### 7.1 Multi-Model Diagnostic Discrimination: ROC and PR Profiles

<table align="center">
  <tr>
    <td align="center" width="50%">
      <img src="results/figures/ML_Model_Comparison_ROC.png" width="100%" alt="ML ROC Curves" /><br />
      <em><b>Figure 7(a): Diagnostic ROC Curves.</b> Demonstrating tight, robust discriminative boundaries across linear and nonlinear architectures ($\text{AUC} \in [0.937, 0.952]$).</em>
    </td>
    <td align="center" width="50%">
      <img src="results/figures/ML_Model_Comparison_PR.png" width="100%" alt="ML PR Curves" /><br />
      <em><b>Figure 7(b): Precision-Recall Curves.</b> Evaluating performance under natural clinical class prevalence ($P = 0.360$) against the theoretical no-skill baseline.</em>
    </td>
  </tr>
</table>

### 7.2 Confusion Matrix Grid Across All 6 Paradigms

<p align="center">
  <img src="results/figures/ML_Confusion_Matrices_Grid.png" width="98%" alt="ML Confusion Matrices Grid" />
  <br>
  <em><b>Figure 8: 2×3 Multi-Model Confusion Matrix Grid.</b> Showing consistent high-specificity retention ($> 94\%$) and solid recall ($> 80\%$) across linear, neural, kernel, and ensemble models on unseen subjects.</em>
</p>

---

## 8. Ablation Studies & Biomechanical Explainability

### 8.1 Model Progression & Feature Ablation
To systematically isolate the source of performance gains, we evaluated 4 successive model iterations under identical 15-fold LOSO conditions:

| Iteration | Feature Representation | Accuracy | F1-Score | Sensitivity | Specificity | Scientific Finding |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| **M1** | Raw Mean Heart Rate (Uncalibrated) | $77.08\%$ | $64.34\%$ | $61.25\%$ | $85.96\%$ | Baseline rate fails due to wide resting HR variance ($50-95\text{ BPM}$). |
| **M2** | 4 Time-Domain Metrics (Uncalibrated) | $80.90\%$ | $70.59\%$ | $67.50\%$ | $88.42\%$ | Adding RMSSD and SDNN provides $+6.25\%$ F1 gain through vagal tracking. |
| **M3** | 13 Multi-Domain Metrics (Uncalibrated) | $81.57\%$ | $73.03\%$ | $68.75\%$ | $88.77\%$ | Frequency and nonlinear features provide marginal incremental lift ($+0.67\%$ Acc). |
| **M4** | **Personalized Baseline-Calibrated ($\\Delta$)** | **92.36%** | **89.03%** | **86.25%** | **95.79%** | **$+10.79\%$ Acc, $+16.00\%$ F1 leap**; proves normalization is the critical factor. |

<table align="center">
  <tr>
    <td align="center" width="50%">
      <img src="results/figures/FINAL_Personalized_Feature_Ablation.png" width="100%" alt="Feature Ablation" /><br />
      <em><b>Figure 9(a): Model Progression & Ablation.</b> Quantitative leap in accuracy and F1-score achieved exclusively by transitioning to differential baseline normalization.</em>
    </td>
    <td align="center" width="50%">
      <img src="results/figures/FINAL_Feature_Group_Comparison.png" width="100%" alt="Feature Group Comparison" /><br />
      <em><b>Figure 9(b): Feature Group Comparison.</b> Performance breakdown across Time-Domain, Frequency-Domain, Nonlinear Poincaré, and Combined representations.</em>
    </td>
  </tr>
</table>

### 8.2 Permutation Feature Importance & Standardized Odds Ratios
To verify that the models capture authentic neurocardiac physiology rather than opportunistic data artifacts, we calculated:
1. **Permutation Importance:** Mean drop in held-out test ROC-AUC and F1-score when a given feature is randomly shuffled across unseen test subjects.
2. **Directional Standardized Odds Ratios ($e^{w_i}$):** Multiplicative change in the odds of acute stress classification per standard deviation increase in the normalized feature.

<p align="center">
  <img src="results/figures/ML_Feature_Importance_Permutation.png" width="95%" alt="Feature Importance and Odds Ratios" />
  <br>
  <em><b>Figure 10: Physiological Attribution and Standardized Odds Ratios.</b> (Left) Mean test ROC-AUC drop under feature permutation across unseen test subjects; (Right) Standardized Logistic Regression odds ratios ($e^{w_i}$) quantifying directional autonomic risk.</em>
</p>

### 8.3 Physiological Interpretation of Learned Weights
- **Cardiac Pacing Interval Compression ($\\Delta\text{MeanRR}$, Odds Ratio $= 0.0645$, AUC Drop $= 0.1766$):** A one standard deviation increase in the normalized RR interval reduces the odds of stress by $93.55\%$, or conversely, interval shortening dramatically drives stress detection. Shuffling this feature causes the largest single drop in model discrimination ($0.1766$ AUC drop), establishing it as the primary physiological anchor.
- **Sympathetic Cardiac Acceleration ($\\Delta\text{MeanHR}$, Odds Ratio $= 5.6453$, F1 Drop $= 0.1401$):** Each standard deviation elevation in normalized heart rate increases the odds of acute stress by **$5.65\times$**, directly capturing sinoatrial node stimulation via beta-1 adrenergic receptors.
- **Vagal Modulation Index ($\\Delta\text{pNN50}$, Odds Ratio $= 4.0784$, AUC Drop $= 0.0596$):** Captures high-frequency interval variability associated with rapid respiratory-cardiac coupling adjustments during acute cognitive load.
- **Autonomic Variance Suppression ($\\Delta\text{SDNN}$, Odds Ratio $= 0.4625$):** Elevated total heart rate variability exhibits a protective effect against stress classification, reflecting healthy vagal modulation at rest.

---

## 9. Inter-Subject Generalization & Heterogeneity Analysis

Wearable algorithms must maintain high clinical reliability across diverse individuals. Evaluating subject-specific recall across all 15 WESAD subjects reveals exceptional cross-cohort stability:

| Subject ID | Total Stress Windows | Correctly Detected | Subject Recall (%) | Physiological Response Profile |
| :---: | :---: | :---: | :---: | :--- |
| **S3** | 10 | 10 | **100.0%** | Robust sympathetic acceleration; marked vagal suppression. |
| **S4** | 10 | 10 | **100.0%** | Pronounced TSST tachycardia ($\Delta\text{HR} > +18\text{ BPM}$). |
| **S5** | 10 | 10 | **100.0%** | Clear sympathetic arousal and interval shortening. |
| **S8** | 11 | 11 | **100.0%** | Classical stress response; high TSST engagement. |
| **S11** | 11 | 11 | **100.0%** | Sharp vagal withdrawal; steep drop in RMSSD. |
| **S13** | 11 | 11 | **100.0%** | High sensitivity; perfect classification across all phases. |
| **S14** | 11 | 11 | **100.0%** | Robust autonomic reactivity; zero false negatives. |
| **S16** | 11 | 11 | **100.0%** | Severe interval compression during mental arithmetic. |
| **S17** | 12 | 12 | **100.0%** | Distinct high-amplitude stress reactivity. |
| **S6** | 10 | 9 | **90.0%** | Rapid stress onset with brief transient recovery. |
| **S7** | 10 | 9 | **90.0%** | High fidelity detection; 1 transient boundary window missed. |
| **S15** | 11 | 9 | **81.8%** | Moderate sympathetic responder; reliable detection. |
| **S10** | 12 | 9 | **75.0%** | Delayed TSST reactivity; initial windows near baseline threshold. |
| **S9** | 10 | 5 | **50.0%** | Blunted cardiovascular response during arithmetic phase. |
| **S2** | 10 | 0 | **0.0%** | Non-responder; persistent high resting vagal tone throughout TSST. |

<p align="center">
  <img src="results/figures/FINAL_Subject_Stress_Detection.png" width="95%" alt="Subject Stress Detection Rates" />
  <br>
  <em><b>Figure 11: Subject-Specific Detection Rate Distribution.</b> 9 out of 15 subjects achieve 100% stress recall, and 13 out of 15 achieve $\ge 75\%$, with atypical non-responders (S2) clearly isolated for clinical transparency.</em>
</p>

### 9.1 Scientific Discussion of Atypical Responders
In clinical literature (*Kirschbaum et al., 1993; Schmidt et al., 2018*), physiological non-responsiveness during laboratory stress protocols is an established phenomenon. In subject **S2**, subjective self-reports indicated low self-perceived distress during public speaking, and ECG telemetry confirmed that S2 maintained an unusually high baseline vagal tone ($\text{RMSSD} > 65\text{ ms}$) throughout the TSST without significant heart rate acceleration. Transparent identification and reporting of non-responders demonstrates high scientific rigor, highlighting that future multimodal models (combining ECG with electrodermal activity [EDA] and respiration) are beneficial for covering atypical cardiovascular phenotypes.

---

## 10. Reproducibility Protocol & Environment Specifications

The entire research pipeline is 100% automated and executable via headless command-line interfaces in both MATLAB and Python environments.

### 10.1 Computational Environment Requirements
- **MATLAB:** Version R2022b or later (Tested on R2026a).
  - *Required Toolboxes:* Signal Processing Toolbox, Statistics and Machine Learning Toolbox.
- **Python:** Version 3.10 or later.
  - *Required Libraries:* `numpy>=1.24`, `scipy>=1.10`, `pandas>=2.0`, `scikit-learn>=1.3`, `matplotlib>=3.7`, `seaborn>=0.12`.

### 10.2 Automated Reproduction Commands

#### A. MATLAB Signal Processing & LOSO Pipeline
```bash
# Execute full interactive signal processing demonstration
matlab -batch "cd('matlab'); DEMO_stress_detection;"

# Re-generate the publication light-theme master dashboard
matlab -batch "cd('matlab'); TWENTY_NINE_project_dashboard;"

# Re-compute full 15-fold LOSO metrics and export CSV scorecards
matlab -batch "cd('matlab'); TWENTY_FOUR_calibrated_stress_detection;"
```

#### B. Python Multi-Model ML Benchmark & Explainability Suite
```bash
# 1. Run the 15-fold LOSO benchmark across all 6 ML classifiers
python python/train_loso_ml_benchmark.py

# 2. Compute permutation importance drops and standardized odds ratios
python python/explainability_feature_importance.py

# 3. Generate publication-grade comparative benchmark figures
python python/plot_ml_evaluation.py
```

---

## 11. Repository Architecture

```plaintext
ECG_STRESS_DETECTION/
├── README.md                                  # Comprehensive research documentation & benchmark report
├── LICENSE                                    # MIT Open Source License
├── requirements.txt                           # Python dependencies for ML & explainability suite
│
├── matlab/                                    # Modular MATLAB signal processing pipeline
│   ├── DEMO_stress_detection.m                # Interactive clinical demonstration & telemetry visualizer
│   ├── TWENTY_NINE_project_dashboard.m        # Master 6-panel publication dashboard generator
│   ├── TWENTY_FOUR_calibrated_stress_detection.m # Calibrated LOSO cross-validation engine
│   ├── 01_data_loading/                       # Raw signal parsers and MAT-file converters
│   ├── 02_preprocessing/                      # Butterworth bandpass filters & motion audit scripts
│   ├── 03_qrs_detection/                      # Pan-Tompkins QRS detection engine & NN cleaning
│   ├── 04_feature_extraction/                 # Time, frequency, and nonlinear HRV extractors
│   ├── 05_model_development/                  # LOSO regression models & ablation experiments
│   └── 06_final_results/                      # Metric calculators and high-resolution export
│
├── python/                                    # Machine learning benchmark & explainability suite
│   ├── train_loso_ml_benchmark.py             # 15-fold LOSO benchmarking across 6 ML architectures
│   ├── explainability_feature_importance.py   # Permutation importance and odds ratio calculator
│   ├── plot_ml_evaluation.py                  # High-contrast publication figure generator
│   └── extract_ecg_labels.py                  # WESAD pickle (.pkl) to NumPy/MAT converter
│
├── data/                                      # Experimental data directory (Ignored via .gitignore)
│   ├── raw/WESAD/                             # Original WESAD subject folders (S2 - S17)
│   └── processed/                             # Preprocessed ECG signals and extracted features
│
└── results/                                   # Validated experimental outputs and figure suite
    ├── FINAL_Model_Metrics.csv                # Primary validated classifier metrics (Acc, F1, AUC, etc.)
    ├── FINAL_Development_Model_Comparison.csv # Four-stage model progression and ablation data
    ├── FINAL_Subject_Stress_Performance.csv   # Subject-by-subject recall and detection statistics
    ├── ML_Model_Benchmark_LOSO.csv            # Cross-model benchmark results across all 6 architectures
    ├── ML_Feature_Importance_Permutation.csv  # Permutation importance and standardized odds ratios
    └── figures/                               # Master publication and telemetry figure suite
        ├── FINAL_Project_Dashboard.png        # Master 6-panel publication light dashboard
        ├── FINAL_Confusion_Matrix.png         # Calibrated LOSO confusion matrix
        ├── FINAL_ROC_Curve.png                # Calibrated LOSO ROC curve (AUC = 0.9494)
        ├── FINAL_Personalized_Feature_Ablation.png # Four-stage ablation performance jump
        ├── FINAL_Feature_Group_Comparison.png # Time vs Frequency vs Nonlinear vs Combined
        ├── FINAL_Subject_Stress_Detection.png # Subject-specific stress recall breakdown
        ├── DEMO_Raw_ECG_LeadII.png            # Lead-II ECG trace (Clinical dark telemetry)
        ├── DEMO_Pan_Tompkins_QRS_Detection.png# 4-stage Pan-Tompkins detection (Dark telemetry)
        ├── DEMO_Protocol_Timeline.png         # WESAD protocol condition timeline (Dark telemetry)
        ├── ML_Model_Benchmark_Bars.png        # 6-model 4-metric comparative benchmark bars
        ├── ML_Model_Comparison_ROC.png        # Multi-model ROC discrimination comparison
        ├── ML_Model_Comparison_PR.png         # Multi-model Precision-Recall curve comparison
        ├── ML_Confusion_Matrices_Grid.png     # 2x3 confusion matrix grid across all 6 classifiers
        └── ML_Feature_Importance_Permutation.png # Permutation drops and directional odds ratios
```

---

## 12. Dataset Access & Ethical Compliance

> [!NOTE]
> **Dataset Exemption & Licensing:** In compliance with scientific data governance and GitHub repository size limits, the raw WESAD sensor recordings (~16 GB) are **not tracked in this repository** and are excluded via `.gitignore`.

To access the original sensor signals:
1. Access the public **WESAD** repository on the [UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/465/wesad+wearable+stress+and+affect+detection).
2. Download and unpack subject archives (`S2/`, `S3/`, ..., `S17/`) into `data/raw/WESAD/`.
3. Execute `python/extract_ecg_labels.py` to generate processed MAT-files for MATLAB and CSV files for Python.

---

## 13. Academic Citation

If you utilize this signal processing pipeline, baseline normalization methodology, machine learning benchmark, or experimental results in academic publications, please cite the underlying WESAD benchmark:

```bibtex
@inproceedings{schmidt2018wesad,
  title={Introducing WESAD, a Multimodal Dataset for Wearable Stress and Affect Detection},
  author={Schmidt, Philip and Reiss, Attila and Duerichen, Robert and Marberger, Claus and Van Laerhoven, Kristof},
  booktitle={Proceedings of the 20th ACM International Conference on Multimodal Interaction (ICMI)},
  pages={400--408},
  year={2018},
  doi={10.1145/3242969.3242985}
}
```

---

## 14. License
This codebase, signal processing algorithms, and machine learning suites are released under the [MIT License](LICENSE).
