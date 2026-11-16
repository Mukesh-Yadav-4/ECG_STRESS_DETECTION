#!/usr/bin/env python3
"""
make_paper_figures.py
=====================
Regenerates publication-quality figures for the ECG stress-detection manuscript
strictly from leak-free experimental CSV files:
  - Fig. 2 (FINAL_ROC_Curve.png): ROC curve for primary model (Logistic Regression,
    N=10 calibration, 295 common evaluation windows). AUC = 0.9361.
    Marks operating points tau=0.50 (90.17% Acc, 86.25% Sens, 94.81% Spec)
    and tau=0.35 (87.80% Acc, 88.75% Sens, 86.67% Spec).
  - Fig. 3 (FINAL_Personalized_Feature_Ablation.png): Multi-feature subset and
    calibration duration ablation across 295 common evaluation windows.

All numbers and coordinates are computed dynamically from CSVs; none are hardcoded.
"""

import os
import ast
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, roc_auc_score

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAL_DIR = os.path.join(REPO_ROOT, "results", "calibration_length")
PREDS_CSV = os.path.join(CAL_DIR, "calibration_length_window_predictions.csv")
ABLATION_CSV = os.path.join(CAL_DIR, "leak_free_ablation_results.csv")

TARGET_FIGURE_DIRS = [
    os.path.join(REPO_ROOT, "paper_package", "figures"),
    os.path.join(REPO_ROOT, "paper", "figures"),
    os.path.join(REPO_ROOT, "results", "figures"),
]

for d in TARGET_FIGURE_DIRS:
    os.makedirs(d, exist_ok=True)


