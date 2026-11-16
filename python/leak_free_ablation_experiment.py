"""
Leak-Free Ablation Study
Comparing 1-feature, 4-feature, 8-feature, and 13-feature representations:
1. Raw (uncalibrated, StandardScaler only)
2. Calibrated N=5 (anchor = first 5 baseline windows, excluded from scoring)
3. Calibrated N=10 (anchor = first 10 baseline windows, excluded from scoring)
All evaluated on the SAME 295-window common evaluation set across 15 subjects (LOSO).
Pre-specified Logistic Regression (C=1.0, liblinear, random_state=42).
Includes subject-level bootstrap 95% CIs (10,000 resamples, seed 0).
Also includes the legacy 445-window all-baseline anchor reference table.
"""

import os
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from scipy.stats import rankdata

DATA_FILE = "results/WESAD_HRV_features_expanded.csv"
BOOTSTRAP_RESAMPLES = 10000
BOOTSTRAP_SEED = 0
EPS = 1e-6

FEATURE_SETS = {
    "1-feature (MeanHR)": ["MeanHR"],
    "4-feature (Classical Time-Domain)": ["MeanHR", "SDNN", "RMSSD", "pNN50"],
    "8-feature (Core Physiological)": [
        "MeanHR", "SDNN", "RMSSD", "pNN50",
        "MeanRR", "RR_CV", "RR_IQR", "HR_IQR"
    ],
    "13-feature (Full Expanded)": [
        "MeanHR", "MedianHR", "StdHR", "MinHR", "MaxHR",
        "MeanRR", "MedianRR", "SDNN", "RMSSD", "pNN50",
        "RR_CV", "RR_IQR", "HR_IQR"
    ],
}

def compute_metrics(y_true, y_pred, y_prob=None):
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
    
    n_pos = tp + fn
    n_neg = tn + fp
    if y_prob is not None and n_pos > 0 and n_neg > 0:
        r = rankdata(y_prob)
        auc = (np.sum(r[y_true == 1]) - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)
    else:
        auc = np.nan
        
    return {
        "Accuracy": acc,
        "Balanced_Accuracy": bal_acc,
        "F1": f1,
        "Sensitivity": sens,
        "Specificity": spec,
        "ROC_AUC": auc,
        "TP": tp, "TN": tn, "FP": fp, "FN": fn
    }

def run_subject_bootstrap_ci(df_preds, n_resamples=BOOTSTRAP_RESAMPLES, seed=BOOTSTRAP_SEED):
    rng = np.random.default_rng(seed)
    subjects = np.array(sorted(df_preds["Subject"].unique()))
    n_subjs = len(subjects)
    
    subj_data = {}
    for s in subjects:
        sub = df_preds[df_preds["Subject"] == s]
        subj_data[s] = (
            sub["True_Label"].values.astype(int),
            sub["Pred_Label"].values.astype(int),
            sub["Prob_Stress"].values.astype(float),
        )
        
    boot_acc = np.zeros(n_resamples)
    boot_bal = np.zeros(n_resamples)
    boot_f1 = np.zeros(n_resamples)
    boot_sens = np.zeros(n_resamples)
    boot_spec = np.zeros(n_resamples)
    
    for b in range(n_resamples):
        sampled = rng.choice(subjects, size=n_subjs, replace=True)
        yt = np.concatenate([subj_data[s][0] for s in sampled])
        yp = np.concatenate([subj_data[s][1] for s in sampled])
        
        tp = np.sum((yt == 1) & (yp == 1))
        tn = np.sum((yt == 0) & (yp == 0))
        fp = np.sum((yt == 0) & (yp == 1))
        fn = np.sum((yt == 1) & (yp == 0))
        tot = len(yt)
        
        boot_acc[b] = (tp + tn) / tot * 100.0 if tot > 0 else 0.0
        sens = tp / (tp + fn) * 100.0 if (tp + fn) > 0 else 0.0
        spec = tn / (tn + fp) * 100.0 if (tn + fp) > 0 else 0.0
        boot_sens[b] = sens
        boot_spec[b] = spec
        boot_bal[b] = 0.5 * (sens + spec)
        denom_f1 = 2 * tp + fp + fn
        boot_f1[b] = (2.0 * tp / denom_f1) * 100.0 if denom_f1 > 0 else 0.0
        
    return {
        "Acc_CI": (np.percentile(boot_acc, 2.5), np.percentile(boot_acc, 97.5)),
        "Bal_CI": (np.percentile(boot_bal, 2.5), np.percentile(boot_bal, 97.5)),
        "F1_CI": (np.percentile(boot_f1, 2.5), np.percentile(boot_f1, 97.5)),
        "Sens_CI": (np.percentile(boot_sens, 2.5), np.percentile(boot_sens, 97.5)),
        "Spec_CI": (np.percentile(boot_spec, 2.5), np.percentile(boot_spec, 97.5)),
    }

