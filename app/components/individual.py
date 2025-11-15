from services.queries.q_individual import GET_PRUEBAS_POR_EVALUADO, GET_RESULTADOS_POR_PRUEBA
from services.agregar_dibujo import agregar_dibujo
from services.db import fetch_df, get_engine
from services.queries.q_historial import ELIMINAR_PRUEBAS
from sqlalchemy import text
from components.historial import confirmar_eliminacion_pruebas
import pandas as pd
import streamlit as st
from pathlib import Path
import base64
import json


def get_info(id: str):
    """Obtiene la información demográfica del evaluado"""
    try:
        if id is None:
            return {}
        try:
            id_int = int(id)
        except Exception:
            return {}

        df = fetch_df("""
        SELECT
            e.nombre AS "Nombre",
            e.apellido AS "Apellido",
            CONVERT(VARCHAR(10), e.fecha_nacimiento, 120) AS fecha_nacimiento,
            e.sexo AS "Sexo",
            e.estado_civil AS "Estado civil",
            e.escolaridad AS "Escolaridad",
            e.ocupacion AS "Ocupación",
            g.nombre AS "Grupo",
            e.id_grupo
        FROM dbo.Evaluado e
        LEFT JOIN dbo.Grupo g ON e.id_grupo = g.id_grupo
        WHERE e.id_evaluado = :id_evaluado
        """, {"id_evaluado": id_int})

        if df is None or df.empty:
            return {}

        info = df.iloc[0].to_dict()

        # Compute Edad from fecha_nacimiento if available (expecting YYYY-MM-DD)
        try:
            fn = info.get('fecha_nacimiento')
            if fn and str(fn).strip():
                from datetime import datetime, date
                try:
                    bdate = datetime.strptime(str(fn), '%Y-%m-%d').date()
                    today = date.today()
                    edad = today.year - bdate.year - ((today.month, today.day) < (bdate.month, bdate.day))
                    info['Edad'] = edad
                except Exception:
                    info['Edad'] = 'N/A'
            else:
                info['Edad'] = 'N/A'
        except Exception:
            info['Edad'] = 'N/A'

    except Exception as e:
        st.error(f"Error fetching evaluado info: {e}")
        info = {}
    return info

def get_pruebas_data(id: str):
    print(f"Fetching pruebas for evaluado ID: {id}")
    """Obtiene las pruebas del evaluado"""
    try:
        if id is None:
            return []
        try:
            id_int = int(id)
        except Exception:
            return []

        df = fetch_df(GET_PRUEBAS_POR_EVALUADO, {"id_evaluado": id_int})
        if df is None or df.empty:
            return []

        expected_cols = ['id_prueba', 'nombre_archivo', 'ruta_imagen', 'formato', 'fecha', 'resultados_json']
        for c in expected_cols:
            if c not in df.columns:
                df[c] = ''

        try:
            df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce').dt.strftime('%Y-%m-%d')
            df['fecha'] = df['fecha'].fillna('')
        except Exception:
            df['fecha'] = df['fecha'].astype(str).fillna('')

        df['formato'] = df['formato'].astype(str).fillna('').str.replace('.', '', regex=False).str.lower()

        df['ruta_imagen'] = df['ruta_imagen'].astype(str).fillna('').str.replace('/', r'\\')

        def safe_int(x):
            try:
                return int(x)
            except Exception:
                return None

        df['id_prueba'] = df['id_prueba'].apply(safe_int)

        pruebas = df[expected_cols].to_dict(orient="records")
    except Exception as e:
        st.error(f"Error fetching pruebas data: {e}")
        pruebas = []
    return pruebas

