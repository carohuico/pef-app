from pathlib import Path
import streamlit as st
import pandas as pd

def estadisticas():
    # ---------- CONFIGURACIÓN ----------
    st.set_page_config(page_title="Rainly", layout="wide", initial_sidebar_state="auto")
    
    # ---------- CSS (externo) ----------
    _css_general = Path(__file__).parent.parent / 'assets' / 'general.css'      
    _css_sidebar = Path(__file__).parent.parent / 'assets' / 'sidebar_component.css'
    _css_estadisticas = Path(__file__).parent.parent / 'assets' / 'estadisticas.css'
    
    try:
        with open(_css_general, 'r', encoding='utf-8') as _f:
            st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
        with open(_css_sidebar, 'r', encoding='utf-8') as _f:
            st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
        with open(_css_estadisticas, 'r', encoding='utf-8') as _f:
            st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
    except Exception as _e:
        st.markdown("""
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
        """, unsafe_allow_html=True)

    # ---------- TÍTULO ----------
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="page-header">Estadísticas</div>', unsafe_allow_html=True)
    with col2:
        button_label = ":material/filter_list: Filtros"
        st.button(button_label, use_container_width=True)

    # ---------- ICONOS SVG ----------
    folder_icon = """<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>"""
    
    users_icon = """<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>"""
    
    chart_icon = """<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"></path><path d="M18 17V9"></path><path d="M13 17V5"></path><path d="M8 17v-3"></path></svg>"""

    # ---------- CARDS DE ESTADÍSTICAS PRINCIPALES ----------
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-icon">{folder_icon}</div>
            <div class="stat-content">
                <div class="stat-number">2,500</div>
                <div class="stat-label">Evaluaciones totales</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-icon">{users_icon}</div>
            <div class="stat-content">
                <div class="stat-number">800</div>
                <div class="stat-label">Cantidad de evaluados</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-icon">{chart_icon}</div>
            <div class="stat-content">
                <div class="stat-number">2.7</div>
                <div class="stat-label">Evaluaciones / persona</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # ---------- GRÁFICAS ----------
    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown('<div class="chart-title">Evaluaciones por mes</div>', unsafe_allow_html=True)
        
        # Datos para la gráfica de barras
        data_mes = pd.DataFrame({
            'Mes': ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'],
            'Evaluaciones': [230, 180, 210, 195, 160, 140, 145, 200, 210, 225, 250, 270]
        })
        
        st.bar_chart(
            data_mes,
            x='Mes',
            y='Evaluaciones',
            color='#FFD751',
            height=250,
            use_container_width=True
        )
    
    with col_right:
        st.markdown('<div class="chart-title">Evaluaciones por año</div>', unsafe_allow_html=True)
        
        # Datos para la gráfica de líneas
        data_año = pd.DataFrame({
            'Año': [2025, 2026, 2027, 2028, 2029, 2030, 2031, 2032, 2033, 2034, 2035],
            'Evaluaciones': [1800, 1600, 1700, 1750, 1500, 1450, 1550, 1700, 1800, 1850, 2000]
        })
        
        st.line_chart(
            data_año,
            x='Año',
            y='Evaluaciones',
            color='#FFD751',
            height=250,
            use_container_width=True
        )
