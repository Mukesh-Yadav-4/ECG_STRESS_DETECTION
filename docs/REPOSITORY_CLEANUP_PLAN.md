# Repository Cleanup Review & Storage Optimization Plan

**Target Repository:** `C:\Users\YASH\Desktop\projects\RESEARCH PROJECTS\ECG_STRESS_DETECTION`  
**Date:** 2026-10-03  
**Mode:** Read-Only Audit (No files deleted, moved, modified, or staged)  

---

## 1. Executive Summary & Canonical Baselines

This document provides a comprehensive, read-only audit of candidate files and directories across the repository to identify redundant artifacts, historical failure logs, intermediate documents, and duplicate figure assets.

### Established Canonical References (Must Not Be Disrupted)
* **Latest Paper Compilation:** `paper/Personalized_ECG_HRV_Stress_Detection_LOSO_STM32_4D_Hyperchaotic_Telemetry_v3.pdf` (5.72 MB, 16-page IEEE format)
* **Active IEEE Manuscript Source:** `paper/ieee_ecg_stress_detection/` (including `main.tex`, `references.bib`, and `generate_figures.py`)
* **Canonical Publication Figures:** `paper/ieee_ecg_stress_detection/figures/` (300 DPI, referenced by both `main.tex` and `README.md`)
* **General Public Figures:** `results/figures/` (top-level exports)
* **Final Hardware-in-the-Loop (HIL) Evidence:** `results/verification/hc1_hardware_hil/corrected_physical_hil/` (10,000-packet zero-loss run with active HC1 M-4DCHS)
* **Canonical Experiment Ground Truth:** `results/verification/canonical_experiment/` (`canonical_metrics.json`, `experiment_manifest.json`, etc.)

---

## 2. Category-by-Category Audit Matrix

### Category 1: Old / Generated Documents

| Candidate Path | Size | Active File References | Unique Evidence? | Breakage Risk if Removed | Recommendation | Est. Space Saved |
|---|:---:|---|:---:|---|:---:|:---:|
| **`paper/Personalized_ECG_Stress_Detection_WESAD_Benchmark_and_STM32_Edge_IoMT_v2.pdf`** | 4.98 MB (5,218,040 B) | **None** (0 references across entire repo) | **No** (Superseded v2 build prior to 4D hyperchaotic & 10k HIL updates) | **None.** No active build script or markdown links to v2. | **REMOVE / ARCHIVE** | **4.98 MB** |
| **`EXECUTION_GUIDE.pdf`** | 247.4 KB (253,354 B) | `docs/generate_pdf.py:428` (output target only) | **No** (Compiled binary output of `EXECUTION_GUIDE.md`) | **None.** Source markdown `EXECUTION_GUIDE.md` is preserved and can recompile anytime. | **REMOVE / .GITIGNORE** | **0.24 MB** |
| **`ROADMAP.pdf`** | 155.8 KB (159,595 B) | **None** (0 references across entire repo) | **No** (Compiled binary output of `ROADMAP.md`) | **None.** Source markdown `ROADMAP.md` is preserved. | **REMOVE / .GITIGNORE** | **0.15 MB** |
| **`docs/EXECUTION_GUIDE.html`** | 15.3 KB (15,671 B) | `docs/generate_pdf.py:427` (intermediate output target only) | **No** (Intermediate HTML artifact generated during PDF build) | **None.** Ephemeral generation artifact. | **REMOVE / .GITIGNORE** | **0.01 MB** |
| **`ECG_STRESS_DETECTION_RUN.txt`** | 3.67 KB (3,755 B) | `docs/PROJECT_CONSISTENCY_AUDIT.md:188` (cited as audit finding regarding formatting) | **No** (Legacy quick-run cheat sheet with local hardcoded machine paths) | **None.** Content is fully documented and maintained in `README.md` and `EXECUTION_GUIDE.md`. | **ARCHIVE / REMOVE** | **< 0.01 MB** |
| **`HOW_TO_RESTORE_ECG_PROJECT.txt`** | 1.78 KB (1,826 B) | `docs/PROJECT_CONSISTENCY_AUDIT.md:234, 235` | **No** (Developer troubleshooting instructions for flashing board & COM10 locks) | **None.** No pipeline dependency. Helpful developer hardware utility note. | **KEEP or MOVE to `docs/`** | Negligible |