def encode_image_to_base64(image_path):
    """Convierte una imagen a base64 para incrustarla en HTML"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception as e:
        print(f"Error al leer imagen {image_path}: {e}")
        return None

def individual(id_evaluado: str = None):
    
     # ---------- CSS (externo) ----------
    _css_individual = Path(__file__).parent.parent / 'assets' / 'individual.css'      
    
    try:
        with open(_css_individual, 'r', encoding='utf-8') as _f:
            st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error loading CSS: {e}")
    
    info = get_info(id_evaluado)
    expediente = get_pruebas_data(id_evaluado)
    
    try:
        open_prueba = st.session_state.pop('open_prueba_id', None)
        if open_prueba is not None and expediente:
            for idx, p in enumerate(expediente):
                try:
                    if p.get('id_prueba') is not None and int(p.get('id_prueba')) == int(open_prueba):
                        st.session_state.current_image_index = idx
                        break
                except Exception:
                    continue
    except Exception:
        pass

    # ---------- CONFIGURACIÓN ----------
    st.set_page_config(page_title="Rainly", layout="wide", initial_sidebar_state="auto")
    
    # Inicializar estado
    if 'current_image_index' not in st.session_state:
        st.session_state.current_image_index = 0
    if 'add_drawing' not in st.session_state:
        st.session_state['add_drawing'] = False
    st.session_state['_agregar_dialog_opened'] = False
    if '_agregar_dialog_open_requested' not in st.session_state:
        st.session_state['_agregar_dialog_open_requested'] = False
        
    #info
    info_obj = {
        "id_evaluado": id_evaluado,
        "Nombre": info.get("Nombre", "Desconocido"),
        "Apellido": info.get("Apellido", "Desconocido"),
        "Edad": info.get("Edad", "N/A"),
        "Sexo": info.get("Sexo", "N/A"),
        "Estado civil": info.get("Estado civil", "N/A"),
        "Escolaridad": info.get("Escolaridad", "N/A"),
        "Ocupación": info.get("Ocupación", "N/A"),
        "Grupo": info.get("Grupo", "N/A")
    }
    
    if not expediente:
        st.warning("No hay pruebas para este evaluado.")
        return

    current_index = st.session_state.current_image_index
    if current_index >= len(expediente):
        st.session_state.current_image_index = 0
        current_index = 0

    current_prueba = expediente[current_index]
    fecha = current_prueba.get("fecha", "N/A")
    
    # Preparar todos los datos del expediente
    images_data = []
    fechas_data = []
    ids_prueba = []
    resultados_data = []
    
    for prueba in expediente:
        img_rel = prueba.get('ruta_imagen', '')
        img_rel_clean = img_rel.lstrip('/').lstrip('\\')
        img_path = (Path(__file__).parent / img_rel_clean).resolve()
        b64 = encode_image_to_base64(str(img_path))
        if b64:
            mime = 'jpeg' if prueba.get('formato', '').lower() in ('jpg', 'jpeg') else prueba.get('formato', 'png') # Default to png
            data_uri = f"data:image/{mime};base64,{b64}" 
            prueba['_data_uri'] = data_uri 
            images_data.append(data_uri) 
        else:
            prueba['_data_uri'] = img_rel
            images_data.append(img_rel)
        
        fechas_data.append(prueba.get('fecha', 'N/A'))
        ids_prueba.append(prueba.get('id_prueba'))
        
        # Procesar resultados_json
        resultados_json = prueba.get('resultados_json', '')
        if resultados_json:
            try:
                # El JSON ya viene como string desde SQL Server
                if isinstance(resultados_json, str):
                    resultados_list = json.loads(resultados_json)
                else:
                    resultados_list = resultados_json
                resultados_data.append(resultados_list)
            except Exception:
                resultados_data.append([])
        else:
            resultados_data.append([])

    imagen_actual = current_prueba.get('_data_uri', current_prueba.get('ruta_imagen'))
    
    # Crear HTML del carrusel
    carousel_items_html = ""
    for i, prueba in enumerate(expediente):
        active = "active" if i == current_index else ""
        img_src = prueba.get('_data_uri', prueba.get('ruta_imagen'))
        carousel_items_html += f"""
        <div class="carousel-item {active}" onclick="selectImage({i})">
            <img src="{img_src}" alt="Prueba {i+1}" onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22120%22 height=%22120%22%3E%3Crect fill=%22%23ddd%22 width=%22120%22 height=%22120%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 text-anchor=%22middle%22 dy=%22.3em%22 fill=%22%23999%22%3E{i+1}%3C/text%3E%3C/svg%3E'">
            <div class="carousel-item-number">{i+1}</div>
        </div>
        """
    
    svg_expand = '''<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" width="20" height="20" stroke-width="2" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" d="M4 8V4h4M20 8v-4h-4M4 16v4h4M20 16v4h-4" />
</svg>'''
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                font-family: 'Poppins', sans-serif;
            }}
            
            html, body {{
                width: 100%;
                height: 100%;
                background: transparent;
                overflow-x: hidden;
            }}
            
            .container {{
                margin-top: 0px !important;
                width: 100%;
                min-width: 100%;
                padding: 0;
                display: flex;
                flex-direction: row;
                gap: 15px;
                height: 100vh;
                max-height: 700px;
            }}
            
            .left-column {{
                flex: 1;
                min-width: 0;
                display: flex;
                flex-direction: column;
                gap: 15px;
            }}
            
            .right-column {{
                flex: 1;
                min-width: 0;
                display: flex;
                flex-direction: column;
                overflow: hidden;
                background: white;
                border-radius: 12px;
            }}
            
            /* Contenedor principal de la imagen */
            .main-image-container {{
                position: relative;
                background: #dedede;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                width: 100%;
                height: calc(100% - 150px);
                min-height: 300px;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            
            .main-image {{
                width: 100%;
                height: 100%;
                object-fit: cover;
                transition: opacity 0.3s ease;
            }}
            
            .main-image.fade-out {{
                opacity: 0;
            }}
            
            /* Card de información demográfica - Efecto Glass */
            .info-card {{
                position: absolute;
                top: 15px;
                left: 15px;
                background: rgba(70, 70, 70, 0.45);
                backdrop-filter: blur(12px);
                -webkit-backdrop-filter: blur(12px);
                border-radius: 12px;
                padding: 8px 16px;
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.15);
                min-width: 180px;
                max-width: 250px;
                z-index: 9999;
                transition: all 0.3s ease;
                cursor: pointer;
            }}
            
            .info-card:hover {{
                background: rgba(70, 70, 70, 0.35);
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
                border: 1px solid rgba(255, 255, 255, 0.25);
            }}
            
            .date-card {{
                position: absolute;
                bottom: 15px;
                left: 15px;
                background: rgba(70, 70, 70, 0.45);
                backdrop-filter: blur(12px);
                -webkit-backdrop-filter: blur(12px);
                border-radius: 12px;
                padding: 8px 16px;
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.15);
                z-index: 9999;
                font-weight: 600;
                color: #ffffff;
                font-size: 14px;
                text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
            }}
            
            .action-buttons {{
                position: absolute;
                bottom: 15px;
                right: 15px;
                display: flex;
                gap: 10px;
                z-index: 9999;
            }}
            
            .action-btn {{
                background: rgba(70, 70, 70, 0.45);
                backdrop-filter: blur(12px);
                -webkit-backdrop-filter: blur(12px);
                border-radius: 10px;
                padding: 10px;
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.15);
                width: 42px;
                height: 42px;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                transition: all 0.3s ease;
                color: #ffffff;
                font-size: 18px;
            }}

            .action-btn svg {{
                width: 18px;
                height: 18px;
                display: block;
                filter: drop-shadow(0 2px 6px rgba(0,0,0,0.45));
            }}
            
            .action-btn:hover {{
                background: rgba(70, 70, 70, 0.55);
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
                border: 1px solid rgba(255, 255, 255, 0.25);
            }}
            
            .action-btn:active {{
                transform: translateY(0);
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
            }}
            
            .info-toggle {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                font-weight: 600;
                color: #ffffff;
                font-size: 13px;
                text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
            }}
            
            .info-arrow {{
                transition: transform 0.3s ease;
                font-size: 11px;
                color: #ffffff;
            }}
            
            .info-card.expanded .info-arrow {{
                transform: rotate(90deg);
            }}
            
            .info-details {{
                font-size: 12px;
                line-height: 1.8;
                margin-top: 10px;
                padding-top: 10px;
                border-top: 1px solid rgba(255, 255, 255, 0.2);
                max-height: 0;
                overflow: hidden;
                transition: max-height 0.3s ease, margin-top 0.3s ease, padding-top 0.3s ease;
                color: #f0f0f0;
            }}
            
            .info-card.expanded .info-details {{
                max-height: 400px;
            }}
            
            .info-card:not(.expanded) .info-details {{
                margin-top: 0;
                padding-top: 0;
                border-top: none;
            }}
            
            .info-row {{
                margin-bottom: 5px;
            }}
            
            .info-label {{
                font-weight: 500;
                color: #ffffff;
            }}
            
            /* Carrusel */
            .carousel-container {{
                background: white;
                border-radius: 12px;
                padding: 15px;
                width: 100%;
                height: 130px;
                flex-shrink: 0;
            }}
            
            .carousel-wrapper {{
                display: flex;
                align-items: center;
                gap: 10px;
                width: 100%;
            }}
            
            .carousel-button {{
                background: white;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                width: 36px;
                height: 36px;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                transition: all 0.2s;
                flex-shrink: 0;
                font-size: 16px;
                color: #333;
            }}
            
            .carousel-button:hover:not(:disabled) {{
                background: #f5f5f5;
                border-color: #999;
            }}
            
            .carousel-button:disabled {{
                opacity: 0.3;
                cursor: not-allowed;
            }}
            
            .carousel-items {{
                display: flex;
                gap: 10px;
                overflow-x: auto;
                scroll-behavior: smooth;
                padding: 4px;
                flex: 1;
            }}
            
            .carousel-items::-webkit-scrollbar {{
                height: 6px;
            }}
            
            .carousel-items::-webkit-scrollbar-track {{
                background: #f1f1f1;
                border-radius: 3px;
            }}
            
            .carousel-items::-webkit-scrollbar-thumb {{
                background: #888;
                border-radius: 3px;
            }}
            
            .carousel-item {{
                position: relative;
                flex-shrink: 0;
                width: 100px;
                height: 100px;
                border-radius: 8px;
                overflow: hidden;
                cursor: pointer;
                border: 3px solid transparent;
                transition: all 0.2s;
                background: #f5f5f5;
            }}
            
            .carousel-item:hover {{
                border-color: #ccc;
                transform: translateY(-2px);
            }}
            
            .carousel-item.active {{
                border-color: #FFC107;
                box-shadow: 0 4px 12px rgba(255, 193, 7, 0.3);
            }}
            
            .carousel-item img {{
                width: 100%;
                height: 100%;
                object-fit: cover;
            }}
            
            .carousel-item-number {{
                position: absolute;
                bottom: 4px;
                right: 4px;
                background: rgba(0, 0, 0, 0.7);
                color: white;
                padding: 2px 6px;
                border-radius: 4px;
                font-size: 10px;
                font-weight: 600;
            }}
            
            /* RESULTADOS */
            .resultados-header {{
                font-size: 16px;
                font-weight: 600;
                color: #444444;
                padding-left: 10px; 
                display: flex;
                align-items: center;
                flex-wrap: wrap;
                flex-shrink: 0;
                background: white;
            }}
            
            .resultados-container {{
                display: flex;
                flex-direction: column;
                gap: 16px;
                overflow-y: auto;
                padding: 20px;
                flex: 1;
                border-radius: 0 0 12px 12px;
            }}
            
            .resultados-container::-webkit-scrollbar {{
                width: 4px;
            }}
            
            .resultados-container::-webkit-scrollbar-track {{
                background: #f1f1f1;
                border-radius: 2px;
            }}
            
            .resultados-container::-webkit-scrollbar-thumb {{
                background: #888;
                border-radius: 2px;
            }}
            
            .resultados-container::-webkit-scrollbar-thumb:hover {{
                background: #555;
            }}
            
            .resultado-card {{
                background: white;
                border-radius: 12px;
                padding: 18px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                transition: all 0.3s ease;
                position: relative;
                overflow: visible;
                width: 100%;
                display: flex;
                flex-direction: column;
            }}
            
            
            .indicador-nombre {{
                font-size: 14px;
                font-weight: 600;
                color: #444444;
                margin-bottom: 10px;
                line-height: 1.4;
            }}
            
            .significado-texto {{
                font-size: 12px;
                color: #444444;
                line-height: 1.6;
                margin-bottom: 14px;
                white-space: normal;
                word-wrap: break-word;
            }}
            .confianza-container {{
                display: flex;
                align-items: center;
                gap: 12px;
                margin-top: auto;
            }}
            
            .confianza-label {{
                font-size: 12px;
                font-weight: 600;
                color: #444444;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                white-space: nowrap;
            }}
            
            .confianza-bar-wrapper {{
                flex: 1;
                height: 8px;
                background: #ecf0f1;
                border-radius: 4px;
                overflow: hidden;
            }}
            
            .confianza-bar {{
                height: 100%;
                border-radius: 4px;
                transition: width 0.6s ease;
                background: linear-gradient(90deg, #FFE451 0%, #FFD626 100%);
            }}
            
            .confianza-valor {{
                font-size: 14px;
                font-weight: 700;
                color: #111111;
                min-width: 50px;
                text-align: right;
                white-space: nowrap;
            }}
            
            .empty-state {{
                border-radius: 12px;
                padding: 60px 40px;
                text-align: center;
                color: black;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                margin: 20px;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100%;
            }}
            
            .empty-state-icon {{
                font-size: 64px;
                margin-bottom: 20px;
            }}
            
            .empty-state-text {{
                font-size: 20px;
                font-weight: 600;
                line-height: 1.4;
            }}
            
            @keyframes slideIn {{
                from {{
                    opacity: 0;
                    transform: translateY(20px);
                }}
                to {{
                    opacity: 1;
                    transform: translateY(0);
                }}
            }}
            
            .resultado-card {{
                animation: slideIn 0.4s ease forwards;
            }}
            
            
        </style>
    </head>
    <body>
        <div class="container">
            <!-- COLUMNA IZQUIERDA: Imagen y Carrusel -->
            <div class="left-column">
                <div class="main-image-container">
                    <div class="info-card" id="infoCard" onclick="toggleInfo()">
                        <div class="info-toggle">
                            <span>Datos personales</span>
                            <span class="info-arrow">▶</span>
                        </div>
                        <div class="info-details">
                            <div class="info-row"><span class="info-label">Edad: </span>{info_obj.get("Edad", "N/A")}</div>
                            <div class="info-row"><span class="info-label">Sexo:</span> {info_obj.get("Sexo", "N/A")}</div>
                            <div class="info-row"><span class="info-label">Estado civil:</span> {info_obj.get("Estado civil", "N/A")}</div>
                            <div class="info-row"><span class="info-label">Escolaridad:</span> {info_obj.get("Escolaridad", "N/A")}</div>
                            <div class="info-row"><span class="info-label">Ocupación:</span> {info_obj.get("Ocupación", "N/A")}</div>
                            <div class="info-row"><span class="info-label">Grupo:</span> {info_obj.get("Grupo", "N/A")}</div>
                        </div>
                        
                    </div>
                    <div class="date-card" id="dateCard">{fecha}</div>
                    
                        
                    <div class="action-buttons">
                        <div class="action-btn" onclick="expandImage()" title="Expandir imagen">
                            <span id="svgExpand">{svg_expand}</span>
                        </div>
                    </div>
                    
                    <img id="mainImage" class="main-image" src="{imagen_actual}" alt="Imagen principal" onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22800%22 height=%22500%22%3E%3Crect fill=%22%23ddd%22 width=%22800%22 height=%22500%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 text-anchor=%22middle%22 dy=%22.3em%22 fill=%22%23999%22 font-size=%2224%22%3EImagen no disponible%3C/text%3E%3C/svg%3E'">
                </div>
                
                <div class="carousel-container">
                    <div class="carousel-wrapper">
                        <button class="carousel-button" id="prevBtn" onclick="previousImage()">◀</button>
                        <div class="carousel-items" id="carouselItems">
                            {carousel_items_html}
                        </div>
                        <button class="carousel-button" id="nextBtn" onclick="nextImage()">▶</button>
                    </div>
                </div>
            </div>
            
            <!-- COLUMNA DERECHA: Resultados -->
            <div class="right-column">
                <div class="resultados-header">
                    <span>Resultados de la prueba</span>
                </div>
                <div class="resultados-container" id="resultadosContainer">
                    <!-- Los resultados se cargarán dinámicamente aquí -->
                </div>
            </div>
        </div>

        <!-- Modal para imagen ampliada (iframe) -->
        <div id="imageModal" class="image-modal">
            <div class="modal-backdrop" onclick="closeImageModal()"></div>
            <div class="modal-content" role="dialog" aria-modal="true" aria-label="Imagen ampliada">
                <button class="modal-close" onclick="closeImageModal()" aria-label="Cerrar">✕</button>
                <iframe id="imageIframe" src="" frameborder="0" style="width:100%; height:100%; border:0;" loading="lazy"></iframe>
            </div>
        </div>

        <style>
            .image-modal {{
                position: fixed;
                inset: 0;
                display: none;
                align-items: center;
                justify-content: center;
                z-index: 10000;
            }}
            .image-modal.show {{
                display: flex;
            }}
            .modal-backdrop {{
                position: absolute;
                inset: 0;
                background: rgba(255, 255, 255, 0.8);
                backdrop-filter: blur(4px);
            }}
            .modal-content {{
                position: relative;
                width: 92%;
                max-width: 1100px;
                height: 85vh;
                background: #fff;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 10px 40px rgba(0,0,0,0.4);
                z-index: 10001;
                display: flex;
            }}
            .modal-close {{
                position: absolute;
                top: 10px;
                right: 12px;
                z-index: 10002;
                background: rgba(255,255,255,0.9);
                border: none;
                font-size: 18px;
                color: #333;
                cursor: pointer;
                padding: 6px 8px;
                border-radius: 8px;
            }}
            .modal-close:hover {{
                background: rgba(255,255,255,1);
            }}
        </style>

        <script>
            let currentIndex = {current_index};
            const images = {json.dumps(images_data)};
            const fechas = {json.dumps(fechas_data)};
            const idsPrueba = {json.dumps(ids_prueba)};
            const resultadosData = {json.dumps(resultados_data)};
            const totalImages = {len(expediente)};
            
            function escapeHtml(text) {{
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML;
            }}
            
            function renderResultados(index) {{
                const container = document.getElementById('resultadosContainer');
                const fechaBadge = document.getElementById('fechaBadge');
                const fecha = fechas[index];
                const resultados = resultadosData[index];
                
                
                if (!resultados || resultados.length === 0) {{
                    container.innerHTML = `
                        <div class="empty-state">
                            <div class="empty-state-text">No hay resultados asociados a esta prueba</div>
                        </div>
                    `;
                    return;
                }}
                
                let html = '';
                resultados.forEach((resultado, idx) => {{
                    const nombre = escapeHtml(resultado.nombre_indicador || 'Indicador');
                    const significado = escapeHtml(resultado.significado || 'Sin descripción');
                    const confianza = resultado.confianza || 0;
                    const confianzaPct = Math.min(100, Math.max(0, confianza * 100));
                    const delay = idx * 0.05;
                    
                    html += `
                        <div class="resultado-card" style="animation-delay: ${{delay}}s;">
                            <div class="indicador-nombre">${{nombre}}</div>
                            <div class="significado-texto">${{significado}}</div>
                            <div class="confianza-container">
                                <span class="confianza-label">Confianza</span>
                                <div class="confianza-bar-wrapper">
                                    <div class="confianza-bar" style="width: ${{confianzaPct}}%;"></div>
                                </div>
                                <span class="confianza-valor">${{confianzaPct.toFixed(1)}}%</span>
                            </div>
                        </div>
                    `;
                }});
                
                container.innerHTML = html;
            }}
            
            function toggleInfo() {{
                const card = document.getElementById('infoCard');
                card.classList.toggle('expanded');
            }}
            
            function expandImage() {{
                const mainImage = document.getElementById('mainImage');
                openImageModal(mainImage.src);
            }}

            function openImageModal(src) {{
                try {{
                    const modal = document.getElementById('imageModal');
                    const iframe = document.getElementById('imageIframe');
                    const safeSrc = String(src).replace(/"/g, '&quot;');
                    const htmlDoc = `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>
                        html,body{{height:100%;margin:0;padding:0;}}
                        body{{display:flex;align-items:flex-start;justify-content:center;background:#111;overflow-y:auto;overflow-x:hidden;}}
                        img{{width:100%;height:auto;max-width:100%;display:block;}}
                    </style></head><body><img src="${{safeSrc}}" alt="Imagen ampliada"></body></html>`;

                    iframe.removeAttribute('src');
                    iframe.srcdoc = htmlDoc;
                    modal.classList.add('show');
                    document.body.style.overflow = 'hidden';
                }} catch (e) {{
                    console.error('Error opening image modal', e);
                    window.open(src, '_blank');
                }}
            }}

            function closeImageModal() {{
                try {{
                    const modal = document.getElementById('imageModal');
                    const iframe = document.getElementById('imageIframe');
                    iframe.src = 'about:blank';
                    modal.classList.remove('show');
                    document.body.style.overflow = '';
                }} catch (e) {{
                    console.error('Error closing image modal', e);
                }}
            }}

            // Cerrar modal con Escape
            document.addEventListener('keydown', function(e) {{
                if (e.key === 'Escape') {{
                    const modal = document.getElementById('imageModal');
                    if (modal && modal.classList.contains('show')) {{
                        closeImageModal();
                    }}
                }}
            }});
            
            function updateImage(index) {{
                const mainImage = document.getElementById('mainImage');
                const dateCard = document.getElementById('dateCard');
                
                mainImage.classList.add('fade-out');
                
                setTimeout(() => {{
                    currentIndex = index;
                    mainImage.src = images[index];
                    
                    mainImage.classList.remove('fade-out');
                    
                    document.querySelectorAll('.carousel-item').forEach((item, i) => {{
                        if (i === index) {{
                            item.classList.add('active');
                        }} else {{
                            item.classList.remove('active');
                        }}
                    }});
                    
                    // Actualizar resultados
                    renderResultados(index);
                    
                    // Centrar el thumbnail activo
                    try {{
                        const carouselItems = document.getElementById('carouselItems');
                        const activeItem = carouselItems.querySelectorAll('.carousel-item')[index];
                        if (activeItem && typeof activeItem.scrollIntoView === 'function') {{
                            activeItem.scrollIntoView({{ behavior: 'smooth', inline: 'center', block: 'nearest' }});
                        }}
                    }} catch (e) {{
                        console.error('Error scrolling thumbnail into view', e);
                    }}
                    
                    document.getElementById('prevBtn').disabled = (index === 0);
                    document.getElementById('nextBtn').disabled = (index === totalImages - 1);
                }}, 150);
            }}
            
            function selectImage(index) {{
                updateImage(index);
            }}
            
            function previousImage() {{
                if (currentIndex > 0) {{
                    updateImage(currentIndex - 1);
                }}
            }}
            
            function nextImage() {{
                if (currentIndex < totalImages - 1) {{
                    updateImage(currentIndex + 1);
                }}
            }}
            
            // Inicialización
            document.getElementById('prevBtn').disabled = (currentIndex === 0);
            document.getElementById('nextBtn').disabled = (currentIndex === totalImages - 1);
            
            // Renderizar resultados iniciales
            renderResultados(currentIndex);
            
            // Centrar thumbnail inicial
            try {{
                const carouselItems = document.getElementById('carouselItems');
                if (carouselItems) {{
                    const initial = carouselItems.querySelectorAll('.carousel-item')[currentIndex];
                    if (initial && typeof initial.scrollIntoView === 'function') {{
                        initial.scrollIntoView({{ behavior: 'auto', inline: 'center', block: 'nearest' }});
                    }}
                }}
            }} catch (e) {{
                console.error('Error centering initial thumbnail', e);
            }}
        </script>
    </body>
    </html>
    """
    
    # ---------- TÍTULO Y BOTÓN ----------
    col1, col2, col3 = st.columns([3,1,1])
    with col1:
        nombre = info_obj.get("Nombre", "Desconocido")
        apellido = info_obj.get("Apellido", "Desconocido")
        boton_regresar, col_nombre = st.columns([1, 6])
        with boton_regresar:
            button_label = ":material/arrow_back:"
            if st.button(button_label, use_container_width=True, type="tertiary"):
                if 'from_ajustes' in st.session_state and st.session_state['from_ajustes']:
                    st.session_state['from_ajustes'] = False
                    st.session_state['active_view'] = 'ajustes'
                else:
                    st.session_state['from_ajustes'] = False
                    st.session_state['active_view'] = 'historial'
                st.session_state['current_image_index'] = 0
                st.session_state['add_drawing'] = False
                st.rerun()
                
        with col_nombre:
            st.markdown(f'<div class="page-header">{nombre} {apellido}</div>', unsafe_allow_html=True)
    with col2:
        #eliminar 
        button_label = ":material/delete: Eliminar prueba"
        if st.button(button_label, use_container_width=True, type="secondary", key="btn_delete_drawing"):
            try:
                id_prueba = current_prueba.get('id_prueba')
            except Exception:
                id_prueba = None

            if id_prueba is None:
                st.warning(":material/warning: No se pudo identificar la prueba a eliminar.")
            else:
                try:
                    # Construir DataFrame con la fila seleccionada para pasar al diálogo
                    try:
                        selected_df = pd.DataFrame([
                            {
                                'id_prueba': id_prueba,
                                'Nombre del evaluado': f"{info_obj.get('Nombre','')} {info_obj.get('Apellido','')}",
                                'Fecha de evaluación': current_prueba.get('fecha', '')
                            }
                        ])
                    except Exception:
                        selected_df = pd.DataFrame([{'id_prueba': id_prueba}])

                    confirmar_eliminacion_pruebas(selected_df)
                except Exception as e:
                    st.error(f"Error abriendo diálogo de confirmación: {e}")
    with col3:
        button_label = ":material/add: Agregar dibujo"
        if st.button(button_label, use_container_width=True, type="primary", key="btn_add_drawing"):
            # Marcar la solicitud para abrir el diálogo; no llamar directamente
            # a `agregar_dibujo` aquí para evitar abrir el mismo diálogo dos veces
            # en una misma ejecución (Streamlit solo permite un diálogo abierto).
            st.session_state['add_drawing'] = True
            st.session_state['_agregar_dialog_open_requested'] = True


    
    if (
        st.session_state.get('add_drawing', False)
        and st.session_state.get('_agregar_dialog_open_requested', False)
        and not st.session_state.get('_agregar_dialog_opened', False)
    ):
        agregar_dibujo(info_obj)
        st.session_state['_agregar_dialog_opened'] = True

    colb1, col_main, colb2 = st.columns([.05, 6, .05])
    with col_main:
        st.components.v1.html(html_content, height=450, scrolling=False)