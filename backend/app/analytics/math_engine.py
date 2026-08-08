# myanmar-gnss-dashboard/backend/app/analytics/math_engine.py
import numpy as np

class GNSSMathEngine:
    """
    GNSS Coordinates Transformation, DOP Matrix နှင့် Positioning Error
    တွက်ချက်ပေးသော Geodetic Math Module
    """
    # WGS84 / CGCS2000 Ellipsoid Constants
    A_SEMAJOR = 6378137.0  # Semi-major axis (meters)
    FLATTENING = 1 / 298.257223563
    E_SQ = 2 * FLATTENING - FLATTENING ** 2  # First eccentricity squared

    @classmethod
    def llh_to_ecef(cls, lat_deg: float, lon_deg: float, alt_m: float):
        """
        Latitude, Longitude, Altitude (WGS84/CGCS2000) မှ ECEF (X, Y, Z) သို့ ပြောင်းလဲခြင်း
        """
        phi = np.radians(lat_deg)
        lam = np.radians(lon_deg)
        
        # Prime vertical radius of curvature
        N = cls.A_SEMAJOR / np.sqrt(1 - cls.E_SQ * (np.sin(phi) ** 2))
        
        x = (N + alt_m) * np.cos(phi) * np.cos(lam)
        y = (N + alt_m) * np.cos(phi) * np.sin(lam)
        z = (N * (1 - cls.E_SQ) + alt_m) * np.sin(phi)
        
        return x, y, z

    @classmethod
    def ecef_to_enu(cls, x: float, y: float, z: float, ref_lat: float, ref_lon: float, ref_alt: float):
        """
        ECEF Coordinates မှ Benchmark Ground Truth Reference ကို အခြေခံ၍ Local ENU Vector သို့ ပြောင်းလဲခြင်း
        """
        x0, y0, z0 = cls.llh_to_ecef(ref_lat, ref_lon, ref_alt)
        dx, dy, dz = x - x0, y - y0, z - z0
        
        phi = np.radians(ref_lat)
        lam = np.radians(ref_lon)
        
        # Rotation Matrix Transformation
        e = -np.sin(lam) * dx + np.cos(lam) * dy
        n = -np.sin(phi) * np.cos(lam) * dx - np.sin(phi) * np.sin(lam) * dy + np.cos(phi) * dz
        u = np.cos(phi) * np.cos(lam) * dx + np.cos(phi) * np.sin(lam) * dy + np.sin(phi) * dz
        
        return e, n, u

    @classmethod
    def calculate_dop(cls, satellites_az_el: list, mask_angle: float = 15.0):
        """
        Azimuth နှင့် Elevation Angles များကို သုံး၍ Direction Cosine Matrix A မှတစ်ဆင့်
        HDOP, VDOP, PDOP များ တွက်ထုတ်ခြင်း
        """
        rows = []
        for sat in satellites_az_el:
            az = sat.get("azimuth", 0.0)
            el = sat.get("elevation", 0.0)
            
            # Elevation Mask Constraint Filter (15 deg အောက် ပယ်ထုတ်ခြင်း)
            if el < mask_angle:
                continue
                
            az_rad = np.radians(az)
            el_rad = np.radians(el)
            
            # Direction Cosine Row Vector
            row = [
                -np.cos(el_rad) * np.sin(az_rad),  # East component
                -np.cos(el_rad) * np.cos(az_rad),  # North component
                -np.sin(el_rad),                    # Up component
                1.0                                 # Clock bias component
            ]
            rows.append(row)

        if len(rows) < 4:
            # ဂြိုဟ်တု ၄ လုံးအောက် လျော့နည်းပါက Geometry Matrix မတွက်နိုင်ပါ
            return {"hdop": None, "vdop": None, "pdop": None, "valid_satellites": len(rows)}

        A = np.array(rows)
        try:
            # Q = (A^T * A)^-1 Covariance Matrix
            Q = np.linalg.inv(A.T @ A)
            
            hdop = float(np.sqrt(Q[0, 0] + Q[1, 1]))
            vdop = float(np.sqrt(Q[2, 2]))
            pdop = float(np.sqrt(Q[0, 0] + Q[1, 1] + Q[2, 2]))
            
            return {
                "hdop": round(hdop, 3),
                "vdop": round(vdop, 3),
                "pdop": round(pdop, 3),
                "valid_satellites": len(rows)
            }
        except np.linalg.LinAlgError:
            return {"hdop": None, "vdop": None, "pdop": None, "valid_satellites": len(rows)}

    @classmethod
    def calculate_position_error(cls, measured_llh: dict, benchmark_llh: dict):
        """
        2D/3D RMS Positioning Errors တွက်ထုတ်ခြင်း
        """
        x, y, z = cls.llh_to_ecef(measured_llh["lat"], measured_llh["lon"], measured_llh["alt"])
        e, n, u = cls.ecef_to_enu(
            x, y, z, 
            benchmark_llh["lat"], benchmark_llh["lon"], benchmark_llh["alt"]
        )
        
        rms_2d = float(np.sqrt(e**2 + n**2))
        rms_3d = float(np.sqrt(e**2 + n**2 + u**2))
        
        return {
            "east_error_m": round(e, 3),
            "north_error_m": round(n, 3),
            "up_error_m": round(u, 3),
            "rms_2d_m": round(rms_2d, 3),
            "rms_3d_m": round(rms_3d, 3)
        }