---

### Category 2: Historical or Superseded Evidence

| Candidate Path | Size | Active File References | Unique Evidence? | Breakage Risk if Removed | Recommendation | Est. Space Saved |
|---|:---:|---|:---:|---|:---:|:---:|
| **`results/raw_evidence_item3_hil_capture.json` & `.txt`** | 1.88 KB (1,922 B) | `docs/PROJECT_CONSISTENCY_AUDIT.md:182, 197`<br>`results/verification/PROJECT_VERIFICATION_REPORT.md:120` | **Historical only.** Documents legacy 15,505-packet run without active HC1 (`flags = 0x01`). Superseded by canonical 10k HIL run. | **Low.** Removing breaks historical traceability cited in internal audit reports. | **ARCHIVE** (Move to `results/verification/archive/`) | Negligible |
| **`results/raw_evidence_item4_parity_check.json` & `.txt`** | 1.67 KB (1,709 B) | `docs/PROJECT_CONSISTENCY_AUDIT.md:196, 248`<br>`results/verification/PROJECT_VERIFICATION_REPORT.md:118`<br>`results/verification/hc1_parity_infrastructure_review.md:142`<br>`results/verification/pre_paper_validation/pre_paper_validation_report.md:36, 114`<br>`results/verification/hc1_hardware_hil/final_hil_preflight.md:65` | **Yes (Negative Control / Provenance).** Documents the initial x87 80-bit FPU vs MSVC float32 divergence (9,377 mismatches) that motivated compiler remediation. | **Moderate.** Cited by 6 internal verification reports as proof that the bug was isolated and resolved. | **KEEP (or Archive)** as historical negative control | Negligible |
| **`results/raw_evidence_item5_chi2_uniformity.json` & `.txt`** | 1.65 KB (1,687 B) | `docs/PROJECT_CONSISTENCY_AUDIT.md:183, 243` | **Yes (Primary Measurement).** Contains raw statistical data: $\chi^2 = 302.03$ ($p = 0.0230, \text{df}=255$) and $H = 7.9973$ bits/byte across 80,000 keystream bytes. Matches manuscript text. | **High.** This is the empirical raw evidence backing the wire statistical claim in Section VI of the paper. | **KEEP (Primary Evidence)** | Negligible |
| **`results/verification/hc1_hardware_hil/dry_run_report/`** (`hil_parity_report.json` & `.txt`) | 4.84 KB (4,961 B) | **None** (0 references across entire repo) | **No.** Simulation dry-run generated before the physical STM32 was connected on COM10. | **None.** Completely superseded by `corrected_physical_hil/`. | **ARCHIVE / REMOVE** | Negligible |
| **`results/verification/hc1_hardware_hil/hil_verification_plan.md`** | 9.76 KB (9,997 B) | `capture_script_review.md:66`<br>`reference_consistency_review.md:29, 49` | **No.** Engineering execution plan for the 5-step hardware HIL protocol. | **Low.** Referenced only by adjacent internal review documents. | **KEEP** (Useful protocol record) | Negligible |
| **`results/verification/hc1_hardware_hil/capture_script_review.md`** | 7.63 KB (7,818 B) | `reference_consistency_review.md:30, 49` | **No.** Static audit of `capture_hardware_telemetry.py`. | **Low.** Referenced only by adjacent internal review documents. | **KEEP** (Engineering documentation) | Negligible |
| **`results/verification/hc1_hardware_hil/final_hil_preflight.md`** | 5.77 KB (5,904 B) | None | **Yes (Provenance).** Preflight checklist verifying firmware SHA-256 (`ed4b...`), COM10 status, and ST-Link PID before flashing. | **Low.** Self-contained preflight report. | **KEEP** (Hardware safety audit record) | Negligible |

