import streamlit as st
import pandas as pd
import pymssql
import os


def get_connection():
    """
    Conexión a SQL Server (Cloud SQL - GCP) usando pymssql,
    compatible con Streamlit Cloud (sin drivers ODBC).
    """
    # Preferir st.secrets en producción (Streamlit Cloud). En desarrollo local
    # usar variables de entorno y, si no están definidas, caer a valores
    # por defecto para facilitar pruebas (estos valores se pueden eliminar
    # o reemplazar por variables de entorno en tu máquina).
    def _get(key: str, default: str | None = None) -> str | None:
        try:
            if hasattr(st, "secrets"):
                val = st.secrets.get(key)
                if val:
                    return val
        except Exception:
            pass
        return os.environ.get(key, default)

    server = _get("DB_HOST", "34.55.82.47")
    port = int(_get("DB_PORT", "1433") or 1433)
    user = _get("DB_USER", "streamlit_user")
    password = _get("DB_PASS", "pbll_pwd")
    database = _get("DB_NAME", "PBLL")

    return pymssql.connect(
        server=server,
        port=port,
        user=user,
        password=password,
        database=database,
        login_timeout=10,
        timeout=30,
    )


def fetch_df(sql: str, params: dict | None = None):
    """
    Ejecuta una consulta SQL Server y devuelve un DataFrame.
    Compatible con Streamlit Cloud.
    """

    import re

    conn = get_connection()
    cursor = conn.cursor()

    try:
        if params:
            # pymssql does not support T-SQL named parameters like `@usuario` when
            # passing a dict directly. Convert named params to positional `%s`
            # placeholders and build a tuple of values in the order of appearance.
            if isinstance(params, dict):
                # find parameter names in order of appearance
                names = re.findall(r"@([A-Za-z0-9_]+)", sql)
                if names:
                    values = tuple(params.get(n) for n in names)
                    sql_exec = re.sub(r"@([A-Za-z0-9_]+)", "%s", sql)
                    cursor.execute(sql_exec, values)
                else:
                    # no @params found; try passing dict directly (best-effort)
                    cursor.execute(sql, params)
            else:
                # params provided as sequence/tuple - pass through
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

    except Exception as e:
        raise

    finally:
        cursor.close()
        conn.close()
        
def get_engine():
    raise NotImplementedError(
        "get_engine() ya no existe. Usa fetch_df() y pyodbc directo."
    )



