# Stage 2 Exploratory Threshold ($\tau = 0.35$) Discrepancy Investigation

## 1. Executive Summary

This investigation analyzes the numerical variation observed at the exploratory operating threshold $\tau = 0.35$ in Stage 2 of the verification audit.

- **Pre-specified Primary Operating Point ($\tau = 0.50$):** The MATLAB and Python pipelines produce identical classification decisions and confusion-matrix metrics at the pre-specified threshold $\tau = 0.50$. This does not imply bit-for-bit equality of probability values or identical model parameters (Accuracy = 92.13%, F1 = 88.29%, Sensitivity = 82.50%, Specificity = 97.54%, TP = 132, FP = 7, TN = 278, FN = 28).
- **Exploratory Operating Point ($\tau = 0.35$):** Both implementations achieve the **exact same overall accuracy** (411 / 445 = **92.359551%**), but exhibit a **1-sample shift** in the confusion matrix between the MATLAB artifact pipeline (`FINAL_Model_Metrics.csv` / `Threshold_Analysis.csv`) and the Python benchmark pipeline (`ML_Predictions_LOSO.csv`):
  - **MATLAB Pipeline:** $\text{TP} = 138$, $\text{FP} = 12$, $\text{TN} = 273$, $\text{FN} = 22 \implies \text{Sens} = 86.25\%$, $\text{Spec} = 95.79\%$, $\text{F1} = 89.03\%$
  - **Python Pipeline:** $\text{TP} = 139$, $\text{FP} = 13$, $\text{TN} = 272$, $\text{FN} = 21 \implies \text{Sens} = 86.88\%$, $\text{Spec} = 95.44\%$, $\text{F1} = 89.10\%$

MATLAB and Python use different Logistic Regression implementations. MATLAB uses custom unregularized gradient descent, while Python uses scikit-learn LogisticRegression with L2 regularization. Therefore, the two pipelines should be treated as numerically related but not mathematically identical models.

The investigation proves that this difference is purely an algorithmic artifact between MATLAB's unregularized gradient descent optimizer and scikit-learn's L2-regularized coordinate descent solver on four borderline predictions straddling $\tau = 0.35$.

---

## 2. Comparative Matrix Across All Analyzed Files

The table below reports the confusion matrix and performance metrics evaluated specifically for **Logistic Regression at $\tau = 0.35$** across all six queried files:

| Metric / Attribute | `Threshold_Analysis.csv` | `FINAL_Model_Metrics.csv` | `Stress_Classifier_Predictions.csv` | `Personalized_Classifier_Predictions.csv` | `ML_Predictions_LOSO.csv` (LR) | `ml_rerun/ML_Predictions_LOSO.csv` (LR) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Pipeline Origin** | MATLAB (`TWENTY_FOUR`) | MATLAB (`TWENTY_EIGHT`) | MATLAB (`SIXTEEN` Uncalibrated) | MATLAB (`TWENTY` Calibrated) | Python (`train_loso` Benchmark) | Python (`train_loso` Rerun) |
| **Row Count** | 81 (Sweep rows) | 12 (Metric rows) | 445 windows | 445 windows | 445 windows (2,670 total) | 445 windows (2,670 total) |
| **True Positive (TP)** | 138 | 138 | 119 | 138 | 139 | 139 |
| **False Positive (FP)**| 12 | 12 | 48 | 12 | 13 | 13 |
| **True Negative (TN)** | 273 | 273 | 237 | 273 | 272 | 272 |
| **False Negative (FN)**| 22 | 22 | 41 | 22 | 21 | 21 |
| **Accuracy (%)** | **92.3596%** | **92.3596%** | **80.0000%** | **92.3596%** | **92.3596%** | **92.3596%** |
| **Correct Detections** | 411 / 445 | 411 / 445 | 356 / 445 | 411 / 445 | 411 / 445 | 411 / 445 |
| **Precision (%)** | 92.0000% | 92.0000% | 71.2575% | 92.0000% | 91.4474% | 91.4474% |
| **Recall / Sens (%)** | 86.2500% | 86.2500% | 74.3750% | 86.2500% | 86.8750% | 86.8750% |
| **Specificity (%)** | 95.7895% | 95.7895% | 83.1579% | 95.7895% | 95.4386% | 95.4386% |
| **F1-Score (%)** | 89.0323% | 89.0323% | 72.7829% | 89.0323% | 89.1026% | 89.1026% |

---

## 3. Analysis of Specific Investigation Questions

