from flask import Flask, jsonify, send_file, request
from flask_cors import CORS
import yfinance as yf
import os, time

app = Flask(__name__)
CORS(app)

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
HTML_FILE = os.path.join(BASE_DIR, 'posicalc_index.html')

_cache = {}
CACHE_TTL = 300  # 5 min

def cache_get(k):
    if k in _cache:
        d, ts = _cache[k]
        if time.time() - ts < CACHE_TTL: return d
    return None

def cache_set(k, d):
    _cache[k] = (d, time.time())

@app.route('/')
def index():
    if os.path.exists(HTML_FILE): return send_file(HTML_FILE)
    return "<h3>posicalc_index.html not found</h3>", 404

@app.route('/api/ping')
def ping():
    return jsonify({'status': 'ok', 'service': 'PosiCalc'})

@app.route('/api/price/<symbol>')
def get_price(symbol):
    sym = symbol.upper().strip()
    # Add .NS if no exchange suffix
    if not sym.endswith('.NS') and not sym.endswith('.BO'):
        sym = sym + '.NS'

    cached = cache_get(sym)
    if cached:
        cached['cached'] = True
        return jsonify(cached)

    try:
        ticker = yf.Ticker(sym)
        hist   = ticker.history(period='5d', auto_adjust=False)
        if hist is None or hist.empty:
            # Try BSE if NSE fails
            if sym.endswith('.NS'):
                sym_bse = sym.replace('.NS', '.BO')
                ticker  = yf.Ticker(sym_bse)
                hist    = ticker.history(period='5d', auto_adjust=False)
                if hist is not None and not hist.empty:
                    sym = sym_bse
                else:
                    return jsonify({'error': f'No data for {symbol}. Check symbol or market hours.'}), 404
            else:
                return jsonify({'error': f'No data for {symbol}.'}), 404

        price    = round(float(hist['Close'].iloc[-1]), 2)
        prev     = round(float(hist['Close'].iloc[-2]), 2) if len(hist) >= 2 else price
        change   = round(price - prev, 2)
        chg_pct  = round((change / prev) * 100, 2) if prev else 0
        day_high = round(float(hist['High'].iloc[-1]), 2)
        day_low  = round(float(hist['Low'].iloc[-1]), 2)

        try:
            fi   = ticker.fast_info
            w52h = round(float(fi.year_high), 2) if hasattr(fi,'year_high') and fi.year_high else None
            w52l = round(float(fi.year_low),  2) if hasattr(fi,'year_low')  and fi.year_low  else None
        except:
            w52h = w52l = None

        result = {
            'symbol': sym, 'price': price, 'prev_close': prev,
            'change': change, 'change_pct': chg_pct,
            'day_high': day_high, 'day_low': day_low,
            'week52_high': w52h, 'week52_low': w52l,
            'source': 'Yahoo Finance (15-min delayed)', 'cached': False
        }
        cache_set(sym, result)
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search')
def search():
    q = request.args.get('q', '').strip().upper()
    if len(q) < 2:
        return jsonify([])
    results = [{"s": s["s"], "n": s["n"]}
               for s in STOCKS
               if q in s["s"] or q in s["n"].upper()][:10]
    return jsonify(results)

