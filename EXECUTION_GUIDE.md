# Master Execution Guide: WESAD ECG & HRV Stress Detection Pipeline

This document provides the definitive, step-by-step instructions for reproducing and running the entire end-to-end research pipeline—from raw WESAD wearable sensor recordings to clinical digital signal processing (DSP), statistical modeling, multi-model machine learning benchmarks, and the interactive web application.

---

## 1. System Architecture & Workflow Overview

```
                                [ RAW DATA ACQUISITION ]
                        WESAD Wearable Dataset (15 Subjects)
                        Chest RespiBAN Lead-II ECG @ 700 Hz
                                        │
                                        ▼ (Step 0: Python Extraction)
                        [ STANDARDIZED S*_ECG_labels.mat ]
                                        │
                    ┌───────────────────┴───────────────────┐
                    ▼                                       ▼
        [ MATLAB DSP & FEATURE PIPELINE ]       [ PYTHON ML BENCHMARK ]
        - 0.5–40 Hz 4th-order Butterworth       - 15-Fold LOSO Validation
        - Pan-Tompkins & MAD Peak Detection     - 6 ML Models (inc. MLP)
        - 60s Sliding Windows (50% Overlap)     - Feature Importance / Odds Ratios
        - 8 Core Autonomic HRV Metrics          - ROC-AUC / PR-AUC Evaluation
        - Subject Baseline Normalization (Δx)   - Streamlit Web Dashboard
                    │                                       │
                    ▼                                       ▼
        [ Publication Figures & Dashboard ]     [ Interactive Telemetry App ]
        - 300 DPI Medical Vector Graphics       - Real-time stress needle gauge
        - Master 6-Panel Research Board         - Live sliding threshold slider
```

---

## 2. Prerequisites & Environment Setup

### 2.1 Software Requirements
* **Operating System:** Windows 10 / 11, Linux, or macOS.
* **Python:** Version `3.10` or higher.
* **MATLAB:** `R2022b` or higher with:
  * *Signal Processing Toolbox* (for `butter`, `filtfilt`, `findpeaks`).
  * *Statistics and Machine Learning Toolbox* (for statistical tests & distributions).

---

### 2.2 Python Virtual Environment Setup

Open PowerShell or Terminal in the project root directory:

```powershell
# 1. Navigate to project root
cd "C:\Users\YASH\Desktop\projects\RESEARCH PROJECTS\ECG_STRESS_DETECTION"

# 2. Create virtual environment (if not already created)
python -m venv venv

# 3. Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Windows Command Prompt:
.\venv\Scripts\activate.bat
# Linux / macOS:
source venv/bin/activate

# 4. Install all required dependencies
pip install -r requirements.txt
```

#### Installed Python Dependencies (`requirements.txt`):
* `streamlit>=1.35.0` (Clinical telemetry web dashboard)
* `plotly>=5.20.0` (Interactive waveform & radar charts)
* `pandas>=2.0.0` (Feature matrix processing)
* `numpy>=1.24.0` (Vectorized numerical computations)
* `scipy>=1.10.0` (Signal processing & MAT file I/O)
* `scikit-learn>=1.3.0` (ML classifiers, LOSO cross-validation, MLP neural network)

---

## 3. Step-by-Step Execution Sequence

---

### Step 0: Raw Data Ingestion & Formatting (Python)
> **Goal:** Extract raw chest ECG and affective ground-truth labels from WESAD pickle files (`.pkl`) and convert them into lightweight compressed MATLAB arrays (`.mat`).

* **Script:** [`python/extract_ecg_labels.py`](python/extract_ecg_labels.py)
* **Command:**
  ```powershell
  python python/extract_ecg_labels.py
  ```
* **What happens:**
  1. Reads `S2.pkl` through `S17.pkl` from the raw WESAD directory.
  2. Extracts the `chest` $\rightarrow$ `ECG` channel ($700\text{ Hz}$) and the synchronous `label` stream.
  3. Downcasts precision to `float32` and `uint8` to optimize memory and disk footprint.
  4. Saves compressed files to `data/processed/S*_ECG_labels.mat`.

