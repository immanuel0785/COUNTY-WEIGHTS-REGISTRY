import pandas as pd
from src.db import get_db_connection

def fetch_audit_logs():
    """Retrieves all transaction logs for executive auditing."""
    with get_db_connection() as conn:
        df = pd.read_sql_query("SELECT * FROM ledger_entries ORDER BY created_at DESC", conn)
    return df
