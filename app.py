#!/usr/bin/env python3
"""
PosiCalc - Stock Price API Server
===================================
Deploy FREE on: Render.com / Railway.app / Koyeb.com
No auth needed. yfinance fetches NSE/BSE data server-side.

Local run:
  pip install flask flask-cors yfinance
  python3 app.py
  Open: http://localhost:5000

Cloud deploy (Render.com - free):
  1. Push this folder to GitHub
  2. Render.com -> New Web Service -> connect repo
  3. Build cmd: pip install -r requirements.txt
  4. Start cmd: python app.py
  Done! Get your public URL like https://posicalc.onrender.com
"""

from flask import Flask, jsonify, send_file, request
from flask_cors import CORS
import yfinance as yf
import os, time, threading
from functools import lru_cache

app = Flask(__name__)
CORS(app)  # Allow all origins — public API

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
HTML_FILE = os.path.join(BASE_DIR, 'posicalc_index.html')

# ── Simple in-memory cache (avoid hammering Yahoo) ──
_cache = {}
CACHE_TTL = 300  # 5 minutes

def cache_get(key):
    if key in _cache:
        data, ts = _cache[key]
        if time.time() - ts < CACHE_TTL:
            return data
    return None

def cache_set(key, data):
    _cache[key] = (data, time.time())

# ─────────────────────────────────────────────────────
@app.route('/')
def index():
    if os.path.exists(HTML_FILE):
        return send_file(HTML_FILE)
    return "<h3>posicalc_index.html not found in same folder</h3>", 404

@app.route('/api/ping')
def ping():
    return jsonify({'status': 'ok', 'service': 'PosiCalc API', 'source': 'Yahoo Finance'})

@app.route('/api/price/<symbol>')
def get_price(symbol):
    # Sanitize symbol
    symbol = symbol.upper().strip()
    # Ensure NSE/BSE suffix
    if not symbol.endswith('.NS') and not symbol.endswith('.BO'):
        symbol = symbol + '.NS'

    cached = cache_get(symbol)
    if cached:
        cached['cached'] = True
        return jsonify(cached)

    try:
        ticker = yf.Ticker(symbol)
        hist   = ticker.history(period='5d', auto_adjust=False)
        if hist is None or hist.empty:
            return jsonify({'error': f'No data for {symbol}. Check symbol or try after market hours.'}), 404

        price    = round(float(hist['Close'].iloc[-1]), 2)
        prev     = round(float(hist['Close'].iloc[-2]), 2) if len(hist) >= 2 else price
        change   = round(price - prev, 2)
        chg_pct  = round((change / prev) * 100, 2) if prev else 0
        day_high = round(float(hist['High'].iloc[-1]), 2)
        day_low  = round(float(hist['Low'].iloc[-1]),  2)

        # 52W via fast_info (faster than 1y history)
        fi    = ticker.fast_info
        w52h  = round(float(fi.year_high), 2) if hasattr(fi, 'year_high') and fi.year_high else None
        w52l  = round(float(fi.year_low),  2) if hasattr(fi, 'year_low')  and fi.year_low  else None

        result = {
            'symbol':      symbol,
            'price':       price,
            'prev_close':  prev,
            'change':      change,
            'change_pct':  chg_pct,
            'day_high':    day_high,
            'day_low':     day_low,
            'week52_high': w52h,
            'week52_low':  w52l,
            'source':      'Yahoo Finance (15-min delayed)',
            'cached':      False
        }
        cache_set(symbol, result)
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search')
def search():
    q = request.args.get('q', '').strip().upper()
    if len(q) < 1:
        return jsonify([])
    results = [s for s in STOCKS if q in s['s'] or q in s['n'].upper()][:10]
    return jsonify(results)