STOCKS = [
    {"s":"RELIANCE",    "n":"Reliance Industries"},
    {"s":"TCS",         "n":"Tata Consultancy Services"},
    {"s":"INFY",        "n":"Infosys"},
    {"s":"HDFCBANK",    "n":"HDFC Bank"},
    {"s":"ICICIBANK",   "n":"ICICI Bank"},
    {"s":"WIPRO",       "n":"Wipro"},
    {"s":"TATAMOTORS",  "n":"Tata Motors"},
    {"s":"SBIN",        "n":"State Bank of India"},
    {"s":"ADANIENT",    "n":"Adani Enterprises"},
    {"s":"BAJFINANCE",  "n":"Bajaj Finance"},
    {"s":"MARUTI",      "n":"Maruti Suzuki India"},
    {"s":"LTIM",        "n":"LTIMindtree"},
    {"s":"TECHM",       "n":"Tech Mahindra"},
    {"s":"COALINDIA",   "n":"Coal India"},
    {"s":"NTPC",        "n":"NTPC"},
    {"s":"POWERGRID",   "n":"Power Grid Corporation"},
    {"s":"HAL",         "n":"Hindustan Aeronautics Ltd"},
    {"s":"BEL",         "n":"Bharat Electronics"},
    {"s":"DRREDDY",     "n":"Dr Reddys Laboratories"},
    {"s":"SUNPHARMA",   "n":"Sun Pharmaceutical"},
    {"s":"CIPLA",       "n":"Cipla"},
    {"s":"DIVISLAB",    "n":"Divis Laboratories"},
    {"s":"APOLLOHOSP",  "n":"Apollo Hospitals"},
    {"s":"HINDUNILVR",  "n":"Hindustan Unilever"},
    {"s":"ITC",         "n":"ITC"},
    {"s":"TITAN",       "n":"Titan Company"},
    {"s":"NESTLEIND",   "n":"Nestle India"},
    {"s":"ULTRACEMCO",  "n":"UltraTech Cement"},
    {"s":"GRASIM",      "n":"Grasim Industries"},
    {"s":"TATASTEEL",   "n":"Tata Steel"},
    {"s":"JSWSTEEL",    "n":"JSW Steel"},
    {"s":"HINDALCO",    "n":"Hindalco Industries"},
    {"s":"VEDL",        "n":"Vedanta"},
    {"s":"ONGC",        "n":"Oil and Natural Gas Corp"},
    {"s":"IOC",         "n":"Indian Oil Corporation"},
    {"s":"BPCL",        "n":"Bharat Petroleum"},
    {"s":"AXISBANK",    "n":"Axis Bank"},
    {"s":"KOTAKBANK",   "n":"Kotak Mahindra Bank"},
    {"s":"INDUSINDBK",  "n":"IndusInd Bank"},
    {"s":"PNB",         "n":"Punjab National Bank"},
    {"s":"BANKBARODA",  "n":"Bank of Baroda"},
    {"s":"CANARABANK",  "n":"Canara Bank"},
    {"s":"BAJAJFINSV",  "n":"Bajaj Finserv"},
    {"s":"HDFCLIFE",    "n":"HDFC Life Insurance"},
    {"s":"SBILIFE",     "n":"SBI Life Insurance"},
    {"s":"BHARTIARTL",  "n":"Bharti Airtel"},
    {"s":"ZOMATO",      "n":"Zomato"},
    {"s":"PAYTM",       "n":"Paytm One97 Communications"},
    {"s":"IRFC",        "n":"Indian Railway Finance Corp"},
    {"s":"IRCTC",       "n":"Indian Railway Catering Tourism"},
    {"s":"RVNL",        "n":"Rail Vikas Nigam"},
    {"s":"NMDC",        "n":"NMDC"},
    {"s":"SAIL",        "n":"Steel Authority of India"},
    {"s":"DLF",         "n":"DLF"},
    {"s":"GODREJPROP",  "n":"Godrej Properties"},
    {"s":"POLYCAB",     "n":"Polycab India"},
    {"s":"ABB",         "n":"ABB India"},
    {"s":"SIEMENS",     "n":"Siemens India"},
    {"s":"HCLTECH",     "n":"HCL Technologies"},
    {"s":"MPHASIS",     "n":"Mphasis"},
    {"s":"PERSISTENT",  "n":"Persistent Systems"},
    {"s":"COFORGE",     "n":"Coforge"},
    {"s":"TATAPOWER",   "n":"Tata Power"},
    {"s":"ADANIPOWER",  "n":"Adani Power"},
    {"s":"ADANIGREEN",  "n":"Adani Green Energy"},
    {"s":"ADANIPORTS",  "n":"Adani Ports and SEZ"},
    {"s":"ASHOKLEY",    "n":"Ashok Leyland"},
    {"s":"MM",          "n":"Mahindra and Mahindra"},
    {"s":"HEROMOTOCO",  "n":"Hero MotoCorp"},
    {"s":"BAJAJ-AUTO",  "n":"Bajaj Auto"},
    {"s":"EICHERMOT",   "n":"Eicher Motors"},
    {"s":"TVSMOTOR",    "n":"TVS Motor Company"},
    {"s":"INDIGO",      "n":"InterGlobe Aviation IndiGo"},
    {"s":"INDIANHOTELS","n":"Indian Hotels Taj"},
    {"s":"DIXON",       "n":"Dixon Technologies"},
    {"s":"PVRINOX",     "n":"PVR Inox"},
    {"s":"LICI",        "n":"LIC of India"},
    {"s":"ASIANPAINT",  "n":"Asian Paints"},
    {"s":"BERGEPAINT",  "n":"Berger Paints"},
    {"s":"PIDILITIND",  "n":"Pidilite Industries"},
    {"s":"TRENT",       "n":"Trent"},
    {"s":"DMART",       "n":"Avenue Supermarts DMart"},
    {"s":"KPITTECH",    "n":"KPIT Technologies"},
    {"s":"LTTS",        "n":"L and T Technology Services"},
    {"s":"BSOFT",       "n":"Birlasoft"},
    {"s":"MPHASIS",     "n":"Mphasis"},
    {"s":"ROUTE",       "n":"Route Mobile"},
    {"s":"TANLA",       "n":"Tanla Platforms"},
    {"s":"ZENSARTECH",  "n":"Zensar Technologies"},
    {"s":"INTELLECT",   "n":"Intellect Design Arena"},
    {"s":"MASTEK",      "n":"Mastek"},
    {"s":"NAUKRI",      "n":"Info Edge Naukri"},
    {"s":"POLICYBZR",   "n":"PB Fintech Policybazaar"},
    {"s":"NYKAA",       "n":"FSN E-Commerce Nykaa"},
    {"s":"DELHIVERY",   "n":"Delhivery"},
    {"s":"SWIGGY",      "n":"Swiggy"},
    {"s":"KAYNES",      "n":"Kaynes Technology"},
    {"s":"DATAPATTERNSIND","n":"Data Patterns India"},
    {"s":"MAZDOCK",     "n":"Mazagon Dock Shipbuilders"},
    {"s":"COCHINSHIP",  "n":"Cochin Shipyard"},
    {"s":"GRSE",        "n":"Garden Reach Shipbuilders"},
    {"s":"MIDHANI",     "n":"Mishra Dhatu Nigam"},
    {"s":"BEML",        "n":"BEML"},
    {"s":"BHEL",        "n":"Bharat Heavy Electricals"},
    {"s":"CONCOR",      "n":"Container Corporation of India"},
    {"s":"AUROPHARMA",  "n":"Aurobindo Pharma"},
    {"s":"LUPIN",       "n":"Lupin"},
    {"s":"TORNTPHARM",  "n":"Torrent Pharmaceuticals"},
    {"s":"ALKEM",       "n":"Alkem Laboratories"},
    {"s":"IPCALAB",     "n":"IPCA Laboratories"},
    {"s":"NATCO",       "n":"Natco Pharma"},
    {"s":"GLENMARK",    "n":"Glenmark Pharmaceuticals"},
    {"s":"JUBILANT",    "n":"Jubilant Pharmova"},
    {"s":"ABBOTINDIA",  "n":"Abbott India"},
    {"s":"PFIZER",      "n":"Pfizer India"},
    {"s":"SANOFI",      "n":"Sanofi India"},
    {"s":"TATACOMM",    "n":"Tata Communications"},
    {"s":"MTNL",        "n":"Mahanagar Telephone Nigam"},
    {"s":"TTML",        "n":"Tata Teleservices"},
    {"s":"IDEA",        "n":"Vodafone Idea"},
    {"s":"INDUSTOWER",  "n":"Indus Towers"},
    {"s":"OBEROIRLTY",  "n":"Oberoi Realty"},
    {"s":"PRESTIGE",    "n":"Prestige Estates"},
    {"s":"BRIGADE",     "n":"Brigade Enterprises"},
    {"s":"SOBHA",       "n":"Sobha"},
    {"s":"MAHINDCIE",   "n":"Mahindra CIE Automotive"},
    {"s":"MOTHERSON",   "n":"Samvardhana Motherson"},
    {"s":"BOSCHLTD",    "n":"Bosch India"},
    {"s":"MINDA",       "n":"Minda Industries"},
    {"s":"SUNDRMFAST",  "n":"Sundram Fasteners"},
    {"s":"TIINDIA",     "n":"Tube Investments of India"},
]

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"\n{'='*50}\n  PosiCalc Server running on port {port}\n{'='*50}\n")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
