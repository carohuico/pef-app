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

    conn = get_connection()
    cursor = conn.cursor()

    try:
        if params:
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
        print("DB ERROR:", e)
        raise

    finally:
        cursor.close()
        conn.close()
        
def get_engine():
    raise NotImplementedError(
        "get_engine() ya no existe. Usa fetch_df() y pyodbc directo."
    )

