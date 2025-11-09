import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import pandas as pd

load_dotenv()

SERVER = os.getenv("DB_SERVER", "localhost")
PORT = os.getenv("DB_PORT", "1433")
DB = os.getenv("DB_NAME", "PBLL")
DRIVER = quote_plus("ODBC Driver 17 for SQL Server")
TRUSTED = os.getenv("DB_TRUSTED", "yes").lower() in ("1", "true", "yes")
UID = os.getenv("DB_USER", "")
PWD = os.getenv("DB_PASSWORD", "")

_engine = None

def _conn_str():
    if TRUSTED:
        return f"mssql+pyodbc://@{SERVER},{PORT}/{DB}?driver={DRIVER}&trusted_connection=yes"
    else:
        return f"mssql+pyodbc://{quote_plus(UID)}:{quote_plus(PWD)}@{SERVER},{PORT}/{DB}?driver={DRIVER}"

def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(_conn_str(), pool_pre_ping=True, future=True)
    return _engine


def fetch_df(sql: str, params: dict | None = None):
    """
    Ejecuta una consulta SQL (string puro) y devuelve un DataFrame.
    Compatible con SQLAlchemy 2.x y pandas 2.x
    """
    engine = get_engine()
    try:
        # Use a transaction block so INSERT/UPDATE/DELETE are committed.
        with engine.begin() as conn:
            result = conn.execute(text(sql), params or {})
            # If the statement returns rows (SELECT), build a DataFrame.
            if getattr(result, 'returns_rows', False):
                try:
                    rows = result.mappings().all()
                    df = pd.DataFrame(rows)
                except Exception:
                    rows = result.fetchall()
                    df = pd.DataFrame(rows, columns=result.keys())
                return df
            else:
                # DML statement executed (no rows to return). Return empty DataFrame.
                return pd.DataFrame()
    except Exception as e:
        print("Error al ejecutar consulta:", e)
        raise
