import sqlite3
import datetime

DB_NAME = 'zhihu_app.db'

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS stats (
                date TEXT PRIMARY KEY,
                daily_visitors INTEGER DEFAULT 0,
                total_visitors INTEGER DEFAULT 0,
                total_downloads INTEGER DEFAULT 0
            )
        ''')
        # We need a singleton row for total stats that persists across dates? 
        # Actually structure:
        # date | daily_visitors | daily_downloads
        # And a separate config/global table for grand totals?
        # Let's keep it simple:
        # 'GLOBAL_STATS' as a key in config? No, explicit table is better.
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        # Initialize 'total_visitors' in config if not exists
        conn.execute("INSERT OR IGNORE INTO config (key, value) VALUES ('total_visitors', '0')")
        conn.execute("INSERT OR IGNORE INTO config (key, value) VALUES ('total_downloads', '0')")
        conn.commit()

def get_stats():
    today = datetime.date.today().isoformat()
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM stats WHERE date = ?", (today,))
        row = cursor.fetchone()
        
        daily_visitors = row['daily_visitors'] if row else 0
        
        # Get totals
        cursor = conn.execute("SELECT value FROM config WHERE key = 'total_visitors'")
        total_visitors = int(cursor.fetchone()['value'])
        
        cursor = conn.execute("SELECT value FROM config WHERE key = 'total_downloads'")
        total_downloads = int(cursor.fetchone()['value'])
        
        return {
            'daily_visitors': daily_visitors,
            'total_visitors': total_visitors,
            'total_downloads': total_downloads
        }

def increment_stats(visit=False, download=False):
    today = datetime.date.today().isoformat()
    with get_db() as conn:
        # Upsert today's stats
        conn.execute('''
            INSERT INTO stats (date, daily_visitors, total_visitors, total_downloads) 
            VALUES (?, 0, 0, 0)
            ON CONFLICT(date) DO NOTHING
        ''', (today,))
        
        visitor_num = 0
        if visit:
            conn.execute("UPDATE stats SET daily_visitors = daily_visitors + 1 WHERE date = ?", (today,))
            conn.execute("UPDATE config SET value = CAST(value AS INTEGER) + 1 WHERE key = 'total_visitors'")
            
            # Get the visitor number for today to show "Welcome Nth partner"
            cursor = conn.execute("SELECT daily_visitors FROM stats WHERE date = ?", (today,))
            visitor_num = cursor.fetchone()[0]
            
        if download:
            conn.execute("UPDATE stats SET total_downloads = total_downloads + 1 WHERE date = ?", (today,)) # reusing column? rename?
            # Actually I defined total_downloads in schema as day specific? 
            # Let's fix schema usage logic.
            # daily_downloads is missing in schema, I reused total_downloads which is confusing.
            # Let's just update global download count in config.
            conn.execute("UPDATE config SET value = CAST(value AS INTEGER) + 1 WHERE key = 'total_downloads'")
            
        conn.commit()
        
        return {
            'visitor_number': visitor_num
        }

def get_config(key):
    with get_db() as conn:
        cursor = conn.execute("SELECT value FROM config WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row['value'] if row else None

def set_config(key, value):
    with get_db() as conn:
        conn.execute("INSERT INTO config (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = ?", (key, value, value))
        conn.commit()
