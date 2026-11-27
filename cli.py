# -*- coding: utf-8 -*-
"""
Thai Stock & Gold Scanner & Analyzer - Command Line Interface (CLI)
Usage:
    python cli.py --scan golden_cross --universe set50
    python cli.py --analyze PTT
    python cli.py --gold
    python cli.py --scan high_dividend_value --export dividend_stocks.csv
"""

import argparse
import sys
import pandas as pd
from stocks_data import SET50_SYMBOLS, SET100_SYMBOLS, clean_symbol
from scanner import SCAN_STRATEGIES, run_scanner
from analyzer import analyze_stock
from gold_data import fetch_thai_gold_price, fetch_gold_history, analyze_gold

def print_banner():
    banner = """
===============================================================
    🇹🇭 Thai Stock & Gold Scanner & Deep Analyzer
    ระบบสแกนและวิเคราะห์หุ้นไทย + วิเคราะห์จุดซื้อ-จุดขายทองคำไทย
===============================================================
"""
    print(banner)

def handle_gold():
    print("[*] กำลังวิเคราะห์สัญญาณเทคนิคอลและจุดซื้อ-จุดขายทองคำไทย...")
    res = analyze_gold()
    if not res or not res.get("success"):
        print("[!] ไม่สามารถดึงข้อมูลราคาทองคำได้ในขณะนี้")
        return

    gold = res['live_info']
    chg_day = gold.get('change_from_prev_day', 0)
    chg_round = gold.get('change_from_prev_round', 0)
    sign_day = "+" if chg_day > 0 else ""
    sign_round = "+" if chg_round > 0 else ""

    print("\n" + "=" * 68)
    print(f"🪙  รายงานราคาทองคำไทย (สมาคมค้าทองคำ - Gold Traders Association)")
    print(f"    ประกาศครั้งที่: {gold.get('round', 1)} | เวลา: {gold.get('announced_at', 'ล่าสุด')}")
    print(f"    การเปลี่ยนแปลงเทียบเมื่อวาน : {sign_day}{chg_day:,} บาท | เทียบรอบก่อน: {sign_round}{chg_round:,} บาท")
    print("=" * 68)

    print("\n📦 1. ราคาทองคำแท่งและทองรูปพรรณ 96.5%:")
    print(f"   - ทองคำแท่ง 96.5%   : รับซื้อ {gold.get('bar_buy', 0):,} บาท | ขายออก {gold.get('bar_sell', 0):,} บาท")
    print(f"   - ทองรูปพรรณ 96.5% : รับซื้อ {gold.get('ornament_buy', 0):,.2f} บาท | ขายออก {gold.get('ornament_sell', 0):,} บาท")
    print(f"   - ทองคำบริสุทธิ์ 99.99%: บาทละ {gold.get('gold_9999_per_baht', 0):,.2f} บาท | กรัมละ {gold.get('gold_9999_per_gram', 0):,.2f} บาท")

    print("\n🌐 2. ตัวชี้วัดตลาดโลก (Global Market Drivers):")
    print(f"   - Gold Spot (XAU/USD)      : ${res['spot_price']:,.2f} / oz")
    print(f"   - อัตราแลกเปลี่ยน (USD/THB)  : {res['usd_thb']:.2f} บาท/ดอลลาร์")
    print(f"   - RSI (14 วัน) : {res['rsi']} | MACD: {res['macd']:.2f} | Signal: {res['macd_signal']:.2f}")
    print(f"   - เส้นค่าเฉลี่ย: EMA20: ${res['ema20']:.2f} | EMA50: ${res['ema50']:.2f} | EMA200: ${res['ema200']:.2f}")

    print(f"\n⭐ คะแนนสัญญาณทองคำ (Bullish Score): {res['score']} / 100")
    print(f"🎯 คำแนะนำของระบบ: {res['verdict']}")

    # Gold Buy / Sell Strategy Section
    setups = res['trade_setups']
    print("\n" + "=" * 68)
    print("📋 วิเคราะห์จุดซื้อ - จุดขายทองคำแท่ง (Gold Buy/Sell Strategies):")
    print("=" * 68)

    sw = setups['swing_trade']
    print("\n🏄 1. สายเก็งกำไรตามรอบ (Swing Trade 1-4 สัปดาห์ - แนะนำ):")
    print(f"   - โซนรับ / ราคาเข้าซื้อ (Buy Zone)     : {sw['buy_zone']}")
    print(f"   - เป้าหมายทำกำไร 1 (Take Profit 1)  : {sw['tp1']:,} บาท")
    print(f"   - เป้าหมายทำกำไร 2 (Take Profit 2)  : {sw['tp2']:,} บาท")
    print(f"   - จุดตัดขาดทุน (Stop Loss)          : {sw['sl']:,} บาท")
    print(f"   - แผนการเทรด: {sw['note']}")

    dt = setups['day_trade']
    print("\n⚡ 2. สายเล่นสั้นในวัน (Day Trade):")
    print(f"   - จุดซื้อเข้าตลาด (Entry)          : {dt['buy']:,} บาท")
    print(f"   - ขายทำกำไรเร็ว (Quick TP)          : {dt['tp']:,} บาท")
    print(f"   - จุดคัทลอสแคบ (Stop Loss)          : {dt['sl']:,} บาท")

    dca = setups['dca']
    print("\n🏦 3. สายออมทอง / สะสมระยะยาว (Long-Term DCA):")
    print(f"   - โซนทยอยสะสม (Buy Accumulate)     : {dca['buy_zone']}")
    print(f"   - เงื่อนไขแบ่งขายทำกำไร              : {dca['exit']}")

    # Technical Levels in Thai Baht
    th_lvl = res['thai_levels']
    print("\n📐 4. ระดับแนวรับ-แนวต้านของทองคำแท่งในไทย:")
    print(f"   - แนวต้าน 2 (R2) : {th_lvl['resistance_2']:,} บาท (${res['spot_levels']['resistance_2']:.1f})")
    print(f"   - แนวต้าน 1 (R1) : {th_lvl['resistance_1']:,} บาท (${res['spot_levels']['resistance_1']:.1f})")
    print(f"   - Pivot Point    : {th_lvl['pivot']:,} บาท (${res['spot_levels']['pivot']:.1f})")
    print(f"   - แนวรับ 1 (S1)  : {th_lvl['support_1']:,} บาท (${res['spot_levels']['support_1']:.1f})")
    print(f"   - แนวรับ 2 (S2)  : {th_lvl['support_2']:,} บาท (${res['spot_levels']['support_2']:.1f})")

    print("\n🟢 สัญญาณซื้อทองคำที่ตรวจพบ:")
    for b in res['buy_signals']:
        print(f"  [+] {b}")

    if res['sell_signals']:
        print("\n🔴 สัญญาณเตือนขาย / ปัจจัยเสี่ยงที่ต้องระวัง:")
        for s in res['sell_signals']:
            print(f"  [-] {s}")
    print("=" * 68 + "\n")

