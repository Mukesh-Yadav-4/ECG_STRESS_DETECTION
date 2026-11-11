from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch


OUT = Path(__file__).resolve().parents[1] / "paper" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

fig, ax = plt.subplots(figsize=(18, 10.5), dpi=180)
fig.patch.set_facecolor("white")
ax.set_facecolor("white")
ax.set_xlim(0, 18)
ax.set_ylim(0, 10.5)
ax.axis("off")

navy = "#12304A"
blue = "#EAF3FB"
teal = "#087F8C"
mint = "#E8F7F2"
gold = "#A56A00"
cream = "#FFF6DF"
gray = "#425466"
light_gray = "#F4F7FA"
green = "#176B4D"


def box(x, y, w, h, text, *, face, edge, size=10.5, weight="normal", color=navy):
    patch = FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.035,rounding_size=0.12",
        linewidth=1.4, edgecolor=edge, facecolor=face,
    )
    ax.add_patch(patch)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=size, color=color, weight=weight, wrap=True)
    return (x, y, w, h)


def arrow(a, b, color=gray, lw=1.5, style="-|>"):
    ax.add_patch(FancyArrowPatch(
        (a[0], a[1]), (b[0], b[1]), arrowstyle=style,
        mutation_scale=13, linewidth=lw, color=color,
        connectionstyle="arc3,rad=0.0",
    ))


def right_mid(b):
    return (b[0] + b[2], b[1] + b[3] / 2)


def left_mid(b):
    return (b[0], b[1] + b[3] / 2)


def top_mid(b):
    return (b[0] + b[2] / 2, b[1] + b[3])


def bottom_mid(b):
    return (b[0] + b[2] / 2, b[1])


ax.text(9, 10.16, "End-to-End ECG/HRV Stress Detection and Embedded Telemetry Workflow",
        ha="center", va="center", fontsize=19, weight="bold", color=navy)
ax.text(9, 9.82, "Personalized offline learning connected to real-time edge processing and host-side monitoring",
        ha="center", va="center", fontsize=10.5, color=gray)

# Lane labels
ax.text(0.35, 9.30, "OFFLINE RESEARCH PIPELINE", fontsize=10, weight="bold", color=navy)
ax.plot([0.35, 17.65], [9.17, 9.17], color=navy, linewidth=1.0)
ax.text(0.35, 5.02, "EMBEDDED TELEMETRY AND MONITORING PIPELINE", fontsize=10, weight="bold", color=teal)
ax.plot([0.35, 17.65], [4.89, 4.89], color=teal, linewidth=1.0)

# Offline path
offline = []
offline.append(box(0.45, 7.45, 1.55, 1.05, "WESAD\nLead-II ECG\nrecordings", face=blue, edge=navy, weight="bold"))
offline.append(box(2.20, 7.45, 1.65, 1.05, "Filtering\n0.5–40 Hz\nButterworth", face=blue, edge=navy))
offline.append(box(4.05, 7.45, 1.65, 1.05, "R-peak\ndetection\nPan–Tompkins + MAD", face=blue, edge=navy, size=9.7))
offline.append(box(5.90, 7.45, 1.65, 1.05, "RR intervals\nphysiological\ngating", face=blue, edge=navy))
offline.append(box(7.75, 7.45, 1.75, 1.05, "60 s windows\n0% overlap\n60 s hop", face=cream, edge=gold, weight="bold", size=9.8))
offline.append(box(9.70, 7.45, 1.75, 1.05, "HRV features\n8 core / 13\nexpanded", face=blue, edge=navy, size=9.8))
offline.append(box(11.65, 7.45, 1.85, 1.05, "Subject-specific\nbaseline\nnormalization", face=mint, edge=teal, size=9.7))
offline.append(box(13.70, 7.45, 1.75, 1.05, "Canonical dataset\n445 windows\n15 subjects", face=mint, edge=teal, weight="bold", size=9.7))
offline.append(box(15.65, 7.45, 1.85, 1.05, "15-fold LOSO\n6 ML models\nmetrics", face=cream, edge=gold, weight="bold", size=9.7))
for a, b in zip(offline, offline[1:]):
    arrow(right_mid(a), left_mid(b), color=navy)

# Offline result card
result = box(6.00, 5.45, 6.10, 1.18,
             "PRIMARY BENCHMARK (τ = 0.50)\n92.13% accuracy   |   88.29% F1   |   0.9493 ROC-AUC   |   97.54% specificity",
             face="#EEF7F1", edge=green, size=10.5, weight="bold", color=green)
arrow(bottom_mid(offline[-1]), top_mid(result), color=gold)

# Embedded path
embedded = []
embedded.append(box(0.45, 2.95, 1.85, 1.05, "ECG replay or\nphysiological\nsensor input", face=mint, edge=teal, weight="bold", size=9.8))
embedded.append(box(2.55, 2.95, 2.05, 1.05, "STM32G474RE\nARM Cortex-M4\n170 MHz", face=mint, edge=teal, weight="bold", size=9.7))
embedded.append(box(4.85, 2.95, 1.95, 1.05, "Real-time ECG\nDSP and HRV\ntelemetry", face=mint, edge=teal, size=9.8))
embedded.append(box(7.05, 2.95, 1.85, 1.05, "Packet framing\nCRC-16\nsequence IDs", face=blue, edge=navy, size=9.8))
embedded.append(box(9.15, 2.95, 1.75, 1.05, "UART\nUSB-VCP\nstream", face=blue, edge=navy, size=9.8))
embedded.append(box(11.15, 2.95, 2.05, 1.05, "HC1 stream\nobfuscation*", face=cream, edge=gold, weight="bold", size=10))
embedded.append(box(13.45, 2.95, 1.85, 1.05, "Host receiver\nvalidation and\ndecryption", face=mint, edge=teal, size=9.7))
embedded.append(box(15.55, 2.95, 1.95, 1.05, "Dashboard\nwaveform, HRV,\nstress probability", face=mint, edge=teal, weight="bold", size=9.5))
for a, b in zip(embedded, embedded[1:]):
    arrow(right_mid(a), left_mid(b), color=teal)

# HIL result card and cross-link
hil = box(6.00, 1.15, 6.10, 1.18,
          "PHYSICAL HIL VALIDATION\n10,000 packets   |   0 CRC errors   |   0 sequence gaps   |   350.02 Hz",
          face="#EEF7F1", edge=green, size=10.5, weight="bold", color=green)
arrow(bottom_mid(embedded[4]), top_mid(hil), color=green)

# Disclaimer
ax.text(9, 0.44,
        "* HC1 is an experimental physical-layer stream-obfuscation mechanism; it is not a formally validated cryptographic cipher or a replacement for AES-GCM.",
        ha="center", va="center", fontsize=8.7, color=gray, style="italic")

fig.savefig(OUT / "FIG_ECG_Stress_Detection_Workflow.png", dpi=300, bbox_inches="tight", facecolor="white")
fig.savefig(OUT / "FIG_ECG_Stress_Detection_Workflow.svg", bbox_inches="tight", facecolor="white")
plt.close(fig)
print(OUT / "FIG_ECG_Stress_Detection_Workflow.png")
print(OUT / "FIG_ECG_Stress_Detection_Workflow.svg")
