import pynmea2
import sqlite3
import json

class NMEAGNSSTracker:
    def __init__(self, db_path="gnss_local.db", max_logs=5000):
        # Database ဖိုင်နာမည်နှင့် အများဆုံးသိမ်းဆည်းမည့် မှတ်တမ်းအရေအတွက် (Limit)
        self.db_path = db_path
        self.max_logs = max_logs
        self.init_db()  # Database Table တည်ဆောက်ခြင်း
        self.reset()

    def init_db(self):
        """SQLite Database နှင့် Table ကို မရှိသေးပါက အလိုအလျောက် တည်ဆောက်ပေးမည်"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gnss_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                lat REAL,
                lon REAL,
                alt REAL,
                gps_count INTEGER,
                bds_count INTEGER,
                satellites_json TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def reset(self):
        self.satellites = []
        self.gps_count = 0
        self.bds_count = 0
        self.coordinates = {"lat": None, "lon": None, "alt": None}

    def parse_nmea_sentence(self, nmea_str: str):
        """
        NMEA Text Line တစ်ကြောင်းစီကို ဖတ်ယူ၍ GPS နှင့် BDS Metrics များ ခွဲထုတ်ခြင်း
        """
        try:
            msg = pynmea2.parse(nmea_str)
            
            # ၁။ Coordinates Data (GGA Sentence)
            if msg.sentence_type in ["GGA"]:
                if msg.latitude and msg.longitude:
                    self.coordinates["lat"] = msg.latitude
                    self.coordinates["lon"] = msg.longitude
                    self.coordinates["alt"] = float(msg.altitude) if msg.altitude else 0.0

            # ၂။ Satellites in View Data (GSV Sentence)
            elif msg.sentence_type in ["GSV"]:
                # Talker ID ခွဲခြားခြင်း ($GPGSV = GPS, $BDGSV/$GBGSV = BeiDou)
                talker = msg.talker
                constellation = "BDS" if talker in ["BD", "GB"] else "GPS"

                # GSV တွင် ပါဝင်သော ဂြိုဟ်တု ၄ လုံးစီ၏ အချက်အလက်များ Extracted ထုတ်ယူခြင်း
                for i in range(1, 5):
                    prn_attr = f"sv_prn_{i}"
                    elev_attr = f"elevation_{i}"
                    az_attr = f"azimuth_{i}"
                    snr_attr = f"snr_{i}"

                    if hasattr(msg, prn_attr):
                        prn = getattr(msg, prn_attr)
                        if prn:
                            elev = float(getattr(msg, elev_attr) or 0)
                            az = float(getattr(msg, az_attr) or 0)
                            snr = float(getattr(msg, snr_attr) or 0)

                            sat_info = {
                                "prn": f"{'C' if constellation == 'BDS' else 'G'}{prn.zfill(2)}",
                                "constellation": constellation,
                                "elevation": elev,
                                "azimuth": az,
                                "snr": snr,  # Carrier-to-Noise Ratio (C/N0)
                            }
                            self.satellites.append(sat_info)

                            if constellation == "BDS":
                                self.bds_count += 1
                            else:
                                self.gps_count += 1

            return True
        except Exception:
            return False

    def get_summary(self):
        return {
            "coordinates": self.coordinates,
            "total_satellites": len(self.satellites),
            "gps_satellites_count": self.gps_count,
            "bds_satellites_count": self.bds_count,
            "satellites_detail": self.satellites
        }

    def save_to_db(self):
        """
        ထုတ်ယူထားသော Data များကို SQLite ထဲသို့ သိမ်းမည်။
        မှတ်တမ်း ၅၀၀၀ ကျော်ပါက အဟောင်းဆုံးကို အလိုအလျောက် ဖျက်မည် (FIFO)။
        """
        summary = self.get_summary()
        
        # Data လုံးဝမရှိပါက Database ထဲ မသိမ်းပါ
        if summary["coordinates"]["lat"] is None and summary["total_satellites"] == 0:
            return False

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Data အသစ်ကို ထည့်သွင်းခြင်း
        cursor.execute('''
            INSERT INTO gnss_logs (lat, lon, alt, gps_count, bds_count, satellites_json)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            summary["coordinates"]["lat"],
            summary["coordinates"]["lon"],
            summary["coordinates"]["alt"],
            summary["gps_satellites_count"],
            summary["bds_satellites_count"],
            json.dumps(summary["satellites_detail"])
        ))

        # FIFO Limit စစ်ဆေးခြင်း: max_logs (၅၀၀၀) ထက်ကျော်လွန်ပါက အဟောင်းဆုံး row များကို ဖျက်ပစ်မည်
        cursor.execute(f'''
            DELETE FROM gnss_logs 
            WHERE id NOT IN (
                SELECT id FROM gnss_logs 
                ORDER BY id DESC 
                LIMIT {self.max_logs}
            )
        ''')

        conn.commit()
        conn.close()
        
        # Save လုပ်ပြီးပါက Memory ပေါ်ရှိ data များကို ရှင်းလင်းမည်
        self.reset() 
        return True