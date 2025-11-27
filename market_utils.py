import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- CONFIGURATION ---
LIQUID_WATCHLIST = [
    'SPY', 'QQQ', 'IWM', 'NVDA', 'TSLA', 'AMD', 
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 
    'NFLX', 'COIN', 'MSTR', 'PLTR'
]

def get_macro_pulse():
    """Fetches key macro indicators: VIX, 10Y Yield, Dollar."""
    tickers = ['^VIX', '^TNX', 'DX-Y.NYB']
    try:
        data = yf.download(tickers, period="5d", progress=False)['Close']
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
            
        pulse = {}
        # VIX
        if '^VIX' in data:
            vix = data['^VIX'].iloc[-1]
            vix_prev = data['^VIX'].iloc[-2]
            pulse['VIX'] = {"val": vix, "delta": vix - vix_prev}
        
        # 10Y Yield (^TNX is usually index points, e.g., 42.50 = 4.25%)
        if '^TNX' in data:
            tnx = data['^TNX'].iloc[-1]
            tnx_prev = data['^TNX'].iloc[-2]
            pulse['TNX'] = {"val": tnx/10, "delta": (tnx - tnx_prev)/10}
            
        # DXY
        if 'DX-Y.NYB' in data:
            dxy = data['DX-Y.NYB'].iloc[-1]
            dxy_prev = data['DX-Y.NYB'].iloc[-2]
            pulse['DXY'] = {"val": dxy, "delta": dxy - dxy_prev}
            
        return pulse
    except Exception as e:
        return None

def get_market_regime():
    """
    Calculates institutional regime indicators.
    1. VIX Term Structure Proxy (VIX9D vs VIX).
    2. Risk Appetite (XLY vs XLP).
    3. Trend (SPY vs 200 SMA).
    """
    try:
        # VIX9D is 9-day vol, VIX is 30-day. 
        # If 9D > 30D, we are in BACKWARDATION (Panic).
        # XLY (Discretionary) / XLP (Staples) > Rising means Risk On.
        tickers = ['^VIX9D', '^VIX', 'XLY', 'XLP', 'SPY']
        data = yf.download(tickers, period="1y", progress=False)['Close']
        
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        regime = {}

        # 1. Term Structure
        if '^VIX9D' in data and '^VIX' in data:
            v9 = data['^VIX9D'].iloc[-1]
            v30 = data['^VIX'].iloc[-1]
            ratio = v9 / v30
            state = "Backwardation (PANIC)" if ratio > 1.05 else "Contango (Normal)"
            regime['Term_Structure'] = {"ratio": ratio, "state": state, "v9": v9, "v30": v30}

        # 2. Risk Gauge
        if 'XLY' in data and 'XLP' in data:
            curr = data['XLY'].iloc[-1] / data['XLP'].iloc[-1]
            prev = data['XLY'].iloc[-5] / data['XLP'].iloc[-5] # 1 week ago
            trend = "Risk ON" if curr > prev else "Risk OFF"
            regime['Risk_Gauge'] = {"val": curr, "trend": trend}

        # 3. SPY 200 SMA
        if 'SPY' in data:
            spy_price = data['SPY'].iloc[-1]
            sma_200 = data['SPY'].rolling(window=200).mean().iloc[-1]
            dist = (spy_price - sma_200) / sma_200 * 100
            regime['SPY_Trend'] = {"price": spy_price, "sma200": sma_200, "dist": dist}

        return regime
    except:
        return None

def scan_volatility_opportunities():
    """Scans Liquid Watchlist for High IV Rank."""
    results = []
    try:
        data = yf.download(LIQUID_WATCHLIST, period="1y", group_by='ticker', progress=False)
        
        for ticker in LIQUID_WATCHLIST:
            try:
                df = data[ticker]
                if df.empty: continue
                
                df['Log_Ret'] = np.log(df['Close'] / df['Close'].shift(1))
                df['Vol'] = df['Log_Ret'].rolling(window=30).std() * np.sqrt(252) * 100
                
                vol_clean = df['Vol'].dropna()
                if vol_clean.empty: continue
                
                current_vol = vol_clean.iloc[-1]
                min_vol, max_vol = vol_clean.min(), vol_clean.max()
                
                iv_rank = 0
                if max_vol != min_vol:
                    iv_rank = (current_vol - min_vol) / (max_vol - min_vol) * 100
                
                results.append({
                    "Ticker": ticker,
                    "Price": df['Close'].iloc[-1],
                    "IV Rank": iv_rank,
                    "Current IV": current_vol
                })
            except: continue
                
        return pd.DataFrame(results).sort_values("IV Rank", ascending=False)
    except:
        return pd.DataFrame()
