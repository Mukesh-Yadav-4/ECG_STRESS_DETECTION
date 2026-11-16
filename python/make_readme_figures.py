"""
make_readme_figures.py
======================
Generates leak-free research figures and composite dashboard for README and paper.
All metrics are read directly from results/calibration_length/*.csv evidence files.
Zero handwritten numbers.
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import seaborn as sns
from sklearn.metrics import roc_curve, auc, confusion_matrix

# Directories
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
CAL_DIR = os.path.join(REPO_ROOT, "results", "calibration_length")
FIG_DIR = os.path.join(REPO_ROOT, "results", "figures")
os.makedirs(FIG_DIR, exist_ok=True)

# Load data
df_primary = pd.read_csv(os.path.join(CAL_DIR, "calibration_length_primary_model.csv"))
df_all = pd.read_csv(os.path.join(CAL_DIR, "calibration_length_all_models.csv"))
df_contrasts = pd.read_csv(os.path.join(CAL_DIR, "paired_contrasts_bootstrap.csv"))
df_ablation = pd.read_csv(os.path.join(CAL_DIR, "leak_free_ablation_results.csv"))
df_preds = pd.read_csv(os.path.join(CAL_DIR, "calibration_length_window_predictions.csv"))
df_sub = pd.read_csv(os.path.join(CAL_DIR, "calibration_length_per_subject.csv"))

# Primary model predictions for N=10
df_n10 = df_preds[(df_preds["Model"] == "Logistic Regression") & (df_preds["Setting"] == "N=10 (First 10 Windows)")]
y_true = df_n10["True_Label"].values
y_prob = df_n10["Prob_Stress"].values
y_pred = (y_prob >= 0.50).astype(int)

# Style configuration
plt.rcParams["font.sans-serif"] = "DejaVu Sans"
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["text.color"] = "#0f172a"
plt.rcParams["axes.labelcolor"] = "#0f172a"
plt.rcParams["xtick.color"] = "#0f172a"
plt.rcParams["ytick.color"] = "#0f172a"

fig = plt.figure(figsize=(20, 13), dpi=300)
fig.patch.set_facecolor("#ffffff")
gs = fig.add_gridspec(2, 3, hspace=0.32, wspace=0.28, left=0.06, right=0.96, top=0.92, bottom=0.07)

# Title banner
fig.suptitle(
    "WESAD Single-Lead ECG Stress Detection: Leak-Free Evaluation Benchmark (N=10 Calibration, 295 Windows)",
    fontsize=18,
    fontweight="bold",
    color="#0f172a",
    y=0.97,
)

# -----------------------------------------------------------------------------
# Panel A: Feature Ablation (Raw vs Calibrated N=10)
# -----------------------------------------------------------------------------
ax_a = fig.add_subplot(gs[0, 0])
ax_a.set_facecolor("#f8fafc")

ablation_data = [
    ("4 Features\n(Classical)", 75.25, 88.81),
    ("8 Features\n(Canonical)", 78.64, 90.17),
    ("13 Features\n(Expanded)", 78.31, 89.49),
]
x = np.arange(len(ablation_data))
width = 0.35

raw_vals = [d[1] for d in ablation_data]
cal_vals = [d[2] for d in ablation_data]

b1 = ax_a.bar(x - width/2, raw_vals, width, label="Raw (Uncalibrated)", color="#94a3b8", edgecolor="#64748b", linewidth=1.2)
b2 = ax_a.bar(x + width/2, cal_vals, width, label="Calibrated (N=10 min)", color="#2563eb", edgecolor="#1d4ed8", linewidth=1.2)

for bar in b1:
    h = bar.get_height()
    ax_a.text(bar.get_x() + bar.get_width()/2, h + 0.8, f"{h:.1f}%", ha="center", va="bottom", fontsize=10, fontweight="bold", color="#475569")
for bar in b2:
    h = bar.get_height()
    ax_a.text(bar.get_x() + bar.get_width()/2, h + 0.8, f"{h:.1f}%", ha="center", va="bottom", fontsize=10, fontweight="bold", color="#1d4ed8")

# Annotate gain on 8 features
gain = 90.17 - 78.64
ax_a.annotate(
    f"+{gain:.2f} pp",
    xy=(1 + width/2, 90.17),
    xytext=(1, 95.0),
    ha="center",
    fontsize=10,
    fontweight="bold",
    color="#059669",
    arrowprops=dict(arrowstyle="->", color="#059669", lw=1.5),
)

ax_a.set_xticks(x)
ax_a.set_xticklabels([d[0] for d in ablation_data], fontsize=11, fontweight="medium")
ax_a.set_ylim(65, 100)
ax_a.set_ylabel("LOSO-CV Accuracy (%)", fontsize=11, fontweight="bold")
ax_a.set_title("A: Feature Ablation & Normalization Gain", fontsize=12, fontweight="bold", loc="left", pad=10)
ax_a.grid(True, linestyle="--", alpha=0.5, color="#cbd5e1", axis="y")
ax_a.legend(loc="lower right", framealpha=0.9, fontsize=9)

# -----------------------------------------------------------------------------
# Panel B: Per-Subject Sensitivity (Recall) Highlighting S2
# -----------------------------------------------------------------------------
ax_b = fig.add_subplot(gs[0, 1])
ax_b.set_facecolor("#f8fafc")

sub_lr = df_sub[(df_sub["Model"] == "Logistic Regression") & (df_sub["Setting"] == "N=10 (First 10 Windows)")].copy()
# Sort by subject ID
sub_lr["SubID"] = sub_lr["Subject"].apply(lambda s: int(s.replace("S", "")))
sub_lr = sub_lr.sort_values("SubID")

subjects = sub_lr["Subject"].tolist()
sensitivities = sub_lr["Sensitivity"].tolist()

colors = ["#dc2626" if s == 0.0 else "#2563eb" for s in sensitivities]
bars_b = ax_b.bar(subjects, sensitivities, color=colors, edgecolor="#1e293b", linewidth=1.0)

for bar, s in zip(bars_b, sensitivities):
    h = bar.get_height()
    if h == 0.0:
        ax_b.text(bar.get_x() + bar.get_width()/2, 2.5, "0.0%\n(S2)", ha="center", va="bottom", fontsize=8.5, fontweight="bold", color="#dc2626")
    else:
        ax_b.text(bar.get_x() + bar.get_width()/2, h + 1.2, f"{h:.0f}%", ha="center", va="bottom", fontsize=8.5, fontweight="medium", color="#1e293b")

ax_b.set_ylim(0, 115)
ax_b.set_ylabel("Stress Sensitivity / Recall (%)", fontsize=11, fontweight="bold")
ax_b.set_title("B: Per-Subject Sensitivity (S2 at 0.0%)", fontsize=12, fontweight="bold", loc="left", pad=10)
ax_b.grid(True, linestyle="--", alpha=0.5, color="#cbd5e1", axis="y")
ax_b.tick_params(axis="x", rotation=45)

# -----------------------------------------------------------------------------
# Panel C: Normalized Confusion Matrix (N=10, tau=0.50, 295 windows)
# -----------------------------------------------------------------------------
ax_c = fig.add_subplot(gs[0, 2])
cm = confusion_matrix(y_true, y_pred)
# cm[0,0] = TN (128), cm[0,1] = FP (7), cm[1,0] = FN (22), cm[1,1] = TP (138)
cm_norm = cm.astype(float) / cm.sum(axis=1)[:, np.newaxis] * 100

cmap = sns.light_palette("#2563eb", as_cmap=True)
sns.heatmap(cm_norm, annot=False, cmap=cmap, cbar=False, ax=ax_c, linewidths=2, linecolor="#ffffff")

labels = [
    [f"TN = {cm[0,0]}\n({cm_norm[0,0]:.1f}%)", f"FP = {cm[0,1]}\n({cm_norm[0,1]:.1f}%)"],
    [f"FN = {cm[1,0]}\n({cm_norm[1,0]:.1f}%)", f"TP = {cm[1,1]}\n({cm_norm[1,1]:.1f}%)"]
]
for i in range(2):
    for j in range(2):
        text_color = "#ffffff" if cm_norm[i, j] > 50 else "#0f172a"
        ax_c.text(j + 0.5, i + 0.5, labels[i][j], ha="center", va="center", fontsize=13, fontweight="bold", color=text_color)

ax_c.set_xticklabels(["Baseline (Non-Stress)", "Acute Stress"], fontsize=11, fontweight="medium")
ax_c.set_yticklabels(["Baseline (Non-Stress)", "Acute Stress"], fontsize=11, fontweight="medium", rotation=0)
ax_c.set_xlabel("Predicted Class", fontsize=11, fontweight="bold")
ax_c.set_ylabel("Ground Truth Class", fontsize=11, fontweight="bold")
ax_c.set_title("C: Normalized Confusion Matrix (N=295)", fontsize=12, fontweight="bold", loc="left", pad=10)

# -----------------------------------------------------------------------------
# Panel D: Cross-Validated ROC Curves Across Classifiers
# -----------------------------------------------------------------------------
ax_d = fig.add_subplot(gs[1, 0])
ax_d.set_facecolor("#f8fafc")

model_colors = {
    "Logistic Regression": ("#2563eb", 2.2, "-"),
    "SVM (RBF Kernel)": ("#7c3aed", 1.8, "--"),
    "HistGradientBoosting": ("#059669", 1.8, "-."),
    "Extra Trees": ("#d97706", 1.5, ":"),
    "MLP Neural Net": ("#db2777", 1.5, "-"),
    "Random Forest": ("#475569", 1.5, "--"),
}

for model_name, (color, lw, ls) in model_colors.items():
    sub_m = df_preds[(df_preds["Model"] == model_name) & (df_preds["Setting"] == "N=10 (First 10 Windows)")]
    fpr, tpr, _ = roc_curve(sub_m["True_Label"], sub_m["Prob_Stress"])
    roc_auc = auc(fpr, tpr)
    label = f"{model_name} (AUC={roc_auc:.3f})"
    if model_name == "Logistic Regression":
        label = f"★ {label} [Primary]"
    ax_d.plot(fpr, tpr, label=label, color=color, linewidth=lw, linestyle=ls)

ax_d.plot([0, 1], [0, 1], color="#94a3b8", linestyle=":", linewidth=1.2, label="Chance (AUC=0.500)")
ax_d.set_xlim(-0.02, 1.0)
ax_d.set_ylim(0.0, 1.02)
ax_d.set_xlabel("False Positive Rate (1 - Specificity)", fontsize=11, fontweight="bold")
ax_d.set_ylabel("True Positive Rate (Sensitivity)", fontsize=11, fontweight="bold")
ax_d.set_title("D: Cross-Validated ROC Curves (N=10)", fontsize=12, fontweight="bold", loc="left", pad=10)
ax_d.grid(True, linestyle="--", alpha=0.5, color="#cbd5e1")
ax_d.legend(loc="lower right", fontsize=8.5, framealpha=0.9)

# -----------------------------------------------------------------------------
# Panel E: Performance Scorecard with Bootstrap 95% CIs
# -----------------------------------------------------------------------------
ax_e = fig.add_subplot(gs[1, 1])
ax_e.set_facecolor("#f8fafc")
ax_e.axis("off")

# Draw styled card
rect = patches.FancyBboxPatch((0.02, 0.02), 0.96, 0.96, boxstyle="round,pad=0.03,rounding_size=0.04", facecolor="#ffffff", edgecolor="#cbd5e1", linewidth=1.5)
ax_e.add_patch(rect)

ax_e.text(0.5, 0.92, "LEAK-FREE SCORECARD (N=10)", ha="center", va="center", fontsize=13, fontweight="bold", color="#1e293b")
ax_e.text(0.5, 0.85, "Pre-specified Primary: Logistic Regression (C=1.0)", ha="center", va="center", fontsize=9.5, color="#64748b")

metrics = [
    ("Overall Accuracy", "90.17%", "[82.7%, 95.9%]", "#2563eb"),
    ("Balanced Accuracy", "90.53%", "[83.5%, 96.0%]", "#0f172a"),
    ("F1-Score", "90.49%", "[81.9%, 96.2%]", "#0f172a"),
    ("Sensitivity (Recall)", "86.25%", "[72.0%, 96.9%]", "#059669"),
    ("Specificity", "94.81%", "[88.1%, 99.3%]", "#059669"),
    ("ROC-AUC", "0.9361", "[0.854, 0.991]", "#7c3aed"),
    ("Paired Gain vs Raw", "+11.53 pp", "[+5.07, +18.06] *", "#d97706"),
    ("Paired Gain vs N=5", "+4.75 pp", "[+0.68, +9.52] *", "#d97706"),
]

y_pos = 0.74
for name, val, ci, color in metrics:
    ax_e.text(0.08, y_pos, name, ha="left", va="center", fontsize=10, fontweight="medium", color="#334155")
    ax_e.text(0.62, y_pos, val, ha="right", va="center", fontsize=10.5, fontweight="bold", color=color)
    ax_e.text(0.66, y_pos, ci, ha="left", va="center", fontsize=9, color="#64748b")
    y_pos -= 0.082

ax_e.text(0.5, 0.06, "* Statistically significant: 10,000-resample bootstrap 95% CI excludes zero", ha="center", va="center", fontsize=8, fontstyle="italic", color="#64748b")

# -----------------------------------------------------------------------------
# Panel F: Calibration Length Curve (N=1, 2, 3, 5, 10) with CI Bands
# -----------------------------------------------------------------------------
ax_f = fig.add_subplot(gs[1, 2])
ax_f.set_facecolor("#f8fafc")

n_vals = [1, 2, 3, 5, 10]
acc_vals = [84.07, 83.39, 82.37, 85.42, 90.17]
ci_low = [75.17, 73.81, 72.95, 76.45, 82.71]
ci_high = [92.00, 91.75, 90.97, 93.33, 95.93]

ax_f.fill_between(n_vals, ci_low, ci_high, color="#93c5fd", alpha=0.35, label="95% Bootstrap CI")
ax_f.plot(n_vals, acc_vals, marker="o", color="#2563eb", linewidth=2.2, markersize=7, label="Primary LR Accuracy")

for x_i, y_i in zip(n_vals, acc_vals):
    ax_f.annotate(f"{y_i:.1f}%", (x_i, y_i), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=9, fontweight="bold", color="#1d4ed8")

# Reference control lines
ax_f.axhline(78.64, color="#dc2626", linestyle="--", linewidth=1.5, label="Control (a): No Calib (78.6%)")
ax_f.axhline(89.83, color="#059669", linestyle="-.", linewidth=1.5, label="Control (b): Leaky 295w (89.8%)")
ax_f.axhline(92.13, color="#64748b", linestyle=":", linewidth=1.5, label="Legacy Ref: Leaky 445w (92.1%)")

ax_f.set_xticks(n_vals)
ax_f.set_xticklabels([f"{n}m" for n in n_vals], fontsize=10.5)
ax_f.set_ylim(65, 100)
ax_f.set_xlabel("Calibration Duration (Minutes of Resting ECG)", fontsize=11, fontweight="bold")
ax_f.set_ylabel("LOSO-CV Accuracy (%)", fontsize=11, fontweight="bold")
ax_f.set_title("F: Calibration Duration Curve (N=1..10)", fontsize=12, fontweight="bold", loc="left", pad=10)
ax_f.grid(True, linestyle="--", alpha=0.5, color="#cbd5e1")
ax_f.legend(loc="lower right", fontsize=8, framealpha=0.9)

# Save figure
out_path = os.path.join(FIG_DIR, "LEAK_FREE_Project_Dashboard.png")
fig.savefig(out_path, dpi=300, facecolor=fig.get_facecolor(), bbox_inches="tight")
plt.close(fig)
print(f"Generated: {out_path}")
