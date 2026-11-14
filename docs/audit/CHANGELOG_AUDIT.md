# CHANGELOG_AUDIT: Comprehensive Verification & Value Reconciliation

This document records every numerical value, metric, parameter, and claim that was audited and updated during the repository and manuscript audit on branch `fix/audit`. Every new value is derived strictly from executed code runs, physical silicon measurements, or verified repository evidence files.

---

## 1. Primary Classification Accuracy & Evaluation Protocol

| Metric / Parameter | Old Draft Value | New Verified Value | Source Evidence File | Status / Reason |
| :--- | :--- | :--- | :--- | :--- |
| **Primary Evaluation Protocol** | 15-Fold LOSO-CV across 445 windows with all-baseline anchor leakage | **Leak-Free 15-Fold LOSO-CV** on **295 non-anchor windows** ($N=10$ anchor excluded from scoring) | `python/calibration_length_experiment.py`, `results/calibration_length/calibration_length_primary_model.csv` | **Corrected.** Prior protocol anchored each subject on all 285 baseline windows and scored those same windows, creating data leakage. |
| **Primary Accuracy (LR, $\tau=0.50$)** | 92.13% | **90.17% [95% CI: 82.7%, 95.9%]** | `results/calibration_length/calibration_length_primary_model.csv`, `results/calibration_length/paired_contrasts_bootstrap.csv` | **Updated.** 266 / 295 windows correct on the common evaluation set ($N=10$ selected post hoc as the best of the five lengths tested). |
| **Primary F1-Score (LR, $\tau=0.50$)** | 88.29% | **90.49% [95% CI: 81.9%, 96.2%]** | `results/calibration_length/calibration_length_primary_model.csv` | **Updated.** Harmonic mean of precision and recall on leak-free set. |
| **Balanced Accuracy (LR, $\tau=0.50$)** | 90.02% | **90.53% [95% CI: 83.5%, 96.0%]** | `results/calibration_length/calibration_length_primary_model.csv` | **Updated.** Unbiased mean of sensitivity (86.25%) and specificity (94.81%). |
| **Sensitivity (Recall) ($\tau=0.50$)** | 82.50% (132 / 160) | **86.25% (138 / 160)** | `results/calibration_length/calibration_length_primary_model.csv` | **Updated.** Detected stress windows. |
| **Specificity ($\tau=0.50$)** | 97.54% (278 / 285) | **94.81% (128 / 135)** | `results/calibration_length/calibration_length_primary_model.csv` | **Updated.** Calm resting windows correct (7 false alarms). |
| **Majority-Class Baseline** | 64.04% (285 / 445) | **54.24% (160 / 295)** | Evaluation set distribution | **Corrected.** Baseline accuracy on evaluation windows. |
| **Legacy Benchmark Status** | Presented as headline | **Clearly labelled as "Legacy all-baseline anchor (leaky) reference" (92.13%)** | `results/calibration_length/leak_free_ablation_results.csv` | **Reclassified.** Retained strictly for historical reference. |

---

## 2. Personal Calibration Gain & Duration Analysis

*Evidence file:* [`results/calibration_length/paired_contrasts_bootstrap.csv`](../../results/calibration_length/paired_contrasts_bootstrap.csv) (10,000 subject-level cluster bootstrap resamples, seed 0). Values match `PHASE2_VERIFY.md` section 1.3 exactly.

