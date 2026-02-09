#!/usr/bin/env python3
"""
Streamlit GUI for Temperature Analysis Tool.

Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from temp_analysis import TempAnalyzer


def main():
    st.set_page_config(
        page_title="Temperature Analysis Tool",
        page_icon="🌡️",
        layout="wide"
    )

    st.title("Temperature Analysis Tool")
    st.markdown("Analyze historical temperature data for streaks, extreme periods, and seasonal patterns.")

    # Sidebar for data loading and analysis type
    with st.sidebar:
        st.header("Data Source")

        data_source = st.radio(
            "Choose data source:",
            ["Default (Huntsville Weather)", "Upload CSV"]
        )

        column_map = None

        if data_source == "Upload CSV":
            uploaded_file = st.file_uploader("Upload weather CSV", type=['csv'])

            if uploaded_file is not None:
                # Preview columns for mapping
                preview_df = pd.read_csv(uploaded_file)
                uploaded_file.seek(0)  # Reset for later reading

                st.subheader("Column Mapping")
                st.caption("Map your CSV columns to expected names")

                cols = preview_df.columns.tolist()

                # Auto-detect column indices by name (case-insensitive)
                def find_col_index(cols, name, fallback):
                    for i, col in enumerate(cols):
                        if col.upper() == name.upper():
                            return i
                    return fallback

                date_idx = find_col_index(cols, 'DATE', 0)
                tmax_idx = find_col_index(cols, 'TMAX', min(1, len(cols)-1))
                tmin_idx = find_col_index(cols, 'TMIN', min(2, len(cols)-1))

                date_col = st.selectbox("DATE column:", cols, index=date_idx)
                tmax_col = st.selectbox("TMAX column:", cols, index=tmax_idx)
                tmin_col = st.selectbox("TMIN column:", cols, index=tmin_idx)

                if date_col != 'DATE' or tmax_col != 'TMAX' or tmin_col != 'TMIN':
                    column_map = {}
                    if date_col != 'DATE':
                        column_map[date_col] = 'DATE'
                    if tmax_col != 'TMAX':
                        column_map[tmax_col] = 'TMAX'
                    if tmin_col != 'TMIN':
                        column_map[tmin_col] = 'TMIN'

                csv_path = uploaded_file
            else:
                csv_path = None
        else:
            csv_path = 'hsvWeather_112024.csv'

        st.divider()

        st.header("Analysis Type")
        analysis_type = st.selectbox(
            "Select analysis:",
            [
                "Temperature Streaks",
                "Extreme Periods",
                "Seasonal Analysis",
                "Custom Date Range",
                "Threshold Histogram",
                "Extreme Event Frequency",
                "Freeze Date Tracker",
                "Temperature Heatmap",
                "Daily Record Envelope"
            ]
        )

        analysis_descriptions = {
            "Temperature Streaks": "Find longest consecutive runs above or below a temperature threshold.",
            "Extreme Periods": "Find the coldest or warmest N-day periods using rolling averages.",
            "Seasonal Analysis": "Rank seasons (winter, spring, summer, fall) by average temperature.",
            "Custom Date Range": "Compare a specific date range (e.g., Dec 20-31) across all years.",
            "Threshold Histogram": "Count how often a threshold is met within a date range, by year.",
            "Extreme Event Frequency": "Track how many days per year exceed a threshold, with trend over time.",
            "Freeze Date Tracker": "Find the last spring and first fall freeze dates for each year.",
            "Temperature Heatmap": "Year-by-month heatmap of temperatures or departures from normal.",
            "Daily Record Envelope": "Daily record highs, lows, and averages with optional year overlay.",
        }
        st.caption(analysis_descriptions[analysis_type])

    # Load data
    if csv_path is None:
        st.info("Please upload a CSV file to begin analysis.")
        return

    try:
        analyzer = TempAnalyzer(csv_path, column_map=column_map)

        # Show data info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Valid Records", f"{len(analyzer.df):,}")
        with col2:
            st.metric("Start Date", analyzer.df['DATE'].min().strftime('%Y-%m-%d'))
        with col3:
            st.metric("End Date", analyzer.df['DATE'].max().strftime('%Y-%m-%d'))

        # Show warning if data was filtered
        if analyzer.dropped_count > 0:
            pct = analyzer.dropped_count / analyzer.original_count * 100
            st.warning(f"Filtered out {analyzer.dropped_count:,} rows with missing temperature data "
                      f"({pct:.1f}% of {analyzer.original_count:,} total rows)")

    except Exception as e:
        st.error(f"Error loading data: {e}")
        return

    st.divider()

    # Analysis-specific UI
    if analysis_type == "Temperature Streaks":
        render_streak_analysis(analyzer)
    elif analysis_type == "Extreme Periods":
        render_period_analysis(analyzer)
    elif analysis_type == "Seasonal Analysis":
        render_seasonal_analysis(analyzer)
    elif analysis_type == "Custom Date Range":
        render_date_range_analysis(analyzer)
    elif analysis_type == "Threshold Histogram":
        render_histogram_analysis(analyzer)
    elif analysis_type == "Extreme Event Frequency":
        render_event_frequency_analysis(analyzer)
    elif analysis_type == "Freeze Date Tracker":
        render_freeze_dates_analysis(analyzer)
    elif analysis_type == "Temperature Heatmap":
        render_heatmap_analysis(analyzer)
    elif analysis_type == "Daily Record Envelope":
        render_climate_band_analysis(analyzer)


def render_streak_analysis(analyzer):
    """Render temperature streak analysis UI."""
    st.header("Temperature Streaks")
    st.markdown("Find the longest consecutive runs of days where a temperature metric stayed above or below "
                "a given threshold. For example, find the longest stretch where the high temperature stayed "
                "at or above 95°F. Results are ranked by streak length and show the start/end dates of each streak.")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        metric = st.selectbox("Metric:", ["TMAX", "TMIN", "TAVG"], key="streak_metric")
    with col2:
        threshold = st.number_input("Threshold (°F):", value=90.0, step=1.0, key="streak_threshold")
    with col3:
        direction = st.selectbox(
            "Direction:", ["above", "below"],
            format_func=lambda x: "at or above" if x == "above" else "at or below",
            key="streak_direction"
        )
    with col4:
        top_n = st.slider("Top N results:", 1, 20, 10, key="streak_topn")

    if st.button("Find Streaks", type="primary"):
        with st.spinner("Analyzing streaks..."):
            streaks = analyzer.find_streaks(
                metric=metric,
                threshold=threshold,
                direction=direction,
                top_n=top_n
            )

        if len(streaks) == 0:
            st.warning("No streaks found matching the criteria.")
            return

        # Display results
        dir_label = "at or above" if direction == "above" else "at or below"
        st.subheader(f"Top {len(streaks)} Streaks: {metric} {dir_label} {threshold}°F")

        # Format for display
        display_df = streaks.copy()
        display_df['Rank'] = range(1, len(display_df) + 1)
        display_df['start_date'] = display_df['start_date'].dt.strftime('%Y-%m-%d')
        display_df['end_date'] = display_df['end_date'].dt.strftime('%Y-%m-%d')
        display_df = display_df.rename(columns={
            'length': 'Days',
            'start_date': 'Start Date',
            'end_date': 'End Date',
            'avg_temp': 'Avg Temp (°F)',
            'min_temp': 'Min Temp (°F)',
            'max_temp': 'Max Temp (°F)'
        })
        display_df = display_df[['Rank', 'Days', 'Start Date', 'End Date',
                                  'Avg Temp (°F)', 'Min Temp (°F)', 'Max Temp (°F)']]

        st.dataframe(display_df, use_container_width=True, hide_index=True)

        # Bar chart of streak lengths
        st.subheader("Streak Length Comparison")
        chart_data = streaks[['length']].copy()
        chart_data.index = [f"#{i+1}" for i in range(len(chart_data))]
        st.bar_chart(chart_data, y='length', use_container_width=True)


def render_period_analysis(analyzer):
    """Render extreme period analysis UI."""
    st.header("Extreme Periods")
    st.markdown("Find the coldest or warmest N-day periods in the dataset using rolling averages. "
                "For example, find the coldest 7-day stretch on record. Periods are non-overlapping "
                "so each result represents a distinct event, ranked by average temperature.")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        metric = st.selectbox("Metric:", ["TAVG", "TMAX", "TMIN"], key="period_metric")
    with col2:
        n_days = st.number_input("Period length (days):", min_value=1, max_value=365, value=7, key="period_days")
    with col3:
        extreme = st.selectbox("Extreme type:", ["coldest", "warmest"], key="period_extreme")
    with col4:
        top_n = st.slider("Top N results:", 1, 20, 10, key="period_topn")

    if st.button("Find Periods", type="primary"):
        with st.spinner("Analyzing periods..."):
            periods = analyzer.find_extreme_periods(
                metric=metric,
                n_days=n_days,
                extreme=extreme,
                top_n=top_n
            )

        if len(periods) == 0:
            st.warning("No periods found.")
            return

        st.subheader(f"Top {len(periods)} {extreme.capitalize()} {n_days}-Day Periods ({metric})")

        display_df = periods.copy()
        display_df['Rank'] = range(1, len(display_df) + 1)
        display_df['start_date'] = display_df['start_date'].dt.strftime('%Y-%m-%d')
        display_df['end_date'] = display_df['end_date'].dt.strftime('%Y-%m-%d')
        display_df = display_df.rename(columns={
            'start_date': 'Start Date',
            'end_date': 'End Date',
            'avg_temp': 'Avg Temp (°F)',
            'min_temp': 'Min Temp (°F)',
            'max_temp': 'Max Temp (°F)',
            'length': 'Days'
        })
        display_df = display_df[['Rank', 'Start Date', 'End Date',
                                  'Avg Temp (°F)', 'Min Temp (°F)', 'Max Temp (°F)']]

        st.dataframe(display_df, use_container_width=True, hide_index=True)

        # Chart
        st.subheader("Average Temperature Comparison")
        chart_data = periods[['avg_temp']].copy()
        chart_data.index = [f"#{i+1}" for i in range(len(chart_data))]
        st.bar_chart(chart_data, y='avg_temp', use_container_width=True)


def render_seasonal_analysis(analyzer):
    """Render seasonal analysis UI."""
    st.header("Seasonal Analysis")
    st.markdown("Rank every season in the dataset by average temperature to find the coldest or warmest on record. "
                "Seasons are defined as Winter (Dec-Feb), Spring (Mar-May), Summer (Jun-Aug), and Fall (Sep-Nov). "
                "December is grouped with the following year's winter (e.g., Dec 2023 belongs to Winter 2023-24).")
    st.caption("Winter = Dec-Feb, Spring = Mar-May, Summer = Jun-Aug, Fall = Sep-Nov")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        season = st.selectbox("Season:", ["winter", "summer", "spring", "fall"], key="season_type")
    with col2:
        metric = st.selectbox("Metric:", ["TAVG", "TMAX", "TMIN"], key="season_metric")
    with col3:
        extreme = st.selectbox("Extreme type:", ["coldest", "warmest"], key="season_extreme")
    with col4:
        top_n = st.slider("Top N results:", 1, 20, 10, key="season_topn")

    if st.button("Find Seasons", type="primary"):
        with st.spinner("Analyzing seasons..."):
            seasons = analyzer.find_extreme_seasons(
                season=season,
                metric=metric,
                extreme=extreme,
                top_n=top_n
            )

        if len(seasons) == 0:
            st.warning("No seasons found.")
            return

        st.subheader(f"Top {len(seasons)} {extreme.capitalize()} {season.capitalize()}s ({metric})")

        display_df = seasons.copy()
        display_df['Rank'] = range(1, len(display_df) + 1)

        # Format season year label
        if season == 'winter':
            display_df['Season'] = display_df['season_year'].apply(
                lambda y: f"Winter {int(y)-1}-{str(int(y))[-2:]}"
            )
        else:
            display_df['Season'] = display_df['season_year'].apply(
                lambda y: f"{season.capitalize()} {int(y)}"
            )

        display_df['start_date'] = display_df['start_date'].dt.strftime('%Y-%m-%d')
        display_df['end_date'] = display_df['end_date'].dt.strftime('%Y-%m-%d')
        display_df = display_df.rename(columns={
            'avg_temp': 'Avg Temp (°F)',
            'min_temp': 'Min Temp (°F)',
            'max_temp': 'Max Temp (°F)',
            'days': 'Days',
            'start_date': 'Start Date',
            'end_date': 'End Date'
        })
        display_df = display_df[['Rank', 'Season', 'Avg Temp (°F)',
                                  'Min Temp (°F)', 'Max Temp (°F)', 'Days']]

        st.dataframe(display_df, use_container_width=True, hide_index=True)

        # Chart
        st.subheader("Average Temperature by Season")
        chart_data = pd.DataFrame({
            'Season': display_df['Season'].values,
            'Avg Temp': seasons['avg_temp'].values
        })
        st.bar_chart(chart_data.set_index('Season'), y='Avg Temp', use_container_width=True)


def render_date_range_analysis(analyzer):
    """Render custom date range analysis UI."""
    st.header("Custom Date Range Analysis")
    st.markdown("Compare a specific calendar date range across every year in the dataset to find the coldest "
                "or warmest instances. For example, find which year had the coldest Dec 20-31 period. "
                "Year-spanning ranges (e.g., Dec 15 - Jan 15) are supported.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Start Date")
        start_month = st.selectbox("Month:", range(1, 13),
                                   format_func=lambda x: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][x-1],
                                   key="range_start_month")
        start_day = st.number_input("Day:", min_value=1, max_value=31, value=1, key="range_start_day")

    with col2:
        st.subheader("End Date")
        end_month = st.selectbox("Month:", range(1, 13),
                                 format_func=lambda x: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                                        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][x-1],
                                 key="range_end_month")
        end_day = st.number_input("Day:", min_value=1, max_value=31, value=31, key="range_end_day")

    col3, col4, col5 = st.columns(3)

    with col3:
        metric = st.selectbox("Metric:", ["TAVG", "TMAX", "TMIN"], key="range_metric")
    with col4:
        extreme = st.selectbox("Extreme type:", ["coldest", "warmest"], key="range_extreme")
    with col5:
        top_n = st.slider("Top N results:", 1, 20, 10, key="range_topn")

    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    range_str = f"{months[start_month-1]} {start_day} - {months[end_month-1]} {end_day}"

    if st.button(f"Find {extreme.capitalize()} {range_str} Periods", type="primary"):
        with st.spinner("Analyzing date ranges..."):
            ranges = analyzer.find_extreme_date_range(
                start_month=start_month,
                start_day=start_day,
                end_month=end_month,
                end_day=end_day,
                metric=metric,
                extreme=extreme,
                top_n=top_n
            )

        if len(ranges) == 0:
            st.warning("No matching periods found.")
            return

        st.subheader(f"Top {len(ranges)} {extreme.capitalize()} {range_str} Periods ({metric})")

        display_df = ranges.copy()
        display_df['Rank'] = range(1, len(display_df) + 1)
        display_df['year'] = display_df['year'].astype(int)
        display_df['start_date'] = display_df['start_date'].dt.strftime('%Y-%m-%d')
        display_df['end_date'] = display_df['end_date'].dt.strftime('%Y-%m-%d')
        display_df = display_df.rename(columns={
            'year': 'Year',
            'avg_temp': 'Avg Temp (°F)',
            'min_temp': 'Min Temp (°F)',
            'max_temp': 'Max Temp (°F)',
            'days': 'Days',
            'start_date': 'Start Date',
            'end_date': 'End Date'
        })
        display_df = display_df[['Rank', 'Year', 'Avg Temp (°F)',
                                  'Min Temp (°F)', 'Max Temp (°F)', 'Days']]

        st.dataframe(display_df, use_container_width=True, hide_index=True)

        # Chart
        st.subheader("Average Temperature by Year")
        chart_data = pd.DataFrame({
            'Year': ranges['year'].astype(int).values,
            'Avg Temp': ranges['avg_temp'].values
        })
        st.bar_chart(chart_data.set_index('Year'), y='Avg Temp', use_container_width=True)


def render_histogram_analysis(analyzer):
    """Render threshold histogram analysis UI."""
    st.header("Threshold Histogram")
    st.markdown("Count how many days within a date range meet a temperature threshold, broken down by year. "
                "For example, how many days in January did the low temperature drop to 32°F or below? "
                "Results show year-by-year counts along with summary statistics like the average and extremes.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Start Date")
        start_month = st.selectbox("Month:", range(1, 13),
                                   format_func=lambda x: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][x-1],
                                   key="hist_start_month")
        start_day = st.number_input("Day:", min_value=1, max_value=31, value=1, key="hist_start_day")

    with col2:
        st.subheader("End Date")
        end_month = st.selectbox("Month:", range(1, 13),
                                 format_func=lambda x: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                                        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][x-1],
                                 key="hist_end_month")
        end_day = st.number_input("Day:", min_value=1, max_value=31, value=31, key="hist_end_day")

    col3, col4, col5 = st.columns(3)

    with col3:
        metric = st.selectbox("Metric:", ["TMIN", "TMAX", "TAVG"], key="hist_metric")
    with col4:
        threshold = st.number_input("Threshold (°F):", value=32.0, step=1.0, key="hist_threshold")
    with col5:
        direction = st.selectbox(
            "Direction:", ["below", "above"],
            format_func=lambda x: "at or above" if x == "above" else "at or below",
            key="hist_direction"
        )

    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    range_str = f"{months[start_month-1]} {start_day} - {months[end_month-1]} {end_day}"
    dir_symbol = '<=' if direction == 'below' else '>='

    if st.button(f"Analyze: {metric} {dir_symbol} {threshold}°F for {range_str}", type="primary"):
        with st.spinner("Analyzing threshold histogram..."):
            result = analyzer.threshold_histogram(
                start_month=start_month,
                start_day=start_day,
                end_month=end_month,
                end_day=end_day,
                metric=metric,
                threshold=threshold,
                direction=direction
            )

        summary = result['summary']
        by_year = result['by_year']

        st.subheader(f"Summary: {metric} {dir_symbol} {threshold}°F for {range_str}")

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Avg Days/Year", f"{summary['avg_days']:.1f}")
        with col2:
            st.metric("Min Days", f"{int(summary['min_days'])}")
        with col3:
            st.metric("Max Days", f"{int(summary['max_days'])}")
        with col4:
            st.metric("Std Dev", f"{summary['std_days']:.1f}")

        st.caption(f"Based on {summary['total_years']} years of data. Average: {summary['avg_percentage']:.1f}% of days in range.")

        st.divider()

        # Year-by-year table
        st.subheader("Year-by-Year Breakdown")

        display_df = by_year.copy()
        display_df['year'] = display_df['year'].astype(int)
        display_df = display_df.rename(columns={
            'year': 'Year',
            'days_meeting_threshold': 'Days Meeting Threshold',
            'total_days': 'Total Days in Range',
            'percentage': 'Percentage (%)'
        })

        st.dataframe(display_df, use_container_width=True, hide_index=True)

        # Chart - sort by year for the chart
        st.subheader("Days Meeting Threshold by Year")
        chart_data = by_year.sort_values('year').copy()
        chart_data['year'] = chart_data['year'].astype(int).astype(str)
        chart_df = pd.DataFrame({
            'Year': chart_data['year'].values,
            'Days': chart_data['days_meeting_threshold'].values
        })
        st.bar_chart(chart_df.set_index('Year'), y='Days', use_container_width=True)


def render_event_frequency_analysis(analyzer):
    """Render extreme event frequency analysis UI."""
    st.header("Extreme Event Frequency")
    st.markdown("Track how many days per year a temperature threshold is met across the entire dataset. "
                "A linear trendline shows whether these events are becoming more or less frequent over time. "
                "Useful for spotting long-term changes in extreme heat days, freezing days, and similar patterns.")

    col1, col2, col3 = st.columns(3)

    with col1:
        metric = st.selectbox("Metric:", ["TMAX", "TMIN", "TAVG"], key="freq_metric")
    with col2:
        threshold = st.number_input("Threshold (°F):", value=100.0, step=1.0, key="freq_threshold")
    with col3:
        direction = st.selectbox(
            "Direction:", ["above", "below"],
            format_func=lambda x: "at or above" if x == "above" else "at or below",
            key="freq_direction"
        )

    dir_symbol = '>=' if direction == 'above' else '<='

    if st.button(f"Analyze: {metric} {dir_symbol} {threshold}°F", type="primary"):
        with st.spinner("Analyzing event frequency..."):
            freq_data = analyzer.find_extreme_event_frequency(
                metric=metric, threshold=threshold, direction=direction
            )

        if len(freq_data) == 0:
            st.warning("No data found.")
            return

        # Summary metrics
        avg_days = freq_data['event_days'].mean()
        min_row = freq_data.loc[freq_data['event_days'].idxmin()]
        max_row = freq_data.loc[freq_data['event_days'].idxmax()]
        z = np.polyfit(freq_data['year'], freq_data['event_days'], 1)
        slope = z[0]

        if abs(slope) < 0.05:
            trend_desc = "Stable"
        elif slope > 0:
            trend_desc = "Increasing"
        else:
            trend_desc = "Decreasing"

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Avg Days/Year", f"{avg_days:.1f}")
        with col2:
            st.metric("Min", f"{int(min_row['event_days'])} ({int(min_row['year'])})")
        with col3:
            st.metric("Max", f"{int(max_row['event_days'])} ({int(max_row['year'])})")
        with col4:
            st.metric("Trend", f"{slope:+.2f} days/yr", delta=trend_desc,
                      delta_color="normal" if slope > 0 else "inverse")

        # Plotly chart
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=freq_data['year'],
            y=freq_data['event_days'],
            name='Event Days',
            marker_color='rgba(55, 83, 109, 0.7)',
            hovertemplate='<b>%{x}</b><br>Days: %{y}<extra></extra>'
        ))

        # Trendline
        p = np.poly1d(z)
        trend_y = p(freq_data['year'])
        fig.add_trace(go.Scatter(
            x=freq_data['year'],
            y=trend_y,
            mode='lines',
            name=f'Trend ({slope:+.2f}/yr)',
            line=dict(color='red', width=2, dash='dash'),
            hovertemplate='Trend: %{y:.1f}<extra></extra>'
        ))

        fig.update_layout(
            title=f'{metric} {dir_symbol} {threshold}°F: Days Per Year',
            xaxis_title='Year',
            yaxis_title='Days',
            hovermode='x unified',
            height=500,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        st.plotly_chart(fig, use_container_width=True)

        # Data table
        st.subheader("Year-by-Year Data")
        display_df = freq_data.copy()
        display_df['year'] = display_df['year'].astype(int)
        display_df = display_df.rename(columns={
            'year': 'Year', 'event_days': 'Event Days',
            'total_days': 'Total Days', 'percentage': 'Percentage (%)'
        })
        st.dataframe(display_df, use_container_width=True, hide_index=True)


def render_freeze_dates_analysis(analyzer):
    """Render freeze date tracker analysis UI."""
    st.header("Freeze Date Tracker")
    st.markdown("Find the last spring freeze and first fall freeze for each year in the dataset. "
                "The growing season length (days between last spring and first fall freeze) is also calculated. "
                "Spring freezes are the latest freeze date before July 1; fall freezes are the earliest on or after July 1.")

    col1, col2 = st.columns(2)

    with col1:
        metric = st.selectbox("Metric:", ["TMIN", "TMAX", "TAVG"], key="freeze_metric")
    with col2:
        threshold = st.number_input("Freeze threshold (°F):", value=32.0, step=1.0, key="freeze_threshold")

    if st.button("Analyze Freeze Dates", type="primary"):
        with st.spinner("Analyzing freeze dates..."):
            freeze_data = analyzer.find_freeze_dates(metric=metric, threshold=threshold)

        if len(freeze_data) == 0:
            st.warning("No data found.")
            return

        valid_spring = freeze_data.dropna(subset=['last_spring_freeze'])
        valid_fall = freeze_data.dropna(subset=['first_fall_freeze'])
        valid_season = freeze_data.dropna(subset=['growing_season_days'])

        # Summary
        col1, col2, col3 = st.columns(3)
        with col1:
            if len(valid_spring) > 0:
                avg_doy = valid_spring['spring_doy'].mean()
                avg_date = pd.Timestamp('2000-01-01') + pd.Timedelta(days=int(avg_doy) - 1)
                st.metric("Avg Last Spring Freeze", avg_date.strftime('%b %d'))
        with col2:
            if len(valid_fall) > 0:
                avg_doy = valid_fall['fall_doy'].mean()
                avg_date = pd.Timestamp('2000-01-01') + pd.Timedelta(days=int(avg_doy) - 1)
                st.metric("Avg First Fall Freeze", avg_date.strftime('%b %d'))
        with col3:
            if len(valid_season) > 0:
                st.metric("Avg Growing Season", f"{valid_season['growing_season_days'].mean():.0f} days")

        # Plotly chart
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        if len(valid_spring) > 0:
            spring_labels = [d.strftime('%b %d') for d in valid_spring['last_spring_freeze']]
            fig.add_trace(
                go.Scatter(
                    x=valid_spring['year'],
                    y=valid_spring['spring_doy'],
                    mode='lines+markers',
                    name='Last Spring Freeze',
                    marker=dict(color='blue', size=5),
                    line=dict(color='blue', width=1),
                    customdata=spring_labels,
                    hovertemplate='<b>%{x}</b><br>Last Spring: %{customdata}<extra></extra>'
                ),
                secondary_y=False
            )

        if len(valid_fall) > 0:
            fall_labels = [d.strftime('%b %d') for d in valid_fall['first_fall_freeze']]
            fig.add_trace(
                go.Scatter(
                    x=valid_fall['year'],
                    y=valid_fall['fall_doy'],
                    mode='lines+markers',
                    name='First Fall Freeze',
                    marker=dict(color='orange', size=5),
                    line=dict(color='orange', width=1),
                    customdata=fall_labels,
                    hovertemplate='<b>%{x}</b><br>First Fall: %{customdata}<extra></extra>'
                ),
                secondary_y=False
            )

        if len(valid_season) > 0:
            fig.add_trace(
                go.Bar(
                    x=valid_season['year'],
                    y=valid_season['growing_season_days'],
                    name='Growing Season',
                    marker_color='rgba(50, 171, 96, 0.3)',
                    hovertemplate='<b>%{x}</b><br>Growing Season: %{y:.0f} days<extra></extra>'
                ),
                secondary_y=True
            )

        fig.update_xaxes(title_text='Year')
        fig.update_yaxes(title_text='Day of Year', secondary_y=False)
        fig.update_yaxes(title_text='Growing Season (Days)', secondary_y=True)

        fig.update_layout(
            title=f'Freeze Dates: {metric} <= {threshold}°F',
            hovermode='x unified',
            height=600,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        st.plotly_chart(fig, use_container_width=True)

        # Data table
        st.subheader("Year-by-Year Data")
        display_df = freeze_data.copy()
        display_df['year'] = display_df['year'].astype(int)
        display_df['last_spring_freeze'] = display_df['last_spring_freeze'].apply(
            lambda d: d.strftime('%b %d') if pd.notna(d) else 'No freeze')
        display_df['first_fall_freeze'] = display_df['first_fall_freeze'].apply(
            lambda d: d.strftime('%b %d') if pd.notna(d) else 'No freeze')
        display_df['growing_season_days'] = display_df['growing_season_days'].apply(
            lambda d: f"{int(d)}" if pd.notna(d) else 'N/A')
        display_df = display_df[['year', 'last_spring_freeze', 'first_fall_freeze', 'growing_season_days']]
        display_df = display_df.rename(columns={
            'year': 'Year', 'last_spring_freeze': 'Last Spring Freeze',
            'first_fall_freeze': 'First Fall Freeze',
            'growing_season_days': 'Growing Season (Days)'
        })
        st.dataframe(display_df, use_container_width=True, hide_index=True)


def render_heatmap_analysis(analyzer):
    """Render temperature heatmap analysis UI."""
    st.header("Temperature Heatmap")
    st.markdown("Visualize monthly average temperatures across all years as a color-coded heatmap. "
                "In absolute mode, colors represent actual temperatures. In anomaly mode, colors show "
                "how much each month departed from its long-term average, making it easy to spot "
                "unusually warm or cold months.")

    col1, col2 = st.columns(2)

    with col1:
        metric = st.selectbox("Metric:", ["TAVG", "TMAX", "TMIN"], key="heatmap_metric")
    with col2:
        mode = st.radio("Display Mode:", ["absolute", "anomaly"],
                        format_func=lambda x: "Absolute Temperatures" if x == "absolute"
                        else "Anomaly (Departure from Mean)",
                        key="heatmap_mode", horizontal=True)

    if st.button("Generate Heatmap", type="primary"):
        with st.spinner("Generating heatmap..."):
            heatmap_data = analyzer.create_temperature_heatmap(metric=metric, mode=mode)

        if len(heatmap_data) == 0:
            st.warning("No data found.")
            return

        # Plotly heatmap
        if mode == 'absolute':
            colorscale = 'RdYlBu_r'
            colorbar_title = f'{metric} (°F)'
            zmid = None
        else:
            colorscale = 'RdBu_r'
            colorbar_title = 'Anomaly (°F)'
            zmid = 0

        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data.values,
            x=heatmap_data.columns.tolist(),
            y=heatmap_data.index.tolist(),
            colorscale=colorscale,
            zmid=zmid,
            hovertemplate='<b>%{y}</b> %{x}<br>%{z:.1f}°F<extra></extra>',
            colorbar=dict(title=colorbar_title)
        ))

        mode_label = 'Absolute Temperatures' if mode == 'absolute' else 'Anomaly from Long-Term Mean'

        fig.update_layout(
            title=f'{metric} {mode_label} (Monthly)',
            xaxis_title='Month',
            yaxis_title='Year',
            height=max(400, len(heatmap_data) * 12),
            yaxis=dict(autorange='reversed', dtick=5)
        )

        st.plotly_chart(fig, use_container_width=True)

        # Summary
        if mode == 'absolute':
            st.caption(f"Hottest cell: {heatmap_data.max().max():.1f}°F | "
                      f"Coldest cell: {heatmap_data.min().min():.1f}°F")
        else:
            st.caption(f"Max warm anomaly: +{heatmap_data.max().max():.1f}°F | "
                      f"Max cold anomaly: {heatmap_data.min().min():.1f}°F")


def render_climate_band_analysis(analyzer):
    """Render daily record envelope (climate band) analysis UI."""
    st.header("Daily Record Envelope")
    st.markdown("Display the all-time record high, record low, and long-term daily average for each day "
                "of the year. The shaded \"envelope\" shows the full historical range of temperatures. "
                "Optionally overlay a specific year to see how it compared to the historical norms. "
                "Use the date range presets or custom range to focus on a particular season.")

    col1, col2 = st.columns(2)

    with col1:
        metric = st.selectbox("Metric:", ["TMAX", "TMIN", "TAVG"], key="band_metric")

    # Date range selection
    with col2:
        date_preset = st.selectbox("Date Range:", [
            "Full Year", "Winter (Dec-Feb)", "Spring (Mar-May)",
            "Summer (Jun-Aug)", "Fall (Sep-Nov)", "Custom"
        ], key="band_preset")

    presets = {
        "Full Year": (None, None, None, None),
        "Winter (Dec-Feb)": (12, 1, 2, 28),
        "Spring (Mar-May)": (3, 1, 5, 31),
        "Summer (Jun-Aug)": (6, 1, 8, 31),
        "Fall (Sep-Nov)": (9, 1, 11, 30),
    }

    if date_preset == "Custom":
        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a:
            sm = st.selectbox("Start Month:", range(1, 13),
                              format_func=lambda x: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                                     'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][x-1],
                              key="band_sm")
        with col_b:
            sd = st.number_input("Start Day:", min_value=1, max_value=31, value=1, key="band_sd")
        with col_c:
            em = st.selectbox("End Month:", range(1, 13), index=11,
                              format_func=lambda x: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                                     'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][x-1],
                              key="band_em")
        with col_d:
            ed = st.number_input("End Day:", min_value=1, max_value=31, value=31, key="band_ed")
    else:
        sm, sd, em, ed = presets[date_preset]

    # Year overlay
    min_year = int(analyzer.df['DATE'].dt.year.min())
    max_year = int(analyzer.df['DATE'].dt.year.max())
    overlay_year = st.number_input("Overlay Year (0 = none):", min_value=0,
                                   max_value=max_year, value=0, key="band_overlay_year")

    if st.button("Generate Climate Band", type="primary"):
        with st.spinner("Calculating daily records..."):
            records = analyzer.calculate_daily_records(
                metric=metric, start_month=sm, start_day=sd,
                end_month=em, end_day=ed
            )

            overlay_data = None
            if overlay_year > 0:
                overlay_data = analyzer.get_year_overlay_data(
                    year=overlay_year, metric=metric,
                    start_month=sm, start_day=sd,
                    end_month=em, end_day=ed
                )

        if len(records) == 0:
            st.warning("No records found for the specified range.")
            return

        # Summary
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Record High", f"{records['record_high'].max():.0f}°F")
        with col2:
            st.metric("Record Low", f"{records['record_low'].min():.0f}°F")
        with col3:
            st.metric("Warmest Avg Day", f"{records['avg_temp'].max():.1f}°F")
        with col4:
            st.metric("Coldest Avg Day", f"{records['avg_temp'].min():.1f}°F")

        # Plotly chart
        fig = go.Figure()

        # Record high line (upper boundary) - add first for fill reference
        fig.add_trace(go.Scatter(
            x=records['plot_x'], y=records['record_high'],
            mode='lines', name='Record High',
            line=dict(color='rgba(255, 80, 80, 0.5)', width=1, dash='dot'),
            customdata=records['date_label'],
            hovertemplate='%{customdata}<br>Record High: %{y:.0f}°F<extra></extra>'
        ))

        # Record low line (lower boundary) with fill to record high
        fig.add_trace(go.Scatter(
            x=records['plot_x'], y=records['record_low'],
            mode='lines', name='Record Low',
            fill='tonexty',
            fillcolor='rgba(200, 200, 200, 0.25)',
            line=dict(color='rgba(80, 80, 255, 0.5)', width=1, dash='dot'),
            customdata=records['date_label'],
            hovertemplate='%{customdata}<br>Record Low: %{y:.0f}°F<extra></extra>'
        ))

        # Average line
        fig.add_trace(go.Scatter(
            x=records['plot_x'], y=records['avg_temp'],
            mode='lines', name='Long-Term Average',
            line=dict(color='black', width=2),
            customdata=records['date_label'],
            hovertemplate='%{customdata}<br>Average: %{y:.1f}°F<extra></extra>'
        ))

        # Year overlay
        if overlay_data is not None and len(overlay_data) > 0:
            fig.add_trace(go.Scatter(
                x=overlay_data['plot_x'], y=overlay_data['temp'],
                mode='lines+markers', name=f'{overlay_year} Actual',
                line=dict(color='green', width=2),
                marker=dict(size=3),
                customdata=overlay_data['date_label'],
                hovertemplate=f'%{{customdata}}<br>{overlay_year}: %{{y:.0f}}°F<extra></extra>'
            ))

        # X-axis: label with month names at month boundaries
        month_starts = records.groupby('month')['plot_x'].min()
        month_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

        fig.update_layout(
            title=f'Daily {metric} Records' + (f' with {overlay_year} Overlay' if overlay_year > 0 else ''),
            xaxis=dict(
                title='',
                tickmode='array',
                tickvals=month_starts.values,
                ticktext=[month_labels[m-1] for m in month_starts.index]
            ),
            yaxis_title=f'{metric} (°F)',
            hovermode='x unified',
            height=600,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        st.plotly_chart(fig, use_container_width=True)


if __name__ == '__main__':
    main()
