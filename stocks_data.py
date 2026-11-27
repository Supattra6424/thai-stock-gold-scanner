# -*- coding: utf-8 -*-
"""
Thai Stock Market Tickers Universe and Data Retrieval Module
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd
import yfinance as yf

# SET50 Constituents (Stock Exchange of Thailand)
SET50_SYMBOLS = [
    "ADVANC", "AOT", "AWC", "BANPU", "BBL", "BCP", "BDMS", "BEM", "BGRIM", "BH",
    "BJC", "BTS", "CBG", "CENTEL", "CPALL", "CPF", "CPN", "CRC", "DELTA", "EA",
    "EGCO", "GLOBAL", "GPSC", "GULF", "HMPRO", "INTUCH", "ITC", "IVL", "KBANK", "KTB",
    "KTC", "LH", "MINT", "MTC", "OR", "OSP", "PTT", "PTTEP", "PTTGC", "RATCH",
    "SCB", "SCC", "SCGP", "SJWD", "TIDLOR", "TISCO", "TLI", "TOP", "TRUE", "TTB", "WHA"
]

# Additional SET100 constituents
SET100_ADDITIONAL = [
    "AMATA", "AP", "BAM", "BA", "BCH", "BCPG", "BTG", "CHG", "CK", "CKP",
    "COM7", "DOHOME", "ERW", "FORTH", "GFPT", "HANA", "ICHI", "IRPC", "JAS", "JMART",
    "JMT", "KAMART", "KCE", "KKP", "MEGA", "MOSHI", "PLANB", "PRM", "PSL", "PTG",
    "QH", "RCL", "SAPPE", "SAWAD", "SC", "SIRI", "SPALI", "SPRC", "STA", "STEC",
    "TASCO", "TCAP", "THANI", "THG", "TKN", "TOA", "TU", "VGI", "WHAUP", "XO"
]

SET100_SYMBOLS = sorted(list(set(SET50_SYMBOLS + SET100_ADDITIONAL)))

# Sector mapping for Thai stocks
SECTOR_MAPPING = {
    "PTT": "Energy and Utilities",
    "PTTEP": "Energy and Utilities",
    "TOP": "Energy and Utilities",
    "BCP": "Energy and Utilities",
    "BANPU": "Energy and Utilities",
    "GULF": "Energy and Utilities",
    "GPSC": "Energy and Utilities",
    "BGRIM": "Energy and Utilities",
    "EGCO": "Energy and Utilities",
    "RATCH": "Energy and Utilities",
    "EA": "Energy and Utilities",
    "IRPC": "Energy and Utilities",
    "KBANK": "Banking",
    "SCB": "Banking",
    "BBL": "Banking",
    "KTB": "Banking",
    "TTB": "Banking",
    "TISCO": "Banking",
    "KKP": "Banking",
    "KTC": "Finance and Securities",
    "MTC": "Finance and Securities",
    "SAWAD": "Finance and Securities",
    "TIDLOR": "Finance and Securities",
    "JMT": "Finance and Securities",
    "BAM": "Finance and Securities",
    "CPALL": "Commerce",
    "CRC": "Commerce",
    "HMPRO": "Commerce",
    "BJC": "Commerce",
    "GLOBAL": "Commerce",
    "DOHOME": "Commerce",
    "COM7": "Commerce",
    "ADVANC": "Information and Communication",
    "TRUE": "Information and Communication",
    "INTUCH": "Information and Communication",
    "JAS": "Information and Communication",
    "AOT": "Transportation and Logistics",
    "BEM": "Transportation and Logistics",
    "BTS": "Transportation and Logistics",
    "PRM": "Transportation and Logistics",
    "PSL": "Transportation and Logistics",
    "RCL": "Transportation and Logistics",
    "BDMS": "Health Care Services",
    "BH": "Health Care Services",
    "BCH": "Health Care Services",
    "CHG": "Health Care Services",
    "THG": "Health Care Services",
    "DELTA": "Electronic Components",
    "HANA": "Electronic Components",
    "KCE": "Electronic Components",
    "SCC": "Construction Materials",
    "SCGP": "Packaging",
    "CPN": "Property Development",
    "AWC": "Property Development",
    "LH": "Property Development",
    "SPALI": "Property Development",
    "AP": "Property Development",
    "SIRI": "Property Development",
    "QH": "Property Development",
    "MINT": "Tourism and Leisure",
    "CENTEL": "Tourism and Leisure",
    "ERW": "Tourism and Leisure",
    "CPF": "Food and Beverage",
    "CBG": "Food and Beverage",
    "OSP": "Food and Beverage",
    "TU": "Food and Beverage",
    "ITC": "Food and Beverage",
    "ICHI": "Food and Beverage",
    "SAPPE": "Food and Beverage",
    "TKN": "Food and Beverage",
    "BTG": "Food and Beverage",
    "WHA": "Industrial Estate",
    "AMATA": "Industrial Estate"
}

def to_yahoo_symbol(symbol: str) -> str:
    sym = symbol.strip().upper()
    if not sym.endswith(".BK"):
        return f"{sym}.BK"
    return sym

def clean_symbol(yahoo_symbol: str) -> str:
    return yahoo_symbol.replace(".BK", "").strip().upper()

class StockDataCache:
    def __init__(self, db_path: str = "stock_cache.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS info_cache (
                    symbol TEXT PRIMARY KEY,
                    updated_at TEXT,
                    data_json TEXT
                )
            """)
            conn.commit()

    def get_info(self, symbol: str, max_age_hours: int = 12) -> Optional[Dict[str, Any]]:
        clean = clean_symbol(symbol)
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute("SELECT updated_at, data_json FROM info_cache WHERE symbol = ?", (clean,))
                row = cur.fetchone()
                if row:
                    updated_at = datetime.fromisoformat(row[0])
                    if datetime.now() - updated_at < timedelta(hours=max_age_hours):
                        return json.loads(row[1])
        except Exception:
            pass
        return None

    def save_info(self, symbol: str, data: Dict[str, Any]):
        clean = clean_symbol(symbol)
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO info_cache (symbol, updated_at, data_json) VALUES (?, ?, ?)",
                    (clean, datetime.now().isoformat(), json.dumps(data, ensure_ascii=False))
                )
                conn.commit()
        except Exception:
            pass

