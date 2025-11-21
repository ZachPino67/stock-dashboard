import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- PAGE CONFIG ---
st.set_page_config(page_title="QUANT-X: Fusion Terminal", page_icon="🦅", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .stApp {background-color: #0e1117;}
    div.stButton > button:first-child {background-color: #00FF00; color: black;}
</style>
""", unsafe_allow_html=True)

# --- INTELLIGENCE DATABASE ---
RELATIONSHIPS = {
    'NVDA': [
        {'ticker': 'TSM', 'name': 'Taiwan Semi', 'role': 'Supplier (Foundry)', 'why': 'Manufactures 100% of Nvidia chips.'},
        {'ticker': 'SMCI', 'name': 'Super Micro', 'role': 'Customer/Partner', 'why': 'Builds the servers NVDA chips go into.'},
        {'ticker': 'VRT', 'name': 'Vertiv', 'role': 'Infrastructure', 'why': 'Cooling systems for AI Data Centers.'},
        {'ticker': 'AMD', 'name': 'AMD', 'role': 'Rival', 'why': 'Direct competitor in GPU market.'}
    ],
    'AAPL': [
        {'ticker': 'SWKS', 'name': 'Skyworks', 'role': 'Supplier (Radio)', 'why': 'Makes 5G/Antenna chips for iPhone.'},
        {'ticker': 'QCOM', 'name': 'Qualcomm', 'role': 'Supplier (Modem)', 'why': 'Provides 5G modems (Critical).'},
        {'ticker': 'CRUS', 'name': 'Cirrus Logic', 'role': 'Supplier (Audio)', 'why': 'Audio chips (80% rev comes from Apple).'},
        {'ticker': 'GLW', 'name': 'Corning', 'role': 'Supplier (Glass)', 'why': 'Makes the "Gorilla Glass" screens.'}
    ],
    'TSLA': [
        {'ticker': 'ALB', 'name': 'Albemarle', 'role': 'Supplier (Raw)', 'why': 'World largest Lithium miner (Batteries).'},
        {'ticker': 'RIVN', 'name': 'Rivian', 'role': 'Rival', 'why': 'High-end EV Truck competitor.'},
        {'ticker': 'BYDDF', 'name': 'BYD', 'role': 'Rival (Global)', 'why': 'Biggest EV rival in China.'}
    ],
    'MSFT': [
        {'ticker': 'CRWD', 'name': 'CrowdStrike', 'role': '