| Contrast / Metric | Point $\Delta$ Accuracy | 95% Bootstrap CI ($\Delta\text{Acc}$) | Statistically Significant? | Point $\Delta$ Balanced Acc | 95% Bootstrap CI ($\Delta\text{Bal Acc}$) | Statistically Significant? |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **$N=1$ minus Control (a)** | $+5.42\text{ pp}$ | $[-2.70, +13.40]\text{ pp}$ | **No** (CI spans 0) | $+5.06\text{ pp}$ | $[-2.81, +12.71]\text{ pp}$ | **No** (CI spans 0) |
| **$N=2$ minus Control (a)** | $+4.75\text{ pp}$ | $[-3.06, +12.72]\text{ pp}$ | **No** (CI spans 0) | $+4.49\text{ pp}$ | $[-3.09, +12.13]\text{ pp}$ | **No** (CI spans 0) |
| **$N=3$ minus Control (a)** | $+3.73\text{ pp}$ | $[-4.05, +11.56]\text{ pp}$ | **No** (CI spans 0) | $+3.44\text{ pp}$ | $[-3.95, +10.72]\text{ pp}$ | **No** (CI spans 0) |
| **$N=5$ minus Control (a)** | $+6.78\text{ pp}$ | $[+0.68, +13.22]\text{ pp}$ | **Yes** (excludes 0) | $+6.60\text{ pp}$ | $[+0.67, +12.98]\text{ pp}$ | **Yes** (excludes 0) |
| **$N=10$ minus Control (a)**| $+11.53\text{ pp}$ | $[+5.07, +18.06]\text{ pp}$ | **Yes** (excludes 0) | $+11.03\text{ pp}$ | $[+4.81, +17.47]\text{ pp}$ | **Yes** (excludes 0) |
| **$N=10$ minus $N=5$** | $+4.75\text{ pp}$ | $[+0.68, +9.52]\text{ pp}$ | **Yes** (excludes 0) | $+4.43\text{ pp}$ | $[+0.74, +8.87]\text{ pp}$ | **Yes** (excludes 0) |
| **$N=10$ minus Control (b) [Leaky]**| $+0.34\text{ pp}$ | $[-3.36, +4.79]\text{ pp}$ | **No detectable difference** | $+0.02\text{ pp}$ | $[-3.76, +4.39]\text{ pp}$ | **No detectable difference** |

### Origin of the +10.79 pp Value
The +10.79 percentage-point value originated from $92.36 - 81.57$ (13-feature calibrated vs raw, all-baseline anchor, documented in `results/Feature_Group_Comparison.csv` and `results/FINAL_Development_Model_Comparison.csv`: $92.35955\% - 81.57303\% = +10.78652\% \approx +10.79\%$). In the leak-free protocol, it is replaced by the pre-specified 8-feature paired contrast between $N=10$ calibrated (90.17%) and uncalibrated Control (a) (78.64%) on the 295-window set, which yields $+11.53\text{ pp}$ [95% CI: $+5.07, +18.06$].

---

## 3. Embedded Hardware Execution & Biquad Filter Timing

| Parameter / Metric | Old Draft Value | New Verified Value | Source Evidence File | Status / Reason |
| :--- | :--- | :--- | :--- | :--- |
| **Claim C-05: Filter Execution Cycles** | 318 cycles (theoretical analytical estimate) | **251 cycles (mean)** [min: 249, max: 281] | `results/raw_evidence_item6_biquad_dwt_cycles.json`, `results/raw_evidence_item6_biquad_dwt_cycles.txt` | **Contradicted & Replaced.** Measured directly on physical silicon (STM32G474RE) across 1,000 trials via internal ARM Cortex-M Data Watchpoint and Trace (`DWT->CYCCNT`) register. Real hardware is 21.1% faster than analytical estimate. |
| **Claim C-06: Filter Execution Latency** | 1.87 µs per sample @ 170 MHz | **1.476 µs per sample** [min: 1.464 µs, max: 1.652 µs] | `results/raw_evidence_item6_biquad_dwt_cycles.json` | **Contradicted & Replaced.** Exact silicon latency at 170 MHz SYSCLK. |
| **CPU Utilization Load @ 350 Hz** | 0.065% | **0.0517%** | Calculated: $(251 \times 350) / 170 \times 10^6$ | **Updated.** Leaves >99.94% processor headroom. |
| **Compiler Optimization Flags** | Not documented | `arm-none-eabi-gcc -mcpu=cortex-m4 -mfpu=fpv4-sp-d16 -mfloat-abi=hard -mthumb -O2 -ffp-contract=off` | `embedded_stm32/Makefile`, `PHASE2_VERIFY.md` (Item 5) | **Documented.** Identical build flags and source filter (`ecg_dsp_filter.c`) verified between benchmark and production firmware. |

---

## 4. Hyperchaotic Engine Parameters & Lyapunov Spectrum

