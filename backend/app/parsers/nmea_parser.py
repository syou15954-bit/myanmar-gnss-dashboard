# myanmar-gnss-dashboard/backend/app/parsers/nmea_parser.py
import pynmea2

class NMEAGNSSTracker:
    def __init__(self):
        self.reset()

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