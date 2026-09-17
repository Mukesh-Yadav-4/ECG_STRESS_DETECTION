"""
Export compact ECG waveform samples for the interactive Streamlit web demo.
Extracts 60-second baseline and acute stress segments for key benchmark subjects
(S2, S3, S10, S17) so the web app can run anywhere (local or cloud) without
requiring the 16 GB raw dataset.
"""

import os
import json
import numpy as np
import scipy.io as sio
from scipy.signal import butter, filtfilt, find_peaks

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "demo", "sample_data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

TARGET_SUBJECTS = ["S2", "S3", "S10", "S17"]
FS = 700
WINDOW_SEC = 60
WINDOW_SAMPLES = FS * WINDOW_SEC
DOWNSAMPLE_FACTOR = 2  # 700 Hz -> 350 Hz (ideal for fast web rendering)
FS_DEMO = FS // DOWNSAMPLE_FACTOR


def butter_bandpass_filter(data, lowcut=0.5, highcut=40.0, fs=700, order=4):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return filtfilt(b, a, data)


def compute_hrv_metrics(r_peaks, fs):
    if len(r_peaks) < 3:
        return {"MeanHR": 0.0, "SDNN_ms": 0.0, "RMSSD_ms": 0.0, "pNN50": 0.0}
    
    rr_sec = np.diff(r_peaks) / fs
    # Physiological gating (300 ms to 1500 ms)
    valid_mask = (rr_sec >= 0.3) & (rr_sec <= 1.5)
    rr_clean = rr_sec[valid_mask]
    
    if len(rr_clean) < 3:
        rr_clean = rr_sec
        
    mean_hr = 60.0 / np.mean(rr_clean)
    sdnn_ms = np.std(rr_clean, ddof=1) * 1000.0
    rr_diff_ms = np.abs(np.diff(rr_clean)) * 1000.0
    rmssd_ms = np.sqrt(np.mean(rr_diff_ms ** 2))
    pnn50 = float(np.sum(rr_diff_ms > 50.0) / len(rr_diff_ms) * 100.0)
    
    return {
        "MeanHR": round(float(mean_hr), 1),
        "SDNN_ms": round(float(sdnn_ms), 2),
        "RMSSD_ms": round(float(rmssd_ms), 2),
        "pNN50": round(float(pnn50), 1),
        "NumBeats": int(len(r_peaks))
    }


def main():
    print(f"[1/3] Extracting demo ECG waveform samples from {PROCESSED_DIR}...")
    sample_arrays = {}
    metadata = {
        "fs_original": FS,
        "fs_demo": FS_DEMO,
        "window_sec": WINDOW_SEC,
        "subjects": {}
    }

    # Load predictions CSV if available for model output mapping
    pred_csv_path = os.path.join(PROJECT_ROOT, "results", "Stress_Classifier_Predictions.csv")
    pred_data = {}
    if os.path.isfile(pred_csv_path):
        import pandas as pd
        df_pred = pd.read_csv(pred_csv_path)
        for s in TARGET_SUBJECTS:
            sub_df = df_pred[df_pred["Subject"] == s]
            if len(sub_df) > 0:
                pred_data[s] = {
                    "mean_prob_base": float(sub_df[sub_df["TrueLabel"] == 0]["StressProbability"].mean()),
                    "mean_prob_stress": float(sub_df[sub_df["TrueLabel"] == 1]["StressProbability"].mean()),
                }

    for subj in TARGET_SUBJECTS:
        mat_path = os.path.join(PROCESSED_DIR, f"{subj}_ECG_labels.mat")
        if not os.path.isfile(mat_path):
            print(f"  [WARN] File not found: {mat_path}, skipping.")
            continue
            
        print(f"  Processing {subj}...")
        mat = sio.loadmat(mat_path)
        ecg = mat["ecg"].flatten().astype(np.float32)
        labels = mat["labels"].flatten().astype(np.int32)
        
        metadata["subjects"][subj] = {}
        
        for cond_name, label_val in [("Baseline", 1), ("Stress", 2)]:
            cond_indices = np.where(labels == label_val)[0]
            if len(cond_indices) < WINDOW_SAMPLES:
                print(f"    [WARN] Not enough samples for {subj} {cond_name}")
                continue
            
            # Select first stable 60-second window (skip first 30s transition if possible)
            start_idx = cond_indices[0] + (FS * 30 if len(cond_indices) > WINDOW_SAMPLES + FS * 30 else 0)
            end_idx = start_idx + WINDOW_SAMPLES
            
            raw_win = ecg[start_idx:end_idx]
            filt_win = butter_bandpass_filter(raw_win, 0.5, 40.0, fs=FS, order=4)
            
            # Peak detection
            mad = np.median(np.abs(filt_win - np.median(filt_win)))
            prominence = max(0.2, 1.8 * mad)
            r_peaks, _ = find_peaks(filt_win, distance=int(FS * 0.35), prominence=prominence)
            
            hrv = compute_hrv_metrics(r_peaks, FS)
            
            # Downsample for web streaming
            raw_down = raw_win[::DOWNSAMPLE_FACTOR].astype(np.float32)
            filt_down = filt_win[::DOWNSAMPLE_FACTOR].astype(np.float32)
            peaks_down = (r_peaks // DOWNSAMPLE_FACTOR).astype(np.int32)
            
            key_prefix = f"{subj}_{cond_name}"
            sample_arrays[f"{key_prefix}_raw"] = raw_down
            sample_arrays[f"{key_prefix}_filt"] = filt_down
            sample_arrays[f"{key_prefix}_peaks"] = peaks_down
            
            prob = 0.85 if cond_name == "Stress" else 0.12
            if subj in pred_data:
                prob = pred_data[subj]["mean_prob_stress"] if cond_name == "Stress" else pred_data[subj]["mean_prob_base"]
                if np.isnan(prob):
                    prob = 0.85 if cond_name == "Stress" else 0.12

            metadata["subjects"][subj][cond_name] = {
                "hrv": hrv,
                "stress_probability": round(float(prob), 4),
                "predicted_label": 1 if prob >= 0.35 else 0,
                "calibrated_threshold": 0.35
            }

    npz_path = os.path.join(OUTPUT_DIR, "ecg_samples.npz")
    np.savez_compressed(npz_path, **sample_arrays)
    print(f"[2/3] Saved compressed ECG waveforms to {npz_path} ({os.path.getsize(npz_path) / 1024:.1f} KB)")

    json_path = os.path.join(OUTPUT_DIR, "samples_meta.json")
    with open(json_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"[3/3] Saved metadata to {json_path}")
    print("Done! Demo samples ready.")


if __name__ == "__main__":
    main()