*(Note: If pre-processed `.mat` files are already present in `data/processed/`, you can proceed directly to Step 1.)*

---

### Step 1: MATLAB Path Initialization (MATLAB)
> **Goal:** Register all subfolders, DSP functions, and feature extraction routines into MATLAB's active path.

1. Open MATLAB.
2. Set the current directory to:
   ```matlab
   cd 'C:\Users\YASH\Desktop\projects\RESEARCH PROJECTS\ECG_STRESS_DETECTION\matlab'
   ```
3. Run the setup script:
   ```matlab
   setup_project
   ```
* **Output:** Displays confirmation that project root and all subdirectories (`01_data_inspection` to `06_final_results`) have been added to the search path.

---

### Step 2: Multi-Subject DSP & Feature Extraction (MATLAB)
> **Goal:** Filter raw ECG, detect R-peaks, enforce physiological interval gating, extract 8 core HRV metrics across 60-second sliding windows (30s step), and calculate subject-specific relative baseline calibration.

* **Script:** [`matlab/02_preprocessing/TEN_process_all_subjects.m`](matlab/02_preprocessing/TEN_process_all_subjects.m)
* **Execution (MATLAB Command Window):**
  ```matlab
  TEN_process_all_subjects
  ```
* **What happens:**
  1. Iterates across all 15 WESAD subjects ($S2 \dots S17$).
  2. Applies a 4th-order zero-phase Butterworth bandpass filter ($0.5\text{--}40\text{ Hz}$) via `filtfilt`.
  3. Calculates the dynamic Median Absolute Deviation (MAD) noise floor:
     $$\text{Noise Level} = 1.4826 \times \text{median}(|x - \text{median}(x)|)$$
  4. Identifies R-peaks with physiological refractory lockout ($350\text{ ms}$).
  5. Computes RR intervals and rejects ectopic/artifactual values outside $300\text{--}1500\text{ ms}$ ($40\text{--}200\text{ BPM}$).
  6. Computes 8 core HRV metrics per window: `MeanHR`, `SDNN`, `RMSSD`, `pNN50`, `MeanRR`, `RR_CV`, `RR_IQR`, `HR_IQR`.
  7. Computes the baseline reference vector $\mathbf{B}_s$ per subject and outputs:
     * `results/WESAD_HRV_features_expanded.csv` (445 standardized windows)
     * `results/WESAD_HRV_features_expanded.mat`

---

### Step 3: Statistical Analysis & Hypothesis Testing (MATLAB)
> **Goal:** Perform paired statistical audits and distribution comparisons confirming physiological response under acute TSST stress.

* **Scripts:** 
  * `FOURTEEN_statistical_tests.m`
  * `FIFTEEN_feature_analysis.m`
* **Execution (MATLAB Command Window):**
  ```matlab
  FOURTEEN_statistical_tests
  FIFTEEN_feature_analysis
  ```
* **What happens:**
  * Computes paired Student’s t-tests and non-parametric Wilcoxon signed-rank tests across baseline vs. stress states.
  * Confirms significant sympathetic activation ($p < 0.001$ for HR increase and RMSSD vagal withdrawal).

---

### Step 4: Publication Figures & Master Clinical Dashboard (MATLAB)
> **Goal:** Generate publication-grade, 300 DPI vector graphics and the master 6-panel clinical research board.

* **Execution (MATLAB Command Window):**
  ```matlab
  TWENTY_SEVEN_final_results       % Computes final metrics table
  TWENTY_EIGHT_report_figures      % Exports individual high-res figures
  TWENTY_NINE_project_dashboard    % Generates the master 6-panel clinical dashboard
  ```
