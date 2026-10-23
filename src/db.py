import sqlite3
import pandas as pd

DB_FILE = "nyeri_weights_master.db"

def get_db_connection():
    return sqlite3.connect(DB_FILE, timeout=5.0)

def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ledger_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year_sheet TEXT,
                date_entry TEXT,
                serial_no TEXT,
                trader_name TEXT,
                phone_no TEXT,
                station TEXT,
                stamped_pumps INTEGER DEFAULT 0,
                stamped_scales INTEGER DEFAULT 0,
                stamped_weights INTEGER DEFAULT 0,
                total_amount REAL DEFAULT 0,
                mpesa_code TEXT,
                inspector_logged TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS traders_registry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trader_name TEXT UNIQUE,
                phone_no TEXT,
                station TEXT,
                category TEXT,
                physical_address TEXT,
                registered_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

def save_trader_to_db(name, phone, station, category, address, registered_by):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO traders_registry (trader_name, phone_no, station, category, physical_address, registered_by)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, phone, station, category, address, registered_by))
            conn.commit()
        return True, "Trader successfully registered in system!"
    except sqlite3.IntegrityError:
        return False, "A trader with this business name already exists."

def load_traders_from_db():
    with get_db_connection() as conn:
        df = pd.read_sql_query("SELECT * FROM traders_registry", conn)
    return df

def save_record_to_db(record):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ledger_entries (year_sheet, date_entry, serial_no, trader_name, phone_no, station, stamped_pumps, stamped_scales, stamped_weights, total_amount, mpesa_code, inspector_logged)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record["year_sheet"], record["date"], record["s_no"],
            record["trader"], record["phone"], record["station"],
            record["pumps"], record["scales"], record["weights"],
            record["fee"], record["code"], record["inspector"]
        ))
        conn.commit()

def load_all_db_records():
    with get_db_connection() as conn:
        df = pd.read_sql_query("SELECT * FROM ledger_entries", conn)
    return df
