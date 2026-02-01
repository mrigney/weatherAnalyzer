# Getting Started - Setup Guide for Beginners

This guide will walk you through setting up Python and running the Temperature Analysis Tool from scratch. No prior Python experience required.

## Table of Contents
- [Windows Setup](#windows-setup)
- [Mac Setup](#mac-setup)
- [Running the Tool](#running-the-tool)
- [Troubleshooting](#troubleshooting)

---

## Windows Setup

### Step 1: Install Python

1. Go to https://www.python.org/downloads/
2. Click the big yellow "Download Python" button (get version 3.10 or later)
3. Run the downloaded installer
4. **IMPORTANT**: Check the box that says "Add Python to PATH" at the bottom of the installer
5. Click "Install Now"
6. Wait for installation to complete, then click "Close"

**Verify installation:**
1. Press `Windows + R`, type `cmd`, press Enter
2. Type `python --version` and press Enter
3. You should see something like `Python 3.12.0`

### Step 2: Download the Tool

**Option A - Using Git:**
1. Install Git from https://git-scm.com/download/win
2. Open Command Prompt
3. Navigate to where you want the project:
   ```
   cd Documents
   ```
4. Clone the repository:
   ```
   git clone https://github.com/mrigney/weatherAnalyzer.git
   cd weatherAnalyzer
   ```

**Option B - Manual Download:**
1. Go to https://github.com/mrigney/weatherAnalyzer
2. Click the green "Code" button
3. Click "Download ZIP"
4. Extract the ZIP file to your Documents folder
5. Open Command Prompt and navigate to it:
   ```
   cd Documents\weatherAnalyzer-main
   ```

### Step 3: Install Dependencies

In Command Prompt, with the project folder open:
```
pip install -r requirements.txt
```

Wait for the packages to download and install. You should see "Successfully installed..." messages.

### Step 4: Run the Tool

**To run the GUI:**
```
python -m streamlit run app.py
```
A browser window will open automatically with the interface.

> **Note:** If `streamlit run app.py` gives a "not recognized" error, use `python -m streamlit run app.py` instead. This ensures Python finds the streamlit module even if it's not in your PATH.

**To run from command line:**
```
python temp_analysis.py hsvWeather_112024.csv --streak --metric TMAX --threshold 90 --top 5
```

---

## Mac Setup

### Step 1: Install Python

Mac comes with Python, but it's often an older version. Install a current version:

**Option A - Using Homebrew (Recommended):**
1. Open Terminal (press `Cmd + Space`, type "Terminal", press Enter)
2. Install Homebrew (if you don't have it):
   ```
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
3. Install Python:
   ```
   brew install python
   ```

**Option B - Direct Download:**
1. Go to https://www.python.org/downloads/
2. Click "Download Python" (get version 3.10 or later)
3. Open the downloaded .pkg file
4. Follow the installer prompts

**Verify installation:**
```
python3 --version
```
You should see something like `Python 3.12.0`

### Step 2: Download the Tool

**Option A - Using Git:**
1. Open Terminal
2. Navigate to where you want the project:
   ```
   cd ~/Documents
   ```
3. Clone the repository:
   ```
   git clone https://github.com/mrigney/weatherAnalyzer.git
   cd weatherAnalyzer
   ```

**Option B - Manual Download:**
1. Go to https://github.com/mrigney/weatherAnalyzer
2. Click the green "Code" button
3. Click "Download ZIP"
4. Extract the ZIP file to your Documents folder
5. Open Terminal and navigate to it:
   ```
   cd ~/Documents/weatherAnalyzer-main
   ```

### Step 3: Install Dependencies

In Terminal, with the project folder open:
```
pip3 install -r requirements.txt
```

Wait for the packages to download and install.

### Step 4: Run the Tool

**To run the GUI:**
```
python3 -m streamlit run app.py
```
A browser window will open automatically with the interface.

> **Note:** If `streamlit run app.py` gives a "command not found" error, use `python3 -m streamlit run app.py` instead.

**To run from command line:**
```
python3 temp_analysis.py hsvWeather_112024.csv --streak --metric TMAX --threshold 90 --top 5
```

---

## Running the Tool

### Using the GUI (Easiest)

1. Open your terminal/command prompt
2. Navigate to the project folder
3. Run:
   ```
   python -m streamlit run app.py   # Windows
   python3 -m streamlit run app.py  # Mac
   ```
4. A browser window opens with the interface
5. Select an analysis type from the sidebar
6. Fill in the parameters and click the analysis button
7. View results in tables and charts

To stop the GUI, press `Ctrl + C` in the terminal.

### Using the Command Line

Basic syntax:
```
python temp_analysis.py <data_file> <analysis_type> [options]
```

**Examples:**

Find heat waves (days with highs >= 95°F):
```
python temp_analysis.py hsvWeather_112024.csv --streak --metric TMAX --threshold 95 --direction above
```

Find coldest 7-day periods:
```
python temp_analysis.py hsvWeather_112024.csv --period --metric TAVG --days 7 --extreme coldest
```

Find coldest winters:
```
python temp_analysis.py hsvWeather_112024.csv --season winter --extreme coldest --top 5
```

Get help:
```
python temp_analysis.py --help
```

### Running the Examples

To see all features in action:
```
python examples.py
```

This runs 8 different analysis examples and prints the results.

---

## Troubleshooting

### "python is not recognized as an internal or external command" (Windows)

Python wasn't added to your PATH. Either:
1. Reinstall Python and check "Add Python to PATH"
2. Or use the full path: `C:\Users\YourName\AppData\Local\Programs\Python\Python312\python.exe`

### "command not found: python" (Mac)

Use `python3` instead of `python`:
```
python3 temp_analysis.py ...
```

### "pip is not recognized" or "command not found: pip"

Try these alternatives:
```
python -m pip install -r requirements.txt    # Windows
python3 -m pip install -r requirements.txt   # Mac
```

### "streamlit is not recognized" or "command not found: streamlit"

Streamlit isn't in your PATH. Use the module syntax instead:
```
python -m streamlit run app.py    # Windows
python3 -m streamlit run app.py   # Mac
```

### "No module named 'pandas'" (or numpy, streamlit)

Dependencies aren't installed. Run:
```
pip install -r requirements.txt    # Windows
pip3 install -r requirements.txt   # Mac
```

### "Permission denied" errors

Add `--user` flag:
```
pip install --user -r requirements.txt
```

### Streamlit opens but shows an error

Make sure you're in the project folder when running `streamlit run app.py`. The app needs to find `temp_analysis.py` and the data file.

### The browser doesn't open automatically

Streamlit will show a URL like `http://localhost:8501`. Copy and paste this into your browser manually.

### "Address already in use" when starting Streamlit

Another instance is already running. Either:
1. Find the existing browser tab with Streamlit
2. Or stop all instances and restart:
   - Press `Ctrl + C` in any terminal running Streamlit
   - Try again

---

## Next Steps

Once you have the tool running:
1. Try the GUI first to explore features visually
2. Read the [User Guide](USER_GUIDE.md) for detailed information on each analysis type
3. Use your own weather data by uploading a CSV file in the GUI
4. Experiment with the command line for automation or scripting
