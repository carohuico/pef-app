import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import pandas as pd

load_dotenv()

# Prefer `st.secrets` when available (deployed Streamlit app). Support common
# alternative key names so users can set `DB_HOST`/`DB_SERVER` and `DB_PASS`/`DB_PASSWORD`.
try:
    import streamlit as _st
    _secrets = getattr(_st, "secrets", None)
except Exception:
    _secrets = None

def _secret_get(*keys, default=None):
    # Try secrets first (in order), then environment variables, then default
    if _secrets:
        for k in keys:
            if k in _secrets:
                return _secrets[k]
    for k in keys:
        val = os.getenv(k)
        if val is not None:
            return val
    return default

SERVER = _secret_get("DB_SERVER", "DB_HOST", default="localhost")
PORT = _secret_get("DB_PORT", default="1433")
DB = _secret_get("DB_NAME", default="PBLL")
DRIVER = quote_plus("ODBC Driver 17 for SQL Server")
TRUSTED = str(_secret_get("DB_TRUSTED", default="yes")).lower() in ("1", "true", "yes")
UID = _secret_get("DB_USER", "DB_USERNAME", default="")
PWD = _secret_get("DB_PASSWORD", "DB_PASS", default="")

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