def handle_analyze(symbol: str):
    sym = clean_symbol(symbol)
    print(f"[*] กำลังวิเคราะห์หุ้น: {sym}...")
    res = analyze_stock(sym)
    if not res:
        print(f"[!] ไม่พบข้อมูลสำหรับหุ้น {sym}")
        return

    print("=" * 65)
    print(f"🏢 ข้อมูลหุ้น: {res['symbol']} - {res['name']}")
    print(f"หมวดหมู่: {res['sector']} | ราคาล่าสุด: {res['current_price']:.2f} THB ({res['change_pct']:+.2f}%)")
    print("=" * 65)
    
    print("\n📊 ข้อมูลทางเทคนิคอลและสัญญาณอินดิเคเตอร์:")
    print(f"  - RSI (14): {res['rsi']} | Volume Ratio: {res['volume_ratio']}x")
    print(f"  - EMA20: {res['ema20']:.2f} | EMA50: {res['ema50']:.2f} | EMA200: {res['ema200']:.2f}")
    print(f"  - MACD: {res['macd']:.3f} | Signal: {res['macd_signal']:.3f} | Hist: {res['macd_hist']:.3f}")
    print(f"  - Bollinger Bands: Upper {res['bb_upper']:.2f} | Middle {res['bb_middle']:.2f} | Lower {res['bb_lower']:.2f}")

    print("\n💰 ข้อมูลปัจจัยพื้นฐาน:")
    print(f"  - P/E: {res['pe']} | P/BV: {res['pbv']} | Dividend Yield: {res['dividend_yield']}% | ROE: {res['roe']}%")

    print(f"\n⭐ ผลการประเมินคะแนน (Bullish Strength Score): {res['bullish_score']} / 100")
    print(f"🎯 คำแนะนำของระบบ: {res['verdict']}")

    styles = res['style_strategies']
    print("\n" + "=" * 65)
    print("📋 วิเคราะห์จุดซื้อ - จุดขาย แบ่งตามสไตล์การเทรด:")
    print("=" * 65)

    sw = styles['swing_trade']
    print("\n🏄 1. สายเก็งกำไรตามรอบ (Swing Trade 1-4 สัปดาห์ - แนะนำ):")
    print(f"   - โซนรับ / ราคาเข้าซื้อ (Buy Zone)     : {sw['entry']} บาท")
    print(f"   - เป้าหมายทำกำไร 1 (Take Profit 1)  : {sw['tp1']:.2f} บาท")
    print(f"   - เป้าหมายทำกำไร 2 (Take Profit 2)  : {sw['tp2']:.2f} บาท")
    print(f"   - จุดตัดขาดทุน (Stop Loss)          : {sw['sl']:.2f} บาท")
    print(f"   - อัตราผลตอบแทนต่อความเสี่ยง (R:R) : {res['trade_setup']['risk_reward_ratio']}")
    print(f"   - หมายเหตุ: {sw['note']}")

    dt = styles['day_trade']
    print("\n⚡ 2. สายเล่นสั้นรายวัน (Day Trade / Scalping):")
    print(f"   - จุดซื้อเข้าตลาด (Entry)          : {dt['entry']:.2f} บาท")
    print(f"   - จุดขายทำกำไรเร็ว (Quick TP)       : {dt['take_profit']:.2f} บาท")
    print(f"   - จุดคัทลอสแคบ (Tight Stop Loss)    : {dt['stop_loss']:.2f} บาท")

    vi = styles['value_investor']
    print("\n🏦 3. สายลงทุนระยะยาว (Value / DCA):")
    print(f"   - โซนทยอยสะสม (Buy / Accumulate)   : {vi['buy_zone']} บาท")
    print(f"   - โซนพิจารณาขายทำกำไร               : {vi['exit_zone']}")

    print("\n🟢 สัญญาณซื้อที่ตรวจพบ (Buy Checkpoints):")
    if res['buy_signals']:
        for s in res['buy_signals']:
            print(f"  [+] {s}")
    else:
        print("  [-] ยังไม่มีสัญญาณซื้อเด่นชัดในแท่งเทียนปัจจุบัน")

    print("\n🔴 สัญญาณเตือนขาย / จุดที่ต้องระมัดระวัง (Sell / Caution):")
    if res['sell_signals']:
        for r in res['sell_signals']:
            print(f"  [-] {r}")
    else:
        print("  [+] ยังไม่มีสัญญาณขายรุนแรง")
    print("=" * 65 + "\n")

