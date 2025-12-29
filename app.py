import streamlit as st
import yfinance as yf
import pandas as pd
import datetime as dt

# Mapping for Interval: (YFinance Interval, Pandas Resample Rule)
INTERVAL_MAP = {
    "Hourly": ("1h", "h"),
    "Daily": ("1d", "D"),
    "Weekly": ("1d", "W"),
    "Quarterly": ("1d", "QE"),
    "Yearly": ("1d", "YE")
}

st.set_page_config(page_title="Stock Price Analyzer", layout="wide")
st.title("📈 Stock Price Analyzer")

# --- SIDEBAR INPUTS ---
st.sidebar.header("Settings")
ticker = st.sidebar.text_input("Stock Ticker", value="SPY")
interval_choice = st.sidebar.selectbox("Interval", list(INTERVAL_MAP.keys()), index=1)

col1, col2 = st.sidebar.columns(2)
start_date = col1.date_input("Start Date", value=dt.date.today() - dt.timedelta(days=365*3))
end_date = col2.date_input("End Date", value=dt.date.today())

if st.sidebar.button("Fetch Data"):
    try:
        yf_interval, resample_rule = INTERVAL_MAP[interval_choice]
        
        # Download data
        df = yf.download(ticker, start=start_date, end=end_date, interval=yf_interval, auto_adjust=False)

        if df.empty:
            st.error("No data found. Note: Hourly data is limited to the last 730 days.")
        else:
            # Data Processing
            close_series = df["Close"]
            if isinstance(close_series, pd.DataFrame):
                close_series = close_series.iloc[:, 0]
            
            resampled = close_series.resample(resample_rule).last()
            data = resampled.to_frame(name="Close Price")
            data["Pct Change"] = data["Close Price"].pct_change() * 100

            # Formatting the Date/Time Column
            if interval_choice == "Quarterly":
                data.index = data.index.to_series().apply(lambda x: f"{x.year}-Q{(x.month-1)//3 + 1}")
            elif interval_choice == "Hourly":
                data.index = data.index.strftime('%Y-%m-%d %H:%M')
            elif interval_choice == "Yearly":
                data.index = data.index.strftime('%Y')
            else:
                data.index = data.index.strftime('%Y-%m-%d')

            # Display Stats
            st.subheader(f"Results for {ticker} ({interval_choice})")
            
            stats_col1, stats_col2 = st.columns(2)
            pct_changes = data["Pct Change"].dropna()
            
            if not pct_changes.empty:
                max_val = pct_changes.max()
                min_val = pct_changes.min()
                stats_col1.metric("Highest % Change", f"{max_val:.2f}%")
                stats_col2.metric("Lowest % Change", f"{min_val:.2f}%")

            # Main Data Table
            # Streamlit dataframes automatically include scrollbars
            st.dataframe(data.style.format({"Close Price": "{:.2f}", "Pct Change": "{:.2f}%"}), use_container_width=True)

    except Exception as e:
        st.error(f"Error: {e}")