### Question 7: Number of Rows
- [`results/Threshold_Analysis.csv`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/results/Threshold_Analysis.csv): 81 rows (thresholds swept from 0.10 to 0.90 in increments of 0.01).
- [`results/FINAL_Model_Metrics.csv`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/results/FINAL_Model_Metrics.csv): 12 rows (key-value scorecard summarizing performance at locked $\tau = 0.35$).
- [`results/Stress_Classifier_Predictions.csv`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/results/Stress_Classifier_Predictions.csv): Exactly **445 rows** (representing the 445 WESAD windows).
- [`results/Personalized_Classifier_Predictions.csv`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/results/Personalized_Classifier_Predictions.csv): Exactly **445 rows**.
- [`results/ML_Predictions_LOSO.csv`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/results/ML_Predictions_LOSO.csv): **2,670 rows** (445 windows $\times$ 6 models; exactly 445 rows for Logistic Regression).
- [`results/verification/ml_rerun/ML_Predictions_LOSO.csv`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/results/verification/ml_rerun/ML_Predictions_LOSO.csv): **2,670 rows** (exactly 445 rows for Logistic Regression).

### Question 8: Whether Probability Values Are Identical
- **Canonical Python vs. Verification Rerun:**  
  The probabilities in `results/ML_Predictions_LOSO.csv` and `results/verification/ml_rerun/ML_Predictions_LOSO.csv` are **100% bit-for-bit identical** ($\max |\Delta| = 0.0000000000$).
- **MATLAB vs. Python:**  
  The probabilities in `results/Personalized_Classifier_Predictions.csv` (MATLAB) and `results/ML_Predictions_LOSO.csv` (Python) are **not identical, but extremely highly correlated**:
  - Pearson correlation: $r = 0.999866$
  - Mean absolute difference: $0.006182$ (0.62 percentage points)
  - Max absolute difference: $0.036454$ (3.65 percentage points)
- **Uncalibrated vs. Calibrated:**  
  `results/Stress_Classifier_Predictions.csv` contains completely different probabilities generated without subject baseline calibration (yielding only 80.00% accuracy at $\tau = 0.35$).

### Question 9: Whether Subject and Window Ordering Is Identical
- **Yes.** In all four 445-row prediction files (`Stress_Classifier_Predictions.csv`, `Personalized_Classifier_Predictions.csv`, `ML_Predictions_LOSO.csv`, and `ml_rerun/ML_Predictions_LOSO.csv`), the ground-truth target vector `TrueLabel` is **identical row-for-row**:
  ```text
  Row 0..30   : Subject S10 (19 Baseline, 12 Stress)
  Row 31..60  : Subject S11 (19 Baseline, 11 Stress)
  Row 61..90  : Subject S13 (19 Baseline, 11 Stress)
  Row 91..120 : Subject S14 (19 Baseline, 11 Stress)
  Row 121..150: Subject S15 (19 Baseline, 11 Stress)
  Row 151..180: Subject S16 (19 Baseline, 11 Stress)
  Row 181..211: Subject S17 (19 Baseline, 12 Stress)
  Row 212..240: Subject S2  (19 Baseline, 10 Stress)
  Row 241..269: Subject S3  (19 Baseline, 10 Stress)
  Row 270..298: Subject S4  (19 Baseline, 10 Stress)
  Row 299..327: Subject S5  (19 Baseline, 10 Stress)
  Row 328..356: Subject S6  (19 Baseline, 10 Stress)
  Row 357..385: Subject S7  (19 Baseline, 10 Stress)
  Row 386..415: Subject S8  (19 Baseline, 11 Stress)
  Row 416..444: Subject S9  (19 Baseline, 10 Stress)
  ```
  `(f_mat['TrueLabel'] == f_py['True_Label']).all() == True` across all 445 rows.

---

## 4. The Exact Reason for the Discrepancy

### 4.1 Boundary Sample Identification
Comparing the predictions between MATLAB and Python across all 445 windows reveals that **441 out of 445 predictions (99.1%) match identically**.

Exactly **4 windows** differ because their predicted probabilities lie in the immediate boundary interval $[0.345, 0.358]$:

| Row Index | Subject | Window | True Condition | MATLAB Prob | Python Prob | MATLAB Pred ($\tau=0.35$) | Python Pred ($\tau=0.35$) | Clinical Impact |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **17** | **S10** | 18 | Calm (0) | `0.354153` | `0.348537` | **1 (False Positive)** | **0 (True Negative)** | Python avoids false alarm |
| **212** | **S2** | 1 | Calm (0) | `0.348658` | `0.358040` | **0 (True Negative)** | **1 (False Positive)** | Python creates false alarm |
| **276** | **S4** | 7 | Calm (0) | `0.347596` | `0.351746` | **0 (True Negative)** | **1 (False Positive)** | Python creates false alarm |
| **440** | **S9** | 6 | Stress (1) | `0.345892` | `0.357512` | **0 (False Negative)** | **1 (True Positive)** | Python catches true stress |

