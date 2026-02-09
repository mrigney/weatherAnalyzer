# Dependencies

## Required Packages

| Package | Minimum Version | Purpose |
|---------|-----------------|---------|
| pandas | 1.5.0 | Data manipulation and analysis |
| numpy | 1.21.0 | Numerical operations |
| streamlit | 1.20.0 | Web-based GUI (optional, only needed for app.py) |
| plotly | 5.0.0 | Interactive charts in the GUI (optional, only needed for app.py) |

## Quick Install

Install all dependencies at once:
```bash
pip install -r requirements.txt
```

## Minimal Install (CLI only)

If you only need the command-line tool and Python API (no GUI):
```bash
pip install pandas numpy
```

## Full Install (with GUI)

For the complete package including the Streamlit web interface with interactive Plotly charts:
```bash
pip install pandas numpy streamlit plotly
```

## Python Version

- **Minimum**: Python 3.8
- **Recommended**: Python 3.10 or later

## Verifying Installation

Check if dependencies are installed:
```bash
python -c "import pandas; import numpy; print('Core dependencies OK')"
python -c "import streamlit; print('Streamlit OK')"
python -c "import plotly; print('Plotly OK')"
```

## Troubleshooting

**pip not found:**
- Try `pip3` instead of `pip`
- Or use `python -m pip install ...`

**Permission errors:**
- Add `--user` flag: `pip install --user -r requirements.txt`
- Or use a virtual environment (recommended)

**Version conflicts:**
- Create a fresh virtual environment:
  ```bash
  python -m venv venv
  source venv/bin/activate  # Mac/Linux
  venv\Scripts\activate     # Windows
  pip install -r requirements.txt
  ```
