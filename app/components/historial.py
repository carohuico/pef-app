import streamlit as st
import pandas as pd
from typing import List, Dict
from pathlib import Path
from services.exportar import render_export_popover

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


def get_historial_data(num_rows: int =8) -> List[Dict]:
    """Genera datos ficticios para el historial."""
    data = []
    campos = ["Nombre", "Apellido", "Edad", "Sexo", "Estado civil", "Escolaridad", "Ocupación", "Grupo"]
    for i in range(num_rows):
        row = {
            "Nombre": "Holi ipsum",
            "Apellido": "Hola ipsum",
            "Edad": "Hole ipsum",
            "Sexo": "Holo ipsum",
            "Estado civil": "Holu ipsum",
            "Escolaridad": "Hohohoho ipsum",
            "Ocupación": "Holo ipsum",
            "Grupo": "Holo ipsum",
        }
        data.append(row)
    return data

def historial():
    # ---------- CONFIGURACIÓN ----------
    st.set_page_config(page_title="Rainly", layout="wide", initial_sidebar_state="auto")
    # ---------- CSS (externo) ----------
    _css_general = Path(__file__).parent.parent / 'assets' / 'general.css'      
    _css_sidebar = Path(__file__).parent.parent / 'assets' / 'sidebar_component.css'
    _css_inicio = Path(__file__).parent.parent / 'assets' / 'historial.css'
    
    try:
        with open(_css_general, 'r', encoding='utf-8') as _f:
            st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
        with open(_css_sidebar, 'r', encoding='utf-8') as _f:
            st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
        with open(_css_inicio, 'r', encoding='utf-8') as _f:
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
            button_label = ":material/file_download: Exportar"
            
            if 'show_export_popover' not in st.session_state:
                st.session_state['show_export_popover'] = False
                
            if st.button(button_label, key="export_button", use_container_width=True):
                sel = st.session_state.get('historial_selection', [])
                
                if not sel:
                    st.warning("No hay filas seleccionadas para exportar.")
                else:
                    st.session_state['show_export_popover'] = True
            
            if st.session_state['show_export_popover']:
                df_to_display = st.session_state.get("filtered_historial_data", pd.DataFrame(get_historial_data()))
                try:
                    selected_rows = df_to_display.iloc[st.session_state.get('historial_selection', [])]
                except Exception:
                    selected_rows = df_to_display.loc[st.session_state.get('historial_selection', [])]

                # Renderizar el popover que contiene el st.download_button.
                # Esta línea necesita ser llamada CADA VEZ que el script corre,
                # pero el popover solo estará abierto si se hizo clic en el botón.
                render_export_popover(selected_rows)
        with col4:
            button_label = ":material/add_2: Nuevo"
            st.button(button_label, type="primary", use_container_width=True)
        
    df_to_display = st.session_state.get("filtered_historial_data", pd.DataFrame(get_historial_data()))
    event = st.dataframe(
        df_to_display, 
        key ="data",
        on_select = "rerun",
        selection_mode=['multi-row', 'multi-column'],
        use_container_width=True 
    )
    
    # persist selection in session_state so buttons elsewhere can access it on next run
    if getattr(event, 'selection', None):
        rows = event.selection.get('rows', [])
        st.session_state['historial_selection'] = rows
    else:
        # keep previous selection if any, or clear
        if 'historial_selection' not in st.session_state:
            st.session_state['historial_selection'] = []
    
    
    
    
    
    