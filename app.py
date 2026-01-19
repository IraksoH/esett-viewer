"""
eSett Data Viewer - Interactive visualization of eSett API data

Fetches and visualizes price data from eSett OpenData API.
"""

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(
    page_title="eSett Price Viewer",
    page_icon="",
    layout="wide",
)

st.title("eSett Price Data Viewer")
st.caption("Visualize imbalance and regulation prices from eSett OpenData API")

# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    
    # MBA selection (Market Balance Area)
    mba_options = {
        "SE1 (Luleå)": "SE1",
        "SE2 (Sundsvall)": "SE2",
        "SE3 (Stockholm)": "SE3",
        "SE4 (Malmö)": "SE4",
        "FI (Finland)": "10YFI_1________U",
        "NO1 (Oslo)": "NO1",
        "NO2 (Kristiansand)": "NO2",
        "NO3 (Trondheim)": "NO3",
        "NO4 (Tromsø)": "NO4",
        "NO5 (Bergen)": "NO5",
        "DK1 (West Denmark)": "DK1",
        "DK2 (East Denmark)": "DK2",
    }
    
    mba_label = st.selectbox("Market Balance Area", options=list(mba_options.keys()), index=0)
    mba_code = mba_options[mba_label]
    
    # Date range
    st.subheader("Date Range")
    end_date = st.date_input(
        "End Date",
        value=datetime.now().date(),
        max_value=datetime.now().date()
    )
    start_date = st.date_input(
        "Start Date",
        value=end_date - timedelta(days=30)
    )
    
    # Price fields to display
    st.subheader("Price Types")
    show_imbl_sales = st.checkbox("Imbalance Sales Price", value=True)
    show_imbl_purchase = st.checkbox("Imbalance Purchase Price", value=True)
    show_up_reg = st.checkbox("Up Regulation Price", value=True)
    show_down_reg = st.checkbox("Down Regulation Price", value=True)
    show_spot_diff = st.checkbox("Imbalance Spot Difference", value=False)
    
    st.subheader("Additional Data")
    show_main_dir = st.checkbox("Main Direction Regulation Power", value=False)
    
    fetch_button = st.button("Fetch Data", type="primary", use_container_width=True)


@st.cache_data(show_spinner=True)
def fetch_esett_data(start_dt: datetime, end_dt: datetime, mba: str) -> pd.DataFrame:
    """
    Fetch data from eSett OpenData API.
    
    Args:
        start_dt: Start datetime
        end_dt: End datetime
        mba: Market Balance Area code
        
    Returns:
        DataFrame with price data
    """
    # Format dates for API (ISO 8601 format with timezone)
    start_str = start_dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    end_str = end_dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    
    # Build API URL
    url = "https://api.opendata.esett.com/EXP14/Prices"
    params = {
        "start": start_str,
        "end": end_str,
        "mba": mba
    }
    headers = {
        "accept": "application/json"
    }
    
    # Make request
    response = requests.get(url, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    
    # Parse JSON
    data = response.json()
    
    # Check if data is empty
    if not data:
        return pd.DataFrame()
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Parse timestamp - handle both 'timestamp' and 'timestampUTC'
    # Convert from UTC to UTC+2 (EET/EEST timezone)
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    elif 'timestampUTC' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestampUTC'], errors='coerce')
    else:
        raise ValueError("No timestamp column found in response")
    
    # Convert timestamps from UTC to UTC+2
    # First ensure timezone aware, then convert to UTC+2
    df['timestamp'] = df['timestamp'].dt.tz_localize('UTC').dt.tz_convert('Etc/GMT-2')
    # Remove timezone info for plotting (keep the values as UTC+2)
    df['timestamp'] = df['timestamp'].dt.tz_localize(None)
    
    # Remove rows with invalid timestamps
    df = df.dropna(subset=['timestamp'])
    
    # Sort by timestamp
    df = df.sort_values('timestamp')
    
    return df


# Main area
if fetch_button:
    try:
        # Convert dates to datetime
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())
        
        # Fetch data
        with st.spinner(f"Fetching data from eSett API for {mba_label}..."):
            df = fetch_esett_data(start_dt, end_dt, mba_code)
        
        # Check if data was returned
        if df.empty:
            st.warning(f"No data available for {mba_label} in the selected date range.")
            st.info("Try selecting a different date range or Market Balance Area.")
            st.stop()
        
        # Check if timestamp column exists
        if 'timestamp' not in df.columns:
            st.error("Data format error: timestamp column missing")
            st.info("The API response format may be unexpected. Please try a different Market Balance Area or date range.")
            with st.expander("Available columns"):
                st.write(df.columns.tolist())
            st.stop()
        
        st.success(f"Fetched {len(df)} records from {df['timestamp'].min()} to {df['timestamp'].max()}")
        
        # Store in session state
        st.session_state['esett_data'] = df
        st.session_state['mba_label'] = mba_label
        
    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {e}")
        st.info("Tip: Some Market Balance Areas may not have data for all date ranges. Try adjusting the date range or selecting a different area.")
    except ValueError as e:
        st.error(f"Data parsing error: {e}")
        st.info("The API response format may be different for this area. Please try a different Market Balance Area.")
    except Exception as e:
        st.error(f"Error: {e}")
        import traceback
        with st.expander("Error details"):
            st.code(traceback.format_exc())

