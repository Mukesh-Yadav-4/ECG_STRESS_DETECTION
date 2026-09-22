import os
import subprocess

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>WESAD ECG Stress Detection - Master Execution Guide</title>
<style>
  @page {
    size: A4;
    margin: 14mm 14mm 14mm 14mm;
  }
  * {
    box-sizing: border-box;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
  body {
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
    color: #1e293b;
    background: #ffffff;
    line-height: 1.5;
    font-size: 10pt;
    margin: 0;
    padding: 0;
  }
  .header-card {
    border-bottom: 2px solid #0284c7;
    padding-bottom: 12px;
    margin-bottom: 16px;
  }
  h1 {
    font-size: 18pt;
    font-weight: 800;
    color: #0f172a;
    margin: 0 0 4px 0;
    letter-spacing: -0.5px;
  }
  .subtitle {
    font-size: 10.5pt;
    color: #475569;
    margin-bottom: 8px;
    font-weight: 500;
  }
  .meta-bar {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    font-size: 8.5pt;
    color: #64748b;
    margin-top: 6px;
  }
  .badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-weight: 600;
    font-size: 8pt;
  }
  .badge-blue { background: #e0f2fe; color: #0369a1; border: 1px solid #bae6fd; }
  .badge-green { background: #dcfce7; color: #15803d; border: 1px solid #bbf7d0; }
  .badge-purple { background: #f3e8ff; color: #7e22ce; border: 1px solid #e9d5ff; }
  .badge-slate { background: #f1f5f9; color: #334155; border: 1px solid #e2e8f0; }

  h2 {
    font-size: 12pt;
    font-weight: 700;
    color: #0f172a;
    border-bottom: 1px solid #e2e8f0;
    padding-bottom: 4px;
    margin: 16px 0 8px 0;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    page-break-after: avoid;
  }
  h3 {
    font-size: 10.5pt;
    font-weight: 700;
    color: #0369a1;
    margin: 12px 0 4px 0;
    page-break-after: avoid;
  }
  p {
    margin: 4px 0 8px 0;
  }
  code {
    font-family: 'Cascadia Code', 'Consolas', 'Courier New', monospace;
    font-size: 8.8pt;
    background: #f1f5f9;
    color: #0f172a;
    padding: 1px 4px;
    border-radius: 3px;
    border: 1px solid #e2e8f0;
  }
  pre {
    background: #0f172a;
    color: #f8fafc;
    font-family: 'Cascadia Code', 'Consolas', monospace;
    font-size: 8.5pt;
    padding: 8px 12px;
    border-radius: 6px;
    margin: 6px 0 10px 0;
    overflow-x: auto;
    line-height: 1.4;
    page-break-inside: avoid;
  }
  pre code {
    background: transparent;
    color: inherit;
    padding: 0;
    border: none;
    font-size: inherit;
  }
  .architecture-box {
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-left: 4px solid #0284c7;
    border-radius: 4px;
    padding: 8px 12px;
    font-family: 'Cascadia Code', 'Consolas', monospace;
    font-size: 8pt;
    line-height: 1.35;
    margin: 8px 0 12px 0;
    page-break-inside: avoid;
    white-space: pre;
    color: #1e293b;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    margin: 8px 0 12px 0;
    font-size: 8.5pt;
    page-break-inside: avoid;
  }
  th {
    background: #f1f5f9;
    color: #0f172a;
    font-weight: 700;
    text-align: left;
    padding: 6px 8px;
    border: 1px solid #cbd5e1;
  }
  td {
    padding: 5px 8px;
    border: 1px solid #e2e8f0;
    vertical-align: top;
  }
  tr:nth-child(even) {
    background: #f8fafc;
  }
  .step-card {
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 8px 12px;
    margin-bottom: 10px;
    background: #ffffff;
    page-break-inside: avoid;
  }
  .step-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 4px;
  }
  .step-title {
    font-size: 10pt;
    font-weight: 700;
    color: #0f172a;
  }
  .step-tag {
    font-size: 7.5pt;
    font-weight: 600;
    padding: 2px 6px;
    border-radius: 3px;
  }
  .tag-matlab { background: #ffedd5; color: #c2410c; border: 1px solid #fed7aa; }
  .tag-python { background: #dbeafe; color: #1d4ed8; border: 1px solid #bfdbfe; }
  .tag-web { background: #fef08a; color: #854d0e; border: 1px solid #fef9c3; }

  ul, ol {
    margin: 4px 0 8px 0;
    padding-left: 18px;
  }
  li {
    margin-bottom: 2px;
  }
  .callout-tip {
    background: #eff6ff;
    border-left: 3px solid #3b82f6;
    padding: 6px 10px;
    border-radius: 0 4px 4px 0;
    margin: 6px 0;
    font-size: 8.5pt;
    color: #1e40af;
    page-break-inside: avoid;
  }
</style>
</head>
<body>

<div class="header-card">
  <h1>Master Execution Guide: WESAD ECG Stress Pipeline</h1>
  <div class="subtitle">End-to-End Operational Protocol: From 700 Hz Wearable Biosignal Telemetry to ML Benchmarks & Web Deployment</div>
  <div class="meta-bar">
    <span><strong>Author:</strong> Mukesh Yadav (ECE, JSSATEN)</span> &bull;
    <span><strong>Dataset:</strong> WESAD (15 Subjects, RespiBAN Chest ECG)</span> &bull;
    <span><strong>Validation:</strong> 15-Fold Leave-One-Subject-Out (LOSO)</span> &bull;
    <span><strong>Benchmark:</strong> ROC-AUC 0.9494 | Sensitivity 86.25%</span>
  </div>
  <div style="margin-top: 6px;">
    <span class="badge badge-blue">MATLAB R2022b+</span>
    <span class="badge badge-purple">Python 3.10+</span>
    <span class="badge badge-green">Scikit-Learn ML Suite</span>
    <span class="badge badge-slate">Streamlit Telemetry App</span>
  </div>
</div>

<h2>1. System Architecture & Information Flow</h2>
<div class="architecture-box">
                                [ RAW DATA ACQUISITION ]
                        WESAD Wearable Dataset (15 Subjects)
                        Chest RespiBAN Lead-II ECG @ 700 Hz
                                        │
                                        ▼ (Step 0: Python Extraction)
                        [ STANDARDIZED S*_ECG_labels.mat ]
                                        │
                    ┌───────────────────┴───────────────────┐
                    ▼                                       ▼
        [ MATLAB DSP & FEATURE SUITE ]          [ PYTHON ML BENCHMARK ]
        - 0.5–40 Hz 4th-order Butterworth       - 15-Fold LOSO Validation
        - Pan-Tompkins & MAD Peak Detection     - 6 ML Models (inc. MLP)
        - 60s Sliding Windows (50% Overlap)     - Feature Importance / Odds Ratios
        - 8 Core Autonomic HRV Metrics          - ROC-AUC / PR-AUC Evaluation
        - Subject Baseline Normalization (Δx)   - Streamlit Web Dashboard
                    │                                       │
                    ▼                                       ▼
        [ Publication Figures & Dashboard ]     [ Interactive Telemetry App ]
        - 300 DPI Medical Vector Graphics       - Real-time stress needle gauge
        - Master 6-Panel Research Board         - Live sliding threshold slider
</div>

<h2>2. Prerequisites & Environment Configuration</h2>
<p>Ensure Python 3.10+ and MATLAB R2022b+ (with <em>Signal Processing</em> & <em>Statistics</em> toolboxes) are configured. Run the following in PowerShell:</p>
<pre><code># Navigate to project directory
cd "C:\Users\YASH\Desktop\projects\RESEARCH PROJECTS\ECG_STRESS_DETECTION"

# Create and activate Python virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install core dependencies
pip install -r requirements.txt</code></pre>

<h2>3. Step-by-Step Chronological Execution Sequence</h2>

<div class="step-card">
  <div class="step-header">
    <span class="step-title">Step 0: Raw Data Ingestion & Formatting</span>
    <span class="step-tag tag-python">PYTHON</span>
  </div>
  <p>Ingests WESAD pickle files (<code>S2.pkl</code> to <code>S17.pkl</code>), extracts the 700 Hz chest ECG and ground-truth affective labels, casts them to <code>float32</code>/<code>uint8</code>, and saves compressed MATLAB arrays.</p>
  <pre><code>python python/extract_ecg_labels.py</code></pre>
  <div><strong>Output:</strong> <code>data/processed/S*_ECG_labels.mat</code> files for all 15 subjects.</div>
</div>

<div class="step-card">
  <div class="step-header">
    <span class="step-title">Step 1: MATLAB Workspace & Path Initialization</span>
    <span class="step-tag tag-matlab">MATLAB</span>
  </div>
  <p>Registers all algorithmic subdirectories, DSP functions, and feature extraction scripts to the MATLAB search path.</p>
  <pre><code>cd 'C:\Users\YASH\Desktop\projects\RESEARCH PROJECTS\ECG_STRESS_DETECTION\matlab'
setup_project</code></pre>
</div>

<div class="step-card">
  <div class="step-header">
    <span class="step-title">Step 2: Multi-Subject DSP & Feature Extraction</span>
    <span class="step-tag tag-matlab">MATLAB</span>
  </div>
  <p>Applies a zero-phase 4th-order Butterworth bandpass (0.5–40 Hz), estimates the noise floor via Median Absolute Deviation (MAD), enforces 350 ms refractory lockout, extracts 60s windows with 50% overlap, gates intervals to 300–1500 ms (40–200 BPM), and extracts 8 core HRV metrics normalized against resting baseline.</p>
  <pre><code>TEN_process_all_subjects</code></pre>
  <div><strong>Output:</strong> <code>results/WESAD_HRV_features_expanded.csv</code> (445 standardized windows across 15 subjects).</div>
</div>

<div class="step-card">
  <div class="step-header">
    <span class="step-title">Step 3: Statistical Hypothesis Testing & Audits</span>
    <span class="step-tag tag-matlab">MATLAB</span>
  </div>
  <p>Executes paired Student's t-tests and Wilcoxon signed-rank tests confirming significant sympathetic activation and parasympathetic withdrawal (p &lt; 0.001).</p>
  <pre><code>FOURTEEN_statistical_tests
FIFTEEN_feature_analysis</code></pre>
</div>

<div class="step-card">
  <div class="step-header">
    <span class="step-title">Step 4: Publication Figures & Master Clinical Dashboard</span>
    <span class="step-tag tag-matlab">MATLAB</span>
  </div>
  <p>Generates 300 DPI vector figures (confusion matrix, ROC curve, timeline) and the comprehensive 6-panel clinical research board.</p>
  <pre><code>TWENTY_SEVEN_final_results       % Computes final metrics table
TWENTY_EIGHT_report_figures      % Exports individual high-res figures
TWENTY_NINE_project_dashboard    % Generates master 6-panel dashboard</code></pre>
  <div><strong>Output:</strong> <code>results/figures/FINAL_Project_Dashboard.png</code> and FIG1–FIG5.</div>
</div>

<div class="step-card">
  <div class="step-header">
    <span class="step-title">Step 5: Interactive Telemetry MATLAB Demo GUI</span>
    <span class="step-tag tag-matlab">MATLAB GUI</span>
  </div>
  <p>Launches an interactive tabbed GUI displaying raw Lead-II telemetry, protocol timelines, Pan-Tompkins QRS detections, and physiological contrast scorecards.</p>
  <pre><code>DEMO_stress_detection</code></pre>
</div>

<div class="step-card">
  <div class="step-header">
    <span class="step-title">Step 6: 15-Fold LOSO Machine Learning Benchmark</span>
    <span class="step-tag tag-python">PYTHON</span>
  </div>
  <p>Performs strict 15-fold Leave-One-Subject-Out cross-validation across 6 machine learning architectures with zero subject data leakage (StandardScaler fit strictly on training subjects).</p>
  <pre><code>python python/train_loso_ml_benchmark.py</code></pre>
  <div><strong>Benchmarked Models:</strong> Logistic Regression, Support Vector Machine (RBF), Random Forest, Extra Trees, HistGradientBoosting, and Multi-Layer Perceptron (MLP Neural Network).</div>
</div>

<div class="step-card">
  <div class="step-header">
    <span class="step-title">Step 7: Explainability & Permutation Feature Importance</span>
    <span class="step-tag tag-python">PYTHON</span>
  </div>
  <p>Quantifies physiological drivers using permutation importance and clinical standardized odds ratios, confirming that cardiac interval compression (ΔMeanRR) and heart rate acceleration (ΔMeanHR) govern the decision boundary.</p>
  <pre><code>python python/explainability_feature_importance.py</code></pre>
</div>

<div class="step-card">
  <div class="step-header">
    <span class="step-title">Step 8: Multi-Model Evaluation Plots & Curves</span>
    <span class="step-tag tag-python">PYTHON</span>
  </div>
  <p>Renders high-resolution comparative ROC curves, Precision-Recall curves, confusion matrices, and performance bar charts across all benchmarked models.</p>
  <pre><code>python python/plot_ml_evaluation.py</code></pre>
</div>

<div class="step-card">
  <div class="step-header">
    <span class="step-title">Step 9: Interactive Clinical Telemetry Web Application</span>
    <span class="step-tag tag-web">STREAMLIT WEB APP</span>
  </div>
  <p>Spins up a local web application featuring interactive ECG waveform playback, live R-peak markers, dynamic decision threshold sliders, and real-time stress needle gauges.</p>
  <pre><code>streamlit run demo/app.py</code></pre>
  <div>Access via browser at: <code>http://localhost:8501</code></div>
</div>

<h2>4. Quick-Run One-Liners</h2>
<table>
  <tr>
    <th style="width: 35%;">Workflow Goal</th>
    <th>Command</th>
  </tr>
  <tr>
    <td><strong>Run Full Python ML Suite</strong></td>
    <td><code>python python/train_loso_ml_benchmark.py; python python/explainability_feature_importance.py; python python/plot_ml_evaluation.py</code></td>
  </tr>
  <tr>
    <td><strong>Run Headless MATLAB Pipeline</strong></td>
    <td><code>matlab -batch "cd('matlab'); setup_project; TWENTY_SEVEN_final_results; TWENTY_EIGHT_report_figures; TWENTY_NINE_project_dashboard; exit"</code></td>
  </tr>
  <tr>
    <td><strong>Launch Web Telemetry Dashboard</strong></td>
    <td><code>streamlit run demo/app.py</code></td>
  </tr>
</table>

<h2>5. Verification Checklist & Expected Benchmarks</h2>
<table>
  <tr>
    <th>Target Output</th>
    <th>Verification Metric</th>
    <th>Status</th>
  </tr>
  <tr>
    <td><code>S*_ECG_labels.mat</code></td>
    <td>15 subject files, 700 Hz Lead-II ECG, synchronized ground truth labels</td>
    <td>&check; Verified</td>
  </tr>
  <tr>
    <td><code>WESAD_HRV_features_expanded.csv</code></td>
    <td>445 total windows (285 baseline, 160 acute TSST stress), 8 core HRV features</td>
    <td>&check; Verified</td>
  </tr>
  <tr>
    <td>Primary Calibrated Classifier</td>
    <td>ROC-AUC = 0.9494, Sensitivity = 86.25%, Specificity = 95.79% (at &tau; = 0.35)</td>
    <td>&check; Verified</td>
  </tr>
  <tr>
    <td>Multi-Model ML Benchmark</td>
    <td>All 6 architectures (LR, SVM, RF, ET, HistGB, MLP) achieve ROC-AUC &gt; 0.937 on held-out subjects</td>
    <td>&check; Verified</td>
  </tr>
  <tr>
    <td>Master Dashboard Graphic</td>
    <td><code>results/figures/FINAL_Project_Dashboard.png</code> generated at 300 DPI</td>
    <td>&check; Verified</td>
  </tr>
</table>

<h2>6. Common Technical Troubleshooting</h2>
<ul>
  <li><strong>Missing Signal Processing Toolbox (MATLAB):</strong> If <code>butter</code> or <code>filtfilt</code> fails, install the toolbox via <em>MATLAB Home &rarr; Add-Ons &rarr; Get Add-Ons</em>.</li>
  <li><strong>CSV Not Found in Python:</strong> Ensure Step 2 (<code>TEN_process_all_subjects.m</code>) has executed to generate <code>results/WESAD_HRV_features_expanded.csv</code>.</li>
  <li><strong>Streamlit Port Collision:</strong> If port 8501 is busy, specify an alternate port: <code>streamlit run demo/app.py --server.port 8502</code>.</li>
</ul>

<div class="callout-tip">
  <strong>Defense / Review Tip:</strong> Always emphasize that all models were evaluated using strict <strong>15-Fold Leave-One-Subject-Out (LOSO) cross-validation</strong> with subject-specific baseline normalization (&Delta;x). This eliminates inter-individual baseline variance without data leakage.
</div>

</body>
</html>
"""

def generate_pdf():
    project_root = r"C:\Users\YASH\Desktop\projects\RESEARCH PROJECTS\ECG_STRESS_DETECTION"
    html_path = os.path.join(project_root, "docs", "EXECUTION_GUIDE.html")
    pdf_path = os.path.join(project_root, "EXECUTION_GUIDE.pdf")
    
    os.makedirs(os.path.dirname(html_path), exist_ok=True)
    
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(HTML_CONTENT)
    print(f"Wrote HTML to {html_path}")
    
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    if not os.path.exists(edge_path):
        edge_path = r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
        
    cmd = [
        edge_path,
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path}",
        html_path
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0 and os.path.exists(pdf_path):
        size_kb = os.path.getsize(pdf_path) / 1024
        print(f"SUCCESS: Generated {pdf_path} ({size_kb:.1f} KB)")
    else:
        print(f"Error: {result.stderr}")

if __name__ == "__main__":
    generate_pdf()