---

### Category 3: Possible Duplicate Verification Outputs

| Candidate Path | Size | Active File References | Unique Evidence? | Breakage Risk if Removed | Recommendation | Est. Space Saved |
|---|:---:|---|:---:|---|:---:|:---:|
| **`results/verification/ml_rerun/`** (2 files: `ML_Model_Benchmark_LOSO.csv`, `ML_Predictions_LOSO.csv`) | 123.3 KB (126,292 B) | `PROJECT_VERIFICATION_REPORT.md:30`<br>`stage2_ml_reproducibility.txt:7`<br>`stage2_threshold_discrepancy.md:22, 47, 51, 61` | **No.** 100% bit-for-bit duplicate of root `results/` and `pre_paper_validation/` CSVs ($\max \|\Delta\| = 0.0000000000$). | **Low.** `stage2_threshold_discrepancy.md` cites this path to prove bit-exact reproducibility. | **KEEP or ARCHIVE** (Minimal footprint: 123 KB) | **0.12 MB** |
| **`results/verification/pre_paper_validation/`** (11 files) | 195.4 KB (200,079 B) | **CRITICAL.** Referenced in:<br>`README.md:411`<br>`docs/GITHUB_FINAL_STAGING_PLAN.md:61, 79, 136, 174`<br>`docs/GITHUB_PRE_PUSH_AUDIT.md:95, 99` | **Yes (Core Audit).** Contains `pre_paper_validation_report.md`, toolchain compiler version table, rebuilt binary hashes, smoke test JSON, and 84-row metric delta table. | **CRITICAL BREAKAGE.** Deleting would break public links and directory structures documented in `README.md`. | **MUST KEEP (DO NOT DELETE)** | — |

---

### Category 4: Possible Duplicate Figure Directories

| Candidate Path | Size | Active File References | Unique Evidence? | Breakage Risk if Removed | Recommendation | Est. Space Saved |
|---|:---:|---|:---:|---|:---:|:---:|
| **`results/figures/matlab/`** (10 files) | 2.17 MB (2,276,419 B) | **None** (0 references across entire repo) | **No.** These are legacy 16-09-2026 exports that are either duplicated in `results/figures/` (top-level) or superseded by updated 02-10-2026 figures. | **None.** No scripts, READMEs, or LaTeX files point to `results/figures/matlab/`. | **REMOVE / ARCHIVE** | **2.17 MB** |
| **`results/figures/python/`** (5 files) | 1.51 MB (1,578,337 B) | Mentioned only in text notes in `EXECUTION_GUIDE.md:235` and `docs/create_docx.py:198`. | **No.** All 5 PNG files are exact byte-for-byte duplicates of the top-level files in `results/figures/`. | **None.** No active code or LaTeX documents load from this path. | **REMOVE / ARCHIVE** | **1.51 MB** |
| **`paper/figures/`** (32 files) | 28.35 MB (29,727,942 B) | `paper/ieee_ecg_stress_detection/generate_figures.py:348, 350` (`src_fig_dir = "paper/figures"`, copies 7 static figures) | **YES (Irreplaceable Raw Physical Camera Photographs).** Contains 5 original high-resolution physical testbed camera photos (~19.35 MB) and 7 static figures: <br>• `FIG_Physical_Testbed_Setup.png` (4.29 MB)<br>• `FIG_STM32_Board_Closeup.png` (4.31 MB)<br>• `Live_ECG_signal_via_stm32_laptop.jpg` (3.52 MB)<br>• `Live_Encrypted_ECG_signal_via_stm32_laptop.jpg` (3.43 MB)<br>• `STM32G474RE.jpg` (3.80 MB) | **CRITICAL SCRIPT BREAKAGE.** `generate_figures.py` copies static figures from this folder. Deleting raw camera photos causes permanent loss of primary experimental hardware photos. | **PARTIAL ARCHIVE:**<br>1. Keep the 7 static source figures required by `generate_figures.py`.<br>2. Move the 5 large raw camera photos (19.35 MB) to a dedicated `archive/raw_hardware_photos/`. | **Up to 19.35 MB** (if raw photos archived) |
| **`paper/ieee_ecg_stress_detection/figures/`** (14 files) | 6.19 MB (6,491,104 B) | **CRITICAL.** Referenced in:<br>• `paper/ieee_ecg_stress_detection/main.tex` (all 10 `\includegraphics` commands)<br>• `README.md` (10 embedded image tags)<br>• `paper/ieee_ecg_stress_detection/figure_audit.md` | **Yes (Canonical Manuscript Figures).** Final 300 DPI publication-grade figures verified in `figure_audit.md`. | **CATASTROPHIC BREAKAGE.** LaTeX compilation and README display will fail immediately. | **CANONICAL PRODUCTION — MUST KEEP UNTOUCHED** | — |