# Display data if available
if 'esett_data' in st.session_state:
    df = st.session_state['esett_data']
    mba_label = st.session_state.get('mba_label', 'Unknown')
    
    # Statistics
    st.subheader("Summary Statistics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_imbl_sales = df['imblSalesPrice'].mean()
        st.metric("Avg Imbalance Sales", f"{avg_imbl_sales:.2f} €/MWh")
    with col2:
        avg_imbl_purchase = df['imblPurchasePrice'].mean()
        st.metric("Avg Imbalance Purchase", f"{avg_imbl_purchase:.2f} €/MWh")
    with col3:
        avg_up_reg = df['upRegPrice'].mean()
        st.metric("Avg Up Regulation", f"{avg_up_reg:.2f} €/MWh")
    with col4:
        avg_down_reg = df['downRegPrice'].mean()
        st.metric("Avg Down Regulation", f"{avg_down_reg:.2f} €/MWh")
    
    # Create interactive chart
    st.subheader("Price Time Series")
    st.caption("Times displayed in UTC+2 timezone")
    
    fig = go.Figure()

    color1 = st.color_picker("Pick A Color", "#00f900")
    st.write("The current color is", color1)
    
    # Add selected price traces
    if show_imbl_sales:
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['imblSalesPrice'],
            mode='lines',
            name='Imbalance Sales Price',
            line=dict(color='color1, width=2)
        ))
    
    if show_imbl_purchase:
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['imblPurchasePrice'],
            mode='lines',
            name='Imbalance Purchase Price',
            line=dict(color='#A23B72', width=2)
        ))
    
    if show_up_reg:
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['upRegPrice'],
            mode='lines',
            name='Up Regulation Price',
            line=dict(color='#F18F01', width=2)
        ))
    
    if show_down_reg:
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['downRegPrice'],
            mode='lines',
            name='Down Regulation Price',
            line=dict(color='#24bf72', width=2)
        ))
    
    if show_spot_diff:
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['imblSpotDifferencePrice'],
            mode='lines',
            name='Imbalance Spot Difference',
            line=dict(color='#6A994E', width=2)
        ))
    
    if show_main_dir:
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['mainDirRegPowerPerMBA'],
            mode='lines+markers',
            name='Main Direction Regulation Power',
            line=dict(color='#8B4513', width=2),
            marker=dict(size=4),
            yaxis='y2'
        ))
    
    # Update layout
    fig.update_layout(
        title=f"eSett Prices - {mba_label}",
        xaxis_title="Time (UTC+2)",
        yaxis_title="Price (€/MWh)",
        hovermode='x unified',
        height=600,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        plot_bgcolor='white',
        xaxis=dict(
            showgrid=True,
            gridcolor='lightgray',
            showline=True,
            linecolor='gray'
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='lightgray',
            showline=True,
            linecolor='gray'
        )
    )
    
    # Add secondary y-axis for main direction if displayed
    if show_main_dir:
        fig.update_layout(
            yaxis2=dict(
                title="Direction (-1=Down, 0=Neutral, 1=Up)",
                overlaying='y',
                side='right',
                showgrid=False,
                range=[-1.5, 1.5]
            )
        )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Data table
    st.subheader("Raw Data")
    
    # Select relevant columns
    display_cols = ['timestamp', 'mba']
    if show_imbl_sales:
        display_cols.append('imblSalesPrice')
    if show_imbl_purchase:
        display_cols.append('imblPurchasePrice')
    if show_up_reg:
        display_cols.append('upRegPrice')
    if show_down_reg:
        display_cols.append('downRegPrice')
    if show_spot_diff:
        display_cols.append('imblSpotDifferencePrice')
    if show_main_dir:
        display_cols.append('mainDirRegPowerPerMBA')
    
    st.dataframe(
        df[display_cols].tail(100),
        use_container_width=True,
        hide_index=True
    )
    
    # Download button
    csv = df.to_csv(index=False)
    st.download_button(
        label="⬇️ Download CSV",
        data=csv,
        file_name=f"esett_prices_{mba_label}_{start_date}_{end_date}.csv",
        mime="text/csv"
    )

else:
    st.info("Configure the settings in the sidebar and click 'Fetch Data' to start.")
    
    # Show example
    with st.expander("About eSett Data"):
        st.markdown("""
        ### eSett OpenData API
        
        This tool visualizes price data from the eSett OpenData API.
        
        **Available Price Types:**
        - **Imbalance Sales Price**: Price for selling imbalance energy
        - **Imbalance Purchase Price**: Price for purchasing imbalance energy
        - **Up Regulation Price**: Price for up-regulation
        - **Down Regulation Price**: Price for down-regulation
        - **Imbalance Spot Difference**: Difference between imbalance and spot price
        
        **Market Balance Areas (MBA):**
        - Sweden: SE1, SE2, SE3, SE4
        - Finland: FI
        - Norway: NO1, NO2, NO3, NO4, NO5
        - Denmark: DK1, DK2
        
        **Data Source:** [eSett OpenData API](https://api.opendata.esett.com)
        """)