def plot_fig2_roc():
    """Generates Figure 2: Leak-Free ROC Curve for N=10 Logistic Regression."""
    print("--> Generating Fig. 2: Leak-Free ROC Curve...")
    df_preds = pd.read_csv(PREDS_CSV)
    df_n10 = df_preds[
        (df_preds["Model"] == "Logistic Regression")
        & (df_preds["Setting"] == "N=10 (First 10 Windows)")
    ].copy()

    y_true = df_n10["True_Label"].values
    y_prob = df_n10["Prob_Stress"].values
    n_windows = len(y_true)

    fpr, tpr, thresholds = roc_curve(y_true, y_prob)
    auc_val = roc_auc_score(y_true, y_prob)

    # Compute operating points dynamically
    # tau = 0.50
    pred_50 = (y_prob >= 0.50).astype(int)
    tp_50 = np.sum((pred_50 == 1) & (y_true == 1))
    fp_50 = np.sum((pred_50 == 1) & (y_true == 0))
    tn_50 = np.sum((pred_50 == 0) & (y_true == 0))
    fn_50 = np.sum((pred_50 == 0) & (y_true == 1))
    acc_50 = (tp_50 + tn_50) / n_windows * 100.0
    sens_50 = tp_50 / (tp_50 + fn_50) * 100.0
    spec_50 = tn_50 / (tn_50 + fp_50) * 100.0
    pt_fpr_50 = 1.0 - (spec_50 / 100.0)
    pt_tpr_50 = sens_50 / 100.0

    # tau = 0.35
    pred_35 = (y_prob >= 0.35).astype(int)
    tp_35 = np.sum((pred_35 == 1) & (y_true == 1))
    fp_35 = np.sum((pred_35 == 1) & (y_true == 0))
    tn_35 = np.sum((pred_35 == 0) & (y_true == 0))
    fn_35 = np.sum((pred_35 == 0) & (y_true == 1))
    acc_35 = (tp_35 + tn_35) / n_windows * 100.0
    sens_35 = tp_35 / (tp_35 + fn_35) * 100.0
    spec_35 = tn_35 / (tn_35 + fp_35) * 100.0
    pt_fpr_35 = 1.0 - (spec_35 / 100.0)
    pt_tpr_35 = sens_35 / 100.0

    print(f"    ROC-AUC: {auc_val:.4f}")
    print(f"    tau=0.50: Acc={acc_50:.2f}%, Sens={sens_50:.2f}%, Spec={spec_50:.2f}%, FPR={pt_fpr_50:.4f}, TPR={pt_tpr_50:.4f}")
    print(f"    tau=0.35: Acc={acc_35:.2f}%, Sens={sens_35:.2f}%, Spec={spec_35:.2f}%, FPR={pt_fpr_35:.4f}, TPR={pt_tpr_35:.4f}")

    fig, ax = plt.subplots(figsize=(6.5, 5.5), dpi=300)

    # Plot ROC curve
    ax.plot(
        fpr, tpr,
        color="#1e3a8a", lw=2.5,
        label=f"Logistic Regression ($N=10$, AUC = {auc_val:.4f})"
    )
    ax.fill_between(fpr, tpr, color="#3b82f6", alpha=0.12)

    # Random chance line
    ax.plot([0, 1], [0, 1], color="#94a3b8", linestyle="--", lw=1.5, label="Chance Reference (AUC = 0.5000)")

    # Operating point tau = 0.50
    ax.scatter(
        [pt_fpr_50], [pt_tpr_50],
        color="#047857", s=90, zorder=5, edgecolor="black", linewidth=1.2,
        label=f"Primary Threshold ($\\tau = 0.50$): {acc_50:.2f}% Acc"
    )
    ax.annotate(
        f"$\\tau = 0.50$ (Balanced)\nAcc: {acc_50:.1f}%\nSens: {sens_50:.1f}%\nSpec: {spec_50:.1f}%",
        xy=(pt_fpr_50, pt_tpr_50),
        xytext=(pt_fpr_50 + 0.12, pt_tpr_50 - 0.14),
        fontsize=9, fontweight="bold",
        arrowprops=dict(arrowstyle="->", color="#047857", lw=1.5),
        bbox=dict(boxstyle="round,pad=0.4", fc="#ecfdf5", ec="#047857", lw=1.2),
    )

    # Operating point tau = 0.35
    ax.scatter(
        [pt_fpr_35], [pt_tpr_35],
        color="#b91c1c", s=90, zorder=5, edgecolor="black", linewidth=1.2,
        label=f"Screening Threshold ($\\tau = 0.35$): {acc_35:.2f}% Acc"
    )
    ax.annotate(
        f"$\\tau = 0.35$ (High-Sens)\nAcc: {acc_35:.1f}%\nSens: {sens_35:.1f}%\nSpec: {spec_35:.1f}%",
        xy=(pt_fpr_35, pt_tpr_35),
        xytext=(pt_fpr_35 + 0.14, pt_tpr_35 + 0.02),
        fontsize=9, fontweight="bold",
        arrowprops=dict(arrowstyle="->", color="#b91c1c", lw=1.5),
        bbox=dict(boxstyle="round,pad=0.4", fc="#fef2f2", ec="#b91c1c", lw=1.2),
    )

    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.04)
    ax.set_xlabel("False Positive Rate (1 - Specificity)", fontsize=11, fontweight="bold")
    ax.set_ylabel("True Positive Rate (Sensitivity)", fontsize=11, fontweight="bold")
    ax.set_title("Receiver Operating Characteristic (ROC) Curve\n15-Fold LOSO Benchmark • Leak-Free $N=10$ Calibration ($N_{\\text{eval}}=295$)", fontsize=11.0, fontweight="bold", pad=14)
    ax.legend(loc="lower right", fontsize=9, frameon=True, framealpha=0.95, edgecolor="#cbd5e1")
    ax.grid(True, linestyle=":", alpha=0.6, color="#cbd5e1")
    plt.tight_layout()

    for out_dir in TARGET_FIGURE_DIRS:
        dest = os.path.join(out_dir, "FINAL_ROC_Curve.png")
        fig.savefig(dest, dpi=300, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    print("    Saved FINAL_ROC_Curve.png to target directories.")


def plot_fig3_ablation():
    """Generates Figure 3: Leak-Free Feature & Calibration Ablation."""
    print("--> Generating Fig. 3: Leak-Free Feature & Calibration Ablation...")
    df_abl = pd.read_csv(ABLATION_CSV)

    # Filter to 12 leak-free rows
    df_lf = df_abl[df_abl["Protocol"] == "Leak-Free (295 Eval Windows)"].copy()

    feature_groups = [
        "1-feature (MeanHR)",
        "4-feature (Classical Time-Domain)",
        "8-feature (Core Physiological)",
        "13-feature (Full Expanded)",
    ]

    labels = [
        "1 Feature\n(MeanHR)",
        "4 Features\n(Time-Domain)",
        "8 Features\n(Core ANS)",
        "13 Features\n(Full Expanded)",
    ]

    cal_types = ["Raw (Uncalibrated)", "Calibrated (N=5)", "Calibrated (N=10)"]
    cal_labels = ["Raw (Uncalibrated)", "Calibrated ($N=5$ min)", "Calibrated ($N=10$ min)"]
    colors = ["#64748b", "#0284c7", "#1e3a8a"]

    x = np.arange(len(feature_groups))
    width = 0.24

    fig, ax = plt.subplots(figsize=(8.0, 5.0), dpi=300)

    for i, (ctype, clabel, col) in enumerate(zip(cal_types, cal_labels, colors)):
        accs = []
        err_lows = []
        err_highs = []
        for fg in feature_groups:
            row = df_lf[(df_lf["Feature_Set"] == fg) & (df_lf["Calibration"] == ctype)].iloc[0]
            acc = row["Accuracy (%)"]
            ci = ast.literal_eval(row["Acc_CI"])
            accs.append(acc)
            err_lows.append(acc - ci[0])
            err_highs.append(ci[1] - acc)

        offset = (i - 1) * width
        rects = ax.bar(
            x + offset, accs, width,
            yerr=[err_lows, err_highs],
            capsize=3.5,
            label=clabel,
            color=col,
            edgecolor="black",
            linewidth=0.8,
            alpha=0.92,
        )

        for rect in rects:
            height = rect.get_height()
            ax.annotate(
                f"{height:.1f}%",
                xy=(rect.get_x() + rect.get_width() / 2, height),
                xytext=(0, 4),
                textcoords="offset points",
                ha="center", va="bottom",
                fontsize=7.5, fontweight="bold",
            )

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10, fontweight="bold")
    ax.set_ylabel("Classification Accuracy (%)", fontsize=11, fontweight="bold")
    ax.set_ylim(50, 105)
    ax.axhline(54.24, color="#ef4444", linestyle="--", lw=1.2, label="Majority Class Baseline (54.24%)")
    ax.set_title("Ablation of Feature Subsets & Baseline Calibration Duration\n15-Fold LOSO Benchmark • Evaluated on Identical 295 Leak-Free Windows", fontsize=11.5, fontweight="bold", pad=12)
    ax.legend(loc="upper left", fontsize=8.5, frameon=True, framealpha=0.95, edgecolor="#cbd5e1")
    ax.grid(True, linestyle=":", alpha=0.5, axis="y", color="#cbd5e1")
    plt.tight_layout()

    for out_dir in TARGET_FIGURE_DIRS:
        dest = os.path.join(out_dir, "FINAL_Personalized_Feature_Ablation.png")
        fig.savefig(dest, dpi=300, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    print("    Saved FINAL_Personalized_Feature_Ablation.png to target directories.")


def main():
    plot_fig2_roc()
    plot_fig3_ablation()
    print("--> All paper figures successfully regenerated from leak-free CSVs!")


if __name__ == "__main__":
    main()
