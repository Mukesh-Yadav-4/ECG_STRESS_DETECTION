"""
plot_ml_evaluation.py
=====================
Publication-grade research figures for the WESAD ECG Machine Learning Benchmark.
Audited for scientific accuracy, neutral terminology, exact metric tracking,
and consistent visual hierarchy across 15 Leave-One-Subject-Out (LOSO) folds.

Generates:
1. ML_Model_Comparison_ROC.png: Multi-model ROC curves with verified AUC.
2. ML_Model_Comparison_PR.png: Multi-model Precision-Recall curves with verified PR-AUC.
3. ML_Model_Benchmark_Bars.png: Grouped performance metrics across all 6 classifiers.
4. ML_Feature_Importance_Permutation.png: Permutation importance and logistic regression odds ratios.
5. ML_Confusion_Matrices_Grid.png: 2x3 grid of normalized confusion matrices (Baseline vs. Stress).
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
from sklearn.metrics import (
    roc_curve,
    auc,
    precision_recall_curve,
    average_precision_score,
    confusion_matrix,
)

import argparse
from matplotlib.colors import LinearSegmentedColormap

# -----------------------------------------------------------------------------
# Fixed Model Order across All Figures
# -----------------------------------------------------------------------------
ORDERED_MODELS = [
    "Logistic Regression",
    "MLP Neural Net",
    "SVM (RBF Kernel)",
    "Random Forest",
    "Extra Trees",
    "HistGradientBoosting",
]

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
FIGURES_DIR = os.path.join(RESULTS_DIR, "figures", "python")
ROOT_FIGURES_DIR = os.path.join(RESULTS_DIR, "figures")
os.makedirs(FIGURES_DIR, exist_ok=True)

PREDS_FILE = os.path.join(RESULTS_DIR, "ML_Predictions_LOSO.csv")
BENCHMARK_FILE = os.path.join(RESULTS_DIR, "ML_Model_Benchmark_LOSO.csv")
IMPORTANCE_FILE = os.path.join(RESULTS_DIR, "ML_Feature_Importance_Permutation.csv")


def get_theme_palette(theme="light"):
    """Returns color dictionary and configures matplotlib styling based on theme."""
    if theme == "light":
        plt.style.use("default")
        palette = {
            "bg": "#ffffff",
            "card_bg": "#ffffff",
            "text_primary": "#000000",   # Pure deep black for ultra-crisp publication readability
            "text_muted": "#1e293b",     # Dark charcoal slate (never faint or washed-out)
            "grid_color": "#e2e8f0",
            "model_colors": {
                "Logistic Regression": "#2563eb",   # Royal Blue
                "MLP Neural Net": "#ea580c",        # Tangerine Orange
                "SVM (RBF Kernel)": "#059669",      # Emerald Green
                "Random Forest": "#d97706",         # Amber
                "Extra Trees": "#7c3aed",           # Deep Violet
                "HistGradientBoosting": "#0891b2",  # Ocean Teal
            },
            "bar_metrics": ["#2563eb", "#059669", "#ea580c", "#7c3aed"],
            "perm_colors": {"LR": "#2563eb", "RF": "#d97706"},
            "or_colors": {"stress": "#dc2626", "baseline": "#059669"},
        }
    else:
        plt.style.use("dark_background")
        palette = {
            "bg": "#0a0d17",
            "card_bg": "#121728",
            "text_primary": "#f2f7ff",
            "text_muted": "#a6bfe0",
            "grid_color": "#242e47",
            "model_colors": {
                "Logistic Regression": "#ff386b",   # Cyber-Ruby
                "MLP Neural Net": "#ff9100",        # Pulsar Orange
                "SVM (RBF Kernel)": "#00e0fa",      # Electric Cyan
                "Random Forest": "#ffbc2e",         # Solar Gold
                "Extra Trees": "#b388ff",           # Nebula Purple
                "HistGradientBoosting": "#00e676",  # Emerald Green
            },
            "bar_metrics": ["#00e0fa", "#ffbc2e", "#ff386b", "#00e676"],
            "perm_colors": {"LR": "#ff386b", "RF": "#ffbc2e"},
            "or_colors": {"stress": "#ff386b", "baseline": "#00e0fa"},
        }

    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]
    plt.rcParams["figure.facecolor"] = palette["bg"]
    plt.rcParams["axes.facecolor"] = palette["card_bg"]
    plt.rcParams["axes.edgecolor"] = palette["grid_color"]
    plt.rcParams["axes.labelcolor"] = palette["text_primary"]
    plt.rcParams["xtick.color"] = palette["text_muted"]
    plt.rcParams["ytick.color"] = palette["text_muted"]
    plt.rcParams["text.color"] = palette["text_primary"]
    plt.rcParams["grid.color"] = palette["grid_color"]
    plt.rcParams["grid.alpha"] = 0.7 if theme == "light" else 0.65

    return palette


# -----------------------------------------------------------------------------
# 1. Multi-Model ROC Comparison
# -----------------------------------------------------------------------------
def plot_roc_curves(df_preds, pal, theme="light"):
    """Plot multi-model ROC curves with verified AUC values in fixed model order."""
    fig, ax = plt.subplots(figsize=(8.6, 6.6), dpi=300)
    fig.patch.set_facecolor(pal["bg"])
    ax.set_facecolor(pal["card_bg"])

    for model in ORDERED_MODELS:
        sub = df_preds[df_preds["Model"] == model]
        if sub.empty:
            continue
        y_true = sub["True_Label"].values
        y_prob = sub["Prob_Stress"].values

        fpr, tpr, _ = roc_curve(y_true, y_prob)
        roc_auc = auc(fpr, tpr)
        color = pal["model_colors"][model]
        ax.plot(
            fpr,
            tpr,
            label=f"{model} (AUC = {roc_auc:.4f})",
            linewidth=2.2,
            color=color,
        )

    ax.plot([0, 1], [0, 1], "--", color=pal["text_muted"], alpha=0.7, linewidth=1.2, label="Chance Level (AUC = 0.5000)")
    ax.set_xlim([-0.02, 1.02])
    ax.set_ylim([-0.02, 1.02])
    ax.set_xlabel("False Positive Rate (1 - Specificity)", fontsize=11, fontweight="bold", color=pal["text_primary"])
    ax.set_ylabel("True Positive Rate (Sensitivity / Recall)", fontsize=11, fontweight="bold", color=pal["text_primary"])
    ax.set_title(
        "WESAD 15-Fold LOSO: Multi-Model ROC Comparison",
        fontsize=13,
        fontweight="bold",
        color=pal["text_primary"],
        pad=12,
    )

    ax.legend(
        loc="lower right",
        frameon=True,
        facecolor=pal["bg"],
        edgecolor=pal["grid_color"],
        labelcolor=pal["text_primary"],
        fontsize=9.5,
    )
    ax.grid(True, linestyle="--", alpha=0.7, color=pal["grid_color"])

    out_path = os.path.join(FIGURES_DIR, "ML_Model_Comparison_ROC.png")
    plt.tight_layout(pad=1.5)
    plt.savefig(out_path, dpi=300, facecolor=pal["bg"])
    plt.close()

    root_out = os.path.join(ROOT_FIGURES_DIR, "ML_Model_Comparison_ROC.png")
    try:
        import shutil
        shutil.copyfile(out_path, root_out)
    except Exception:
        pass
    print(f"Generated: {out_path}")


# -----------------------------------------------------------------------------
# 2. Multi-Model Precision-Recall Curves
# -----------------------------------------------------------------------------
def plot_pr_curves(df_preds, pal, theme="light"):
    """Plot Precision-Recall curves with verified PR-AUC in fixed model order."""
    fig, ax = plt.subplots(figsize=(8.6, 6.6), dpi=300)
    fig.patch.set_facecolor(pal["bg"])
    ax.set_facecolor(pal["card_bg"])

    baseline_prev = (df_preds["True_Label"] == 1).mean()

    for model in ORDERED_MODELS:
        sub = df_preds[df_preds["Model"] == model]
        if sub.empty:
            continue
        y_true = sub["True_Label"].values
        y_prob = sub["Prob_Stress"].values

        precision, recall, _ = precision_recall_curve(y_true, y_prob)
        ap = average_precision_score(y_true, y_prob)
        color = pal["model_colors"][model]
        ax.plot(
            recall,
            precision,
            label=f"{model} (PR-AUC = {ap:.4f})",
            linewidth=2.2,
            color=color,
        )

    ax.axhline(
        y=baseline_prev,
        color=pal["text_muted"],
        linestyle="--",
        linewidth=1.2,
        alpha=0.7,
        label=f"No-Skill Baseline (Prevalence = {baseline_prev:.3f})",
    )
    ax.set_xlim([-0.02, 1.02])
    ax.set_ylim([0.25, 1.02])
    ax.set_xlabel("Recall / Sensitivity (Proportion of Real Stress Caught)", fontsize=11, fontweight="bold", color=pal["text_primary"])
    ax.set_ylabel("Precision (Positive Predictive Value: Real Stress / All Flags)", fontsize=11, fontweight="bold", color=pal["text_primary"])
    ax.set_title(
        "WESAD 15-Fold LOSO: Multi-Model Precision–Recall Curves",
        fontsize=13,
        fontweight="bold",
        color=pal["text_primary"],
        pad=12,
    )
    ax.legend(
        loc="lower left",
        frameon=True,
        facecolor=pal["bg"],
        edgecolor=pal["grid_color"],
        labelcolor=pal["text_primary"],
        fontsize=9.5,
    )
    ax.grid(True, linestyle="--", alpha=0.7, color=pal["grid_color"])

    out_path = os.path.join(FIGURES_DIR, "ML_Model_Comparison_PR.png")
    plt.tight_layout(pad=1.5)
    plt.savefig(out_path, dpi=300, facecolor=pal["bg"])
    plt.close()

    root_out = os.path.join(ROOT_FIGURES_DIR, "ML_Model_Comparison_PR.png")
    try:
        import shutil
        shutil.copyfile(out_path, root_out)
    except Exception:
        pass
    print(f"Generated: {out_path}")


# -----------------------------------------------------------------------------
# 3. Multi-Model Benchmark Bar Chart
# -----------------------------------------------------------------------------
def plot_benchmark_bars(df_bench, pal, theme="light"):
    """Grouped bar chart of accuracy, F1-score, sensitivity, and specificity across 6 models."""
    fig, ax = plt.subplots(figsize=(13.0, 6.4), dpi=300)
    fig.patch.set_facecolor(pal["bg"])
    ax.set_facecolor(pal["card_bg"])

    df_sorted = df_bench.set_index("Model").reindex(ORDERED_MODELS).reset_index()

    metrics = ["Accuracy (%)", "F1-Score (%)", "Sensitivity/Recall (%)", "Specificity (%)"]
    metric_labels = ["Accuracy", "F1-Score", "Recall (Sensitivity)", "Specificity"]
    metric_colors = pal["bar_metrics"]

    x = np.arange(len(df_sorted))
    width = 0.19

    for i, (m, label, color) in enumerate(zip(metrics, metric_labels, metric_colors)):
        vals = df_sorted[m].values
        rects = ax.bar(x + (i - 1.5) * width, vals, width, label=label, color=color, alpha=0.92)
        for rect in rects:
            h = rect.get_height()
            ax.annotate(
                f"{h:.1f}%",
                xy=(rect.get_x() + rect.get_width() / 2, h),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=7.6,
                fontweight="bold",
                color=pal["text_primary"],
            )

    ax.set_ylabel("Cross-Validation Score (%)", fontsize=11, fontweight="bold", color=pal["text_primary"])
    ax.set_title(
        "15-Fold LOSO Machine-Learning Classifier Benchmark on WESAD\nEvaluated at Standard Classification Threshold (τ = 0.50)",
        fontsize=12.5,
        fontweight="bold",
        color=pal["text_primary"],
        pad=12,
    )
    ax.set_xticks(x)
    ax.set_xticklabels(df_sorted["Model"], fontsize=10, fontweight="bold", color=pal["text_primary"])
    ax.set_ylim([60, 112])
    ax.legend(
        loc="upper right",
        ncol=4,
        frameon=True,
        facecolor=pal["bg"],
        edgecolor=pal["grid_color"],
        labelcolor=pal["text_primary"],
        fontsize=9.5,
    )
    ax.grid(True, axis="y", linestyle="--", alpha=0.7, color=pal["grid_color"])

    out_path = os.path.join(FIGURES_DIR, "ML_Model_Benchmark_Bars.png")
    plt.tight_layout(pad=1.5)
    plt.savefig(out_path, dpi=300, facecolor=pal["bg"])
    plt.close()

    root_out = os.path.join(ROOT_FIGURES_DIR, "ML_Model_Benchmark_Bars.png")
    try:
        import shutil
        shutil.copyfile(out_path, root_out)
    except Exception:
        pass
    print(f"Generated: {out_path}")


# -----------------------------------------------------------------------------
# 4. Feature Importance & Logistic Regression Odds Ratios
# -----------------------------------------------------------------------------
def plot_feature_importance(df_imp, pal, theme="light"):
    """
    Two-panel scientific comparison:
    (A) Permutation Importance: Predictive test ROC-AUC degradation upon shuffling.
    (B) Adjusted Odds Ratios: Parametric effect size exp(beta) in multivariable Logistic Regression.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15.2, 6.2), dpi=300)
    fig.patch.set_facecolor(pal["bg"])
    ax1.set_facecolor(pal["card_bg"])
    ax2.set_facecolor(pal["card_bg"])

    feature_labels = {
        "MeanRR": "Mean RR",
        "MeanHR": "Mean HR (ΔHR)",
        "pNN50": "pNN50",
        "HR_IQR": "HR IQR",
        "SDNN": "SDNN",
        "RR_IQR": "RR IQR",
        "RR_CV": "RR CV",
        "RMSSD": "RMSSD",
    }

    # --- Subplot 1: Permutation Importance (Ranked by LR Drop) ---
    df_sorted_perm = df_imp.sort_values(by="LR_Mean_AUC_Drop", ascending=True).copy()
    df_sorted_perm["Feature_Name"] = df_sorted_perm["Feature"].map(lambda f: feature_labels.get(f, f))

    y = np.arange(len(df_sorted_perm))
    ax1.barh(y - 0.18, df_sorted_perm["LR_Mean_AUC_Drop"], color=pal["perm_colors"]["LR"], alpha=0.92, height=0.34, label="Logistic Regression")
    ax1.barh(y + 0.18, df_sorted_perm["RF_Mean_AUC_Drop"], color=pal["perm_colors"]["RF"], alpha=0.92, height=0.34, label="Random Forest")
    ax1.set_yticks(y)
    ax1.set_yticklabels(df_sorted_perm["Feature_Name"], fontsize=10, fontweight="bold", color=pal["text_primary"])
    ax1.set_xlabel("Mean Test ROC-AUC Degradation (15 LOSO Folds)", fontsize=10, fontweight="bold", color=pal["text_primary"])
    ax1.set_title(
        "(A) Permutation Feature Importance\n(Empirical Impact on Model Discrimination When Shuffled)",
        fontsize=11,
        fontweight="bold",
        color=pal["text_primary"],
        pad=10,
    )
    ax1.legend(loc="lower right", frameon=True, facecolor=pal["bg"], edgecolor=pal["grid_color"], labelcolor=pal["text_primary"], fontsize=9.2)
    ax1.grid(True, linestyle="--", alpha=0.7, color=pal["grid_color"])

    # --- Subplot 2: Logistic Regression Odds Ratios ---
    df_sorted_odds = df_imp.sort_values(by="Odds_Ratio", ascending=True).copy()
    df_sorted_odds["Feature_Name"] = df_sorted_odds["Feature"].map(lambda f: feature_labels.get(f, f))

    or_colors = [pal["or_colors"]["stress"] if val > 1.0 else pal["or_colors"]["baseline"] for val in df_sorted_odds["Odds_Ratio"]]
    bars = ax2.barh(df_sorted_odds["Feature_Name"], df_sorted_odds["Odds_Ratio"], color=or_colors, alpha=0.92, height=0.55)
    ax2.axvline(x=1.0, color=pal["text_muted"], linestyle="--", linewidth=1.2, alpha=0.8)

    for bar, val in zip(bars, df_sorted_odds["Odds_Ratio"]):
        if val < 0.30:
            offset = 0.08
            ha = "left"
        elif val <= 1.0:
            offset = -0.06
            ha = "right"
        else:
            offset = 0.08
            ha = "left"
        ax2.text(
            val + offset,
            bar.get_y() + bar.get_height() / 2,
            f"{val:.2f}×",
            va="center",
            ha=ha,
            fontsize=9.0,
            fontweight="bold",
            color=pal["text_primary"],
        )

    ax2.set_xlabel("Adjusted Odds Ratio [ exp(β) per 1-SD Feature Increase ]", fontsize=10, fontweight="bold", color=pal["text_primary"])
    ax2.set_title(
        "(B) Multivariable Logistic Regression Odds Ratios\n(Red: OR > 1.0 Stress Association  •  Green: OR < 1.0 Baseline Association)",
        fontsize=11,
        fontweight="bold",
        color=pal["text_primary"],
        pad=10,
    )
    ax2.grid(True, linestyle="--", alpha=0.7, color=pal["grid_color"])

    fig.suptitle(
        "Permutation Feature Importance and Logistic Regression Odds Ratios",
        fontsize=12.5,
        fontweight="bold",
        color=pal["text_primary"],
        y=0.98,
    )

    out_path = os.path.join(FIGURES_DIR, "ML_Feature_Importance_Permutation.png")
    plt.tight_layout(pad=1.5)
    plt.subplots_adjust(top=0.88)
    plt.savefig(out_path, dpi=300, facecolor=pal["bg"])
    plt.close()

    root_out = os.path.join(ROOT_FIGURES_DIR, "ML_Feature_Importance_Permutation.png")
    try:
        import shutil
        shutil.copyfile(out_path, root_out)
    except Exception:
        pass
    print(f"Generated: {out_path}")


