import streamlit as st
import pyodbc
import pandas as pd
from urllib.parse import quote_plus


def get_connection():
    """
    Crea una conexión estable a SQL Server (Cloud SQL - GCP)
    usando pyodbc directo, con SSL habilitado.
    """

    server = st.secrets["DB_HOST"]
    port = st.secrets["DB_PORT"]
    database = st.secrets["DB_NAME"]
    username = st.secrets["DB_USER"]
    password = st.secrets["DB_PASS"]

    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={server},{port};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
        "Connection Timeout=30;"
    )

    return pyodbc.connect(conn_str)


def fetch_df(sql: str, params: dict | None = None):
    """
    Ejecuta una consulta SQL y devuelve un DataFrame.
    Reemplaza completamente SQLAlchemy para asegurar estabilidad en Streamlit Cloud.
    """

    conn = get_connection()
    cursor = conn.cursor()

    try:
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)

        # SELECT → devuelve rows
        if cursor.description:
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            return pd.DataFrame.from_records(rows, columns=columns)

        # UPDATE / INSERT / DELETE → sin rows
        conn.commit()
        return pd.DataFrame()

    except Exception as e:
        print("Error al ejecutar consulta:", e)
        raise

    finally:
        try:
            cursor.close()
        except:
            pass
        try:
            conn.close()
        except:
            pass
