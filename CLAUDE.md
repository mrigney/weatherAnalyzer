# Temperature Analysis Tool - Project Summary

## Overview
A Python tool for analyzing historical temperature data to find patterns, extremes, and trends. Supports command-line, Python API, and Streamlit GUI interfaces.

## Files

| File | Purpose |
|------|---------|
| `temp_analysis.py` | Core module with `TempAnalyzer` class and CLI |
| `app.py` | Streamlit web GUI |
| `examples.py` | Usage examples with CLI equivalents |
| `hsvWeather_112024.csv` | Sample data: 66+ years of Huntsville, AL weather (1958-2024) |

## Data Format
CSV with columns:
- `DATE` - Date (required)
- `TMAX` - Daily maximum temperature in °F (required)
- `TMIN` - Daily minimum temperature in °F (required)
- `TAVG` - Daily average temperature (optional, calculated from TMAX/TMIN if missing)

Column mapping supported for CSVs with different column names.

## Features

### 1. Temperature Streaks
Find longest consecutive periods where temperature stayed above/below a threshold.
```python
analyzer.find_streaks(metric='TMAX', threshold=95, direction='above', top_n=10)
```
CLI: `python temp_analysis.py data.csv --streak --metric TMAX --threshold 95 --direction above`

### 2. Extreme Periods
Find coldest/warmest N-day periods using rolling averages.
```python
analyzer.find_extreme_periods(metric='TAVG', n_days=7, extreme='coldest', top_n=10)
```
CLI: `python temp_analysis.py data.csv --period --metric TAVG --days 7 --extreme coldest`

### 3. Seasonal Analysis
Find coldest/warmest seasons across all years.
- Winter = Dec-Feb (Dec belongs to following year's winter)
- Spring = Mar-May
- Summer = Jun-Aug
- Fall = Sep-Nov

```python
analyzer.find_extreme_seasons(season='winter', metric='TAVG', extreme='coldest', top_n=10)
```
CLI: `python temp_analysis.py data.csv --season winter --extreme coldest`

### 4. Custom Date Range Analysis
Find coldest/warmest instances of any date range across all years. Supports year-spanning ranges (e.g., Dec 15 - Jan 15).
```python
analyzer.find_extreme_date_range(12, 20, 12, 31, metric='TAVG', extreme='coldest', top_n=10)
```
CLI: `python temp_analysis.py data.csv --date-range 12/20-12/31 --extreme coldest`

### 5. Threshold Histogram
Count how often temperature meets a threshold within a date range, broken down by year.
```python
result = analyzer.threshold_histogram(1, 1, 1, 31, metric='TMIN', threshold=32, direction='below')
# Returns {'summary': {...}, 'by_year': DataFrame}
```
CLI: `python temp_analysis.py data.csv --histogram 1/1-1/31 --metric TMIN --threshold 32 --direction below`

### 6. Extreme Event Frequency
Count days per year where temperature crosses a threshold, with trendline analysis.
```python
freq_data = analyzer.find_extreme_event_frequency(metric='TMAX', threshold=100, direction='above')
# Returns DataFrame with year, event_days, total_days, percentage
```
CLI: `python temp_analysis.py data.csv --event-freq --metric TMAX --threshold 100 --direction above`

### 7. Freeze Date Tracker
Track first fall freeze and last spring freeze dates, plus growing season length.
```python
freeze_data = analyzer.find_freeze_dates(metric='TMIN', threshold=32.0)
# Returns DataFrame with year, last_spring_freeze, first_fall_freeze, growing_season_days, spring_doy, fall_doy
```
CLI: `python temp_analysis.py data.csv --freeze-dates` (defaults to TMIN <= 32°F)

### 8. Temperature Heatmap
Year × month heatmap showing temperature patterns. Supports absolute values or anomaly (departure from long-term mean).
```python
heatmap = analyzer.create_temperature_heatmap(metric='TAVG', mode='anomaly')
# Returns pivoted DataFrame: index=year, columns=month names, values=avg temp or anomaly
```
CLI: `python temp_analysis.py data.csv --heatmap --metric TAVG --heatmap-mode anomaly`

### 9. Daily Record Envelope (Climate Band)
Daily record highs, lows, and long-term averages by day of year. Supports seasonal sub-selection and year overlay.
```python
records = analyzer.calculate_daily_records(metric='TMAX', start_month=6, start_day=1, end_month=8, end_day=31)
overlay = analyzer.get_year_overlay_data(year=2023, metric='TMAX')
```
CLI: `python temp_analysis.py data.csv --climate-band --metric TMAX --overlay-year 2023 --band-range 6/1-8/31`

## Running the Tool

### Command Line
```powershell
python temp_analysis.py hsvWeather_112024.csv --streak --threshold 90 --top 5
```

### Python API
```python
from temp_analysis import TempAnalyzer
analyzer = TempAnalyzer('hsvWeather_112024.csv')
streaks = analyzer.find_streaks(metric='TMAX', threshold=90)
```

### Streamlit GUI
```powershell
pip install streamlit  # if not installed
streamlit run app.py
```

## Column Mapping
For CSVs with non-standard column names:
```python
# Python
analyzer = TempAnalyzer('data.csv', column_map={'MaxTemp': 'TMAX', 'MinTemp': 'TMIN', 'Date': 'DATE'})
```
```bash
# CLI
python temp_analysis.py data.csv --streak --threshold 90 --map MaxTemp=TMAX MinTemp=TMIN Date=DATE
```

## Implementation Notes
- Uses pandas for data manipulation
- Rolling averages use `min_periods=n_days` to avoid partial windows
- Non-overlapping periods in extreme analysis to avoid redundant results
- Winter season handling: December belongs to the following year's winter (e.g., Dec 2023 → Winter 2023-24)
- Year-spanning date ranges supported in both date-range and histogram features
- Histogram uses '#' character for bars (Windows-compatible)

## Dependencies
- pandas
- numpy
- streamlit (for GUI only)
- plotly (for interactive charts in GUI)
