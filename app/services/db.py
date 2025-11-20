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


def get_db_info():
    """Retorna un dict con información diagnóstica de la conexión:
    - current_db: nombre de la base de datos en la sesión
    - current_user: usuario actual
    - tables: DataFrame con los schemas y tablas visibles
    Esta función facilita depurar por qué una tabla (p. ej. `usuarios`) no existe.
    """
    try:
        # DB actual y usuario
        df_db = fetch_df("SELECT DB_NAME() AS current_db, SUSER_SNAME() AS current_user;")
        current_db = None
        current_user = None
        if df_db is not None and not df_db.empty:
            current_db = df_db.iloc[0].get("current_db")
            current_user = df_db.iloc[0].get("current_user")

        # Listar tablas visibles con su esquema
        df_tables = fetch_df(
            "SELECT s.name AS schema_name, t.name AS table_name "
            "FROM sys.tables t JOIN sys.schemas s ON t.schema_id = s.schema_id "
            "ORDER BY s.name, t.name;"
        )

        return {
            "current_db": current_db,
            "current_user": current_user,
            "tables": df_tables,
        }
    except Exception as e:
        return {"error": str(e)}

