import sqlite3
import os

# Database ဖိုင်တည်နေရာ သတ်မှတ်ခြင်း
DB_PATH = os.path.join(os.path.dirname(__file__), "gnss_dashboard.db")

def get_db_connection():
    """
    Database Connection စတင်ဖွင့်လှစ်ပေးသည့် Helper Function
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Data များကို Dictionary ပုံစံဖြင့် ဖတ်ယူရလွယ်ကူစေရန်
    return conn