| Parameter / Metric | Old Draft Value | New Verified Value | Source Evidence File | Status / Reason |
| :--- | :--- | :--- | :--- | :--- |
| **Chaotic Parameter Vector $(a,b,c,d,r)$** | $a=35, b=3, c=28, d=-1, r=5$ (Old Lorenz-type set) | **$a=15.81, b=2.76, c=86.03, d=-9.07, r=10.79$** (HC1 M-4DCHS) | `embedded_stm32/src/telemetry_protocol.c` (lines 53-57), `python/m4d_hyperchaos.py` (lines 20-25) | **Replaced.** Audited all code and confirmed that embedded firmware and Python suite execute the HC1 parameter set. Legacy $a=35$ set removed from all papers and docs. |
| **Largest Lyapunov Exponent $\lambda_1$** | $+0.0006$ (Weakly chaotic) | **$+0.4182 \text{ to } +0.5282$** (Mean: **$+0.4432$**) | `results/m4d_lyapunov_benchmark.txt` | **Replaced.** Audited across all 10 independent integration runs ($dt$, duration, initial conditions). |
| **Second Lyapunov Exponent $\lambda_2$** | Not reported | **$+0.2361 \text{ to } +0.2995$** (Mean: **$+0.2710$**) | `results/m4d_lyapunov_benchmark.txt` | **Added.** Confirms hyperchaos ($\lambda_1 > 0, \lambda_2 > 0$). |
| **Phase Space Divergence $\nabla \cdot \mathbf{F}$** | Not reported | **$-27.640000$** | Derived analytically: $\nabla \cdot \mathbf{F} = \frac{\partial \dot{x}}{\partial x} + \frac{\partial \dot{y}}{\partial y} + \frac{\partial \dot{z}}{\partial z} + \frac{\partial \dot{w}}{\partial w} = -a - b + d = -15.81 - 2.76 + (-9.07) = -27.640000$. | `results/m4d_lyapunov_benchmark.txt` | **Verified.** Continuous dissipative volume contraction. |
| **Kaplan-Yorke Dimension $D_{KY}$** | Not reported | **$3.0233 \text{ to } 3.0290$** (Mean: **$3.0251$**) | `results/m4d_lyapunov_benchmark.txt` | **Added.** Validated fractional attractor dimension. |

---

## 5. Physical Hardware-in-the-Loop (HIL) Telemetry & Byte Scope

| Parameter / Metric | Old Draft Value | New Verified Value | Source Evidence File | Status / Reason |
| :--- | :--- | :--- | :--- | :--- |
| **HIL Packet Count & Wire Bytes** | 10,000 pkts / 200,000 wire bytes | **10,000 consecutive pkts / 200,000 wire bytes** | `results/verification/hc1_hardware_hil/hardware_raw_packets_meta.json` | **Confirmed.** Monotonic sequence IDs 11,428 to 21,427 with 0 lost frames and 0 CRC errors. |
| **HIL Replay Source Signal** | Ambiguous live ADC / sensor | **WESAD Subject S2 Baseline in Flash** (`WESAD_S2_RAW_ECG`, 2,100 samples) | `embedded_stm32/src/main_stm32.c` (lines 115-125), `PHASE2_VERIFY.md` (Item 6) | **Clarified.** Corrected modulo alignment (`seq_id % 2100`) resolved initial 0.926 mV phase shift, proving bit-exact 0.0 mV reconstruction error. |
| **Shannon Entropy Scope** | $H = 7.9973$ bits/byte (scope unspecified) | **Scrambled Payload Only (Bytes 10..17, 80 kB): $H = 7.9977$ bits/byte**<br>Full Frame (Bytes 0..19, 200 kB): $H = 7.0705$ bits/byte | `python/verify_hardware_hc1_capture.py` (line 277: `pkt_bytes[10:18]`), `results/verification/hc1_hardware_hil/corrected_physical_hil/corrected_item5_chi2_uniformity.txt` | **Clarified.** Full-frame entropy is lower due to static framing headers (`0xAA55, 0x01, 0x05`). Scrambled payload passes uniform byte distribution. |
| **Chi-Square Uniformity ($\chi^2$) Scope** | $\chi^2 = 257.79, p = 0.4394$ (scope unspecified) | **Scrambled Payload Only (Bytes 10..17, 80 kB): $\chi^2 = 257.79, p = 0.4394$** ($df=255$)<br>Full Frame (Bytes 0..19, 200 kB): $\chi^2 = 999331.89, p = 0.0000$ | `results/verification/hc1_hardware_hil/corrected_physical_hil/corrected_item5_chi2_uniformity.txt` | **Clarified.** Rejection on full frame is expected due to static sync headers; non-rejection on payload confirms diffusion quality. |

---

## 6. Threshold Reconciliation ($\tau = 0.35$ vs $\tau = 0.50$)