* **Generated Assets:**
  * `results/figures/FINAL_Project_Dashboard.png` (Comprehensive 6-panel board)
  * `results/figures/FIG1_Study_Protocol_Timeline.png`
  * `results/figures/FIG2_QRS_Detection_Validation.png`
  * `results/figures/FIG3_Physiological_Distributions.png`
  * `results/figures/FIG4_Confusion_Matrix_LOSO.png`
  * `results/figures/FIG5_ROC_Curve_LOSO.png`

---

### Step 5: Interactive Telemetry MATLAB Demo (MATLAB GUI)
> **Goal:** Run an interactive, tabbed telemetry interface showcasing raw ECG waveforms, the experimental timeline, Pan-Tompkins QRS detection, and biological feature contrasts.

* **Script:** [`matlab/DEMO_stress_detection.m`](matlab/DEMO_stress_detection.m)
* **Execution (MATLAB Command Window):**
  ```matlab
  DEMO_stress_detection
  ```
* **Interactive Features:**
  * **Tab 1:** Lead-II Raw ECG telemetry segment.
  * **Tab 2:** Full 101-minute experimental protocol with color-coded stress zones.
  * **Tab 3:** 60-second window Pan-Tompkins detection telemetry with highlighted R-peaks.
  * **Tab 4:** Summary scorecard comparing baseline vs. acute stress physiology.

---

### Step 6: 15-Fold LOSO Machine Learning Benchmark (Python)
> **Goal:** Execute strict Leave-One-Subject-Out cross-validation across 6 machine learning architectures using subject-specific relative baseline calibration ($\Delta x$).

* **Script:** [`python/train_loso_ml_benchmark.py`](python/train_loso_ml_benchmark.py)
* **Execution (Terminal / PowerShell):**
  ```powershell
  python python/train_loso_ml_benchmark.py
  ```
* **What happens:**
  * Loads `results/WESAD_HRV_features_expanded.csv` (445 windows across 15 subjects).
  * Executes 15 iterative folds: in fold $k$, subject $k$ is held out as the test set while the remaining 14 subjects form the training set.
  * Fits `StandardScaler` strictly on the training fold to guarantee zero data leakage.
  * Trains and benchmarks 6 distinct classifier paradigms:
    1. **Logistic Regression** ($L2$ regularized, liblinear solver)
    2. **Support Vector Machine** (RBF non-linear kernel, probability calibration)
    3. **Random Forest** (100 bagged trees, max depth 6)
    4. **Extra Trees** (100 extremely randomized trees)
    5. **HistGradientBoosting** (Histogram-based gradient boosted trees)
    6. **Multi-Layer Perceptron (MLP)** (Feedforward Neural Net: layers (32, 16), ReLU, Adam optimizer, $\alpha=0.01$)
  * **Output Table:** Prints Accuracy, Balanced Accuracy, Sensitivity (Recall), Specificity, F1-Score, and ROC-AUC for all 6 models.

---

### Step 7: Explainability, Permutation Importance & Odds Ratios (Python)
> **Goal:** Quantify physiological drivers behind classifier decisions using permutation importance and clinical standardized odds ratios.

* **Script:** [`python/explainability_feature_importance.py`](python/explainability_feature_importance.py)
* **Execution (Terminal / PowerShell):**
  ```powershell
  python python/explainability_feature_importance.py
  ```
* **Key Findings:**
  * Confirms that cardiac interval compression ($\Delta \text{MeanRR}$) and heart rate acceleration ($\Delta \text{MeanHR}$) contribute $>65\%$ of the total predictive power.
  * Vagal withdrawal ($\Delta \text{RMSSD}$) provides the primary secondary confirmation of parasympathetic suppression.

---

### Step 8: Multi-Model Evaluation Plots & Visualizations (Python)
> **Goal:** Render and save high-resolution comparative ROC curves, Precision-Recall curves, confusion matrices, and benchmark bar charts.

