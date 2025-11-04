from pathlib import Path
from services.queries.q_estadisticas import GET_CANTIDAD_EVALUADOS, GET_EVALUACIONES_POR_PERSONA, GET_EVALUACIONES_TOTALES
from services.queries.q_estadisticas import (
    GET_EVALUACIONES_POR_MES,
    GET_EVALUACIONES_POR_ANIO,
)
from services.db import get_engine, fetch_df
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
        evaluaciones_totales = fetch_df(GET_EVALUACIONES_TOTALES).iloc[0,0]
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-icon">{folder_icon}</div>
            <div class="stat-content">
                <div class="stat-number">{evaluaciones_totales}</div>
                <div class="stat-label">Evaluaciones totales</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        #consulta real
        cantidad_evaluados = fetch_df(GET_CANTIDAD_EVALUADOS).iloc[0,0]
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-icon">{users_icon}</div>
            <div class="stat-content">
                <div class="stat-number">{cantidad_evaluados}</div>
                <div class="stat-label">Cantidad de evaluados</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        avg_evaluaciones = round(fetch_df(GET_EVALUACIONES_POR_PERSONA).iloc[0,0], 2)
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-icon">{chart_icon}</div>
            <div class="stat-content">
                <div class="stat-number">{avg_evaluaciones}</div>
                <div class="stat-label">Evaluaciones / persona</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # ---------- GRÁFICAS ----------
    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown('<div class="chart-title">Evaluaciones por mes</div>', unsafe_allow_html=True)
        # ------- GRÁFICAS DINÁMICAS DESDE BD -------
        
        MONTH_SHORT = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

        try:
            df_years = fetch_df(GET_EVALUACIONES_POR_ANIO)
        except Exception:
            df_years = pd.DataFrame()

        available_years = []
        if not df_years.empty and 'anio' in df_years.columns:
            available_years = sorted(df_years['anio'].astype(int).tolist())

        import datetime
        import altair as alt
        current_year = datetime.date.today().year
        default_year = available_years[-1] if available_years else current_year

        with col2:
            year = st.selectbox('Año', options=available_years if available_years else [current_year], index=(len(available_years)-1 if available_years else 0), label_visibility='collapsed')

        try:
            df_mes = fetch_df(GET_EVALUACIONES_POR_MES, {'anio': int(year)})
        except Exception:
            df_mes = pd.DataFrame()

        months_df = pd.DataFrame({'mes_num': list(range(1,13)), 'Mes': MONTH_SHORT})
        if df_mes.empty:
            months_df['Evaluaciones'] = 0
        else:
            df_mes['mes_num'] = df_mes['mes_num'].astype(int)
            df_mes['cantidad'] = df_mes['cantidad'].astype(int)
            months_df = months_df.merge(df_mes[['mes_num','cantidad']], on='mes_num', how='left')
            months_df['Evaluaciones'] = months_df['cantidad'].fillna(0).astype(int)
            months_df = months_df[['Mes','Evaluaciones']]

        # Calcular máximo y fijar dominio Y = [0, max+1]
        y_max = int(months_df['Evaluaciones'].max()) if not months_df.empty else 0
        domain_max = y_max + 1

        chart = (
            alt.Chart(months_df)
            .mark_bar(color='#FFD751')
            .encode(
            x=alt.X('Mes', sort=MONTH_SHORT),
            y=alt.Y('Evaluaciones', scale=alt.Scale(domain=[0, domain_max]))
            )
            .properties(height=250)
        )

        st.altair_chart(chart, use_container_width=True)
    
    with col_right:
        st.markdown('<div class="chart-title">Evaluaciones por año</div>', unsafe_allow_html=True)
        
        # Datos reales para la gráfica de líneas (por año)
        try:
            df_anio = fetch_df(GET_EVALUACIONES_POR_ANIO)
        except Exception:
            df_anio = pd.DataFrame()

        if df_anio.empty:
            st.info('No hay datos de evaluaciones por año en la base de datos.')
        else:
            df_anio = df_anio.sort_values('anio')
            df_anio_plot = pd.DataFrame({
                'Año': df_anio['anio'].astype(int),
                'Evaluaciones': df_anio['cantidad'].astype(int)
            })
            st.line_chart(
                df_anio_plot,
                x='Año',
                y='Evaluaciones',
                color='#FFD751',
                height=250,
                use_container_width=True
            )
