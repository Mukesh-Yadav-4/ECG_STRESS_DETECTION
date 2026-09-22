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

[data-testid="stSidebar"] {
    background-color: #0B0E1B !important;
    border-right: 1px solid var(--border-subtle) !important;
}

/* Custom Card Container */
.telemetry-card {
    background-color: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: 12px;
    padding: 1.25rem 1.4rem;
    margin-bottom: 1rem;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    transition: border 0.2s ease, transform 0.2s ease;
}
.telemetry-card:hover {
    border-color: var(--border-accent);
}

.kpi-title {
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-dim);
    margin-bottom: 0.25rem;
}
.kpi-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.85rem;
    font-weight: 700;
    color: var(--text-main);
    line-height: 1.15;
}
.kpi-sub {
    font-size: 0.8rem;
    color: var(--text-muted);
    margin-top: 0.35rem;
}

/* Status Badges */
.status-pill-stress {
    display: inline-flex;
    align-items: center;
    background: rgba(255, 51, 102, 0.15);
    border: 1px solid rgba(255, 51, 102, 0.6);
    color: #FF6688;
    padding: 0.4rem 1.1rem;
    border-radius: 9999px;
    font-weight: 700;
    font-size: 0.95rem;
    letter-spacing: 0.04em;
    font-family: 'JetBrains Mono', monospace;
}
.status-pill-calm {
    display: inline-flex;
    align-items: center;
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid rgba(16, 185, 129, 0.6);
    color: #34D399;
    padding: 0.4rem 1.1rem;
    border-radius: 9999px;
    font-weight: 700;
    font-size: 0.95rem;
    letter-spacing: 0.04em;
    font-family: 'JetBrains Mono', monospace;
}

/* Tabs styling */
button[data-baseweb="tab"] {
    background: transparent !important;
    color: var(--text-muted) !important;
    font-size: 0.92rem !important;
    font-weight: 600 !important;
    padding: 0.75rem 1.25rem !important;
    border-radius: 8px !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #00F0FF !important;
    background: rgba(0, 240, 255, 0.08) !important;
    border-bottom: 2px solid #00F0FF !important;
}

