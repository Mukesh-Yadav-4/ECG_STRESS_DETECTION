"""
run_biquad_dwt_benchmark.py
===========================
Automated hardware runner for STM32G474RE 5-stage Biquad IIR DWT->CYCCNT benchmark.

Steps performed:
1. Flashes embedded_stm32/STM32G474_Biquad_DWT_Benchmark.bin to NUCLEO-G474RE via SWD.
2. Captures DWT benchmark report from USART2 (ST-LINK VCP COM10 @ 115200 baud).
3. Parses min, mean, max cycles and microseconds at 170 MHz.
4. Updates results/raw_evidence_item6_biquad_dwt_cycles.json and .txt with measured values.
5. Safely reflashes production firmware embedded_stm32/STM32G474_HC1_Telemetry.bin.
"""

import os
import sys
import time
import subprocess
import json
import re

PROGRAMMER_PATH = r"C:\ST\STM32CubeIDE_2.2.0\STM32CubeIDE\plugins\com.st.stm32cube.ide.mcu.externaltools.cubeprogrammer.win32_2.2.500.202603051304\tools\bin\STM32_Programmer_CLI.exe"
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BENCH_BIN = os.path.join(PROJECT_ROOT, "embedded_stm32", "STM32G474_Biquad_DWT_Benchmark.bin")
PROD_BIN = os.path.join(PROJECT_ROOT, "embedded_stm32", "STM32G474_HC1_Telemetry.bin")
OUT_JSON = os.path.join(PROJECT_ROOT, "results", "raw_evidence_item6_biquad_dwt_cycles.json")
OUT_TXT = os.path.join(PROJECT_ROOT, "results", "raw_evidence_item6_biquad_dwt_cycles.txt")
PORT = "COM10"
BAUD = 115200


def flash_binary(bin_path):
    print(f"Flashing {os.path.basename(bin_path)} via SWD...")
    cmd = [PROGRAMMER_PATH, "-c", "port=SWD", "-w", bin_path, "0x08000000", "-v", "-rst"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Flashing failed:\n{res.stdout}\n{res.stderr}")
    print("Flashing successful!")


def capture_benchmark_output(port=PORT, baud=BAUD, timeout_sec=10):
    import serial
    print(f"Opening {port} @ {baud} baud to capture DWT benchmark...")
    ser = serial.Serial(port, baud, timeout=1.0)
    start_time = time.time()
    lines = []
    captured_report = False

    while (time.time() - start_time) < timeout_sec:
        raw_line = ser.readline()
        if not raw_line:
            continue
        try:
            line = raw_line.decode("utf-8", errors="replace").strip()
            print(f"  [MCU] {line}")
            lines.append(line)
            if "BIQUAD_DWT_BENCHMARK_DONE" in line:
                captured_report = True
                break
        except Exception:
            pass

    ser.close()
    if not captured_report:
        raise TimeoutError("Timed out waiting for BIQUAD_DWT_BENCHMARK_DONE marker from MCU.")
    return lines


def parse_and_save(lines):
    full_text = "\n".join(lines)
    min_m = re.search(r"Min\s+Cycles:\s+(\d+)\s+\(([\d\.]+)\s+us", full_text)
    mean_m = re.search(r"Mean\s+Cycles:\s+(\d+)\s+\(([\d\.]+)\s+us", full_text)
    max_m = re.search(r"Max\s+Cycles:\s+(\d+)\s+\(([\d\.]+)\s+us", full_text)

    if not (min_m and mean_m and max_m):
        raise ValueError("Could not parse cycles from benchmark output.")

    min_cycles = int(min_m.group(1))
    min_us = float(min_m.group(2))
    mean_cycles = int(mean_m.group(1))
    mean_us = float(mean_m.group(2))
    max_cycles = int(max_m.group(1))
    max_us = float(max_m.group(2))

    print("\nParsed Results:")
    print(f"  Min Cycles:  {min_cycles} ({min_us} us)")
    print(f"  Mean Cycles: {mean_cycles} ({mean_us} us)")
    print(f"  Max Cycles:  {max_cycles} ({max_us} us)")

    # Update JSON
    with open(OUT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["verdict"] = "MEASURED"
    data["reason"] = "Executed hardware DWT CYCCNT benchmark on physical STM32G474RE target."
    data["biquad_cascade_bench"]["min_cycles"] = min_cycles
    data["biquad_cascade_bench"]["mean_cycles"] = mean_cycles
    data["biquad_cascade_bench"]["max_cycles"] = max_cycles
    data["biquad_cascade_bench"]["min_time_us_170mhz"] = min_us
    data["biquad_cascade_bench"]["mean_time_us_170mhz"] = mean_us
    data["biquad_cascade_bench"]["max_time_us_170mhz"] = max_us
    data["raw_mcu_output"] = lines

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    # Update TXT
    txt_content = f"""======================================================================
STM32G474RE 5-STAGE BIQUAD IIR DWT->CYCCNT HARDWARE MEASUREMENT REPORT
======================================================================
Status:                      MEASURED
Target Hardware:             STMicroelectronics NUCLEO-G474RE (ARM Cortex-M4 @ 170 MHz)
Clock Frequency:             170 MHz
Filter Stages:               5 (4 Biquad Butterworth Bandpass 0.5-40Hz + 1 Biquad Notch 50Hz)
Sampling Rate:               350 Hz (2857 us sampling period)
Measurement Method:          DWT->CYCCNT Hardware Cycle Counter (1,000 Trials)

--- Prior Paper Analytical Claim (Section V-A) ---
  Cycles Claimed:            ~318 cycles (ESTIMATED, 5 MACs/biquad, not DWT measured)
  Execution Time Claimed:    1.87 us @ 170 MHz
  CPU Overhead Claimed:      0.065%

--- Hardware DWT Measurement Results (1,000 Trials) ---
  Min Cycles:                {min_cycles} ({min_us:.3f} us @ 170 MHz)
  Mean Cycles:               {mean_cycles} ({mean_us:.3f} us @ 170 MHz)
  Max Cycles:                {max_cycles} ({max_us:.3f} us @ 170 MHz)
  CPU Overhead @ 350 Hz:     {mean_us / 2857.0 * 100:.4f}%
======================================================================
"""
    with open(OUT_TXT, "w", encoding="utf-8") as f:
        f.write(txt_content)

    print("Updated raw evidence files successfully!")


def main():
    try:
        flash_binary(BENCH_BIN)
        time.sleep(1)
        lines = capture_benchmark_output()
        parse_and_save(lines)
    finally:
        print("\nRestoring production firmware...")
        try:
            flash_binary(PROD_BIN)
            print("Production firmware restored successfully.")
        except Exception as e:
            print(f"Warning: Failed to restore production firmware: {e}")


if __name__ == "__main__":
    main()
