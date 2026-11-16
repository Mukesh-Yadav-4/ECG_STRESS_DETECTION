"""
Paired Contrasts Bootstrap Analysis
Primary Model: Logistic Regression (C=1.0, liblinear) on 295-window common evaluation set.
10,000 subject-level bootstrap resamples, seed 0.
"""

import pandas as pd
import numpy as np

def compute_metrics(y_true, y_pred):
    tp = np.sum((y_true == 1) & (y_pred == 1))
    tn = np.sum((y_true == 0) & (y_pred == 0))
    fp = np.sum((y_true == 0) & (y_pred == 1))
    fn = np.sum((y_true == 1) & (y_pred == 0))
    tot = len(y_true)
    
    acc = (tp + tn) / tot * 100.0 if tot > 0 else 0.0
    sens = tp / (tp + fn) * 100.0 if (tp + fn) > 0 else 0.0
    spec = tn / (tn + fp) * 100.0 if (tn + fp) > 0 else 0.0
    bal_acc = 0.5 * (sens + spec)
    return acc, bal_acc

def main():
    df = pd.read_csv("results/calibration_length/calibration_length_window_predictions.csv")
    df_lr = df[df["Model"] == "Logistic Regression"]
    
    subjects = np.array(sorted(df_lr["Subject"].unique()))
    n_subjs = len(subjects)
    n_resamples = 10000
    seed = 0
    
    # Organize data by setting and subject
    # setting -> subject -> (y_true, y_pred)
    settings_data = {}
    for setting in df_lr["Setting"].unique():
        sub_df = df_lr[df_lr["Setting"] == setting]
        settings_data[setting] = {}
        for s in subjects:
            s_df = sub_df[sub_df["Subject"] == s]
            settings_data[setting][s] = (
                s_df["True_Label"].values.astype(int),
                s_df["Pred_Label"].values.astype(int)
            )
            
    # Baseline settings names
    c_a = "Control (a): No Calibration"
    c_b = "Control (b): Leaky (All 19 Windows)"
    n1 = "N=1 (First 1 Windows)"
    n2 = "N=2 (First 2 Windows)"
    n3 = "N=3 (First 3 Windows)"
    n5 = "N=5 (First 5 Windows)"
    n10 = "N=10 (First 10 Windows)"
    
    contrasts = [
        ("N=1 minus Control (a)", n1, c_a),
        ("N=2 minus Control (a)", n2, c_a),
        ("N=3 minus Control (a)", n3, c_a),
        ("N=5 minus Control (a)", n5, c_a),
        ("N=10 minus Control (a)", n10, c_a),
        ("N=10 minus N=5", n10, n5),
        ("N=10 minus Control (b) [Leaky]", n10, c_b),
    ]
    
    # Compute point estimates on original 295 windows
    print("=== Point Estimates on 295-Window Evaluation Set ===")
    point_estimates = {}
    for name, setting_key in [
        ("Control (a): No Calibration", c_a),
        ("N=1", n1),
        ("N=2", n2),
        ("N=3", n3),
        ("N=5", n5),
        ("N=10", n10),
        ("Control (b): Leaky Reference", c_b),
    ]:
        all_yt = np.concatenate([settings_data[setting_key][s][0] for s in subjects])
        all_yp = np.concatenate([settings_data[setting_key][s][1] for s in subjects])
        acc, bal_acc = compute_metrics(all_yt, all_yp)
        point_estimates[setting_key] = (acc, bal_acc)
        print(f"{name:32s} | Acc: {acc:6.2f}% | Bal Acc: {bal_acc:6.2f}%")
        
    print("\n=== Paired Contrasts with 10,000 Subject-Level Bootstrap CIs (seed=0) ===")
    
    rng = np.random.default_rng(seed)
    # Pre-generate subject resampling indices for reproducibility across all contrasts
    sampled_subjs_all = [rng.choice(subjects, size=n_subjs, replace=True) for _ in range(n_resamples)]
    
    results = []
    
    for label, set_A, set_B in contrasts:
        pt_acc_diff = point_estimates[set_A][0] - point_estimates[set_B][0]
        pt_bal_acc_diff = point_estimates[set_A][1] - point_estimates[set_B][1]
        
        diff_acc_boot = np.zeros(n_resamples)
        diff_bal_acc_boot = np.zeros(n_resamples)
        
        for b in range(n_resamples):
            s_list = sampled_subjs_all[b]
            
            yt_A = np.concatenate([settings_data[set_A][s][0] for s in s_list])
            yp_A = np.concatenate([settings_data[set_A][s][1] for s in s_list])
            acc_A, bal_A = compute_metrics(yt_A, yp_A)
            
            yt_B = np.concatenate([settings_data[set_B][s][0] for s in s_list])
            yp_B = np.concatenate([settings_data[set_B][s][1] for s in s_list])
            acc_B, bal_B = compute_metrics(yt_B, yp_B)
            
            diff_acc_boot[b] = acc_A - acc_B
            diff_bal_acc_boot[b] = bal_A - bal_B
            
        ci_acc_low, ci_acc_high = np.percentile(diff_acc_boot, 2.5), np.percentile(diff_acc_boot, 97.5)
        ci_bal_low, ci_bal_high = np.percentile(diff_bal_acc_boot, 2.5), np.percentile(diff_bal_acc_boot, 97.5)
        
        acc_sig = (ci_acc_low > 0 or ci_acc_high < 0)
        bal_sig = (ci_bal_low > 0 or ci_bal_high < 0)
        
        results.append({
            "Contrast": label,
            "Delta_Acc (%)": pt_acc_diff,
            "Acc_CI_Low (%)": ci_acc_low,
            "Acc_CI_High (%)": ci_acc_high,
            "Acc_Significant": acc_sig,
            "Delta_Bal_Acc (%)": pt_bal_acc_diff,
            "Bal_CI_Low (%)": ci_bal_low,
            "Bal_CI_High (%)": ci_bal_high,
            "Bal_Significant": bal_sig,
        })
        
        print(f"--- {label} ---")
        print(f"  Delta Accuracy:     {pt_acc_diff:+6.2f} pp [95% CI: {ci_acc_low:+6.2f}, {ci_acc_high:+6.2f}] | Significant (CI excludes 0): {acc_sig}")
        print(f"  Delta Balanced Acc: {pt_bal_acc_diff:+6.2f} pp [95% CI: {ci_bal_low:+6.2f}, {ci_bal_high:+6.2f}] | Significant (CI excludes 0): {bal_sig}")

    df_out = pd.DataFrame(results)
    df_out.to_csv("results/calibration_length/paired_contrasts_bootstrap.csv", index=False)
    print("\nSaved to results/calibration_length/paired_contrasts_bootstrap.csv")

if __name__ == "__main__":
    main()
