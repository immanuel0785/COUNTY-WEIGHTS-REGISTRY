import pandas as pd
from src.db import get_db_connection

def execute_annual_rollover(source_sheet: str, target_year: str, officer_name: str):
    """Rolls over registered traders into a new target year sheet with PENDING status."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT trader_name, phone_no, station FROM traders_registry")
        traders = cursor.fetchall()
        
        for trader, phone, station in traders:
            cursor.execute("""
                INSERT INTO ledger_entries (year_sheet, date_entry, serial_no, trader_name, phone_no, station, stamped_pumps, stamped_scales, stamped_weights, total_amount, mpesa_code, inspector_logged)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (target_year, "PENDING", "PENDING", trader, phone, station, 0, 0, 0, 0.0, "", officer_name))
        conn.commit()
    return True, f"Successfully rolled over traders into sheet '{target_year}'!"
