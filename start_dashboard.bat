@echo off
echo =======================================================
echo  Starting ECG Stress Detection Clinical Dashboard
echo =======================================================
cd /d "%~dp0"
python -m streamlit run demo/app.py --server.headless false --server.port 8501
pause
