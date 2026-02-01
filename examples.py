#!/usr/bin/env python3
"""
Example usage of temperature analyzer for interactive queries.

Each example includes the equivalent command-line invocation as a comment.
"""

from temp_analysis import TempAnalyzer

# Load your data
analyzer = TempAnalyzer('hsvWeather_112024.csv')

print(f"Data loaded: {len(analyzer.df)} records")
print(f"Date range: {analyzer.df['DATE'].min()} to {analyzer.df['DATE'].max()}\n")

# Example 1: Find longest heat waves (TMAX >= 95°F)
# CLI: python temp_analysis.py hsvWeather_112024.csv --streak --metric TMAX --threshold 95 --direction above --top 3
print("="*80)
print("Example 1: Longest heat waves (TMAX >= 95°F)")
print("="*80)
streaks = analyzer.find_streaks(metric='TMAX', threshold=95, direction='above', top_n=3)
analyzer.print_streak_report(streaks, 'TMAX', 95, 'above')

# Example 2: Coldest 10-day periods
# CLI: python temp_analysis.py hsvWeather_112024.csv --period --metric TAVG --days 10 --extreme coldest --top 3
print("="*80)
print("Example 2: Coldest 10-day periods (TAVG)")
print("="*80)
periods = analyzer.find_extreme_periods(metric='TAVG', n_days=10, extreme='coldest', top_n=3)
analyzer.print_period_report(periods, 'TAVG', 10, 'coldest')

# Example 3: Longest freezing streaks (TMIN <= 32°F)
# CLI: python temp_analysis.py hsvWeather_112024.csv --streak --metric TMIN --threshold 32 --direction below --top 3
print("="*80)
print("Example 3: Longest freezing streaks (TMIN <= 32°F)")
print("="*80)
freezes = analyzer.find_streaks(metric='TMIN', threshold=32, direction='below', top_n=3)
analyzer.print_streak_report(freezes, 'TMIN', 32, 'below')

# Example 4: Warmest weeks (7-day periods)
# CLI: python temp_analysis.py hsvWeather_112024.csv --period --metric TMAX --days 7 --extreme warmest --top 3
print("="*80)
print("Example 4: Warmest 7-day periods (TMAX)")
print("="*80)
hot_weeks = analyzer.find_extreme_periods(metric='TMAX', n_days=7, extreme='warmest', top_n=3)
analyzer.print_period_report(hot_weeks, 'TMAX', 7, 'warmest')

# Example 5: Coldest winters
# CLI: python temp_analysis.py hsvWeather_112024.csv --season winter --metric TAVG --extreme coldest --top 5
print("="*80)
print("Example 5: Top 5 coldest winters (TAVG)")
print("="*80)
winters = analyzer.find_extreme_seasons(season='winter', metric='TAVG', extreme='coldest', top_n=5)
analyzer.print_season_report(winters, 'winter', 'TAVG', 'coldest')

# Example 6: Warmest summers
# CLI: python temp_analysis.py hsvWeather_112024.csv --season summer --metric TMAX --extreme warmest --top 5
print("="*80)
print("Example 6: Top 5 warmest summers (TMAX)")
print("="*80)
summers = analyzer.find_extreme_seasons(season='summer', metric='TMAX', extreme='warmest', top_n=5)
analyzer.print_season_report(summers, 'summer', 'TMAX', 'warmest')

# Example 7: Coldest Christmas weeks (Dec 20 - Dec 31)
# CLI: python temp_analysis.py hsvWeather_112024.csv --date-range 12/20-12/31 --metric TAVG --extreme coldest --top 5
print("="*80)
print("Example 7: Coldest Christmas weeks (Dec 20 - Dec 31)")
print("="*80)
christmas = analyzer.find_extreme_date_range(12, 20, 12, 31, metric='TAVG', extreme='coldest', top_n=5)
analyzer.print_date_range_report(christmas, 12, 20, 12, 31, 'TAVG', 'coldest')

# Example 8: Histogram - How often does it freeze in January?
# CLI: python temp_analysis.py hsvWeather_112024.csv --histogram 1/1-1/31 --metric TMIN --threshold 32 --direction below
print("="*80)
print("Example 8: Freezing days histogram for January (TMIN <= 32°F)")
print("="*80)
histogram = analyzer.threshold_histogram(1, 1, 1, 31, metric='TMIN', threshold=32, direction='below')
analyzer.print_histogram_report(histogram, 1, 1, 1, 31, 'TMIN', 32, 'below')

print("\n" + "="*80)
print("You can modify this script or use temp_analysis.py from the command line!")
print("="*80)
