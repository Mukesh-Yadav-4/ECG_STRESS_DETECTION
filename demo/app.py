"""
WESAD ECG Stress Detection - Interactive Clinical Telemetry & Benchmark Dashboard
Author: Mukesh Yadav (Department of ECE, JSS Academy of Technical Education, Noida)
Publication: Zenodo (CERN) DOI: 10.5281/zenodo.22806710
Repository: https://github.com/Mukesh-Yadav-4/ECG_STRESS_DETECTION
"""

import os
import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

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
PAPER_PDF_PATH = os.path.join(PROJECT_ROOT, "paper", "ECG_Stress_Detection_WESAD_Benchmark_Paper.pdf")


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
col_head_left, col_head_right = st.columns([3.2, 1.3])

with col_head_left:
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.4rem;">
            <span style="font-size: 1.8rem;">🫀</span>
            <h1 style="font-size: 1.75rem; font-weight: 800; margin: 0; color: #F8FAFC; letter-spacing: -0.02em;">
                Personalized ECG & HRV Dynamics for Acute Stress Detection
            </h1>
        </div>
        <p style="color: #94A3B8; font-size: 0.95rem; margin: 0 0 0.8rem 0;">
            15-Fold Leave-One-Subject-Out (LOSO-CV) Clinical Telemetry Benchmark on the WESAD Dataset
        </p>
        """,
        unsafe_allow_html=True,
    )

with col_head_right:
    st.markdown(
        """
        <div style="text-align: right; padding-top: 0.4rem;">
            <a href="https://doi.org/10.5281/zenodo.22806710" target="_blank">
                <img src="https://zenodo.org/badge/DOI/10.5281/zenodo.22806710.svg" alt="DOI: 10.5281/zenodo.22806710" style="margin-bottom: 4px;" />
            </a>
            <br>
            <span style="font-size: 0.8rem; color: #64748B;">Author: <b>Mukesh Yadav</b> (JSSATEN Noida)</span>
        </div>
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
tab_demo, tab_features, tab_benchmark, tab_paper = st.tabs([
    "📈 1. Live Telemetry & Stress Engine",
    "🔬 2. HRV Biomarkers & Baseline Formula",
    "⚖️ 3. Multi-Model Benchmark & Threshold Sweep",
    "📄 4. Research Paper, DOI & Citation",
])

# ==============================================================================
# TAB 1: Live Telemetry & Stress Engine
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
            index=1,
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


# ==============================================================================
# TAB 4: Paper, DOI & Citation Hub
# ==============================================================================
with tab_paper:
    c_paper_left, c_paper_right = st.columns([1.8, 1.2])

    with c_paper_left:
        st.markdown(
            """
            <div class="telemetry-card">
                <div class="kpi-title" style="color: #00F0FF;">Official Research Preprint</div>
                <h3 style="margin: 0.2rem 0 0.6rem 0; font-size: 1.25rem; color: #FFFFFF; font-weight: 700;">
                    Personalized Electrocardiographic and HRV Dynamics for Acute Stress Detection: A Leave-One-Subject-Out Benchmark on WESAD
                </h3>
                <p style="color: #CBD5E1; font-size: 0.9rem; line-height: 1.5; margin-bottom: 0.75rem;">
                    <b>Author:</b> Mukesh Yadav<br>
                    <b>Affiliation:</b> Department of Electronics and Communication Engineering (ECE), JSS Academy of Technical Education, Noida, India<br>
                    <b>License:</b> Creative Commons Attribution 4.0 International (CC-BY 4.0)<br>
                    <b>Permanent DOI:</b> <a href="https://doi.org/10.5281/zenodo.22806710" target="_blank" style="color: #00F0FF;">10.5281/zenodo.22806710</a>
                </p>
                <div style="margin-top: 1rem;">
                    <a href="https://doi.org/10.5281/zenodo.22806710" target="_blank" style="text-decoration: none;">
                        <button style="background: #00F0FF; color: #070913; font-weight: 700; border: none; padding: 0.55rem 1.2rem; border-radius: 6px; cursor: pointer; margin-right: 0.5rem;">
                            🌐 Open Zenodo Record (CERN)
                        </button>
                    </a>
                    <a href="https://github.com/Mukesh-Yadav-4/ECG_STRESS_DETECTION" target="_blank" style="text-decoration: none;">
                        <button style="background: #1E293B; color: #F1F5F9; font-weight: 600; border: 1px solid #2A3656; padding: 0.55rem 1.2rem; border-radius: 6px; cursor: pointer;">
                            🐙 GitHub Repository
                        </button>
                    </a>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # PDF Download Button
        if os.path.isfile(PAPER_PDF_PATH):
            with open(PAPER_PDF_PATH, "rb") as pdf_file:
                pdf_bytes = pdf_file.read()
            st.download_button(
                label="📥 Download Full 6-Page IEEE Benchmark Paper (PDF)",
                data=pdf_bytes,
                file_name="ECG_Stress_Detection_WESAD_Benchmark_Paper.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

    with c_paper_right:
        st.markdown(
            """
            <div class="telemetry-card">
                <div class="kpi-title" style="color: #F59E0B;">BibTeX Academic Citation</div>
            """,
            unsafe_allow_html=True,
        )
        bibtex_code = """@article{yadav2026ecg,
  title     = {Personalized Electrocardiographic and HRV Dynamics for Acute Stress Detection: A Leave-One-Subject-Out Benchmark on WESAD},
  author    = {Yadav, Mukesh},
  journal   = {Zenodo},
  year      = {2026},
  doi       = {10.5281/zenodo.22806710},
  url       = {https://doi.org/10.5281/zenodo.22806710}
}"""
        st.code(bibtex_code, language="bibtex")
        st.markdown("</div>", unsafe_allow_html=True)
