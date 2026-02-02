#!/usr/bin/env python3
"""
Streamlit GUI for Temperature Analysis Tool.

Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
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
                "Threshold Histogram"
            ]
        )

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


def render_streak_analysis(analyzer):
    """Render temperature streak analysis UI."""
    st.header("Temperature Streaks")
    st.markdown("Find longest consecutive periods where temperature stayed above or below a threshold.")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        metric = st.selectbox("Metric:", ["TMAX", "TMIN", "TAVG"], key="streak_metric")
    with col2:
        threshold = st.number_input("Threshold (°F):", value=90.0, step=1.0, key="streak_threshold")
    with col3:
        direction = st.selectbox("Direction:", ["above", "below"], key="streak_direction")
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
        st.subheader(f"Top {len(streaks)} Streaks: {metric} {direction} {threshold}°F")

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
    st.markdown("Find the coldest or warmest N-day periods based on rolling averages.")

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
    st.markdown("Find the coldest or warmest seasons across all years.")
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
    st.markdown("Find coldest or warmest instances of a specific date range across all years.")

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
    st.markdown("Analyze how often temperature meets a threshold within a date range across all years.")

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
        direction = st.selectbox("Direction:", ["below", "above"], key="hist_direction")

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


if __name__ == '__main__':
    main()
