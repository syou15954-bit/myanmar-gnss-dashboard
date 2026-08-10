import pandas as pd

def analyze_gps_vs_bds(df: pd.DataFrame) -> dict:
    df_gnss = df[df['system'].isin(['G', 'C'])].copy()
    
    if df_gnss.empty:
        return {"error": "RINEX File ထဲတွင် GPS (G) သို့မဟုတ် BeiDou (C) Data မတွေ့ရှိပါ။"}

    df_gnss['time_str'] = df_gnss['time']

    sat_counts = (
        df_gnss.groupby(['time_str', 'system'])['sv']
        .nunique()
        .unstack(fill_value=0)
        .reset_index()
    )
    
    if 'G' not in sat_counts.columns: sat_counts['G'] = 0
    if 'C' not in sat_counts.columns: sat_counts['C'] = 0

    timestamps = sat_counts['time_str'].tolist()
    gps_counts = [int(x) for x in sat_counts['G'].tolist()]
    bds_counts = [int(x) for x in sat_counts['C'].tolist()]

    avg_gps = round(sum(gps_counts) / len(gps_counts), 2) if gps_counts else 0
    avg_bds = round(sum(bds_counts) / len(bds_counts), 2) if bds_counts else 0

    return {
        "timestamps": timestamps,
        "sat_count": {
            "gps": gps_counts,
            "bds": bds_counts,
            "avg_gps": avg_gps,
            "avg_bds": avg_bds
        }
    }