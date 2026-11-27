# -*- coding: utf-8 -*-
"""
Thai Gold Price Retrieval & Analysis Module
Fetches real-time Thai Gold Traders Association prices, Gold Spot (XAU/USD), and USD/THB
With comprehensive Technical Analysis & Buy/Sell Strategy Calculation
"""

import requests
import json
import pandas as pd
import yfinance as yf
from datetime import datetime
from typing import Dict, Any, Optional
from indicators import add_all_indicators, calculate_support_resistance

def fetch_thai_gold_price() -> Dict[str, Any]:
    """
    Fetch live Thai Gold prices from Gold Traders Association API
    With fallback estimation from Gold Spot (XAU/USD) and USD/THB exchange rate
    """
    url = "https://xn--42cg1cb9cb6etbb7p.com/api/v1/latest"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    try:
        resp = requests.get(url, headers=headers, timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            assoc = data.get("association", {})
            rt = data.get("realtime", {})
            bar_965 = assoc.get("bar_965", {})
            orn_965 = assoc.get("ornament_965", {})
            gold_9999 = assoc.get("gold_9999_buy", {})
            shops = data.get("shops", [])

            return {
                "success": True,
                "source": "สมาคมค้าทองคำ (Gold Traders Association)",
                "announced_at": assoc.get("announced_at", ""),
                "round": assoc.get("round", 1),
                "change_from_prev_day": assoc.get("change_from_prev_day", 0),
                "change_from_prev_round": assoc.get("change_from_prev_round", 0),
                # Bar 96.5%
                "bar_buy": bar_965.get("buy", 0),
                "bar_sell": bar_965.get("sell", 0),
                # Ornament 96.5%
                "ornament_buy": orn_965.get("buy", 0),
                "ornament_sell": orn_965.get("sell", 0),
                # Gold 99.99%
                "gold_9999_per_baht": gold_9999.get("per_baht", 0),
                "gold_9999_per_gram": gold_9999.get("per_gram", 0),
                # Realtime Drivers
                "gold_spot_usd": rt.get("xau_usd") or assoc.get("ref_spot_usd", 0),
                "usd_thb": rt.get("usdthb") or assoc.get("ref_usdthb", 0),
                "next_round_estimate": rt.get("next_round_estimate", {}),
                "shops": shops,
                "is_fallback": False
            }
    except Exception as e:
        print(f"[Warning] Failed to fetch live GTA API: {e}. Using Yahoo Finance fallback.")

    # Fallback using Yahoo Finance calculation
    try:
        g = yf.Ticker("GC=F").history(period="5d")
        fx = yf.Ticker("THB=X").history(period="5d")
        spot = float(g['Close'].iloc[-1]) if not g.empty else 2600.0
        thb = float(fx['Close'].iloc[-1]) if not fx.empty else 34.0

        est_price = (spot / 31.1035) * 15.244 * 0.965 * thb
        bar_buy = int(round((est_price - 100) / 50) * 50)
        bar_sell = int(round((est_price) / 50) * 50)

        return {
            "success": True,
            "source": "คำนวณประมาณการจาก Gold Spot & USD/THB (Fallback)",
            "announced_at": datetime.now().isoformat(),
            "round": 1,
            "change_from_prev_day": 0,
            "change_from_prev_round": 0,
            "bar_buy": bar_buy,
            "bar_sell": bar_sell,
            "ornament_buy": int(bar_buy * 0.98),
            "ornament_sell": bar_sell + 800,
            "gold_9999_per_baht": int(est_price / 0.965),
            "gold_9999_per_gram": round((est_price / 0.965) / 15.244, 2),
            "gold_spot_usd": round(spot, 2),
            "usd_thb": round(thb, 2),
            "next_round_estimate": {},
            "shops": [],
            "is_fallback": True
        }
    except Exception as ex:
        print(f"[Error] Fallback failed: {ex}")
        return {"success": False, "error": str(ex)}

def fetch_gold_history(period: str = "1y") -> pd.DataFrame:
    """Fetch historical Gold Futures price data with technical indicators"""
    try:
        ticker = yf.Ticker("GC=F")
        df = ticker.history(period=period, interval="1d")
        if df.empty:
            return pd.DataFrame()
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        df_ind = add_all_indicators(df)
        return df_ind
    except Exception as e:
        print(f"[Error] Fetching gold history: {e}")
        return pd.DataFrame()

def convert_spot_to_thai_baht(spot_usd: float, usd_thb: float) -> int:
    """Convert Gold Spot price (USD/oz) to Thai Gold Bar 96.5% price per baht-weight"""
    # Formula: Spot * (15.244 / 31.1035) * 0.965 * USD_THB
    raw_thb = (spot_usd / 31.1035) * 15.244 * 0.965 * usd_thb
    # Round to nearest 50 baht (Standard Association step)
    return int(round(raw_thb / 50.0) * 50)

def analyze_gold() -> Dict[str, Any]:
    """
    Comprehensive Technical and Strategic Buy & Sell Points Analysis for Thai Gold
    """
    live_info = fetch_thai_gold_price()
    df_gold = fetch_gold_history(period="1y")

    if df_gold.empty or not live_info.get("success"):
        return {"success": False, "error": "Cannot load gold data"}

    last = df_gold.iloc[-1]
    prev = df_gold.iloc[-2]
    levels = calculate_support_resistance(df_gold, window=20)

    spot_close = float(last['Close'])
    usd_thb = float(live_info.get('usd_thb', 34.0))
    bar_sell = int(live_info.get('bar_sell', 0))
    bar_buy = int(live_info.get('bar_buy', 0))

    ema20 = float(last['EMA20'])
    ema50 = float(last['EMA50'])
    ema200 = float(last['EMA200'])
    rsi = float(last['RSI14'])
    macd = float(last['MACD'])
    macd_sig = float(last['MACD_Signal'])
    atr = float(last['ATR14'])

    # Convert Spot Technical Levels to Thai Baht (บาทละ)
    s1_thb = convert_spot_to_thai_baht(levels['support_1'], usd_thb)
    s2_thb = convert_spot_to_thai_baht(levels['support_2'], usd_thb)
    r1_thb = convert_spot_to_thai_baht(levels['resistance_1'], usd_thb)
    r2_thb = convert_spot_to_thai_baht(levels['resistance_2'], usd_thb)
    pivot_thb = convert_spot_to_thai_baht(levels['pivot'], usd_thb)

    # Bullish Scoring
    gold_score = 50
    buy_signals = []
    sell_signals = []

    if spot_close > ema200:
        gold_score += 15
        buy_signals.append("ราคาทองโลกยืนเหนือ EMA 200 วัน (ภาพใหญ่ยังคงเป็นแนวโน้มขาขึ้น)")
    else:
        sell_signals.append("ราคาทองโลกหลุดต่ำกว่า EMA 200 วัน (ภาพใหญ่เริ่มเป็นขาลง/พักฐานลึก)")

    if ema20 > ema50:
        gold_score += 15
        buy_signals.append("เส้น EMA 20 อยู่เหนือ EMA 50 (โมเมนตัมระยะสั้น-กลางเป็นบวก)")
    else:
        sell_signals.append("เส้น EMA 20 ต่ำกว่า EMA 50 (ระยะสั้นยังอยู่ในช่วงพักตัว)")

    if macd > macd_sig:
        gold_score += 10
        buy_signals.append("MACD ตัดเหนือ Signal Line (มีแรงส่งฝั่งซื้อหนุนตลาด)")
    else:
        sell_signals.append("MACD ตัดลงต่ำกว่า Signal Line (มีแรงเทขายกดดัน)")

    if 45 <= rsi <= 68:
        gold_score += 10
        buy_signals.append(f"RSI อยู่ที่ {rsi:.1f} (กำลังวิ่งในโซนกระทิง ยังไม่ Overbought)")
    elif rsi > 70:
        sell_signals.append(f"RSI พุ่งแตะ {rsi:.1f} (เข้าเขต Overbought สูง เสี่ยงโดนเทขายทำกำไรระยะสั้น)")
    elif rsi < 35:
        buy_signals.append(f"RSI อยู่ที่ {rsi:.1f} (เขต Oversold มีโอกาสดีดตัวกลับแรง)")
        gold_score += 10

    gold_score = min(100, max(0, gold_score))

    if gold_score >= 75:
        gold_verdict = "BUY ON DIP (ย่อซื้อตามแนวโน้มขาขึ้น)"
        verdict_color = "#2e7d32"
    elif gold_score >= 50:
        gold_verdict = "HOLD & ACCUMULATE (ถือรันเทรนด์ / ทยอยสะสม)"
        verdict_color = "#f57c00"
    else:
        gold_verdict = "TAKE PROFIT / WAIT & SEE (ระวังแรงเทขาย / รอตั้งรับฐานใหม่)"
        verdict_color = "#d32f2f"

    # --- STRATEGIC BUY & SELL SETUPS (จุดซื้อ-จุดขายทองคำ) ---
    # 1. Swing Trade (เก็งกำไรตามรอบ 1-4 สัปดาห์)
    swing_buy_low = min(bar_buy, s1_thb)
    swing_buy_high = bar_buy
    swing_tp1 = max(bar_sell + 200, r1_thb)
    swing_tp2 = max(swing_tp1 + 300, r2_thb)
    swing_sl = min(bar_buy - 400, s2_thb)

    # 2. Day Trade / Scalping
    day_buy = bar_buy
    day_tp = bar_sell + 150
    day_sl = bar_buy - 150

    # 3. Long-term DCA (สะสมรายเดือน/ออมทอง)
    dca_zone = f"{s2_thb:,} - {s1_thb:,} บาท"
    dca_exit = f"เมื่อ Gold Spot แตะแนวต้านใหญ่ ${levels['resistance_2']:.0f} (ประมาณ {r2_thb:,} บาท) หรือเมื่อ RSI > 75"

    return {
        "success": True,
        "live_info": live_info,
        "history_df": df_gold,
        "spot_price": spot_close,
        "usd_thb": usd_thb,
        "rsi": round(rsi, 1),
        "macd": round(macd, 2),
        "macd_signal": round(macd_sig, 2),
        "ema20": round(ema20, 2),
        "ema50": round(ema50, 2),
        "ema200": round(ema200, 2),
        "atr": round(atr, 2),
        "score": gold_score,
        "verdict": gold_verdict,
        "verdict_color": verdict_color,
        "spot_levels": levels,
        "thai_levels": {
            "pivot": pivot_thb,
            "support_1": s1_thb,
            "support_2": s2_thb,
            "resistance_1": r1_thb,
            "resistance_2": r2_thb
        },
        "trade_setups": {
            "swing_trade": {
                "buy_zone": f"{swing_buy_low:,} - {swing_buy_high:,} บาท",
                "tp1": swing_tp1,
                "tp2": swing_tp2,
                "sl": swing_sl,
                "note": "รอจังหวะ Gold Spot ย่อตัวทดสอบแนวรับ แล้วเปิดสถานะซื้อเพื่อขายที่แนวต้าน"
            },
            "day_trade": {
                "buy": day_buy,
                "tp": day_tp,
                "sl": day_sl,
                "note": "เล่นรอบเร็วตามประกาศรอบสมาคมฯ ระหว่างวัน"
            },
            "dca": {
                "buy_zone": dca_zone,
                "exit": dca_exit,
                "note": "เน้นซื้อสะสมเป็นทองคำแท่ง ถือป้องกันเงินเฟ้อระยะยาว 6-24 เดือน"
            }
        },
        "buy_signals": buy_signals,
        "sell_signals": sell_signals
    }
