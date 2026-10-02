# GitHub Final Staging & Pre-Release Publication Plan

**Project:** ECG Stress Detection & Embedded Telemetry (WESAD & STM32G474RE)  
**Author:** Mukesh Yadav (`mkpy06@gmail.com`)  
**Target Branch:** `main`  
**Tracking Remote:** `origin https://github.com/Mukesh-Yadav-4/ECG_STRESS_DETECTION.git`  
**Audit Status:** Final Public Release Review  
**Policy:** Read-Only Audit (Zero commits, zero pushes, zero deletions, zero file modifications)

---

## 1. Review of Deleted Working-Tree Files

The following three tracked files are currently deleted in the working tree:
1. `HARDWARE_COMPONENTS_LIST.html`
2. `HARDWARE_COMPONENTS_LIST.pdf`
3. `ROADMAP.html`

### Finding & Assessment: **Generated Duplicates**
* **`ROADMAP.html`:** A generated HTML export of `ROADMAP.md`. The authoritative markdown source [`ROADMAP.md`](../ROADMAP.md) is present, tracked, and current in the repository root.
* **`HARDWARE_COMPONENTS_LIST.html` & `.pdf`:** Generated HTML and PDF exports describing the bill of materials (NUCLEO-G474RE, AD8232 ECG sensor, jumper pinouts). All hardware setup, wiring, pin configurations, and BOM details are fully documented in Markdown in:
  - [`README.md`](../README.md) (Section 8: Bare-Metal Edge Implementation)
  - [`PROJECT_IMPLEMENTATION_SYSTEMATIC_GUIDE.md`](../PROJECT_IMPLEMENTATION_SYSTEMATIC_GUIDE.md) (Hardware Architecture & Pinout)
  - [`PROJECT_QUICK_REFERENCE.md`](../PROJECT_QUICK_REFERENCE.md)
  - [`results/verification/canonical_experiment/reproducibility_commands.md`](../results/verification/canonical_experiment/reproducibility_commands.md)
* **Final Recommendation:** **Formally remove from Git tracking (`git rm`)**. This maintains a clean, Markdown-first repository structure free of redundant generated binary/HTML formats.

---

## 2. Root `README.md` Completeness Review

A line-by-line review of the root [`README.md`](../README.md) confirms all 9 required sections are complete and accurate:

| Required Section | Status | Location in `README.md` | Details Confirmed |
| :--- | :---: | :--- | :--- |
| **1. Project Overview** | Complete | Lines 1–20, 71–83 | WESAD 15-subject benchmark, personalized baseline calibration ($\Delta x$), edge IoMT goals. |
| **2. Architecture** | Complete | Lines 131–171, 274–326 | 3-stage signal processing, 5-stage Biquad IIR DSP, 4D hyperchaotic flow (M-4DCHS). |
| **3. Verified Results** | Complete | Lines 172–241 | 15-fold LOSO primary scorecard: 92.13% Acc, 88.29% F1, 97.54% Spec, 0.9493 ROC-AUC. |
| **4. Reproducibility Instructions**| Complete | Lines 428–436 | CLI command lines for live telemetry receiver, virtual streaming, and cross-reference to guides. |
| **5. Paper Link** | Complete | Line 14 | Research paper badge linking to preprint PDF download. |
| **6. Hardware/HIL Results** | Complete | Lines 343–370 | Telemetry frame structure, 350.02 Hz throughput, zero CRC errors, zero packet drops. |
| **7. HC1 Security Limitation** | Complete | Lines 375–377 | Explicit scientific disclaimer stating HC1 is physical-layer obfuscation, not a certified cryptographic cipher. |
| **8. Dataset Licensing** | Complete | Lines 438–441 | UCI Machine Learning Repository link, ~16 GB raw data exclusion rule, ethical attribution. |
| **9. Author Information** | Complete | Lines 17, 444–452 | Mukesh Yadav, JSSATEN, Zenodo citation, and research portfolio link. |

---

## 3. Deep Privacy, Path, and Metadata Inspection

A comprehensive scan was conducted across all proposed candidate staging files for local workstation paths, usernames, COM ports, ST-Link serial numbers, and credentials:

### A. Credentials & Encryption Secrets
* **API Keys, Passwords, Tokens, Private Keys:** **Zero detected.**
* **Real Encryption Secrets:** The HC1 algorithm is a deterministic physical-layer obfuscation scheme with publicly published parameters in the paper; no private cryptokeys exist.

