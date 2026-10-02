# Pre-Push Git Working Tree Audit

**Audit Date:** October 2, 2026  
**Repository Branch:** `main`  
**Tracking Status:** Ahead of `origin/main` by 2 commits  
**Remote Target:** `origin https://github.com/Mukesh-Yadav-4/ECG_STRESS_DETECTION.git`  
**Audit Policy:** Read-Only inspection (No files committed, pushed, deleted, restored, or staged)

---

## Executive Summary

A comprehensive pre-push audit was conducted across the Git repository state, working tree modifications, untracked artifacts, cryptographic safety, and dataset boundaries.

| Category | Status | Count / Scope | Recommendation |
| :--- | :---: | :--- | :--- |
| **1. Intended Project Improvements** | Ready | 4 files (`python/`, `results/`) | Review & commit with clear message |
| **2. New Paper & Documentation Artifacts** | Ready | 18 files (`paper/ieee_ecg_stress_detection/`, `docs/`) | Commit to formalize IEEE manuscript |
| **3. Generated Verification Outputs** | Ready | 26 files (`results/verification/`) | Review & commit for audit trail |
| **4. Temporary Files** | Action Required | 24 files in `tmp/` (~11.8 MB) | Add `tmp/` to `.gitignore` |
| **5. Deleted Files (HTML/PDF)** | Decision Required | 3 tracked files deleted | Restore or formally `git rm` |
| **6. Sensitive Files & Dataset Protection** | Verified Safe | 0 secrets; WESAD protected | Safe to publish after `tmp/` ignore |

---

## 1. Remote and Branch Synchronisation

- **Git Remote (`git remote -v`):**
  - `origin https://github.com/Mukesh-Yadav-4/ECG_STRESS_DETECTION.git (fetch)`
  - `origin https://github.com/Mukesh-Yadav-4/ECG_STRESS_DETECTION.git (push)`
- **Branch Relationship:**
  - Local branch `main` is **ahead of `origin/main` by 2 commits**:
    1. `c2e2964 documentation consistency corrections`
    2. `9999392 verify(hc1): implement strict host parity and physical HIL verification framework`

---

## 2. Working Tree Modifications (`git diff --stat`)

```text
 HARDWARE_COMPONENTS_LIST.html                      | 223 --------------
 HARDWARE_COMPONENTS_LIST.pdf                       | Bin 112565 -> 0 bytes
 ROADMAP.html                                       | 338 ---------------------
 python/verify_hardware_hc1_capture.py              | 163 ++++++++--
 .../hc1_strict_parity/build_command.txt            |   2 +-
 .../hc1_strict_parity/parity_report.json           |   2 +-
 .../hc1_strict_parity/parity_report.txt            |   2 +-
 7 files changed, 136 insertions(+), 594 deletions(-)
```

---

## 3. Comprehensive File Classification

### Category 1: Intended Project Improvements to Commit
*Files modified to enhance verification capabilities and report precision:*

| File | Status | Description & Rationale |
| :--- | :---: | :--- |
| `python/verify_hardware_hc1_capture.py` | Modified | Added `--align-by-sequence` flag, `--report-prefix`, modular `subsystem_verdicts` breakdown, sequence range tracking (`11,428` to `21,427`), and scientific wire statistical disclaimers for entropy/chi-square. |
| `results/verification/hc1_strict_parity/build_command.txt` | Modified | Updated build timestamp for the strict single-precision GCC host C parity harness. |
| `results/verification/hc1_strict_parity/parity_report.json` | Modified | Updated verification execution timestamp confirming bit-exact C-to-Python parity (PASS). |
| `results/verification/hc1_strict_parity/parity_report.txt` | Modified | Human-readable counterpart to JSON parity report with updated execution timestamp (PASS). |

---

### Category 2: New Paper and Documentation Artifacts to Commit
*Complete unpublished IEEE conference paper package and pre-push audit records:*