| Dataset / Pipeline | Prior Documented Value | Verified True Value | Source Evidence File | Status / Reason |
| :--- | :--- | :--- | :--- | :--- |
| **Threshold Metric Mix-Up Attribution** | "89.66% Acc / 90.00% Sens / 89.47% Spec" | Accidental table lookup of $\tau=0.18$ / $0.19$ | Introduced in `PHASE1_REPORT.md` (lines 148-152), from `results/Threshold_Analysis.csv` (rows 18-19). Paper drafts and source prediction CSVs were correct. | **Attributed.** Row lookup error in `PHASE1_REPORT.md`. |
| **Legacy 445-Window MATLAB ($\tau=0.35$)** | Cited in README / papers | **92.36% Acc / 86.25% Sens / 95.79% Spec** | `results/Personalized_Classifier_Predictions.csv` | **Verified.** 411 / 445 correct windows. |
| **Legacy 445-Window Python ($\tau=0.35$)** | Cited in README / papers | **92.36% Acc / 86.88% Sens / 95.44% Spec** | `results/ML_Predictions_LOSO.csv` | **Verified.** 411 / 445 correct windows (1 TP/FP shift due to coordinate descent solver). |
| **Leak-Free 295-Window ($\tau=0.50$, Primary)** | Not available | **90.17% Acc / 86.25% Sens / 94.81% Spec** | `results/calibration_length/calibration_length_primary_model.csv` | **Authoritative.** 266 / 295 correct windows. |
| **Leak-Free 295-Window ($\tau=0.35$, Screening)**| Not available | **87.80% Acc / 88.75% Sens / 86.67% Spec** | `results/calibration_length/calibration_length_window_predictions.csv` | **Authoritative.** 259 / 295 correct windows. |

---

## 7. Banned Terminology & Tone De-Escalation

| Concept / Phrase | Prior Wording | Replacement Wording | Reason |
| :--- | :--- | :--- | :--- |
| **HC1 Security Claim** | "secure", "privacy-preserving", "AES replacement", "cryptographic privacy" | **"lightweight stream obfuscation without key management or session authentication"** | HC1 lacks formal CPA/CCA proofs and key exchange; it is wire obfuscation. |
| **Diagnostic Claims** | "validating clinical diagnostic efficacy" | **"evaluating stress classification performance"** | Single-lead research benchmark in laboratory TSST setting is not a certified diagnostic device. |
| **Superlatives** | "outperforms", "exceptional generalizability", "state-of-the-art leap" | **"achieves", "evaluates", "demonstrates"** | Scientific objectivity and rigorous empirical tone. |
| **Validation Terminology** | "validated" (used ubiquitously) | **"evaluated" / "measured" / "benchmarked"** | Reserved "validated" strictly for formal physiological gating checks. |

---

## 8. Bibliography & Comparison Audit

| Reference | Prior BibTeX Record | Updated Verified Record | Status |
| :--- | :--- | :--- | :--- |
| **Plarre et al.** | SenSys 2011, pp. 400–408 | Proceedings of the 10th ACM/IEEE International Conference on Information Processing in Sensor Networks (IPSN 2011), Chicago, IL, USA, pp. 97–108. DOI: `10.5555/1989732.1989745` | **Corrected.** Verified against ACM/IEEE Digital Library. |
| **Bobade & Vani (2020)** | PACM IMWUT 2020 / ICACCI | Proceedings of the 2nd International Conference on Inventive Research in Computing Applications (ICIRCA 2020), Coimbatore, India, pp. 511–517, IEEE. DOI: `10.1109/ICIRCA48905.2020.9182908` | **Corrected.** Venue verified as ICIRCA 2020. Quoted in Table IV/VI strictly with its paper numbers: Multimodal (Chest+Wrist), Random Split (ANN), 84.32% 3-Class / 95.21% Binary. |
| **Lin et al. (2023)** | BSPC vol. 84, p. 104751 | Cited article does not exist as described (BSPC vol. 84, p. 104751 belongs to an unrelated paper). | **REMOVED.** Completely removed from Table IV/VI, manuscripts, and README. |
| **Schmidt et al. (2018)** | ICMI 2018 | Proceedings of the 20th ACM ICMI 2018, pp. 400–408. | **Verified.** Retained as foundational WESAD reference (Multimodal Chest, LOSO-CV, 80.34% 3-Class). |
