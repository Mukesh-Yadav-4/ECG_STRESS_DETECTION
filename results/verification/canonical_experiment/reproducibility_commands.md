# Reproducibility Guide & Execution Commands

**Project:** WESAD ECG Stress Detection with Chaotic Telemetry  
**Scope:** Canonical End-to-End Pipeline Reproduction  
**Operating Systems:** Windows 11 Enterprise (PowerShell 5.1 / PowerShell 7+), Linux (Bash compatible)  
**Location:** `results/verification/canonical_experiment/`  

---

## 1. Prerequisites & Environment Setup

### 1.1 Python Environment
Verify that Python 3.10+ (tested on Python 3.14.3 AMD64) is installed with core scientific dependencies:

```powershell
# Set Python module search path
$env:PYTHONPATH = "python"

# Verify installed packages
python -c "import numpy, pandas, scipy, sklearn, streamlit; print('All core libraries verified!')"
```

Required packages:
- `numpy >= 1.24.0` (validated on `2.4.3`)
- `pandas >= 2.0.0` (validated on `3.0.1`)
- `scipy >= 1.10.0` (validated on `1.17.1`)
- `scikit-learn >= 1.3.0` (validated on `1.8.0`)
- `streamlit >= 1.30.0` (validated on `1.64.0`)
- `plotly >= 5.15.0`

### 1.2 MATLAB Environment
- Tested on **MATLAB R2026a Update 4 (Version 26.1.0.3312084)**.
- Required Toolboxes: Signal Processing Toolbox, Statistics and Machine Learning Toolbox.

### 1.3 Embedded Cross-Compiler Toolchain
- **Toolchain:** GNU Tools for STM32 14.3.1 (`arm-none-eabi-gcc.exe`)
- Default Installation Path:
  `C:\ST\STM32CubeIDE_2.2.0\STM32CubeIDE\plugins\com.st.stm32cube.ide.mcu.externaltools.gnu-tools-for-stm32.14.3.rel1.win32_1.0.100.202602081740\tools\bin`

---

## 2. Stage-by-Stage Reproduction Commands

### Stage 1: MATLAB Feature Extraction & Signal Conditioning

To verify signal conditioning parameters, zero-phase Butterworth filtering, and R-peak detection non-destructively:

```powershell
# Execute MATLAB non-destructive preprocessing verification
matlab -batch "addpath('src'); run('src/run_preprocessing.m'); exit;"
```

*Expected Output:* Generates/verifies `results/WESAD_HRV_features_expanded.csv` containing 445 rows $\times$ 16 columns across the 15 subjects (`S2–S11, S13–S17`).

---

### Stage 2: Python 15-Fold LOSO Machine Learning Benchmark

Executes strict 15-fold Leave-One-Subject-Out cross-validation across all 6 classifiers with subject baseline calibration:

```powershell
# Run the canonical multi-model LOSO benchmark
$env:PYTHONPATH = "python"
python python/train_loso_ml_benchmark.py
```

*Expected Primary Outputs:*
- `results/ML_Model_Benchmark_LOSO.csv`: Leaderboard table reporting metrics at primary threshold $\tau = 0.50$ (Logistic Regression: 92.13% Acc, 88.29% F1, 82.50% Sens, 97.54% Spec, 0.9493 ROC-AUC, 0.9467 PR-AUC).
- `results/ML_Predictions_LOSO.csv`: Complete 2,670 out-of-fold window predictions (445 windows $\times$ 6 models).

---

### Stage 3: Host Python/C HC1 Stream Parity Verification

Compiles the embedded telemetry protocol with strict SSE2/floating-point compiler flags (`-O2 -msse2 -mfpmath=sse -ffp-contract=off`) to enforce strict IEEE-754 64-bit alignment, testing 10,000 packets ($200,000$ bytes):

```powershell
# Run strict host C vs Python parity verifier
$env:PYTHONPATH = "python"
python python/verify_m4d_parity.py
```

*Expected Result:*
- 10,000 packets tested ($120,000$ encrypted payload bytes).
- Total byte mismatches: **0 bytes** (0.00000%).
- Maximum absolute voltage error: **0.0 mV**.

---

