# Reproducible Edge-to-Cloud ECG Stress Detection with Embedded Telemetry and Hardware-in-the-Loop Validation

**Format:** IEEE Conference Format (`\documentclass[conference]{IEEEtran}`)  
**Status:** Unpublished Research Manuscript  
**Target Submission:** IEEE Transactions on Biomedical Engineering / IEEE JBHI / IEEE EMBC  
**Package Archive:** `ieee_ecg_stress_detection.zip` (Directly uploadable to Overleaf)  
**Primary Engine:** pdfLaTeX (TeX Live 2022+ / Overleaf Standard)  

---

## 1. Overview & Manuscript Notice

> **IMPORTANT SCIENTIFIC & STATUS NOTICE:**  
> This manuscript is an **unpublished research manuscript** prepared for peer-reviewed IEEE conference/journal submission. All experimental evaluations are conducted as a **retrospective laboratory benchmark** on the public 15-subject WESAD physiological dataset (*Schmidt et al., 2018*). The embedded HC1 telemetry scheme serves as **lightweight physical-layer telemetry obfuscation**, not as formally certified or standardized cryptography. The web dashboard interfaces represent **research demonstration prototypes**, not certified clinical diagnostic consoles.

Author information:
```latex
\author{\IEEEauthorblockN{Mukesh Yadav}
\IEEEauthorblockA{Department of Electronics and Communication Engineering\\
JSS Academy of Technical Education, Noida (JSSATEN)\\
Noida, Uttar Pradesh, India\\
Email: mkpy06@gmail.com}}
```

---

## 2. Overleaf Compilation Instructions

