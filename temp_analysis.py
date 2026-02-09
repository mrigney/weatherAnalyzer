#!/usr/bin/env python3
"""
Temperature Analysis Utility
Analyzes temperature streaks and extreme periods from historical weather data.
"""

import sys
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

        # Filter out rows with missing TMAX or TMIN
        self.original_count = len(self.df)
        self.df = self.df.dropna(subset=['TMAX', 'TMIN'])
        self.dropped_count = self.original_count - len(self.df)

        if self.dropped_count > 0:
            print(f"Note: Dropped {self.dropped_count:,} rows with missing temperature data "
                  f"({self.dropped_count/self.original_count*100:.1f}% of {self.original_count:,} total rows)")

        if len(self.df) == 0:
            raise ValueError("No valid temperature data found after filtering out missing values.")

        self.df = self.df.reset_index(drop=True)

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

    def find_extreme_event_frequency(self,
                                    metric: Literal['TMIN', 'TMAX', 'TAVG'] = 'TMAX',
                                    threshold: float = 100.0,
                                    direction: Literal['above', 'below'] = 'above') -> pd.DataFrame:
        """
        Count days per year where temperature meets a threshold.

        Args:
            metric: Temperature metric to analyze ('TMIN', 'TMAX', 'TAVG')
            threshold: Temperature threshold in Fahrenheit
            direction: 'above' (>=) or 'below' (<=) threshold

        Returns:
            DataFrame with columns: year, event_days, total_days, percentage
            Sorted by year ascending
        """
        df = self.df.copy()
        df['year'] = df['DATE'].dt.year

        if direction == 'above':
            df['meets_threshold'] = df[metric] >= threshold
        else:
            df['meets_threshold'] = df[metric] <= threshold

        year_stats = df.groupby('year').agg({
            'meets_threshold': 'sum',
            'DATE': 'count'
        }).reset_index()
        year_stats.columns = ['year', 'event_days', 'total_days']
        year_stats['event_days'] = year_stats['event_days'].astype(int)
        year_stats['percentage'] = (year_stats['event_days'] / year_stats['total_days'] * 100).round(1)

        return year_stats.sort_values('year').reset_index(drop=True)

    def find_freeze_dates(self,
                         metric: Literal['TMIN', 'TMAX', 'TAVG'] = 'TMIN',
                         threshold: float = 32.0) -> pd.DataFrame:
        """
        Find first fall freeze and last spring freeze for each year.

        Args:
            metric: Temperature metric to analyze ('TMIN', 'TMAX', 'TAVG')
            threshold: Freeze threshold in Fahrenheit (default: 32.0)

        Returns:
            DataFrame with columns: year, last_spring_freeze, first_fall_freeze,
                                    growing_season_days, spring_doy, fall_doy
            Sorted by year ascending
        """
        df = self.df.copy()
        df['year'] = df['DATE'].dt.year
        df['month'] = df['DATE'].dt.month
        df['doy'] = df['DATE'].dt.dayofyear

        freeze_days = df[df[metric] <= threshold]

        results = []
        for year in sorted(df['year'].unique()):
            year_freezes = freeze_days[freeze_days['year'] == year]

            # Last spring freeze: latest freeze date before July 1
            spring = year_freezes[year_freezes['month'] < 7]
            last_spring = spring['DATE'].max() if len(spring) > 0 else pd.NaT
            spring_doy = spring['doy'].max() if len(spring) > 0 else np.nan

            # First fall freeze: earliest freeze date on/after July 1
            fall = year_freezes[year_freezes['month'] >= 7]
            first_fall = fall['DATE'].min() if len(fall) > 0 else pd.NaT
            fall_doy = fall['doy'].min() if len(fall) > 0 else np.nan

            # Growing season length
            if pd.notna(last_spring) and pd.notna(first_fall):
                growing_days = (first_fall - last_spring).days
            else:
                growing_days = np.nan

            results.append({
                'year': year,
                'last_spring_freeze': last_spring,
                'first_fall_freeze': first_fall,
                'growing_season_days': growing_days,
                'spring_doy': spring_doy,
                'fall_doy': fall_doy
            })

        return pd.DataFrame(results)

    def create_temperature_heatmap(self,
                                   metric: Literal['TMIN', 'TMAX', 'TAVG'] = 'TAVG',
                                   mode: Literal['absolute', 'anomaly'] = 'absolute') -> pd.DataFrame:
        """
        Create temperature heatmap data: years vs months.

        Args:
            metric: Temperature metric to analyze ('TMIN', 'TMAX', 'TAVG')
            mode: 'absolute' for actual temps or 'anomaly' for departure from long-term mean

        Returns:
            DataFrame with years as index and month names as columns.
            Values are average temperatures or anomalies.
        """
        df = self.df.copy()
        df['year'] = df['DATE'].dt.year
        df['month'] = df['DATE'].dt.month

        monthly = df.groupby(['year', 'month'])[metric].mean().reset_index()
        pivot = monthly.pivot(index='year', columns='month', values=metric)

        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        pivot.columns = [month_names[m - 1] for m in pivot.columns]

        if mode == 'anomaly':
            long_term_means = pivot.mean()
            pivot = pivot - long_term_means

        return pivot

    def calculate_daily_records(self,
                                metric: Literal['TMIN', 'TMAX', 'TAVG'] = 'TMAX',
                                start_month: int = None,
                                start_day: int = None,
                                end_month: int = None,
                                end_day: int = None) -> pd.DataFrame:
        """
        Calculate daily record highs, lows, and averages for each day of year.

        Args:
            metric: Temperature metric to analyze ('TMIN', 'TMAX', 'TAVG')
            start_month: Optional start month (1-12) for seasonal filtering
            start_day: Optional start day for seasonal filtering
            end_month: Optional end month (1-12) for seasonal filtering
            end_day: Optional end day for seasonal filtering

        Returns:
            DataFrame with columns: day_of_year, month, day, record_high,
                                    record_low, avg_temp, date_label
        """
        df = self.df.copy()
        df['month'] = df['DATE'].dt.month
        df['day'] = df['DATE'].dt.day
        df['day_of_year'] = df['DATE'].dt.dayofyear

        # Apply seasonal filter if provided
        if start_month is not None and end_month is not None:
            spans_year = (start_month > end_month) or (start_month == end_month and start_day > end_day)
            if spans_year:
                mask = ((df['month'] > start_month) |
                        ((df['month'] == start_month) & (df['day'] >= start_day)) |
                        (df['month'] < end_month) |
                        ((df['month'] == end_month) & (df['day'] <= end_day)))
            else:
                mask = (((df['month'] > start_month) |
                         ((df['month'] == start_month) & (df['day'] >= start_day))) &
                        ((df['month'] < end_month) |
                         ((df['month'] == end_month) & (df['day'] <= end_day))))
            df = df[mask]

        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

        daily = df.groupby(['month', 'day']).agg({
            metric: ['max', 'min', 'mean'],
            'day_of_year': 'first'
        }).reset_index()
        daily.columns = ['month', 'day', 'record_high', 'record_low', 'avg_temp', 'day_of_year']
        daily['date_label'] = daily.apply(lambda r: f"{months[int(r['month'])-1]} {int(r['day'])}", axis=1)

        # For year-spanning ranges, shift "after new year" days so they plot contiguously
        if start_month is not None and end_month is not None:
            spans_year = (start_month > end_month) or (start_month == end_month and start_day > end_day)
            if spans_year:
                daily['plot_x'] = daily.apply(
                    lambda r: r['day_of_year'] + 365 if r['month'] <= end_month else r['day_of_year'], axis=1)
            else:
                daily['plot_x'] = daily['day_of_year']
        else:
            daily['plot_x'] = daily['day_of_year']

        return daily.sort_values('plot_x').reset_index(drop=True)

    def get_year_overlay_data(self,
                              year: int,
                              metric: Literal['TMIN', 'TMAX', 'TAVG'] = 'TMAX',
                              start_month: int = None,
                              start_day: int = None,
                              end_month: int = None,
                              end_day: int = None) -> pd.DataFrame:
        """
        Get daily temperature data for a specific year to overlay on climate band.

        Args:
            year: Year to extract
            metric: Temperature metric
            start_month/start_day/end_month/end_day: Optional seasonal filter

        Returns:
            DataFrame with columns: day_of_year, month, day, temp, date_label
        """
        df = self.df.copy()
        df['month'] = df['DATE'].dt.month
        df['day'] = df['DATE'].dt.day
        df['day_of_year'] = df['DATE'].dt.dayofyear

        df = df[df['DATE'].dt.year == year]

        if start_month is not None and end_month is not None:
            spans_year = (start_month > end_month) or (start_month == end_month and start_day > end_day)
            if spans_year:
                mask = ((df['month'] > start_month) |
                        ((df['month'] == start_month) & (df['day'] >= start_day)) |
                        (df['month'] < end_month) |
                        ((df['month'] == end_month) & (df['day'] <= end_day)))
            else:
                mask = (((df['month'] > start_month) |
                         ((df['month'] == start_month) & (df['day'] >= start_day))) &
                        ((df['month'] < end_month) |
                         ((df['month'] == end_month) & (df['day'] <= end_day))))
            df = df[mask]

        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

        result = df[['day_of_year', 'month', 'day']].copy()
        result['temp'] = df[metric].values

        if len(result) == 0:
            result['date_label'] = pd.Series(dtype=str)
            result['plot_x'] = pd.Series(dtype=float)
        else:
            result['date_label'] = result.apply(lambda r: f"{months[int(r['month'])-1]} {int(r['day'])}", axis=1)
            # For year-spanning ranges, shift "after new year" days so they plot contiguously
            if start_month is not None and end_month is not None:
                spans_year = (start_month > end_month) or (start_month == end_month and start_day > end_day)
                if spans_year:
                    result['plot_x'] = result.apply(
                        lambda r: r['day_of_year'] + 365 if r['month'] <= end_month else r['day_of_year'], axis=1)
                else:
                    result['plot_x'] = result['day_of_year']
            else:
                result['plot_x'] = result['day_of_year']

        return result.sort_values('plot_x').reset_index(drop=True)

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

    def print_event_frequency_report(self, freq_data: pd.DataFrame,
                                     metric: str, threshold: float, direction: str):
        """Print formatted extreme event frequency report."""
        dir_symbol = '<=' if direction == 'below' else '>='

        print(f"\n{'='*80}")
        print(f"EXTREME EVENT FREQUENCY: {metric} {dir_symbol} {threshold}°F")
        print(f"{'='*80}\n")

        avg_days = freq_data['event_days'].mean()
        min_row = freq_data.loc[freq_data['event_days'].idxmin()]
        max_row = freq_data.loc[freq_data['event_days'].idxmax()]

        # Trendline
        z = np.polyfit(freq_data['year'], freq_data['event_days'], 1)
        slope = z[0]
        if abs(slope) < 0.05:
            trend_desc = "stable"
        elif slope > 0:
            trend_desc = "increasing"
        else:
            trend_desc = "decreasing"

        print("SUMMARY")
        print("-" * 40)
        print(f"  Total Years:  {len(freq_data)}")
        print(f"  Avg Events:   {avg_days:.1f} days/year")
        print(f"  Minimum:      {int(min_row['event_days'])} days ({int(min_row['year'])})")
        print(f"  Maximum:      {int(max_row['event_days'])} days ({int(max_row['year'])})")
        print(f"  Trend:        {slope:+.2f} days/year ({trend_desc})")
        print()

        print("YEAR-BY-YEAR")
        print("-" * 40)
        max_days = freq_data['event_days'].max()
        bar_width = 30
        for _, row in freq_data.iterrows():
            days = int(row['event_days'])
            pct = row['percentage']
            bar_len = int((days / max_days) * bar_width) if max_days > 0 else 0
            bar = '#' * bar_len
            print(f"  {int(row['year'])}: {days:3d} days ({pct:5.1f}%)  {bar}")
        print()

    def print_freeze_dates_report(self, freeze_data: pd.DataFrame,
                                  metric: str, threshold: float):
        """Print formatted freeze date tracker report."""
        print(f"\n{'='*80}")
        print(f"FREEZE DATE TRACKER: {metric} <= {threshold}°F")
        print(f"{'='*80}\n")

        valid_spring = freeze_data.dropna(subset=['last_spring_freeze'])
        valid_fall = freeze_data.dropna(subset=['first_fall_freeze'])
        valid_season = freeze_data.dropna(subset=['growing_season_days'])

        print("SUMMARY")
        print("-" * 40)
        if len(valid_spring) > 0:
            avg_spring_doy = valid_spring['spring_doy'].mean()
            avg_spring_date = pd.Timestamp('2000-01-01') + pd.Timedelta(days=int(avg_spring_doy) - 1)
            print(f"  Avg Last Spring Freeze:  {avg_spring_date.strftime('%b %d')} (day {int(avg_spring_doy)})")
        if len(valid_fall) > 0:
            avg_fall_doy = valid_fall['fall_doy'].mean()
            avg_fall_date = pd.Timestamp('2000-01-01') + pd.Timedelta(days=int(avg_fall_doy) - 1)
            print(f"  Avg First Fall Freeze:   {avg_fall_date.strftime('%b %d')} (day {int(avg_fall_doy)})")
        if len(valid_season) > 0:
            print(f"  Avg Growing Season:      {valid_season['growing_season_days'].mean():.0f} days")
        print(f"  Years Analyzed:          {len(freeze_data)}")
        print()

        print(f"{'Year':<6} {'Last Spring':<14} {'First Fall':<14} {'Growing Season'}")
        print("-" * 55)
        for _, row in freeze_data.iterrows():
            year = int(row['year'])
            spring = row['last_spring_freeze'].strftime('%b %d') if pd.notna(row['last_spring_freeze']) else 'No freeze'
            fall = row['first_fall_freeze'].strftime('%b %d') if pd.notna(row['first_fall_freeze']) else 'No freeze'
            season = f"{int(row['growing_season_days'])} days" if pd.notna(row['growing_season_days']) else 'N/A'
            print(f"  {year:<4} {spring:<14} {fall:<14} {season}")
        print()

    def print_heatmap_report(self, heatmap_data: pd.DataFrame, metric: str, mode: str):
        """Print formatted heatmap report."""
        mode_label = 'Absolute Values' if mode == 'absolute' else 'Anomaly from Mean'

        print(f"\n{'='*80}")
        print(f"TEMPERATURE HEATMAP: {metric} ({mode_label}, Monthly)")
        print(f"{'='*80}\n")

        # Header
        print(f"{'Year':<6}", end='')
        for col in heatmap_data.columns:
            print(f"{col:>7}", end='')
        print()
        print("-" * (6 + 7 * len(heatmap_data.columns)))

        for year, row in heatmap_data.iterrows():
            print(f"{year:<6}", end='')
            for val in row:
                if pd.notna(val):
                    print(f"{val:7.1f}", end='')
                else:
                    print(f"{'':>7}", end='')
            print()
        print()

    def print_climate_band_report(self, records: pd.DataFrame, metric: str,
                                  overlay_data=None, overlay_year=None):
        """Print formatted climate band report."""
        print(f"\n{'='*80}")
        print(f"DAILY RECORD ENVELOPE: {metric}")
        print(f"{'='*80}\n")

        print("RECORDS SUMMARY")
        print("-" * 40)
        print(f"  Highest Record High:  {records['record_high'].max():.0f}°F")
        print(f"  Lowest Record Low:    {records['record_low'].min():.0f}°F")
        print(f"  Warmest Avg Day:      {records['avg_temp'].max():.1f}°F")
        print(f"  Coldest Avg Day:      {records['avg_temp'].min():.1f}°F")
        print()

        # Show a sample of records
        print(f"{'Date':<10} {'Record Low':>11} {'Average':>9} {'Record High':>12}")
        print("-" * 45)
        step = max(1, len(records) // 20)
        for i in range(0, len(records), step):
            row = records.iloc[i]
            print(f"  {row['date_label']:<8} {row['record_low']:8.0f}°F  {row['avg_temp']:6.1f}°F  {row['record_high']:8.0f}°F")

        if overlay_data is not None and overlay_year is not None and len(overlay_data) > 0:
            print(f"\nOVERLAY: {overlay_year}")
            print("-" * 40)
            print(f"  Data points: {len(overlay_data)} days")
            print(f"  Min temp:    {overlay_data['temp'].min():.0f}°F")
            print(f"  Max temp:    {overlay_data['temp'].max():.0f}°F")
            print(f"  Avg temp:    {overlay_data['temp'].mean():.1f}°F")
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

  # Extreme event frequency: how many days per year does TMAX hit 100°F?
  python temp_analysis.py data.csv --event-freq --metric TMAX --threshold 100 --direction above

  # Freeze date tracker: first/last freeze dates by year
  python temp_analysis.py data.csv --freeze-dates --threshold 32

  # Temperature heatmap (absolute or anomaly)
  python temp_analysis.py data.csv --heatmap --metric TAVG --heatmap-mode anomaly

  # Climate band: daily record envelope with year overlay
  python temp_analysis.py data.csv --climate-band --metric TMAX --overlay-year 2023
  python temp_analysis.py data.csv --climate-band --metric TMAX --band-range 6/1-8/31

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
    parser.add_argument('--event-freq', action='store_true',
                       help='Analyze extreme event frequency over time')
    parser.add_argument('--freeze-dates', action='store_true',
                       help='Track first/last freeze dates by year')
    parser.add_argument('--heatmap', action='store_true',
                       help='Generate temperature heatmap (year x month)')
    parser.add_argument('--heatmap-mode', choices=['absolute', 'anomaly'], default='absolute',
                       help='Heatmap mode: absolute temps or anomaly from mean (default: absolute)')
    parser.add_argument('--climate-band', action='store_true',
                       help='Generate daily record envelope chart')
    parser.add_argument('--overlay-year', type=int,
                       help='Year to overlay on climate band')
    parser.add_argument('--band-range', metavar='M/D-M/D',
                       help='Date range for climate band (e.g., 6/1-8/31 for summer)')
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

    if args.event_freq:
        if args.threshold is None:
            parser.error("--threshold required for event frequency analysis")
        freq_data = analyzer.find_extreme_event_frequency(
            metric=args.metric,
            threshold=args.threshold,
            direction=args.direction
        )
        analyzer.print_event_frequency_report(freq_data, args.metric,
                                              args.threshold, args.direction)
        ran_analysis = True

    if args.freeze_dates:
        freeze_threshold = args.threshold if args.threshold is not None else 32.0
        # Default to TMIN for freeze analysis unless user explicitly set --metric
        freeze_metric = args.metric if '--metric' in sys.argv else 'TMIN'
        freeze_data = analyzer.find_freeze_dates(
            metric=freeze_metric,
            threshold=freeze_threshold
        )
        analyzer.print_freeze_dates_report(freeze_data, freeze_metric, freeze_threshold)
        ran_analysis = True

    if args.heatmap:
        heatmap_data = analyzer.create_temperature_heatmap(
            metric=args.metric,
            mode=args.heatmap_mode
        )
        analyzer.print_heatmap_report(heatmap_data, args.metric, args.heatmap_mode)
        ran_analysis = True

    if args.climate_band:
        if args.band_range:
            sm, sd, em, ed = parse_date_range(args.band_range)
        else:
            sm = sd = em = ed = None
        records = analyzer.calculate_daily_records(
            metric=args.metric,
            start_month=sm, start_day=sd,
            end_month=em, end_day=ed
        )
        overlay_data = None
        if args.overlay_year:
            overlay_data = analyzer.get_year_overlay_data(
                year=args.overlay_year,
                metric=args.metric,
                start_month=sm, start_day=sd,
                end_month=em, end_day=ed
            )
        analyzer.print_climate_band_report(records, args.metric,
                                           overlay_data, args.overlay_year)
        ran_analysis = True

    if not ran_analysis:
        parser.print_help()


if __name__ == '__main__':
    main()
