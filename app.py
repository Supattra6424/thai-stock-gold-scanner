# -*- coding: utf-8 -*-
"""
Thai Stock Market & Gold Scanner & Deep Dive Analyzer - Streamlit Web Dashboard
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import importlib
import stocks_data
import indicators
import scanner
import analyzer
import gold_data

importlib.reload(stocks_data)
importlib.reload(indicators)
importlib.reload(scanner)
importlib.reload(analyzer)
importlib.reload(gold_data)

from stocks_data import SET50_SYMBOLS, SET100_SYMBOLS, fetch_price_history, fetch_stock_info, clean_symbol
from indicators import add_all_indicators
from scanner import SCAN_STRATEGIES, run_scanner
from analyzer import analyze_stock
from gold_data import fetch_thai_gold_price, fetch_gold_history, analyze_gold

# Page Configuration
st.set_page_config(
    page_title="Thai Stock & Gold Scanner | สแกนหุ้นและราคาทองคำไทย",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.1rem;
        font-weight: 700;
        color: #1E88E5;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #616161;
        margin-bottom: 1.2rem;
    }
    .gold-ticker-bar {
        background: linear-gradient(90deg, #fff8e1 0%, #fffde7 100%);
        border: 1px solid #ffe082;
        border-radius: 8px;
        padding: 10px 16px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .buy-box {
        background-color: #f1f8e9;
        border-left: 4px solid #4caf50;
        padding: 12px 16px;
        border-radius: 6px;
        margin-bottom: 10px;
    }
    .sell-box {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        padding: 12px 16px;
        border-radius: 6px;
        margin-bottom: 10px;
    }
    .gold-box {
        background-color: #fffdf5;
        border-left: 4px solid #fbc02d;
        padding: 12px 16px;
        border-radius: 6px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Fetch quick gold price for top banner
gold_quick = fetch_thai_gold_price()
if gold_quick and gold_quick.get("success"):
    chg = gold_quick.get("change_from_prev_day", 0)
    chg_str = f"+{chg:,}" if chg > 0 else f"{chg:,}"
    st.markdown(f"""
    <div class="gold-ticker-bar">
        <div>
            <b>🪙 ราคาทองคำแท่ง 96.5% ล่าสุด:</b> รับซื้อ <b>{gold_quick.get('bar_buy', 0):,}</b> บาท | ขายออก <b>{gold_quick.get('bar_sell', 0):,}</b> บาท 
            <span style="color:{'#2e7d32' if chg >= 0 else '#c62828'}; font-weight:bold;">({chg_str} บาท)</span>
        </div>
        <div>
            🌍 <b>Gold Spot:</b> ${gold_quick.get('gold_spot_usd', 0):,.2f} | 💵 <b>USD/THB:</b> {gold_quick.get('usd_thb', 0):.2f} ฿
        </div>
    </div>
    """, unsafe_allow_html=True)

# Sidebar Menu
st.sidebar.image("https://img.icons8.com/color/96/bullish.png", width=64)
st.sidebar.title("เมนูการทำงาน")
app_mode = st.sidebar.radio(
    "เลือกฟังก์ชัน:",
    [
        "🎯 สแกนหาหุ้นเด่น (Stock Scanner)",
        "🔬 วิเคราะห์เจาะลึกรายตัว (Stock Analyzer)",
        "🪙 ราคาทองคำไทย & วิเคราะห์จุดซื้อ-ขายทอง (Thai Gold)",
        "ℹ️ วิธีใช้งานและกลยุทธ์ (Guide)"
    ]
)

# -------------------------------------------------------------
# TAB 1: STOCK SCANNER
# -------------------------------------------------------------
if app_mode == "🎯 สแกนหาหุ้นเด่น (Stock Scanner)":
    st.markdown('<div class="main-header">🎯 เครื่องมือสแกนหาหุ้นไทย (Thai Stock Scanner)</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">คัดกรองหุ้นตามสัญญาณเทคนิคอลและปัจจัยพื้นฐานแบบเรียลไทม์</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2, 2, 1.5])
    with col1:
        strategy_choice = st.selectbox(
            "📌 เลือกกลยุทธ์การสแกน (Strategy):",
            options=list(SCAN_STRATEGIES.keys()),
            format_func=lambda x: SCAN_STRATEGIES[x],
            index=0
        )
    with col2:
        universe_choice = st.selectbox(
            "🌐 กลุ่มหุ้นที่ต้องการสแกน (Universe):",
            ["SET50 (หุ้นใหญ่ 50 ตัวแรก)", "SET100 (หุ้น 100 ตัวแรก)", "Custom (ระบุเอง)"],
            index=0
        )
    with col3:
        min_score = st.slider("⭐ คะแนนสัญญาณขั้นต่ำ (Bullish Score):", min_value=0, max_value=100, value=50, step=5)

    custom_symbols = []
    if "Custom" in universe_choice:
        custom_input = st.text_input("ใส่ชื่อย่อหุ้น คั่นด้วยเครื่องหมายจุลภาค (,):", value="PTT, CPALL, BDMS, DELTA, GULF, ADVANC, KBANK")
        custom_symbols = [s.strip().upper() for s in custom_input.split(",") if s.strip()]

    start_scan = st.button("🚀 เริ่มการสแกนหุ้น (Start Scan)", type="primary", use_container_width=True)

    if start_scan or "scan_results" in st.session_state:
        if start_scan:
            if "SET50" in universe_choice:
                target_symbols = SET50_SYMBOLS
            elif "SET100" in universe_choice:
                target_symbols = SET100_SYMBOLS
            else:
                target_symbols = custom_symbols

            with st.spinner(f"กำลังดึงข้อมูลและประมวลผลสัญญาณหุ้น {len(target_symbols)} ตัว... กรุณารอสักครู่"):
                df_results = run_scanner(symbols=target_symbols, strategy=strategy_choice, max_workers=6)
                st.session_state["scan_results"] = df_results

        df_scan = st.session_state.get("scan_results", pd.DataFrame())

        if df_scan.empty:
            st.warning("⚠️ ไม่พบหุ้นที่ตรงกับเงื่อนไขในขณะนี้ ลองปรับเปลี่ยนกลยุทธ์หรือขยายกลุ่มหุ้น")
        else:
            filtered = df_scan[df_scan["score"] >= min_score].copy()
            st.success(f"✅ พบหุ้นที่เข้าเกณฑ์ทั้งหมด {len(filtered)} ตัว (จากที่ตรวจพบ {len(df_scan)} ตัว)")

            display_df = filtered.copy()
            display_df['signals'] = display_df['signals'].apply(lambda x: ", ".join(x) if isinstance(x, list) else str(x))
            
            rename_dict = {
                "symbol": "ชื่อหุ้น", "name": "ชื่อบริษัท", "sector": "กลุ่มอุตสาหกรรม",
                "price": "ราคาล่าสุด (บาท)", "change_pct": "เปลี่ยนแปลง (%)",
                "volume_ratio": "Volume Ratio", "rsi": "RSI (14)",
                "pe": "P/E", "pbv": "P/BV", "div_yield": "ปันผล (%)",
                "score": "Bullish Score", "signals": "สัญญาณเด่นที่พบ"
            }
            cols_to_show = ["symbol", "price", "change_pct", "volume_ratio", "rsi", "pe", "div_yield", "score", "signals", "sector"]
            cols_available = [c for c in cols_to_show if c in display_df.columns]
            
            st.dataframe(
                display_df[cols_available].rename(columns=rename_dict),
                use_container_width=True,
                height=450
            )

            csv_data = filtered.to_csv(index=False, encoding="utf-8-sig")
            st.download_button(
                label="📥 ดาวน์โหลดผลลัพธ์เป็นไฟล์ CSV",
                data=csv_data, file_name="thai_stock_scan_results.csv", mime="text/csv"
            )

# -------------------------------------------------------------
# TAB 2: STOCK ANALYZER (DEEP DIVE + BUY/SELL POINTS)
# -------------------------------------------------------------
elif app_mode == "🔬 วิเคราะห์เจาะลึกรายตัว (Stock Analyzer)":
    st.markdown('<div class="main-header">🔬 วิเคราะห์เจาะลึกรายตัว & จุดซื้อ-จุดขายหุ้น</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">วิเคราะห์แนวโน้ม โมเมนตัม วางแผนจุดเข้าซื้อ (Entry) และจุดทำกำไร/ตัดขาดทุน (Take Profit / Stop Loss)</div>', unsafe_allow_html=True)

    col_input, col_btn = st.columns([4, 1])
    with col_input:
        selected_ticker = st.text_input("กรอกชื่อย่อหุ้นไทยที่ต้องการวิเคราะห์ (เช่น PTT, CPALL, BDMS, DELTA, AOT):", value="PTT").strip().upper()
    with col_btn:
        st.write("")
        st.write("")
        run_analysis = st.button("🔍 วิเคราะห์หุ้น", type="primary", use_container_width=True)

    if selected_ticker:
        with st.spinner(f"กำลังรวบรวมข้อมูลและวิเคราะห์หุ้น {selected_ticker}..."):
            analysis = analyze_stock(selected_ticker)

        if not analysis:
            st.error(f"❌ ไม่สามารถดึงข้อมูลหุ้น '{selected_ticker}' ได้ กรุณาตรวจสอบชื่อหุ้นอีกครั้ง")
        else:
            st.markdown(f"### 🏢 {analysis['symbol']} - {analysis['name']}")
            st.caption(f"กลุ่มอุตสาหกรรม: **{analysis['sector']}** | สกุลเงิน: THB")

            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("ราคาปิดล่าสุด", f"{analysis['current_price']:.2f} ฿", f"{analysis['change_pct']:+.2f}%")
            c2.metric("RSI (14 วัน)", f"{analysis['rsi']:.1f}", "Oversold" if analysis['rsi'] < 35 else ("Overbought" if analysis['rsi'] > 70 else "ปกติ"))
            c3.metric("Volume Ratio", f"{analysis['volume_ratio']:.2f}x", "Volume เข้า" if analysis['volume_ratio'] >= 1.5 else "ปกติ")
            c4.metric("P/E Ratio", f"{analysis['pe']:.2f}" if analysis['pe'] else "N/A")
            c5.metric("เงินปันผลต่อปี", f"{analysis['dividend_yield']:.2f}%" if analysis['dividend_yield'] else "N/A")

            st.markdown("---")
            vcol1, vcol2 = st.columns([1, 2])
            with vcol1:
                score = analysis['bullish_score']
                st.metric("คะแนนสัญญาณ (Bullish Strength Score)", f"{score} / 100")
                st.progress(score / 100.0)
                st.markdown(f"**คำแนะนำระบบ:** <span style='font-size:1.15rem; color:{analysis['verdict_color']}; font-weight:bold;'>{analysis['verdict']}</span>", unsafe_allow_html=True)

            with vcol2:
                b_signals = analysis['buy_signals']
                s_signals = analysis['sell_signals']
                
                if b_signals:
                    st.markdown('<div class="buy-box"><b>🟢 สัญญาณซื้อที่ตรวจพบ (Buy Triggers):</b><br>' + '<br>'.join([f"• {b}" for b in b_signals]) + '</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="buy-box"><b>🟢 สัญญาณซื้อ:</b> ยังไม่มีสัญญาณเข้าซื้อชัดเจนในรอบนี้ ควรรอจังหวะย่อตัว</div>', unsafe_allow_html=True)

                if s_signals:
                    st.markdown('<div class="sell-box"><b>🔴 สัญญาณขาย/จุดระวัง (Sell / Take Profit Triggers):</b><br>' + '<br>'.join([f"• {s}" for s in s_signals]) + '</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="sell-box"><b>🔴 สัญญาณขาย:</b> ยังไม่พบสัญญาณขายรุนแรง สามารถถือรันเทรนด์ได้</div>', unsafe_allow_html=True)

            # 3-Style Action Plan
            st.markdown("---")
            st.markdown("### 📋 แผนการวิเคราะห์จุดซื้อ - จุดขายหุ้น (Trade Setups by Style)")
            styles = analysis['style_strategies']
            
            p_tab1, p_tab2, p_tab3 = st.tabs([
                "🏄 สายเก็งกำไรตามรอบ (Swing Trade)",
                "⚡ สายเล่นสั้นจบในวัน (Day Trade)",
                "🏦 สายลงทุนระยะยาว (Value / DCA)"
            ])

            with p_tab1:
                sw = styles['swing_trade']
                sc1, sc2, sc3, sc4 = st.columns(4)
                sc1.metric("🟢 โซนรับเข้าซื้อ (Buy Zone)", f"{sw['entry']} ฿")
                sc2.metric("🎯 เป้าหมายทำกำไร 1 (TP1)", f"{sw['tp1']:.2f} ฿", f"+{((sw['tp1']-analysis['current_price'])/analysis['current_price'])*100:.1f}%")
                sc3.metric("🎯 เป้าหมายทำกำไร 2 (TP2)", f"{sw['tp2']:.2f} ฿", f"+{((sw['tp2']-analysis['current_price'])/analysis['current_price'])*100:.1f}%")
                sc4.metric("🛑 จุดตัดขาดทุน (Stop Loss)", f"{sw['sl']:.2f} ฿", f"-{((analysis['current_price']-sw['sl'])/analysis['current_price'])*100:.1f}%")
                st.caption(f"💡 **กลยุทธ์:** {sw['note']} | **Risk / Reward Ratio:** {analysis['trade_setup']['risk_reward_ratio']}")

            with p_tab2:
                dt = styles['day_trade']
                dc1, dc2, dc3 = st.columns(3)
                dc1.metric("🟢 จุดซื้อเข้าตลาด (Entry)", f"{dt['entry']:.2f} ฿")
                dc2.metric("🎯 ขายทำกำไรเร็ว (Quick TP)", f"{dt['take_profit']:.2f} ฿", f"+{((dt['take_profit']-dt['entry'])/dt['entry'])*100:.1f}%")
                dc3.metric("🛑 คัทลอสแคบ (Tight Stop Loss)", f"{dt['stop_loss']:.2f} ฿", f"-{((dt['entry']-dt['stop_loss'])/dt['entry'])*100:.1f}%")
                st.caption(f"💡 **กลยุทธ์:** {dt['note']}")

            with p_tab3:
                vi = styles['value_investor']
                vc1, vc2 = st.columns(2)
                vc1.metric("🛒 โซนทยอยสะสม (Buy Accumulate)", f"{vi['buy_zone']} ฿")
                vc2.metric("💰 เงื่อนไขขายทำกำไร (Exit)", "เมื่อเต็มมูลค่าพื้นฐาน")
                st.write(f"📌 **เป้าหมายขาย:** {vi['exit_zone']}")
                st.caption(f"💡 **กลยุทธ์:** {vi['note']}")

            # Interactive Candlestick Chart with Buy/Sell Levels
            st.markdown("---")
            st.markdown("### 📊 กราฟราคาเทคนิคอล & ระดับจุดซื้อ-จุดขาย (Interactive Chart)")
            df_chart = analysis['history_df']
            setup = analysis['trade_setup']

            fig = make_subplots(
                rows=4, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.03,
                row_heights=[0.55, 0.15, 0.15, 0.15],
                subplot_titles=(f"กราฟราคา {analysis['symbol']} + โซนเข้าซื้อ-ขายทำกำไร", "Volume", "RSI (14)", "MACD (12, 26, 9)")
            )

            fig.add_trace(go.Candlestick(
                x=df_chart.index, open=df_chart['Open'], high=df_chart['High'], low=df_chart['Low'], close=df_chart['Close'], name="OHLC"
            ), row=1, col=1)

            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['EMA20'], line=dict(color='#ff9800', width=1.5), name="EMA 20"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['EMA50'], line=dict(color='#2196f3', width=1.5), name="EMA 50"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['EMA200'], line=dict(color='#9c27b0', width=2), name="EMA 200"), row=1, col=1)

            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['BB_Upper'], line=dict(color='gray', width=1, dash='dash'), name="BB Upper"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['BB_Lower'], line=dict(color='gray', width=1, dash='dash'), name="BB Lower"), row=1, col=1)

            fig.add_hline(y=setup['target_1'], line_dash="dash", line_color="#1976d2", annotation_text=f"Target 1 ({setup['target_1']:.2f})", annotation_position="top right", row=1, col=1)
            fig.add_hline(y=setup['target_2'], line_dash="dash", line_color="#7b1fa2", annotation_text=f"Target 2 ({setup['target_2']:.2f})", annotation_position="top right", row=1, col=1)
            fig.add_hline(y=setup['stop_loss'], line_dash="dash", line_color="#d32f2f", annotation_text=f"Stop Loss ({setup['stop_loss']:.2f})", annotation_position="bottom right", row=1, col=1)

            vol_colors = ['#26a69a' if c >= o else '#ef5350' for c, o in zip(df_chart['Close'], df_chart['Open'])]
            fig.add_trace(go.Bar(x=df_chart.index, y=df_chart['Volume'], marker_color=vol_colors, name="Volume"), row=2, col=1)
            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['Vol_SMA20'], line=dict(color='#ff9800', width=1), name="Vol MA20"), row=2, col=1)

            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['RSI14'], line=dict(color='#7e57c2', width=1.5), name="RSI 14"), row=3, col=1)
            fig.add_hline(y=70, line_dash="dot", line_color="red", row=3, col=1)
            fig.add_hline(y=30, line_dash="dot", line_color="green", row=3, col=1)

            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['MACD'], line=dict(color='#1e88e5', width=1.5), name="MACD"), row=4, col=1)
            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['MACD_Signal'], line=dict(color='#ff5722', width=1.5), name="Signal"), row=4, col=1)
            hist_colors = ['#26a69a' if h >= 0 else '#ef5350' for h in df_chart['MACD_Hist']]
            fig.add_trace(go.Bar(x=df_chart.index, y=df_chart['MACD_Hist'], marker_color=hist_colors, name="Hist"), row=4, col=1)

            fig.update_layout(height=880, xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig, use_container_width=True)

# -------------------------------------------------------------
# TAB 3: THAI GOLD PRICES & BUY/SELL ANALYSIS
# -------------------------------------------------------------
elif app_mode == "🪙 ราคาทองคำไทย & วิเคราะห์จุดซื้อ-ขายทอง (Thai Gold)":
    st.markdown('<div class="main-header">🪙 ราคาทองคำไทย & วิเคราะห์จุดซื้อ-จุดขายทองคำ</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">รายงานราคาสมาคมค้าทองคำ + วิเคราะห์เทคนิคอล กราฟราคาโลก และแผนการเทรดทองแท่ง</div>', unsafe_allow_html=True)

    with st.spinner("กำลังวิเคราะห์ข้อมูลและสัญญาณเทคนิคอลทองคำ..."):
        gold_analysis = analyze_gold()

    if not gold_analysis or not gold_analysis.get("success"):
        st.error("❌ ไม่สามารถดึงข้อมูลราคาทองคำได้ในขณะนี้ กรุณาลองใหม่อีกครั้ง")
    else:
        gold = gold_analysis['live_info']
        chg_day = gold.get('change_from_prev_day', 0)
        chg_round = gold.get('change_from_prev_round', 0)
        sign_day = "+" if chg_day > 0 else ""
        sign_round = "+" if chg_round > 0 else ""

        st.info(f"📢 **ประกาศโดย:** {gold.get('source')} | **ครั้งที่:** {gold.get('round', 1)} | **เวลา:** {gold.get('announced_at', '')}")

        # Top Metric Cards
        gc1, gc2, gc3, gc4 = st.columns(4)
        gc1.metric("ทองคำแท่ง 96.5% (รับซื้อ)", f"{gold.get('bar_buy', 0):,} ฿", f"{sign_day}{chg_day:,} บาท (เทียบเมื่อวาน)")
        gc2.metric("ทองคำแท่ง 96.5% (ขายออก)", f"{gold.get('bar_sell', 0):,} ฿", f"{sign_round}{chg_round:,} บาท (เทียบรอบก่อน)")
        gc3.metric("ทองรูปพรรณ 96.5% (ขายออก)", f"{gold.get('ornament_sell', 0):,} ฿", f"รับซื้อ: {gold.get('ornament_buy', 0):,.2f} ฿")
        gc4.metric("ทองคำ 99.99% (บาทละ)", f"{gold.get('gold_9999_per_baht', 0):,.2f} ฿", f"กรัมละ {gold.get('gold_9999_per_gram', 0):,.2f} ฿")

        # Score & Verdict
        st.markdown("---")
        gv_col1, gv_col2 = st.columns([1, 2])
        with gv_col1:
            g_score = gold_analysis['score']
            st.metric("คะแนนสัญญาณเทคนิคอลทองคำ", f"{g_score} / 100")
            st.progress(g_score / 100.0)
            st.markdown(f"**คำแนะนำระบบ:** <span style='font-size:1.15rem; color:{gold_analysis['verdict_color']}; font-weight:bold;'>{gold_analysis['verdict']}</span>", unsafe_allow_html=True)
            st.caption(f"Gold Spot: **${gold_analysis['spot_price']:,.2f}** | USD/THB: **{gold_analysis['usd_thb']:.2f} ฿** | RSI: **{gold_analysis['rsi']}**")

        with gv_col2:
            gb_sig = gold_analysis['buy_signals']
            gs_sig = gold_analysis['sell_signals']
            if gb_sig:
                st.markdown('<div class="buy-box"><b>🟢 สัญญาณซื้อทองคำที่ตรวจพบ:</b><br>' + '<br>'.join([f"• {b}" for b in gb_sig]) + '</div>', unsafe_allow_html=True)
            if gs_sig:
                st.markdown('<div class="sell-box"><b>🔴 สัญญาณเตือนขาย/ความเสี่ยง:</b><br>' + '<br>'.join([f"• {s}" for s in gs_sig]) + '</div>', unsafe_allow_html=True)
            if not gb_sig and not gs_sig:
                st.markdown('<div class="gold-box"><b>⚖️ สัญญาณเป็นกลาง:</b> ราคาทองกำลังทรงตัวในกรอบ Sideway</div>', unsafe_allow_html=True)

        # 3 Gold Trading Strategies
        st.markdown("---")
        st.markdown("### 📋 วิเคราะห์จุดซื้อ - จุดขายทองคำแท่ง (Gold Buy/Sell Strategies)")
        g_setups = gold_analysis['trade_setups']

        gt1, gt2, gt3 = st.tabs([
            "🏄 สายเก็งกำไรตามรอบ (Swing Trade 1-4 สัปดาห์)",
            "⚡ สายเล่นสั้นในวัน (Day Trade)",
            "🏦 สายออมทอง / ลงทุนระยะยาว (DCA)"
        ])

        with gt1:
            gsw = g_setups['swing_trade']
            gsc1, gsc2, gsc3, gsc4 = st.columns(4)
            gsc1.metric("🟢 โซนรับเข้าซื้อ (Buy Zone)", gsw['buy_zone'])
            gsc2.metric("🎯 เป้าหมายทำกำไร 1 (TP1)", f"{gsw['tp1']:,} ฿", f"+{((gsw['tp1']-gold.get('bar_sell',0))/gold.get('bar_sell',1))*100:.1f}%")
            gsc3.metric("🎯 เป้าหมายทำกำไร 2 (TP2)", f"{gsw['tp2']:,} ฿", f"+{((gsw['tp2']-gold.get('bar_sell',0))/gold.get('bar_sell',1))*100:.1f}%")
            gsc4.metric("🛑 จุดตัดขาดทุน (Stop Loss)", f"{gsw['sl']:,} ฿", f"-{((gold.get('bar_buy',0)-gsw['sl'])/gold.get('bar_buy',1))*100:.1f}%")
            st.caption(f"💡 **กลยุทธ์:** {gsw['note']}")

        with gt2:
            gdt = g_setups['day_trade']
            gdc1, gdc2, gdc3 = st.columns(3)
            gdc1.metric("🟢 จุดซื้อเข้าตลาด (Entry)", f"{gdt['buy']:,} ฿")
            gdc2.metric("🎯 ขายทำกำไรเร็ว (Quick TP)", f"{gdt['tp']:,} ฿", f"+{gdt['tp']-gdt['buy']:,} บาท")
            gdc3.metric("🛑 คัทลอสแคบ (Tight Stop Loss)", f"{gdt['sl']:,} ฿", f"-{gdt['buy']-gdt['sl']:,} บาท")
            st.caption(f"💡 **กลยุทธ์:** {gdt['note']}")

        with gt3:
            gdca = g_setups['dca']
            gvc1, gvc2 = st.columns(2)
            gvc1.metric("🛒 โซนทยอยสะสม (Buy Accumulate)", gdca['buy_zone'])
            gvc2.metric("💰 เงื่อนไขแบ่งขายทำกำไร", "เป้าหมายระยะยาว")
            st.write(f"📌 **เป้าหมายขาย:** {gdca['exit']}")
            st.caption(f"💡 **กลยุทธ์:** {gdca['note']}")

        # Technical Support & Resistance Levels in Thai Baht & USD
        st.markdown("---")
        st.markdown("##### 📐 ระดับแนวรับ - แนวต้านสำคัญของทองคำแท่ง (แปลงเป็นบาททองคำ)")
        th_lvl = gold_analysis['thai_levels']
        sp_lvl = gold_analysis['spot_levels']
        lc1, lc2, lc3, lc4, lc5 = st.columns(5)
        lc1.metric("แนวรับ 2 (S2)", f"{th_lvl['support_2']:,} ฿", f"${sp_lvl['support_2']:.1f}")
        lc2.metric("แนวรับ 1 (S1)", f"{th_lvl['support_1']:,} ฿", f"${sp_lvl['support_1']:.1f}")
        lc3.metric("Pivot Point", f"{th_lvl['pivot']:,} ฿", f"${sp_lvl['pivot']:.1f}")
        lc4.metric("แนวต้าน 1 (R1)", f"{th_lvl['resistance_1']:,} ฿", f"${sp_lvl['resistance_1']:.1f}")
        lc5.metric("แนวต้าน 2 (R2)", f"{th_lvl['resistance_2']:,} ฿", f"${sp_lvl['resistance_2']:.1f}")

        # Interactive Candlestick Chart with Target Levels
        st.markdown("---")
        st.markdown("### 📈 กราฟราคาทองคำโลก (Gold Futures - GC=F) & โซนเป้าหมาย")
        df_gold = gold_analysis['history_df']

        if not df_gold.empty:
            gfig = make_subplots(
                rows=3, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.04,
                row_heights=[0.60, 0.20, 0.20],
                subplot_titles=("กราฟแท่งเทียน Gold Futures + เส้นแนวรับ-แนวต้าน", "RSI (14)", "MACD (12, 26, 9)")
            )

            gfig.add_trace(go.Candlestick(
                x=df_gold.index, open=df_gold['Open'], high=df_gold['High'], low=df_gold['Low'], close=df_gold['Close'], name="Gold Spot"
            ), row=1, col=1)

            gfig.add_trace(go.Scatter(x=df_gold.index, y=df_gold['EMA20'], line=dict(color='#ff9800', width=1.5), name="EMA 20"), row=1, col=1)
            gfig.add_trace(go.Scatter(x=df_gold.index, y=df_gold['EMA50'], line=dict(color='#2196f3', width=1.5), name="EMA 50"), row=1, col=1)
            gfig.add_trace(go.Scatter(x=df_gold.index, y=df_gold['EMA200'], line=dict(color='#9c27b0', width=2), name="EMA 200"), row=1, col=1)

            # Target lines on Gold chart
            gfig.add_hline(y=sp_lvl['resistance_1'], line_dash="dash", line_color="#1976d2", annotation_text=f"R1 (${sp_lvl['resistance_1']:.1f})", row=1, col=1)
            gfig.add_hline(y=sp_lvl['resistance_2'], line_dash="dash", line_color="#7b1fa2", annotation_text=f"R2 (${sp_lvl['resistance_2']:.1f})", row=1, col=1)
            gfig.add_hline(y=sp_lvl['support_1'], line_dash="dash", line_color="#d32f2f", annotation_text=f"S1 (${sp_lvl['support_1']:.1f})", row=1, col=1)

            gfig.add_trace(go.Scatter(x=df_gold.index, y=df_gold['RSI14'], line=dict(color='#7e57c2', width=1.5), name="RSI 14"), row=2, col=1)
            gfig.add_hline(y=70, line_dash="dot", line_color="red", row=2, col=1)
            gfig.add_hline(y=30, line_dash="dot", line_color="green", row=2, col=1)

            gfig.add_trace(go.Scatter(x=df_gold.index, y=df_gold['MACD'], line=dict(color='#1e88e5', width=1.5), name="MACD"), row=3, col=1)
            gfig.add_trace(go.Scatter(x=df_gold.index, y=df_gold['MACD_Signal'], line=dict(color='#ff5722', width=1.5), name="Signal"), row=3, col=1)
            ghist_colors = ['#26a69a' if h >= 0 else '#ef5350' for h in df_gold['MACD_Hist']]
            gfig.add_trace(go.Bar(x=df_gold.index, y=df_gold['MACD_Hist'], marker_color=ghist_colors, name="Hist"), row=3, col=1)

            gfig.update_layout(height=800, xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(gfig, use_container_width=True)

# -------------------------------------------------------------
# TAB 4: USER GUIDE
# -------------------------------------------------------------
else:
    st.markdown('<div class="main-header">ℹ️ วิธีการใช้งานและคำอธิบายกลยุทธ์</div>', unsafe_allow_html=True)
    st.markdown("""
    ### 📖 กลยุทธ์การสแกนหุ้น:
    1. **EMA Golden Cross:** EMA 20 ตัดขึ้นเหนือ EMA 50 หรือ ราคายืนเหนือ EMA 200 วัน
    2. **MACD Bullish Cross:** MACD ตัดเหนือ Signal Line (จุดกลับตัว)
    3. **RSI Oversold Bounce:** RSI < 35 สำหรับสายดักรีบาวด์
    4. **Volume Breakout:** Volume พุ่งเกิน 1.8 เท่า พร้อมแท่งเขียว
    5. **Bollinger Bands Squeeze & Breakout:** บีบตัวเตรียมระเบิดกรอบบน
    6. **High Dividend & Value:** ปันผล >= 4%, P/E <= 18 เท่า, P/BV เหมาะสม
    7. **52-Week High Breakout:** จ่อทำ New High 52 สัปดาห์

    ---
    ### 🪙 การวิเคราะห์จุดซื้อ-จุดขายทองคำ:
    - **แปลงราคาจากระดับสากลสู่บาททองคำ:** คำนวณแนวรับแนวต้านจาก Gold Spot (USD/oz) และค่าเงินบาท (USD/THB) เป็นราคาบาทละ
    - **Swing Trade:** รอเข้าซื้อโซนแนวรับ S1 และตั้งขายทำกำไรที่ R1 และ R2
    - **Day Trade:** เล่นรอบเร็วตามการประกาศของสมาคมค้าทองคำระหว่างวัน
    - **DCA:** ซื้อสะสมเมื่อราคาพักตัวใกล้แนวรับใหญ่ S2 เพื่อถือครองป้องกันเงินเฟ้อระยะยาว
    """)
