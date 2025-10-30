import streamlit as st
from pathlib import Path
import base64
import json

def get_pruebas_data(id: str):
    """Obtiene las pruebas del evaluado"""
    pruebas = [
        {
            "id_prueba": 1,
            "nombre_archivo": "prueba1.png",
            "ruta_imagen": "dibujos\\1.jpg",
            "formato": "jpg",
            "fecha": "2023-01-01"
        },
        {
            "id_prueba": 2,
            "nombre_archivo": "prueba2.jpg",
            "ruta_imagen": "dibujos\\2.jpg",
            "formato": "jpg",
            "fecha": "2023-02-01"
        },
        {
            "id_prueba": 3,
            "nombre_archivo": "prueba3.jpg",
            "ruta_imagen": "dibujos\\3.jpg",
            "formato": "jpg",
            "fecha": "2023-03-01"
        },
        {
            "id_prueba": 4,
            "nombre_archivo": "prueba4.jpg",
            "ruta_imagen": "dibujos\\4.jpg",
            "formato": "jpg",
            "fecha": "2023-04-01"
        },
        {
            "id_prueba": 5,
            "nombre_archivo": "prueba5.jpg",
            "ruta_imagen": "dibujos\\5.jpg",
            "formato": "jpg",
            "fecha": "2023-05-01"
        }
    ]
    return pruebas