### B. Local Machine Paths (`C:\Users\YASH...` and `C:\ST...`)
Local machine paths are strictly absent from all source code (`python/`, `matlab/`, `embedded_stm32/`) and the LaTeX paper package (`paper/ieee_ecg_stress_detection/`). They are confined exclusively to diagnostic logs and reproducibility reports:
1. **Toolchain Installation Paths (`C:\ST\...`, `C:\MinGW\...`):**
   - `results/verification/canonical_experiment/reproducibility_commands.md`: Example Windows toolchain paths (`C:\ST\STM32CubeIDE_2.2.0\...`).
   - `results/verification/hc1_strict_parity/build_command.txt`: Host compiler log (`C:\MinGW\bin\gcc.EXE`).
   - `results/verification/pre_paper_validation/pre_paper_validation_report.md`: Provenance table listing local compiler versions.
2. **Local Machine Working Directory (`C:\Users\YASH\Desktop\...`):**
   - `results/verification/hc1_hardware_hil/hardware_raw_packets_meta.json`: Capture metadata field `"raw_binary_path"`.
   - `results/verification/hc1_hardware_hil/dry_run_packets_meta.json`: Capture metadata field `"raw_binary_path"`.
   - Markdown internal file links (`file:///C:/Users/YASH/...`): Found in internal working logs (`physical_hil_failure_root_cause.md`, `canonical_model_decision.md`, `PROJECT_VERIFICATION_REPORT.md`).

### C. Hardware Interface & Port Specifics
* **COM Port (`COM10`):** Appears in hardware scripts, `README.md`, `main.tex`, and HIL reports. Specifying the target virtual COM port (`COM10` @ 115,200 baud) is standard documentation practice for reproducible embedded telemetry testbeds.
* **ST-Link Serial Number (`066BFF535351717867174628`):** Appears only in `results/verification/hc1_hardware_hil/hardware_flash_log.txt`. This is non-sensitive diagnostic hardware metadata confirming physical board programming.

---

## 4. Per-Artifact Publication Classification

| Artifact Path | Classification | Recommendation & Rationale |
| :--- | :---: | :--- |
| **`paper/ieee_ecg_stress_detection/`** | **Commit Unchanged** | Publication manuscript, BibTeX, 14 PNG figures, and scripts are 100% clean of local user paths and secrets. |
| **`results/verification/canonical_experiment/`** | **Commit Unchanged** | Authoritative canonical benchmarks, manifest, schema, and consistency report. Vital for peer review. |
| **`results/verification/pre_paper_validation/`** | **Commit Unchanged** | Multi-stage CSV/JSON benchmarks proving 0.0000 metric delta against canonical baseline. |
| **`results/verification/hc1_strict_parity/`** | **Commit Unchanged** | Host C single-precision parity build log and test reports (PASS). |
| **`results/verification/hc1_hardware_hil/`** (logs & markdown) | **Commit Unchanged** | Physical HIL telemetry evidence, failure root-cause analysis, and corrected 10,000-packet verification. |
| **`python/verify_hardware_hc1_capture.py`** | **Commit Unchanged** | Modular verification script with sequence alignment and wire statistical disclaimers. |
| **`.gitignore`** | **Commit Unchanged** | Preserves all rules while neutralizing `tmp/`, `.env`, and Python caches. |
| **`docs/GITHUB_*.md`** | **Commit Unchanged** | Clean pre-push and secret audit reports. |
| **`HARDWARE_COMPONENTS_LIST.*`, `ROADMAP.html`** | **Exclude (Remove via `git rm`)** | Generated duplicates superseded by Markdown sources. |
| **`tmp/` (24 PNG images, ~11.8 MB)** | **Exclude (`.gitignore`)** | Scratch Overleaf PDF preview renders. Retained locally only. |
| **`*.bin`, `*.elf`, `*.map`, `*.zip`** | **Exclude (`.gitignore`)** | Raw binaries and firmware objects excluded automatically by repository policy. |

> [!NOTE]
> **Provenance Transparency in Research Artifacts:**  
> Retaining execution paths (`C:\MinGW`, `C:\ST...`) in `results/verification/` is standard and beneficial in scientific reproducibility artifacts because it establishes the exact compiler environment, architecture, and toolchain versions used to generate the verified results.

---

