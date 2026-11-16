# Pipeline Reproduction Order: Raw WESAD to Paper Package

This document defines the exact sequential execution order to reproduce all results, tables, and figures in the paper from the raw WESAD dataset.

---

### Step 1: Raw Data Extraction & Label Parsing
* **Script:** `python/extract_ecg_labels.py`
* **Input:** Raw WESAD archive directories (`data/raw/WESAD/SX/SX.pkl` for 15 subjects: S2–S11, S13–S17).
* **Operation:** Extracts raw chest RespiBAN single-channel ECG (sampled at 700 Hz) and protocol condition labels (Condition 1 = Baseline, Condition 2 = Stress).
* **Output:** `data/processed/S*_ECG_labels.mat` (15 subject MAT files).

---

### Step 2: R-Peak Detection & HRV Feature Extraction
* **Script:** `matlab/02_preprocessing/TEN_process_all_subjects.m`
* **Input:** `data/processed/S*_ECG_labels.mat`
* **Operation:** Applies 0.5–40 Hz 4th-order Butterworth bandpass filtering, Pan--Tompkins QRS complex detection, physiological interval gating (300–1500 ms), and extracts 13 time-, frequency-, and nonlinear-domain HRV metrics across non-overlapping 60-second windows.
* **Output:**
  - `results/WESAD_HRV_features_expanded.csv` (Tracked in Git, 446 lines: header + 445 diagnostic windows; 285 baseline, 160 stress across 15 subjects).
  - `results/WESAD_HRV_features_expanded.mat`.

---

### Step 3: Leak-Free Baseline Calibration Experiment
* **Script:** `python/calibration_length_experiment.py`
* **Input:** `results/WESAD_HRV_features_expanded.csv`
* **Operation:**
  1. For each subject $s$, computes baseline anchor vector $B_{s,f}$ using strictly the first $N$ chronological baseline windows ($N \in \{1, 2, 3, 5, 10\}$):
     $$\Delta f_{s,i} = \frac{f_{s,i} - B_{s,f}}{\max(|B_{s,f}|, 10^{-6})}$$
  2. Anchors are excluded from scoring; evaluation is performed on the common 295 evaluation windows (135 baseline + 160 stress; majority-class baseline 54.24%).
  3. In each cross-validation fold, training subjects' first $N$ windows are also excluded from training folds.
  4. Runs 15-fold Leave-One-Subject-Out (LOSO) across 6 classifier architectures (Logistic Regression, SVM (RBF), HistGradientBoosting, Extra Trees, MLP, Random Forest).
* **Outputs:**
  - `results/calibration_length/calibration_length_primary_model.csv`
  - `results/calibration_length/calibration_length_all_models.csv`
  - `results/calibration_length/calibration_length_per_subject.csv`
  - `results/calibration_length/calibration_length_window_predictions.csv`

---

### Step 4: Leak-Free Feature Ablation Experiment
* **Script:** `python/leak_free_ablation_experiment.py`
* **Input:** `results/WESAD_HRV_features_expanded.csv`
* **Operation:** Evaluates 4 feature subsets (1-feature MeanHR, 4-feature time domain, 8-feature core set, 13-feature full set) across three calibration regimes (Uncalibrated Raw, $N=5$, $N=10$) under 15-fold LOSO cross-validation on the 295 common evaluation windows.
* **Output:** `results/calibration_length/leak_free_ablation_results.csv`

---

### Step 5: Paired Cluster Bootstrap Contrasts
* **Script:** `python/paired_contrasts_bootstrap.py`
* **Input:** `results/calibration_length/calibration_length_window_predictions.csv`
* **Operation:** Runs 10,000 subject-level cluster bootstrap iterations (seed = 0) to calculate paired contrast point estimates and empirical 95% percentile confidence intervals for:
  - $N \in \{1, 2, 3, 5, 10\}$ vs. Uncalibrated Control (a)
  - $N=10$ vs. $N=5$
  - $N=10$ vs. Leaky Control (b)
* **Output:** `results/calibration_length/paired_contrasts_bootstrap.csv`

---

### Step 6: Embedded Hardware Benchmark Verification
* **Script:** `python/run_biquad_dwt_benchmark.py`
* **Operation:** Analyzes DWT cycle counter logs from physical ARM Cortex-M4 (STM32G474RE @ 170 MHz) hardware execution for the 5-stage Direct Form I Biquad filter (biquad DWT benchmark only; HC1 physical telemetry validation is captured separately in the 10,000-packet HIL suite).
* **Output:** `results/raw_evidence_item6_biquad_dwt_cycles.json`

---

### Step 7: LaTeX Tables & Macro Generation
* **Script:** `python/make_paper_tables.py`
* **Inputs:**
  - `results/calibration_length/calibration_length_primary_model.csv`
  - `results/calibration_length/calibration_length_all_models.csv`
  - `results/calibration_length/paired_contrasts_bootstrap.csv`
  - `results/calibration_length/leak_free_ablation_results.csv`
  - `results/calibration_length/calibration_length_window_predictions.csv`
  - `results/raw_evidence_item6_biquad_dwt_cycles.json`
* **Outputs:**
  - `paper_package/numbers.tex` (all LaTeX value macros)
  - `paper_package/tables/tab_calibration_length.tex` (Table I)
  - `paper_package/tables/tab_ml_benchmark.tex` (Table II)
  - `paper_package/tables/tab_ablation.tex` (Table III)
  - `paper_package/tables/tab_thresholds.tex` (Table IV)
  - `paper_package/tables/tab_hw_profile.tex` (Table V)

---

### Step 8: Paper Figure Generation
* **Script:** `python/make_paper_figures.py`
* **Inputs:**
  - `results/calibration_length/calibration_length_window_predictions.csv`
  - `results/calibration_length/leak_free_ablation_results.csv`
* **Outputs:**
  - `paper_package/figures/FINAL_ROC_Curve.png` (Fig. 2)
  - `paper_package/figures/FINAL_Personalized_Feature_Ablation.png` (Fig. 3)

---

### Step 9: Manuscript Compilation
* **Tool:** `pdflatex` or `latexmk -pdf`
* **Directory:** `paper_package/`
* **Target:** `main.tex`
* **Output:** `main.pdf` (Exactly 6 pages, 0 errors, 0 undefined references/citations).
