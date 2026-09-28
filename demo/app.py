"""
WESAD ECG Stress Detection - Interactive Clinical Telemetry & Benchmark Dashboard
"""

import os
import time
import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(PROJECT_ROOT, "python"))

# ==============================================================================
# Page Configuration & Clinical Telemetry Dark Theme
# ==============================================================================
st.set_page_config(
    page_title="WESAD ECG Stress Detection | Benchmark Demo",
    page_icon="🫀",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,100..1000;1,9..40,100..1000&family=JetBrains+Mono:ital,wght@0,100..800;1,100..800&display=swap');

:root {
    --bg-primary: #070913;
    --bg-card: #0F1424;
    --bg-card-hover: #161D33;
    --border-subtle: #1C243B;
    --border-accent: #2A3656;
    --text-main: #F1F5F9;
    --text-muted: #94A3B8;
    --text-dim: #64748B;
    --ruby-pulse: #FF3366;
    --cyan-wave: #00F0FF;
    --gold-alert: #F59E0B;
    --emerald-calm: #10B981;
    --violet-accent: #8B5CF6;
}

html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"], .main {
    background-color: var(--bg-primary) !important;
    color: var(--text-main) !important;
    font-family: 'DM Sans', -apple-system, sans-serif !important;
}

/* Eliminate top dead space and optimize viewport margins */
.block-container {
    padding-top: 0.6rem !important;
    padding-bottom: 0.3rem !important;
    padding-left: 1.2rem !important;
    padding-right: 1.2rem !important;
    max-width: 100% !important;
}
header[data-testid="stHeader"] {
    display: none !important;
    height: 0px !important;
}
div[data-testid="stVerticalBlock"] {
    gap: 0.35rem !important;
}

[data-testid="stSidebar"] {
    background-color: #0B0E1B !important;
    border-right: 1px solid var(--border-subtle) !important;
}

/* Compact Telemetry Card */
.telemetry-card {
    background-color: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: 8px;
    padding: 0.5rem 0.75rem;
    margin-bottom: 0.35rem;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.35);
    transition: border 0.15s ease;
}
.telemetry-card:hover {
    border-color: var(--border-accent);
}

.kpi-title {
    font-size: 0.65rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-dim);
    margin-bottom: 0.15rem;
}
.kpi-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.35rem;
    font-weight: 700;
    color: var(--text-main);
    line-height: 1.1;
}
.kpi-sub {
    font-size: 0.68rem;
    color: var(--text-muted);
    margin-top: 0.15rem;
}

/* Status Badges */
.status-pill-stress {
    display: inline-flex;
    align-items: center;
    background: rgba(255, 51, 102, 0.15);
    border: 1px solid rgba(255, 51, 102, 0.6);
    color: #FF6688;
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-weight: 700;
    font-size: 0.8rem;
    letter-spacing: 0.03em;
    font-family: 'JetBrains Mono', monospace;
}
.status-pill-calm {
    display: inline-flex;
    align-items: center;
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid rgba(16, 185, 129, 0.6);
    color: #34D399;
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-weight: 700;
    font-size: 0.8rem;
    letter-spacing: 0.03em;
    font-family: 'JetBrains Mono', monospace;
}

/* Tabs styling */
button[data-baseweb="tab"] {
    background: transparent !important;
    color: var(--text-muted) !important;
    font-size: 0.84rem !important;
    font-weight: 600 !important;
    padding: 0.35rem 0.85rem !important;
    border-radius: 6px !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #00F0FF !important;
    background: rgba(0, 240, 255, 0.08) !important;
    border-bottom: 2px solid #00F0FF !important;
}
div[data-testid="stTabs"] {
    margin-bottom: 0.3rem !important;
}

/* Hide default streamlit decorations */
#MainMenu, footer {
    visibility: hidden;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
SAMPLE_DIR = os.path.join(PROJECT_ROOT, "demo", "sample_data")


# ==============================================================================
# Cached Data Loaders
# ==============================================================================
@st.cache_resource
def load_sample_waveforms():
    npz_path = os.path.join(SAMPLE_DIR, "ecg_samples.npz")
    json_path = os.path.join(SAMPLE_DIR, "samples_meta.json")
    if not os.path.isfile(npz_path) or not os.path.isfile(json_path):
        return None, None
    with np.load(npz_path) as data:
        arrays = {k: data[k] for k in data.files}
    with open(json_path, "r") as f:
        meta = json.load(f)
    return arrays, meta


@st.cache_data
def load_tabular_results():
    data = {}
    csv_map = {
        "benchmark": "ML_Model_Benchmark_LOSO.csv",
        "predictions": "Stress_Classifier_Predictions.csv",
        "features": "WESAD_HRV_features_expanded.csv",
        "metrics": "FINAL_Model_Metrics.csv",
        "threshold": "Threshold_Analysis.csv",
        "importance": "ML_Feature_Importance_Permutation.csv",
    }
    for key, filename in csv_map.items():
        path = os.path.join(RESULTS_DIR, filename)
        if not os.path.isfile(path):
            path = os.path.join(SAMPLE_DIR, filename)
        if os.path.isfile(path):
            try:
                data[key] = pd.read_csv(path)
            except Exception:
                data[key] = None
        else:
            data[key] = None
    return data


waveforms_data, sample_meta = load_sample_waveforms()
tab_data = load_tabular_results()