def handle_scan(strategy: str, universe: str, min_score: float, custom_symbols_str: str, export_path: str):
    if custom_symbols_str:
        symbols = [s.strip().upper() for s in custom_symbols_str.split(",") if s.strip()]
    elif universe.lower() == "set100":
        symbols = SET100_SYMBOLS
    else:
        symbols = SET50_SYMBOLS

    strat_desc = SCAN_STRATEGIES.get(strategy, strategy)
    print(f"[*] เริ่มการสแกนหุ้น {len(symbols)} ตัว...")
    print(f"[*] กลยุทธ์: {strat_desc}")
    print(f"[*] เกณฑ์คะแนนขั้นต่ำ: {min_score}")

    df = run_scanner(symbols=symbols, strategy=strategy)
    if df.empty:
        print("[!] ไม่พบหุ้นที่ตรงตามเงื่อนไข")
        return

    filtered = df[df['score'] >= min_score].copy()
    print(f"\n[+] สแกนเสร็จสิ้น! พบหุ้นที่ผ่านเกณฑ์ {len(filtered)} ตัว (จากที่ตรวจพบ {len(df)} ตัว):\n")

    cols = ["symbol", "price", "change_pct", "volume_ratio", "rsi", "pe", "div_yield", "score", "signals"]
    cols_exist = [c for c in cols if c in filtered.columns]
    
    disp = filtered[cols_exist].copy()
    disp['signals'] = disp['signals'].apply(lambda x: ", ".join(x) if isinstance(x, list) else str(x))
    print(disp.to_string(index=False))

    if export_path:
        filtered.to_csv(export_path, index=False, encoding="utf-8-sig")
        print(f"\n[+] บันทึกผลการสแกนลงไฟล์สำเร็จ: {export_path}")

def main():
    print_banner()
    parser = argparse.ArgumentParser(description="Thai Stock & Gold Scanner and Analyzer CLI")
    parser.add_argument("--scan", type=str, choices=list(SCAN_STRATEGIES.keys()), help="กลยุทธ์การสแกนหุ้น")
    parser.add_argument("--universe", type=str, default="set50", choices=["set50", "set100", "custom"], help="กลุ่มหุ้นเป้าหมาย (default: set50)")
    parser.add_argument("--symbols", type=str, default="", help="รายชื่อหุ้นกรณีเลือก custom (คั่นด้วยจุลภาค เช่น PTT,CPALL,BDMS)")
    parser.add_argument("--analyze", type=str, default="", help="วิเคราะห์หุ้นรายตัวเชิงลึกและจุดซื้อ-จุดขาย (เช่น --analyze PTT)")
    parser.add_argument("--gold", action="store_true", help="วิเคราะห์ราคาทองคำแท่งและจุดซื้อ-จุดขายทองคำ")
    parser.add_argument("--min-score", type=float, default=50.0, help="คะแนนขั้นต่ำ (default: 50)")
    parser.add_argument("--export", type=str, default="", help="พาธไฟล์สำหรับบันทึกผลเป็น CSV")

    args = parser.parse_args()

    if args.gold:
        handle_gold()
    elif args.analyze:
        handle_analyze(args.analyze)
    elif args.scan:
        handle_scan(args.scan, args.universe, args.min_score, args.symbols, args.export)
    else:
        print("[i] ใช้งานด่วน:")
        print("    1. วิเคราะห์จุดซื้อ-จุดขายทองคำ : python cli.py --gold")
        print("    2. วิเคราะห์จุดซื้อ-จุดขายหุ้น  : python cli.py --analyze PTT")
        print("    3. สแกนหุ้นภาพรวม SET50        : python cli.py --scan all")

if __name__ == "__main__":
    main()
