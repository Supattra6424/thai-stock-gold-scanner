# 🇹🇭 Thai Stock Scanner & Deep Analyzer
### ระบบสแกนและวิเคราะห์หุ้นไทย (SET50 / SET100 / หุ้นรายตัว)

โปรแกรมสำหรับนักลงทุนและเทรดเดอร์ตลาดหลักทรัพย์แห่งประเทศไทย (SET) ที่ช่วยคัดกรองหุ้นตามสัญญาณเทคนิคอลและปัจจัยพื้นฐาน พร้อมระบบวิเคราะห์เจาะลึกรายตัว คำนวณแผนการเทรด (จุดเข้าซื้อ, จุดทำกำไร, จุดตัดขาดทุน) และแสดงผลกราฟแท่งเทียนแบบ Interactive

---

## 🌟 ฟีเจอร์หลัก (Key Features)

### 🪙 ระบบรายงานราคาทองคำไทย & วิเคราะห์ทองคำ (Thai Gold Price & Analysis)
- **ราคาทองคำแท่งและทองรูปพรรณ 96.5%:** ราคารับซื้อ, ราคาขายออก ตามประกาศของ **สมาคมค้าทองคำ (Gold Traders Association)**
- **ราคาทองคำ 99.99%:** ราคาต่อบาท และราคาต่อกรัม
- **ข้อมูลการประกาศ:** ครั้งที่ประกาศของวัน, เวลาที่ประกาศ, ความเปลี่ยนแปลงเทียบวันก่อนหน้า (+/- บาท)
- **ปัจจัยขับเคลื่อนตลาด (Market Drivers):** ราคาทองคำโลก Gold Spot (XAU/USD) และ อัตราแลกเปลี่ยนค่าเงินบาท (USD/THB)
- **ราคาร้านทองชั้นนำ:** แม่ทองสุก (MTS), วายแอลจี (YLG), ออโรร่า (Aurora)
- **กราฟราคาทองคำโลกย้อนหลัง (Gold Futures Chart):** พร้อมอินดิเคเตอร์ EMA, RSI (14), MACD

### 1. 🎯 ระบบสแกนหุ้นหลากมิติ (Multi-Strategy Scanner)
- **ครอบคลุมหุ้นไทย:** รองรับทั้งหุ้นกลุ่ม **SET50**, **SET100** และ Custom (กรอกชื่อหุ้นเองได้)
- **กลยุทธ์ยอดนิยมที่คัดสรรมาให้:**
  - 📈 **EMA Golden Cross:** EMA 20 ตัดขึ้นเหนือ EMA 50 หรือ ยืนเหนือเส้น 200 วัน (รันเทรนด์)
  - 🔄 **MACD Bullish Cross:** MACD ตัดขึ้นเหนือ Signal Line หรือกำลังตัดขึ้นจากแดนลบ (ต้นรอบ)
  - 📉 **RSI Oversold Bounce:** RSI < 35 สำหรับสายดักรีบาวด์ (Buy on Dip) ในหุ้นที่ย่อลึกเกินไป
  - 💥 **Volume Breakout:** วอลุ่มพุ่งเกิน 1.8 เท่าของค่าเฉลี่ย 20 วัน พร้อมแท่งเทียนเขียว
  - 📦 **Bollinger Bands Squeeze & Breakout:** หุ้นที่บีบตัวแคบและเตรียมระเบิดราคา
  - 💰 **High Dividend & Value Play:** หุ้นปันผลเด่น (Div >= 4%), P/E ต่ำ (<= 18 เท่า), P/BV เหมาะสม
  - 🚀 **52-Week High Breakout:** หุ้นที่กำลังจ่อทดสอบหรือทำ New High รอบ 52 สัปดาห์
- **ความเร็วสูง:** ใช้ระบบประมวลผลแบบคู่ขนาน (Multi-threading) พร้อม Local Cache (SQLite)

### 2. 🔬 ระบบวิเคราะห์เจาะลึกรายตัว (Deep Dive Stock Analyzer)
- **ประเมินคะแนนความแข็งแกร่ง (Bullish Strength Score):** 0 - 100 คะแนน
- **คำแนะนำระบบ (Action Verdict):** Strong Buy, Buy/Accumulate, Wait & See, หรือ Avoid
- **วางแผนการเทรดอัตโนมัติ (Automated Trade Plan):**
  - **โซนราคาเข้าซื้อ (Entry Zone)**
  - **เป้าหมายทำกำไร 1 & 2 (Target 1, Target 2)** อิงตาม Resistance & ATR
  - **จุดตัดขาดทุน (Stop Loss)** อิงตาม Support สำคัญ & ATR
  - **อัตราผลตอบแทนต่อความเสี่ยง (Risk / Reward Ratio: R:R)**
