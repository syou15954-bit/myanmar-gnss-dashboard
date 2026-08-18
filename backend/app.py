import os
import time
import requests
from flask import Flask, render_template, jsonify

app = Flask(__name__, template_folder='.', static_folder='.')

TLE_CACHE = {}
LAST_FETCH_TIME = 0
CACHE_DURATION = 14400  # 4 Hours Cache

GNSS_CELESTRAK_URL = 'https://celestrak.org/NORAD/elements/gp.php?GROUP=gnss&FORMAT=tle'

def categorize_sat(name):
    uname = name.upper()
    if 'GPS' in uname:
        return 'gps'
    elif 'BEIDOU' in uname or 'BD' in uname or 'C0' in uname:
        return 'bds'
    elif 'GALILEO' in uname or 'GSAT' in uname:
        return 'galileo'
    elif 'GLONASS' in uname or 'COSMOS' in uname:
        return 'glonass'
    return 'gps'

def parse_gnss_tle(tle_text):
    categories = {'gps': [], 'bds': [], 'galileo': [], 'glonass': [], 'all': []}
    if not tle_text or '<html' in tle_text.lower():
        return categories
        
    lines = [line.strip() for line in tle_text.strip().split('\n') if line.strip()]
    
    i = 0
    while i < len(lines):
        try:
            if i + 2 < len(lines) and lines[i+1].startswith('1 ') and lines[i+2].startswith('2 '):
                sat_name = lines[i]
                line1 = lines[i+1]
                line2 = lines[i+2]
                if len(line1) >= 7:
                    norad_id = line1[2:7].strip()
                    cat = categorize_sat(sat_name)
                    sat_obj = {
                        'id': norad_id,
                        'name': f"{sat_name} ({norad_id})",
                        'line1': line1,
                        'line2': line2
                    }
                    categories[cat].append(sat_obj)
                    categories['all'].append(sat_obj)
                i += 3
            elif lines[i].startswith('1 ') and i + 1 < len(lines) and lines[i+1].startswith('2 '):
                line1 = lines[i]
                line2 = lines[i+1]
                if len(line1) >= 7:
                    norad_id = line1[2:7].strip()
                    sat_obj = {
                        'id': norad_id,
                        'name': f"SAT-{norad_id}",
                        'line1': line1,
                        'line2': line2
                    }
                    categories['gps'].append(sat_obj)
                    categories['all'].append(sat_obj)
                i += 2
            else:
                i += 1
        except Exception:
            i += 1
    return categories

@app.route('/')
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/tle')
def get_live_tles():
    global TLE_CACHE, LAST_FETCH_TIME
    now = time.time()

    if TLE_CACHE and (now - LAST_FETCH_TIME < CACHE_DURATION):
        return jsonify({'status': 'cached', 'data': TLE_CACHE})

    urls = [
        'https://celestrak.org/NORAD/elements/gp.php?GROUP=gnss&FORMAT=tle',
        'https://celestrak.com/NORAD/elements/gp.php?GROUP=active&FORMAT=tle'
    ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/plain'
    }

    for url in urls:
        try:
            res = requests.get(url, headers=headers, timeout=15)
            if res.status_code == 200 and len(res.text) > 200:
                parsed = parse_gnss_tle(res.text)
                if parsed and parsed.get('all'):
                    TLE_CACHE = parsed
                    LAST_FETCH_TIME = now
                    return jsonify({'status': 'live', 'data': TLE_CACHE})
        except Exception as e:
            print(f"URL {url} failed: {e}")

    return jsonify({'status': 'fallback', 'data': TLE_CACHE if TLE_CACHE else {'gps': [], 'bds': [], 'galileo': [], 'glonass': [], 'all': []}})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)