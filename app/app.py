import streamlit as st
from pathlib import Path

css_path = Path(__file__).parent / "assets" / "styles.css"
with open(css_path, encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


st.set_page_config(page_title="Persona Bajo la Lluvia", layout="wide")

st.title("PBLL – Plataforma de Evaluación")
st.write("Estructura base lista. Usa el menú de páginas (arriba: ‘⋮’ → Pages) si aparece.")
st.info("Cuando veas esta pantalla en el navegador, la app base está funcionando.")