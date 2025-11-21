import streamlit as st
import pandas as pd
import pymssql


def get_connection():
    """
    Conexión a SQL Server (Cloud SQL - GCP) usando pymssql,
    compatible con Streamlit Cloud (sin drivers ODBC).
    """
    server = st.secrets["DB_HOST"]
    port = int(st.secrets["DB_PORT"])
    user = st.secrets["DB_USER"]
    password = st.secrets["DB_PASS"]
    database = st.secrets["DB_NAME"]

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
            return pd.DataFrame(rows, columns=columns)

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



