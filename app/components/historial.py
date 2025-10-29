import streamlit as st
import pandas as pd
from typing import List, Dict
from pathlib import Path
from services.exportar import render_export_popover
import contextlib

class Modal:
    """MODAL POP UP STREAMLIT THAT COVERS THE SCREEN WITH A SEMI-TRANSPARENT BACKDROP AND STYLED DIALOG."""

    def __init__(self, title: str, key: str | None = None):
        self.title = title
        self.key = key or f"modal_{title}"
        if self.key not in st.session_state:
            st.session_state[self.key] = False

    def open(self):
        st.session_state[self.key] = True

    def close(self):
        st.session_state[self.key] = False

    def is_open(self) -> bool:
        return bool(st.session_state.get(self.key, False))

    @contextlib.contextmanager
    def container(self):
        """When open, injects styled backdrop + modal wrapper and yields a Streamlit container
        whose outputs are wrapped inside the modal. The opening <div> is rendered before yielding
        and a closing </div> is rendered after, so Streamlit widgets placed inside the with-block
        appear inside the modal box."""
        if not self.is_open():
            yield None
            return

        overlay_css = f"""
        <style>
        /* Backdrop */
        .modal-backdrop-{self.key} {{
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.45);
            z-index: 9997;
            backdrop-filter: blur(2px);
        }}
        /* Modal box */
        .modal-content-{self.key} {{
            position: fixed;
            left: 50%;
            top: 50%;
            transform: translate(-50%, -50%);
            z-index: 9999;
            width: min(800px, 92%);
            background-color: #ffffff;
            border-radius: 12px;
            padding: 18px;
            box-shadow: 0 10px 30px rgba(2,6,23,0.2);
            font-family: "Poppins", sans-serif;
            color: #222;
        }}
        .modal-header-{self.key} {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            margin-bottom: 10px;
        }}
        .modal-title-{self.key} {{
            font-size: 18px;
            font-weight: 600;
        }}
        .modal-close-{self.key} {{
            background: transparent;
            border: none;
            font-size: 20px;
            line-height: 1;
            cursor: pointer;
            color: #666;
        }}
        .modal-body-{self.key} {{
            margin-top: 6px;
        }}
        /* Make sure internal Streamlit elements inside modal stay above backdrop */
        </style>
        """

        open_html = (
            overlay_css
            + f"<div class='modal-backdrop-{self.key}'></div>"
            + f"<div class='modal-content-{self.key}'>"
            + f"<div class='modal-header-{self.key}'>"
            + f"<div class='modal-title-{self.key}'>{self.title}</div>"
            + f"</div>"
            + f"<div class='modal-body-{self.key}'>"
        )
        close_html = "</div></div>"

        container = st.container()
        # Render the opening HTML (starts the modal box)
        container.markdown(open_html, unsafe_allow_html=True)
        try:
            yield container
        finally:
            # Close the modal HTML wrapper
            container.markdown(close_html, unsafe_allow_html=True)

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
            if st.button(button_label, use_container_width=True):
                st.session_state['show_export_popover'] = True
        with col4:
            button_label = ":material/add_2: Nuevo"
            if st.button(button_label, type="primary", use_container_width=True):
                st.session_state["active_view"] = "registrar"
        
    df_to_display = st.session_state.get("filtered_historial_data", pd.DataFrame(get_historial_data()))
    event = st.dataframe(
        df_to_display, 
        key ="data",
        on_select = "rerun",
        selection_mode=['multi-row', 'multi-column'],
        use_container_width=True 
    )
    
    if getattr(event, 'selection', None):
        rows = event.selection.get('rows', [])
        st.session_state['historial_selection'] = rows
    else:
        if 'historial_selection' not in st.session_state:
            st.session_state['historial_selection'] = []
    
    if 'show_export_popover' not in st.session_state:
                st.session_state['show_export_popover'] = False
                
    if st.button(button_label, key="export_button", use_container_width=True):
        sel = st.session_state.get('historial_selection', [])
        
        if not sel:
            st.markdown("""<div class="warning">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" style="flex:0 0 14px;">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
                        </svg>
                        <span>Seleccione al menos una fila para exportar los datos.</span>
                        </div>""", unsafe_allow_html=True)
        else:
            st.session_state['show_export_popover'] = True
    
    if st.session_state['show_export_popover']:
        confirmationEdit = Modal("Atención", key= "popUp_edit")
        submitted = st.button("Enviar")
        if submitted:
            confirmationEdit.open()
            
        if confirmationEdit.is_open():
            with confirmationEdit.container():
                st.markdown(""" ### ¿Deseas guardar los cambios? """)
                yes = st.button("Sí")
                no  = st.button("No")

                if yes == True:
                    confirmationEdit.close()

                if no == True:
                    confirmationEdit.close()
    
    
    
    
    