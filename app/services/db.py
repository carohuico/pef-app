import streamlit as st
import pandas as pd
import pymssql
import os
import queue
import threading
import time
from typing import Optional

# Lightweight connection pool to reduce latency when opening many DB connections.
# Pool size is configurable via st.secrets['DB_POOL_SIZE'] or env DB_POOL_SIZE.
_POOL: Optional[queue.Queue] = None
_POOL_LOCK = threading.Lock()


def _get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    try:
        if hasattr(st, "secrets"):
            val = st.secrets.get(key)
            if val:
                return val
    except Exception:
        pass
    return os.environ.get(key, default)


def _make_connection():
    server = _get_secret("DB_HOST") or "34.55.82.47"
    port = int(_get_secret("DB_PORT") or os.environ.get("DB_PORT") or 1433)
    user = _get_secret("DB_USER") or "streamlit_user"
    password = _get_secret("DB_PASS") or "pbll_pwd"
    database = _get_secret("DB_NAME") or "PBLL"

    return pymssql.connect(
        server=server,
        port=port,
        user=user,
        password=password,
        database=database,
        login_timeout=10,
        timeout=30,
    )


def get_connection():
    """Backwards-compatible: crea una conexión nueva.

    Preferir `borrow_connection()` para reusar conexiones del pool.
    """
    return _make_connection()


def init_pool(size: int = None):
    """Inicializa el pool global (idempotente)."""
    global _POOL
    with _POOL_LOCK:
        if _POOL is not None:
            return
        try:
            cfg_size = None
            try:
                cfg_size = int(_get_secret("DB_POOL_SIZE") or os.environ.get("DB_POOL_SIZE"))
            except Exception:
                cfg_size = None
            pool_size = size or cfg_size or 5
            q = queue.Queue(maxsize=pool_size)
            # pre-populate one connection to reduce cold-start latency
            try:
                q.put(_make_connection(), block=False)
            except Exception:
                pass
            _POOL = q
        except Exception:
            _POOL = None
def borrow_connection(timeout: float = 2.0):
    """Toma una conexión del pool, o crea una nueva si el pool está vacío."""
    global _POOL
    if _POOL is None:
        init_pool()

    try:
        conn = _POOL.get(block=True, timeout=timeout)
    except Exception:
        # pool vacío o timeout -> crear conexión efímera
        return _make_connection()

    # health check
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchall()
        cur.close()
        return conn
    except Exception:
        try:
            conn.close()
        except Exception:
            pass
        return _make_connection()


def return_connection(conn):
    """Devuelve la conexión al pool o la cierra si el pool está lleno."""
    global _POOL
    if conn is None:
        return
    if _POOL is None:
        try:
            conn.close()
        except Exception:
            pass
        return

    try:
        _POOL.put(conn, block=False)
    except Exception:
        try:
            conn.close()
        except Exception:
            pass


def fetch_df(sql: str, params: dict | None = None):
    """Ejecuta una consulta SQL Server y devuelve un DataFrame.

    Usa conexiones del pool cuando sea posible para reducir latencia.
    """

    import re

    conn = None
    cursor = None
    try:
        conn = borrow_connection()
        cursor = conn.cursor()

        if params:
            # Convert named @params to positional %s placeholders preserving order
            if isinstance(params, dict):
                names = re.findall(r"@([A-Za-z0-9_]+)", sql)
                if names:
                    values = tuple(params.get(n) for n in names)
                    sql_exec = re.sub(r"@([A-Za-z0-9_]+)", "%s", sql)
                    cursor.execute(sql_exec, values)
                else:
                    cursor.execute(sql, params)
            else:
                cursor.execute(sql, params)
        else:
            cursor.execute(sql)

        if cursor.description:
            columns = [c[0] for c in cursor.description]
            rows = cursor.fetchall()
            df = pd.DataFrame(rows, columns=columns)

            try:
                sql_start = sql.lstrip().split(None, 1)[0].lower()
            except Exception:
                sql_start = ""
            if sql_start not in ("select",):
                try:
                    conn.commit()
                except Exception:
                    pass
            return df

        conn.commit()
        return pd.DataFrame()

    except Exception:
        raise

    finally:
        try:
            if cursor is not None:
                cursor.close()
        except Exception:
            pass
        try:
            if conn is not None:
                return_connection(conn)
        except Exception:
            pass


def get_engine():
    raise NotImplementedError(
        "get_engine() ya no existe. Usa fetch_df() en su lugar."
    )



