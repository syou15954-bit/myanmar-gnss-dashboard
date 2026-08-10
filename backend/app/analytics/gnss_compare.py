import pandas as pd

def analyze_gps_vs_bds(df: pd.DataFrame) -> dict:
    """
    GPS (G) နှင့် BeiDou (C) တို့၏ Satellite Visibility နဲ့ SNR Data များကို Matrix ထုတ်ပေးသည်။
    """
    # GPS နှင့် BDS သာ သီးခြား Filter လုပ်ခြင်း
    df_gnss = df[df['system'].isin(['G', 'C'])].copy()
    
    if df_gnss.empty:
        return {"error": "RINEX File ထဲတွင် GPS သို့မဟုတ် BeiDou Data မတွေ့ရှိပါ။"}

    # Time Format ညှိခြင်း
    df_gnss['time_str'] = pd.to_datetime(df_gnss['time']).dt.strftime('%Y-%m-%d %H:%M:%S')

    # 1. Satellite Count over Time
    sat_counts = (
        df_gnss.groupby(['time_str', 'system'])['sv']
        .nunique()
        .unstack(fill_value=0)
        .reset_index()
    )
    
    if 'G' not in sat_counts.columns: sat_counts['G'] = 0
    if 'C' not in sat_counts.columns: sat_counts['C'] = 0

    timestamps = sat_counts['time_str'].tolist()
    gps_counts = sat_counts['G'].tolist()
    bds_counts = sat_counts['C'].tolist()

    # Average Metrics
    avg_gps = round(sum(gps_counts) / len(gps_counts), 2) if gps_counts else 0
    avg_bds = round(sum(bds_counts) / len(bds_counts), 2) if bds_counts else 0

    # 2. Average SNR Calculation
    snr_cols = [c for c in df_gnss.columns if c.startswith('S') and len(c) <= 4]
    snr_summary = {}

    if snr_cols:
        main_snr = snr_cols[0] # ဥပမာ- S1C သို့မဟုတ် S1I
        snr_df = df_gnss.dropna(subset=[main_snr])
        
        snr_time = (
            snr_df.groupby(['time_str', 'system'])[main_snr]
            .mean()
            .unstack(fill_value=0)
            .reset_index()
        )
        
        snr_summary = {
            "signal_code": main_snr,
            "gps_snr": snr_time['G'].round(2).tolist() if 'G' in snr_time.columns else [],
            "bds_snr": snr_time['C'].round(2).tolist() if 'C' in snr_time.columns else []
        }

    return {
        "timestamps": timestamps,
        "sat_count": {
            "gps": gps_counts,
            "bds": bds_counts,
            "avg_gps": avg_gps,
            "avg_bds": avg_bds
        },
        "snr": snr_summary
    }