import streamlit as st
from datetime import datetime
from pathlib import Path
import os
import sys

# Importar las funciones necesarias
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
try:
    from config.settings import TEMP_DIR, STD_DIR
    from services.image_preprocess import estandarizar_imagen
    from services.indicadores import simular_resultado
    from services.db import get_engine
    from services.queries.q_registro import POST_PRUEBA, POST_RESULTADO
    from components.bounding_boxes import imagen_bboxes
    from PIL import Image
    from sqlalchemy import text
    import pandas as pd
except ImportError as e:
    st.error(f"Error importing modules: {e}")

@st.dialog("Agregar Dibujo", width="large")
def agregar_dibujo_modal(id_evaluado: str = None, current_image_index: int = 0):
    """Modal para agregar un nuevo dibujo al expediente del evaluado."""
    
    # Inicializar estado del modal
    if 'modal_step' not in st.session_state:
        st.session_state['modal_step'] = 1
    if 'modal_uploaded_file' not in st.session_state:
        st.session_state['modal_uploaded_file'] = None
    if 'modal_indicadores' not in st.session_state:
        st.session_state['modal_indicadores'] = None
    
    current_step = st.session_state['modal_step']
    
    # CSS
    st.markdown("""
    <style>
        /* Centrar el modal vertical y horizontalmente */
        [data-testid="stModal"] {
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        
        [data-testid="stModal"] > div[data-testid="stVerticalBlock"] {
            margin: auto !important;
        }
        
        .modal-stepper {
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 32px;
            padding: 20px 0;
        }
        
        .modal-step {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 8px;
        }
        
        .modal-step-circle {
            width: 48px;
            height: 48px;
            border-radius: 50%;
            background: #FFE451;
            color: #111;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 18px;
        }
        
        .modal-step-text {
            font-size: 14px;
            color: #111;
            font-weight: 600;
        }
        
        .warning {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 12px 16px;
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            border-radius: 4px;
            margin: 16px 0;
            color: #856404;
        }
        
        /* Alinear el botón de file uploader arriba */
        [data-testid="stFileUploader"] {
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        
        [data-testid="stFileUploader"] > div {
            width: 100%;
        }
        
        [data-testid="stFileUploader"] button {
            align-self: center;
        }
        
        /* Contenedor de imagen con scroll y sin redimensionar */
        .image-container {
            width: 100%;
            max-height: 400px;
            overflow: auto;
            border-radius: 10px;
            border: 1px solid #ddd;
            display: flex;
            justify-content: center;
            align-items: flex-start;
            background-color: #f8f9fa;
        }
        
        .image-container img {
            border-radius: 10px !important;
            width: auto !important;
            height: auto !important;
            max-width: none !important;
            display: block;
        }
        
        /* Mantener estilos de imagen originales pero solo dentro del modal */
        [data-testid="stModal"] [data-testid="stImage"] {
            display: flex;
            justify-content: center;
        }
        
        [data-testid="stModal"] [data-testid="stImage"] img {
            border-radius: 10px !important;
            max-height: 400px;
            width: auto !important;
            object-fit: contain;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Mostrar solo el paso actual
    step_labels = {1: "Subir dibujo", 2: "Resultados", 3: "Exportar"}
    st.markdown(f"""
    <div class="modal-stepper">
        <div class="modal-step">
            <div class="modal-step-circle">{current_step}</div>
            <div class="modal-step-text">{step_labels[current_step]}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # PASO 1: Subir dibujo
    if current_step == 1:
        uploaded_file = st.file_uploader(
            "Selecciona una imagen",
            type=["png", "jpg", "jpeg", "heic"],
            key="modal_file_uploader",
            label_visibility="collapsed"
        )
        
        if uploaded_file is not None:
            st.session_state['modal_uploaded_file'] = uploaded_file
    
    # PASO 2: Resultados
    elif current_step == 2:
        if st.session_state.get("modal_uploaded_file") is not None:
            filename = st.session_state["modal_uploaded_file"].name
            txt_filename = os.path.splitext(filename)[0] + ".txt"

            indicadores = simular_resultado(txt_filename)
            # store under the modal-specific key
            st.session_state['modal_indicadores'] = indicadores


            if st.session_state.get("modal_uploaded_file") is not None:
                try:
                    original = Image.open(st.session_state["modal_uploaded_file"])
                except Exception:
                    original = None
                if original is not None:
                    # dibujar bounding boxes en la imagen
                    boxes = []
                    for ind in indicadores:
                        box = {
                            'nombre': ind.get('nombre', ''),
                            'x_min': ind.get('x_min', 0),
                            'x_max': ind.get('x_max', 0),
                            'y_min': ind.get('y_min', 0),
                            'y_max': ind.get('y_max', 0),
                        }
                        boxes.append(box)

                    preview = imagen_bboxes(original, boxes)
                    
                    # Mostrar imagen en contenedor con scroll
                    st.markdown('<div class="image-container">', unsafe_allow_html=True)
                    st.image(preview, use_column_width=False)
                    st.markdown('</div>', unsafe_allow_html=True)

                if not indicadores:
                    st.markdown("No se encontraron indicadores.")
                else:
                    rows = []
                    for ind in indicadores:
                        nombre = ind.get('nombre', '')
                        significado = ind.get('significado', '')
                        confianza = ind.get('confianza', None)
                        try:
                            conf_val = float(confianza)
                        except Exception:
                            conf_val = None
                        rows.append({"Indicador": nombre, "Descripción": significado, "Confianza": conf_val})
                    df = pd.DataFrame(rows)
                    if 'Confianza' in df.columns:
                        df['Confianza'] = df['Confianza'].round(2)
                    def style_dataframe(df):
                        return df.style.set_properties(**{'border-radius': '10px', 'border': '1px solid #ddd', 'margin-left': '20px',
                                      'text-align': 'center', 'background-color': "#ffffff", 'color': "#000000", 'height': '40px', 'font-family': 'Poppins'})
                    styled_df = style_dataframe(df)
                    st.dataframe(styled_df, use_container_width=True)
        else:
            st.markdown("<em>No se ha subido ningún archivo en el modal.</em>", unsafe_allow_html=True)
    
    # PASO 3: Exportar
    elif current_step == 3:
        st.write("Preparando exportación...")
    
    # Botones de navegación
    st.markdown("<br>", unsafe_allow_html=True)
    
    # En paso 2: mostrar Exportar y Finalizar con diseño especial
    if current_step == 2:
        col_back, col_exp, col_fin = st.columns([1, 1, 1])
        
        with col_back:
            if st.button("Atrás", key="modal_back", use_container_width=True):
                st.session_state['modal_step'] = current_step - 1
                st.rerun()
        
        with col_exp:
            if st.button("Exportar", key="modal_export", use_container_width=True):
                st.session_state['modal_step'] = 3
                st.rerun()
        
        with col_fin:
            if st.button("Finalizar", key="modal_finish", use_container_width=True, type="primary"):
                # Lógica para guardar y cerrar
                st.session_state['modal_step'] = 1
                st.session_state['modal_uploaded_file'] = None
                st.session_state['modal_indicadores'] = None
                st.rerun()
    else:
        # Para otros pasos: botón Atrás/Cancelar a la izquierda, Siguiente a la derecha
        col_back, col_spacer, col_next = st.columns([1, 1, 1])
        
        with col_back:
            if st.button("Atrás" if current_step > 1 else "Cancelar", key="modal_back", use_container_width=True):
                if current_step > 1:
                    st.session_state['modal_step'] = current_step - 1
                    st.rerun()
                else:
                    # Cancelar - limpiar y cerrar
                    st.session_state['modal_step'] = 1
                    st.session_state['modal_uploaded_file'] = None
                    st.session_state['modal_indicadores'] = None
                    st.rerun()
        
        with col_next:
            next_label = "Siguiente" if current_step < 3 else "Finalizar"
            next_disabled = current_step >= 3
            
            if st.button(next_label, disabled=next_disabled, key="modal_next", use_container_width=True, type="primary"):
                if current_step == 1:
                    if st.session_state.get('modal_uploaded_file') is None:
                        st.markdown("""
                        <div class="warning">
                            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4">
                                <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
                            </svg>
                            <span>Por favor, sube una imagen para continuar</span>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.session_state['modal_step'] = 2
                        st.rerun()
                elif current_step == 3:
                    # Lógica para finalizar
                    st.session_state['modal_step'] = 1
                    st.session_state['modal_uploaded_file'] = None
                    st.session_state['modal_indicadores'] = None
                    st.rerun()