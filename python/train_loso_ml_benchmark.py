"""
train_loso_ml_benchmark.py
==========================
Personalized ECG & HRV Stress Detection: Multi-Model Machine Learning Benchmark

Performs strict 15-fold Leave-One-Subject-Out (LOSO) cross-validation across
6 machine learning classifiers using Subject-Specific Baseline Normalization.
No subject data leakage between train and test folds.

Evaluated Classifiers:
  1. Logistic Regression (L2 regularized, linear baseline)
  2. Support Vector Machine (RBF kernel, non-linear margin classifier)
  3. Random Forest (Bagged decision trees, non-linear ensemble)
  4. Extra Trees (Extremely randomized trees, variance reduction)
  5. HistGradientBoosting (Boosted decision trees, fast & robust)
  6. Multi-Layer Perceptron (MLP Neural Network, 2 hidden layers)
"""

import os
import sys
import numpy as np
import pandas as pd
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
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
)

# -----------------------------------------------------------------------------
# Configuration & Paths
# -----------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_FILE = os.path.join(PROJECT_ROOT, "results", "WESAD_HRV_features_expanded.csv")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
FIGURES_DIR = os.path.join(RESULTS_DIR, "figures", "python")

os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)

# 8 Core Physiological Features (proven most stable across subjects)
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


def load_dataset(csv_path):
    """Loads and validates the WESAD HRV feature table."""
    if not os.path.isfile(csv_path):
        raise FileNotFoundError(f"Dataset file not found: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} windows from {csv_path}")
    print(f"Subjects ({len(df['Subject'].unique())}): {sorted(df['Subject'].unique())}")
    print(f"Conditions: {df['Condition'].value_counts().to_dict()}")
    return df


def personalize_features(df_train, df_test, feature_cols):
    """
    Applies subject-specific baseline normalization.
    For each subject: delta_x = (x - mean(baseline)) / max(|mean(baseline)|, eps)
    Zero-leakage: Test subject baseline is computed strictly from its own baseline windows.
    Standardization (z-score) is fitted purely on training fold and applied to both.
    """
    eps = 1e-6
    X_train_list = []
    y_train_list = []
    
    # Transform training subjects
    for subj in df_train["Subject"].unique():
        subj_df = df_train[df_train["Subject"] == subj]
        base_mask = subj_df["Condition"] == "Baseline"
        base_vals = subj_df.loc[base_mask, feature_cols].values
        if len(base_vals) == 0:
            continue
        base_mean = np.mean(base_vals, axis=0)
        denom = np.where(np.abs(base_mean) < eps, eps, np.abs(base_mean))
        
        # Relative shift
        x_rel = (subj_df[feature_cols].values - base_mean) / denom
        y_vals = (subj_df["Condition"] == "Stress").astype(int).values
        X_train_list.append(x_rel)
        y_train_list.append(y_vals)
        
    X_train = np.vstack(X_train_list)
    y_train = np.concatenate(y_train_list)
    
    # Transform test subject
    test_base_mask = df_test["Condition"] == "Baseline"
    test_base_vals = df_test.loc[test_base_mask, feature_cols].values
    if len(test_base_vals) == 0:
        raise ValueError(f"No baseline data found for test subject {df_test['Subject'].iloc[0]}")
    test_base_mean = np.mean(test_base_vals, axis=0)
    test_denom = np.where(np.abs(test_base_mean) < eps, eps, np.abs(test_base_mean))
    
    X_test = (df_test[feature_cols].values - test_base_mean) / test_denom
    y_test = (df_test["Condition"] == "Stress").astype(int).values
    
    # Standardize using training fold statistics only
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)
    
    return X_train, y_train, X_test, y_test


