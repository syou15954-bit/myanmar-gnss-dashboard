import numpy as np
from datetime import datetime, timezone
from sgp4.api import Satrec, jday

# Yangon Ground Station Coordinates (Default)
YANGON_LAT = 16.8661
YANGON_LON = 96.1951
YANGON_ALT = 20.0  # Meters above sea level

def _gmst_rad(jd, fr):
    """Greenwich Mean Sidereal Time (GMST) ကို Radians ဖြင့် တွက်ထုတ်ခြင်း"""
    ut = (jd + fr - 2451545.0) / 36525.0
    gmst_sec = 24110.54841 + 8640184.812866 * ut + 0.093104 * (ut**2) - 6.2e-6 * (ut**3)
    gmst_sec += ((fr + 0.5) % 1.0) * 86400.0 * 1.00273790935
    return (gmst_sec % 86400.0) * (2 * np.pi / 86400.0)

def _lla_to_ecef(lat_deg, lon_deg, alt_m):
    """Lat/Lon/Alt ကို ECEF Cartesian Coordinates (X, Y, Z) သို့ ပြောင်းလဲခြင်း"""
    a = 6378137.0
    f = 1 / 298.257223563
    e2 = 2*f - f**2

    phi, lam = np.radians(lat_deg), np.radians(lon_deg)
    N = a / np.sqrt(1 - e2 * np.sin(phi)**2)

    x = (N + alt_m) * np.cos(phi) * np.cos(lam)
    y = (N + alt_m) * np.cos(phi) * np.sin(lam)
    z = (N * (1 - e2) + alt_m) * np.sin(phi)
    return np.array([x, y, z])

def _ecef_to_enu(r_ecef_m, obs_lat_deg, obs_lon_deg, obs_ecef_m):
    """ECEF တည်နေရာကို Observer Tangent Plane (East, North, Up) သို့ ပြောင်းလဲခြင်း"""
    d_ecef = r_ecef_m - obs_ecef_m
    phi, lam = np.radians(obs_lat_deg), np.radians(obs_lon_deg)

    R = np.array([
        [-np.sin(lam),              np.cos(lam),             0],
        [-np.sin(phi)*np.cos(lam), -np.sin(phi)*np.sin(lam), np.cos(phi)],
        [ np.cos(phi)*np.cos(lam),  np.cos(phi)*np.sin(lam), np.sin(phi)]
    ])
    return R.dot(d_ecef)

def calculate_skyplot_data(satellite_tle_list, obs_lat=YANGON_LAT, obs_lon=YANGON_LON, obs_alt=YANGON_ALT, mask_angle=10.0):
    """
    TLE List အပေါ် အခြေခံ၍ Yangon Station မှ မြင်တွေ့ရမည့် Azimuth နှင့် Elevation ကို တွက်ပေးသည့် Function
    """
    now = datetime.now(timezone.utc)
    jd, fr = jday(now.year, now.month, now.day, now.hour, now.minute, now.second + now.microsecond / 1e6)
    gmst = _gmst_rad(jd, fr)
    obs_ecef = _lla_to_ecef(obs_lat, obs_lon, obs_alt)

    skyplot_results = []

    for sat in satellite_tle_list:
        try:
            satellite = Satrec.twoline2rv(sat['tle_line1'], sat['tle_line2'])
            e, r_eci, _ = satellite.sgp4(jd, fr)

            if e != 0:
                continue

            # ECI Position -> ECEF Position (in meters)
            x_eci, y_eci, z_eci = r_eci
            x_ecef = (x_eci * np.cos(gmst) + y_eci * np.sin(gmst)) * 1000.0
            y_ecef = (-x_eci * np.sin(gmst) + y_eci * np.cos(gmst)) * 1000.0
            z_ecef = z_eci * 1000.0
            r_ecef_m = np.array([x_ecef, y_ecef, z_ecef])

            # ENU Vector & Azimuth/Elevation
            E, N, U = _ecef_to_enu(r_ecef_m, obs_lat, obs_lon, obs_ecef)
            horizon_dist = np.sqrt(E**2 + N**2)

            azimuth = float(np.degrees(np.arctan2(E, N)) % 360.0)
            elevation = float(np.degrees(np.arctan2(U, horizon_dist)))

            # Sub-point (Lat/Lon) တွက်ချက်ခြင်း
            dist_km = np.sqrt(x_eci**2 + y_eci**2 + z_eci**2)
            sat_lat = float(np.degrees(np.arcsin(z_eci / dist_km)))
            sat_lon = float(np.degrees(np.arctan2(y_ecef, x_ecef)))

            skyplot_results.append({
                "name": sat['name'],
                "azimuth_deg": round(azimuth, 2),
                "elevation_deg": round(elevation, 2),
                "visible": elevation >= mask_angle,  # Mask Angle (10°) ထက်မြင့်မှ မြင်ကွင်းထဲတွင် ရှိမည်
                "sat_lat": round(sat_lat, 4),
                "sat_lon": round(sat_lon, 4)
            })
        except Exception:
            continue

    return skyplot_results