# Full stock list for search
STOCKS = [
    {"s":"RELIANCE",   "n":"Reliance Industries"},
    {"s":"TCS",        "n":"Tata Consultancy Services"},
    {"s":"INFY",       "n":"Infosys"},
    {"s":"HDFCBANK",   "n":"HDFC Bank"},
    {"s":"ICICIBANK",  "n":"ICICI Bank"},
    {"s":"WIPRO",      "n":"Wipro"},
    {"s":"TATAMOTORS", "n":"Tata Motors"},
    {"s":"SBIN",       "n":"State Bank of India"},
    {"s":"ADANIENT",   "n":"Adani Enterprises"},
    {"s":"BAJFINANCE", "n":"Bajaj Finance"},
    {"s":"MARUTI",     "n":"Maruti Suzuki"},
    {"s":"LTIM",       "n":"LTIMindtree"},
    {"s":"TECHM",      "n":"Tech Mahindra"},
    {"s":"COALINDIA",  "n":"Coal India"},
    {"s":"NTPC",       "n":"NTPC"},
    {"s":"POWERGRID",  "n":"Power Grid Corporation"},
    {"s":"HAL",        "n":"Hindustan Aeronautics Ltd"},
    {"s":"BEL",        "n":"Bharat Electronics"},
    {"s":"DRREDDY",    "n":"Dr Reddys Laboratories"},
    {"s":"SUNPHARMA",  "n":"Sun Pharmaceutical"},
    {"s":"CIPLA",      "n":"Cipla"},
    {"s":"DIVISLAB",   "n":"Divis Laboratories"},
    {"s":"APOLLOHOSP", "n":"Apollo Hospitals"},
    {"s":"HINDUNILVR", "n":"Hindustan Unilever"},
    {"s":"ITC",        "n":"ITC"},
    {"s":"TITAN",      "n":"Titan Company"},
    {"s":"NESTLEIND",  "n":"Nestle India"},
    {"s":"ULTRACEMCO", "n":"UltraTech Cement"},
    {"s":"GRASIM",     "n":"Grasim Industries"},
    {"s":"TATASTEEL",  "n":"Tata Steel"},
    {"s":"JSWSTEEL",   "n":"JSW Steel"},
    {"s":"HINDALCO",   "n":"Hindalco Industries"},
    {"s":"VEDL",       "n":"Vedanta"},
    {"s":"ONGC",       "n":"Oil and Natural Gas Corp"},
    {"s":"IOC",        "n":"Indian Oil Corporation"},
    {"s":"BPCL",       "n":"Bharat Petroleum"},
    {"s":"AXISBANK",   "n":"Axis Bank"},
    {"s":"KOTAKBANK",  "n":"Kotak Mahindra Bank"},
    {"s":"INDUSINDBK", "n":"IndusInd Bank"},
    {"s":"PNB",        "n":"Punjab National Bank"},
    {"s":"BANKBARODA", "n":"Bank of Baroda"},
    {"s":"CANARABANK", "n":"Canara Bank"},
    {"s":"BAJAJFINSV", "n":"Bajaj Finserv"},
    {"s":"HDFCLIFE",   "n":"HDFC Life Insurance"},
    {"s":"SBILIFE",    "n":"SBI Life Insurance"},
    {"s":"BHARTIARTL", "n":"Bharti Airtel"},
    {"s":"ZOMATO",     "n":"Zomato"},
    {"s":"PAYTM",      "n":"Paytm One97 Communications"},
    {"s":"IRFC",       "n":"Indian Railway Finance Corp"},
    {"s":"IRCTC",      "n":"Indian Railway Catering Tourism"},
    {"s":"RVNL",       "n":"Rail Vikas Nigam"},
    {"s":"NMDC",       "n":"NMDC"},
    {"s":"SAIL",       "n":"Steel Authority of India"},
    {"s":"DLF",        "n":"DLF"},
    {"s":"GODREJPROP", "n":"Godrej Properties"},
    {"s":"POLYCAB",    "n":"Polycab India"},
    {"s":"ABB",        "n":"ABB India"},
    {"s":"SIEMENS",    "n":"Siemens India"},
    {"s":"HCLTECH",    "n":"HCL Technologies"},
    {"s":"MPHASIS",    "n":"Mphasis"},
    {"s":"PERSISTENT", "n":"Persistent Systems"},
    {"s":"COFORGE",    "n":"Coforge"},
    {"s":"TATAPOWER",  "n":"Tata Power"},
    {"s":"ADANIPOWER", "n":"Adani Power"},
    {"s":"ADANIGREEN", "n":"Adani Green Energy"},
    {"s":"ADANIPORTS", "n":"Adani Ports and SEZ"},
    {"s":"ASHOKLEY",   "n":"Ashok Leyland"},
    {"s":"MM",         "n":"Mahindra and Mahindra"},
    {"s":"HEROMOTOCO", "n":"Hero MotoCorp"},
    {"s":"BAJAJ-AUTO", "n":"Bajaj Auto"},
    {"s":"EICHERMOT",  "n":"Eicher Motors"},
    {"s":"TVSMOTOR",   "n":"TVS Motor Company"},
    {"s":"INDIGO",     "n":"InterGlobe Aviation IndiGo"},
    {"s":"INDIANHOTELS","n":"Indian Hotels Taj"},
    {"s":"DIXON",      "n":"Dixon Technologies"},
    {"s":"PVRINOX",    "n":"PVR Inox"},
    {"s":"LICI",       "n":"LIC of India"},
    {"s":"ASIANPAINT", "n":"Asian Paints"},
    {"s":"BERGEPAINT", "n":"Berger Paints"},
    {"s":"PIDILITIND", "n":"Pidilite Industries"},
    {"s":"TRENT",      "n":"Trent"},
    {"s":"DMART",      "n":"Avenue Supermarts DMart"},
    {"s":"KPITTECH",   "n":"KPIT Technologies"},
    {"s":"LTTS",       "n":"L and T Technology Services"},
]

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"\n{'='*50}")
    print(f"  PosiCalc API Server")
    print(f"  Local : http://localhost:{port}")
    print(f"  Ping  : http://localhost:{port}/api/ping")
    print(f"  Test  : http://localhost:{port}/api/price/INFY")
    print(f"{'='*50}\n")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