| Path | Type | Details |
| :--- | :---: | :--- |
| `paper/ieee_ecg_stress_detection/main.tex` | LaTeX Source | 10-page IEEEtran manuscript. Contains author details (Mukesh Yadav, JSSATEN), split Table III-A and Table III-B, 4-column Table IV, wrapped Table V footnote, and verified formulas. |
| `paper/ieee_ecg_stress_detection/references.bib` | BibTeX | Complete bibliography with 30 authoritative citations. |
| `paper/ieee_ecg_stress_detection/README.md` | Markdown | Compilation instructions, Overleaf workflow, and reproducibility guide. |
| `paper/ieee_ecg_stress_detection/generate_figures.py` | Python Script | Deterministic script generating all paper figures from canonical results. |
| `paper/ieee_ecg_stress_detection/figure_audit.md` | Markdown | Comprehensive audit verifying every figure against canonical metrics. |
| `paper/ieee_ecg_stress_detection/figures/*.png` | PNG (14 files) | Publication-quality figures (300 DPI) for primary ($\tau = 0.50$) and exploratory ($\tau = 0.35$) benchmarks, Pan-Tompkins pipeline, protocol timeline, hyperchaotic attractor, testbed composite, and HIL validation. |
| `docs/GITHUB_SECRET_SCAN.md` | Markdown | Bounded secret scan report confirming zero hardcoded credentials. |
| `docs/GITHUB_PRE_PUSH_AUDIT.md` | Markdown | Authoritative pre-push working tree audit report (this document). |

*(Note: `paper/ieee_ecg_stress_detection/ieee_ecg_stress_detection.zip` is automatically excluded by `.gitignore` via `*.zip` rule).*

---

### Category 3: Generated Verification Output to Review
*Reproducibility artifacts and hardware testbed validation records produced during pre-paper checks:*

#### A. Canonical Experiment Framework (`results/verification/canonical_experiment/`)
- `experiment_manifest.json` & `experiment_manifest.md`: Complete SHA-256 integrity-pinned experiment manifest.
- `canonical_metrics.json`: Authoritative benchmark metrics for all six ML classifiers at $\tau = 0.50$.
- `feature_schema.json`: Formal schema defining the 25 input HRV features, baseline calibration, and order.
- `reproducibility_commands.md`: Exact CLI commands to reproduce all stages from scratch.
- `consistency_check_report.md`: Verification report proving zero-tolerance consistency across all files.

#### B. Pre-Paper Multi-Stage Validation (`results/verification/pre_paper_validation/`)
- `metric_comparison.csv`: Direct delta comparison between current runs and canonical metrics.
- `ML_Model_Benchmark_LOSO.csv`: Reproducibility rerun of the 15-fold LOSO multi-model leaderboard.
- `ML_Predictions_LOSO.csv`: All 445 out-of-fold window predictions across 15 subjects.
- `pre_paper_validation_report.md` & `pre_paper_validation_summary.json`: Multi-stage verification summary.
- `stage1_dataset_validation.json`: Static dataset validation (15 subjects, 445 windows, 285 calm, 160 stress, 0 NaNs).
- `stage2_matlab_output.txt`: MATLAB pipeline consistency verification log.
- `stage5_firmware_build.json`: STM32 bare-metal build log (`11,316` bytes Flash, `1,436` bytes RAM).
- `stage6_dashboard_smoke_test.json`: Telemetry dashboard smoke test validation log.

#### C. Hardware-in-the-Loop Verification (`results/verification/hc1_hardware_hil/`)
- `hardware_flash_log.txt`: ST-Link physical flashing verification log.
- `hardware_raw_packets_meta.json`: Capture metadata for 10,000 physical UART packets.
- `hil_parity_report.json` & `hil_parity_report.txt`: Baseline HIL parity assessment.
- `physical_hil_failure_root_cause.md`: Scientific root-cause analysis documenting circular buffer wrap-around.
- `corrected_physical_hil/`:
  - `corrected_hil_parity_report.json` & `corrected_hil_parity_report.txt`: Corrected sequence-aligned verification report ($0.0\,\text{mV}$ error).
  - `corrected_physical_hil_verification.md`: Comprehensive physical HIL verification report.

---

### Category 4: Temporary Files That Must Be Ignored

| Path | Size | Reason & Action Required |
| :--- | :---: | :--- |
| `tmp/pdf4_review/` (11 PNGs) | ~4.7 MB | Rendered page previews of compiled Overleaf PDF #4 used for visual LaTeX layout auditing. |
| `tmp/pdf_review/` (10 PNGs) | ~4.5 MB | Rendered page previews of compiled Overleaf PDF #1. |
| `tmp/pdf_review_hi/` (3 PNGs) | ~2.6 MB | High-resolution cropped inspection images of pages 4, 8, and 10. |

> [!WARNING]
> **Action Required Before Staging:**
> The directory `tmp/` is **not currently in `.gitignore`**. If `git add .` or `git add -A` is executed, 24 PNG files totalling **~11.8 MB** will be staged into Git history.
> **Fix:** Add `tmp/` to `.gitignore`.

