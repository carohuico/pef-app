import streamlit as st
from pathlib import Path
import unicodedata

def render_sidebar():
    st.sidebar.title("Rainly")


def sidebar_component():
    _css_sidebar = Path(__file__).parent.parent / 'assets' / 'sidebar_component.css'
    try:
        with open(_css_sidebar, 'r', encoding='utf-8') as _f:
            st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
    except Exception as _e:
        st.markdown(
            """
            <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
            """,
            unsafe_allow_html=True
        )
        
    st.sidebar.markdown(
        f"""
            <h2 style="text-align: center; color:white; margin: 0;">Rainly</h2>
        """,
        unsafe_allow_html=True
    )
    
    avatar_path = Path(__file__).parent.parent / 'assets' / 'luis.jpeg'
    st.sidebar.image(avatar_path, width=100)
    st.sidebar.markdown(
        f"""
            <div class="user-profile" style="margin: 0; padding: 0;">
                <p class="username" style="margin: 0;">Nombre</p>
                <p class="role" style="margin: 0;">Usuario</p>
            </div>
        """,
        unsafe_allow_html=True
    )

    if "active_view" not in st.session_state:
        st.session_state["active_view"] = "inicio"

    icons = [":material/home:", ":material/history:", ":material/analytics:", ":material/settings:", ":material/logout:"]
    nav_links = ["Inicio", "Historial", "Estadísticas", "Ajustes", "Salir"]

    def label_to_key(lbl: str) -> str:
        # Normalize label to ASCII, lower-case, and remove spaces so it matches
        # the keys used in session_state (e.g. 'Estadísticas' -> 'estadisticas').
        nf = unicodedata.normalize('NFKD', lbl)
        ascii_only = nf.encode('ASCII', 'ignore').decode('ASCII')
        return ascii_only.lower().replace(' ', '')

    for icon, label in zip(icons, nav_links):
        label_key = label_to_key(label)
        is_active = st.session_state["active_view"] == label_key
        custom_class = "primary" if is_active else "secondary"
        st.sidebar.markdown(f'<div class="nav-item-container" style="margin: 0; padding: 0;">', unsafe_allow_html=True)
        # use a sanitized key for the Streamlit widget key
        widget_key = f"nav_{label_key}"
        if st.sidebar.button(f"{icon} {label}", key=widget_key, type=custom_class):
            # set the canonical session key using the normalized label_key
            if label_key == "inicio":
                st.session_state["active_view"] = "inicio"
            elif label_key == "historial":
                st.session_state["active_view"] = "historial"
            elif label_key == "estadisticas":
                st.session_state["active_view"] = "estadisticas"
            elif label_key == "ajustes":
                st.session_state["active_view"] = "ajustes"
            elif label_key == "salir":
                st.session_state["active_view"] = "salir"
            st.rerun()
        st.sidebar.markdown('</div>', unsafe_allow_html=True)