* **Script:** [`python/plot_ml_evaluation.py`](python/plot_ml_evaluation.py)
* **Execution (Terminal / PowerShell):**
  ```powershell
  python python/plot_ml_evaluation.py
  ```
* **Generated Figures (`results/figures/python/`):**
  * `ml_benchmark_roc_curves.png` (Comparison of all 6 models on held-out subjects)
  * `ml_benchmark_pr_curves.png` (Precision-recall trade-offs)
  * `ml_benchmark_metrics_bars.png` (Multi-metric comparison bar chart)
  * `loso_confusion_matrices.png` (Subject-by-subject classification outcomes)

---

### Step 9: Interactive Clinical Telemetry Web Dashboard (Streamlit)
> **Goal:** Launch a web-based clinical dashboard allowing real-time subject playback, live ECG waveform visualization, dynamic decision threshold adjustment, and stress needle gauges.

* **Script:** [`demo/app.py`](demo/app.py)
* **Execution (Terminal / PowerShell):**
  ```powershell
  streamlit run demo/app.py
  ```
* **Dashboard Capabilities:**
  * **Subject Selector:** Choose any of the 15 WESAD subjects ($S2 \dots S17$).
  * **Interactive Waveform View:** Zoomable 700 Hz Lead-II ECG with detected R-peaks and RR tachogram.
  * **Dynamic Threshold Slider:** Adjust $\tau \in [0.10, 0.90]$ to observe real-time sensitivity vs. specificity trade-offs.
  * **Stress Needle Gauge:** Color-coded gauge indicating instantaneous stress probability.
  * **Autonomic Radar Profile:** Displays percentage deviation of HRV metrics from resting baseline.

---

## 4. Quick-Run Cheat Sheet (Single-Command Execution)

### To Run the Entire Python Machine Learning Suite in One Command:
```powershell
python python/train_loso_ml_benchmark.py; python python/explainability_feature_importance.py; python python/plot_ml_evaluation.py
```

### To Run MATLAB Headless from Terminal (Without Opening MATLAB GUI):
```powershell
matlab -batch "cd('matlab'); setup_project; TWENTY_SEVEN_final_results; TWENTY_EIGHT_report_figures; TWENTY_NINE_project_dashboard; exit"
```

---

## 5. Verification Checklist

After running the full pipeline, verify that the following key outputs exist and match expected benchmarks:

| Target File / Output | Verification Metric | Status |
| :--- | :--- | :--- |
| `data/processed/S2_ECG_labels.mat` | File size $\approx 10\text{–}15\text{ MB}$, variables: `ecg`, `labels`, `Fs` | ✅ |
| `results/WESAD_HRV_features_expanded.csv` | Exactly 445 rows (windows), 15 subjects, 8 core features | ✅ |
| `results/figures/FINAL_Project_Dashboard.png` | High-res 6-panel graphic containing ROC (AUC = 0.9494) | ✅ |
| `python/train_loso_ml_benchmark.py` Log | All 6 classifiers achieve $\text{ROC-AUC} \ge 0.937$ on held-out subjects | ✅ |
| Streamlit Local Server (`localhost:8501`) | Dashboard loads smoothly with interactive Plotly charts | ✅ |

---

## 6. Troubleshooting & Common Questions

* **Error: `Undefined function 'butter' or 'filtfilt'` in MATLAB:**
  * *Fix:* Your MATLAB installation is missing the **Signal Processing Toolbox**. Install it via MATLAB Home $\rightarrow$ Add-Ons $\rightarrow$ Get Add-Ons.
* **Error: `FileNotFoundError: results/WESAD_HRV_features_expanded.csv` in Python:**
  * *Fix:* Run Step 2 (`TEN_process_all_subjects.m`) in MATLAB first, or verify the CSV is in the `results/` folder.
* **Streamlit Port In Use (`Port 8501 already in use`):**
  * *Fix:* Run on an alternate port:
    ```powershell
    streamlit run demo/app.py --server.port 8502
    ```
