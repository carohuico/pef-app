import streamlit as st
import pyodbc

st.title("🔌 Test SQL Server connection")

server   = st.secrets["DB_HOST"]
port     = st.secrets["DB_PORT"]
database = st.secrets["DB_NAME"]
username = st.secrets["DB_USER"]
password = st.secrets["DB_PASS"]

conn_str = (
    "Driver={ODBC Driver 18 for SQL Server};"
    f"Server={server},{port};"
    f"Database={database};"
    f"Uid={username};"
    f"Pwd={password};"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
    "Connection Timeout=30;"
)

st.code(conn_str)

try:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sys.databases;")
    rows = cursor.fetchall()

    st.success("Conexión EXITOSA a SQL Server 🎉")
    st.write([r[0] for r in rows])

except Exception as e:
    st.error("❌ Error conectando a SQL Server")
    st.exception(e)
