from sgp4.api import Satrec, jday
from datetime import datetime, timezone
import numpy as np

def propagate_tle_to_latlon(tle_line1: str, tle_line2: str):
    """
    TLE Line 1 & 2 ကို အသုံးပြု၍ လက်ရှိအချိန်၌ ဂြိုဟ်တုရောက်ရှိနေသော Lat, Lng, Alt ကို တွက်ထုတ်ခြင်း
    """
    satellite = Satrec.twoline2rv(tle_line1, tle_line2)
    now = datetime.now(timezone.utc)
    jd, fr = jday(now.year, now.month, now.day, now.hour, now.minute, now.second + now.microsecond / 1e6)
    
    e, r, v = satellite.sgp4(jd, fr)
    if e != 0:
        return None  # Propagation error

    # ECI Position (x, y, z in km) မှ Latitude, Longitude, Altitude သို့ ပြောင်းလဲခြင်း
    x, y, z = r[0], r[1], r[2]
    dist = np.sqrt(x**2 + y**2 + z**2)
    lat = np.degrees(np.arcsin(z / dist))
    lng = np.degrees(np.arctan2(y, x))
    alt = dist - 6371.0  # Earth Radius approx 6371 km

    return {"latitude": round(lat, 4), "longitude": round(lng, 4), "altitude_km": round(alt, 2)}