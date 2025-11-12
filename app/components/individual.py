from services.queries.q_individual import GET_PRUEBAS_POR_EVALUADO, GET_RESULTADOS_POR_PRUEBA
from services.agregar_dibujo import agregar_dibujo
from services.db import fetch_df
import pandas as pd
import streamlit as st
from pathlib import Path
import base64
import json

def get_info(id: str):
    """Obtiene la información demográfica del evaluado"""
    try:
        if id is None:
            return []
        try:
            id_int = int(id)
        except Exception:
            return []

        
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
            return []

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

        expected_cols = ['id_prueba', 'nombre_archivo', 'ruta_imagen', 'formato', 'fecha']
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
    # initialize add_drawing flag (do not show modal by default)
    if 'add_drawing' not in st.session_state:
        st.session_state['add_drawing'] = False
        
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
    resultados = current_prueba.get("resultados", [])
    
    images_data = []
    fechas_data = []
    for prueba in expediente:
        img_rel = prueba.get('ruta_imagen', '')
        
        # Remover el slash inicial si existe
        img_rel_clean = img_rel.lstrip('/').lstrip('\\')
        
        # porque las imágenes están en components/uploads/
        img_path = (Path(__file__).parent / img_rel_clean).resolve()
        b64 = encode_image_to_base64(str(img_path))
        if b64:
            mime = 'jpeg' if prueba.get('formato', '').lower() in ('jpg', 'jpeg') else prueba.get('formato', 'png')
            data_uri = f"data:image/{mime};base64,{b64}"
            prueba['_data_uri'] = data_uri
            images_data.append(data_uri)
        else:
            prueba['_data_uri'] = img_rel
            images_data.append(img_rel)
        
        fechas_data.append(prueba.get('fecha', 'N/A'))

    imagen_actual = current_prueba.get('_data_uri', current_prueba.get('ruta_imagen'))
    
    carousel_items_html = ""
    
    # Imágenes del carrusel
    for i, prueba in enumerate(expediente):
        active = "active" if i == current_index else ""
        img_src = prueba.get('_data_uri', prueba.get('ruta_imagen'))
        carousel_items_html += f"""
        <div class=\"carousel-item {active}\" onclick=\"selectImage({i})\">
            <img src=\"{img_src}\" alt=\"Prueba {i+1}\" onerror=\"this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22120%22 height=%22120%22%3E%3Crect fill=%22%23ddd%22 width=%22120%22 height=%22120%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 text-anchor=%22middle%22 dy=%22.3em%22 fill=%22%23999%22%3E{i+1}%3C/text%3E%3C/svg%3E'\">
            <div class=\"carousel-item-number\">{i+1}</div>
        </div>
        """
    
    
        svg_download = '''<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" width="20" height="20" stroke-width="2" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3" />
    </svg>'''
        # Use a clearer "expand" icon (corners outward) to ensure visibility
        svg_expand = '''<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" width="20" height="20" stroke-width="2" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" d="M4 8V4h4M20 8v-4h-4M4 16v4h4M20 16v4h-4" />
</svg>'''
        svg_add = '''<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" width="20" height="20" stroke-width="2" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5H4.5" />
</svg>'''

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
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
            }}
            
            /* Contenedor principal de la imagen */
            .main-image-container {{
                position: relative;
                background: #dedede;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                margin-bottom: 0;
                width: 100%;
                height: 60vh;
                min-height: 300px;
                max-height: 500px;
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
            
            /* Fecha - Efecto Glass */
            .date-card {{
                position: absolute;
                top: 15px;
                left: 50%;
                transform: translateX(-50%);
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
            
            /* Botones de acción - Efecto Glass */
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
                margin-top: 15px;
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
            
            /* Responsividad */
            @media (max-width: 768px) {{
                .main-image-container {{
                    height: 50vh;
                }}
                
                .info-card {{
                    top: 10px;
                    left: 10px;
                    padding: 6px 12px;
                    min-width: 150px;
                }}
                
                .date-card {{
                    top: 10px;
                    padding: 6px 12px;
                    font-size: 12px;
                }}
                
                .action-buttons {{
                    bottom: 10px;
                    right: 10px;
                    gap: 8px;
                }}
                
                .action-btn {{
                    width: 38px;
                    height: 38px;
                    padding: 8px;
                }}
                
                .action-btn svg {{
                    width: 16px;
                    height: 16px;
                }}
                
                .carousel-item {{
                    width: 80px;
                    height: 80px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
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
                    <div class="action-btn" onclick="exportImage()" title="Descargar imagen">
                        <span id="svgDownload">{svg_download}</span>
                    </div>
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
        
        <script>
            let currentIndex = {current_index};
            const images = {json.dumps(images_data)};
            const fechas = {json.dumps(fechas_data)};
            const totalImages = {len(expediente)};
            
            function toggleInfo() {{
                const card = document.getElementById('infoCard');
                card.classList.toggle('expanded');
            }}
            
            function expandImage() {{
                const mainImage = document.getElementById('mainImage');
                window.open(mainImage.src, '_blank');
            }}
            
            function exportImage() {{
                const mainImage = document.getElementById('mainImage');
                const link = document.createElement('a');
                link.href = mainImage.src;
                link.download = `imagen_${{currentIndex + 1}}.jpg`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }}
            
            function addDrawing() {{
                console.log("Adding drawing...");
                window.parent.postMessage({{
                    type: 'streamlit:setComponentValue',
                    value: {{ action: 'add_drawing', index: currentIndex }}
                }}, '*');
            }}
            
            function updateImage(index) {{
                const mainImage = document.getElementById('mainImage');
                const dateCard = document.getElementById('dateCard');
                
                mainImage.classList.add('fade-out');
                
                setTimeout(() => {{
                    currentIndex = index;
                    mainImage.src = images[index];
                    dateCard.textContent = fechas[index];
                    
                    mainImage.classList.remove('fade-out');
                    
                    document.querySelectorAll('.carousel-item').forEach((item, i) => {{
                        if (i === index) {{
                            item.classList.add('active');
                        }} else {{
                            item.classList.remove('active');
                        }}
                    }});
                    
                    document.getElementById('prevBtn').disabled = (index === 0);
                    document.getElementById('nextBtn').disabled = (index === totalImages - 1);
                    
                    // Notificar a Streamlit que cambió el índice para actualizar los resultados
                    window.parent.postMessage({{
                        type: 'streamlit:setComponentValue',
                        value: {{ action: 'image_changed', index: index }}
                    }}, '*');
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
            
            document.getElementById('prevBtn').disabled = (currentIndex === 0);
            document.getElementById('nextBtn').disabled = (currentIndex === totalImages - 1);
        </script>
    </body>
    </html>
    """
    # ---------- TÍTULO Y BOTÓN DE FILTROS ----------
    col1, col2 = st.columns([3, 1])
    with col1:
        nombre=info_obj.get("Nombre", "Desconocido")
        apellido=info_obj.get("Apellido", "Desconocido")
        boton_regresar, col_nombre = st.columns([1, 8])
        with boton_regresar:
            #boton de regresar
            button_label = ":material/arrow_back:"
            if st.button(button_label, use_container_width=True, type="secondary"):
                #regresar a ajustes si vengo de ajustes
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
        button_label = ":material/add: Agregar dibujo"
        if st.button(button_label, use_container_width=True, type="primary"):
            agregar_dibujo(info_obj)
            st.session_state['add_drawing'] = True

    # ---------- LAYOUT 50/50: IMAGEN Y RESULTADOS ----------
    col_imagen, col_resultados = st.columns([1, 1], gap="medium")
    
    with col_imagen:
        # Renderizar el HTML con el carrusel y la imagen
        component_key = f"individual_carousel_{id_evaluado or 'none'}"
        component_value = st.components.v1.html(html_content, height=580, scrolling=False)

        # Detectar cambios en el índice desde el componente HTML
        # Usar `is not None` porque `0` es un valor válido (primer índice) y es falsy
        if component_value is not None:
            # Puede llegar un dict { action, index } o un número (index)
            if isinstance(component_value, dict):
                action = component_value.get('action')
                if action in ('image_changed', 'image_select'):
                    try:
                        new_index = int(component_value.get('index', current_index))
                    except Exception:
                        new_index = current_index
                    if new_index != st.session_state.current_image_index:
                        st.session_state.current_image_index = new_index
                        st.rerun()
                elif action == 'add_drawing':
                    # activar modal/flag para agregar dibujo
                    st.session_state['add_drawing'] = True
                    try:
                        idx = int(component_value.get('index', st.session_state.current_image_index))
                    except Exception:
                        idx = st.session_state.current_image_index
                    if idx != st.session_state.current_image_index:
                        st.session_state.current_image_index = idx
                    st.rerun()
            else:
                # Si viene un número simple (por compatibilidad), usarlo como índice
                try:
                    new_index = int(component_value)
                    if new_index != st.session_state.current_image_index:
                        st.session_state.current_image_index = new_index
                        st.rerun()
                except Exception:
                    # ignore non-integer payloads
                    pass
    
    # Mostrar la fecha de la prueba seleccionada (fuera del HTML) para asegurar que
    # la UI de Streamlit refleje el cambio cuando se actualice el índice.
    try:
        idx_display = st.session_state.get('current_image_index', current_index)
        if expediente and 0 <= idx_display < len(expediente):
            fecha_display = expediente[idx_display].get('fecha', 'N/A')
        else:
            fecha_display = 'N/A'
    except Exception:
        fecha_display = 'N/A'

    with col_resultados:
        st.markdown(f"**Fecha seleccionada:** {fecha_display}")
        # ---------- TABLA DE RESULTADOS POR PRUEBA ----------
        try:
            id_prueba = current_prueba.get('id_prueba')
            if id_prueba is not None:
                try:
                    # cada que se cambia la imagen, se cargan los resultados de la prueba actual
                    df_resultados = fetch_df(GET_RESULTADOS_POR_PRUEBA, {"id_prueba": id_prueba})
                except Exception:
                    df_resultados = None

                if df_resultados is None or df_resultados.empty:
                    st.info("No hay resultados asociados a esta prueba.")
                else:
                    # Preparar dataframe para mostrar solo: nombre_indicador, significado, confianza
                    try:
                        df_show = df_resultados.copy()
                        
                        # Normalizar confianza
                        if 'confianza' in df_show.columns:
                            df_show['confianza'] = pd.to_numeric(df_show['confianza'], errors='coerce').round(3)
                        
                        # Seleccionar solo las columnas deseadas
                        cols_display = []
                        if 'nombre_indicador' in df_show.columns:
                            cols_display.append('nombre_indicador')
                        if 'significado' in df_show.columns:
                            cols_display.append('significado')
                        if 'confianza' in df_show.columns:
                            cols_display.append('confianza')
                        
                        if cols_display:
                            st.markdown("### Resultados por prueba")
                            # Configurar las columnas para mejor visualización
                            column_config = {}
                            if 'nombre_indicador' in cols_display:
                                column_config['nombre_indicador'] = st.column_config.TextColumn(
                                    "Indicador",
                                    width="small"
                                )
                            if 'significado' in cols_display:
                                column_config['significado'] = st.column_config.TextColumn(
                                    "Significado",
                                    width="small"
                                )
                            if 'confianza' in cols_display:
                                column_config['confianza'] = st.column_config.NumberColumn(
                                    "Confianza",
                                    format="%.3f",
                                    width="small"
                                )
                            
                            st.dataframe(
                                df_show[cols_display].reset_index(drop=True), 
                                use_container_width=True, 
                                height=350,
                                column_config=column_config,
                                hide_index=True
                            )
                        else:
                            st.warning("No se encontraron las columnas esperadas en los resultados.")
                    except Exception as e:
                        st.error(f"Error preparando la tabla de resultados: {e}")
            else:
                st.info("Selecciona una prueba para ver sus resultados.")
        except Exception as e:
            st.error(f"Error al cargar los resultados: {e}")

    new_index = st.session_state.get('current_image_index', current_index)
    if new_index != current_index:
        st.session_state.current_image_index = new_index
        
        st.rerun()