# -----------------------------------------------------------------------------
# 5. Confusion Matrices (2x3 Grid)
# -----------------------------------------------------------------------------
def plot_confusion_matrices_grid(df_preds, pal, theme="light"):
    """
    Plot 2x3 grid of normalized confusion matrices in fixed model order.
    Classes: Baseline vs. Stress.
    Subplot titles formatted compactly to guarantee zero horizontal collision.
    """
    fig, axes = plt.subplots(2, 3, figsize=(15.2, 9.8), dpi=300)
    fig.patch.set_facecolor(pal["bg"])
    axes = axes.flatten()

    if theme == "light":
        matrix_cmap = sns.color_palette("Blues", as_cmap=True)
    else:
        matrix_cmap = LinearSegmentedColormap.from_list(
            "space_cyan", ["#070a14", "#0a223a", "#006978", "#00b4d8", "#00f0ff"], N=256
        )

    classes = ["Baseline", "Stress"]

    for idx, model in enumerate(ORDERED_MODELS):
        ax = axes[idx]
        ax.set_facecolor(pal["card_bg"])
        sub = df_preds[df_preds["Model"] == model]
        y_true = sub["True_Label"].values
        y_pred = sub["Pred_Label"].values

        cm = confusion_matrix(y_true, y_pred)
        cm_norm = cm.astype("float") / cm.sum(axis=1)[:, np.newaxis] * 100.0

        annot = np.empty_like(cm, dtype=object)
        annot[0, 0] = f"{cm[0, 0]}\nTrue Baseline\n({cm_norm[0, 0]:.1f}%)"
        annot[0, 1] = f"{cm[0, 1]}\nFalse Stress\n({cm_norm[0, 1]:.1f}%)"
        annot[1, 0] = f"{cm[1, 0]}\nMissed Stress\n({cm_norm[1, 0]:.1f}%)"
        annot[1, 1] = f"{cm[1, 1]}\nDetected Stress\n({cm_norm[1, 1]:.1f}%)"

        sns.heatmap(
            cm,
            annot=annot,
            fmt="",
            cmap=matrix_cmap,
            cbar=False,
            ax=ax,
            xticklabels=classes,
            yticklabels=classes,
            annot_kws={
                "fontsize": 10.0,
                "fontweight": "bold",
                "color": "#ffffff" if theme == "dark" else "#000000"
            },
        )

        # High-contrast typography: only deep navy cells (val > 180) receive white text.
        # Medium-blue cells (Detected Stress ~122-134) and pale cells get deep pure black (#000000) for clear readability.
        for text_obj in ax.texts:
            txt = text_obj.get_text()
            val = int(txt.split("\n")[0])
            if theme == "light":
                text_obj.set_color("#ffffff" if val > 180 else "#000000")
            else:
                text_obj.set_color("#ffffff")

        acc = (cm[0, 0] + cm[1, 1]) / cm.sum() * 100.0
        sens = cm[1, 1] / (cm[1, 1] + cm[1, 0]) * 100.0

        title_color = pal["model_colors"][model] if theme == "dark" else "#000000"
        ax.set_title(
            f"{model}\nAcc: {acc:.1f}%  |  Recall: {sens:.1f}% ({cm[1, 1]}/160)",
            fontsize=11.0,
            fontweight="bold",
            color=title_color,
            pad=8,
        )
        ax.set_ylabel("Actual Condition", fontsize=10.5, fontweight="bold", color="#000000" if theme == "light" else pal["text_primary"])
        ax.set_xlabel("Predicted Condition", fontsize=10.5, fontweight="bold", color="#000000" if theme == "light" else pal["text_primary"])
        ax.set_xticklabels(classes, fontsize=10.5, fontweight="bold", color="#000000" if theme == "light" else pal["text_muted"])
        ax.set_yticklabels(classes, fontsize=10.5, fontweight="bold", color="#000000" if theme == "light" else pal["text_muted"])
        ax.tick_params(colors="#000000" if theme == "light" else pal["text_muted"], labelsize=10.5)

    plt.suptitle(
        "15-Fold LOSO Confusion Matrix Comparison\nWESAD Dataset (445 Total Windows: 285 Baseline, 160 Stress)  •  Evaluated at τ = 0.50",
        fontsize=13.5,
        fontweight="bold",
        color="#000000" if theme == "light" else pal["text_primary"],
        y=0.965,
    )

    plt.subplots_adjust(top=0.86, bottom=0.07, left=0.07, right=0.97, hspace=0.38, wspace=0.30)

    out_path = os.path.join(FIGURES_DIR, "ML_Confusion_Matrices_Grid.png")
    plt.savefig(out_path, dpi=300, facecolor=pal["bg"])
    plt.close()

    root_out = os.path.join(ROOT_FIGURES_DIR, "ML_Confusion_Matrices_Grid.png")
    try:
        import shutil
        shutil.copyfile(out_path, root_out)
    except Exception:
        pass
    print(f"Generated: {out_path}")


# -----------------------------------------------------------------------------
# Main Execution Pipeline
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Generate WESAD ML Benchmark Figures")
    parser.add_argument("--theme", choices=["light", "dark"], default="light", help="Visual theme palette (default: light)")
    args = parser.parse_args()

    print(f"Generating audited, publication-grade research figures in '{args.theme}' theme...")
    if not os.path.isfile(PREDS_FILE):
        raise FileNotFoundError(f"Missing predictions file: {PREDS_FILE}. Run train_loso_ml_benchmark.py first.")

    df_preds = pd.read_csv(PREDS_FILE)
    df_bench = pd.read_csv(BENCHMARK_FILE)
    df_imp = pd.read_csv(IMPORTANCE_FILE)

    pal = get_theme_palette(args.theme)

    plot_roc_curves(df_preds, pal, theme=args.theme)
    plot_pr_curves(df_preds, pal, theme=args.theme)
    plot_benchmark_bars(df_bench, pal, theme=args.theme)
    plot_feature_importance(df_imp, pal, theme=args.theme)
    plot_confusion_matrices_grid(df_preds, pal, theme=args.theme)
    print(f"\nAll 5 ML benchmark figures generated successfully in '{args.theme}' theme!")


if __name__ == "__main__":
    main()