---

### Category 5: Possible Accidental Deletion

| File | Historical Size | Nature of File | Assessment |
| :--- | :---: | :--- | :--- |
| `HARDWARE_COMPONENTS_LIST.html` | 223 lines | HTML render of component bill of materials | Generated file |
| `HARDWARE_COMPONENTS_LIST.pdf` | 112,565 bytes | PDF render of component bill of materials | Generated binary |
| `ROADMAP.html` | 338 lines | HTML render of project roadmap | Generated file |

* **Context:** The authoritative source files `ROADMAP.md` and `docs/PROJECT_CONSISTENCY_AUDIT.md` remain intact, tracked, and up to date in Markdown.
* **Assessment:** These deletions were likely an intentional cleanup of derived HTML/PDF artifacts to keep the repository Markdown-first, but Git still tracks them as deleted.
* **Decision needed prior to commit:**
  - *Option A (Cleanup):* Run `git rm HARDWARE_COMPONENTS_LIST.html HARDWARE_COMPONENTS_LIST.pdf ROADMAP.html` to finalize their removal from Git tracking.
  - *Option B (Restore):* Run `git checkout HEAD -- HARDWARE_COMPONENTS_LIST.html HARDWARE_COMPONENTS_LIST.pdf ROADMAP.html` if compiled HTML/PDF artifacts must remain in the repository.

---

### Category 6: Sensitive Files & Dataset Protection Review

#### A. Secret Key & Credential Audit
- A bounded security scan (`docs/GITHUB_SECRET_SCAN.md`) was executed across all **120 Git-tracked text files** in the repository.
- **Results:**
  - GitHub Personal Access Tokens (`ghp_`, `github_pat_`): **0 detected**
  - AWS Access Keys (`AKIA...`): **0 detected**
  - Google Cloud API Keys (`AIza...`): **0 detected**
  - Private Keys (`BEGIN RSA/OPENSSH PRIVATE KEY`): **0 detected**
  - Hardcoded Passwords & Plaintext Credentials: **0 detected**

#### B. WESAD Raw Dataset Protection
- The `.gitignore` file strictly excludes:
  ```gitignore
  data/
  data/**
  **/WESAD/**
  *.pkl
  *.pkl.gz
  ```
- **Verification:** Zero raw participant Pickle files (`S2.pkl`, etc.) or raw sensory files are tracked or present in the working tree. Only aggregated, anonymized HRV features are preserved in `results/WESAD_HRV_features_expanded.csv`.

#### C. Raw Hardware Captures & Binaries
- The binary files `hardware_raw_packets.bin` (200 KB) and `dry_run_packets.bin` (200 KB) are automatically ignored by Git due to the `*.bin` rule in `.gitignore`.
- Firmware binaries (`STM32G474_HC1_rebuild.bin`, `*.elf`, `*.map`) are also cleanly ignored.
- `hardware_flash_log.txt`: Contains local ST-Link serial number (`066BFF535351717867174628`) and ST-Link CLI output. This is a non-sensitive diagnostic log confirming physical flashing, safe to commit as audit evidence.

---

## 4. Pre-Push Action Checklist

Prior to staging and pushing to GitHub, perform the following steps:

1. [ ] **Update `.gitignore` to ignore temporary review images:**
   ```gitignore
   tmp/
   ```
2. [ ] **Resolve deleted HTML/PDF files:**
   - If keeping markdown-only: `git rm HARDWARE_COMPONENTS_LIST.html HARDWARE_COMPONENTS_LIST.pdf ROADMAP.html`
   - If restoring: `git checkout HEAD -- HARDWARE_COMPONENTS_LIST.html HARDWARE_COMPONENTS_LIST.pdf ROADMAP.html`
3. [ ] **Stage paper artifacts and verification evidence:**
   ```bash
   git add paper/ieee_ecg_stress_detection/
   git add results/verification/
   git add python/verify_hardware_hc1_capture.py
   git add docs/GITHUB_SECRET_SCAN.md
   git add docs/GITHUB_PRE_PUSH_AUDIT.md
   ```
4. [ ] **Commit with clear descriptive message:**
   ```bash
   git commit -m "docs(paper): add IEEE conference manuscript package and pre-paper verification suite"
   ```
5. [ ] **Push to GitHub:**
   ```bash
   git push origin main
   ```