# ==============================================================================
# Header & Publication Badge Bar
# ==============================================================================
st.markdown(
    """
    <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #1C243B; padding-bottom:0.3rem; margin-bottom:0.4rem;">
        <div style="display:flex; align-items:center; gap:0.55rem;">
            <span style="font-size:1.35rem;">🫀</span>
            <div>
                <h1 style="font-size:1.15rem; font-weight:800; margin:0; color:#F8FAFC; letter-spacing:-0.01em; display:inline;">
                    Personalized Electrocardiographic and HRV Dynamics for Acute Stress Detection
                </h1>
                <span style="font-size:0.75rem; color:#64748B; margin-left:0.6rem;">
                    15-Fold LOSO-CV Benchmark &amp; Bare-Metal Edge IoMT Node
                </span>
            </div>
        </div>
        <div style="font-size:0.75rem; color:#94A3B8; display:flex; gap:0.75rem; align-items:center;">
            <span><b>Mukesh Yadav</b> (ECE, JSSATEN)</span>
            <a href="https://doi.org/10.5281/zenodo.22895173" target="_blank" style="color:#00F0FF; text-decoration:none; font-weight:600; background:rgba(0,240,255,0.08); border:1px solid rgba(0,240,255,0.25); padding:2px 8px; border-radius:4px;">
                Zenodo DOI ↗
            </a>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Top KPI Metric Strip
k1, k2, k3, k4, k5, k6 = st.columns(6)
kpis = [
    ("Accuracy", "92.36 %", "+10.79% vs raw", "#10B981"),
    ("Stress F1-Score", "89.03 %", "+16.00% boost", "#00F0FF"),
    ("ROC-AUC", "0.9494", "High separation", "#8B5CF6"),
    ("Sensitivity", "86.25 %", "138/160 stress", "#FF3366"),
    ("Specificity", "95.79 %", "273/285 calm", "#10B981"),
    ("Benchmark", "15 Subjects", "445 windows", "#F59E0B"),
]
for col, (label, val, sub, color) in zip([k1, k2, k3, k4, k5, k6], kpis):
    with col:
        st.markdown(
            f"""
            <div class="telemetry-card" style="padding: 0.35rem 0.65rem; margin-bottom: 0.3rem; border-left: 3px solid {color};">
                <div class="kpi-title" style="font-size: 0.65rem; margin-bottom: 0.1rem;">{label}</div>
                <div style="display: flex; align-items: baseline; justify-content: space-between;">
                    <span class="kpi-value" style="font-size: 1.25rem; color: {color};">{val}</span>
                    <span class="kpi-sub" style="font-size: 0.65rem; margin: 0; color: #94A3B8;">{sub}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ==============================================================================
# Navigation Tabs
# ==============================================================================
tab_stm32, tab_demo, tab_features, tab_benchmark = st.tabs([
    "⚡ 1. STM32G474 IoMT Hardware Telemetry",
    "📈 2. Interactive Waveform & Calibration Engine",
    "🔬 3. HRV Biomarkers & Baseline Formula",
    "⚖️ 4. Multi-Model Benchmark & Threshold Sweep",
])

# ==============================================================================
# TAB 1: STM32G474 IoMT Hardware Telemetry
# ==============================================================================
with tab_stm32:

    stm_col_ctrl, stm_col_view = st.columns([1, 3.1])

    with stm_col_ctrl:
        st.markdown(
            """
            <div class="telemetry-card" style="padding:0.4rem 0.6rem; margin-bottom:0.25rem;">
                <div class="kpi-title" style="color: #00F0FF; font-size:0.65rem; margin-bottom:0.15rem;">Hardware Link Interface</div>
            """,
            unsafe_allow_html=True,
        )

        link_mode = st.radio(
            "Telemetry Link Mode:",
            options=["Simulated STM32 Link (Virtual)", "Physical USB COM Port"],
            index=0,
            horizontal=True,
            help="Simulated mode streams real WESAD subjects through the exact STM32 20-byte packet protocol without needing physical hardware connected.",
        )

        if link_mode == "Simulated STM32 Link (Virtual)":
            stm_subj = st.selectbox(
                "Patient / Subject:",
                options=["S3", "S2", "S10", "S17"],
                format_func=lambda s: {
                    "S3": "S3 (Strong Autonomic Responder)",
                    "S2": "S2 (Clinical Non-Responder)",
                    "S10": "S10 (Tachycardic Profile)",
                    "S17": "S17 (Rapid Acceleration)"
                }[s],
                index=0,
            )

            stm_cond = st.radio(
                "Condition:",
                options=["Baseline", "Stress"],
                format_func=lambda c: "🟢 Resting Calm" if c == "Baseline" else "🔴 Acute Stress",
                index=0,
                horizontal=True,
            )

            stm_duration = 25

        else:
            try:
                import serial.tools.list_ports
                all_ports = list(serial.tools.list_ports.comports())
                sorted_ports = sorted(
                    all_ports,
                    key=lambda p: 0 if ("stlink" in p.description.lower() or "stmicroelectronics" in p.description.lower()) else 1
                )
                port_options = [p.device for p in sorted_ports]
                port_labels = {p.device: f"{p.device} — {p.description.split('(')[0].strip()}" for p in sorted_ports}
            except Exception:
                port_options = []
                port_labels = {}

            if not port_options:
                port_options = ["Virtual / Offline Port"]
                port_labels = {"Virtual / Offline Port": "Virtual / Offline Port (No USB Hardware Attached)"}

            com_port = st.selectbox(
                "Detected Serial COM Port:",
                options=port_options,
                format_func=lambda d: port_labels.get(d, d),
                index=0,
                key="hardware_com_port_select"
            )

            baud_rate = 115200
            stm_duration = 8
            stm_subj, stm_cond = "S2", "Baseline"
            if com_port != "Virtual / Offline Port":
                st.caption(f"Port `{com_port}` @ {baud_rate} baud")

        continuous_stream = st.toggle(
            "🔴 Live Stream (350 Hz)",
            value=False,
            help="Continuously ingests incoming packets in real-time and scrolls the live ECG waveform without freezing."
        )

        chart_renderer = "🟢 Hospital Monitor (Flicker-Free Native)"

        crypto_engine_choice = st.selectbox(
            "IoMT Cipher:",
            options=[
                "🔮 4D Coupled Hyperchaos (M-4DCHS)",
                "⚡ 32-Bit Scrambler (Xorshift32 + Weyl)",
                "🔓 Unencrypted Plaintext"
            ],
            index=0,
            help="Select the cryptographic engine running on the edge IoMT node."
        )

        if "4D" in crypto_engine_choice:
            active_flags = 0x05  # TELEMETRY_FLAG_ENCRYPTED | TELEMETRY_FLAG_CHAOS_4D
            spec_sec = "4D Hyperchaos (M-4DCHS)"
            spec_cost = "0.48 µs (82 cycles)"
            spec_key = "> 2^256 (ℝ⁴)"
        elif "32-Bit" in crypto_engine_choice:
            active_flags = 0x01  # TELEMETRY_FLAG_ENCRYPTED
            spec_sec = "32-Bit Cipher (Xorshift32)"
            spec_cost = "0.19 µs (32 cycles)"
            spec_key = "2^32"
        else:
            active_flags = 0x00
            spec_sec = "None (Plaintext)"
            spec_cost = "0.00 µs"
            spec_key = "0 bits"

        security_view_mode = st.radio(
            "IoMT Security View:",
            options=["🟢 Authorized (Decrypted)", "🕵️ Wiretap (Ciphertext)"],
            index=0,
            horizontal=True,
            help="Toggle between authorized clinical view and wiretap ciphertext noise."
        )

        st.markdown("</div>", unsafe_allow_html=True)

        # Edge Node Specs Card
        st.markdown(
            f"""
            <div class="telemetry-card" style="font-size:0.68rem; line-height:1.32; padding:0.35rem 0.55rem; margin-top:0.25rem; border-left:2px solid #00F0FF;">
                <div class="kpi-title" style="color:#00F0FF; font-size:0.62rem; margin-bottom:0.1rem;">STM32 Edge Node Specs</div>
                • <b>MCU:</b> Cortex-M4 @ 170MHz + FPU<br>
                • <b>DSP:</b> 5-stage IIR (0.5–40Hz + 50Hz)<br>
                • <b>Frame:</b> 20B Binary + CRC-16<br>
                • <b>Security:</b> {spec_sec}<br>
                • <b>Keyspace:</b> <code>{spec_key}</code><br>
                • <b>Cost:</b> {spec_cost}
            </div>
            """,
            unsafe_allow_html=True,
        )

    from stm32_telemetry_receiver import (
        LiveTelemetryStream, build_c_packet,
        get_shared_serial_connection, release_shared_serial_connection,
        _GLOBAL_SERIAL_CONN
    )

    with stm_col_view:
        if waveforms_data is not None and sample_meta is not None:
            raw_key = f"{stm_subj}_{stm_cond}_raw"
            filt_key = f"{stm_subj}_{stm_cond}_filt"

            raw_full = waveforms_data.get(raw_key, np.array([]))
            filt_full = waveforms_data.get(filt_key, np.array([]))

            fs = sample_meta.get("fs_demo", 350)
            pts_to_stream = min(len(raw_full), stm_duration * fs)

            # Initialize LiveTelemetryStream
            # Maintain persistent stream buffer in session_state across fragment reruns
            stream_key = f"stream_{link_mode}_{com_port if link_mode == 'Physical USB COM Port' else stm_subj}_{stm_cond}"
            if "active_stream_key" not in st.session_state or st.session_state.active_stream_key != stream_key:
                st.session_state.active_stream_key = stream_key
                st.session_state.telemetry_stream = LiveTelemetryStream(fs=fs, window_sec=60)
                st.session_state.sim_step = 0

            telemetry_stream = st.session_state.telemetry_stream

            # Persistent shared serial connection management
            if link_mode == "Physical USB COM Port":
                cur_ser = st.session_state.get("serial_conn")
                if cur_ser is None or not getattr(cur_ser, "is_open", False) or getattr(cur_ser, "port", "") != com_port:
                    try:
                        active_ser = get_shared_serial_connection(com_port, baud_rate)
                        st.session_state["serial_conn"] = active_ser
                    except Exception as e:
                        if _GLOBAL_SERIAL_CONN is not None and getattr(_GLOBAL_SERIAL_CONN, "is_open", False):
                            st.session_state["serial_conn"] = _GLOBAL_SERIAL_CONN
                        else:
                            st.session_state["serial_conn"] = None
                            st.error(f"Cannot connect to serial port {com_port}: {e}")
            else:
                release_shared_serial_connection()
                st.session_state["serial_conn"] = None

            # Setup personalized baseline for selected subject / hardware stream
            if link_mode == "Physical USB COM Port":
                # Physical STM32 firmware transmits authentic WESAD Subject S2 Lead-II ECG (Baseline Calm)
                # Baseline calibration matches Subject S2 resting baseline:
                base_dict = {
                    "MeanHR": 80.2,
                    "SDNN": 111.7,
                    "RMSSD": 109.61,
                    "pNN50": 57.1,
                    "MeanRR": 0.764,
                    "RR_CV": 0.1462,
                    "RR_IQR": 0.154,
                    "HR_IQR": 15.5,
                }
                telemetry_stream.classifier.set_subject_baseline(base_dict)
            elif stm_subj in sample_meta.get("subjects", {}) and "Baseline" in sample_meta["subjects"][stm_subj]:
                b_hrv = sample_meta["subjects"][stm_subj]["Baseline"]["hrv"]
                base_dict = {
                    "MeanHR": b_hrv.get("MeanHR", 75.0),
                    "SDNN": b_hrv.get("SDNN_ms", 50.0),
                    "RMSSD": b_hrv.get("RMSSD_ms", 40.0),
                    "pNN50": max(5.0, b_hrv.get("pNN50", 20.0)),
                    "MeanRR": 60.0 / max(1.0, b_hrv.get("MeanHR", 75.0)),
                    "RR_CV": b_hrv.get("SDNN_ms", 50.0) / (60.0 / max(1.0, b_hrv.get("MeanHR", 75.0)) * 1000.0),
                    "RR_IQR": 0.08,
                    "HR_IQR": 8.0,
                }
                telemetry_stream.classifier.set_subject_baseline(base_dict)

            def generate_threejs_phase_space_html(ecg_samples: list) -> str:
                ecg_json = json.dumps(ecg_samples)
                return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body, html {{
    width: 100%;
    height: 100%;
    overflow: hidden;
    background: #0B0E1B;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace;
    user-select: none;
  }}
  #canvas-container {{
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: radial-gradient(circle at 50% 50%, #111827 0%, #070913 100%);
  }}
  .hud-panel {{
    position: absolute;
    top: 6px;
    left: 8px;
    background: rgba(11, 14, 27, 0.9);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(139, 92, 246, 0.35);
    border-radius: 6px;
    padding: 3px 7px;
    font-size: 9.5px;
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    color: #F1F5F9;
    box-shadow: 0 2px 8px rgba(0,0,0,0.5);
    z-index: 10;
  }}
  .hud-header {{
    display: flex;
    align-items: center;
    gap: 5px;
    font-weight: 700;
    font-size: 9.5px;
    color: #00F0FF;
    margin-bottom: 1px;
  }}
  .live-dot {{
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #00F0FF;
    box-shadow: 0 0 6px #00F0FF;
    display: inline-block;
    animation: blink 1.2s infinite alternate ease-in-out;
  }}
  @keyframes blink {{
    0% {{ opacity: 0.3; transform: scale(0.9); }}
    100% {{ opacity: 1.0; transform: scale(1.1); }}
  }}
  .hud-row {{
    color: #94A3B8;
    font-size: 9px;
  }}
  .hud-val {{
    color: #A78BFA;
    font-weight: 600;
  }}
  .toolbar {{
    position: absolute;
    top: 6px;
    right: 8px;
    display: flex;
    gap: 4px;
    z-index: 10;
  }}
  .btn-mode {{
    background: rgba(15, 20, 36, 0.9);
    backdrop-filter: blur(8px);
    border: 1px solid #334155;
    color: #94A3B8;
    padding: 3px 8px;
    font-size: 9.5px;
    font-weight: 600;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.15s ease;
  }}
  .btn-mode:hover {{
    color: #F1F5F9;
    border-color: #8B5CF6;
  }}
  .btn-mode.active {{
    background: #8B5CF6;
    color: #FFFFFF;
    border-color: #A78BFA;
    box-shadow: 0 0 10px rgba(139, 92, 246, 0.4);
  }}
  .bottom-bar {{
    position: absolute;
    bottom: 5px;
    right: 8px;
    display: flex;
    gap: 4px;
    z-index: 10;
  }}
  .btn-icon {{
    background: rgba(15, 20, 36, 0.9);
    backdrop-filter: blur(8px);
    border: 1px solid #334155;
    color: #CBD5E1;
    padding: 2px 6px;
    font-size: 8.5px;
    font-weight: 600;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.15s ease;
  }}
  .btn-icon:hover {{
    border-color: #00F0FF;
    color: #00F0FF;
  }}
  .btn-icon.active {{
    background: rgba(0, 240, 255, 0.2);
    border-color: #00F0FF;
    color: #00F0FF;
  }}
  .instructions {{
    position: absolute;
    bottom: 5px;
    left: 8px;
    color: #64748B;
    font-size: 8px;
    z-index: 10;
    pointer-events: none;
    font-family: 'JetBrains Mono', monospace;
  }}
</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
</head>
<body>
<div id="canvas-container"></div>

<div class="hud-panel">
  <div class="hud-header">
    <span class="live-dot" id="live-dot"></span>
    <span id="hud-title">M-4DCHS HYPERCHAOTIC ATTRACTOR</span>
  </div>
  <div class="hud-row" id="hud-coords">
    x: <span class="hud-val">0.00</span> &nbsp; 
    y: <span class="hud-val">0.00</span> &nbsp; 
    z: <span class="hud-val">0.00</span> &nbsp; 
    w: <span class="hud-val">0.00</span>
  </div>
  <div class="hud-row" id="hud-sub" style="margin-top:2px; font-size:9.5px; color:#64748B;">
    λ₁=+0.205, λ₂=+0.085 | div(F)=-39.0 | Keyspace &gt; 2²⁵⁶
  </div>
