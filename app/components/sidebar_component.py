import streamlit as st
from pathlib import Path

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

    icons = [":material/home:", ":material/history:", ":material/analytics:", ":material/logout:"]
    nav_links = ["Inicio", "Historial", "Estadísticas", "Salir"]

    for icon, label in zip(icons, nav_links):
        is_active = st.session_state["active_view"] == label.lower()
        custom_class = "primary" if is_active else "secondary"

        st.sidebar.markdown(f'<div class="nav-item-container" style="margin: 0; padding: 0;">', unsafe_allow_html=True)
        if st.sidebar.button(f"{icon} {label}", key=f"nav_{label}", type=custom_class):
            if label == "Inicio":
                st.session_state["active_view"] = "inicio"
            elif label == "Historial":
                st.session_state["active_view"] = "historial"
            elif label == "Estadísticas":
                st.session_state["active_view"] = "estadisticas"
            elif label == "Salir":
                st.session_state["active_view"] = "salir"
            st.rerun()
        st.sidebar.markdown('</div>', unsafe_allow_html=True)



