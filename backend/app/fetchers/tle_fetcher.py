import requests

# အင်တာနက် သို့မဟုတ် CelesTrak မရပါက အလိုအလျောက် သုံးမည့် Fallback TLE Data
FALLBACK_GPS_TLE = [
    {
        "name": "GPS BIIR-2 (PRN 13)",
        "tle_line1": "1 24876U 97035A   26219.17999263 -.00000079  00000+0  00000+0 0  9999",
        "tle_line2": "2 24876  55.1029 322.8419 0170720 317.6040  58.3926  2.00558031159457"
    },
    {
        "name": "GPS BIIRM-1 (PRN 17)",
        "tle_line1": "1 28874U 05038A   26219.64219750  .00000028  00000+0  00000+0 0  9997",
        "tle_line2": "2 28874  54.8382 271.0974 0128509 296.7420  18.1122  2.00562049152861"
    },
    {
        "name": "GPS IIF-1 (PRN 25)",
        "tle_line1": "1 36585U 10022A   26219.00324755  .00000094  00000+0  00000+0 0  9999",
        "tle_line2": "2 36585  54.2667 206.5157 0127384  66.2189  71.0988  2.00564804118611"
    }
]

def get_live_tle_data(constellation: str = "gps"):
    url = f"https://celestrak.org/NORAD/elements/gp.php?GROUP={constellation}&FORMAT=tle"
    try:
        # Timeout ကို 3 စက္ကန့်သတ်မှတ်ထားသဖြင့် လိုင်းနှေးလျှင်လည်း ကြန့်ကြာမည်မဟုတ်ပါ
        response = requests.get(url, timeout=3)
        response.raise_for_status()
        lines = response.text.strip().split('\n')
        satellites = []
        for i in range(0, len(lines), 3):
            if i + 2 < len(lines):
                satellites.append({
                    "name": lines[i].strip(),
                    "tle_line1": lines[i+1].strip(),
                    "tle_line2": lines[i+2].strip()
                })
        if satellites:
            return {"status": "success", "count": len(satellites), "data": satellites}
    except Exception as e:
        print(f"CelesTrak Fetch Warning: {e}. Using fallback data.")

    # အင်တာနက် မရပါက Fallback Data ဖြင့် တိုက်ရိုက် တုံ့ပြန်ပေးခြင်း
    return {"status": "success", "count": len(FALLBACK_GPS_TLE), "data": FALLBACK_GPS_TLE}