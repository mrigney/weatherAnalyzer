#!/usr/bin/env python3
"""
Temperature Analysis Utility
Analyzes temperature streaks and extreme periods from historical weather data.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Literal, Optional


class TempAnalyzer:
    """Analyze temperature records for streaks and extreme periods."""

    REQUIRED_COLUMNS = ['DATE', 'TMAX', 'TMIN']

    def __init__(self, csv_path: str, column_map: Optional[dict] = None):
        """
        Load temperature data from CSV.

        Args:
            csv_path: Path to CSV file
            column_map: Optional mapping from your CSV column names to expected names.
                        e.g., {'Max_Temp': 'TMAX', 'Min_Temp': 'TMIN', 'Date': 'DATE'}
                        Expected column names: DATE, TMAX, TMIN (TAVG is optional)
        """
        self.df = pd.read_csv(csv_path)

        # Apply column mapping if provided
        if column_map:
            self.df = self.df.rename(columns=column_map)

        # Validate required columns exist
        missing_cols = [col for col in self.REQUIRED_COLUMNS if col not in self.df.columns]
        if missing_cols:
            available_cols = ', '.join(self.df.columns.tolist())
            missing_str = ', '.join(missing_cols)
            raise ValueError(
                f"Missing required columns: {missing_str}\n"
                f"Available columns: {available_cols}\n"
                f"Use column_map parameter to map your column names, e.g.:\n"
                f"  TempAnalyzer('file.csv', column_map={{'YourDateCol': 'DATE', 'YourMaxCol': 'TMAX', 'YourMinCol': 'TMIN'}})"
            )

        self.df['DATE'] = pd.to_datetime(self.df['DATE'])
        self.df = self.df.sort_values('DATE').reset_index(drop=True)

        # Calculate mean if not present or has NaN values
        if 'TAVG' not in self.df.columns or self.df['TAVG'].isna().any():
            self.df['TAVG'] = (self.df['TMAX'] + self.df['TMIN']) / 2
    
    def find_streaks(self, 
                     metric: Literal['TMIN', 'TMAX', 'TAVG'] = 'TMAX',
                     threshold: float = 90.0,
                     direction: Literal['above', 'below'] = 'above',
                     top_n: int = 10) -> pd.DataFrame:
        """
        Find longest temperature streaks.
        
        Args:
            metric: Temperature metric to analyze ('TMIN', 'TMAX', 'TAVG')
            threshold: Temperature threshold in Fahrenheit
            direction: 'above' or 'below' threshold
            top_n: Number of top streaks to return
            
        Returns:
            DataFrame with streak information
        """
        # Create boolean mask for threshold condition
        if direction == 'above':
            mask = self.df[metric] >= threshold
        else:
            mask = self.df[metric] <= threshold
        
        # Identify streak groups
        streak_id = (mask != mask.shift()).cumsum()
        
        # Filter only streaks that meet the condition
        streaks = self.df[mask].copy()
        streaks['streak_id'] = streak_id[mask]
        
        # Calculate streak statistics
        streak_stats = streaks.groupby('streak_id').agg({
            'DATE': ['first', 'last', 'count'],
            metric: ['mean', 'min', 'max']
        }).reset_index()
        
        # Flatten column names
        streak_stats.columns = ['streak_id', 'start_date', 'end_date', 'length',
                                'avg_temp', 'min_temp', 'max_temp']
        
        # Sort by length and return top N
        streak_stats = streak_stats.sort_values('length', ascending=False).head(top_n)
        streak_stats = streak_stats.reset_index(drop=True)
        
        return streak_stats
    
    def find_extreme_periods(self,
                            metric: Literal['TMIN', 'TMAX', 'TAVG'] = 'TAVG',
                            n_days: int = 7,
                            extreme: Literal['coldest', 'warmest'] = 'coldest',
                            top_n: int = 10) -> pd.DataFrame:
        """
        Find coldest or warmest n-day periods.
        
        Args:
            metric: Temperature metric to analyze ('TMIN', 'TMAX', 'TAVG')
            n_days: Number of days in the period
            extreme: 'coldest' or 'warmest'
            top_n: Number of top periods to return
            
        Returns:
            DataFrame with period information
        """
        # Calculate rolling average
        rolling_avg = self.df[metric].rolling(window=n_days, min_periods=n_days).mean()
        
        # Sort to find extremes (excluding NA values)
        valid_mask = rolling_avg.notna()
        valid_indices = np.where(valid_mask)[0]
        valid_values = rolling_avg.iloc[valid_indices].values

        if extreme == 'coldest':
            order = np.argsort(valid_values)
        else:
            order = np.argsort(valid_values)[::-1]
        sorted_indices = valid_indices[order]
        
        # Collect non-overlapping periods
        periods = []
        used_dates = set()
        
        for idx in sorted_indices:
            if pd.isna(rolling_avg.iloc[idx]):
                continue
                
            # Get date range for this period
            start_idx = idx - n_days + 1
            end_idx = idx
            
            if start_idx < 0:
                continue
            
            date_range = range(start_idx, end_idx + 1)
            
            # Check if any dates in this period are already used
            if any(i in used_dates for i in date_range):
                continue
            
            # Add this period
            start_date = self.df.loc[start_idx, 'DATE']
            end_date = self.df.loc[end_idx, 'DATE']
            avg_temp = rolling_avg.iloc[idx]
            
            period_temps = self.df.loc[start_idx:end_idx, metric]
            min_temp = period_temps.min()
            max_temp = period_temps.max()
            
            periods.append({
                'start_date': start_date,
                'end_date': end_date,
                'avg_temp': avg_temp,
                'min_temp': min_temp,
                'max_temp': max_temp,
                'length': n_days
            })
            
            # Mark these dates as used
            used_dates.update(date_range)
            
            if len(periods) >= top_n:
                break
        
        return pd.DataFrame(periods)

    # Season definitions: month -> (season_name, year_offset)
    # year_offset is used for winter so Dec belongs to the following winter
    SEASONS = {
        12: ('winter', 1), 1: ('winter', 0), 2: ('winter', 0),
        3: ('spring', 0), 4: ('spring', 0), 5: ('spring', 0),
        6: ('summer', 0), 7: ('summer', 0), 8: ('summer', 0),
        9: ('fall', 0), 10: ('fall', 0), 11: ('fall', 0)
    }

    def find_extreme_seasons(self,
                             season: Literal['winter', 'spring', 'summer', 'fall'],
                             metric: Literal['TMIN', 'TMAX', 'TAVG'] = 'TAVG',
                             extreme: Literal['coldest', 'warmest'] = 'coldest',
                             top_n: int = 10) -> pd.DataFrame:
        """
        Find coldest or warmest seasons.

        Args:
            season: Season to analyze ('winter', 'spring', 'summer', 'fall')
            metric: Temperature metric to analyze ('TMIN', 'TMAX', 'TAVG')
            extreme: 'coldest' or 'warmest'
            top_n: Number of top seasons to return

        Returns:
            DataFrame with season information (year, avg_temp, min_temp, max_temp, days)
        """
        df = self.df.copy()
        df['month'] = df['DATE'].dt.month
        df['year'] = df['DATE'].dt.year

        # Assign season and season_year (for winter, Dec belongs to next year's winter)
        df['season'] = df['month'].map(lambda m: self.SEASONS[m][0])
        df['season_year'] = df.apply(
            lambda row: row['year'] + self.SEASONS[row['month']][1], axis=1
        )

        # Filter to requested season
        season_df = df[df['season'] == season].copy()

        # Group by season_year and calculate stats
        season_stats = season_df.groupby('season_year').agg({
            metric: ['mean', 'min', 'max', 'count'],
            'DATE': ['min', 'max']
        }).reset_index()

        season_stats.columns = ['season_year', 'avg_temp', 'min_temp', 'max_temp',
                                'days', 'start_date', 'end_date']

        # Sort by average temp
        ascending = (extreme == 'coldest')
        season_stats = season_stats.sort_values('avg_temp', ascending=ascending).head(top_n)
        season_stats = season_stats.reset_index(drop=True)

        return season_stats

    def find_extreme_date_range(self,
                                start_month: int, start_day: int,
                                end_month: int, end_day: int,
                                metric: Literal['TMIN', 'TMAX', 'TAVG'] = 'TAVG',
                                extreme: Literal['coldest', 'warmest'] = 'coldest',
                                top_n: int = 10) -> pd.DataFrame:
        """
        Find coldest or warmest instances of a custom date range across all years.

        Args:
            start_month: Start month (1-12)
            start_day: Start day of month
            end_month: End month (1-12)
            end_day: End day of month
            metric: Temperature metric to analyze ('TMIN', 'TMAX', 'TAVG')
            extreme: 'coldest' or 'warmest'
            top_n: Number of top years to return

        Returns:
            DataFrame with year, avg_temp, min_temp, max_temp, days for each year
        """
        df = self.df.copy()
        df['month'] = df['DATE'].dt.month
        df['day'] = df['DATE'].dt.day
        df['year'] = df['DATE'].dt.year

        # Handle ranges that span year boundary (e.g., Dec 15 - Jan 15)
        spans_year = (start_month > end_month) or (start_month == end_month and start_day > end_day)

        if spans_year:
            # For year-spanning ranges, assign to the year of the start
            mask = ((df['month'] > start_month) |
                    ((df['month'] == start_month) & (df['day'] >= start_day)) |
                    (df['month'] < end_month) |
                    ((df['month'] == end_month) & (df['day'] <= end_day)))
            # Assign range_year: if in start portion, use that year; if in end portion, use previous year
            df['range_year'] = df.apply(
                lambda row: row['year'] if (row['month'] > start_month or
                    (row['month'] == start_month and row['day'] >= start_day))
                else row['year'] - 1, axis=1
            )
        else:
            # Simple case: range within same year
            mask = (((df['month'] > start_month) |
                     ((df['month'] == start_month) & (df['day'] >= start_day))) &
                    ((df['month'] < end_month) |
                     ((df['month'] == end_month) & (df['day'] <= end_day))))
            df['range_year'] = df['year']

        range_df = df[mask].copy()

        # Group by range_year and calculate stats
        range_stats = range_df.groupby('range_year').agg({
            metric: ['mean', 'min', 'max', 'count'],
            'DATE': ['min', 'max']
        }).reset_index()

        range_stats.columns = ['year', 'avg_temp', 'min_temp', 'max_temp',
                               'days', 'start_date', 'end_date']

        # Sort by average temp
        ascending = (extreme == 'coldest')
        range_stats = range_stats.sort_values('avg_temp', ascending=ascending).head(top_n)
        range_stats = range_stats.reset_index(drop=True)

        return range_stats

    def threshold_histogram(self,
                           start_month: int, start_day: int,
                           end_month: int, end_day: int,
                           metric: Literal['TMIN', 'TMAX', 'TAVG'] = 'TMIN',
                           threshold: float = 32.0,
                           direction: Literal['above', 'below'] = 'below') -> dict:
        """
        Analyze how often a threshold is met within a date range across all years.

        Args:
            start_month: Start month (1-12)
            start_day: Start day of month
            end_month: End month (1-12)
            end_day: End day of month
            metric: Temperature metric to analyze ('TMIN', 'TMAX', 'TAVG')
            threshold: Temperature threshold in Fahrenheit
            direction: 'above' or 'below' threshold

        Returns:
            Dictionary with 'summary' (stats) and 'by_year' (DataFrame with year-by-year counts)
        """
        df = self.df.copy()
        df['month'] = df['DATE'].dt.month
        df['day'] = df['DATE'].dt.day
        df['year'] = df['DATE'].dt.year

        # Handle ranges that span year boundary
        spans_year = (start_month > end_month) or (start_month == end_month and start_day > end_day)

        if spans_year:
            mask = ((df['month'] > start_month) |
                    ((df['month'] == start_month) & (df['day'] >= start_day)) |
                    (df['month'] < end_month) |
                    ((df['month'] == end_month) & (df['day'] <= end_day)))
            df['range_year'] = df.apply(
                lambda row: row['year'] if (row['month'] > start_month or
                    (row['month'] == start_month and row['day'] >= start_day))
                else row['year'] - 1, axis=1
            )
        else:
            mask = (((df['month'] > start_month) |
                     ((df['month'] == start_month) & (df['day'] >= start_day))) &
                    ((df['month'] < end_month) |
                     ((df['month'] == end_month) & (df['day'] <= end_day))))
            df['range_year'] = df['year']

        range_df = df[mask].copy()

        # Apply threshold condition
        if direction == 'above':
            range_df['meets_threshold'] = range_df[metric] >= threshold
        else:
            range_df['meets_threshold'] = range_df[metric] <= threshold

        # Count days meeting threshold per year, and total days per year
        year_stats = range_df.groupby('range_year').agg({
            'meets_threshold': 'sum',
            'DATE': 'count'
        }).reset_index()
        year_stats.columns = ['year', 'days_meeting_threshold', 'total_days']
        year_stats['percentage'] = (year_stats['days_meeting_threshold'] / year_stats['total_days'] * 100).round(1)

        # Calculate summary statistics
        summary = {
            'avg_days': year_stats['days_meeting_threshold'].mean(),
            'min_days': year_stats['days_meeting_threshold'].min(),
            'max_days': year_stats['days_meeting_threshold'].max(),
            'std_days': year_stats['days_meeting_threshold'].std(),
            'total_years': len(year_stats),
            'avg_percentage': year_stats['percentage'].mean()
        }

        return {
            'summary': summary,
            'by_year': year_stats.sort_values('year', ascending=False).reset_index(drop=True)
        }

    def print_streak_report(self, streaks: pd.DataFrame, metric: str,
                           threshold: float, direction: str):
        """Print formatted streak report."""
        print(f"\n{'='*80}")
        print(f"TEMPERATURE STREAKS: {metric} {direction} {threshold}°F")
        print(f"{'='*80}\n")
        
        for idx, row in streaks.iterrows():
            print(f"Rank #{idx + 1}: {row['length']} days")
            print(f"  Period: {row['start_date'].strftime('%Y-%m-%d')} to "
                  f"{row['end_date'].strftime('%Y-%m-%d')}")
            print(f"  Temps:  Avg={row['avg_temp']:.1f}°F  "
                  f"Min={row['min_temp']:.1f}°F  Max={row['max_temp']:.1f}°F")
            print()
    
    def print_period_report(self, periods: pd.DataFrame, metric: str,
                           n_days: int, extreme: str):
        """Print formatted extreme period report."""
        print(f"\n{'='*80}")
        print(f"{extreme.upper()} {n_days}-DAY PERIODS: {metric}")
        print(f"{'='*80}\n")

        for idx, row in periods.iterrows():
            print(f"Rank #{idx + 1}: {row['avg_temp']:.1f}°F average")
            print(f"  Period: {row['start_date'].strftime('%Y-%m-%d')} to "
                  f"{row['end_date'].strftime('%Y-%m-%d')}")
            print(f"  Range:  Min={row['min_temp']:.1f}°F  Max={row['max_temp']:.1f}°F")
            print()

    def print_season_report(self, seasons: pd.DataFrame, season: str,
                           metric: str, extreme: str):
        """Print formatted seasonal analysis report."""
        print(f"\n{'='*80}")
        print(f"{extreme.upper()} {season.upper()}S: {metric}")
        print(f"{'='*80}\n")

        for idx, row in seasons.iterrows():
            # Format season year label (e.g., "Winter 2023-24" for winter)
            if season == 'winter':
                year_label = f"{int(row['season_year'])-1}-{str(int(row['season_year']))[-2:]}"
            else:
                year_label = str(int(row['season_year']))

            print(f"Rank #{idx + 1}: {season.capitalize()} {year_label}")
            print(f"  Average: {row['avg_temp']:.1f}°F")
            print(f"  Range:   Min={row['min_temp']:.1f}°F  Max={row['max_temp']:.1f}°F")
            print(f"  Period:  {row['start_date'].strftime('%Y-%m-%d')} to "
                  f"{row['end_date'].strftime('%Y-%m-%d')} ({int(row['days'])} days)")
            print()

    def print_date_range_report(self, ranges: pd.DataFrame,
                                start_month: int, start_day: int,
                                end_month: int, end_day: int,
                                metric: str, extreme: str):
        """Print formatted custom date range report."""
        # Format date range string
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        range_str = f"{months[start_month-1]} {start_day} - {months[end_month-1]} {end_day}"

        print(f"\n{'='*80}")
        print(f"{extreme.upper()} {range_str} PERIODS: {metric}")
        print(f"{'='*80}\n")

        for idx, row in ranges.iterrows():
            print(f"Rank #{idx + 1}: {int(row['year'])}")
            print(f"  Average: {row['avg_temp']:.1f}°F")
            print(f"  Range:   Min={row['min_temp']:.1f}°F  Max={row['max_temp']:.1f}°F")
            print(f"  Period:  {row['start_date'].strftime('%Y-%m-%d')} to "
                  f"{row['end_date'].strftime('%Y-%m-%d')} ({int(row['days'])} days)")
            print()

    def print_histogram_report(self, result: dict,
                               start_month: int, start_day: int,
                               end_month: int, end_day: int,
                               metric: str, threshold: float, direction: str):
        """Print formatted threshold histogram report."""
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        range_str = f"{months[start_month-1]} {start_day} - {months[end_month-1]} {end_day}"
        dir_symbol = '<=' if direction == 'below' else '>='

        summary = result['summary']
        by_year = result['by_year']

        print(f"\n{'='*80}")
        print(f"THRESHOLD ANALYSIS: {metric} {dir_symbol} {threshold}°F for {range_str}")
        print(f"{'='*80}\n")

        print("SUMMARY")
        print("-" * 40)
        print(f"  Average:  {summary['avg_days']:.1f} days/year ({summary['avg_percentage']:.1f}%)")
        print(f"  Minimum:  {int(summary['min_days'])} days")
        print(f"  Maximum:  {int(summary['max_days'])} days")
        print(f"  Std Dev:  {summary['std_days']:.1f} days")
        print(f"  Years:    {summary['total_years']}")
        print()

        print("YEAR-BY-YEAR")
        print("-" * 40)

        # Calculate bar scale
        max_days = by_year['days_meeting_threshold'].max()
        bar_width = 30

        for _, row in by_year.iterrows():
            days = int(row['days_meeting_threshold'])
            pct = row['percentage']
            bar_len = int((days / max_days) * bar_width) if max_days > 0 else 0
            bar = '#' * bar_len
            print(f"  {int(row['year'])}: {days:3d} days ({pct:5.1f}%)  {bar}")
        print()


def main():
    """Example usage and interactive queries."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Analyze temperature streaks and extreme periods',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Find longest streaks above 90°F
  python temp_analysis.py data.csv --streak --metric TMAX --threshold 90 --direction above

  # Find coldest 7-day periods
  python temp_analysis.py data.csv --period --metric TAVG --days 7 --extreme coldest

  # Find top 10 coldest winters
  python temp_analysis.py data.csv --season winter --extreme coldest

  # Find top 5 warmest summers
  python temp_analysis.py data.csv --season summer --extreme warmest --top 5

  # Find coldest Jan 3 - Jan 20 periods across all years
  python temp_analysis.py data.csv --date-range 1/3-1/20 --extreme coldest

  # Histogram: how often does TMIN drop below 32°F in January?
  python temp_analysis.py data.csv --histogram 1/1-1/31 --threshold 32 --direction below --metric TMIN

  # Use custom column names from your CSV
  python temp_analysis.py data.csv --streak --threshold 90 --map Date=DATE MaxTemp=TMAX MinTemp=TMIN
        """)
    
    parser.add_argument('csv_file', help='Path to weather CSV file')
    parser.add_argument('--map', nargs='*', metavar='SRC=DST',
                       help='Map column names: SRC=DST (e.g., MaxTemp=TMAX MinTemp=TMIN Date=DATE)')
    parser.add_argument('--streak', action='store_true', help='Find temperature streaks')
    parser.add_argument('--period', action='store_true', help='Find extreme periods')
    parser.add_argument('--season', choices=['winter', 'spring', 'summer', 'fall'],
                       help='Find extreme seasons (winter=Dec-Feb, spring=Mar-May, summer=Jun-Aug, fall=Sep-Nov)')
    parser.add_argument('--date-range', metavar='M/D-M/D',
                       help='Find extremes for custom date range (e.g., 1/3-1/20)')
    parser.add_argument('--histogram', metavar='M/D-M/D',
                       help='Threshold histogram for date range (e.g., 1/1-1/31)')
    parser.add_argument('--metric', choices=['TMIN', 'TMAX', 'TAVG'], default='TMAX',
                       help='Temperature metric (default: TMAX)')
    parser.add_argument('--threshold', type=float, help='Temperature threshold for streaks/histogram')
    parser.add_argument('--direction', choices=['above', 'below'], default='above',
                       help='Threshold direction (default: above)')
    parser.add_argument('--days', type=int, default=7,
                       help='Number of days for period analysis (default: 7)')
    parser.add_argument('--extreme', choices=['coldest', 'warmest'], default='coldest',
                       help='Type of extreme (default: coldest)')
    parser.add_argument('--top', type=int, default=10,
                       help='Number of results to show (default: 10)')
    
    args = parser.parse_args()
    
    # Parse column mapping if provided
    column_map = None
    if args.map:
        column_map = {}
        for mapping in args.map:
            if '=' not in mapping:
                parser.error(f"Invalid mapping format: '{mapping}'. Use SRC=DST format.")
            src, dst = mapping.split('=', 1)
            column_map[src] = dst

    # Load data
    print(f"Loading data from {args.csv_file}...")
    analyzer = TempAnalyzer(args.csv_file, column_map=column_map)
    print(f"Loaded {len(analyzer.df)} records from "
          f"{analyzer.df['DATE'].min().strftime('%Y-%m-%d')} to "
          f"{analyzer.df['DATE'].max().strftime('%Y-%m-%d')}")
    
    # Helper to parse date range strings like "1/3-1/20"
    def parse_date_range(date_str):
        try:
            start, end = date_str.split('-')
            start_month, start_day = map(int, start.split('/'))
            end_month, end_day = map(int, end.split('/'))
            return start_month, start_day, end_month, end_day
        except ValueError:
            parser.error(f"Invalid date range format: '{date_str}'. Use M/D-M/D (e.g., 1/3-1/20)")

    # Track if any analysis was run
    ran_analysis = False

    # Run analyses
    if args.streak:
        if args.threshold is None:
            parser.error("--threshold required for streak analysis")

        streaks = analyzer.find_streaks(
            metric=args.metric,
            threshold=args.threshold,
            direction=args.direction,
            top_n=args.top
        )
        analyzer.print_streak_report(streaks, args.metric, args.threshold, args.direction)
        ran_analysis = True

    if args.period:
        periods = analyzer.find_extreme_periods(
            metric=args.metric,
            n_days=args.days,
            extreme=args.extreme,
            top_n=args.top
        )
        analyzer.print_period_report(periods, args.metric, args.days, args.extreme)
        ran_analysis = True

    if args.season:
        seasons = analyzer.find_extreme_seasons(
            season=args.season,
            metric=args.metric,
            extreme=args.extreme,
            top_n=args.top
        )
        analyzer.print_season_report(seasons, args.season, args.metric, args.extreme)
        ran_analysis = True

    if args.date_range:
        start_month, start_day, end_month, end_day = parse_date_range(args.date_range)
        ranges = analyzer.find_extreme_date_range(
            start_month=start_month,
            start_day=start_day,
            end_month=end_month,
            end_day=end_day,
            metric=args.metric,
            extreme=args.extreme,
            top_n=args.top
        )
        analyzer.print_date_range_report(ranges, start_month, start_day, end_month, end_day,
                                         args.metric, args.extreme)
        ran_analysis = True

    if args.histogram:
        if args.threshold is None:
            parser.error("--threshold required for histogram analysis")
        start_month, start_day, end_month, end_day = parse_date_range(args.histogram)
        result = analyzer.threshold_histogram(
            start_month=start_month,
            start_day=start_day,
            end_month=end_month,
            end_day=end_day,
            metric=args.metric,
            threshold=args.threshold,
            direction=args.direction
        )
        analyzer.print_histogram_report(result, start_month, start_day, end_month, end_day,
                                        args.metric, args.threshold, args.direction)
        ran_analysis = True

    if not ran_analysis:
        parser.print_help()


if __name__ == '__main__':
    main()