def evaluate_loso_leak_free(df, feature_cols, mode="raw", N=5):
    """
    Evaluates 15-fold LOSO on common 295 windows.
    mode in {'raw', 'calibrated'}.
    If mode=='calibrated', anchor = first N baseline windows.
    """
    subjects = sorted(df["Subject"].unique())
    records = []
    
    for test_subj in subjects:
        df_train = df[df["Subject"] != test_subj].copy()
        df_test = df[df["Subject"] == test_subj].copy()
        
        if mode == "raw":
            X_train = df_train[feature_cols].values
            y_train = (df_train["Condition"] == "Stress").astype(int).values
            
            test_eval_mask = (df_test["Condition"] == "Stress") | (
                (df_test["Condition"] == "Baseline") & (df_test["Window"] >= 11)
            )
            df_test_eval = df_test[test_eval_mask].copy()
            X_test = df_test_eval[feature_cols].values
            y_test = (df_test_eval["Condition"] == "Stress").astype(int).values
            windows = df_test_eval["Window"].values
            
        elif mode == "calibrated":
            # Train subjects: anchor on first N baseline windows, exclude those N windows from training
            X_train_list, y_train_list = [], []
            for s in df_train["Subject"].unique():
                s_df = df_train[df_train["Subject"] == s]
                anchor_mask = (s_df["Condition"] == "Baseline") & (s_df["Window"] <= N)
                b_vals = s_df.loc[anchor_mask, feature_cols].values
                if len(b_vals) == 0:
                    continue
                b_mean = np.mean(b_vals, axis=0)
                denom = np.where(np.abs(b_mean) < EPS, EPS, np.abs(b_mean))
                
                train_mask = (s_df["Condition"] == "Stress") | (
                    (s_df["Condition"] == "Baseline") & (s_df["Window"] > N)
                )
                s_train = s_df[train_mask]
                X_train_list.append((s_train[feature_cols].values - b_mean) / denom)
                y_train_list.append((s_train["Condition"] == "Stress").astype(int).values)
                
            X_train = np.vstack(X_train_list)
            y_train = np.concatenate(y_train_list)
            
            # Test subject: anchor strictly on first N baseline windows
            test_anchor_mask = (df_test["Condition"] == "Baseline") & (df_test["Window"] <= N)
            test_b_vals = df_test.loc[test_anchor_mask, feature_cols].values
            test_b_mean = np.mean(test_b_vals, axis=0)
            test_denom = np.where(np.abs(test_b_mean) < EPS, EPS, np.abs(test_b_mean))
            
            test_eval_mask = (df_test["Condition"] == "Stress") | (
                (df_test["Condition"] == "Baseline") & (df_test["Window"] >= 11)
            )
            df_test_eval = df_test[test_eval_mask].copy()
            X_test = (df_test_eval[feature_cols].values - test_b_mean) / test_denom
            y_test = (df_test_eval["Condition"] == "Stress").astype(int).values
            windows = df_test_eval["Window"].values
            
        scaler = StandardScaler()
        X_train_sc = scaler.fit_transform(X_train)
        X_test_sc = scaler.transform(X_test)
        
        clf = LogisticRegression(C=1.0, solver="liblinear", random_state=42)
        clf.fit(X_train_sc, y_train)
        
        y_pred = clf.predict(X_test_sc)
        y_prob = clf.predict_proba(X_test_sc)[:, 1]
        
        for w, yt, yp, ypr in zip(windows, y_test, y_pred, y_prob):
            records.append({
                "Subject": test_subj,
                "Window": w,
                "True_Label": yt,
                "Pred_Label": yp,
                "Prob_Stress": ypr
            })
            
    df_preds = pd.DataFrame(records)
    metrics = compute_metrics(
        df_preds["True_Label"].values,
        df_preds["Pred_Label"].values,
        df_preds["Prob_Stress"].values
    )
    ci = run_subject_bootstrap_ci(df_preds)
    return metrics, ci, df_preds

