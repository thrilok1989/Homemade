import streamlit as st
from streamlit_autorefresh import st_autorefresh
import requests
import pandas as pd
import numpy as np
from datetime import datetime
import math
from scipy.stats import norm
from pytz import timezone
import plotly.graph_objects as go
import io

# === Streamlit Config ===
st.set_page_config(page_title="NSE Options Analyzer", layout="wide")
st_autorefresh(interval=120000, key="datarefresh")  # Refresh every 2 min

# Define all instruments we'll analyze
INSTRUMENTS = {
    'indices': {
        'NIFTY': {'lot_size': 75, 'zone_size': 20, 'atm_range': 200},
        'BANKNIFTY': {'lot_size': 25, 'zone_size': 100, 'atm_range': 500},
        'NIFTY IT': {'lot_size': 50, 'zone_size': 50, 'atm_range': 300},
        'NIFTY AUTO': {'lot_size': 50, 'zone_size': 50, 'atm_range': 300}
    },
    'stocks': {
        'TCS': {'lot_size': 150, 'zone_size': 30, 'atm_range': 150},
        'RELIANCE': {'lot_size': 250, 'zone_size': 40, 'atm_range': 200},
        'HDFCBANK': {'lot_size': 550, 'zone_size': 50, 'atm_range': 250}
    }
}

# Initialize session states for all instruments
for category in INSTRUMENTS:
    for instrument in INSTRUMENTS[category]:
        if f'{instrument}_price_data' not in st.session_state:
            st.session_state[f'{instrument}_price_data'] = pd.DataFrame(columns=["Time", "Spot"])
        
        if f'{instrument}_trade_log' not in st.session_state:
            st.session_state[f'{instrument}_trade_log'] = []
        
        if f'{instrument}_call_log_book' not in st.session_state:
            st.session_state[f'{instrument}_call_log_book'] = []
        
        if f'{instrument}_support_zone' not in st.session_state:
            st.session_state[f'{instrument}_support_zone'] = (None, None)
        
        if f'{instrument}_resistance_zone' not in st.session_state:
            st.session_state[f'{instrument}_resistance_zone'] = (None, None)

# === Telegram Config ===
TELEGRAM_BOT_TOKEN = "8133685842:AAGdHCpi9QRIsS-fWW5Y1ArgKJvS95QL9xU"
TELEGRAM_CHAT_ID = "5704496584"