---

## 3. Storage Savings Breakdown

| Action Tier | Scope | Target Files / Directories | Space Reclaimed |
|---|---|---|:---:|
| **Tier 1: Safe Immediate Cleanup** | Redundant compiled outputs & legacy drafts | • `paper/..._v2.pdf`<br>• `EXECUTION_GUIDE.pdf`<br>• `ROADMAP.pdf`<br>• `docs/EXECUTION_GUIDE.html`<br>• `results/figures/matlab/`<br>• `results/figures/python/` | **~9.06 MB** |
| **Tier 2: Hardware Photos Archiving** | Move original camera photos to external archive or `archive/` | • 5 raw camera photos in `paper/figures/` (keeping the 7 static vector/composite assets for `generate_figures.py`) | **~19.35 MB** |
| **Tier 3: Audit Documentation Consolidation** | Historical single-run txt/json artifacts | • `ECG_STRESS_DETECTION_RUN.txt`<br>• `results/verification/hc1_hardware_hil/dry_run_report/`<br>• `results/raw_evidence_item3_hil_capture.*` | **~0.02 MB** |
| **Total Potential Reclaimable Storage** | | | **~28.43 MB** |

---

## 4. Recommended Action Plan (When Authorized)

When the user chooses to proceed with cleanup in a future step, the recommended execution sequence is:

1. **Step 1 (Remove Obsolete Paper Drafts):**
   * Delete `paper/Personalized_ECG_Stress_Detection_WESAD_Benchmark_and_STM32_Edge_IoMT_v2.pdf` (keeping the canonical `..._v3.pdf`).
2. **Step 2 (Clean Build Artifacts):**
   * Delete `EXECUTION_GUIDE.pdf`, `ROADMAP.pdf`, and `docs/EXECUTION_GUIDE.html`. Add `*.pdf` (root level) and `docs/*.html` to `.gitignore` so they are treated as build products.
3. **Step 3 (Eliminate Duplicate Figure Directories):**
   * Delete `results/figures/matlab/` and `results/figures/python/`. The top-level `results/figures/` directory already houses all canonical public figures.
4. **Step 4 (Preserve Hardware Assets in `paper/figures/`):**
   * Keep `paper/figures/` containing the 7 static figures needed by `paper/ieee_ecg_stress_detection/generate_figures.py`.
   * Move the 5 high-resolution raw camera photographs (`FIG_Physical_Testbed_Setup.png`, `FIG_STM32_Board_Closeup.png`, etc.) to `archive/hardware_photos/` rather than deleting them permanently.
5. **Step 5 (Preserve Canonical Audit Trails):**
   * **Do NOT delete** `results/verification/pre_paper_validation/` (breaks `README.md`).
   * **Do NOT delete** `results/raw_evidence_item5_chi2_uniformity.*` (contains paper's primary raw statistical test measurement).
   * **Do NOT delete** `paper/ieee_ecg_stress_detection/figures/` (breaks active IEEE LaTeX compilation and README display).
