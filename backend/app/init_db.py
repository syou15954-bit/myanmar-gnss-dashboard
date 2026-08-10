import sqlite3
import os

def init_database():
    # Database file path setup
    db_path = os.path.join(os.path.dirname(__file__), "gnss_dashboard.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Ground Stations Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            altitude REAL NOT NULL,
            status TEXT DEFAULT 'ACTIVE'
        )
    ''')

    # Insert default Yangon Ground Station
    cursor.execute("SELECT COUNT(*) FROM stations")
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO stations (name, latitude, longitude, altitude, status)
            VALUES ('Yangon Ground Station', 16.8661, 96.1951, 15.0, 'ACTIVE')
        ''')

    # 2. System Logs Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            level TEXT NOT NULL,
            message TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ GNSS Database setup completed successfully.")

if __name__ == "__main__":
    init_database()