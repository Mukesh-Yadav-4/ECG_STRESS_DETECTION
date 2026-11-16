"""
calibration_length_experiment.py
================================
Personalized ECG Stress Detection: Calibration-Length & Data-Leakage Experiment

Protocol:
---------
- Investigates the impact of baseline anchor length N in {1, 2, 3, 5, 10} windows.
- In the original benchmark, B_s was anchored on ALL 19 baseline windows and then
  those same baseline windows were scored during LOSO evaluation, representing a
  leaky reference.
- New strict protocol:
    * For each subject (both training and testing folds), anchor B_s strictly on the
      first N baseline windows in chronological order (Window 1 .. Window N).
    * Those first N baseline windows are excluded from scoring and training.
    * Both train and test subjects use the exact same calibration length N.
- Controls:
    * Control (a): No personal calibration (standardization via per-fold StandardScaler only).
    * Control (b): Leaky all-baseline reference (B_s anchored on all 19 baseline windows).
- Primary pre-specified model: Logistic Regression (C=1.0, liblinear, random_state=42).
- All 6 classifiers are evaluated under identical conditions (no model selected on test results).
- Rigorous evaluation on the SAME common evaluation windows across all settings:
  Baseline windows 11..19 (9 windows per subject) + all Stress windows (160 windows).
  Total common evaluation windows = 295.
- Statistical inference: Subject-level bootstrap 95% CIs (10,000 resamples, seed 0).
- Self-test: Automatically asserts that no scored window belongs to the subject's anchor set.
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.ensemble import (
    RandomForestClassifier,
    ExtraTreesClassifier,
    HistGradientBoostingClassifier,
)
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    recall_score,
    roc_auc_score,
    confusion_matrix,
)
from scipy.stats import rankdata

# -----------------------------------------------------------------------------
# Paths and Constants
# -----------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_FILE = os.path.join(PROJECT_ROOT, "results", "WESAD_HRV_features_expanded.csv")
OUT_DIR = os.path.join(PROJECT_ROOT, "results", "calibration_length")
os.makedirs(OUT_DIR, exist_ok=True)

FEATURE_COLS = [
    "MeanHR",
    "SDNN",
    "RMSSD",
    "pNN50",
    "MeanRR",
    "RR_CV",
    "RR_IQR",
    "HR_IQR",
]

CALIBRATION_LENGTHS = [1, 2, 3, 5, 10]
BOOTSTRAP_RESAMPLES = 10000
BOOTSTRAP_SEED = 0


def get_models():
    """Initializes the standard benchmark models."""
    return {
        "Logistic Regression": LogisticRegression(
            C=1.0, solver="liblinear", random_state=42
        ),
        "SVM (RBF Kernel)": SVC(
            kernel="rbf", C=1.5, gamma="scale", probability=True, random_state=42
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=100, max_depth=6, min_samples_split=4, random_state=42
        ),
        "Extra Trees": ExtraTreesClassifier(
            n_estimators=100, max_depth=6, min_samples_split=4, random_state=42
        ),
        "HistGradientBoosting": HistGradientBoostingClassifier(
            max_iter=100, max_depth=4, learning_rate=0.08, random_state=42
        ),
        "MLP Neural Net": MLPClassifier(
            hidden_layer_sizes=(32, 16),
            activation="relu",
            solver="adam",
            learning_rate_init=0.005,
            max_iter=1000,
            alpha=0.01,
            random_state=42,
        ),
    }


def compute_fast_metrics(y_true, y_pred, y_prob=None):
    """Computes standard metrics rapidly for bootstrap resampling."""
    tp = np.sum((y_true == 1) & (y_pred == 1))
    tn = np.sum((y_true == 0) & (y_pred == 0))
    fp = np.sum((y_true == 0) & (y_pred == 1))
    fn = np.sum((y_true == 1) & (y_pred == 0))
    total = len(y_true)

    acc = (tp + tn) / total * 100.0 if total > 0 else 0.0
    sens = tp / (tp + fn) * 100.0 if (tp + fn) > 0 else 0.0
    spec = tn / (tn + fp) * 100.0 if (tn + fp) > 0 else 0.0
    bal_acc = 0.5 * (sens + spec)
    denom_f1 = (2 * tp + fp + fn)
    f1 = (2.0 * tp / denom_f1) * 100.0 if denom_f1 > 0 else 0.0

    auc = np.nan
    if y_prob is not None and len(np.unique(y_true)) > 1:
        try:
            auc = roc_auc_score(y_true, y_prob)
        except Exception:
            auc = np.nan

    return {
        "Accuracy": acc,
        "Balanced_Accuracy": bal_acc,
        "F1": f1,
        "Sensitivity": sens,
        "Specificity": spec,
        "ROC_AUC": auc,
    }


def run_subject_bootstrap_ci(df_preds, n_resamples=BOOTSTRAP_RESAMPLES, seed=BOOTSTRAP_SEED):
    """
    Performs subject-level bootstrap resampling (cluster bootstrap)
    to compute 95% confidence intervals on pooled metrics.
    """
    rng = np.random.default_rng(seed)
    subjects = np.array(sorted(df_preds["Subject"].unique()))
    n_subjs = len(subjects)

    # Pre-organize arrays per subject for sub-second resampling
    subj_data = {}
    for s in subjects:
        sub = df_preds[df_preds["Subject"] == s]
        subj_data[s] = (
            sub["True_Label"].values.astype(int),
            sub["Pred_Label"].values.astype(int),
            sub["Prob_Stress"].values.astype(float),
        )

    boot_results = {
        "Accuracy": np.zeros(n_resamples),
        "Balanced_Accuracy": np.zeros(n_resamples),
        "F1": np.zeros(n_resamples),
        "Sensitivity": np.zeros(n_resamples),
        "Specificity": np.zeros(n_resamples),
        "ROC_AUC": np.zeros(n_resamples),
    }

    # Vectorized / fast loop
    for b in range(n_resamples):
        sampled_subjs = rng.choice(subjects, size=n_subjs, replace=True)
        yt_list = [subj_data[s][0] for s in sampled_subjs]
        yp_list = [subj_data[s][1] for s in sampled_subjs]
        ypr_list = [subj_data[s][2] for s in sampled_subjs]

        y_true = np.concatenate(yt_list)
        y_pred = np.concatenate(yp_list)
        y_prob = np.concatenate(ypr_list)

        # Fast metrics
        tp = np.sum((y_true == 1) & (y_pred == 1))
        tn = np.sum((y_true == 0) & (y_pred == 0))
        fp = np.sum((y_true == 0) & (y_pred == 1))
        fn = np.sum((y_true == 1) & (y_pred == 0))
        tot = len(y_true)

        acc = (tp + tn) / tot * 100.0 if tot > 0 else 0.0
        sens = tp / (tp + fn) * 100.0 if (tp + fn) > 0 else 0.0
        spec = tn / (tn + fp) * 100.0 if (tn + fp) > 0 else 0.0
        bal_acc = 0.5 * (sens + spec)
        denom_f1 = 2 * tp + fp + fn
        f1 = (2.0 * tp / denom_f1) * 100.0 if denom_f1 > 0 else 0.0

        boot_results["Accuracy"][b] = acc
        boot_results["Balanced_Accuracy"][b] = bal_acc
        boot_results["F1"][b] = f1
        boot_results["Sensitivity"][b] = sens
        boot_results["Specificity"][b] = spec

        # Compute ROC-AUC (fast exact Mann-Whitney formulation)
        n_pos = tp + fn
        n_neg = tn + fp
        if n_pos > 0 and n_neg > 0:
            r = rankdata(y_prob)
            boot_results["ROC_AUC"][b] = (np.sum(r[y_true == 1]) - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)
        else:
            boot_results["ROC_AUC"][b] = np.nan

    ci_dict = {}
    for metric_name, arr in boot_results.items():
        valid_arr = arr[~np.isnan(arr)]
        if len(valid_arr) > 0:
            low = np.percentile(valid_arr, 2.5)
            high = np.percentile(valid_arr, 97.5)
        else:
            low, high = np.nan, np.nan
        ci_dict[metric_name] = (low, high)

    return ci_dict


def run_experiment():
    print("=" * 80)
    print("ECG STRESS DETECTION: CALIBRATION-LENGTH EXPERIMENT (LEAK-FREE)")
    print("=" * 80)

    if not os.path.isfile(DATA_FILE):
        raise FileNotFoundError(f"Missing dataset file: {DATA_FILE}")

    df = pd.read_csv(DATA_FILE)
    subjects = sorted(df["Subject"].unique())
    print(f"Loaded dataset: {len(df)} total windows across {len(subjects)} subjects.")

    # Confirm chronological ordering of windows
    for subj in subjects:
        subj_base = df[(df["Subject"] == subj) & (df["Condition"] == "Baseline")]
        assert list(subj_base["Window"]) == sorted(list(subj_base["Window"])), (
            f"Subject {subj} baseline windows are not strictly sorted!"
        )

    # Define the common evaluation window set:
    # Baseline windows 11..19 + all Stress windows.
    # Excludes the maximum calibration length N=10 so all N in {1,2,3,5,10} are scored
    # on the EXACT SAME windows.
    common_eval_mask = (
        (df["Condition"] == "Stress")
        | ((df["Condition"] == "Baseline") & (df["Window"] >= 11))
    )
    df_common_eval = df[common_eval_mask].copy()
    print(f"Common evaluation set contains {len(df_common_eval)} windows:")
    print(f"  - Baseline (windows 11..19): {np.sum(df_common_eval['Condition'] == 'Baseline')}")
    print(f"  - Stress (all windows):      {np.sum(df_common_eval['Condition'] == 'Stress')}")

    majority_class_count = max(
        np.sum(df_common_eval["Condition"] == "Baseline"),
        np.sum(df_common_eval["Condition"] == "Stress"),
    )
    majority_baseline_acc = (majority_class_count / len(df_common_eval)) * 100.0
    print(f"  - Majority-class baseline accuracy: {majority_baseline_acc:.2f}%\n")

    # Define experiment settings to evaluate:
    # 1. New protocol: N in {1, 2, 3, 5, 10}
    # 2. Control (a): No personal calibration (StandardScaler only)
    # 3. Control (b): Leaky all-baseline reference (anchored on all 19 windows)
    settings = []
    for n in CALIBRATION_LENGTHS:
        settings.append({"type": "anchor_N", "N": n, "label": f"N={n} (First {n} Windows)"})
    settings.append({"type": "no_calibration", "N": 0, "label": "Control (a): No Calibration"})
    settings.append({"type": "leaky_all", "N": 19, "label": "Control (b): Leaky (All 19 Windows)"})

    all_preds_records = []
    summary_records = []
    per_subject_records = []

    models = get_models()
    eps = 1e-6

    # Run LOSO benchmark for every setting
    for setting in settings:
        stype = setting["type"]
        N = setting["N"]
        slabel = setting["label"]
        print(f"--> Running LOSO benchmark for: {slabel} ...")

        # Predictions store for this setting
        setting_preds = {m: {"Subject": [], "Window": [], "Condition": [], "True_Label": [], "Pred_Label": [], "Prob_Stress": []} for m in models}

        for test_subj in subjects:
            df_train = df[df["Subject"] != test_subj].copy()
            df_test = df[df["Subject"] == test_subj].copy()

            # Self-test check containers
            anchor_windows_test = []

            # Determine Anchor Bs and normalize
            if stype == "no_calibration":
                # Raw features directly, no subject baseline subtraction
                X_train = df_train[FEATURE_COLS].values
                y_train = (df_train["Condition"] == "Stress").astype(int).values

                # Evaluation windows for test
                test_eval_mask = (df_test["Condition"] == "Stress") | (
                    (df_test["Condition"] == "Baseline") & (df_test["Window"] >= 11)
                )
                df_test_eval = df_test[test_eval_mask].copy()

                X_test = df_test_eval[FEATURE_COLS].values
                y_test = (df_test_eval["Condition"] == "Stress").astype(int).values
                test_windows = df_test_eval["Window"].values
                test_conds = df_test_eval["Condition"].values

            elif stype == "leaky_all":
                # Leaky reference: anchor on all 19 baseline windows
                X_train_list, y_train_list = [], []
                for subj in df_train["Subject"].unique():
                    s_df = df_train[df_train["Subject"] == subj]
                    b_vals = s_df.loc[s_df["Condition"] == "Baseline", FEATURE_COLS].values
                    b_mean = np.mean(b_vals, axis=0)
                    denom = np.where(np.abs(b_mean) < eps, eps, np.abs(b_mean))
                    X_train_list.append((s_df[FEATURE_COLS].values - b_mean) / denom)
                    y_train_list.append((s_df["Condition"] == "Stress").astype(int).values)
                X_train = np.vstack(X_train_list)
                y_train = np.concatenate(y_train_list)

                # Test subject: anchor on all 19 baseline windows
                test_b_vals = df_test.loc[df_test["Condition"] == "Baseline", FEATURE_COLS].values
                test_b_mean = np.mean(test_b_vals, axis=0)
                test_denom = np.where(np.abs(test_b_mean) < eps, eps, np.abs(test_b_mean))

                test_eval_mask = (df_test["Condition"] == "Stress") | (
                    (df_test["Condition"] == "Baseline") & (df_test["Window"] >= 11)
                )
                df_test_eval = df_test[test_eval_mask].copy()

                X_test = (df_test_eval[FEATURE_COLS].values - test_b_mean) / test_denom
                y_test = (df_test_eval["Condition"] == "Stress").astype(int).values
                test_windows = df_test_eval["Window"].values
                test_conds = df_test_eval["Condition"].values

            elif stype == "anchor_N":
                # New strict protocol:
                # Training fold: each training subject anchors on its first N baseline windows,
                # and those first N baseline windows are excluded from training.
                X_train_list, y_train_list = [], []
                for subj in df_train["Subject"].unique():
                    s_df = df_train[df_train["Subject"] == subj]
                    anchor_mask = (s_df["Condition"] == "Baseline") & (s_df["Window"] <= N)
                    b_anchor_vals = s_df.loc[anchor_mask, FEATURE_COLS].values
                    if len(b_anchor_vals) == 0:
                        continue
                    b_mean = np.mean(b_anchor_vals, axis=0)
                    denom = np.where(np.abs(b_mean) < eps, eps, np.abs(b_mean))

                    # Non-anchor training windows
                    train_non_anchor_mask = (s_df["Condition"] == "Stress") | (
                        (s_df["Condition"] == "Baseline") & (s_df["Window"] > N)
                    )
                    s_df_train = s_df[train_non_anchor_mask]
                    X_train_list.append((s_df_train[FEATURE_COLS].values - b_mean) / denom)
                    y_train_list.append((s_df_train["Condition"] == "Stress").astype(int).values)

                X_train = np.vstack(X_train_list)
                y_train = np.concatenate(y_train_list)

                # Test subject: anchor strictly on first N baseline windows
                test_anchor_mask = (df_test["Condition"] == "Baseline") & (df_test["Window"] <= N)
                anchor_windows_test = df_test.loc[test_anchor_mask, "Window"].tolist()
                test_b_vals = df_test.loc[test_anchor_mask, FEATURE_COLS].values
                test_b_mean = np.mean(test_b_vals, axis=0)
                test_denom = np.where(np.abs(test_b_mean) < eps, eps, np.abs(test_b_mean))

                # Common evaluation mask (Windows 11..19 of baseline + all stress)
                test_eval_mask = (df_test["Condition"] == "Stress") | (
                    (df_test["Condition"] == "Baseline") & (df_test["Window"] >= 11)
                )
                df_test_eval = df_test[test_eval_mask].copy()

                X_test = (df_test_eval[FEATURE_COLS].values - test_b_mean) / test_denom
                y_test = (df_test_eval["Condition"] == "Stress").astype(int).values
                test_windows = df_test_eval["Window"].values
                test_conds = df_test_eval["Condition"].values

                # SELF-TEST: Assert no scored window is inside anchor set (Condition == "Baseline" and Window <= N)
                for cond, tw in zip(test_conds, test_windows):
                    if cond == "Baseline" and tw <= N:
                        raise AssertionError(
                            f"LEAK DETECTED! Window {tw} of Baseline for test subject {test_subj} is inside anchor set (N={N})!"
                        )

            # Fit per-fold StandardScaler
            scaler = StandardScaler()
            X_train = scaler.fit_transform(X_train)
            X_test = scaler.transform(X_test)

            # Train and predict with each model
            for m_name in models.keys():
                clf = get_models()[m_name]
                clf.fit(X_train, y_train)
                y_pred = clf.predict(X_test)
                if hasattr(clf, "predict_proba"):
                    y_prob = clf.predict_proba(X_test)[:, 1]
                elif hasattr(clf, "decision_function"):
                    dfn = clf.decision_function(X_test)
                    y_prob = 1.0 / (1.0 + np.exp(-dfn))
                else:
                    y_prob = y_pred.astype(float)

                setting_preds[m_name]["Subject"].extend([test_subj] * len(y_test))
                setting_preds[m_name]["Window"].extend(test_windows)
                setting_preds[m_name]["Condition"].extend(test_conds)
                setting_preds[m_name]["True_Label"].extend(y_test)
                setting_preds[m_name]["Pred_Label"].extend(y_pred)
                setting_preds[m_name]["Prob_Stress"].extend(y_prob)

                # Store per-subject metrics
                s_acc = accuracy_score(y_test, y_pred) * 100.0
                s_f1 = f1_score(y_test, y_pred, zero_division=0) * 100.0
                s_rec = recall_score(y_test, y_pred, zero_division=0) * 100.0
                tn_s, fp_s, fn_s, tp_s = confusion_matrix(y_test, y_pred, labels=[0, 1]).ravel()
                s_spec = (tn_s / (tn_s + fp_s)) * 100.0 if (tn_s + fp_s) > 0 else 0.0

                per_subject_records.append({
                    "Setting": slabel,
                    "Setting_Type": stype,
                    "N": N,
                    "Model": m_name,
                    "Subject": test_subj,
                    "Num_Evaluation_Windows": len(y_test),
                    "Accuracy": round(s_acc, 2),
                    "F1": round(s_f1, 2),
                    "Sensitivity": round(s_rec, 2),
                    "Specificity": round(s_spec, 2),
                })

        # Process setting predictions across all evaluation windows
        for m_name in models.keys():
            df_m_preds = pd.DataFrame(setting_preds[m_name])
            df_m_preds["Setting"] = slabel
            df_m_preds["Setting_Type"] = stype
            df_m_preds["N"] = N
            df_m_preds["Model"] = m_name
            all_preds_records.append(df_m_preds)

            y_t = df_m_preds["True_Label"].values
            y_p = df_m_preds["Pred_Label"].values
            y_pr = df_m_preds["Prob_Stress"].values

            m_scores = compute_fast_metrics(y_t, y_p, y_pr)

            # Compute 10,000 subject-bootstrap CIs
            ci_dict = run_subject_bootstrap_ci(df_m_preds, n_resamples=BOOTSTRAP_RESAMPLES, seed=BOOTSTRAP_SEED)

            summary_records.append({
                "Setting": slabel,
                "Setting_Type": stype,
                "N": N,
                "Model": m_name,
                "Is_Primary_Model": (m_name == "Logistic Regression"),
                "Num_Evaluation_Windows": len(y_t),
                "Majority_Baseline_Acc (%)": round(majority_baseline_acc, 2),
                "Accuracy (%)": round(m_scores["Accuracy"], 2),
                "Acc_CI_Low (%)": round(ci_dict["Accuracy"][0], 2),
                "Acc_CI_High (%)": round(ci_dict["Accuracy"][1], 2),
                "Balanced_Acc (%)": round(m_scores["Balanced_Accuracy"], 2),
                "Bal_Acc_CI_Low (%)": round(ci_dict["Balanced_Accuracy"][0], 2),
                "Bal_Acc_CI_High (%)": round(ci_dict["Balanced_Accuracy"][1], 2),
                "F1-Score (%)": round(m_scores["F1"], 2),
                "F1_CI_Low (%)": round(ci_dict["F1"][0], 2),
                "F1_CI_High (%)": round(ci_dict["F1"][1], 2),
                "Sensitivity (%)": round(m_scores["Sensitivity"], 2),
                "Sens_CI_Low (%)": round(ci_dict["Sensitivity"][0], 2),
                "Sens_CI_High (%)": round(ci_dict["Sensitivity"][1], 2),
                "Specificity (%)": round(m_scores["Specificity"], 2),
                "Spec_CI_Low (%)": round(ci_dict["Specificity"][0], 2),
                "Spec_CI_High (%)": round(ci_dict["Specificity"][1], 2),
                "ROC-AUC": round(m_scores["ROC_AUC"], 4) if not np.isnan(m_scores["ROC_AUC"]) else np.nan,
                "ROC_AUC_CI_Low": round(ci_dict["ROC_AUC"][0], 4) if not np.isnan(ci_dict["ROC_AUC"][0]) else np.nan,
                "ROC_AUC_CI_High": round(ci_dict["ROC_AUC"][1], 4) if not np.isnan(ci_dict["ROC_AUC"][1]) else np.nan,
            })

    # Convert to DataFrames
    df_all_summary = pd.DataFrame(summary_records)
    df_all_preds = pd.concat(all_preds_records, ignore_index=True)
    df_per_subj = pd.DataFrame(per_subject_records)

    # Filter Primary Model (Logistic Regression)
    df_primary_summary = df_all_summary[df_all_summary["Model"] == "Logistic Regression"].copy()
    df_primary_summary.reset_index(drop=True, inplace=True)

    # Save CSVs
    p_primary_csv = os.path.join(OUT_DIR, "calibration_length_primary_model.csv")
    p_all_csv = os.path.join(OUT_DIR, "calibration_length_all_models.csv")
    p_subj_csv = os.path.join(OUT_DIR, "calibration_length_per_subject.csv")
    p_preds_csv = os.path.join(OUT_DIR, "calibration_length_window_predictions.csv")

    df_primary_summary.to_csv(p_primary_csv, index=False)
    df_all_summary.to_csv(p_all_csv, index=False)
    df_per_subj.to_csv(p_subj_csv, index=False)
    df_all_preds.to_csv(p_preds_csv, index=False)

    print("\n" + "=" * 80)
    print("SAVED CSV RESULTS:")
    print(f"  - Primary Model (Logistic Regression): {p_primary_csv}")
    print(f"  - All Models:                         {p_all_csv}")
    print(f"  - Per-Subject Breakdowns:             {p_subj_csv}")
    print(f"  - Window-by-Window Predictions:       {p_preds_csv}")
    print("=" * 80)

    # Print clean formatted tables to console
    print("\nPRIMARY PRE-SPECIFIED MODEL: LOGISTIC REGRESSION (C=1.0, liblinear)")
    print("(Note: Model pre-specified prior to test evaluation; no model selected on test results)")
    print("-" * 105)
    cols_display = [
        "Setting",
        "Accuracy (%)",
        "Acc_CI_Low (%)",
        "Acc_CI_High (%)",
        "F1-Score (%)",
        "F1_CI_Low (%)",
        "F1_CI_High (%)",
        "ROC-AUC",
        "ROC_AUC_CI_Low",
        "ROC_AUC_CI_High",
    ]
    df_disp = df_primary_summary[cols_display].copy()
    df_disp["Accuracy [95% CI]"] = df_primary_summary.apply(
        lambda r: f"{r['Accuracy (%)']:.2f}% [{r['Acc_CI_Low (%)']:.1f}, {r['Acc_CI_High (%)']:.1f}]", axis=1
    )
    df_disp["F1-Score [95% CI]"] = df_primary_summary.apply(
        lambda r: f"{r['F1-Score (%)']:.2f}% [{r['F1_CI_Low (%)']:.1f}, {r['F1_CI_High (%)']:.1f}]", axis=1
    )
    df_disp["ROC-AUC [95% CI]"] = df_primary_summary.apply(
        lambda r: f"{r['ROC-AUC']:.4f} [{r['ROC_AUC_CI_Low']:.4f}, {r['ROC_AUC_CI_High']:.4f}]", axis=1
    )
    print(df_disp[["Setting", "Accuracy [95% CI]", "F1-Score [95% CI]", "ROC-AUC [95% CI]"]].to_string(index=False))
    print("-" * 105)
    print(f"Majority-class baseline: {majority_baseline_acc:.2f}% on N=295 common evaluation windows.")

    # -------------------------------------------------------------------------
    # Generate Publication Figure
    # -------------------------------------------------------------------------
    fig_path = os.path.join(OUT_DIR, "calibration_length_evaluation.png")
    generate_figure(df_primary_summary, majority_baseline_acc, fig_path)
    print(f"Saved evaluation figure to: {fig_path}")

    return df_primary_summary, df_all_summary


def generate_figure(df_primary, majority_baseline_acc, save_path):
    """Generates publication-quality figure: metric vs N with CI bands and control lines."""
    # Filter N protocol rows
    df_n = df_primary[df_primary["Setting_Type"] == "anchor_N"].copy()
    df_n = df_n.sort_values(by="N")
    ns = df_n["N"].values

    # Control rows
    row_ctrl_none = df_primary[df_primary["Setting_Type"] == "no_calibration"].iloc[0]
    row_ctrl_leaky = df_primary[df_primary["Setting_Type"] == "leaky_all"].iloc[0]

    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    fig, axes = plt.subplots(1, 3, figsize=(16, 5), dpi=300)

    # Panel 1: Accuracy
    ax = axes[0]
    ax.plot(ns, df_n["Accuracy (%)"], "o-", color="#059669", lw=2.5, markersize=8, label="Anchor Protocol (N)")
    ax.fill_between(
        ns,
        df_n["Acc_CI_Low (%)"],
        df_n["Acc_CI_High (%)"],
        color="#059669",
        alpha=0.18,
        label="Subject-Bootstrap 95% CI",
    )
    # Horizontal control lines
    ax.axhline(
        row_ctrl_none["Accuracy (%)"],
        color="#64748b",
        linestyle="--",
        lw=2.0,
        label=f"Control (a): No Calib ({row_ctrl_none['Accuracy (%)']:.1f}%)",
    )
    ax.axhline(
        row_ctrl_leaky["Accuracy (%)"],
        color="#dc2626",
        linestyle=":",
        lw=2.0,
        label=f"Control (b): Leaky Ref ({row_ctrl_leaky['Accuracy (%)']:.1f}%)",
    )
    ax.axhline(
        majority_baseline_acc,
        color="#94a3b8",
        linestyle="-.",
        lw=1.5,
        label=f"Majority Baseline ({majority_baseline_acc:.1f}%)",
    )
    ax.set_title("A. Classification Accuracy vs. N", fontsize=13, fontweight="bold", pad=10)
    ax.set_xlabel("Calibration Length N (60s Baseline Windows)", fontsize=11)
    ax.set_ylabel("Accuracy (%)", fontsize=11)
    ax.set_xticks(ns)
    ax.set_ylim(60, 100)
    ax.legend(loc="lower right", fontsize=8.5, frameon=True)

    # Panel 2: F1-Score
    ax = axes[1]
    ax.plot(ns, df_n["F1-Score (%)"], "s-", color="#7c3aed", lw=2.5, markersize=8, label="Anchor Protocol (N)")
    ax.fill_between(
        ns,
        df_n["F1_CI_Low (%)"],
        df_n["F1_CI_High (%)"],
        color="#7c3aed",
        alpha=0.18,
        label="Subject-Bootstrap 95% CI",
    )
    ax.axhline(
        row_ctrl_none["F1-Score (%)"],
        color="#64748b",
        linestyle="--",
        lw=2.0,
        label=f"Control (a): No Calib ({row_ctrl_none['F1-Score (%)']:.1f}%)",
    )
    ax.axhline(
        row_ctrl_leaky["F1-Score (%)"],
        color="#dc2626",
        linestyle=":",
        lw=2.0,
        label=f"Control (b): Leaky Ref ({row_ctrl_leaky['F1-Score (%)']:.1f}%)",
    )
    ax.set_title("B. Stress F1-Score vs. N", fontsize=13, fontweight="bold", pad=10)
    ax.set_xlabel("Calibration Length N (60s Baseline Windows)", fontsize=11)
    ax.set_ylabel("F1-Score (%)", fontsize=11)
    ax.set_xticks(ns)
    ax.set_ylim(50, 100)
    ax.legend(loc="lower right", fontsize=8.5, frameon=True)

    # Panel 3: ROC-AUC
    ax = axes[2]
    ax.plot(ns, df_n["ROC-AUC"], "^-", color="#0284c7", lw=2.5, markersize=8, label="Anchor Protocol (N)")
    ax.fill_between(
        ns,
        df_n["ROC_AUC_CI_Low"],
        df_n["ROC_AUC_CI_High"],
        color="#0284c7",
        alpha=0.18,
        label="Subject-Bootstrap 95% CI",
    )
    ax.axhline(
        row_ctrl_none["ROC-AUC"],
        color="#64748b",
        linestyle="--",
        lw=2.0,
        label=f"Control (a): No Calib ({row_ctrl_none['ROC-AUC']:.3f})",
    )
    ax.axhline(
        row_ctrl_leaky["ROC-AUC"],
        color="#dc2626",
        linestyle=":",
        lw=2.0,
        label=f"Control (b): Leaky Ref ({row_ctrl_leaky['ROC-AUC']:.3f})",
    )
    ax.set_title("C. ROC-AUC vs. N", fontsize=13, fontweight="bold", pad=10)
    ax.set_xlabel("Calibration Length N (60s Baseline Windows)", fontsize=11)
    ax.set_ylabel("ROC-AUC", fontsize=11)
    ax.set_xticks(ns)
    ax.set_ylim(0.70, 1.00)
    ax.legend(loc="lower right", fontsize=8.5, frameon=True)

    plt.suptitle(
        "Subject-Specific Baseline Calibration Length Experiment (WESAD 15-Fold LOSO Benchmark)\n"
        "Evaluated on N=295 Identical Non-Anchor Windows • Pre-Specified Logistic Regression (C=1.0) • 10,000 Bootstrap CIs",
        fontsize=13,
        fontweight="bold",
        y=1.03,
    )
    plt.tight_layout()
    plt.savefig(save_path, bbox_inches="tight")
    plt.close()


if __name__ == "__main__":
    run_experiment()
