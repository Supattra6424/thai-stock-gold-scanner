# -*- coding: utf-8 -*-
"""
Thai Stock Deep-Dive Analyzer Module
Provides in-depth technical analysis, fundamental evaluation, and automated trade plan setups
(Buy & Sell Points Strategy Analysis)
"""

from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np
from stocks_data import fetch_price_history, fetch_stock_info, clean_symbol
from indicators import add_all_indicators, calculate_support_resistance

def detect_buy_sell_signals(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Detect historical and latest actionable Buy and Sell trigger points
    Returns signal flags, descriptions, and indices for chart markers
    """
    if len(df) < 5:
        return {"buy_signals": [], "sell_signals": [], "chart_markers": []}

    buy_signals = []
    sell_signals = []
    markers = []

    last = df.iloc[-1]
    prev1 = df.iloc[-2]
    prev2 = df.iloc[-3] if len(df) >= 3 else prev1

    close = float(last['Close'])
    prev_close = float(prev1['Close'])

    ema20 = float(last['EMA20'])
    ema50 = float(last['EMA50'])
    ema200 = float(last['EMA200'])

    prev_ema20 = float(prev1['EMA20'])
    prev_ema50 = float(prev1['EMA50'])

    rsi = float(last['RSI14'])
    prev_rsi = float(prev1['RSI14'])

    macd = float(last['MACD'])
    signal = float(last['MACD_Signal'])
    prev_macd = float(prev1['MACD'])
    prev_signal = float(prev1['MACD_Signal'])

    bb_up = float(last['BB_Upper'])
    bb_low = float(last['BB_Lower'])
    vol_ratio = float(last['Vol_Ratio'])

    # --- BUY TRIGGERS ---
    # 1. EMA Golden Cross
    if prev_ema20 <= prev_ema50 and ema20 > ema50:
        buy_signals.append("🔔 สัญญาณซื้อรันเทรนด์: EMA 20 เพิ่งตัดขึ้นเหนือ EMA 50 (Golden Cross)")
    elif ema20 > ema50 and close > ema200:
        buy_signals.append("✅ แนวโน้มขาขึ้นสมบูรณ์: ราคายืนเหนือ EMA 20, 50, 200 (Buy on Dip เมื่อย่อตัว)")

    # 2. MACD Bullish Crossover
    if prev_macd <= prev_signal and macd > signal:
        buy_signals.append("⚡ สัญญาณซื้อกลับตัว: MACD เพิ่งตัดขึ้นเหนือ Signal Line (จุดเริ่มรอบใหม่)")
    elif macd > signal and macd > 0:
        buy_signals.append("✅ โมเมนตัมขาขึ้น: MACD อยู่เหนือ Signal Line และสูงกว่าระดับ 0")

    # 3. RSI Oversold Reversal
    if prev_rsi < 35 and rsi >= 35:
        buy_signals.append(f"🎯 สัญญาณซื้อดักรีบาวด์: RSI เพิ่งดีดตัวหลุดโซน Oversold ขึ้นมาที่ {rsi:.1f}")
    elif rsi < 35:
        buy_signals.append(f"🛒 โซนทยอยสะสม: RSI อยู่ในเขต Oversold ({rsi:.1f}) มีโอกาสเกิด Technical Rebound")

    # 4. Bollinger Bounce
    if prev_close <= bb_low and close > bb_low:
        buy_signals.append("📈 สัญญาณซื้อเด้งกรอบล่าง: ราคาเด้งกลับจากขอบล่าง Bollinger Bands")

    # 5. Volume Breakout
    if vol_ratio >= 1.8 and close > prev_close:
        buy_signals.append(f"💥 สัญญาณซื้อตามน้ำ (Breakout): ปริมาณซื้อขายหนาแน่นผิดปกติ ({vol_ratio:.1f}x) แท่งเทียนเขียว")

    # --- SELL TRIGGERS (Take Profit & Stop Loss) ---
    # 1. EMA Death Cross
    if prev_ema20 >= prev_ema50 and ema20 < ema50:
        sell_signals.append("🚨 สัญญาณขายตัดขาดทุน/หนีรอบ: EMA 20 เพิ่งตัดลงต่ำกว่า EMA 50 (Death Cross)")
    elif close < ema200 and prev_close >= ema200:
        sell_signals.append("⚠️ สัญญาณขายเตือนภัย: ราคาหลุดเส้นค่าเฉลี่ย 200 วัน (เปลี่ยนแนวโน้มเป็นขาลง)")

    # 2. MACD Bearish Crossover
    if prev_macd >= prev_signal and macd < signal:
        sell_signals.append("🚨 สัญญาณขายทำกำไร/ลดพอร์ต: MACD เพิ่งตัดลงต่ำกว่า Signal Line (สูญเสียโมเมนตัม)")
    elif macd < signal and macd < 0:
        sell_signals.append("⚠️ สัญญาณระวัง: MACD อยู่ในแดนลบและต่ำกว่า Signal Line (แรงขายครอบงำ)")

    # 3. RSI Overbought
    if rsi >= 70:
        sell_signals.append(f"💰 สัญญาณทยอยขายทำกำไร (Take Profit): RSI เข้าเขต Overbought ({rsi:.1f}) ระวังแรงขายทำกำไร")

    # 4. Bollinger Upper Band Resistance
    if close >= bb_up:
        sell_signals.append("🎯 จุดขายทำกำไรระยะสั้น: ราคาแตะขอบบน Bollinger Bands มีโอกาสพักฐาน")

    # Generate recent chart markers for buy/sell
    for i in range(max(0, len(df) - 60), len(df)):
        d_prev = df.iloc[i - 1] if i > 0 else df.iloc[i]
        d_curr = df.iloc[i]
        d_date = df.index[i]
        d_close = float(d_curr['Close'])
        d_low = float(d_curr['Low'])
        d_high = float(d_curr['High'])

        # Buy Marker: MACD cross up or EMA cross up
        m_cross_up = (d_prev['MACD'] <= d_prev['MACD_Signal']) and (d_curr['MACD'] > d_curr['MACD_Signal'])
        ema_cross_up = (d_prev['EMA20'] <= d_prev['EMA50']) and (d_curr['EMA20'] > d_curr['EMA50'])
        if m_cross_up or ema_cross_up:
            markers.append({
                "date": d_date, "price": d_low * 0.985, "type": "BUY",
                "text": "BUY" if not m_cross_up else "MACD BUY", "color": "#2e7d32"
            })

        # Sell Marker: MACD cross down or EMA cross down
        m_cross_down = (d_prev['MACD'] >= d_prev['MACD_Signal']) and (d_curr['MACD'] < d_curr['MACD_Signal'])
        ema_cross_down = (d_prev['EMA20'] >= d_prev['EMA50']) and (d_curr['EMA20'] < d_curr['EMA50'])
        if m_cross_down or ema_cross_down:
            markers.append({
                "date": d_date, "price": d_high * 1.015, "type": "SELL",
                "text": "SELL" if not m_cross_down else "MACD SELL", "color": "#c62828"
            })

    return {
        "buy_signals": buy_signals,
        "sell_signals": sell_signals,
        "chart_markers": markers
    }

def analyze_stock(symbol: str) -> Optional[Dict[str, Any]]:
    """Comprehensive analysis for a single Thai stock ticker with Buy & Sell Points"""
    sym = clean_symbol(symbol)
    df = fetch_price_history(sym, period="1y")
    if df.empty or len(df) < 30:
        return None

    df_ind = add_all_indicators(df)
    last = df_ind.iloc[-1]
    info = fetch_stock_info(sym, use_cache=True)
    levels = calculate_support_resistance(df_ind, window=20)
    signal_pack = detect_buy_sell_signals(df_ind)

    close = float(last['Close'])
    open_p = float(last['Open'])
    high = float(last['High'])
    low = float(last['Low'])
    vol = float(last['Volume'])
    vol_ratio = float(last['Vol_Ratio']) if not pd.isna(last['Vol_Ratio']) else 1.0

    ema10 = float(last['EMA10']) if not pd.isna(last['EMA10']) else close
    ema20 = float(last['EMA20']) if not pd.isna(last['EMA20']) else close
    ema50 = float(last['EMA50']) if not pd.isna(last['EMA50']) else close
    ema200 = float(last['EMA200']) if not pd.isna(last['EMA200']) else close

    rsi = float(last['RSI14']) if not pd.isna(last['RSI14']) else 50.0
    macd = float(last['MACD']) if not pd.isna(last['MACD']) else 0.0
    macd_sig = float(last['MACD_Signal']) if not pd.isna(last['MACD_Signal']) else 0.0
    macd_hist = float(last['MACD_Hist']) if not pd.isna(last['MACD_Hist']) else 0.0

    bb_up = float(last['BB_Upper']) if not pd.isna(last['BB_Upper']) else close
    bb_mid = float(last['BB_Middle']) if not pd.isna(last['BB_Middle']) else close
    bb_low = float(last['BB_Lower']) if not pd.isna(last['BB_Lower']) else close
    atr = float(last['ATR14']) if not pd.isna(last['ATR14']) else (high - low)

    # 1. Scoring Logic
    bullish_points = 0
    total_points = 10
    if close > ema200: bullish_points += 2
    if ema20 > ema50: bullish_points += 2
    if macd > macd_sig and macd > 0: bullish_points += 2
    elif macd > macd_sig: bullish_points += 1
    if 45 <= rsi <= 68: bullish_points += 2
    elif rsi < 35: bullish_points += 1
    if vol_ratio >= 1.5: bullish_points += 2

    bullish_score = int(round((bullish_points / total_points) * 100))

    if bullish_score >= 80:
        action_verdict = "STRONG BUY (สัญญาณซื้อแข็งแกร่งมาก)"
        verdict_color = "#2e7d32"
    elif bullish_score >= 60:
        action_verdict = "BUY / ACCUMULATE (ทยอยสะสมตามแนวโน้ม)"
        verdict_color = "#388e3c"
    elif bullish_score >= 40:
        action_verdict = "WAIT & SEE / WATCHLIST (รอสัญญาณคอนเฟิร์ม)"
        verdict_color = "#f57c00"
    else:
        action_verdict = "AVOID / TAKE PROFIT (ระมัดระวังแรงขาย/ชะลอการลงทุน)"
        verdict_color = "#d32f2f"

    # 2. Buy & Sell Action Points by Trading Style
    # --- SWING TRADE (1-4 สัปดาห์) ---
    swing_entry_low = round(max(levels['support_1'], ema20 * 0.99), 2)
    swing_entry_high = round(close, 2)
    swing_tp1 = round(max(levels['resistance_1'], close + (1.5 * atr)), 2)
    swing_tp2 = round(max(levels['resistance_2'], close + (3.0 * atr)), 2)
    swing_sl = round(min(levels['support_1'] * 0.99, close - (1.2 * atr)), 2)
    swing_risk = max(0.01, close - swing_sl)
    swing_reward = max(0.01, swing_tp1 - close)
    swing_rr = round(swing_reward / swing_risk, 2)

    # --- DAY TRADE / SCALPING (รายวัน) ---
    day_entry = round(close, 2)
    day_tp = round(close + (1.0 * atr), 2)
    day_sl = round(close - (0.8 * atr), 2)

    # --- VALUE / DCA (ถือยาว 3-12 เดือน) ---
    value_buy_zone = f"{round(levels['support_2'], 2)} - {round(levels['support_1'], 2)}"
    value_exit_zone = f"เมื่อ P/E > 25 หรือ ราคาแตะ {round(levels['resistance_2'] * 1.1, 2)} บาท"

    return {
        "symbol": sym,
        "name": info.get("name", sym),
        "sector": info.get("sector", "Other"),
        "current_price": close,
        "open": open_p,
        "high": high,
        "low": low,
        "change_pct": round(float(last['Change_Pct']), 2),
        "volume": int(vol),
        "volume_ratio": round(vol_ratio, 2),
        # Indicators
        "rsi": round(rsi, 1),
        "macd": round(macd, 3),
        "macd_signal": round(macd_sig, 3),
        "macd_hist": round(macd_hist, 3),
        "ema10": round(ema10, 2),
        "ema20": round(ema20, 2),
        "ema50": round(ema50, 2),
        "ema200": round(ema200, 2),
        "bb_upper": round(bb_up, 2),
        "bb_middle": round(bb_mid, 2),
        "bb_lower": round(bb_low, 2),
        "atr": round(atr, 2),
        # Fundamental Ratios
        "pe": info.get("pe_ratio"),
        "pbv": info.get("pbv_ratio"),
        "dividend_yield": info.get("dividend_yield"),
        "roe": info.get("roe"),
        "market_cap": info.get("market_cap"),
        "high_52w": info.get("fifty_two_week_high"),
        "low_52w": info.get("fifty_two_week_low"),
        # Levels
        "support_levels": levels,
        # Verdict & Strategy
        "bullish_score": bullish_score,
        "verdict": action_verdict,
        "verdict_color": verdict_color,
        # Action Plans
        "trade_setup": {
            "entry_range": f"{swing_entry_low:.2f} - {swing_entry_high:.2f}",
            "target_1": swing_tp1,
            "target_2": swing_tp2,
            "stop_loss": swing_sl,
            "risk_reward_ratio": f"1 : {swing_rr:.2f}"
        },
        "style_strategies": {
            "day_trade": {
                "entry": day_entry,
                "take_profit": day_tp,
                "stop_loss": day_sl,
                "note": "เน้นปิดจบใน 1-2 วัน ป้องกันความผันผวนข้ามวัน"
            },
            "swing_trade": {
                "entry": f"{swing_entry_low:.2f} - {swing_entry_high:.2f}",
                "tp1": swing_tp1,
                "tp2": swing_tp2,
                "sl": swing_sl,
                "note": "เน้นถือ 1-4 สัปดาห์ ตามรอบคลื่นราคาและแนวรับแนวต้าน"
            },
            "value_investor": {
                "buy_zone": value_buy_zone,
                "exit_zone": value_exit_zone,
                "note": "เน้นรับเงินปันผลและสะสมในโซนราคาต่ำกว่ามูลค่า"
            }
        },
        # Signals & Risks
        "buy_signals": signal_pack['buy_signals'],
        "sell_signals": signal_pack['sell_signals'],
        "chart_markers": signal_pack['chart_markers'],
        "history_df": df_ind
    }
