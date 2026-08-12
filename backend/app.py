import os
import time
import requests
from flask import Flask, render_template, jsonify

app = Flask(__name__, template_folder='.', static_folder='.')

# CelesTrak TLE Cache Config (Cache for 4 Hours)
TLE_CACHE = {}
LAST_FETCH_TIME = 0
CACHE_DURATION = 14400 

CELESTRAK_URLS = {
    'gps': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=gps-ops&FORMAT=tle',
    'bds': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=beidou&FORMAT=tle',
    'galileo': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=galileo&FORMAT=tle',
    'glonass': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=glo-ops&FORMAT=tle'
}

def parse_tle_raw(tle_text):
    sats = []
    lines = [line.strip() for line in tle_text.strip().split('\n') if line.strip()]
    
    i = 0
    while i < len(lines):
        if i + 2 < len(lines) and lines[i+1].startswith('1 ') and lines[i+2].startswith('2 '):
            sat_name = lines[i]
            line1 = lines[i+1]
            line2 = lines[i+2]
            norad_id = line1[2:7].strip()
            sats.append({
                'id': norad_id,
                'name': sat_name,
                'line1': line1,
                'line2': line2
            })
            i += 3
        elif lines[i].startswith('1 ') and i + 1 < len(lines) and lines[i+1].startswith('2 '):
            line1 = lines[i]
            line2 = lines[i+1]
            norad_id = line1[2:7].strip()
            sats.append({
                'id': norad_id,
                'name': f"SAT-{norad_id}",
                'line1': line1,
                'line2': line2
            })
            i += 2
        else:
            i += 1
    return sats

@app.route('/')
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/tle')
def get_live_tles():
    global TLE_CACHE, LAST_FETCH_TIME
    now = time.time()

    # Return cached TLEs if fetched within 4 hours
    if TLE_CACHE and (now - LAST_FETCH_TIME < CACHE_DURATION):
        return jsonify({'status': 'cached', 'data': TLE_CACHE})

    fetched_data = {}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    for const, url in CELESTRAK_URLS.items():
        try:
            res = requests.get(url, headers=headers, timeout=8)
            if res.status_code == 200:
                parsed = parse_tle_raw(res.text)
                fetched_data[const] = parsed
        except Exception as e:
            print(f"Failed to fetch {const} TLE: {e}")

    if fetched_data:
        TLE_CACHE = fetched_data
        LAST_FETCH_TIME = now
        return jsonify({'status': 'live', 'data': TLE_CACHE})
    
    return jsonify({'status': 'fallback', 'data': TLE_CACHE})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)