## 5. Final Recommended Public-Release File List

When staged, the commit will include exactly **44 files (~6.58 MB)** across six functional categories:

```text
├── .gitignore
├── docs/
│   ├── GITHUB_FINAL_STAGING_PLAN.md
│   ├── GITHUB_PRE_PUSH_AUDIT.md
│   └── GITHUB_SECRET_SCAN.md
├── paper/ieee_ecg_stress_detection/
│   ├── README.md
│   ├── figure_audit.md
│   ├── generate_figures.py
│   ├── main.tex
│   ├── references.bib
│   └── figures/ (14 publication figures: confusion matrices, ROC, ablation, HIL, testbed)
├── python/
│   └── verify_hardware_hc1_capture.py
└── results/verification/
    ├── canonical_experiment/
    │   ├── canonical_metrics.json
    │   ├── consistency_check_report.md
    │   ├── experiment_manifest.json
    │   ├── experiment_manifest.md
    │   ├── feature_schema.json
    │   └── reproducibility_commands.md
    ├── hc1_hardware_hil/
    │   ├── hardware_flash_log.txt
    │   ├── hardware_raw_packets_meta.json
    │   ├── hil_parity_report.json
    │   ├── hil_parity_report.txt
    │   ├── physical_hil_failure_root_cause.md
    │   └── corrected_physical_hil/
    │       ├── corrected_hil_parity_report.json
    │       ├── corrected_hil_parity_report.txt
    │       └── corrected_physical_hil_verification.md
    ├── hc1_strict_parity/
    │   ├── build_command.txt
    │   ├── parity_report.json
    │   └── parity_report.txt
    └── pre_paper_validation/
        ├── ML_Model_Benchmark_LOSO.csv
        ├── ML_Predictions_LOSO.csv
        ├── metric_comparison.csv
        ├── pre_paper_validation_report.md
        ├── pre_paper_validation_summary.json
        ├── stage1_dataset_validation.json
        ├── stage2_matlab_output.txt
        ├── stage5_firmware_build.json
        └── stage6_dashboard_smoke_test.json
```

---

## 6. Exact Staging & Release Commands

Execute the following commands when you are ready to stage, commit, and push:

```bash
# -------------------------------------------------------------
# 1. Cleanly remove the 3 deleted generated duplicate files
# -------------------------------------------------------------
git rm HARDWARE_COMPONENTS_LIST.html HARDWARE_COMPONENTS_LIST.pdf ROADMAP.html

# -------------------------------------------------------------
# 2. Stage updated repository ignore configuration
# -------------------------------------------------------------
git add .gitignore

# -------------------------------------------------------------
# 3. Stage the complete IEEE research paper package
# -------------------------------------------------------------
git add paper/ieee_ecg_stress_detection/

# -------------------------------------------------------------
# 4. Stage authoritative verification and reproducibility suites
# -------------------------------------------------------------
git add results/verification/canonical_experiment/
git add results/verification/pre_paper_validation/
git add results/verification/hc1_strict_parity/
git add results/verification/hc1_hardware_hil/hardware_flash_log.txt
git add results/verification/hc1_hardware_hil/hardware_raw_packets_meta.json
git add results/verification/hc1_hardware_hil/hil_parity_report.json
git add results/verification/hc1_hardware_hil/hil_parity_report.txt
git add results/verification/hc1_hardware_hil/physical_hil_failure_root_cause.md
git add results/verification/hc1_hardware_hil/corrected_physical_hil/

# -------------------------------------------------------------
# 5. Stage Python verification tool enhancements
# -------------------------------------------------------------
git add python/verify_hardware_hc1_capture.py

# -------------------------------------------------------------
# 6. Stage release documentation and audit reports
# -------------------------------------------------------------
git add docs/GITHUB_SECRET_SCAN.md
git add docs/GITHUB_PRE_PUSH_AUDIT.md
git add docs/GITHUB_FINAL_STAGING_PLAN.md

# -------------------------------------------------------------
# 7. Review staged index (Confirm ~44 staged files, 0 in tmp/)
# -------------------------------------------------------------
git status

# -------------------------------------------------------------
# 8. Commit
# -------------------------------------------------------------
git commit -m "docs(paper): add IEEE conference manuscript package, reproducibility framework, and physical HIL verification"

# -------------------------------------------------------------
# 9. Push to GitHub
# -------------------------------------------------------------
git push origin main
```
