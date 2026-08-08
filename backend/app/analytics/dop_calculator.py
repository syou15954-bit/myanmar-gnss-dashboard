import numpy as np

def calculate_dop_metrics(skyplot_data):
    """
    Visible Satellites ၏ Azimuth & Elevation များမှတစ်ဆင့် Design Matrix G နှင့် Covariance Matrix Q ကို တွက်ချက်ခြင်း
    Q = (G^T * G)^(-1)
    """
    # Elevation Mask Angle (10°) ထက်ကြီးပြီး မြင်ကွင်းထဲရှိသော ဂြိုဟ်တုများကိုသာ စစ်ထုတ်ခြင်း
    visible_sats = [s for s in skyplot_data if s.get("visible", False)]
    
    # Position Fix ရရှိရန် အနည်းဆုံး ဂြိုဟ်တု (၄) လုံး လိုအပ်ပါသည်
    if len(visible_sats) < 4:
        return {
            "status": "insufficient_satellites",
            "visible_count": len(visible_sats),
            "pdop": None, "hdop": None, "vdop": None, "tdop": None, "gdop": None
        }

    G = []
    for sat in visible_sats:
        az = np.radians(sat["azimuth_deg"])
        el = np.radians(sat["elevation_deg"])
        
        # East, North, Up Directional Unit Vectors တွက်ချက်ခြင်း
        e = np.cos(el) * np.sin(az)
        n = np.cos(el) * np.cos(az)
        u = np.sin(el)
        
        # Design Matrix Row: [-e, -n, -u, 1]
        G.append([-e, -n, -u, 1.0])

    G = np.array(G)
    
    try:
        # Geometry Covariance Matrix Q တွက်ထုတ်ခြင်း
        Q = np.linalg.inv(G.T @ G)
        
        q_east, q_north, q_up, q_time = Q[0, 0], Q[1, 1], Q[2, 2], Q[3, 3]

        hdop = np.sqrt(max(0, q_east + q_north))
        vdop = np.sqrt(max(0, q_up))
        pdop = np.sqrt(max(0, q_east + q_north + q_up))
        tdop = np.sqrt(max(0, q_time))
        gdop = np.sqrt(max(0, q_east + q_north + q_up + q_time))

        return {
            "status": "success",
            "visible_count": len(visible_sats),
            "pdop": round(float(pdop), 2),
            "hdop": round(float(hdop), 2),
            "vdop": round(float(vdop), 2),
            "tdop": round(float(tdop), 2),
            "gdop": round(float(gdop), 2)
        }
    except np.linalg.LinAlgError:
        return {"status": "singular_matrix_error", "pdop": None, "hdop": None, "vdop": None}