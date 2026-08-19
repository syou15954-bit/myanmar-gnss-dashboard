import os
import time
from flask import Flask, render_template, jsonify

app = Flask(__name__, template_folder='.', static_folder='.')

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
    try:
        cache_path = os.path.join(os.path.dirname(__file__), 'tle_cache.txt')
        if os.path.exists(cache_path):
            with open(cache_path, 'r', encoding='utf-8') as f:
                tle_text = f.read()
            parsed = parse_gnss_tle(tle_text)
            if parsed and parsed.get('all'):
                return jsonify({'status': 'live', 'data': parsed})
    except Exception as e:
        print(f"Failed to read local TLE cache: {e}")

    return jsonify({'status': 'fallback', 'data': {'gps': [], 'bds': [], 'galileo': [], 'glonass': [], 'all': []}})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)