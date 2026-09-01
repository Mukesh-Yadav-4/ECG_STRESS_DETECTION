import os
import pickle
import numpy as np
from scipy.io import savemat

# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

BASE_DIR = r"C:\Users\YASH\Desktop\projects\RESEARCH PROJECTS\WESAD\WESAD"
OUTPUT_DIR = os.path.join(BASE_DIR, "MATLAB_DATA")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# WESAD subjects
subjects = [
    "S2", "S3", "S4", "S5",
    "S6", "S7", "S8", "S9",
    "S10", "S11",
    "S13", "S14", "S15",
    "S16", "S17"
]

FS = 700

# ---------------------------------------------------------
# Process subjects one at a time
# ---------------------------------------------------------

for subject in subjects:

    print("\n" + "=" * 60)
    print(f"Processing {subject}")
    print("=" * 60)

    pkl_path = os.path.join(
        BASE_DIR,
        subject,
        f"{subject}.pkl"
    )

    output_path = os.path.join(
        OUTPUT_DIR,
        f"{subject}_ECG_labels.mat"
    )

    if not os.path.exists(pkl_path):
        print(f"ERROR: File not found: {pkl_path}")
        continue

    try:

        # ---------------------------------------------
        # Load WESAD subject
        # ---------------------------------------------

        print("Loading pickle...")

        with open(pkl_path, "rb") as f:
            data = pickle.load(f, encoding="latin1")

        # ---------------------------------------------
        # Extract ECG and labels
        # ---------------------------------------------

        ecg = np.asarray(
            data["signal"]["chest"]["ECG"]
        ).flatten()

        labels = np.asarray(
            data["label"]
        ).flatten()

        # ---------------------------------------------
        # Basic validation
        # ---------------------------------------------

        print(f"ECG samples:   {len(ecg):,}")
        print(f"Label samples: {len(labels):,}")

        if len(ecg) != len(labels):
            print("WARNING: ECG and labels have different lengths!")
            del data, ecg, labels
            continue

        # ---------------------------------------------
        # Reduce storage size
        # ---------------------------------------------

        ecg = ecg.astype(np.float32)
        labels = labels.astype(np.uint8)

        # ---------------------------------------------
        # Save MATLAB file
        # ---------------------------------------------

        print("Saving MATLAB file...")

        savemat(
            output_path,
            {
                "ecg": ecg,
                "labels": labels,
                "Fs": np.array([[FS]], dtype=np.float64)
            },
            do_compression=True
        )

        print(f"Saved: {output_path}")

        # ---------------------------------------------
        # Free memory before next subject
        # ---------------------------------------------

        del data
        del ecg
        del labels

        print(f"{subject} completed successfully.")

    except Exception as e:

        print(f"ERROR while processing {subject}:")
        print(e)

print("\n" + "=" * 60)
print("ALL SUBJECTS COMPLETED")
print("=" * 60)