- **สรุปสัญญาณบวก & จุดที่ต้องระมัดระวัง (Pros & Risks Summary)** ชัดเจนเข้าใจง่าย
- **การเงินและมูลค่า:** P/E, P/BV, Dividend Yield %, ROE %, 52W High/Low

### 3. 📊 กราฟราคาแบบ Interactive (Plotly Candlestick Chart)
- แสดงแท่งเทียนแบบเรียลไทม์ ซูมเข้า-ออก ดูราคาย้อนหลังได้
- เส้นค่าเฉลี่ย EMA 20, EMA 50, EMA 200
- แถบความผันผวน Bollinger Bands (Upper, Middle, Lower)
- ปริมาณการซื้อขาย (Volume) พร้อมเส้นเฉลี่ย MA20 แยกแท่งเขียว/แดง
- อินดิเคเตอร์ย่อย: RSI (14) และ MACD (Line, Signal, Histogram)
- ระดับแนวรับ-แนวต้านอัตโนมัติ (Pivot Points, S1, S2, R1, R2)

---

## 📁 โครงสร้างโปรเจกต์ (Project Structure)

```text
Settrade/
├── app.py              # Web Dashboard แบบ Interactive พัฒนาด้วย Streamlit
├── cli.py              # เครื่องมือสั่งการและสแกนผ่าน Command Line (Terminal)
├── scanner.py          # เครื่องมือคัดกรองและประเมินสัญญาณตามกลยุทธ์ต่างๆ
├── analyzer.py         # เครื่องมือวิเคราะห์หุ้นรายตัวและคำนวณแผนการเทรด
├── indicators.py       # สูตรคำนวณ EMA, SMA, RSI, MACD, BB, ATR, Pivot Points
├── stocks_data.py      # รายชื่อหุ้น SET50/SET100, ข้อมูล Sector, Cache และ Data Engine
└── README.md           # คู่มือการใช้งานโปรแกรม
```

---

## 🚀 วิธีการใช้งาน (How to Use)

### 1. เปิดใช้งาน Web Dashboard (แนะนำสำหรับหน้าจอสวยงาม ใช้งานง่าย)
รันคำสั่งต่อไปนี้ใน Terminal:
```bash
streamlit run app.py
```
- เปิดเบราว์เซอร์ไปที่ `http://localhost:8501`
- เมนูด้านซ้ายสามารถสลับระหว่าง:
  - **🎯 สแกนหาหุ้นเด่น (Stock Scanner):** เลือกกลยุทธ์, เลือกว่าจะสแกน SET50 หรือ SET100, กดปุ่มเดียวรู้ผลทันที พร้อมปุ่มดาวน์โหลด CSV
  - **🔬 วิเคราะห์เจาะลึกรายตัว (Stock Analyzer):** พิมพ์ชื่อย่อหุ้น เช่น `PTT`, `CPALL`, `BDMS`, `DELTA`, `AOT` เพื่อดูแผนเทรดและกราฟเทคนิคอล
  - **ℹ️ วิธีใช้งานและกลยุทธ์:** ศึกษาเงื่อนไขแต่ละกลยุทธ์

---

### 2. ใช้งานผ่าน Command Line (CLI)

#### 🔹 สแกนหุ้น SET50 ภาพรวมทั้งหมด:
```bash
python cli.py --scan all --universe set50
```

#### 🔹 สแกนหาหุ้นที่เกิด EMA Golden Cross ใน SET100:
```bash
python cli.py --scan golden_cross --universe set100
```

#### 🔹 สแกนหาหุ้นปันผลเด่น & หุ้นคุณค่า (High Dividend & Value):
```bash
python cli.py --scan high_dividend_value --universe set50
```

#### 🔹 สแกนหาหุ้น Volume เข้าผิดปกติ (Volume Breakout):
```bash
python cli.py --scan volume_breakout --universe set50
```

#### 🔹 สแกนเฉพาะหุ้นที่เราสนใจ และบันทึกผลเป็น CSV:
```bash
python cli.py --scan all --symbols PTT,CPALL,BDMS,DELTA,ADVANC,KBANK,SCB --export my_scan.csv
```

#### 🔹 วิเคราะห์หุ้นรายตัวเชิงลึก:
```bash
python cli.py --analyze PTT
python cli.py --analyze CPALL
python cli.py --analyze DELTA
```

---

## ⚙️ ข้อมูลและแหล่งที่มา (Data Source)
- ดึงข้อมูลราคาหุ้นและงบการเงินผ่าน Yahoo Finance (สัญลักษณ์ลงท้ายด้วย `.BK` เช่น `PTT.BK`, `CPALL.BK`)
- มีระบบ Local Caching (SQLite) บันทึกข้อมูลพื้นฐานอัตโนมัติ ช่วยให้การสแกนรอบต่อๆ ไปรวดเร็วและไม่ติด Rate Limit
