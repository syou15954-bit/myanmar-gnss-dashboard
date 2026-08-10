import georinex as gr
import pandas as pd
import tempfile
import os

def parse_rinex_bytes(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """
    RINEX File Bytes ကို ယာယီ File အဖြစ် သိမ်းပြီး DataFrame ပြောင်းပေးသည်။
    """
    ext = os.path.splitext(filename)[1] or '.rnx'
    
    # Temp File ဖန်တီး၍ georinex ဖြင့် Read ခြင်း
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        obs = gr.load(tmp_path)
        df = obs.to_dataframe().reset_index()
        
        # SV Column ကို String ပြောင်းပြီး System ('G' သို့မဟုတ် 'C') ခွဲထုတ်ခြင်း
        df['sv'] = df['sv'].astype(str)
        df['system'] = df['sv'].str[0]
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return df