1. Download or locate the archive: `paper/ieee_ecg_stress_detection/ieee_ecg_stress_detection.zip`.
2. Navigate to [Overleaf](https://www.overleaf.com/).
3. Click **New Project** $\rightarrow$ **Upload Project**.
4. Select `ieee_ecg_stress_detection.zip` and upload.
5. In the Overleaf project settings (left panel menu):
   - **Compiler:** `pdfLaTeX`
   - **TeX Live version:** `2024` (or `2023` / `2022`)
   - **Main document:** `main.tex`
6. Click **Recompile**. The manuscript will compile cleanly to PDF with all tables, figures, equations, and references.

---

## 3. Local Compilation Instructions (TeX Live / MacTeX / MiKTeX)

To compile locally from the command line:

```bash
cd paper/ieee_ecg_stress_detection

# First pass: generate auxiliary files and citation requests
pdflatex main.tex

# Compile bibliography database
bibtex main

# Second pass: resolve cross-references and citation numbers
pdflatex main.tex

# Third pass: resolve final floats and balance column heights
pdflatex main.tex
```

The resulting `main.pdf` will be generated in the same directory.

---

## 4. Package File Inventory

```text
paper/ieee_ecg_stress_detection/
├── main.tex                    # Authoritative IEEEtran LaTeX source code (18 sections)
├── references.bib              # Verified BibTeX database (peer-reviewed literature only)
├── README.md                   # This instruction and compilation guide
├── figure_audit.md             # Pre-manuscript scientific figure audit report
├── generate_figures.py         # 300 DPI high-resolution figure regeneration script
├── ieee_ecg_stress_detection.zip # Overleaf-ready compilation bundle
└── figures/                    # 14 Publication-grade 300 DPI figures
    ├── DEMO_Protocol_Timeline.png                     # Fig. 1: WESAD protocol timeline
    ├── DEMO_Pan_Tompkins_QRS_Detection.png            # Fig. 2: ECG filtering & R-peak pipeline
    ├── FINAL_Confusion_Matrix.png                     # Fig. 3: Primary confusion matrix (tau=0.50)
    ├── FINAL_ROC_Curve.png                            # Fig. 4: 15-fold LOSO ROC curve (AUC=0.9493)
    ├── ML_Model_Benchmark_Bars.png                    # Fig. 5: Multi-model comparative benchmark
    ├── FINAL_Personalized_Feature_Ablation.png        # Fig. 6: M1-M4 ablation (+10.79 pp leap)
    ├── ML_Feature_Importance_Permutation.png          # Fig. 7: Permutation importance & odds ratios
    ├── FINAL_Subject_Stress_Detection.png             # Fig. 8: 15-subject stress recall (S2 callout)
    ├── FIG_Hardware_Testbed_Composite.png             # Fig. 9: STM32G474RE laboratory testbed setup
    ├── FIG_Physical_HIL_10k_Validation.png            # Fig. 10: 10,000-packet HIL validation
    ├── FINAL_Confusion_Matrix_Exploratory_tau035.png  # Fig. S1: MATLAB vs Python at tau=0.35
    ├── FIG_M4D_Attractor_3D.png                       # Fig. S2: 4D hyperchaotic attractor 3D plot
    ├── FIG_Dashboard_SinglePage_M4D_Decrypted.png     # Fig. S3: Authorized terminal prototype UI
    └── FIG_Dashboard_M4D_Eavesdropper.png             # Fig. S4: Wiretap adversary prototype UI
```

---

## 5. Authoritative Experimental & Hardware Benchmarks

### 5.1 Machine-Learning Benchmark (15-Fold LOSO, 445 Windows)
- **Primary Operating Threshold ($\tau = 0.50$):**
  - **Accuracy:** $92.13\%$ ($410 / 445$ windows)
  - **F1-Score:** $88.29\%$
  - **Sensitivity (Recall):** $82.50\%$ ($132 / 160$ acute stress windows)
  - **Specificity:** $97.54\%$ ($278 / 285$ calm windows, only $7$ false alarms)
  - **Precision:** $94.96\%$
  - **ROC-AUC:** $0.9493$
  - **PR-AUC:** $0.9467$
- **Exploratory Screening Threshold ($\tau = 0.35$):**
  - **Accuracy:** $92.36\%$ ($411 / 445$ windows)
  - **Sensitivity:** $86.25\%$ (MATLAB) / $86.88\%$ (Python)
  - **Specificity:** $95.79\%$ (MATLAB) / $95.44\%$ (Python)
  - **F1-Score:** $89.03\%$ (MATLAB) / $89.10\%$ (Python)
- **Personalized Normalization Leap ($\Delta x$):**
  - Uncalibrated 13 features (M3): $81.57\%$ accuracy, $73.03\%$ F1-score
  - Personalized 13 features (M4): $92.36\%$ accuracy, $88.67\%$ F1-score ($+10.79\text{ pp}$ accuracy gain)

### 5.2 Physical STM32 Hardware-in-the-Loop Telemetry
- **Microcontroller:** STM32G474RE Nucleo-64 (ARM Cortex-M4 @ 170\,MHz SYSCLK)
- **Firmware Flash Footprint:** $11,316\text{ bytes}$
- **Biquad IIR Filter Latency:** $1.87\,\mu\text{s}$ per sample ($\approx 318$ CPU cycles, $0.065\%$ of $2.857\text{ ms}$ budget)
- **Physical UART Capture:** Exactly $10,000$ consecutive 20-byte packets ($200,000\text{ wire bytes}$) at $350.02\text{ Hz}$
- **Sequence Continuity:** Monotonic from $11,428$ to $21,427$ ($0$ drops, $0$ gaps, $0$ CRC-16 errors)
- **Reconstruction Accuracy:** $0.0\text{ mV}$ raw and filtered signal error ($\text{MSE} = 0.000\text{ mV}^2$) after sequence-aligned comparison with the canonical firmware replay reference
- **QRS Peak Preservation:** $39 / 39$ peaks preserved ($100\%$ detection fidelity)
- **Wire Statistical Checks:** Shannon entropy $H = 7.9977\text{ b/B}$ ($99.97\%$ max), $\chi^2 = 257.79$ ($p = 0.4394$)
- **Artifact Integrity:** The principal software, firmware, result, and physical-capture artifacts are integrity-pinned using SHA-256 hashes.
