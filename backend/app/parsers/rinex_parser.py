import pandas as pd

def parse_rinex_bytes(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """
    Pure Python RINEX 3 Observation Parser (No C-libraries required)
    """
    content = file_bytes.decode('utf-8', errors='ignore')
    lines = content.splitlines()
    
    records = []
    current_epoch = None
    in_header = True

    for line in lines:
        if in_header:
            if "END OF HEADER" in line:
                in_header = False
            continue

        line_str = line.strip()
        if not line_str:
            continue

        # RINEX 3 Epoch Header Line starts with '>'
        if line_str.startswith('>'):
            parts = line_str.split()
            if len(parts) >= 7:
                try:
                    year, month, day = parts[1], parts[2].zfill(2), parts[3].zfill(2)
                    hour, minute = parts[4].zfill(2), parts[5].zfill(2)
                    sec = str(int(float(parts[6]))).zfill(2)
                    current_epoch = f"{year}-{month}-{day} {hour}:{minute}:{sec}"
                except Exception:
                    current_epoch = None
            continue

        # Satellite observation line (e.g., G01, C02, E05...)
        if current_epoch and len(line_str) >= 3:
            sv_id = line_str[:3].strip()
            system = sv_id[0] if len(sv_id) > 0 else ''
            
            if system in ['G', 'C', 'E', 'R']:
                records.append({
                    'time': current_epoch,
                    'sv': sv_id,
                    'system': system
                })

    if not records:
        return pd.DataFrame(columns=['time', 'sv', 'system'])

    return pd.DataFrame(records)