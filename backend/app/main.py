import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

# Modules Import များကို ဖိုင်ထိပ်ဆုံးတွင် စုစည်းထားခြင်း
from app.fetchers.tle_fetcher import get_live_tle_data
from app.analytics.skyplot import calculate_skyplot_data
from app.analytics.dop_calculator import calculate_dop_metrics
from app.parsers.rinex_parser import parse_rinex_bytes
from app.analytics.gnss_compare import analyze_gps_vs_bds

app = FastAPI(title="Myanmar GNSS Dashboard API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dashboard UI ကို /dashboard သို့မဟုတ် / လမ်းကြောင်းမှ တိုက်ရိုက် ပြသပေးခြင်း
@app.get("/dashboard", response_class=HTMLResponse)
@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    html_path = os.path.join(os.path.dirname(__file__), "..", "dashboard.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>dashboard.html file not found!</h1>"

# Dashboard Summary Data API
@app.get("/api/v1/dashboard/summary")
def get_dashboard_summary():
    return {
        "fleet_status": {"total": 31, "active": 28, "degraded": 2, "inactive": 1},
        "global_coverage": {"coverage_percent": 98.7, "avg_pdop": 1.8},
        "alerts": [
            {"severity": "CRITICAL", "message": "SVN-45 Oscillator Anomaly"},
            {"severity": "WARNING", "message": "PDOP Spike over Pacific"},
            {"severity": "INFO", "message": "GNSS-OD Software Updated"}
        ]
    }

# Dashboard Telemetry & Performance API
@app.get("/api/v1/dashboard/telemetry")
def get_telemetry_metrics():
    return {
        "selected_sat": "SVN-62 / PRN-07",
        "fuel_level": 85,
        "power_kw": 2.1,
        "temp_c": -2,
        "clock_error": [0.01, -0.02, 0.03, -0.01, 0.02, 0.00, -0.01],
        "pdop_history": [2.1, 1.9, 1.8, 3.5, 1.8, 1.7, 2.0]
    }

# GPS နှင့် BDS Live Orbit Data တောင်းယူမည့် API
@app.get("/api/v1/gnss/live-orbit")
def fetch_satellite_orbits(system: str = "gps"):
    group = "beidou" if system.lower() == "bds" else "gps-ops"
    return get_live_tle_data(constellation=group)

# Yangon Ground Station မှ Sky Plot (Azimuth / Elevation) တောင်းယူမည့် API
@app.get("/api/v1/gnss/skyplot")
def get_skyplot_api(system: str = "gps", mask_angle: float = 10.0):
    group = "beidou" if system.lower() == "bds" else "gps-ops"
    tle_res = get_live_tle_data(constellation=group)
    
    if tle_res["status"] != "success":
        return {"status": "error", "message": "Failed to fetch TLE data"}

    skyplot_data = calculate_skyplot_data(tle_res["data"], mask_angle=mask_angle)
    visible_count = sum(1 for s in skyplot_data if s["visible"])

    return {
        "status": "success",
        "station": "Yangon Ground Station",
        "constellation": system.upper(),
        "total_satellites": len(skyplot_data),
        "visible_satellites": visible_count,
        "mask_angle_deg": mask_angle,
        "data": skyplot_data
    }

# DOP Metrics (PDOP, HDOP, VDOP) API Endpoint
@app.get("/api/v1/gnss/dop")
def get_dop_metrics_api(system: str = "gps", mask_angle: float = 10.0):
    group = "beidou" if system.lower() == "bds" else "gps-ops"
    tle_res = get_live_tle_data(constellation=group)
    
    if tle_res["status"] != "success":
        return {"status": "error", "message": "Failed to fetch TLE data"}

    skyplot_data = calculate_skyplot_data(tle_res["data"], mask_angle=mask_angle)
    dop_results = calculate_dop_metrics(skyplot_data)
    
    return {
        "status": "success",
        "station": "Yangon Ground Station",
        "constellation": system.upper(),
        "dop_analysis": dop_results
    }

# RINEX File မှ GPS (G) နှင့် BDS (C) နှိုင်းယှဉ်ချက် Data ထုတ်ပေးမည့် API Endpoint
@app.post("/api/v1/gnss/gps-vs-bds")
async def compare_gps_bds_endpoint(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        # 1. RINEX File Bytes ကို Read ပြုလုပ်ခြင်း
        df = parse_rinex_bytes(contents, file.filename)
        
        # 2. GPS (G) နှင့် BDS (C) Analytics တွက်ချက်ခြင်း
        results = analyze_gps_vs_bds(df)
        
        if "error" in results:
            return {"status": "error", "message": results["error"]}
            
        return {
            "status": "success",
            "filename": file.filename,
            "analytics": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data Processing Error: {str(e)}")