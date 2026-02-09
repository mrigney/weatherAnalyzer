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
  - [Extreme Event Frequency](#6-extreme-event-frequency)
  - [Freeze Date Tracker](#7-freeze-date-tracker)
  - [Temperature Heatmap](#8-temperature-heatmap)
  - [Daily Record Envelope](#9-daily-record-envelope)
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

Find the longest consecutive runs of days where a temperature metric stayed above or below a given threshold. For example, find the longest stretch where the high temperature stayed at or above 95°F. Results are ranked by streak length and show the start and end dates of each streak.

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

Find the coldest or warmest N-day periods in the dataset using rolling averages. Periods are non-overlapping so each result represents a distinct event, ranked by average temperature. Useful for identifying notable cold snaps, heat waves, or sustained temperature anomalies of any duration.

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

Rank every season in the dataset by average temperature to find the coldest or warmest on record. December is grouped with the following year's winter (e.g., Dec 2023 belongs to Winter 2023-24). This makes it easy to answer questions like "Which winter was the coldest?" or "Which summer had the highest average highs?"

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

Compare a specific calendar date range across every year in the dataset to find the coldest or warmest instances. For example, find which year had the coldest Christmas week or the warmest July 4th period. Year-spanning ranges (e.g., Dec 15 - Jan 15) are supported, letting you analyze periods that cross the new year boundary.

**Examples:**
- Coldest Christmas weeks (Dec 20 - Dec 31)
- Warmest 4th of July weeks
- Temperature during spring break dates

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

Count how many days within a date range meet a temperature threshold, broken down by year. For example, how many days in January did the low temperature drop to 32°F or below? Results show year-by-year counts along with summary statistics like the average and extremes. Supports year-spanning date ranges.

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

### 6. Extreme Event Frequency

Track how many days per year a temperature threshold is met across the entire dataset. A linear trendline shows whether these events are becoming more or less frequent over time. Useful for spotting long-term changes in extreme heat days, freezing days, and similar patterns. The GUI displays an interactive bar chart with a dashed trendline overlay.

**Examples:**
- How many 100°F+ days per year? Is it increasing?
- How many freezing days per year? Is it decreasing?
- Days above 90°F per year with trend

**CLI:**
```bash
# How many days per year does TMAX hit 100°F?
python temp_analysis.py data.csv --event-freq --metric TMAX --threshold 100 --direction above

# How many freezing days per year?
python temp_analysis.py data.csv --event-freq --metric TMIN --threshold 32 --direction below
```

**Python:**
```python
freq_data = analyzer.find_extreme_event_frequency(metric='TMAX', threshold=100, direction='above')
analyzer.print_event_frequency_report(freq_data, 'TMAX', 100, 'above')
```

**Output includes:**
- Summary: average events/year, minimum, maximum, trend slope
- Trend direction (increasing, decreasing, or stable)
- Year-by-year event counts with bar chart
- In the GUI: interactive Plotly bar chart with dashed red trendline

---

### 7. Freeze Date Tracker

Find the last spring freeze and first fall freeze for each year in the dataset. The growing season length (the number of days between last spring freeze and first fall freeze) is also calculated. Spring freezes are defined as the latest freeze date before July 1; fall freezes are the earliest freeze date on or after July 1. Years with no freezes in a season are handled gracefully.

**Examples:**
- When does the last freeze typically occur in spring?
- When does the first freeze typically arrive in fall?
- Is the growing season getting longer over time?

**CLI:**
```bash
# Track freeze dates using default TMIN <= 32°F
python temp_analysis.py data.csv --freeze-dates

# Use a different threshold
python temp_analysis.py data.csv --freeze-dates --threshold 28

# Use a different metric
python temp_analysis.py data.csv --freeze-dates --metric TMAX --threshold 32
```

Note: `--freeze-dates` defaults to TMIN with a 32°F threshold. Use `--metric` to override.

**Python:**
```python
freeze_data = analyzer.find_freeze_dates(metric='TMIN', threshold=32.0)
analyzer.print_freeze_dates_report(freeze_data, 'TMIN', 32.0)
```

**Output includes:**
- Summary: average last spring freeze date, average first fall freeze date, average growing season length
- Year-by-year table with last spring freeze, first fall freeze, and growing season days
- In the GUI: dual-axis chart with spring/fall freeze dates (lines) and growing season bars

---

### 8. Temperature Heatmap

Visualize monthly average temperatures across all years as a color-coded heatmap with years on the y-axis and months on the x-axis. In **absolute** mode, colors represent actual temperatures (using a red-yellow-blue color scale). In **anomaly** mode, colors show how much each month departed from its long-term average, making it easy to spot unusually warm or cold months (using a red-blue diverging scale centered at zero).

**Examples:**
- Which months and years were unusually warm or cold?
- Are summers getting hotter over the decades?
- Visualize warming/cooling trends at a glance

**CLI:**
```bash
# Absolute temperature heatmap
python temp_analysis.py data.csv --heatmap --metric TAVG

# Anomaly (departure from mean) heatmap
python temp_analysis.py data.csv --heatmap --metric TAVG --heatmap-mode anomaly

# Heatmap of daily highs
python temp_analysis.py data.csv --heatmap --metric TMAX
```

**Python:**
```python
# Absolute temperatures
heatmap = analyzer.create_temperature_heatmap(metric='TAVG', mode='absolute')
analyzer.print_heatmap_report(heatmap, 'TAVG', 'absolute')

# Anomaly from long-term mean
anomaly = analyzer.create_temperature_heatmap(metric='TAVG', mode='anomaly')
analyzer.print_heatmap_report(anomaly, 'TAVG', 'anomaly')
```

**Output includes:**
- CLI: tabular display of monthly averages (or anomalies) by year
- GUI: interactive Plotly heatmap with hover tooltips showing exact values
- Summary of hottest/coldest cells (absolute) or largest warm/cold anomalies

---

### 9. Daily Record Envelope

Display the all-time record high, record low, and long-term daily average for each day of the year. The shaded "envelope" shows the full historical range of temperatures for the chosen metric. Optionally overlay a specific year to see how it compared to historical norms. Use the date range presets or a custom range to focus on a particular season.

The **metric** selector changes which temperature value is analyzed:
- **TMAX**: shows the highest TMAX ever, lowest TMAX ever, and average TMAX for each calendar day
- **TMIN**: shows the highest TMIN ever, lowest TMIN ever, and average TMIN for each calendar day
- **TAVG**: same concept for daily average temperatures

**Examples:**
- How did 2023 compare to historical records?
- What are the all-time records for each day of summer?
- Was a particular winter unusually cold compared to the long-term envelope?

**CLI:**
```bash
# Full year climate band
python temp_analysis.py data.csv --climate-band --metric TMAX

# With a specific year overlay
python temp_analysis.py data.csv --climate-band --metric TMAX --overlay-year 2023

# Summer only
python temp_analysis.py data.csv --climate-band --metric TMAX --band-range 6/1-8/31

# Winter with overlay
python temp_analysis.py data.csv --climate-band --metric TMIN --band-range 12/1-2/28 --overlay-year 2010
```

**Python:**
```python
# Calculate daily records for the full year
records = analyzer.calculate_daily_records(metric='TMAX')
analyzer.print_climate_band_report(records, 'TMAX')

# With year overlay
overlay = analyzer.get_year_overlay_data(year=2023, metric='TMAX')
analyzer.print_climate_band_report(records, 'TMAX', overlay_data=overlay, overlay_year=2023)

# Summer only
records = analyzer.calculate_daily_records(metric='TMAX', start_month=6, start_day=1, end_month=8, end_day=31)
overlay = analyzer.get_year_overlay_data(year=2023, metric='TMAX', start_month=6, start_day=1, end_month=8, end_day=31)
analyzer.print_climate_band_report(records, 'TMAX', overlay_data=overlay, overlay_year=2023)
```

**Output includes:**
- Summary: highest record high, lowest record low, warmest/coldest average days
- Sampled table of daily records (CLI)
- Overlay year comparison stats if provided
- In the GUI: interactive Plotly chart with shaded envelope, record lines, average line, and year overlay. Seasonal presets (Full Year, Winter, Spring, Summer, Fall, Custom) for quick date range selection.

---

## Using the GUI

The Streamlit GUI provides a visual interface for all 9 analysis types with interactive Plotly charts.

**To start:**
```
streamlit run app.py
```

If that gives a "not recognized" error, use:
```
python -m streamlit run app.py
```

**Features:**
1. **Data source**: Use the included Huntsville data or upload your own CSV
2. **Column mapping**: If uploading custom data, map your columns to expected names
3. **Analysis selector**: Choose from all 9 analysis types in the sidebar. A brief description appears below the dropdown to explain what each analysis does.
4. **Interactive forms**: Fill in parameters (metric, threshold, direction, dates, etc.) for each analysis type
5. **Results**: View formatted summary metrics, interactive Plotly charts with hover tooltips, and data tables
6. **Plotly charts**: The newer visualization features (Event Frequency, Freeze Dates, Heatmap, Daily Record Envelope) use interactive Plotly charts that support zooming, panning, and hover details

---

## Using the Command Line

The CLI supports all 9 analysis types with flexible options.

**General syntax:**
```
python temp_analysis.py <csv_file> <analysis_type> [options]
```

**Analysis type flags:**
| Flag | Analysis |
|------|----------|
| `--streak` | Temperature Streaks |
| `--period` | Extreme Periods |
| `--season` | Seasonal Analysis |
| `--date-range` | Custom Date Range |
| `--histogram` | Threshold Histogram |
| `--event-freq` | Extreme Event Frequency |
| `--freeze-dates` | Freeze Date Tracker |
| `--heatmap` | Temperature Heatmap |
| `--climate-band` | Daily Record Envelope |

**Common options:**
| Option | Description | Default |
|--------|-------------|---------|
| `--metric` | TMIN, TMAX, or TAVG | TMAX |
| `--threshold` | Temperature threshold (°F) | - |
| `--direction` | above or below | above |
| `--extreme` | coldest or warmest | coldest |
| `--days` | Period length for --period | 7 |
| `--top` | Number of results | 10 |
| `--heatmap-mode` | absolute or anomaly (for --heatmap) | absolute |
| `--overlay-year` | Year to overlay (for --climate-band) | - |
| `--band-range` | Date range M/D-M/D (for --climate-band) | full year |
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

# Original analysis methods
streaks = analyzer.find_streaks(metric='TMAX', threshold=90, direction='above', top_n=5)
periods = analyzer.find_extreme_periods(metric='TAVG', n_days=7, extreme='coldest', top_n=5)
seasons = analyzer.find_extreme_seasons(season='winter', metric='TAVG', extreme='coldest', top_n=5)
ranges = analyzer.find_extreme_date_range(12, 20, 12, 31, metric='TAVG', extreme='coldest', top_n=5)
histogram = analyzer.threshold_histogram(1, 1, 1, 31, metric='TMIN', threshold=32, direction='below')

# Visualization analysis methods
freq = analyzer.find_extreme_event_frequency(metric='TMAX', threshold=100, direction='above')
freezes = analyzer.find_freeze_dates(metric='TMIN', threshold=32.0)
heatmap = analyzer.create_temperature_heatmap(metric='TAVG', mode='anomaly')
records = analyzer.calculate_daily_records(metric='TMAX')
overlay = analyzer.get_year_overlay_data(year=2023, metric='TMAX')

# Print formatted reports
analyzer.print_streak_report(streaks, 'TMAX', 90, 'above')
analyzer.print_event_frequency_report(freq, 'TMAX', 100, 'above')
analyzer.print_freeze_dates_report(freezes, 'TMIN', 32.0)
analyzer.print_heatmap_report(heatmap, 'TAVG', 'anomaly')
analyzer.print_climate_band_report(records, 'TMAX', overlay_data=overlay, overlay_year=2023)

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
6. **Year-spanning ranges**: The Climate Band and Custom Date Range features handle ranges that cross the year boundary (e.g., Dec-Feb for winter)
7. **Interactive charts**: Plotly charts in the GUI support zooming, panning, and hover tooltips for detailed exploration
