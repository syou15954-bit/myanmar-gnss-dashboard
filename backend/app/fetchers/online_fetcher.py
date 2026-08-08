# myanmar-gnss-dashboard/backend/app/fetchers/online_fetcher.py
import os
import gzip
import shutil
import requests
from datetime import datetime, timezone, timedelta

class OnlineEphemerisFetcher:
    """
    IGS / BKG Repository မှ Daily Multi-GNSS Broadcast Navigation File (GPS + BDS)
    များကို Auto-fetch ပြုလုပ်ပြီး ဖိုင်မရှိပါက ယမန်နေ့ဖိုင်သို့ Auto-Fallback လုပ်ပေးသော Module
    """
    def __init__(self, storage_dir: str = "./app/data/ephemeris"):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)
        self.base_url = "https://igs.bkg.bund.de/root_ftp/IGS/BRDC/"

    def fetch_today_ephemeris(self, max_fallback_days: int = 3):
        now = datetime.now(timezone.utc)
        
        # ယနေ့ ဖိုင်မရှိပါက လွန်ခဲ့သော ရက်များ သို့ နောက်ပြန်ဆွဲမည့် Logic
        for offset in range(max_fallback_days):
            target_date = now - timedelta(days=offset)
            year = target_date.strftime("%Y")
            doy = target_date.strftime("%j")  # Day of Year (001-366)
            
            file_name = f"BRDC00IGS_R_{year}{doy}0000_01D_MN.rnx.gz"
            file_url = f"{self.base_url}{year}/{doy}/{file_name}"
            
            gz_path = os.path.join(self.storage_dir, file_name)
            rnx_path = gz_path.replace(".gz", "")

            # ဖိုင် ရှိပြီးသားဖြစ်ပါက ပြန်မဆွဲပါ
            if os.path.exists(rnx_path):
                return {
                    "status": "ALREADY_EXISTS",
                    "file_path": rnx_path,
                    "file_name": os.path.basename(rnx_path),
                    "day_offset": offset,
                    "doy": doy
                }

            try:
                response = requests.get(file_url, stream=True, timeout=15)
                if response.status_code == 200:
                    with open(gz_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    # GZ Compressed File အား ဖြည်ချခြင်း
                    with gzip.open(gz_path, "rb") as f_in:
                        with open(rnx_path, "wb") as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    
                    os.remove(gz_path)
                    return {
                        "status": "DOWNLOAD_SUCCESS",
                        "file_path": rnx_path,
                        "file_name": os.path.basename(rnx_path),
                        "day_offset": offset,
                        "doy": doy
                    }
            except Exception:
                continue

        return {
            "status": "FAILED",
            "http_code": 404,
            "message": f"Ephemeris file not found for the last {max_fallback_days} days on IGS server."
        }