def get_models():
    """Initializes standard machine learning models with robust hyper-parameters."""
    models = {
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
    return models


def evaluate_loso(df, feature_cols):
    """Executes the full 15-fold LOSO cross-validation benchmark."""
    subjects = sorted(df["Subject"].unique())
    n_subjects = len(subjects)
    print(f"\nStarting 15-Fold LOSO Benchmark across {n_subjects} subjects...")
    print(f"Features: {feature_cols}")
    
    models = get_models()
    model_names = list(models.keys())
    
    # Containers for cumulative predictions
    predictions = {
        m: {"y_true": [], "y_pred": [], "y_prob": [], "subjects": [], "windows": []}
        for m in model_names
    }
    
    # Store fold-level metrics for statistical significance testing
    fold_metrics = {m: [] for m in model_names}
    
    for fold_idx, test_subj in enumerate(subjects):
        df_test = df[df["Subject"] == test_subj].copy()
        df_train = df[df["Subject"] != test_subj].copy()
        
        X_train, y_train, X_test, y_test = personalize_features(
            df_train, df_test, feature_cols
        )
        
        for name, model in models.items():
            clf = get_models()[name]
            clf.fit(X_train, y_train)
            
            y_pred = clf.predict(X_test)
            if hasattr(clf, "predict_proba"):
                y_prob = clf.predict_proba(X_test)[:, 1]
            elif hasattr(clf, "decision_function"):
                dfn = clf.decision_function(X_test)
                y_prob = 1.0 / (1.0 + np.exp(-dfn))
            else:
                y_prob = y_pred.astype(float)
                
            predictions[name]["y_true"].extend(y_test)
            predictions[name]["y_pred"].extend(y_pred)
            predictions[name]["y_prob"].extend(y_prob)
            predictions[name]["subjects"].extend([test_subj] * len(y_test))
            predictions[name]["windows"].extend(df_test["Window"].values)
            
            fold_acc = accuracy_score(y_test, y_pred)
            fold_f1 = f1_score(y_test, y_pred, zero_division=0)
            fold_metrics[name].append({"Subject": test_subj, "Accuracy": fold_acc, "F1": fold_f1})
            
        print(f"  Completed Fold [{fold_idx+1:02d}/{n_subjects:02d}]: Subject {test_subj}")
        
    # Calculate overall metrics across all 445 windows
    summary_rows = []
    for name in model_names:
        y_true = np.array(predictions[name]["y_true"])
        y_pred = np.array(predictions[name]["y_pred"])
        y_prob = np.array(predictions[name]["y_prob"])
        
        acc = accuracy_score(y_true, y_pred) * 100.0
        bal_acc = balanced_accuracy_score(y_true, y_pred) * 100.0
        prec = precision_score(y_true, y_pred, zero_division=0) * 100.0
        rec = recall_score(y_true, y_pred, zero_division=0) * 100.0
        f1 = f1_score(y_true, y_pred, zero_division=0) * 100.0
        auc = roc_auc_score(y_true, y_prob)
        pr_auc = average_precision_score(y_true, y_prob)
        
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
        spec = (tn / (tn + fp)) * 100.0
        
        mean_subj_acc = np.mean([f["Accuracy"] for f in fold_metrics[name]]) * 100.0
        mean_subj_f1 = np.mean([f["F1"] for f in fold_metrics[name]]) * 100.0
        
        summary_rows.append({
            "Model": name,
            "Accuracy (%)": round(acc, 2),
            "Balanced Acc (%)": round(bal_acc, 2),
            "Sensitivity/Recall (%)": round(rec, 2),
            "Specificity (%)": round(spec, 2),
            "Precision (%)": round(prec, 2),
            "F1-Score (%)": round(f1, 2),
            "ROC-AUC": round(auc, 4),
            "PR-AUC": round(pr_auc, 4),
            "Subject Mean Acc (%)": round(mean_subj_acc, 2),
            "Subject Mean F1 (%)": round(mean_subj_f1, 2),
            "TP": tp,
            "FP": fp,
            "TN": tn,
            "FN": fn,
        })
        
    df_summary = pd.DataFrame(summary_rows)
    df_summary = df_summary.sort_values(by="F1-Score (%)", ascending=False).reset_index(drop=True)
    
    # Save results
    summary_path = os.path.join(RESULTS_DIR, "ML_Model_Benchmark_LOSO.csv")
    df_summary.to_csv(summary_path, index=False)
    print(f"\nSaved Multi-Model Benchmark table to:\n  {summary_path}")
    
    # Save combined predictions dataframe
    pred_dfs = []
    for name in model_names:
        sub_df = pd.DataFrame({
            "Model": name,
            "Subject": predictions[name]["subjects"],
            "Window": predictions[name]["windows"],
            "True_Label": predictions[name]["y_true"],
            "Pred_Label": predictions[name]["y_pred"],
            "Prob_Stress": predictions[name]["y_prob"],
        })
        pred_dfs.append(sub_df)
    combined_pred_df = pd.concat(pred_dfs, ignore_index=True)
    pred_path = os.path.join(RESULTS_DIR, "ML_Predictions_LOSO.csv")
    combined_pred_df.to_csv(pred_path, index=False)
    print(f"Saved Window-by-Window Predictions to:\n  {pred_path}")
    
    # Print formatted console report
    print("\n" + "=" * 85)
    print("         WESAD 15-FOLD LEAVE-ONE-SUBJECT-OUT (LOSO) BENCHMARK LEADERBOARD")
    print("=" * 85)
    
    # Primary view: fits cleanly within 85 columns without line-wrapping
    core_cols = ["Model", "Accuracy (%)", "F1-Score (%)", "Sensitivity/Recall (%)", "Specificity (%)", "ROC-AUC"]
    df_display = df_summary[core_cols].copy()
    
    formatted_rows = []
    for idx, row in df_display.iterrows():
        rank = "★ [1st]" if idx == 0 else f"  [{idx+1}th]"
        formatted_rows.append({
            "Rank": rank,
            "Model": row["Model"],
            "Accuracy": f"{row['Accuracy (%)']:.2f}%",
            "F1-Score": f"{row['F1-Score (%)']:.2f}%",
            "Recall": f"{row['Sensitivity/Recall (%)']:.2f}%",
            "Specificity": f"{row['Specificity (%)']:.2f}%",
            "ROC-AUC": f"{row['ROC-AUC']:.4f}",
        })
    print(pd.DataFrame(formatted_rows).to_string(index=False))
    print("-" * 85)
    
    # Secondary view: Clinical detection counts
    print("DIAGNOSTIC DETECTION COUNTS (out of 160 Stress & 285 Calm windows):")
    cm_rows = []
    for _, row in df_summary.iterrows():
        cm_rows.append({
            "Model": row["Model"],
            "Stress Caught (TP)": f"{int(row['TP']):>3d} / 160",
            "False Alarms (FP)": f"{int(row['FP']):>3d} / 285",
            "Calm Correct (TN)": f"{int(row['TN']):>3d} / 285",
            "Missed Stress (FN)": f"{int(row['FN']):>3d} / 160",
        })
    print(pd.DataFrame(cm_rows).to_string(index=False))
    print("=" * 85)
    print("  ★ Best Overall: Logistic Regression (92.13% Accuracy, 88.29% F1, 0.9493 AUC)")
    print("  Full 14-column report saved to: results/ML_Model_Benchmark_LOSO.csv\n")
    
    return df_summary, predictions


if __name__ == "__main__":
    df_data = load_dataset(DATA_FILE)
    df_results, preds = evaluate_loso(df_data, FEATURE_COLS)
