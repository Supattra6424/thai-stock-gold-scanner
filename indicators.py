# -*- coding: utf-8 -*-
"""
Technical Indicators Calculation Module
Computes EMA, SMA, RSI, MACD, Bollinger Bands, ATR, Volume Metrics, and Support/Resistance
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple

def calculate_ema(series: pd.Series, span: int) -> pd.Series:
    """Exponential Moving Average"""
    return series.ewm(span=span, adjust=False).mean()

def calculate_sma(series: pd.Series, window: int) -> pd.Series:
    """Simple Moving Average"""
    return series.rolling(window=window).mean()

def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index (RSI) using Wilder's Smoothing"""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    # Wilder exponential moving average
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()

    rs = avg_gain / (avg_loss + 1e-10)
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Moving Average Convergence Divergence (MACD)"""
    fast_ema = calculate_ema(series, fast)
    slow_ema = calculate_ema(series, slow)
    macd_line = fast_ema - slow_ema
    signal_line = calculate_ema(macd_line, signal)
    macd_hist = macd_line - signal_line
    return macd_line, signal_line, macd_hist

def calculate_bollinger_bands(series: pd.Series, period: int = 20, num_std: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
    """Bollinger Bands (Upper, Middle, Lower, Bandwidth)"""
    middle = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    upper = middle + (std * num_std)
    lower = middle - (std * num_std)
    bandwidth = ((upper - lower) / (middle + 1e-10)) * 100
    return upper, middle, lower, bandwidth

def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average True Range (ATR)"""
    high = df['High']
    low = df['Low']
    close = df['Close']
    prev_close = close.shift(1)

    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    return atr

def calculate_support_resistance(df: pd.DataFrame, window: int = 20) -> Dict[str, float]:
    """Calculate recent support & resistance levels and standard Pivot Points"""
    if len(df) < window:
        window = len(df)
    
    recent_high = float(df['High'].iloc[-window:].max())
    recent_low = float(df['Low'].iloc[-window:].min())
    
    last = df.iloc[-1]
    last_high = float(last['High'])
    last_low = float(last['Low'])
    last_close = float(last['Close'])

    pivot = (last_high + last_low + last_close) / 3.0
    r1 = (2 * pivot) - last_low
    s1 = (2 * pivot) - last_high
    r2 = pivot + (last_high - last_low)
    s2 = pivot - (last_high - last_low)

    return {
        "recent_high_20d": round(recent_high, 2),
        "recent_low_20d": round(recent_low, 2),
        "pivot": round(pivot, 2),
        "resistance_1": round(r1, 2),
        "support_1": round(s1, 2),
        "resistance_2": round(r2, 2),
        "support_2": round(s2, 2)
    }

def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Enrich dataframe with full suite of technical indicators"""
    if df.empty or len(df) < 20:
        return df

    res = df.copy()
    close = res['Close']
    vol = res['Volume']

    # EMAs & SMAs
    res['EMA10'] = calculate_ema(close, 10)
    res['EMA20'] = calculate_ema(close, 20)
    res['EMA50'] = calculate_ema(close, 50)
    res['EMA200'] = calculate_ema(close, 200)
    res['SMA50'] = calculate_sma(close, 50)
    res['SMA200'] = calculate_sma(close, 200)

    # RSI
    res['RSI14'] = calculate_rsi(close, 14)

    # MACD
    macd, signal, hist = calculate_macd(close, 12, 26, 9)
    res['MACD'] = macd
    res['MACD_Signal'] = signal
    res['MACD_Hist'] = hist

    # Bollinger Bands
    bb_up, bb_mid, bb_low, bb_width = calculate_bollinger_bands(close, 20, 2.0)
    res['BB_Upper'] = bb_up
    res['BB_Middle'] = bb_mid
    res['BB_Lower'] = bb_low
    res['BB_Width'] = bb_width

    # Volume Indicators
    res['Vol_SMA20'] = calculate_sma(vol, 20)
    res['Vol_Ratio'] = (vol / (res['Vol_SMA20'] + 1e-10)).round(2)

    # Price Changes
    res['Change_Pct'] = res['Close'].pct_change() * 100

    # ATR
    res['ATR14'] = calculate_atr(res, 14)

    return res