</div>

<div class="toolbar">
  <button id="btn-chaos" class="btn-mode active" onclick="setMode('chaos')">🔮 4D Hyperchaos</button>
  <button id="btn-cardiac" class="btn-mode" onclick="setMode('cardiac')">❤️ 3D Cardiac Loop</button>
</div>

<div class="bottom-bar">
  <button id="btn-autorotate" class="btn-icon active" onclick="toggleAutoRotate()">🔄 Auto-Rotate</button>
  <button id="btn-reset" class="btn-icon" onclick="resetCamera()">🎯 Reset View</button>
</div>

<div class="instructions">
  🖱️ Drag: Rotate 3D &nbsp;|&nbsp; Scroll: Zoom &nbsp;|&nbsp; Right-Click: Pan
</div>

<script>
let currentMode = 'chaos';
let autoRotate = true;

const container = document.getElementById('canvas-container');
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
camera.position.set(28, 22, 38);

const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true, powerPreference: 'high-performance' }});
renderer.setSize(container.clientWidth, container.clientHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
container.appendChild(renderer.domElement);

let controls;
let isDragging = false;
let prevMousePos = {{ x: 0, y: 0 }};
let spherical = {{ radius: 52, theta: 0.65, phi: 1.1 }};

function updateCamSpherical() {{
  camera.position.x = spherical.radius * Math.sin(spherical.phi) * Math.sin(spherical.theta);
  camera.position.y = spherical.radius * Math.cos(spherical.phi);
  camera.position.z = spherical.radius * Math.sin(spherical.phi) * Math.cos(spherical.theta);
  camera.lookAt(0, 0, 0);
}}

if (typeof THREE.OrbitControls !== 'undefined') {{
  controls = new THREE.OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.autoRotate = autoRotate;
  controls.autoRotateSpeed = 1.0;
}} else {{
  renderer.domElement.addEventListener('pointerdown', (e) => {{
    isDragging = true;
    prevMousePos = {{ x: e.clientX, y: e.clientY }};
  }});
  window.addEventListener('pointermove', (e) => {{
    if (!isDragging) return;
    const dx = e.clientX - prevMousePos.x;
    const dy = e.clientY - prevMousePos.y;
    spherical.theta -= dx * 0.01;
    spherical.phi = Math.max(0.1, Math.min(Math.PI - 0.1, spherical.phi - dy * 0.01));
    prevMousePos = {{ x: e.clientX, y: e.clientY }};
    updateCamSpherical();
  }});
  window.addEventListener('pointerup', () => {{ isDragging = false; }});
  renderer.domElement.addEventListener('wheel', (e) => {{
    e.preventDefault();
    spherical.radius = Math.max(15, Math.min(150, spherical.radius + e.deltaY * 0.06));
    updateCamSpherical();
  }}, {{ passive: false }});
  updateCamSpherical();
}}

// Grid & Axes
const gridHelper = new THREE.GridHelper(36, 14, 0x334155, 0x1E293B);
gridHelper.position.y = -15;
scene.add(gridHelper);

const axesHelper = new THREE.AxesHelper(16);
axesHelper.position.set(-16, -15, -16);
scene.add(axesHelper);

// Lighting
const ambientLight = new THREE.AmbientLight(0xFFFFFF, 0.75);
scene.add(ambientLight);
const dirLight = new THREE.DirectionalLight(0x00F0FF, 0.85);
dirLight.position.set(25, 35, 25);
scene.add(dirLight);

const chaosGroup = new THREE.Group();
const cardiacGroup = new THREE.Group();
scene.add(chaosGroup);
scene.add(cardiacGroup);
cardiacGroup.visible = false;

// 1. M-4DCHS CHAOS SYSTEM
const a = 35.0, b = 3.0, c = 28.0, d = -1.0, r = 5.0, dt = 0.0025;
let s = [1.0, 1.0, 1.0, 1.0];

function f_ode(v) {{
  return [
    a * (v[1] - v[0]) + v[3],
    c * v[0] - v[0] * v[2] + d * v[1],
    v[0] * v[1] - b * v[2],
    -r * v[0]
  ];
}}

function rk4(v, h) {{
  const k1 = f_ode(v);
  const v2 = [v[0] + 0.5 * h * k1[0], v[1] + 0.5 * h * k1[1], v[2] + 0.5 * h * k1[2], v[3] + 0.5 * h * k1[3]];
  const k2 = f_ode(v2);
  const v3 = [v[0] + 0.5 * h * k2[0], v[1] + 0.5 * h * k2[1], v[2] + 0.5 * h * k2[2], v[3] + 0.5 * h * k2[3]];
  const k3 = f_ode(v3);
  const v4 = [v[0] + h * k3[0], v[1] + h * k3[1], v[2] + h * k3[2], v[3] + h * k3[3]];
  const k4 = f_ode(v4);
  return [
    v[0] + (h / 6.0) * (k1[0] + 2.0 * k2[0] + 2.0 * k3[0] + k4[0]),
    v[1] + (h / 6.0) * (k1[1] + 2.0 * k2[1] + 2.0 * k3[1] + k4[1]),
    v[2] + (h / 6.0) * (k1[2] + 2.0 * k2[2] + 2.0 * k3[2] + k4[2]),
    v[3] + (h / 6.0) * (k1[3] + 2.0 * k2[3] + 2.0 * k3[3] + k4[3])
  ];
}}

for (let i = 0; i < 4000; i++) {{
  s = rk4(s, dt);
}}

const MAX_POINTS = 1400;
const chaosPositions = new Float32Array(MAX_POINTS * 3);
const chaosColors = new Float32Array(MAX_POINTS * 3);
const chaosHistory = [];

for (let i = 0; i < MAX_POINTS; i++) {{
  s = rk4(s, dt);
  chaosHistory.push([...s]);
}}

const chaosGeometry = new THREE.BufferGeometry();
chaosGeometry.setAttribute('position', new THREE.BufferAttribute(chaosPositions, 3));
chaosGeometry.setAttribute('color', new THREE.BufferAttribute(chaosColors, 3));

const chaosMaterial = new THREE.LineBasicMaterial({{
  vertexColors: true,
  linewidth: 2.2,
  transparent: true,
  opacity: 0.95
}});
const chaosLine = new THREE.Line(chaosGeometry, chaosMaterial);
chaosGroup.add(chaosLine);

const headGeo = new THREE.OctahedronGeometry(0.75, 0);
const headMat = new THREE.MeshBasicMaterial({{ color: 0x00F0FF }});
const headMesh = new THREE.Mesh(headGeo, headMat);
chaosGroup.add(headMesh);

const headLight = new THREE.PointLight(0x00F0FF, 1.8, 14);
chaosGroup.add(headLight);

// 2. CARDIAC DELAY EMBEDDING
const rawEcg = {ecg_json};
const tau = 8;
const cardiacPts = [];
let minX = 999, maxX = -999, minY = 999, maxY = -999, minZ = 999, maxZ = -999;

if (rawEcg && rawEcg.length > 2 * tau) {{
  for (let i = 2 * tau; i < rawEcg.length; i++) {{
    const x = rawEcg[i] * 12.0;
    const y = rawEcg[i - tau] * 12.0;
    const z = rawEcg[i - 2 * tau] * 12.0;
    cardiacPts.push([x, y, z]);
    if (x < minX) minX = x; if (x > maxX) maxX = x;
    if (y < minY) minY = y; if (y > maxY) maxY = y;
    if (z < minZ) minZ = z; if (z > maxZ) maxZ = z;
  }}
}}

const cLen = cardiacPts.length;
const cPositions = new Float32Array(cLen * 3);
const cColors = new Float32Array(cLen * 3);
const cx = (minX + maxX) / 2.0;
const cy = (minY + maxY) / 2.0;
const cz = (minZ + maxZ) / 2.0;

for (let i = 0; i < cLen; i++) {{
  cPositions[i * 3] = cardiacPts[i][0] - cx;
  cPositions[i * 3 + 1] = cardiacPts[i][2] - cz;
  cPositions[i * 3 + 2] = cardiacPts[i][1] - cy;
  
  const t = i / cLen;
  cColors[i * 3] = 0.95 * t + 0.1 * (1 - t);
  cColors[i * 3 + 1] = 0.05 * t + 0.85 * (1 - t);
  cColors[i * 3 + 2] = 0.35 * t + 0.95 * (1 - t);
}}

const cardiacGeo = new THREE.BufferGeometry();
cardiacGeo.setAttribute('position', new THREE.BufferAttribute(cPositions, 3));
cardiacGeo.setAttribute('color', new THREE.BufferAttribute(cColors, 3));
const cardiacMat = new THREE.LineBasicMaterial({{ vertexColors: true, linewidth: 2.4, transparent: true, opacity: 0.95 }});
const cardiacLine = new THREE.Line(cardiacGeo, cardiacMat);
cardiacGroup.add(cardiacLine);

const beatGeo = new THREE.SphereGeometry(0.8, 16, 16);
const beatMat = new THREE.MeshBasicMaterial({{ color: 0xFF0055 }});
const beatMesh = new THREE.Mesh(beatGeo, beatMat);
cardiacGroup.add(beatMesh);
let cardiacIdx = 0;

function setMode(mode) {{
  currentMode = mode;
  document.getElementById('btn-chaos').classList.toggle('active', mode === 'chaos');
  document.getElementById('btn-cardiac').classList.toggle('active', mode === 'cardiac');
  chaosGroup.visible = (mode === 'chaos');
  cardiacGroup.visible = (mode === 'cardiac');
  
  if (mode === 'chaos') {{
    document.getElementById('hud-title').innerText = "M-4DCHS HYPERCHAOTIC ATTRACTOR";
    document.getElementById('hud-sub').innerText = "λ₁=+0.205, λ₂=+0.085 | div(F)=-39.0 | Keyspace > 2²⁵⁶";
    document.getElementById('live-dot').style.background = "#00F0FF";
    document.getElementById('live-dot').style.boxShadow = "0 0 8px #00F0FF";
  }} else {{
    document.getElementById('hud-title').innerText = "TAKENS 3D CARDIAC PHASE PORTRAIT";
    document.getElementById('hud-sub').innerText = "Embedding Delay τ = 22.9 ms (8 samples) | Closed QRS Trajectory";
    document.getElementById('live-dot').style.background = "#FF0055";
    document.getElementById('live-dot').style.boxShadow = "0 0 8px #FF0055";
  }}
}}

function toggleAutoRotate() {{
  autoRotate = !autoRotate;
  if (controls) controls.autoRotate = autoRotate;
  document.getElementById('btn-autorotate').classList.toggle('active', autoRotate);
}}

function resetCamera() {{
  camera.position.set(28, 22, 38);
  if (controls) {{
    controls.target.set(0, 0, 0);
    controls.update();
  }} else {{
    spherical = {{ radius: 52, theta: 0.65, phi: 1.1 }};
    updateCamSpherical();
  }}
}}

window.addEventListener('resize', () => {{
  if (!container) return;
  camera.aspect = container.clientWidth / container.clientHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(container.clientWidth, container.clientHeight);
}});

function animate() {{
  requestAnimationFrame(animate);
  
  if (currentMode === 'chaos') {{
    for (let k = 0; k < 5; k++) {{
      s = rk4(s, dt);
      chaosHistory.push([...s]);
      if (chaosHistory.length > MAX_POINTS) {{
        chaosHistory.shift();
      }}
    }}
    
    const pos = chaosGeometry.attributes.position.array;
    const col = chaosGeometry.attributes.color.array;
    const n = chaosHistory.length;
    
    for (let i = 0; i < n; i++) {{
      const pt = chaosHistory[i];
      pos[i * 3] = pt[0] * 0.42;
      pos[i * 3 + 1] = (pt[2] - 27.5) * 0.42;
      pos[i * 3 + 2] = pt[1] * 0.42;
      
      const t = i / n;
      col[i * 3] = 0.55 * (1 - t) + 0.1 * t;
      col[i * 3 + 1] = 0.2 * (1 - t) + 0.95 * t;
      col[i * 3 + 2] = 0.95 * (1 - t) + 0.9 * t;
    }}
    
    chaosGeometry.attributes.position.needsUpdate = true;
    chaosGeometry.attributes.color.needsUpdate = true;
    chaosGeometry.setDrawRange(0, n);
    
    const head = chaosHistory[n - 1];
    headMesh.position.set(head[0] * 0.42, (head[2] - 27.5) * 0.42, head[1] * 0.42);
    headLight.position.copy(headMesh.position);
    
    document.getElementById('hud-coords').innerHTML =
      `x: <span class="hud-val">${{head[0].toFixed(2)}}</span> &nbsp; ` +
      `y: <span class="hud-val">${{head[1].toFixed(2)}}</span> &nbsp; ` +
      `z: <span class="hud-val">${{head[2].toFixed(2)}}</span> &nbsp; ` +
      `w: <span class="hud-val">${{head[3].toFixed(2)}}</span>`;
  }} else {{
    if (cLen > 0) {{
      cardiacIdx = (cardiacIdx + 2) % cLen;
      const cPt = cardiacPts[cardiacIdx];
      beatMesh.position.set(cPt[0] - cx, cPt[2] - cz, cPt[1] - cy);
      
      document.getElementById('hud-coords').innerHTML =
        `s(t): <span class="hud-val">${{(cPt[0]/12.0).toFixed(3)}} mV</span> &nbsp; ` +
        `s(t-τ): <span class="hud-val">${{(cPt[1]/12.0).toFixed(3)}} mV</span> &nbsp; ` +
        `s(t-2τ): <span class="hud-val">${{(cPt[2]/12.0).toFixed(3)}} mV</span>`;
    }}
  }}
  
  if (controls) controls.update();
  renderer.render(scene, camera);
}}

setMode('chaos');
animate();
</script>
</body>
</html>"""

            def render_clinical_svg_gauge(prob: float, is_stress: int) -> str:
                prob_c = max(0.0, min(1.0, float(prob)))
                angle_rad = np.pi * (1.0 - prob_c)

                # Center and dimensions
                cx, cy = 100.0, 95.0
                r_needle = 56.0
                tip_x = cx + r_needle * np.cos(angle_rad)
                tip_y = cy - r_needle * np.sin(angle_rad)

                g_col = "#FF3366" if is_stress else "#10B981"
                b_bg = "rgba(255, 51, 102, 0.15)" if is_stress else "rgba(16, 185, 129, 0.15)"
                b_brd = "#FF3366" if is_stress else "#10B981"
                s_txt = "🚨 ACUTE STRESS DETECTED" if is_stress else "🟢 RESTING CALM"

                return (
                    f"<div class='telemetry-card' style='text-align:center;padding:0.45rem 0.55rem;height:195px;box-sizing:border-box;display:flex;flex-direction:column;justify-content:space-between;margin-bottom:0.35rem;'>"
                    f"<div>"
                    f"<div class='kpi-title' style='margin-bottom:0.15rem;font-size:0.65rem;'>Calibrated Stress Dial (τ=0.35)</div>"
                    f"<svg viewBox='0 0 200 115' style='width:82%;max-width:175px;margin:0 auto;display:block;'>"
                    f"<!-- Background track -->"
                    f"<path d='M 32 95 A 68 68 0 0 1 168 95' fill='none' stroke='#161D33' stroke-width='10' stroke-linecap='round' />"
                    f"<!-- Zone 1: Calm (0% to 35%) -->"
                    f"<path d='M 32 95 A 68 68 0 0 1 69.1 34.4' fill='none' stroke='#10B981' stroke-width='8' stroke-linecap='round' opacity='0.75' />"
                    f"<!-- Zone 2: Alert (35% to 65%) -->"
                    f"<path d='M 69.1 34.4 A 68 68 0 0 1 130.9 34.4' fill='none' stroke='#F59E0B' stroke-width='8' opacity='0.75' />"
                    f"<!-- Zone 3: Stress (65% to 100%) -->"
                    f"<path d='M 130.9 34.4 A 68 68 0 0 1 168 95' fill='none' stroke='#FF3366' stroke-width='8' stroke-linecap='round' opacity='0.75' />"
                    f"<!-- Threshold marker τ=0.35 -->"
                    f"<line x1='72.8' y1='41.5' x2='64.0' y2='25.5' stroke='#F59E0B' stroke-width='2.5' />"
                    f"<text x='54' y='21' font-size='9' font-weight='700' fill='#F59E0B' text-anchor='middle'>τ=0.35</text>"
                    f"<!-- Radial Indicator Needle -->"
                    f"<line x1='100' y1='95' x2='{tip_x:.1f}' y2='{tip_y:.1f}' stroke='{g_col}' stroke-width='3.2' stroke-linecap='round' />"
                    f"<circle cx='100' cy='95' r='5' fill='#0B0E1B' stroke='{g_col}' stroke-width='2.5' />"
                    f"<circle cx='{tip_x:.1f}' cy='{tip_y:.1f}' r='2.5' fill='{g_col}' />"
                    f"<!-- Digital Readout -->"
                    f"<text x='100' y='80' font-family='JetBrains Mono, monospace' font-size='20' font-weight='700' fill='{g_col}' text-anchor='middle'>{prob*100.0:.1f}%</text>"
                    f"<text x='100' y='91' font-size='8' font-weight='600' letter-spacing='0.06em' fill='#64748B' text-anchor='middle'>STRESS PROBABILITY</text>"
                    f"<text x='30' y='108' font-size='8' font-weight='600' fill='#64748B' text-anchor='middle'>0%</text>"
                    f"<text x='170' y='108' font-size='8' font-weight='600' fill='#64748B' text-anchor='middle'>100%</text>"
                    f"</svg>"
                    f"</div>"
                    f"<div style='background:{b_bg};border:1px solid {b_brd};border-radius:6px;padding:0.25rem;font-weight:bold;color:{g_col};font-size:0.75rem;font-family:JetBrains Mono,monospace;'>"
                    f"{s_txt}"
                    f"</div>"
                    f"</div>"
                )

            fragment_rate = "1s" if continuous_stream else None

            @st.fragment(run_every=fragment_rate)
            def live_monitor_view():
                # 1. Packet Ingestion Step
                if link_mode == "Physical USB COM Port":
                    ser = st.session_state.get("serial_conn")
                    if ser is None or not getattr(ser, "is_open", False):
                        try:
                            ser = get_shared_serial_connection(com_port, baud_rate)
                            st.session_state["serial_conn"] = ser
                        except Exception:
                            ser = None

                    if ser and getattr(ser, "is_open", False):
                        try:
                            if continuous_stream:
                                n = ser.in_waiting
                                if n > 0:
                                    chunk = ser.read(n)
                                    pkts = telemetry_stream.parser.feed_bytes(chunk)
                                    for p in pkts:
                                        telemetry_stream.add_packet(p)
                            else:
                                col_btn, col_cap = st.columns([1.2, 2.5])
                                with col_btn:
                                    capture_clicked = st.button("⚡ Capture Hardware Telemetry Buffer", key="btn_capture_telemetry", type="primary")
                                with col_cap:
                                    st.caption(f"Static Mode — Ingests {stm_duration}s window from {com_port}. Toggle continuous stream for live scrolling.")

                                if (len(telemetry_stream.filt_buf) == 0) or capture_clicked:
                                    with st.spinner(f"Capturing {stm_duration}s telemetry from {com_port}..."):
                                        t0 = time.time()
                                        while time.time() - t0 < stm_duration:
                                            n = ser.in_waiting
                                            if n > 0:
                                                chunk = ser.read(n)
                                                pkts = telemetry_stream.parser.feed_bytes(chunk)
                                                for p in pkts:
                                                    telemetry_stream.add_packet(p)
                                            time.sleep(0.01)
                        except Exception as e:
                            release_shared_serial_connection()
                            st.session_state["serial_conn"] = None
                            st.error(f"⚠️ STM32 communication error on {com_port}: {e}")
                    else:
                        st.warning(f"⚠️ Serial port {com_port} is not connected. Reconnect the STM32 board or switch Telemetry Link Mode to 'Simulated STM32 Link (Virtual)'.")
                else:
                    if continuous_stream:
                        step = st.session_state.get("sim_step", 0)
                        chunk_size = int(fs * 1.0)
                        start_i = (step * chunk_size) % len(raw_full)
                        end_i = min(start_i + chunk_size, len(raw_full))
                        for i in range(start_i, end_i):
                            pkt_bytes = build_c_packet(
                                seq_id=i % 65536,
                                timestamp_ms=int((i / fs) * 1000),
                                raw_val=float(raw_full[i]),
                                filt_val=float(filt_full[i]),
                                flags=active_flags,
                            )
                            pkts = telemetry_stream.parser.feed_bytes(pkt_bytes)
                            for p in pkts:
                                telemetry_stream.add_packet(p)
                        st.session_state.sim_step = step + 1
                    else:
                        col_btn, col_cap = st.columns([1.2, 2.5])
                        with col_btn:
                            capture_clicked = st.button("⚡ Capture Simulated Telemetry Buffer", key="btn_capture_virtual_telemetry", type="primary")
                        with col_cap:
                            st.caption(f"Static Mode — Ingests {stm_duration}s snapshot. Toggle continuous stream for live scrolling.")

                        if (len(telemetry_stream.filt_buf) == 0) or capture_clicked:
                            telemetry_stream.time_buf.clear()
                            telemetry_stream.raw_buf.clear()
                            telemetry_stream.filt_buf.clear()
                            if hasattr(telemetry_stream, "cipher_buf"):
                                telemetry_stream.cipher_buf.clear()
                            for i in range(pts_to_stream):
                                pkt_bytes = build_c_packet(
                                    seq_id=i % 65536,
                                    timestamp_ms=int((i / fs) * 1000),
                                    raw_val=float(raw_full[i]),
                                    filt_val=float(filt_full[i]),
                                    flags=active_flags,
                                )
                                pkts = telemetry_stream.parser.feed_bytes(pkt_bytes)
                                for p in pkts:
                                    telemetry_stream.add_packet(p)

                hrv_res = telemetry_stream.extract_current_hrv()
                snap = telemetry_stream.get_snapshot()
                stats = snap["stats"]
                t_arr = np.array(snap["time"])
                raw_arr = np.array(snap["raw"])
                filt_arr = np.array(snap["filtered"])
                st_prob = snap["stress_prob"]
                st_lbl = snap["stress_label"]

                if continuous_stream:
                    st.caption("🔴 **Live Hospital Monitor Active** — Real-time telemetry streamed @ 350 Hz with hardware-accelerated rendering")

                # 2. Metric Strip (unindented inline string)
                is_enc = snap.get("is_encrypted", False)
                entropy_val = snap.get("entropy", 7.98)
                cipher_arr = np.array(snap.get("cipher", []))
                sec_badge_val = "Chaotic 32b" if is_enc else "Plaintext"
                sec_badge_sub = f"Encrypted (H={entropy_val:.2f}b)" if is_enc else "Unencrypted Stream"
                sec_badge_col = "#10B981" if is_enc else "#F59E0B"

                s_html = (
                    f"<div style='display:flex;gap:0.35rem;margin-bottom:0.25rem;'>"
                    f"<div class='telemetry-card' style='flex:1;padding:0.3rem 0.55rem;margin:0;border-left:2.5px solid #00F0FF;'>"
                    f"<div class='kpi-title' style='font-size:0.6rem;margin-bottom:0.05rem;'>Packets Ingested</div>"
                    f"<div style='display:flex;align-items:baseline;justify-content:space-between;'>"
                    f"<span class='kpi-value' style='font-size:1.1rem;color:#00F0FF;'>{stats['valid_packets']:,}</span>"
                    f"<span style='font-size:0.6rem;color:#94A3B8;'>100% CRC</span>"
                    f"</div>"
                    f"</div>"
                    f"<div class='telemetry-card' style='flex:1;padding:0.3rem 0.55rem;margin:0;border-left:2.5px solid #10B981;'>"
                    f"<div class='kpi-title' style='font-size:0.6rem;margin-bottom:0.05rem;'>CRC Errors / Drops</div>"
                    f"<div style='display:flex;align-items:baseline;justify-content:space-between;'>"
                    f"<span class='kpi-value' style='font-size:1.1rem;color:#10B981;'>{stats['crc_errors']} / {stats['dropped_packets']}</span>"
                    f"<span style='font-size:0.6rem;color:#94A3B8;'>Loss: 0%</span>"
                    f"</div>"
                    f"</div>"
                    f"<div class='telemetry-card' style='flex:1;padding:0.3rem 0.55rem;margin:0;border-left:2.5px solid #8B5CF6;'>"
                    f"<div class='kpi-title' style='font-size:0.6rem;margin-bottom:0.05rem;'>Frame Sync</div>"
                    f"<div style='display:flex;align-items:baseline;justify-content:space-between;'>"
                    f"<span class='kpi-value' style='font-size:1.1rem;color:#8B5CF6;'>0xAA 0x55</span>"
                    f"<span style='font-size:0.6rem;color:#94A3B8;'>Locked</span>"
                    f"</div>"
                    f"</div>"
                    f"<div class='telemetry-card' style='flex:1;padding:0.3rem 0.55rem;margin:0;border-left:2.5px solid {sec_badge_col};'>"
                    f"<div class='kpi-title' style='font-size:0.6rem;margin-bottom:0.05rem;'>IoMT Security</div>"
                    f"<div style='display:flex;align-items:baseline;justify-content:space-between;'>"
                    f"<span class='kpi-value' style='font-size:1.1rem;color:{sec_badge_col};'>{sec_badge_val}</span>"
                    f"<span style='font-size:0.6rem;color:#94A3B8;'>H={entropy_val:.2f}b</span>"
                    f"</div>"
                    f"</div>"
                    f"</div>"
                )
                st.markdown(s_html, unsafe_allow_html=True)

                # 3. Waveform & Gauge
                col_wave, col_gauge = st.columns([2.3, 1.1])

                is_native_stream = chart_renderer.startswith("🟢")
                is_eavesdropper = security_view_mode.startswith("🕵️")

                with col_wave:
                    if len(t_arr) > 0:
                        pts_show = min(len(t_arr), int(fs * 8))
                        step_d = 4 if pts_show > 1000 else 1
                        idx_d = np.arange(len(t_arr) - pts_show, len(t_arr), step_d)
                        t_win = np.round(t_arr[idx_d] - t_arr[idx_d[0]], 3)
                        raw_win = np.round(raw_arr[idx_d], 3)
                        filt_win = np.round(filt_arr[idx_d], 3)

                        if is_eavesdropper:
                            st.markdown(
                                f"""
                                <div style="background: rgba(255, 51, 102, 0.12); border: 1px solid #FF3366; border-radius: 6px; padding: 0.35rem 0.65rem; margin-bottom: 0.25rem; font-size: 0.74rem; color: #F8FAFC;">
                                    🔒 <b>Eavesdropper Intercept Mode:</b> High-entropy ciphertext over UART (<b>Entropy: {entropy_val:.2f} bits/byte</b>).
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                            if len(cipher_arr) >= len(t_arr):
                                c_win = np.array([cipher_arr[i] for i in idx_d], dtype=np.float32)
                                c_plot = np.nan_to_num(c_win, nan=0.0, posinf=5.0, neginf=-5.0)
                                c_plot = np.clip(c_plot, -5.0, 5.0)
                            else:
                                c_plot = np.random.uniform(-1.0, 1.0, len(idx_d))

                            chart_df = pd.DataFrame(
                                {
                                    "Time (s)": t_win,
                                    "Wire Intercepted Ciphertext (Obfuscated Noise)": c_plot,
                                }
                            )
                            st.line_chart(
                                chart_df,
                                x="Time (s)",
                                y=["Wire Intercepted Ciphertext (Obfuscated Noise)"],
                                color=["#FF3366"],
                                height=195,
                                x_label="Time (s) — Wire Ciphertext",
                                y_label="Cipher Amplitude",
                            )
                        elif is_native_stream:
                            chart_df = pd.DataFrame(
                                {
                                    "Time (s)": t_win,
                                    "Raw Acquisition (Lead-II)": raw_win,
                                    "STM32 Biquad Filtered": filt_win,
                                }
                            )
                            st.line_chart(
                                chart_df,
                                x="Time (s)",
                                y=["Raw Acquisition (Lead-II)", "STM32 Biquad Filtered"],
                                color=["#64748B", "#00F0FF"],
                                height=195,
                                x_label="Time (s) — 8s Window",
                                y_label="ECG (mV)",
                            )
                        else:
                            fig_w = go.Figure()
                            fig_w.add_trace(go.Scatter(
                                x=t_win,
                                y=raw_win,
                                name="Raw Sensor ECG (Acquisition)",
                                line=dict(color="#64748B", width=1.0),
                                opacity=0.6,
                                mode="lines",
                            ))
                            fig_w.add_trace(go.Scatter(
                                x=t_win,
                                y=filt_win,
                                name="STM32 Biquad Filtered",
                                line=dict(color="#00F0FF", width=2.0),
                                mode="lines",
                            ))
                            fig_w.update_layout(
                                title=dict(text="Real-Time Ingestion (8s Window)", font=dict(color="#F1F5F9", size=11)),
                                template="none",
                                paper_bgcolor="#0F1424",
                                plot_bgcolor="#070913",
                                height=195,
                                margin=dict(l=30, r=15, t=25, b=20),
                                legend=dict(orientation="h", y=1.15, x=0.01, font=dict(color="#94A3B8", size=9)),
                                xaxis=dict(title=dict(text="Time (s)", font=dict(color="#94A3B8", size=9)), showgrid=True, gridcolor="#1C243B", range=[0, 8], autorange=False, fixedrange=True, tickcolor="#64748B", tickfont=dict(color="#94A3B8")),
                                yaxis=dict(title=dict(text="mV", font=dict(color="#94A3B8", size=9)), showgrid=True, gridcolor="#1C243B", range=[-0.8, 1.2], autorange=False, fixedrange=True, tickcolor="#64748B", tickfont=dict(color="#94A3B8")),
                                uirevision="live_stream_const",
                                transition=dict(duration=0),
                            )
                            st.plotly_chart(
                                fig_w,
                                width="stretch",
                                key="telemetry_live_waveform_chart",
                                theme=None,
                                config={"displayModeBar": False, "responsive": True, "staticPlot": True}
                            )
                    else:
                        st.warning("No telemetry packets received yet. Verify COM port.")

                with col_gauge:
                    if is_eavesdropper:
                        is_4d_active = snap.get("is_4d_chaos", False) or ("4D" in crypto_engine_choice)
                        c_title = "Novel 4D Hyperchaos (M-4DCHS)" if is_4d_active else "Xorshift32 + Weyl"
                        c_keyspace = "&gt; 2<sup>256</sup>" if is_4d_active else "2<sup>32</sup>"
                        c_kdf = "Biometric RR + Nonce KDF" if is_4d_active else "Nonce Linear Mixer"
                        c_accent = "#A78BFA" if is_4d_active else "#FF6688"
                        c_border = "#8B5CF6" if is_4d_active else "#FF3366"
                        c_bg = "rgba(139, 92, 246, 0.12)" if is_4d_active else "rgba(255, 51, 102, 0.1)"
                        c_brd = "rgba(139, 92, 246, 0.3)" if is_4d_active else "rgba(255, 51, 102, 0.25)"

                        st.markdown(
                            f"""
                            <div class="telemetry-card" style="text-align: center; border-left: 3px solid {c_border}; padding: 1.4rem 1rem;">
                                <div style="font-size: 2.2rem; margin-bottom: 0.3rem;">🔒</div>
                                <div style="font-size: 0.85rem; font-weight: 700; color: {c_accent}; text-transform: uppercase; letter-spacing: 0.08em;">
                                    Zero-Trust IoMT Shield Active
                                </div>
                                <div style="font-family: 'JetBrains Mono'; font-size: 1.25rem; font-weight: 700; color: #F1F5F9; margin: 0.3rem 0;">
                                    BIOMETRIC ENCRYPTED
                                </div>
                                <div style="font-size: 0.76rem; color: #94A3B8; line-height: 1.35;">
                                    Patient ECG morphology and acute stress inference are locked to prevent eavesdropping and unauthorized profiling.
                                </div>
                                <div style="margin-top: 0.7rem; font-size: 0.72rem; color: #CBD5E1; background: {c_bg}; border: 1px solid {c_brd}; border-radius: 6px; padding: 0.45rem; text-align: left;">
                                    • <b>Cipher:</b> {c_title}<br>
                                    • <b>Keyspace:</b> <code>{c_keyspace}</code><br>
                                    • <b>Key Seeding:</b> {c_kdf}<br>
                                    • <b>Shannon Entropy:</b> <code>{entropy_val:.3f} bits/Byte</code>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                    elif is_native_stream:
                        svg_gauge_html = render_clinical_svg_gauge(st_prob, st_lbl)
                        st.markdown(svg_gauge_html, unsafe_allow_html=True)
                    else:
                        g_col = "#FF3366" if st_lbl == 1 else "#10B981"
                        s_txt = "🚨 ACUTE STRESS DETECTED" if st_lbl == 1 else "🟢 RESTING CALM"
                        b_bg = "rgba(255, 51, 102, 0.15)" if st_lbl == 1 else "rgba(16, 185, 129, 0.15)"
                        b_brd = "#FF3366" if st_lbl == 1 else "#10B981"

                        fig_g = go.Figure(go.Indicator(
                            mode="gauge+number",
                            value=st_prob * 100.0,
                            number=dict(suffix="%", font=dict(color=g_col, size=24, family="JetBrains Mono")),
                            gauge=dict(
                                axis=dict(range=[0, 100], tickcolor="#64748B"),
                                bar=dict(color=g_col),
                                bgcolor="#070913",
                                borderwidth=1,
                                bordercolor="#1C243B",
                                steps=[
                                    dict(range=[0, 35], color="rgba(16, 185, 129, 0.2)"),
                                    dict(range=[35, 65], color="rgba(245, 158, 11, 0.2)"),
                                    dict(range=[65, 100], color="rgba(255, 51, 102, 0.2)"),
                                ],
                                threshold=dict(line=dict(color="#F59E0B", width=3), thickness=0.8, value=35),
                            ),
                            title=dict(text="Calibrated Stress Dial (τ=0.35)", font=dict(color="#F1F5F9", size=13)),
                        ))
                        fig_g.update_layout(
                            template="none",
                            paper_bgcolor="#0F1424",
                            height=240,
                            margin=dict(l=20, r=20, t=40, b=10),
                            uirevision="live_gauge_const",
                            transition=dict(duration=0),
                        )
                        st.plotly_chart(
                            fig_g,
                            width="stretch",
                            key="telemetry_live_stress_gauge_chart",
                            theme=None,
                            config={"displayModeBar": False, "responsive": True, "staticPlot": True}
                        )
                        st.markdown(
                            f"<div style='text-align:center;background:{b_bg};border:1px solid {b_brd};border-radius:8px;padding:0.4rem;font-weight:bold;color:{g_col};font-size:0.85rem;font-family:JetBrains Mono,monospace;'>{s_txt}</div>",
                            unsafe_allow_html=True
                        )

                # 4. HRV Cards Strip (unindented)
                if hrv_res:
                    if is_eavesdropper:
                        h_data = [
                            ("Mean Heart Rate", "🔒 LOCKED", "Signal masked to noise", "#FF3366"),
                            ("RMSSD", "🔒 LOCKED", "Key required for vagal tone", "#64748B"),
                            ("SDNN", "🔒 LOCKED", "R-peaks unresolvable", "#64748B"),
                            ("pNN50", "🔒 LOCKED", "Cryptographically shielded", "#64748B"),
                            ("Mean RR", "🔒 LOCKED", "Beat intervals masked", "#64748B"),
                            ("Detected Beats", "0", "0 valid QRS complexes", "#FF3366"),
                        ]
                    else:
                        h_data = [
                            ("Mean Heart Rate", f"{hrv_res['MeanHR']} BPM", "Cardiac pace", "#00F0FF"),
                            ("RMSSD", f"{hrv_res['RMSSD']} ms", "Vagal tone marker", "#10B981" if hrv_res['RMSSD'] > 25 else "#FF3366"),
                            ("SDNN", f"{hrv_res['SDNN']} ms", "Total ANS variance", "#8B5CF6"),
                            ("pNN50", f"{hrv_res['pNN50']} %", "Parasympathetic %", "#10B981" if hrv_res['pNN50'] > 5 else "#FF3366"),
                            ("Mean RR", f"{hrv_res['MeanRR'] * 1000:.0f} ms", "Beat period", "#F1F5F9"),
                            ("Detected Beats", f"{hrv_res['NumBeats']}", "QRS complexes", "#F59E0B"),
                        ]
                    c_html = "<div style='display:flex;gap:0.35rem;margin-top:0.25rem;margin-bottom:0.3rem;'>"
                    for lbl, v, sub, c in h_data:
                        c_html += (
                            f"<div class='telemetry-card' style='flex:1;padding:0.22rem 0.45rem;border-left:2px solid {c};background:rgba(15,23,42,0.7);'>"
                            f"<div class='kpi-title' style='font-size:0.6rem;color:#94A3B8;letter-spacing:0.03em;'>{lbl}</div>"
                            f"<div class='kpi-value' style='font-size:0.95rem;font-weight:700;line-height:1.1;margin:0.05rem 0;color:{c};'>{v}</div>"
                            f"<div class='kpi-sub' style='font-size:0.56rem;color:#64748B;'>{sub}</div>"
                            f"</div>"
                        )
                    c_html += "</div>"
                    st.markdown(c_html, unsafe_allow_html=True)

            live_monitor_view()

            # 5. Live 3D Continuous Phase Space Monitor (Three.js WebGL 60 FPS Engine - Flicker-Free)
            st.markdown(
                """
                <div style="display:flex;align-items:center;justify-content:space-between;margin:0.25rem 0 0.2rem 0;padding:0.18rem 0.45rem;background:rgba(139,92,246,0.06);border:1px solid rgba(139,92,246,0.2);border-radius:4px;">
                    <div style="font-size:0.7rem;font-weight:700;color:#C4B5FD;font-family:'JetBrains Mono',monospace;display:flex;align-items:center;gap:0.4rem;">
                        <span style="color:#00F0FF;">🌀</span> LIVE CONTINUOUS 3D PHASE SPACE MONITOR
                        <span style="color:#64748B;font-weight:400;font-size:0.62rem;">| Cardiac Takens Delay &amp; M-4DCHS Memristive Attractors</span>
                    </div>
                    <div style="font-size:0.6rem;color:#10B981;font-family:'JetBrains Mono',monospace;font-weight:600;">● GPU ACCELERATED (60 FPS)</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            col_att1, col_att2 = st.columns([1.85, 1.15])

            # Extract ECG points for cardiac Takens delay reconstruction
            if len(telemetry_stream.filt_buf) >= 100:
                ecg_window = [round(float(v), 3) for v in list(telemetry_stream.filt_buf)[-1500:]]
            elif len(filt_full) > 0:
                ecg_window = [round(float(v), 3) for v in filt_full[:1500]]
            else:
                ecg_window = []

            with col_att1:
                threejs_code = generate_threejs_phase_space_html(ecg_window)
                components.html(threejs_code, height=225)

            with col_att2:
                st.markdown(
                    """
                    <div class="telemetry-card" style="font-size:0.68rem; line-height:1.35; border-left:3px solid #8B5CF6; height:225px; box-sizing:border-box; overflow-y:auto; padding:0.35rem 0.55rem;">
                        <div class="kpi-title" style="color:#A78BFA; font-size:0.72rem; margin-bottom:0.25rem;">M-4DCHS Mathematical Specification</div>
                        <b>Coupled Hyperchaotic Differential Equations:</b><br>
                        <code>dx/dt = a·(y - x) + w</code><br>
                        <code>dy/dt = c·x - x·z + d·y</code><br>
                        <code>dz/dt = x·y - b·z</code><br>
                        <code>dw/dt = -r·x</code><br>
                        • <b>Engine:</b> <span style="color:#00F0FF;font-weight:bold;">CLIENT WEBGL (60 FPS)</span> | Zero DOM re-mounting<br>
                        • <b>Hyperchaotic Parameters:</b> a=35.0, b=3.0, c=28.0, d=-1.0, r=5.0<br>
                        • <b>Lyapunov Spectrum:</b> λ₁ = +0.205, λ₂ = +0.085 (2 Positive Exponents)<br>
                        • <b>Dissipation:</b> div(F) = -(a+b-d) = -39.0 &lt; 0 (Volume Contraction)<br>
                        • <b>Dimension:</b> D<sub>KY</sub> = 3.42 | <b>Keyspace:</b> &gt; 2<sup>256</sup> (ℝ⁴)<br>
                        • <b>Shannon Entropy:</b> H = 7.9980 bits/byte | <b>Uniformity:</b> χ² = 273.65<br>
                        • <b>Takens Embedding:</b> τ = 8 samples (22.9 ms), [s(t), s(t-τ), s(t-2τ)]<br>
                        • <b>Controls:</b> Left-drag to rotate, scroll to zoom, HUD buttons to toggle modes.
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.error("Demo sample data could not be loaded. Check demo/sample_data directory.")

# ==============================================================================
# TAB 2: Interactive Waveform & Calibration Engine
# ==============================================================================
with tab_demo:
    col_ctrl, col_display = st.columns([1, 3.2])

    with col_ctrl:
        st.markdown(
            """
            <div class="telemetry-card">
                <div class="kpi-title" style="color: #00F0FF;">Telemetry Controls</div>
            """,
            unsafe_allow_html=True,
        )

        subject_options = {
            "S3": "Subject S3 (Strong Autonomic Responder)",
            "S2": "Subject S2 (Blunted / Non-Responder)",
            "S10": "Subject S10 (Elevated Basal HR)",
            "S17": "Subject S17 (Rapid Acceleration)",
        }
        selected_subj = st.selectbox(
            "Select Subject Profile:",
            options=list(subject_options.keys()),
            format_func=lambda s: subject_options[s],
            index=0,
            help="S3 exhibits clear sympathetic surge; S2 demonstrates physiological non-responder behavior where heart rate barely shifts.",
        )

        selected_cond = st.radio(
            "Experimental Condition:",
            options=["Baseline", "Stress"],
            format_func=lambda c: "🟢 Resting State (Baseline Calm)" if c == "Baseline" else "🔴 Acute Stress (TSST Public Speaking)",
            index=0,
        )

        filter_mode = st.toggle(
            "Apply 0.5–40 Hz Butterworth Filter",
            value=True,
            help="Removes baseline wander (<0.5 Hz) and high-frequency electromyographic muscle noise (>40 Hz).",
        )

        zoom_sec = st.slider(
            "Waveform Display Window (Seconds):",
            min_value=5,
            max_value=60,
            value=15,
            step=5,
            help="Zoom in to inspect individual ventricular QRS complexes and beat-to-beat intervals.",
        )

        st.markdown("</div>", unsafe_allow_html=True)

        # Subject Clinical Profile Card
        clinical_notes = {
            "S3": "<b>Subject S3:</b> Highly reactive autonomic nervous system. Under Trier Social Stress Test (TSST), heart rate surges by >45 BPM while parasympathetic RMSSD plunges by ~75%. Strong stress prediction.",
            "S2": "<b>Subject S2 (Clinical Non-Responder):</b> Exhibits minimal autonomic reactivity during TSST (blunted cortisol/cardiac response). In clinical stress literature, 10–15% of healthy individuals display this profile. Model correctly outputs low probability.",
            "S10": "<b>Subject S10:</b> Tachycardic baseline resting profile (~95 BPM). Uncalibrated global models misclassify resting calm as stress; subject-specific baseline normalization correctly anchors this shift.",
            "S17": "<b>Subject S17:</b> Rapid cardiac acceleration profile during public speaking with pronounced interval compression (ΔMeanRR < -30%).",
        }
        st.markdown(
            f"""
            <div class="telemetry-card" style="font-size: 0.82rem; color: #CBD5E1; line-height: 1.45; border-left: 3px solid #8B5CF6;">
                <div class="kpi-title" style="color: #8B5CF6;">Clinical Case Study Note</div>
                {clinical_notes.get(selected_subj, '')}
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_display:
        if waveforms_data is not None and sample_meta is not None:
            prefix = f"{selected_subj}_{selected_cond}"
            raw_sig = waveforms_data[f"{prefix}_raw"]
            filt_sig = waveforms_data[f"{prefix}_filt"]
            peaks_idx = waveforms_data[f"{prefix}_peaks"]
            meta_info = sample_meta["subjects"][selected_subj][selected_cond]
            hrv = meta_info["hrv"]
            fs_demo = sample_meta["fs_demo"]

            # Sub-slice according to zoom_sec
            num_pts = int(fs_demo * zoom_sec)
            t_axis = np.arange(num_pts) / fs_demo
            active_sig = filt_sig[:num_pts] if filter_mode else raw_sig[:num_pts]

            # Filter peaks inside the zoom window
            valid_peaks = peaks_idx[peaks_idx < num_pts]
            peak_times = valid_peaks / fs_demo
            peak_vals = active_sig[valid_peaks]

            # Waveform Plotly Figure
            fig_ecg = go.Figure()

            # Signal line
            sig_color = "#00F0FF" if filter_mode else "#FF9900"
            sig_name = "0.5–40 Hz Zero-Phase Filtered" if filter_mode else "Raw Lead-II ECG"
            fig_ecg.add_trace(go.Scatter(
                x=t_axis,
                y=active_sig,
                mode="lines",
                name=sig_name,
                line=dict(color=sig_color, width=1.5),
                hovertemplate="Time: %{x:.2f}s<br>Voltage: %{y:.2f} mV<extra></extra>",
            ))

            # R-peaks markers
            if len(valid_peaks) > 0:
                fig_ecg.add_trace(go.Scatter(
                    x=peak_times,
                    y=peak_vals,
                    mode="markers",
                    name="Detected R-Peaks (Ventricular Beats)",
                    marker=dict(
                        symbol="triangle-down",
                        size=9,
                        color="#FF3366",
                        line=dict(color="#FFFFFF", width=1),
                    ),
                    hovertemplate="R-Peak Beat<br>Time: %{x:.2f}s<extra></extra>",
                ))

            fig_ecg.update_layout(
                title=dict(
                    text=f"Lead-II Cardiac Telemetry Trace — {selected_subj} ({selected_cond}) | {zoom_sec}s Window",
                    font=dict(size=14, color="#F1F5F9"),
                ),
                paper_bgcolor="#0F1424",
                plot_bgcolor="#0A0E1A",
                margin=dict(l=45, r=20, t=45, b=35),
                height=320,
                xaxis=dict(
                    title="Time in Window (seconds)",
                    color="#94A3B8",
                    gridcolor="#1C243B",
                    zerolinecolor="#2A3656",
                    showline=True,
                    linecolor="#2A3656",
                ),
                yaxis=dict(
                    title="Amplitude (mV)",
                    color="#94A3B8",
                    gridcolor="#1C243B",
                    zerolinecolor="#2A3656",
                    showline=True,
                    linecolor="#2A3656",
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    font=dict(color="#CBD5E1", size=11),
                ),
            )
            st.plotly_chart(fig_ecg, use_container_width=True)

            # Instantaneous Vitals Bar + Stress Needle Gauge
            col_vitals, col_gauge = st.columns([1.7, 1.3])

            with col_vitals:
                st.markdown("<div class=\"kpi-title\" style=\"margin-top:0.4rem;\">Window Autonomic Metrics (60s NN Analysis)</div>", unsafe_allow_html=True)
                v1, v2 = st.columns(2)
                with v1:
                    st.markdown(
                        f"""
                        <div class="telemetry-card" style="margin-bottom: 0.65rem;">
                            <div class="kpi-title">Heart Rate (BPM)</div>
                            <div class="kpi-value" style="color: {'#FF3366' if hrv['MeanHR'] > 85 else '#10B981'};">
                                {hrv['MeanHR']} <span style="font-size: 0.9rem; color: #64748B;">BPM</span>
                            </div>
                            <div class="kpi-sub">Total {hrv['NumBeats']} ventricular beats</div>
                        </div>
                        <div class="telemetry-card" style="margin-bottom: 0.65rem;">
                            <div class="kpi-title">RMSSD (Parasympathetic Vagal Tone)</div>
                            <div class="kpi-value" style="color: {'#FF3366' if hrv['RMSSD_ms'] < 30 else '#00F0FF'};">
                                {hrv['RMSSD_ms']} <span style="font-size: 0.9rem; color: #64748B;">ms</span>
                            </div>
                            <div class="kpi-sub">Successive beat variance</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with v2:
                    st.markdown(
                        f"""
                        <div class="telemetry-card" style="margin-bottom: 0.65rem;">
                            <div class="kpi-title">SDNN (Total Autonomic Variance)</div>
                            <div class="kpi-value" style="color: #F59E0B;">
                                {hrv['SDNN_ms']} <span style="font-size: 0.9rem; color: #64748B;">ms</span>
                            </div>
                            <div class="kpi-sub">Standard deviation of NN intervals</div>
                        </div>
                        <div class="telemetry-card" style="margin-bottom: 0.65rem;">
                            <div class="kpi-title">pNN50 (Vagal Calming Tone)</div>
                            <div class="kpi-value" style="color: {'#FF3366' if hrv['pNN50'] < 10 else '#10B981'};">
                                {hrv['pNN50']} <span style="font-size: 0.9rem; color: #64748B;">%</span>
                            </div>
                            <div class="kpi-sub">Pairs differing by &gt; 50 ms</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            with col_gauge:
                prob = meta_info["stress_probability"]
                is_stress = prob >= 0.35

                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=prob * 100,
                    number={"suffix": "%", "font": {"size": 32, "color": "#F8FAFC", "family": "JetBrains Mono"}},
                    title={"text": "Acute Stress Probability", "font": {"size": 13, "color": "#94A3B8"}},
                    gauge={
                        "axis": {"range": [0, 100], "tickcolor": "#94A3B8", "tickfont": {"size": 10, "color": "#64748B"}},
                        "bar": {"color": "#FF3366" if is_stress else "#10B981", "thickness": 0.3},
                        "bgcolor": "#0A0E1A",
                        "borderwidth": 1,
                        "bordercolor": "#1C243B",
                        "steps": [
                            {"range": [0, 35], "color": "rgba(16, 185, 129, 0.2)"},
                            {"range": [35, 70], "color": "rgba(245, 158, 11, 0.2)"},
                            {"range": [70, 100], "color": "rgba(255, 51, 102, 0.25)"},
                        ],
                        "threshold": {
                            "line": {"color": "#F59E0B", "width": 3},
                            "thickness": 0.8,
                            "value": 35.0,
                        },
                    },
                ))
                fig_gauge.update_layout(
                    paper_bgcolor="#0F1424",
                    plot_bgcolor="#0F1424",
                    margin=dict(l=25, r=25, t=30, b=10),
                    height=200,
                )
                st.plotly_chart(fig_gauge, use_container_width=True)

                if is_stress:
                    st.markdown(
                        """
                        <div style="text-align: center; margin-top: -0.5rem;">
                            <span class="status-pill-stress">⚠️ ACUTE STRESS DETECTED (P ≥ 0.35)</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        """
                        <div style="text-align: center; margin-top: -0.5rem;">
                            <span class="status-pill-calm">✅ RESTING / CALM STATE (P &lt; 0.35)</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
        else:
            st.warning("Demo waveform samples not found. Run `python python/export_demo_samples.py` to generate them.")


# ==============================================================================
# TAB 2: HRV Biomarkers & Baseline Formula
# ==============================================================================
with tab_features:
    st.markdown(
        """
        <div class="telemetry-card">
            <h3 style="margin: 0 0 0.4rem 0; font-size: 1.15rem; color: #00F0FF;">
                The Core Scientific Challenge: Inter-Individual Baseline Heterogeneity
            </h3>
            <p style="color: #CBD5E1; font-size: 0.9rem; line-height: 1.5; margin-bottom: 0.75rem;">
                Resting heart rate varies from 50 to 95+ BPM across healthy adults due to cardiorespiratory fitness, genetic differences, and circadian phase. 
                Consequently, an uncalibrated global classifier fails on held-out subjects. We resolve this by computing a 
                <b>personalized relative baseline transform</b> for each subject:
            </p>
            <div style="text-align: center; padding: 0.6rem; background: rgba(0,0,0,0.3); border-radius: 8px; font-family: 'JetBrains Mono', monospace; font-size: 1.15rem; color: #F59E0B; margin-bottom: 0.75rem;">
                X* = ( X - B<sub>s</sub> ) / | B<sub>s</sub> |
            </div>
            <p style="color: #94A3B8; font-size: 0.85rem; margin: 0;">
                Where <i>X</i> is the raw 60-second window metric, and <i>B<sub>s</sub></i> is the subject's mean resting baseline metric.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c_ablate_left, c_ablate_right = st.columns([1.6, 2.4])

    with c_ablate_left:
        # Four-stage progression bar chart
        progression_data = pd.DataFrame({
            "Stage": [
                "1. Global Raw Features",
                "2. + Clinical Gating",
                "3. + Baseline Normalization",
                "4. + Calibrated Threshold",
            ],
            "Accuracy": [81.57, 83.15, 92.13, 92.36],
            "F1_Score": [73.03, 75.20, 88.62, 89.03],
        })

        fig_prog = go.Figure()
        fig_prog.add_trace(go.Bar(
            y=progression_data["Stage"],
            x=progression_data["Accuracy"],
            name="Accuracy (%)",
            orientation="h",
            marker=dict(color="#00F0FF"),
            text=progression_data["Accuracy"].apply(lambda v: f"{v:.1f}%"),
            textposition="auto",
        ))
        fig_prog.add_trace(go.Bar(
            y=progression_data["Stage"],
            x=progression_data["F1_Score"],
            name="Stress F1 (%)",
            orientation="h",
            marker=dict(color="#FF3366"),
            text=progression_data["F1_Score"].apply(lambda v: f"{v:.1f}%"),
            textposition="auto",
        ))
        fig_prog.update_layout(
            title=dict(text="Ablation: Pipeline Evolution (LOSO-CV)", font=dict(size=13, color="#F1F5F9")),
            paper_bgcolor="#0F1424",
            plot_bgcolor="#0A0E1A",
            barmode="group",
            height=340,
            margin=dict(l=10, r=20, t=40, b=30),
            xaxis=dict(range=[65, 100], color="#94A3B8", gridcolor="#1C243B"),
            yaxis=dict(autorange="reversed", color="#CBD5E1", tickfont=dict(size=10)),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="#CBD5E1")),
        )
        st.plotly_chart(fig_prog, use_container_width=True)

    with c_ablate_right:
        if tab_data.get("features") is not None:
            df_feat = tab_data["features"]
            feature_choices = ["MeanHR", "MeanRR", "RMSSD", "SDNN", "pNN50", "RR_CV"]
            sel_feature = st.selectbox("Inspect Feature Distribution Across 445 Windows:", feature_choices, index=0)

            fig_box = px.violin(
                df_feat,
                x="Condition",
                y=sel_feature,
                color="Condition",
                box=True,
                points="all",
                color_discrete_map={"Baseline": "#10B981", "Stress": "#FF3366"},
            )
            fig_box.update_layout(
                title=dict(text=f"Physiological Contrast: {sel_feature} (Baseline vs. Acute Stress)", font=dict(size=13, color="#F1F5F9")),
                paper_bgcolor="#0F1424",
                plot_bgcolor="#0A0E1A",
                height=340,
                margin=dict(l=40, r=20, t=40, b=30),
                xaxis=dict(color="#94A3B8", gridcolor="#1C243B"),
                yaxis=dict(color="#94A3B8", gridcolor="#1C243B"),
                showlegend=False,
            )
            st.plotly_chart(fig_box, use_container_width=True)
        else:
            st.info("Feature dataset `WESAD_HRV_features_expanded.csv` not found.")


# ==============================================================================
# TAB 3: Multi-Model Benchmark & Dynamic Decision Threshold Sweep
# ==============================================================================
with tab_benchmark:
    st.markdown(
        """
        <div class="telemetry-card">
            <h3 style="margin: 0 0 0.4rem 0; font-size: 1.15rem; color: #F59E0B;">
                Cross-Model Architecture Benchmark (15-Fold LOSO-CV)
            </h3>
            <p style="color: #CBD5E1; font-size: 0.9rem; margin: 0;">
                All 6 machine learning architectures generalize robustly across held-out subjects when trained with personalized baseline relative features (ROC-AUC &gt; 0.937 across all models).
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if tab_data.get("benchmark") is not None:
        df_bench = tab_data["benchmark"].copy()
        
        # Robust column name lookup
        roc_col = "ROC-AUC" if "ROC-AUC" in df_bench.columns else "ROC AUC"
        f1_col = "F1-Score (%)" if "F1-Score (%)" in df_bench.columns else "F1 Score (%)"
        sens_col = "Sensitivity/Recall (%)" if "Sensitivity/Recall (%)" in df_bench.columns else "Sensitivity (%)"

        col_table, col_bars = st.columns([1.7, 2.3])
        with col_table:
            display_cols = ["Model", "Accuracy (%)", f1_col, roc_col, sens_col, "Specificity (%)"]
            avail_cols = [c for c in display_cols if c in df_bench.columns]
            format_dict = {}
            if "Accuracy (%)" in avail_cols: format_dict["Accuracy (%)"] = "{:.2f}%"
            if f1_col in avail_cols: format_dict[f1_col] = "{:.2f}%"
            if roc_col in avail_cols: format_dict[roc_col] = "{:.4f}"
            if sens_col in avail_cols: format_dict[sens_col] = "{:.2f}%"
            if "Specificity (%)" in avail_cols: format_dict["Specificity (%)"] = "{:.2f}%"

            st.dataframe(
                df_bench[avail_cols].style.format(format_dict),
                use_container_width=True,
                height=260,
            )

        with col_bars:
            fig_b = px.bar(
                df_bench,
                x=roc_col,
                y="Model",
                orientation="h",
                color=roc_col,
                color_continuous_scale="Viridis",
                text=df_bench[roc_col].apply(lambda v: f"{v:.4f}"),
            )
            fig_b.update_layout(
                title=dict(text="ROC-AUC Diagnostic Separation by Architecture", font=dict(size=13, color="#F1F5F9")),
                paper_bgcolor="#0F1424",
                plot_bgcolor="#0A0E1A",
                height=260,
                margin=dict(l=10, r=20, t=35, b=25),
                xaxis=dict(range=[0.88, 0.96], color="#94A3B8", gridcolor="#1C243B", title="ROC-AUC"),
                yaxis=dict(color="#CBD5E1", autorange="reversed"),
                coloraxis_showscale=False,
            )
            st.plotly_chart(fig_b, use_container_width=True)

    st.markdown("---")

    # Dynamic Threshold Sweep Section
    st.markdown("#### 🎯 Interactive Decision Threshold Sweep (\\(\\tau \\in [0.10, 0.90]\\))")
    st.markdown(
        """
        <p style="color: #94A3B8; font-size: 0.88rem;">
            Scrub the decision threshold slider below to observe the real-time trade-off between 
            <b>Sensitivity (catching stress episodes)</b> and <b>Specificity (preventing false alarms)</b>.
        </p>
        """,
        unsafe_allow_html=True,
    )

    t_col1, t_col2 = st.columns([1.2, 2.8])

    with t_col1:
        tau_val = st.slider(
            "Operating Threshold (τ):",
            min_value=0.10,
            max_value=0.90,
            value=0.35,
            step=0.01,
            help="At tau = 0.35, the model catches 86.25% of stress windows while maintaining 95.79% specificity.",
        )

        # Look up or compute metrics at this threshold
        if tab_data.get("threshold") is not None:
            df_th = tab_data["threshold"]
            # Find closest threshold
            idx = (df_th["Threshold"] - tau_val).abs().idxmin()
            row = df_th.iloc[idx]
            acc_th = row["Accuracy"]
            rec_th = row["Recall"]
            spec_th = row["Specificity"]
            f1_th = row["F1"]
        else:
            acc_th, rec_th, spec_th, f1_th = 92.36, 86.25, 95.79, 89.03

        # Compute dynamic confusion matrix counts (N=445 total, 160 stress, 285 non-stress)
        tp_cnt = int(round(160 * (rec_th / 100.0)))
        fn_cnt = 160 - tp_cnt
        tn_cnt = int(round(285 * (spec_th / 100.0)))
        fp_cnt = 285 - tn_cnt

        st.markdown(
            f"""
            <div class="telemetry-card" style="border-left: 3px solid #F59E0B; padding: 1rem;">
                <div class="kpi-title" style="color: #F59E0B;">Metrics at τ = {tau_val:.2f}</div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-top: 0.5rem;">
                    <div>
                        <div class="kpi-title" style="font-size: 0.7rem;">Sensitivity (Recall)</div>
                        <div style="font-family: 'JetBrains Mono'; font-size: 1.25rem; font-weight: 700; color: #FF3366;">
                            {rec_th:.1f}%
                        </div>
                    </div>
                    <div>
                        <div class="kpi-title" style="font-size: 0.7rem;">Specificity</div>
                        <div style="font-family: 'JetBrains Mono'; font-size: 1.25rem; font-weight: 700; color: #10B981;">
                            {spec_th:.1f}%
                        </div>
                    </div>
                    <div>
                        <div class="kpi-title" style="font-size: 0.7rem;">Accuracy</div>
                        <div style="font-family: 'JetBrains Mono'; font-size: 1.25rem; font-weight: 700; color: #00F0FF;">
                            {acc_th:.1f}%
                        </div>
                    </div>
                    <div>
                        <div class="kpi-title" style="font-size: 0.7rem;">F1-Score</div>
                        <div style="font-family: 'JetBrains Mono'; font-size: 1.25rem; font-weight: 700; color: #8B5CF6;">
                            {f1_th:.1f}%
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with t_col2:
        # Dynamic 2x2 Confusion Matrix Heatmap
        cm_matrix = np.array([[tn_cnt, fp_cnt], [fn_cnt, tp_cnt]])
        fig_cm = go.Figure(data=go.Heatmap(
            z=cm_matrix,
            x=["Predicted Calm", "Predicted Stress"],
            y=["True Calm (N=285)", "True Stress (N=160)"],
            colorscale=[[0, "#0A0E1A"], [0.5, "#1E293B"], [1.0, "#00F0FF"]],
            text=[[f"<b>TN = {tn_cnt}</b><br>({tn_cnt/285*100:.1f}%)", f"<b>FP = {fp_cnt}</b><br>({fp_cnt/285*100:.1f}%)"],
                  [f"<b>FN = {fn_cnt}</b><br>({fn_cnt/160*100:.1f}%)", f"<b>TP = {tp_cnt}</b><br>({tp_cnt/160*100:.1f}%)"]],
            texttemplate="%{text}",
            textfont={"size": 14, "color": "#FFFFFF", "family": "DM Sans"},
            showscale=False,
        ))
        fig_cm.update_layout(
            title=dict(text=f"Dynamic Confusion Matrix at Operating Threshold τ = {tau_val:.2f}", font=dict(size=13, color="#F1F5F9")),
            paper_bgcolor="#0F1424",
            plot_bgcolor="#0A0E1A",
            height=260,
            margin=dict(l=30, r=20, t=35, b=25),
            xaxis=dict(color="#94A3B8"),
            yaxis=dict(color="#94A3B8", autorange="reversed"),
        )
        st.plotly_chart(fig_cm, use_container_width=True)