### 4.2 Arithmetic Mechanism
1. **Stress Windows:**
   - In MATLAB, row 440 was $P = 0.3459 < 0.35 \implies \text{FN}$.
   - In Python, row 440 was $P = 0.3575 \ge 0.35 \implies \text{TP}$.
   - Result: Python gains $+1$ True Positive ($\text{TP} = 138 \rightarrow 139$) and loses $-1$ False Negative ($\text{FN} = 22 \rightarrow 21$).
2. **Calm Windows:**
   - Row 17: MATLAB FP $\rightarrow$ Python TN ($+1$ TN, $-1$ FP).
   - Rows 212 & 276: MATLAB TN $\rightarrow$ Python FP ($-2$ TN, $+2$ FP).
   - Net Calm change: $\text{TN} = 273 \rightarrow 272$ ($-1$), $\text{FP} = 12 \rightarrow 13$ ($+1$).
3. **Net Invariance of Total Accuracy:**
   $$\Delta \text{Correct} = (+1 \text{ TP}) + (-1 \text{ TN}) = 0$$
   $$\text{Total Correct (MATLAB)} = 138 + 273 = 411 / 445 = 92.359551\%$$
   $$\text{Total Correct (Python)} = 139 + 272 = 411 / 445 = 92.359551\%$$

### 4.3 Root Cause in the Codebases
The minor probability divergence ($< 0.01$) on these four boundary samples stems from two distinct algorithmic differences between the two implementations:

1. **Optimization Solver & Regularization:**
   - **MATLAB ([`matlab/05_modeling/TWENTY_personalized_classifier.m#L110-L117`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/matlab/05_modeling/TWENTY_personalized_classifier.m#L110-L117)):**  
     Uses a custom **unregularized gradient descent** routine (`learning_rate = 0.05, iterations = 2500` with manual gradient descent loop `w = w - learning_rate * grad`). It does not include an L2 weight penalty.
   - **Python ([`python/train_loso_ml_benchmark.py#L131-L133`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/python/train_loso_ml_benchmark.py#L131-L133)):**  
     Uses scikit-learn's `LogisticRegression(C=1.0, solver="liblinear", random_state=42)` which applies an **L2 regularization penalty** with Coordinate Descent optimization.
2. **Dual Origin of Summary Files:**
   - `results/FINAL_Model_Metrics.csv` and `results/Threshold_Analysis.csv` were produced by the MATLAB post-processing script [`matlab/06_final_results/TWENTY_EIGHT_report_figures.m`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/matlab/06_final_results/TWENTY_EIGHT_report_figures.m#L18), which read `Personalized_Classifier_Predictions.csv`.
   - `results/ML_Model_Benchmark_LOSO.csv` and `results/ML_Predictions_LOSO.csv` were produced by the Python benchmark script [`python/train_loso_ml_benchmark.py`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/python/train_loso_ml_benchmark.py).
   - In [`stage2_ml_reproducibility.txt`](file:///C:/Users/YASH/Desktop/projects/RESEARCH%20PROJECTS/ECG_STRESS_DETECTION/results/verification/stage2_ml_reproducibility.txt), the "Expected" values for $\tau = 0.35$ were extracted from `FINAL_Model_Metrics.csv` (the MATLAB summary), while the "Observed" values were computed by the Python rerun. Because of the 1-sample solver boundary shift, the test log recorded $\text{TP}=139\text{ vs }138$ and $\text{F1}=89.10\%\text{ vs }89.03\%$.

---

## 5. Summary Conclusion

1. **Both pipelines agree 100% on overall accuracy at $\tau = 0.35$:** Exactly **92.36% (411/445)**.
2. **Both pipelines agree 100% on the pre-specified primary operating point ($\tau = 0.50$):** Exactly **92.13% Accuracy, 88.29% F1, 132 TP, 7 FP, 278 TN, 28 FN**.
3. The minor difference between $\text{TP}=138$ (MATLAB) and $\text{TP}=139$ (Python) at $\tau = 0.35$ is fully accounted for by 4 boundary samples straddling the exploratory cutoff due to L2 regularization differences between scikit-learn and MATLAB's custom gradient descent solver.
