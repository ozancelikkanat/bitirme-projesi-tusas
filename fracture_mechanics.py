@echo off
cd /d "%~dp0"
python -m streamlit --version >nul 2>&1
if errorlevel 1 (
    echo Gerekli Python paketleri kuruluyor...
    python -m pip install -r requirements.txt
)
python -m streamlit run streamlit_app.py
pause