def evaluate_loso_legacy_leaky(df, feature_cols):
    """
    Legacy 445-window leaky protocol: anchor on all 19 baseline windows,
    score on all 445 windows.
    """
    subjects = sorted(df["Subject"].unique())
    records = []
    
    for test_subj in subjects:
        df_train = df[df["Subject"] != test_subj].copy()
        df_test = df[df["Subject"] == test_subj].copy()
        
        X_train_list, y_train_list = [], []
        for s in df_train["Subject"].unique():
            s_df = df_train[df_train["Subject"] == s]
            b_vals = s_df.loc[s_df["Condition"] == "Baseline", feature_cols].values
            b_mean = np.mean(b_vals, axis=0)
            denom = np.where(np.abs(b_mean) < EPS, EPS, np.abs(b_mean))
            X_train_list.append((s_df[feature_cols].values - b_mean) / denom)
            y_train_list.append((s_df["Condition"] == "Stress").astype(int).values)
            
        X_train = np.vstack(X_train_list)
        y_train = np.concatenate(y_train_list)
        
        test_b_vals = df_test.loc[df_test["Condition"] == "Baseline", feature_cols].values
        test_b_mean = np.mean(test_b_vals, axis=0)
        test_denom = np.where(np.abs(test_b_mean) < EPS, EPS, np.abs(test_b_mean))
        X_test = (df_test[feature_cols].values - test_b_mean) / test_denom
        y_test = (df_test["Condition"] == "Stress").astype(int).values
        windows = df_test["Window"].values
        
        scaler = StandardScaler()
        X_train_sc = scaler.fit_transform(X_train)
        X_test_sc = scaler.transform(X_test)
        
        clf = LogisticRegression(C=1.0, solver="liblinear", random_state=42)
        clf.fit(X_train_sc, y_train)
        
        y_pred = clf.predict(X_test_sc)
        y_prob = clf.predict_proba(X_test_sc)[:, 1]
        
        for w, yt, yp, ypr in zip(windows, y_test, y_pred, y_prob):
            records.append({
                "Subject": test_subj,
                "Window": w,
                "True_Label": yt,
                "Pred_Label": yp,
                "Prob_Stress": ypr
            })
            
    df_preds = pd.DataFrame(records)
    metrics = compute_metrics(
        df_preds["True_Label"].values,
        df_preds["Pred_Label"].values,
        df_preds["Prob_Stress"].values
    )
    ci = run_subject_bootstrap_ci(df_preds)
    return metrics, ci, df_preds