### Stage 4: STM32 Firmware Clean Rebuild (Non-Destructive)

Rebuilds the target bare-metal ARM Cortex-M4 binary directly from sources without modifying hardware or flashing:

```powershell
$toolchain = "C:\ST\STM32CubeIDE_2.2.0\STM32CubeIDE\plugins\com.st.stm32cube.ide.mcu.externaltools.gnu-tools-for-stm32.14.3.rel1.win32_1.0.100.202602081740\tools\bin"
$cc = Join-Path $toolchain "arm-none-eabi-gcc.exe"
$objcopy = Join-Path $toolchain "arm-none-eabi-objcopy.exe"
$size = Join-Path $toolchain "arm-none-eabi-size.exe"

$cflags = @(
    "-mcpu=cortex-m4", "-mfpu=fpv4-sp-d16", "-mfloat-abi=hard", "-mthumb",
    "-O2", "-ffp-contract=off", "-Wall", "-fdata-sections", "-ffunction-sections",
    "-Iembedded_stm32/include"
)
$ldflags = @(
    "-mcpu=cortex-m4", "-mfpu=fpv4-sp-d16", "-mfloat-abi=hard", "-mthumb",
    "-Tembedded_stm32/STM32G474RETX_FLASH.ld", "-Wl,--gc-sections",
    "-specs=nano.specs", "-specs=nosys.specs", "-lc", "-lm", "-lnosys"
)
$srcs = @(
    "embedded_stm32/src/main_stm32.c",
    "embedded_stm32/src/ecg_dsp_filter.c",
    "embedded_stm32/src/telemetry_protocol.c",
    "embedded_stm32/src/wesad_test_samples.c",
    "embedded_stm32/src/syscalls.c",
    "embedded_stm32/src/sysmem.c",
    "embedded_stm32/src/startup_stm32g474retx.s"
)

$out_elf = "results/verification/canonical_experiment/STM32G474_HC1_rebuild.elf"
$out_bin = "results/verification/canonical_experiment/STM32G474_HC1_rebuild.bin"

# Compile and extract binary
& $cc @cflags @srcs @ldflags -o $out_elf
& $objcopy -O binary $out_elf $out_bin
& $size $out_elf

# Verify SHA-256 hash match
$hash = (Get-FileHash -Algorithm SHA256 $out_bin).Hash.ToLower()
Write-Output "Rebuilt Binary SHA-256: $hash"
# Target: ed4b97b3e7279dc0f6d2add3a21b1ddf45347dbc9e8bfa21f1f48ac86657edc1
```

---

### Stage 5: Offline Physical HIL Telemetry Verification

Verifies the preserved physical 10,000-packet capture (`hardware_raw_packets.bin`) against the canonical sequence-aligned firmware replay reference:

```powershell
$env:PYTHONPATH = "python"
python python/verify_hardware_hc1_capture.py `
    --raw results/verification/hc1_hardware_hil/hardware_raw_packets.bin `
    --meta results/verification/hc1_hardware_hil/hardware_raw_packets_meta.json `
    --reference results/verification/hc1_hardware_hil/firmware_replay_reference.npz
```

*Expected Verification Results:*
- Captured Packets: 10,000 packets ($200,000\text{ bytes}$).
- Sequence Continuity: Monotonic range 11,428 to 21,427 with 0 gaps.
- Sampling Rate: $350.02\text{ Hz}$ (Passes $[345, 355]\text{ Hz}$ window).
- Active Wire Flags: All 10,000 packets set to `0x05`.
- CRC-16 Errors: **0 errors**.
- Signal Parity: Max absolute error raw = $0.0\text{ mV}$, filt = $0.0\text{ mV}$ (100% bit-exact).

---

### Stage 6: Interactive Dashboard Launch

Launches the clinical monitoring and benchmark demonstration dashboard:

```powershell
$env:PYTHONPATH = "python"
streamlit run demo/app.py
```

*Access Point:* Opens in default browser at `http://localhost:8501`.
- **Default Mode:** Simulated STM32 Link (streams real WESAD subjects through the exact 20-byte packet protocol offline without requiring physical hardware).
- **Physical Mode:** Requires user selection of "Physical USB COM Port" and specified COM port.