_cache = StockDataCache()

def fetch_price_history(symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    yf_sym = to_yahoo_symbol(symbol)
    try:
        ticker = yf.Ticker(yf_sym)
        df = ticker.history(period=period, interval=interval)
        if df.empty:
            return pd.DataFrame()
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        df.dropna(subset=["Close"], inplace=True)
        return df
    except Exception as e:
        print(f"[Error] Fetching history for {symbol}: {e}")
        return pd.DataFrame()

def fetch_stock_info(symbol: str, use_cache: bool = True) -> Dict[str, Any]:
    clean = clean_symbol(symbol)
    if use_cache:
        cached = _cache.get_info(clean)
        if cached:
            return cached

    yf_sym = to_yahoo_symbol(symbol)
    raw_info = {}
    try:
        ticker = yf.Ticker(yf_sym)
        raw_info = ticker.info or {}
    except Exception as e:
        print(f"[Error] Fetching info for {symbol}: {e}")

    div_rate = raw_info.get("dividendYield")
    div_yield = round(div_rate, 2) if (div_rate is not None and div_rate > 0) else None

    roe_val = raw_info.get("returnOnEquity")
    roe = round(roe_val * 100, 2) if roe_val is not None else None

    info = {
        "symbol": clean,
        "name": raw_info.get("longName") or raw_info.get("shortName") or clean,
        "sector": SECTOR_MAPPING.get(clean) or raw_info.get("sector", "Other"),
        "industry": raw_info.get("industry", "N/A"),
        "current_price": raw_info.get("currentPrice") or raw_info.get("regularMarketPrice"),
        "previous_close": raw_info.get("previousClose") or raw_info.get("regularMarketPreviousClose"),
        "market_cap": raw_info.get("marketCap"),
        "pe_ratio": round(raw_info.get("trailingPE"), 2) if raw_info.get("trailingPE") else None,
        "pbv_ratio": round(raw_info.get("priceToBook"), 2) if raw_info.get("priceToBook") else None,
        "dividend_yield": div_yield,
        "roe": roe,
        "fifty_two_week_high": raw_info.get("fiftyTwoWeekHigh"),
        "fifty_two_week_low": raw_info.get("fiftyTwoWeekLow"),
        "currency": raw_info.get("currency", "THB")
    }

    _cache.save_info(clean, info)
    return info