def main():
    df = pd.read_csv(DATA_FILE)
    print("Loaded data:", len(df), "windows.")
    
    rows = []
    
    # 1. Leak-Free Protocol on 295 windows: Raw, Calibrated N=5, Calibrated N=10
    configs = [
        ("Raw (Uncalibrated)", "raw", None),
        ("Calibrated (N=5)", "calibrated", 5),
        ("Calibrated (N=10)", "calibrated", 10),
    ]
    
    for fset_name, fcols in FEATURE_SETS.items():
        n_feats = len(fcols)
        for cfg_name, mode, N in configs:
            m, ci, _ = evaluate_loso_leak_free(df, fcols, mode=mode, N=N)
            rows.append({
                "Protocol": f"Leak-Free (295 Eval Windows)",
                "Configuration": f"{fset_name} - {cfg_name}",
                "Feature_Set": fset_name,
                "Num_Features": n_feats,
                "Calibration": cfg_name,
                "Accuracy (%)": round(m["Accuracy"], 2),
                "Acc_CI": f"[{ci['Acc_CI'][0]:.1f}, {ci['Acc_CI'][1]:.1f}]",
                "Balanced_Acc (%)": round(m["Balanced_Accuracy"], 2),
                "Bal_CI": f"[{ci['Bal_CI'][0]:.1f}, {ci['Bal_CI'][1]:.1f}]",
                "F1 (%)": round(m["F1"], 2),
                "F1_CI": f"[{ci['F1_CI'][0]:.1f}, {ci['F1_CI'][1]:.1f}]",
                "Sensitivity (%)": round(m["Sensitivity"], 2),
                "Sens_CI": f"[{ci['Sens_CI'][0]:.1f}, {ci['Sens_CI'][1]:.1f}]",
                "Specificity (%)": round(m["Specificity"], 2),
                "Spec_CI": f"[{ci['Spec_CI'][0]:.1f}, {ci['Spec_CI'][1]:.1f}]",
            })
            
    # 2. Legacy All-Baseline Leaky Protocol on 445 windows
    for fset_name, fcols in FEATURE_SETS.items():
        n_feats = len(fcols)
        m, ci, _ = evaluate_loso_legacy_leaky(df, fcols)
        rows.append({
            "Protocol": "Legacy Leaky (445 Windows, All-Baseline Anchor)",
            "Configuration": f"{fset_name} - Leaky All-Baseline",
            "Feature_Set": fset_name,
            "Num_Features": n_feats,
            "Calibration": "Leaky All-Baseline",
            "Accuracy (%)": round(m["Accuracy"], 2),
            "Acc_CI": f"[{ci['Acc_CI'][0]:.1f}, {ci['Acc_CI'][1]:.1f}]",
            "Balanced_Acc (%)": round(m["Balanced_Accuracy"], 2),
            "Bal_CI": f"[{ci['Bal_CI'][0]:.1f}, {ci['Bal_CI'][1]:.1f}]",
            "F1 (%)": round(m["F1"], 2),
            "F1_CI": f"[{ci['F1_CI'][0]:.1f}, {ci['F1_CI'][1]:.1f}]",
            "Sensitivity (%)": round(m["Sensitivity"], 2),
            "Sens_CI": f"[{ci['Sens_CI'][0]:.1f}, {ci['Sens_CI'][1]:.1f}]",
            "Specificity (%)": round(m["Specificity"], 2),
            "Spec_CI": f"[{ci['Spec_CI'][0]:.1f}, {ci['Spec_CI'][1]:.1f}]",
        })
        
    df_out = pd.DataFrame(rows)
    os.makedirs("results/calibration_length", exist_ok=True)
    out_csv = "results/calibration_length/leak_free_ablation_results.csv"
    df_out.to_csv(out_csv, index=False)
    print(f"\nSaved leak-free ablation results to {out_csv}\n")
    
    print("=== LEAK-FREE ABLATION TABLE (295 Evaluation Windows) ===")
    df_lf = df_out[df_out["Protocol"] == "Leak-Free (295 Eval Windows)"]
    print(df_lf[["Configuration", "Accuracy (%)", "Acc_CI", "F1 (%)", "F1_CI", "Sensitivity (%)", "Specificity (%)"]].to_string(index=False))
    
    print("\n=== LEGACY LEAKY REFERENCE TABLE (445 Windows, All-Baseline Anchor) ===")
    df_leg = df_out[df_out["Protocol"] == "Legacy Leaky (445 Windows, All-Baseline Anchor)"]
    print(df_leg[["Configuration", "Accuracy (%)", "Acc_CI", "F1 (%)", "F1_CI", "Sensitivity (%)", "Specificity (%)"]].to_string(index=False))

if __name__ == "__main__":
    main()