def encode_image_to_base64(image_path):
    """Convierte una imagen a base64 para incrustarla en HTML"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return None

def individual(info: object):
    id_val = info.get("id", "Desconocido") if info else "Desconocido"
    expediente = get_pruebas_data(id_val)
    
    # ---------- CONFIGURACIÓN ----------
    st.set_page_config(page_title="Rainly", layout="wide", initial_sidebar_state="auto")
    
    # Inicializar estado
    if 'current_image_index' not in st.session_state:
        st.session_state.current_image_index = 0
    
    # Header con botón de regreso - sin usar columnas que limitan el ancho
    st.markdown("""
    <style>
    .header-container {
        display: flex;
        align-items: center;
        gap: 16px;
        margin-bottom: 24px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Datos demográficos
    nombre = info.get("Nombre", "Desconocido") if info else "Desconocido"
    apellido = info.get("Apellido", "Desconocido") if info else "Desconocido"
    edad = info.get("Edad", "N/A") if info else "N/A"
    sexo = info.get("Sexo", "N/A") if info else "N/A"
    estado_civil = info.get("Estado civil", "N/A") if info else "N/A"
    escolaridad = info.get("Escolaridad", "N/A") if info else "N/A"
    
    current_index = st.session_state.current_image_index
    current_prueba = expediente[current_index]
    fecha = current_prueba.get("fecha", "N/A")
    
    # Preparar datos para el HTML
    # Construir data URIs para las imágenes locales para que el HTML pueda cargarlas
    images_data = []
    for prueba in expediente:
        img_rel = prueba.get('ruta_imagen', '')
        img_path = (Path(__file__).parent.parent / img_rel).resolve()
        b64 = encode_image_to_base64(str(img_path))
        if b64:
            mime = 'jpeg' if prueba.get('formato', '').lower() in ('jpg', 'jpeg') else prueba.get('formato', 'png')
            data_uri = f"data:image/{mime};base64,{b64}"
            prueba['_data_uri'] = data_uri
            images_data.append(data_uri)
        else:
            prueba['_data_uri'] = img_rel
            images_data.append(img_rel)

    imagen_actual = current_prueba.get('_data_uri', current_prueba.get('ruta_imagen'))
    
    # Generar HTML del carrusel con las miniaturas
    carousel_items_html = ""
    for i, prueba in enumerate(expediente):
        active = "active" if i == current_index else ""
        img_src = prueba.get('_data_uri', prueba.get('ruta_imagen'))
        carousel_items_html += f"""
        <div class=\"carousel-item {active}\" onclick=\"selectImage({i})\">
            <img src=\"{img_src}\" alt=\"Prueba {i+1}\" onerror=\"this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22120%22 height=%22120%22%3E%3Crect fill=%22%23ddd%22 width=%22120%22 height=%22120%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 text-anchor=%22middle%22 dy=%22.3em%22 fill=%22%23999%22%3E{i+1}%3C/text%3E%3C/svg%3E'\">
            <div class=\"carousel-item-number\">{i+1}</div>
        </div>
        """
    
    # HTML completo con JavaScript integrado
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
                margin-bottom: 20px;
                width: 100%;
                height: 300px;
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
                top: 20px;
                left: 20px;
                background: rgba(70, 70, 70, 0.45);
                backdrop-filter: blur(12px);
                -webkit-backdrop-filter: blur(12px);
                border-radius: 12px;
                padding: 8px 20px;
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.15);
                min-width: 200px;
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
            
            /* Botones de acción - Efecto Glass */
            .action-buttons {{
                position: absolute;
                bottom: 20px;
                right: 20px;
                display: flex;
                gap: 12px;
                z-index: 9999;
            }}
            
            .action-btn {{
                background: rgba(70, 70, 70, 0.45);
                backdrop-filter: blur(12px);
                -webkit-backdrop-filter: blur(12px);
                border-radius: 12px;
                padding: 12px;
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.15);
                width: 48px;
                height: 48px;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                transition: all 0.3s ease;
                color: #ffffff;
                font-size: 20px;
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
                font-size: 14px;
                text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
            }}
            
            .info-arrow {{
                transition: transform 0.3s ease;
                font-size: 12px;
                color: #ffffff;
            }}
            
            .info-card.expanded .info-arrow {{
                transform: rotate(90deg);
            }}
            
            .info-details {{
                font-size: 13px;
                line-height: 1.8;
                margin-top: 12px;
                padding-top: 12px;
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
                margin-bottom: 6px;
            }}
            
            .info-label {{
                font-weight: 500;
                color: #ffffff;
            }}
            
            /* Botones de navegación sobre la imagen */
            .nav-button {{
                position: absolute;
                top: 50%;
                transform: translateY(-50%);
                z-index: 10;
                background: rgba(255, 255, 255, 0.9);
                backdrop-filter: blur(10px);
                border: 2px solid rgba(0, 0, 0, 0.1);
                color: #333;
                width: 50px;
                height: 50px;
                border-radius: 50%;
                cursor: pointer;
                font-size: 24px;
                transition: all 0.2s;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            
            .nav-button:hover:not(:disabled) {{
                background: white;
                border-color: #FFC107;
                color: #FFC107;
                transform: translateY(-50%) scale(1.1);
            }}
            
            .nav-button:disabled {{
                opacity: 0.3;
                cursor: not-allowed;
            }}
            
            .nav-button.prev {{
                left: 20px;
            }}
            
            .nav-button.next {{
                right: 20px;
            }}
            
            /* Carrusel */
            .carousel-container {{
                background: white;
                border-radius: 12px;
                padding: 20px;
                width: 100%;
            }}
            
            .carousel-wrapper {{
                display: flex;
                align-items: center;
                gap: 12px;
                width: 100%;
            }}
            
            .carousel-button {{
                background: white;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                width: 40px;
                height: 40px;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                transition: all 0.2s;
                flex-shrink: 0;
                font-size: 18px;
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
                gap: 12px;
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
                width: 120px;
                height: 120px;
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
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 600;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="main-image-container">
                <div class="info-card" id="infoCard" onclick="toggleInfo()">
                    <div class="info-toggle">
                        <span>{nombre} {apellido}</span>
                        <span class="info-arrow">▶</span>
                    </div>
                    <div class="info-details">
                        <div class="info-row"><span class="info-label">Edad:</span> {edad}</div>
                        <div class="info-row"><span class="info-label">Sexo:</span> {sexo}</div>
                        <div class="info-row"><span class="info-label">Estado civil:</span> {estado_civil}</div>
                        <div class="info-row"><span class="info-label">Escolaridad:</span> {escolaridad}</div>
                    </div>
                </div>
                
                <div class="action-buttons">
                    <div class="action-btn" onclick="expandImage()" title="Expandir imagen">
                        ⛶
                    </div>
                    <div class="action-btn" onclick="exportImage()" title="Exportar imagen">
                        ⤓
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
            const totalImages = {len(expediente)};
            
            function toggleInfo() {{
                const card = document.getElementById('infoCard');
                card.classList.toggle('expanded');
            }}
            
            function expandImage() {{
                const mainImage = document.getElementById('mainImage');
                // Abrir imagen en nueva ventana/pestaña
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
            
            function updateImage(index) {{
                const mainImage = document.getElementById('mainImage');
                
                // Fade out
                mainImage.classList.add('fade-out');
                
                setTimeout(() => {{
                    currentIndex = index;
                    mainImage.src = images[index];
                    
                    // Fade in
                    mainImage.classList.remove('fade-out');
                    
                    // Actualizar miniaturas activas
                    document.querySelectorAll('.carousel-item').forEach((item, i) => {{
                        if (i === index) {{
                            item.classList.add('active');
                        }} else {{
                            item.classList.remove('active');
                        }}
                    }});
                    
                    // Actualizar estado de botones del carrusel
                    document.getElementById('prevBtn').disabled = (index === 0);
                    document.getElementById('nextBtn').disabled = (index === totalImages - 1);
                    
                    // Comunicar cambio a Streamlit
                    window.parent.postMessage({{
                        type: 'streamlit:setComponentValue',
                        key: 'current_image_index',
                        value: index
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
            
            // Inicializar estado de botones
            document.getElementById('prevBtn').disabled = (currentIndex === 0);
            document.getElementById('nextBtn').disabled = (currentIndex === totalImages - 1);
        </script>
    </body>
    </html>
    """
    
    # Renderizar HTML en un contenedor de ancho completo
    st.components.v1.html(html_content, height=500, width=800, scrolling=False)
    
    # Actualizar índice si cambió desde el HTML
    new_index = st.session_state.get('current_image_index', current_index)
    if new_index != current_index:
        st.session_state.current_image_index = new_index
        st.rerun()