from pathlib import Path
from services.queries.q_estadisticas import (
    GET_EVALUACIONES_TOTALES, 
    GET_CANTIDAD_EVALUADOS, 
    GET_EVALUACIONES_POR_PERSONA, 
    GET_EVALUACIONES_TOTALES_FILTERED,
    GET_CANTIDAD_EVALUADOS_FILTERED,
    GET_EVALUACIONES_POR_PERSONA_FILTERED,
    GET_EVALUACIONES_POR_MES_FILTERED,
    GET_EVALUACIONES_POR_ANIO_FILTERED,
    GET_LISTA_EVALUADOS,
    GET_LISTA_GRUPOS,
    GET_LISTA_SEXOS,
    GET_RANGO_FECHAS
)
from services.queries.q_estadisticas import (
    GET_EVALUACIONES_POR_MES,
    GET_EVALUACIONES_POR_ANIO,
)
from services.db import get_engine, fetch_df
import streamlit as st
import pandas as pd
import datetime
import altair as alt

@st.dialog("🔍 Filtros de búsqueda", width="large")
def modal_filtros():
    """Modal de filtros usando st.dialog nativo de Streamlit"""
    
    # Obtener datos para los selectores
    try:
        df_evaluados = fetch_df(GET_LISTA_EVALUADOS)
        df_grupos = fetch_df(GET_LISTA_GRUPOS)
        df_sexos = fetch_df(GET_LISTA_SEXOS)
        df_rango_fechas = fetch_df(GET_RANGO_FECHAS)
    except Exception as e:
        st.error(f"Error al cargar opciones de filtros: {e}")
        df_evaluados = pd.DataFrame()
        df_grupos = pd.DataFrame()
        df_sexos = pd.DataFrame()
        df_rango_fechas = pd.DataFrame()

    # Inicializar valores de los widgets a partir de los filtros ya aplicados
    # de modo que al cerrar y reabrir el modal se conserven las selecciones.
    filtros_actuales = st.session_state.get('filtros_aplicados', {
        'id_evaluado': None,
        'sexo': None,
        'id_grupo': None,
        'fecha_inicio': None,
        'fecha_fin': None
    })

    # Si se solicitó un reset de los widgets del modal (por ejemplo desde
    # el botón "Limpiar filtros"), eliminar las claves de widget de
    # session_state antes de que los widgets se instancien. Esto evita la
    # excepción de Streamlit al modificar keys ya creadas.
    if st.session_state.get('_reset_modal_widgets'):
        for _k in ('filtro_evaluado', 'filtro_grupo', 'filtro_sexo', 'filtro_fecha_inicio', 'filtro_fecha_fin'):
            if _k in st.session_state:
                try:
                    del st.session_state[_k]
                except Exception:
                    # ignore if deletion fails for any reason
                    pass
        # clear the flag
        st.session_state['_reset_modal_widgets'] = False

    # filtro: evaluado (guardamos el nombre_completo correspondiente si existe)
    if 'filtro_evaluado' not in st.session_state:
        if filtros_actuales.get('id_evaluado') and not df_evaluados.empty:
            matches = df_evaluados[df_evaluados['id_evaluado'] == int(filtros_actuales['id_evaluado'])]
            if not matches.empty:
                st.session_state['filtro_evaluado'] = matches['nombre_completo'].iloc[0]
            else:
                st.session_state['filtro_evaluado'] = 'Todos'
        else:
            st.session_state['filtro_evaluado'] = 'Todos'

    # filtro: grupo
    if 'filtro_grupo' not in st.session_state:
        if filtros_actuales.get('id_grupo') and not df_grupos.empty:
            matches = df_grupos[df_grupos['id_grupo'] == int(filtros_actuales['id_grupo'])]
            if not matches.empty:
                st.session_state['filtro_grupo'] = matches['nombre'].iloc[0]
            else:
                st.session_state['filtro_grupo'] = 'Todos'
        else:
            st.session_state['filtro_grupo'] = 'Todos'

    # filtro: sexo
    if 'filtro_sexo' not in st.session_state:
        st.session_state['filtro_sexo'] = filtros_actuales.get('sexo') if filtros_actuales.get('sexo') else 'Todos'

    # filtros: fechas
    # Aseguramos que las claves existan en session_state; valores pueden ser None o date
    if 'filtro_fecha_inicio' not in st.session_state:
        st.session_state['filtro_fecha_inicio'] = filtros_actuales.get('fecha_inicio')
    if 'filtro_fecha_fin' not in st.session_state:
        st.session_state['filtro_fecha_fin'] = filtros_actuales.get('fecha_fin')

    # Primera fila: Participante y Grupo
    col1, col2 = st.columns(2)
    
    with col1:
        evaluado_options = ['Todos'] + df_evaluados['nombre_completo'].tolist() if not df_evaluados.empty else ['Todos']
        evaluado_selected = st.selectbox(
            'Participante',
            options=evaluado_options,
            key='filtro_evaluado'
        )
    
    with col2:
        grupo_options = ['Todos'] + df_grupos['nombre'].tolist() if not df_grupos.empty else ['Todos']
        grupo_selected = st.selectbox(
            'Grupo',
            options=grupo_options,
            key='filtro_grupo'
        )
    
    # Segunda fila: Sexo y Rango de fechas
    col1, col2 = st.columns(2)
    
    with col1:
        sexo_options = ['Todos'] + df_sexos['sexo'].tolist() if not df_sexos.empty else ['Todos']
        sexo_selected = st.selectbox(
            'Sexo',
            options=sexo_options,
            key='filtro_sexo'
        )
    
    with col2:
        col_fecha1, col_fecha2 = st.columns(2)
        
        fecha_min = df_rango_fechas['fecha_min'].iloc[0] if not df_rango_fechas.empty else datetime.date.today()
        fecha_max = df_rango_fechas['fecha_max'].iloc[0] if not df_rango_fechas.empty else datetime.date.today()
        
        with col_fecha1:
            fecha_inicio = st.date_input(
                'Desde',
                value=None,
                min_value=fecha_min,
                max_value=fecha_max,
                key='filtro_fecha_inicio',
                format="YYYY/MM/DD"
            )
        
        with col_fecha2:
            fecha_fin = st.date_input(
                'Hasta',
                value=None,
                min_value=fecha_min,
                max_value=fecha_max,
                key='filtro_fecha_fin',
                format="YYYY/MM/DD"
            )
    
    st.divider()
    
    # Botones de acción
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button('Limpiar filtros', use_container_width=True, key='btn_limpiar'):
            st.session_state.filtros_aplicados = {
                'id_evaluado': None,
                'sexo': None,
                'id_grupo': None,
                'fecha_inicio': None,
                'fecha_fin': None
            }
            # Señalar que queremos resetear los widgets del modal. La lógica
            # de inicialización del modal borrará las claves antes de crear
            # los widgets y así se mostrarán los valores por defecto.
            st.session_state['_reset_modal_widgets'] = True
            st.rerun()
    
    with col_btn2:
        if st.button('Aplicar filtros', use_container_width=True, type='primary', key='btn_aplicar'):
            # Mapear selecciones a IDs
            id_evaluado = None
            if evaluado_selected != 'Todos':
                idx = df_evaluados[df_evaluados['nombre_completo'] == evaluado_selected].index
                if len(idx) > 0:
                    id_evaluado = int(df_evaluados.loc[idx[0], 'id_evaluado'])
            
            id_grupo = None
            if grupo_selected != 'Todos':
                idx = df_grupos[df_grupos['nombre'] == grupo_selected].index
                if len(idx) > 0:
                    id_grupo = int(df_grupos.loc[idx[0], 'id_grupo'])
            
            # Actualizar filtros
            st.session_state.filtros_aplicados = {
                'id_evaluado': id_evaluado,
                'sexo': sexo_selected if sexo_selected != 'Todos' else None,
                'id_grupo': id_grupo,
                'fecha_inicio': fecha_inicio if fecha_inicio else None,
                'fecha_fin': fecha_fin if fecha_fin else None
            }
            st.rerun()


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

    # ---------- INICIALIZAR SESSION STATE ----------
    if 'filtros_aplicados' not in st.session_state:
        st.session_state.filtros_aplicados = {
            'id_evaluado': None,
            'sexo': None,
            'id_grupo': None,
            'fecha_inicio': None,
            'fecha_fin': None
        }

    # ---------- TÍTULO Y BOTÓN DE FILTROS ----------
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown('<div class="page-header">Estadísticas</div>', unsafe_allow_html=True)
    with col2:
        button_label = ":material/filter_list: Filtros"
        if st.button(button_label, use_container_width=True):
            modal_filtros()

    # ---------- VERIFICAR SI HAY FILTROS ACTIVOS ----------
    filtros_activos = any(v is not None for v in st.session_state.filtros_aplicados.values())

    # Mostrar indicador de filtros activos
    if filtros_activos:
        filtros_texto = []
        if st.session_state.filtros_aplicados['id_evaluado']:
            filtros_texto.append("Participante específico")
        if st.session_state.filtros_aplicados['sexo']:
            filtros_texto.append(f"Sexo: {st.session_state.filtros_aplicados['sexo']}")
        if st.session_state.filtros_aplicados['id_grupo']:
            filtros_texto.append("Grupo específico")
        if st.session_state.filtros_aplicados['fecha_inicio'] or st.session_state.filtros_aplicados['fecha_fin']:
            filtros_texto.append("Rango de fechas")
        

    # ---------- ICONOS SVG ----------
    folder_icon = """<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>"""
    
    users_icon = """<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>"""
    
    chart_icon = """<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"></path><path d="M18 17V9"></path><path d="M13 17V5"></path><path d="M8 17v-3"></path></svg>"""

    # ---------- CARDS DE ESTADÍSTICAS PRINCIPALES ----------
    col1, col2, col3 = st.columns(3)
    
    # Preparar parámetros según si hay filtros o no
    if filtros_activos:
        params = st.session_state.filtros_aplicados
    else:
        params = None
    
    with col1:
        try:
            if filtros_activos:
                evaluaciones_totales = fetch_df(GET_EVALUACIONES_TOTALES_FILTERED, params).iloc[0, 0]
            else:
                evaluaciones_totales = fetch_df(GET_EVALUACIONES_TOTALES).iloc[0, 0]
        except Exception as e:
            evaluaciones_totales = 0
            st.error(f"Error al obtener evaluaciones totales: {e}")
        
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
        try:
            if filtros_activos:
                cantidad_evaluados = fetch_df(GET_CANTIDAD_EVALUADOS_FILTERED, params).iloc[0, 0]
            else:
                cantidad_evaluados = fetch_df(GET_CANTIDAD_EVALUADOS).iloc[0, 0]
        except Exception as e:
            cantidad_evaluados = 0
            st.error(f"Error al obtener cantidad de evaluados: {e}")
        
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
        try:
            if filtros_activos:
                avg_evaluaciones = round(fetch_df(GET_EVALUACIONES_POR_PERSONA_FILTERED, params).iloc[0, 0], 2)
            else:
                avg_evaluaciones = round(fetch_df(GET_EVALUACIONES_POR_PERSONA).iloc[0, 0], 2)
        except Exception as e:
            avg_evaluaciones = 0.0
            st.error(f"Error al obtener promedio de evaluaciones: {e}")
        
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
        
        MONTH_SHORT = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

        try:
            if filtros_activos:
                params_anio = st.session_state.filtros_aplicados.copy()
                df_years = fetch_df(GET_EVALUACIONES_POR_ANIO_FILTERED, params_anio)
            else:
                df_years = fetch_df(GET_EVALUACIONES_POR_ANIO)
        except Exception:
            df_years = pd.DataFrame()

        available_years = []
        if not df_years.empty and 'anio' in df_years.columns:
            available_years = sorted(df_years['anio'].astype(int).tolist())

        current_year = datetime.date.today().year
        default_year = available_years[-1] if available_years else current_year

        with col2:
            year = st.selectbox('Año', options=available_years if available_years else [current_year], 
                              index=(len(available_years)-1 if available_years else 0), 
                              label_visibility='collapsed')

        try:
            if filtros_activos:
                params_mes = st.session_state.filtros_aplicados.copy()
                params_mes['anio'] = int(year)
                df_mes = fetch_df(GET_EVALUACIONES_POR_MES_FILTERED, params_mes)
            else:
                df_mes = fetch_df(GET_EVALUACIONES_POR_MES, {'anio': int(year)})
        except Exception:
            df_mes = pd.DataFrame()

        months_df = pd.DataFrame({'mes_num': list(range(1, 13)), 'Mes': MONTH_SHORT})
        if df_mes.empty:
            months_df['Evaluaciones'] = 0
        else:
            df_mes['mes_num'] = df_mes['mes_num'].astype(int)
            df_mes['cantidad'] = df_mes['cantidad'].astype(int)
            months_df = months_df.merge(df_mes[['mes_num', 'cantidad']], on='mes_num', how='left')
            months_df['Evaluaciones'] = months_df['cantidad'].fillna(0).astype(int)
            months_df = months_df[['Mes', 'Evaluaciones']]

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
        
        try:
            if filtros_activos:
                df_anio = fetch_df(GET_EVALUACIONES_POR_ANIO_FILTERED, st.session_state.filtros_aplicados)
            else:
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