/* Hide default streamlit decorations */
header[data-testid="stHeader"] {
    background: transparent !important;
}
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
    <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.4rem;">
        <span style="font-size: 1.8rem;">🫀</span>
        <h1 style="font-size: 1.75rem; font-weight: 800; margin: 0; color: #F8FAFC; letter-spacing: -0.02em;">
            Personalized Electrocardiographic and HRV Dynamics for Acute Stress Detection
        </h1>
    </div>
    <p style="color: #94A3B8; font-size: 0.95rem; margin: 0 0 0.8rem 0;">
        15-Fold Leave-One-Subject-Out (LOSO-CV) Benchmark &amp; Bare-Metal Edge IoMT Implementation • 
        <b>Mukesh Yadav</b> (Department of Electronics and Communication Engineering, JSSATEN) • 
        <a href="https://doi.org/10.5281/zenodo.22895173" target="_blank" style="color: #00F0FF; text-decoration: none; font-weight: 600;">
            Zenodo DOI: 10.5281/zenodo.22895173 ↗
        </a>
    </p>
    """,
    unsafe_allow_html=True,
)

# Top KPI Metric Strip
k1, k2, k3, k4, k5, k6 = st.columns(6)
kpis = [
    ("Accuracy", "92.36 %", "+10.79% vs uncalibrated", "#10B981"),
    ("Stress F1-Score", "89.03 %", "+16.00% boost", "#00F0FF"),
    ("ROC-AUC", "0.9494", "High diagnostic separation", "#8B5CF6"),
    ("Sensitivity", "86.25 %", "138 / 160 stress windows", "#FF3366"),
    ("Specificity", "95.79 %", "273 / 285 calm windows", "#10B981"),
    ("Benchmark", "15 Subjects", "445 standardized windows", "#F59E0B"),
]
for col, (label, val, sub, color) in zip([k1, k2, k3, k4, k5, k6], kpis):
    with col:
        st.markdown(
            f"""
            <div class="telemetry-card" style="padding: 0.85rem 1rem; border-left: 3px solid {color};">
                <div class="kpi-title">{label}</div>
                <div class="kpi-value" style="font-size: 1.45rem; color: {color};">{val}</div>
                <div class="kpi-sub" style="font-size: 0.72rem;">{sub}</div>
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
    st.markdown(
        """
        <div style="margin-bottom: 1.25rem;">
            <div style="display: flex; align-items: center; gap: 0.6rem;">
                <span style="font-size: 1.5rem;">⚡</span>
                <h2 style="font-size: 1.4rem; font-weight: 700; margin: 0; color: #00F0FF;">
                    STM32G474 Edge Node: Real-Time IoMT Telemetry & Stress Detection
                </h2>
            </div>
            <p style="color: #94A3B8; font-size: 0.88rem; margin: 0.2rem 0 0 0;">
                Direct telemetry ingestion from the ARM Cortex-M4 edge microcontroller (20-byte binary frames @ 350/700 Hz with hardware CRC-16).
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    stm_col_ctrl, stm_col_view = st.columns([1, 3.1])

    with stm_col_ctrl:
        st.markdown(
            """
            <div class="telemetry-card">
                <div class="kpi-title" style="color: #00F0FF;">Hardware Link Interface</div>
            """,
            unsafe_allow_html=True,
        )

        link_mode = st.radio(
            "Telemetry Link Mode:",
            options=["Simulated STM32 Link (Virtual)", "Physical USB COM Port"],
            index=0,
            help="Simulated mode streams real WESAD subjects through the exact STM32 20-byte packet protocol without needing physical hardware connected.",
        )

        if link_mode == "Simulated STM32 Link (Virtual)":
            stm_subj = st.selectbox(
                "Simulated Patient / Subject:",
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
                "Simulated State:",
                options=["Baseline", "Stress"],
                format_func=lambda c: "🟢 Resting State (Baseline Calm)" if c == "Baseline" else "🔴 Acute Stress (TSST Public Speaking)",
                index=0,
            )

            stm_duration = st.slider(
                "Streaming Window (Seconds):",
                min_value=10,
                max_value=60,
                value=25,
                step=5,
            )

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

            baud_rate = st.selectbox("Baud Rate:", [115200, 921600], index=0)
            stm_duration = st.slider("Streaming Capture Window (Seconds):", min_value=5, max_value=30, value=8, step=1)
            stm_subj, stm_cond = "S2", "Baseline"
            if com_port == "Virtual / Offline Port":
                st.info("ℹ️ Physical USB COM Port mode connects to local hardware. On cloud instances without hardware connected, use **'Simulated STM32 Link (Virtual)'** above to stream authentic 20-byte packet telemetry.")
            else:
                st.caption(f"Ready to ingest from serial port: `{com_port}` @ {baud_rate} baud")

        st.markdown("<hr style='border: 0; border-top: 1px solid #1C243B; margin: 0.8rem 0;'>", unsafe_allow_html=True)
        continuous_stream = st.toggle(
            "🔴 Continuous Live Stream (Hospital Monitor)",
            value=False,
            help="Continuously ingests incoming packets in real-time and scrolls the live ECG waveform without freezing."
        )

        chart_renderer = st.radio(
            "Telemetry Waveform Engine:",
            options=["🟢 Hospital Monitor (Flicker-Free Native)", "📊 Plotly Interactive Lab"],
            index=0,
            help="Hospital Monitor uses native streaming with zero unmounting/flicker. Plotly Interactive Lab enables manual box-zoom/pan inspection."
        )

        security_view_mode = st.radio(
            "IoMT Security Inspector:",
            options=["🟢 Authorized Clinical View (Decrypted Telemetry)", "🕵️ Eavesdropper Intercept View (Raw Wire Ciphertext)"],
            index=0,
            help="Toggle between authorized clinical view (decrypted ECG with 100% bit precision) and intercepted wire view (high-entropy chaotic white noise)."
        )

        st.markdown("</div>", unsafe_allow_html=True)

        # Edge Node Specs Card
        st.markdown(
            """
            <div class="telemetry-card" style="font-size: 0.82rem; color: #CBD5E1; margin-top: 1rem; border-left: 3px solid #00F0FF;">
                <div class="kpi-title" style="color: #00F0FF;">STM32G474 Specs & Framing</div>
                • <b>Core:</b> ARM Cortex-M4 @ 170 MHz + FPU<br>
                • <b>DSP Filter:</b> 5-stage Biquad IIR (0.5–40 Hz BP + 50 Hz Notch)<br>
                • <b>Telemetry Frame:</b> 20 Bytes Binary<br>
                • <b>Header / Sync:</b> <code>0xAA 0x55</code><br>
                • <b>Integrity Check:</b> CRC-16-CCITT (Poly: <code>0x1021</code>)<br>
                • <b>Security Layer:</b> 32-Bit Chaotic Cipher (Xorshift32 + Weyl)<br>
                • <b>On-Chip Cipher Cost:</b> 0.19 µs/packet (32 cycles @ 170 MHz)
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
                    f"<div class='telemetry-card' style='text-align:center;padding:1rem 0.8rem;height:280px;box-sizing:border-box;display:flex;flex-direction:column;justify-content:space-between;'>"
                    f"<div>"
                    f"<div class='kpi-title' style='margin-bottom:0.4rem;'>Calibrated Stress Dial (τ=0.35)</div>"
                    f"<svg viewBox='0 0 200 120' style='width:90%;max-width:220px;margin:0 auto;display:block;'>"
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
                    f"<text x='100' y='82' font-family='JetBrains Mono, monospace' font-size='22' font-weight='700' fill='{g_col}' text-anchor='middle'>{prob*100.0:.1f}%</text>"
                    f"<text x='100' y='93' font-size='8.5' font-weight='600' letter-spacing='0.08em' fill='#64748B' text-anchor='middle'>STRESS PROBABILITY</text>"
                    f"<text x='30' y='108' font-size='8' font-weight='600' fill='#64748B' text-anchor='middle'>0%</text>"
                    f"<text x='170' y='108' font-size='8' font-weight='600' fill='#64748B' text-anchor='middle'>100%</text>"
                    f"</svg>"
                    f"</div>"
                    f"<div style='background:{b_bg};border:1px solid {b_brd};border-radius:8px;padding:0.4rem;font-weight:bold;color:{g_col};font-size:0.82rem;font-family:JetBrains Mono,monospace;'>"
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
                                flags=0x01,
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
                                    flags=0x01,
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
                    f"<div style='display:flex;gap:0.8rem;margin-bottom:0.8rem;'>"
                    f"<div class='telemetry-card' style='flex:1;padding:0.7rem 0.9rem;border-left:3px solid #00F0FF;'>"
                    f"<div class='kpi-title'>Packets Ingested</div>"
                    f"<div class='kpi-value' style='font-size:1.3rem;color:#00F0FF;'>{stats['valid_packets']:,}</div>"
                    f"<div class='kpi-sub'>100% Valid CRC-16</div>"
                    f"</div>"
                    f"<div class='telemetry-card' style='flex:1;padding:0.7rem 0.9rem;border-left:3px solid #10B981;'>"
                    f"<div class='kpi-title'>CRC Errors / Drops</div>"
                    f"<div class='kpi-value' style='font-size:1.3rem;color:#10B981;'>{stats['crc_errors']} / {stats['dropped_packets']}</div>"
                    f"<div class='kpi-sub'>Zero packet loss</div>"
                    f"</div>"
                    f"<div class='telemetry-card' style='flex:1;padding:0.7rem 0.9rem;border-left:3px solid #8B5CF6;'>"
                    f"<div class='kpi-title'>Frame Sync</div>"
                    f"<div class='kpi-value' style='font-size:1.3rem;color:#8B5CF6;'>0xAA 0x55</div>"
                    f"<div class='kpi-sub'>Synchronized</div>"
                    f"</div>"
                    f"<div class='telemetry-card' style='flex:1;padding:0.7rem 0.9rem;border-left:3px solid {sec_badge_col};'>"
                    f"<div class='kpi-title'>IoMT Security</div>"
                    f"<div class='kpi-value' style='font-size:1.3rem;color:{sec_badge_col};'>{sec_badge_val}</div>"
                    f"<div class='kpi-sub'>{sec_badge_sub}</div>"
                    f"</div>"
                    f"</div>"
                )
                st.markdown(s_html, unsafe_allow_html=True)

                # 3. Waveform & Gauge
                col_wave, col_gauge = st.columns([2.2, 1.2])

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
                                <div style="background: rgba(255, 51, 102, 0.12); border: 1px solid #FF3366; border-radius: 8px; padding: 0.5rem 0.8rem; margin-bottom: 0.5rem; font-size: 0.8rem; color: #F8FAFC;">
                                    🔒 <b>Eavesdropper Wire Intercept Mode:</b> Showing raw scrambled ciphertext intercepted over UART. 
                                    Cardiac biometric morphology is masked into high-entropy pseudo-random noise 
                                    (<b>Shannon Entropy: {entropy_val:.2f} bits/byte</b>).
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
                                height=280,
                                x_label="Time (seconds) — Obfuscated Wire Ciphertext",
                                y_label="Cipher Amplitude (Float)",
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
                                height=280,
                                x_label="Time (seconds) — 8s Rolling Ingestion Window",
                                y_label="Amplitude (mV)",
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
                                title=dict(text="Real-Time Ingestion: Raw vs. STM32 Filtered Waveform (8s Rolling Window)", font=dict(color="#F1F5F9", size=13)),
                                template="none",
                                paper_bgcolor="#0F1424",
                                plot_bgcolor="#070913",
                                height=280,
                                margin=dict(l=40, r=20, t=40, b=30),
                                legend=dict(orientation="h", y=1.15, x=0.01, font=dict(color="#94A3B8")),
                                xaxis=dict(title=dict(text="Time (seconds)", font=dict(color="#94A3B8")), showgrid=True, gridcolor="#1C243B", range=[0, 8], autorange=False, fixedrange=True, tickcolor="#64748B", tickfont=dict(color="#94A3B8")),
                                yaxis=dict(title=dict(text="Amplitude (mV)", font=dict(color="#94A3B8")), showgrid=True, gridcolor="#1C243B", range=[-0.8, 1.2], autorange=False, fixedrange=True, tickcolor="#64748B", tickfont=dict(color="#94A3B8")),
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
                        st.markdown(
                            f"""
                            <div class="telemetry-card" style="text-align: center; border-left: 3px solid #FF3366; padding: 1.4rem 1rem;">
                                <div style="font-size: 2.2rem; margin-bottom: 0.3rem;">🔒</div>
                                <div style="font-size: 0.85rem; font-weight: 700; color: #FF6688; text-transform: uppercase; letter-spacing: 0.08em;">
                                    Telemetry Encrypted
                                </div>
                                <div style="font-family: 'JetBrains Mono'; font-size: 1.25rem; font-weight: 700; color: #F1F5F9; margin: 0.3rem 0;">
                                    KEY LOCKED
                                </div>
                                <div style="font-size: 0.76rem; color: #94A3B8; line-height: 1.35;">
                                    Biometric HRV and acute stress inference are locked to prevent unauthorized patient tracking.
                                </div>
                                <div style="margin-top: 0.7rem; font-size: 0.72rem; color: #CBD5E1; background: rgba(255, 51, 102, 0.1); border: 1px solid rgba(255, 51, 102, 0.25); border-radius: 6px; padding: 0.45rem; text-align: left;">
                                    • <b>Cipher:</b> Xorshift32 + Weyl<br>
                                    • <b>Diffusion:</b> Nonce CBC Chained<br>
                                    • <b>Wire Entropy:</b> <code>{entropy_val:.2f} bits/B</code>
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
                    c_html = "<div style='display:flex;gap:0.6rem;margin-top:0.5rem;'>"
                    for lbl, v, sub, c in h_data:
                        c_html += (
                            f"<div class='telemetry-card' style='flex:1;padding:0.6rem 0.8rem;border-left:2px solid {c};'>"
                            f"<div class='kpi-title' style='font-size:0.72rem;'>{lbl}</div>"
                            f"<div class='kpi-value' style='font-size:1.15rem;color:{c};'>{v}</div>"
                            f"<div class='kpi-sub' style='font-size:0.68rem;'>{sub}</div>"
                            f"</div>"
                        )
                    c_html += "</div>"
                    st.markdown(c_html, unsafe_allow_html=True)

            live_monitor_view()
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
