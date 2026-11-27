# -*- coding: utf-8 -*-
"""
Thai Stock Scanner Module
Multi-strategy scanner for SET50, SET100, and custom lists
"""

import concurrent.futures
from typing import List, Dict, Any, Optional
import pandas as pd
from stocks_data import SET50_SYMBOLS, SET100_SYMBOLS, fetch_price_history, fetch_stock_info, clean_symbol
from indicators import add_all_indicators

SCAN_STRATEGIES = {
    "all": "สแกนภาพรวมและประเมินสัญญาณทั้งหมด (All Signals Overview)",
    "golden_cross": "EMA Golden Cross (EMA20 ตัดขึ้นเหนือ EMA50 หรือ ราคา > EMA200)",
    "macd_bullish": "MACD Bullish Cross (MACD ตัดขึ้นเหนือ Signal Line)",
    "rsi_oversold": "RSI Oversold (RSI < 35 มีโอกาสรีบาวด์ดีดกลับ)",
    "volume_breakout": "Volume Breakout (Volume พุ่งเกิน 1.8 เท่าของค่าเฉลี่ย + ราคาบวก)",
    "bollinger_breakout": "Bollinger Bands Breakout (ทะลุกรอบบน หรือ บีบตัวเตรียมระเบิด)",
    "high_dividend_value": "หุ้นปันผลเด่น & มูลค่าน่าสนใจ (Div >= 4%, PE <= 18, PBV <= 2)",
    "breakout_52w": "จ่อทะลุ High 52 สัปดาห์ (ภายใน 5% จาก New High)"
}

def scan_single_stock(symbol: str, strategy: str = "all") -> Optional[Dict[str, Any]]:
    """Scan and evaluate a single stock against the chosen strategy"""
    sym = clean_symbol(symbol)
    df = fetch_price_history(sym, period="1y")
    if df.empty or len(df) < 50:
        return None

    df_ind = add_all_indicators(df)
    last = df_ind.iloc[-1]
    prev1 = df_ind.iloc[-2]
    prev2 = df_ind.iloc[-3] if len(df_ind) >= 3 else prev1

    info = fetch_stock_info(sym, use_cache=True)

    close = float(last['Close'])
    change_pct = float(last['Change_Pct'])
    rsi = float(last['RSI14']) if not pd.isna(last['RSI14']) else 50.0
    vol_ratio = float(last['Vol_Ratio']) if not pd.isna(last['Vol_Ratio']) else 1.0
    ema20 = float(last['EMA20']) if not pd.isna(last['EMA20']) else close
    ema50 = float(last['EMA50']) if not pd.isna(last['EMA50']) else close
    ema200 = float(last['EMA200']) if not pd.isna(last['EMA200']) else close

    macd = float(last['MACD']) if not pd.isna(last['MACD']) else 0.0
    macd_signal = float(last['MACD_Signal']) if not pd.isna(last['MACD_Signal']) else 0.0
    prev_macd = float(prev1['MACD']) if not pd.isna(prev1['MACD']) else 0.0
    prev_signal = float(prev1['MACD_Signal']) if not pd.isna(prev1['MACD_Signal']) else 0.0

    bb_upper = float(last['BB_Upper']) if not pd.isna(last['BB_Upper']) else close
    bb_lower = float(last['BB_Lower']) if not pd.isna(last['BB_Lower']) else close
    bb_width = float(last['BB_Width']) if not pd.isna(last['BB_Width']) else 10.0

    pe = info.get("pe_ratio")
    pbv = info.get("pbv_ratio")
    div_yield = info.get("dividend_yield")
    high_52w = info.get("fifty_two_week_high") or float(df['High'].max())

    # Strategy signals
    is_golden_cross = (ema20 > ema50 and close > ema200) or (prev1['EMA20'] <= prev1['EMA50'] and ema20 > ema50)
    is_macd_cross = (prev_macd <= prev_signal and macd > macd_signal) or (macd > macd_signal and macd > 0)
    is_rsi_oversold = rsi < 35.0
    is_vol_breakout = (vol_ratio >= 1.8) and (change_pct >= 1.2)
    is_bb_breakout = (close >= bb_upper) or (bb_width < 7.0 and change_pct > 1.0)
    is_dividend_val = (div_yield is not None and div_yield >= 4.0) and (pe is not None and 0 < pe <= 18.0)
    is_52w_breakout = (high_52w is not None and high_52w > 0) and (close >= high_52w * 0.95)

    # Filtering based on strategy
    match = False
    signal_tags = []

    if is_golden_cross:
        signal_tags.append("EMA Golden Cross")
    if is_macd_cross:
        signal_tags.append("MACD Bullish")
    if is_rsi_oversold:
        signal_tags.append("RSI Oversold")
    if is_vol_breakout:
        signal_tags.append("Volume Breakout")
    if is_bb_breakout:
        signal_tags.append("BB Breakout/Squeeze")
    if is_dividend_val:
        signal_tags.append("High Dividend & Value")
    if is_52w_breakout:
        signal_tags.append("Near 52W High")

    if strategy == "all":
        match = len(signal_tags) > 0
    elif strategy == "golden_cross" and is_golden_cross:
        match = True
    elif strategy == "macd_bullish" and is_macd_cross:
        match = True
    elif strategy == "rsi_oversold" and is_rsi_oversold:
        match = True
    elif strategy == "volume_breakout" and is_vol_breakout:
        match = True
    elif strategy == "bollinger_breakout" and is_bb_breakout:
        match = True
    elif strategy == "high_dividend_value" and is_dividend_val:
        match = True
    elif strategy == "breakout_52w" and is_52w_breakout:
        match = True

    if not match:
        return None

    # Calculate overall bullish strength score (0 to 100)
    score = 50.0
    if close > ema200: score += 15
    if ema20 > ema50: score += 10
    if macd > macd_signal: score += 10
    if macd > 0: score += 5
    if 45 <= rsi <= 65: score += 10
    elif rsi < 35: score += 5  # Rebound potential
    if vol_ratio > 1.5: score += 10
    if div_yield and div_yield > 4.0: score += 5
    score = min(100.0, max(0.0, score))

    return {
        "symbol": sym,
        "name": info.get("name", sym),
        "sector": info.get("sector", "Other"),
        "price": round(close, 2),
        "change_pct": round(change_pct, 2),
        "volume_ratio": round(vol_ratio, 2),
        "rsi": round(rsi, 1),
        "macd": round(macd, 3),
        "macd_signal": round(macd_signal, 3),
        "ema20": round(ema20, 2),
        "ema50": round(ema50, 2),
        "ema200": round(ema200, 2),
        "pe": pe,
        "pbv": pbv,
        "div_yield": div_yield,
        "score": round(score, 1),
        "signals": signal_tags
    }

def run_scanner(symbols: Optional[List[str]] = None, strategy: str = "all", max_workers: int = 8) -> pd.DataFrame:
    """Run parallel scanner across symbols list"""
    if symbols is None or len(symbols) == 0:
        symbols = SET50_SYMBOLS

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_sym = {executor.submit(scan_single_stock, s, strategy): s for s in symbols}
        for future in concurrent.futures.as_completed(future_to_sym):
            try:
                res = future.result()
                if res:
                    results.append(res)
            except Exception as e:
                pass

    if not results:
        return pd.DataFrame()

    df_res = pd.DataFrame(results)
    df_res.sort_values(by="score", ascending=False, inplace=True)
    df_res.reset_index(drop=True, inplace=True)
    return df_res
