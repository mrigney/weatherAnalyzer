# Temperature Analysis Tool - User Guide

This tool analyzes historical weather data to find temperature patterns, extremes, and trends. You can use it via command line, Python code, or a web-based GUI.

## Table of Contents
- [Quick Start](#quick-start)
- [Data Format](#data-format)
- [Analysis Types](#analysis-types)
  - [Temperature Streaks](#1-temperature-streaks)
  - [Extreme Periods](#2-extreme-periods)
  - [Seasonal Analysis](#3-seasonal-analysis)
  - [Custom Date Range](#4-custom-date-range)
  - [Threshold Histogram](#5-threshold-histogram)
- [Using the GUI](#using-the-gui)
- [Using the Command Line](#using-the-command-line)
- [Using the Python API](#using-the-python-api)
- [Working with Custom Data](#working-with-custom-data)

---

## Quick Start

**GUI (easiest):**
```
streamlit run app.py
```
A browser window will open with an interactive interface.

**Command Line:**
```
python temp_analysis.py hsvWeather_112024.csv --streak --metric TMAX --threshold 90 --top 5
```

**Python:**
```python
from temp_analysis import TempAnalyzer
analyzer = TempAnalyzer('hsvWeather_112024.csv')
results = analyzer.find_streaks(metric='TMAX', threshold=90, top_n=5)
```

---

## Data Format

Your CSV file needs these columns:
| Column | Description | Required |
|--------|-------------|----------|
| DATE | Date in any standard format (YYYY-MM-DD, MM/DD/YYYY, etc.) | Yes |
| TMAX | Daily maximum temperature (Fahrenheit) | Yes |
| TMIN | Daily minimum temperature (Fahrenheit) | Yes |
| TAVG | Daily average temperature (Fahrenheit) | No (calculated if missing) |

If your CSV has different column names, see [Working with Custom Data](#working-with-custom-data).

---

## Analysis Types

### 1. Temperature Streaks

Find the longest consecutive periods where temperature stayed above or below a threshold.

**Examples:**
- Longest heat waves (TMAX >= 95°F)
- Longest freezing streaks (TMIN <= 32°F)
- Longest mild periods (TAVG between thresholds)

**CLI:**
```bash
# Find longest heat waves (highs at or above 95°F)
python temp_analysis.py data.csv --streak --metric TMAX --threshold 95 --direction above --top 10

# Find longest freezing streaks (lows at or below 32°F)
python temp_analysis.py data.csv --streak --metric TMIN --threshold 32 --direction below --top 10
```

**Python:**
```python
# Longest heat waves
streaks = analyzer.find_streaks(metric='TMAX', threshold=95, direction='above', top_n=10)
analyzer.print_streak_report(streaks, 'TMAX', 95, 'above')
```

**Output includes:**
- Rank and streak length (days)
- Start and end dates
- Average, minimum, and maximum temperatures during the streak

---

### 2. Extreme Periods

Find the coldest or warmest N-day periods using rolling averages. Periods are non-overlapping to avoid redundant results.

**Examples:**
- Coldest 7-day periods
- Warmest 2-week stretches
- Most extreme monthly periods

**CLI:**
```bash
# Find coldest 7-day periods
python temp_analysis.py data.csv --period --metric TAVG --days 7 --extreme coldest --top 10

# Find warmest 14-day periods
python temp_analysis.py data.csv --period --metric TMAX --days 14 --extreme warmest --top 5
```

**Python:**
```python
periods = analyzer.find_extreme_periods(metric='TAVG', n_days=7, extreme='coldest', top_n=10)
analyzer.print_period_report(periods, 'TAVG', 7, 'coldest')
```

**Output includes:**
- Rank and average temperature
- Start and end dates
- Temperature range (min/max) during the period

---

### 3. Seasonal Analysis

Find the coldest or warmest seasons across all years in your data.

**Season definitions:**
- Winter: December - February (Dec belongs to the following year's winter)
- Spring: March - May
- Summer: June - August
- Fall: September - November

**CLI:**
```bash
# Find coldest winters
python temp_analysis.py data.csv --season winter --metric TAVG --extreme coldest --top 10

# Find warmest summers
python temp_analysis.py data.csv --season summer --metric TMAX --extreme warmest --top 10
```

**Python:**
```python
winters = analyzer.find_extreme_seasons(season='winter', metric='TAVG', extreme='coldest', top_n=10)
analyzer.print_season_report(winters, 'winter', 'TAVG', 'coldest')
```

**Output includes:**
- Season year (e.g., "Winter 2013-14")
- Average temperature for the season
- Temperature range and number of days

---

### 4. Custom Date Range

Analyze any date range across all years. Great for holidays, special events, or custom periods.

**Examples:**
- Coldest Christmas weeks (Dec 20 - Dec 31)
- Warmest 4th of July weeks
- Temperature during spring break dates

Supports year-spanning ranges (e.g., Dec 15 - Jan 15).

**CLI:**
```bash
# Coldest Christmas periods
python temp_analysis.py data.csv --date-range 12/20-12/31 --metric TAVG --extreme coldest --top 10

# Warmest July 4th weeks
python temp_analysis.py data.csv --date-range 7/1-7/7 --metric TMAX --extreme warmest --top 5
```

**Python:**
```python
christmas = analyzer.find_extreme_date_range(12, 20, 12, 31, metric='TAVG', extreme='coldest', top_n=10)
analyzer.print_date_range_report(christmas, 12, 20, 12, 31, 'TAVG', 'coldest')
```

**Output includes:**
- Year and average temperature
- Temperature range
- Actual dates covered

---

### 5. Threshold Histogram

Count how often temperature meets a threshold within a date range, broken down by year. Useful for understanding frequency of events.

**Examples:**
- How often does it freeze in January?
- How many 100°F+ days in summer?
- Frequency of mild winter days

**CLI:**
```bash
# How often does it freeze in January?
python temp_analysis.py data.csv --histogram 1/1-1/31 --metric TMIN --threshold 32 --direction below

# How many 90°F+ days in summer?
python temp_analysis.py data.csv --histogram 6/1-8/31 --metric TMAX --threshold 90 --direction above
```

**Python:**
```python
result = analyzer.threshold_histogram(1, 1, 1, 31, metric='TMIN', threshold=32, direction='below')
analyzer.print_histogram_report(result, 1, 1, 1, 31, 'TMIN', 32, 'below')
```

**Output includes:**
- Summary statistics (average, min, max, std dev)
- Year-by-year breakdown with visual bar chart
- Percentage of days meeting threshold

---

## Using the GUI

The Streamlit GUI provides a visual interface for all features.

**To start:**
```
streamlit run app.py
```

**Features:**
1. **Data source**: Use included Huntsville data or upload your own CSV
2. **Column mapping**: If uploading custom data, map your columns to expected names
3. **Analysis selector**: Choose from all 5 analysis types in the sidebar
4. **Interactive forms**: Fill in parameters for each analysis type
5. **Results**: View formatted tables and charts

---

## Using the Command Line

The CLI supports all analysis types with flexible options.

**General syntax:**
```
python temp_analysis.py <csv_file> <analysis_type> [options]
```

**Common options:**
| Option | Description | Default |
|--------|-------------|---------|
| `--metric` | TMIN, TMAX, or TAVG | TMAX |
| `--threshold` | Temperature threshold (°F) | - |
| `--direction` | above or below | above |
| `--extreme` | coldest or warmest | coldest |
| `--days` | Period length for --period | 7 |
| `--top` | Number of results | 10 |
| `--map` | Column mapping (see below) | - |

**Get help:**
```
python temp_analysis.py --help
```

---

## Using the Python API

Import the `TempAnalyzer` class for programmatic access.

```python
from temp_analysis import TempAnalyzer

# Load data
analyzer = TempAnalyzer('your_data.csv')

# Check data info
print(f"Records: {len(analyzer.df)}")
print(f"Date range: {analyzer.df['DATE'].min()} to {analyzer.df['DATE'].max()}")

# Run any analysis
streaks = analyzer.find_streaks(metric='TMAX', threshold=90, direction='above', top_n=5)
periods = analyzer.find_extreme_periods(metric='TAVG', n_days=7, extreme='coldest', top_n=5)
seasons = analyzer.find_extreme_seasons(season='winter', metric='TAVG', extreme='coldest', top_n=5)
ranges = analyzer.find_extreme_date_range(12, 20, 12, 31, metric='TAVG', extreme='coldest', top_n=5)
histogram = analyzer.threshold_histogram(1, 1, 1, 31, metric='TMIN', threshold=32, direction='below')

# Print formatted reports
analyzer.print_streak_report(streaks, 'TMAX', 90, 'above')
# ... or work with the DataFrames directly
```

See `examples.py` for complete usage examples.

---

## Working with Custom Data

If your CSV has different column names, use column mapping.

**CLI:**
```bash
python temp_analysis.py mydata.csv --streak --threshold 90 --map MaxTemp=TMAX MinTemp=TMIN Date=DATE
```

**Python:**
```python
analyzer = TempAnalyzer('mydata.csv', column_map={
    'MaxTemp': 'TMAX',
    'MinTemp': 'TMIN',
    'Date': 'DATE'
})
```

**GUI:**
When uploading a CSV, use the column mapping dropdowns to select which columns correspond to DATE, TMAX, and TMIN.

---

## Tips

1. **Temperature units**: All thresholds and output are in Fahrenheit
2. **Missing TAVG**: Automatically calculated as (TMAX + TMIN) / 2
3. **Date formats**: Most standard formats are supported (YYYY-MM-DD, MM/DD/YYYY, etc.)
4. **Large datasets**: The tool handles decades of daily data efficiently
5. **Non-overlapping periods**: Extreme period analysis avoids redundant overlapping results
