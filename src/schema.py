# Database table schemas and official configuration constants

DB_NAME = "nyeri_weights_master.db"

STATIONS = [
    "NYERI TOWN", "OTHAYA", "MUKURWEINI", "TETU",
    "KIENI EAST", "KIENI WEST", "MATHIRA EAST", "MATHIRA WEST"
]

FEE_RATES = {
    "pump": 2400,
    "scale": 2000,
    "weight": 500
}

LEDGER_SCHEMA = """
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
);
"""

TRADERS_SCHEMA = """
CREATE TABLE IF NOT EXISTS traders_registry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trader_name TEXT UNIQUE,
    phone_no TEXT,
    station TEXT,
    category TEXT,
    physical_address TEXT,
    registered_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""
