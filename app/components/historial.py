import streamlit as st
import pandas as pd
from typing import List, Dict
from pathlib import Path
from services.exportar import render_export_popover
from services.db import fetch_df
from services.queries import LISTADO_EVALUADOS_SQL

def styled_search_bar():
    st.markdown("""
        <style>
        /* ... Tu CSS de la barra de búsqueda (lo mantendremos igual) ... */
        /*  */
        div[data-testid="stTextInput"] > div:first-child > div:first-child {
            border-radius: 25px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.06);
            background-color: white;
            border: 1px solid #e6e6e6; 
            display: flex;
            align-items: center;
            padding: 0 10px;
            height: 44px;
            box-sizing: border-box;
        }

        div[data-testid="stTextInput"] input {
            background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="%23888888" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>');
            background-repeat: no-repeat;
            background-position: 14px center;
            background-size: 18px 18px;
            padding-left: 44px !important;
            padding-right: 8px !important;
            border: none !important;
            outline: none !important;
            width: 100% !important;
            height: 100% !important;
            background-color: transparent !important;
            color: #444444 !important;
            box-sizing: border-box !important;
            font-size: 14px !important;
        }

        div[data-testid="stTextInput"] input::placeholder {
            color: #888888 !important;
        }
        div[data-testid="stTextInput"] input:focus {
            outline: none !important;
            box-shadow: none !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    query = st.text_input(
        label="Buscar", 
        value="", 
        placeholder="Buscar", 
        key="historial_search",
        label_visibility="hidden"
    )
    
    original_data = get_historial_data()
    
    if query:
        q = query.lower()
        
        filtered_results = [
            item for item in original_data 
            if any(isinstance(val, str) and q in val.lower() for val in item.values())
        ]
        st.session_state["filtered_historial_data"] = pd.DataFrame(filtered_results)
    else:
        st.session_state["filtered_historial_data"] = pd.DataFrame(original_data)

def get_historial_data(num_rows: int = 8) -> List[Dict]:
    """Attempt to fetch historial data from the DB using the LISTADO_EVALUADOS_SQL.

    Falls back to a small hard-coded sample if the DB is unavailable or the query fails.
    Returns a list of dicts matching the keys expected by the UI.
    """
    try:
        df = fetch_df(LISTADO_EVALUADOS_SQL)
        if df is None or df.empty:
            raise ValueError("No rows returned from DB")

        # Normalize column names to match existing UI expectations
        # - 'Ocupacion' -> 'Ocupación' (accent)
        if 'Ocupacion' in df.columns:
            df = df.rename(columns={'Ocupacion': 'Ocupación'})

        # Ensure the keys used by the UI exist; if not, fill with empty strings
        expected_cols = [
            'Nombre', 'Apellido', 'Edad', 'Sexo', 'Estado civil',
            'Escolaridad', 'Ocupación', 'Grupo'
        ]
        for c in expected_cols:
            if c not in df.columns:
                df[c] = ''

        # Convert to list of dicts for the rest of the component
        records = df[expected_cols].fillna('').to_dict(orient='records')
        return records
    except Exception as e:
        st.error(f"Error fetching data from database: {e}")
        # Fallback sample data (keeps previous behavior when DB not available)
        data = []
        nombres = ["caro", "juan", "maria", "luis", "ana", "carlos", "sofia", "diego"]
        apellidos = ["huico", "gomez", "lopez", "martinez", "garcia", "rodriguez", "fernandez", "sanchez"]
        edades = [25, 30, 22, 35, 28, 40, 32, 29]
        estados_civiles = ["Soltero(a)", "Casado(a)", "Divorciado(a)", "Viudo(a)", "Separado(a)"]
        escolaridades = ["Primaria", "Secundaria", "Preparatoria", "Universidad"]
        ocupaciones = ["Estudiante", "Empleado", "Desempleado", "Estudiante"]
        grupos = ["Grupo A", "Grupo B", "Grupo C", "Grupo D"]
        sexos = ["Femenino", "Masculino"]
        for i in range(num_rows):
            row = {
                "Nombre": nombres[i % len(nombres)],
                "Apellido": apellidos[i % len(apellidos)],
                "Edad": edades[i % len(edades)],
                "Sexo": sexos[i % len(sexos)],
                "Estado civil": estados_civiles[i % len(estados_civiles)],
                "Escolaridad": escolaridades[i % len(escolaridades)],
                "Ocupación": ocupaciones[i % len(ocupaciones)],
                "Grupo": grupos[i % len(grupos)],
            }
            data.append(row)
        return data

def historial():
    # ---------- CONFIGURACIÓN ----------
    st.set_page_config(page_title="Rainly", layout="wide", initial_sidebar_state="auto")
    # ---------- CSS (externo) ----------
    _css_general = Path(__file__).parent.parent / 'assets' / 'general.css'      
    _css_sidebar = Path(__file__).parent.parent / 'assets' / 'sidebar_component.css'
    _css_historial = Path(__file__).parent.parent / 'assets' / 'historial.css'
    
    try:
        with open(_css_general, 'r', encoding='utf-8') as _f:
            st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
        with open(_css_sidebar, 'r', encoding='utf-8') as _f:
            st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
        with open(_css_historial, 'r', encoding='utf-8') as _f:
            st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
    except Exception as _e:
        st.markdown("""
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
        """, unsafe_allow_html=True)
    
    st.markdown('<div class="page-header">Historial</div>', unsafe_allow_html=True)
    col1, col2 = st.columns([.7, 1])
        
    with col1:
        styled_search_bar()
    with col2:
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        with col1:
            button_label = ":material/delete: Eliminar"
            st.button(button_label, use_container_width=True)
        with col2:
            button_label = ":material/filter_list: Filtros"
            st.button(button_label, use_container_width=True)
        with col3:
            sel = st.session_state.get('historial_selection', [])
            button_label = ":material/file_download: Exportar"
            help_msg = "**:material/error: Seleccione al menos una fila para exportar**"
            if st.button(button_label, use_container_width=True, disabled=len(sel) == 0,
                        help=help_msg if len(sel) == 0 else None):
                st.session_state['show_export_popover'] = True
        with col4:
            button_label = ":material/add_2: Nuevo"
            if st.button(button_label, type="primary", use_container_width=True):
                st.session_state["active_view"] = "registrar"
        
    df_to_display = st.session_state.get("filtered_historial_data", pd.DataFrame(get_historial_data()))
    event = st.dataframe(
        df_to_display, 
        key="data",
        on_select="rerun",
        selection_mode='multi-row',
        use_container_width=True,
        hide_index=True, 
        height=300
    )
    
    if event and getattr(event, 'selection', None):
        rows = event.selection.rows
        export_rows = df_to_display.iloc[rows]
        st.session_state['historial_selection'] = rows
        
        if st.session_state.get('show_export_popover', False):
           render_export_popover(export_rows)
           st.session_state['show_export_popover'] = False
    else:
        st.session_state['historial_selection'] = []
        rows = []
    
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        sel = st.session_state.get('historial_selection', [])
        is_single_selection = len(sel) == 1
        
        help_msg = "**:material/error: Seleccione una sola fila para ver el expediente**"
        
        if st.button("Ver expediente", 
                    type="primary", 
                    use_container_width=True, 
                    disabled=not is_single_selection,
                    help=help_msg if not is_single_selection else None):
            #selected data object
            selected_data = df_to_display.iloc[sel[0]]
            st.session_state["individual"] = selected_data.to_dict()
            st.session_state["active_view"] = "individual"
            st.rerun()