from services.db import fetch_df
import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import base64
from decimal import Decimal
try:
    import numpy as np
except Exception:
    np = None
import datetime
import json
import os
import mimetypes
from services.gcs import get_image_data_uri


# Cached loader for indicador names used during export
@st.cache_data(ttl=3600, max_entries=1)
def load_indicadores_nombres():
    df = fetch_df("SELECT nombre FROM dbo.Indicador ORDER BY id_indicador ASC")
    if df is None or df.empty:
        return []
    try:
        return df['nombre'].tolist()
    except Exception:
        return []

   
def render_export_popover(info_evaluado=None, indicadores=None):
    def to_dataframe(obj):
        if obj is None:
            return pd.DataFrame()
        if isinstance(obj, pd.DataFrame):
            return obj.reset_index(drop=True)
        if isinstance(obj, pd.Series):
            return obj.to_frame().T.reset_index(drop=True)
        if isinstance(obj, dict):
            return pd.DataFrame([obj])
        if isinstance(obj, list):
            if len(obj) == 0:
                return pd.DataFrame()
        return pd.DataFrame(obj)

    df_info = to_dataframe(info_evaluado)

    indicadores_nombres = load_indicadores_nombres()

    indicadores_per_row = []
    if isinstance(indicadores, list):
        if not df_info.empty and len(indicadores) == len(df_info):
            indicadores_per_row = indicadores
        else:
            indicadores_per_row = [indicadores] * max(1, len(df_info))
    else:
        indicadores_per_row = [[]] * max(1, len(df_info))

    # Construir filas finales: por cada fila de info (o una fila vacía si no hay info), añadir columnas de indicadores
    rows_final = []
    if df_info.empty:
        rows_final = []
    else:
        for idx in range(len(df_info)):
            row = df_info.iloc[idx].to_dict()

            detected_names = set()
            try:
                inds = indicadores_per_row[idx] if idx < len(indicadores_per_row) else []
            except Exception:
                inds = []

            if isinstance(inds, list):
                for ind in inds:
                    if isinstance(ind, dict):
                        nombre = ind.get('nombre') or ind.get('Indicador') or ind.get('indicador')
                        if nombre:
                            detected_names.add(str(nombre))
                    else:
                        try:
                            detected_names.add(str(ind))
                        except Exception:
                            continue

            # Añadir columnas de indicadores (1/0 según presencia para esta fila)
            for name in indicadores_nombres:
                row[name] = 1 if name in detected_names else 0

            rows_final.append(row)

    selected_rows = pd.DataFrame(rows_final)

    try:
        if not selected_rows.empty:
            cols = list(selected_rows.columns)
            if 'Fecha de evaluación' in cols:
                if 'Fecha' in cols:
                    try:
                        selected_rows = selected_rows.drop(columns=['Fecha de evaluación']) 
                    except Exception:
                        pass
                else:
                    try:
                        selected_rows = selected_rows.rename(columns={'Fecha de evaluación': 'Fecha'}) 
                    except Exception:
                        pass
            # Prefer 'Nombre del evaluado' over a generic 'Nombre' column
            try:
                if 'Nombre del evaluado' in cols and 'Nombre' in cols:
                    selected_rows = selected_rows.drop(columns=['Nombre'])
                    # refresh cols to reflect changes
                    cols = list(selected_rows.columns)
            except Exception:
                pass
    except Exception:
        pass

    csv_bytes = selected_rows.to_csv(index=False).encode("utf-8-sig")
    csv_b64 = base64.b64encode(csv_bytes).decode("utf-8-sig")
    csv_href = f"data:text/csv;charset=utf-8-sig;base64,{csv_b64}"
    
    from datetime import datetime
    filename = f"historial_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv" 

    # Lista de opciones/indicadores para el dropdown
    column_options = selected_rows.columns.tolist() if not selected_rows.empty else [
        "Fecha", "Nombre", "Apellido", "Edad", "Sexo", "Estado civil", 
        "Escolaridad", "Ocupación", "Grupo"
    ]
    try:
        if 'ruta_imagen' in column_options:
            column_options = [c for c in column_options if c != 'ruta_imagen']
    except Exception:
        pass
    for n in indicadores_nombres:
        if n not in column_options:
            column_options.append(n)

    # === GENERAR HTML DE CHECKBOXES ===
    checkboxes_html = ""
    for i, col in enumerate(column_options):
        checkboxes_html += f"""
        <label class="checkbox-label">
            <input type="checkbox" 
                 class="column-checkbox" 
                 value="{col}" 
                 checked>
            <span class="checkbox-text">{col}</span>
        </label>
        """
        
    def make_serializable(o):
        if isinstance(o, Decimal):
            try:
                return float(o)
            except Exception:
                return str(o)
        if np is not None:
            try:
                if isinstance(o, (np.integer,)):
                    return int(o)
                if isinstance(o, (np.floating,)):
                    return float(o)
                if isinstance(o, np.ndarray):
                    return o.tolist()
            except Exception:
                pass
        try:
            if isinstance(o, pd.Timestamp):
                return o.isoformat()
        except Exception:
            pass
        try:
            if isinstance(o, datetime.datetime):
                return o.isoformat()
        except Exception:
            pass
        try:
            return str(o)
        except Exception:
            return None

    df_json = json.dumps(selected_rows.to_dict(orient='records'), default=make_serializable)
    
    pruebas_data = []
    if not df_info.empty:
        for idx in range(len(df_info)):
            dem = df_info.iloc[idx].to_dict()
            prueba_info = {
                'demograficos': dem,
                'indicadores': []
            }
            
            # Obtener indicadores para esta prueba
            try:
                inds = indicadores_per_row[idx] if idx < len(indicadores_per_row) else []
                if isinstance(inds, list):
                    for ind in inds:
                        if isinstance(ind, dict):
                            prueba_info['indicadores'].append(ind)
            except Exception:
                pass
                
            # intentar incrustar la imagen (si `ruta_imagen` está presente y el archivo existe)
            try:
                ruta = dem.get('ruta_imagen') or dem.get('ruta') or dem.get('image') or dem.get('imagen')
                if ruta:
                    data_url = None
                    # Si la ruta es un URI de GCS, intentar obtener un data URI usando la utilidad existente
                    try:
                        if isinstance(ruta, str) and ruta.strip().lower().startswith('gs://'):
                            data_url = get_image_data_uri(ruta)
                    except Exception:
                        data_url = None

                    # Si no obtuvimos data_url desde GCS, intentar como ruta local
                    if not data_url:
                        try:
                            if os.path.exists(ruta):
                                with open(ruta, 'rb') as f:
                                    b = f.read()
                                b64 = base64.b64encode(b).decode('utf-8')
                                mime = mimetypes.guess_type(ruta)[0] or 'image/jpeg'
                                data_url = f"data:{mime};base64,{b64}"
                        except Exception:
                            data_url = None

                    if data_url:
                        prueba_info['demograficos']['image_base64'] = data_url
            except Exception:
                pass

            pruebas_data.append(prueba_info)
    
    pruebas_json = json.dumps(pruebas_data, default=make_serializable)
        
    # Obtener fecha actual
    current_date = datetime.now().strftime("%d/%m/%Y %H:%M")
    pdf_filename = f"evaluaciones_psicologicas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    html = f"""
        <script>
        (function() {{
            if (parent.document.getElementById('st-export-modal')) return;

            // Función para cargar scripts dinámicamente
            function loadScript(src) {{
                return new Promise((resolve, reject) => {{
                    const script = parent.document.createElement('script');
                    script.src = src;
                    script.onload = resolve;
                    script.onerror = reject;
                    parent.document.head.appendChild(script);
                }});
            }}

            // Cargar librerías PDF
            Promise.all([
                loadScript('https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js'),
                loadScript('https://cdnjs.cloudflare.com/ajax/libs/jspdf-autotable/3.5.31/jspdf.plugin.autotable.min.js')
            ]).then(() => {{
                console.log('PDF libraries loaded successfully');
                initModal();
            }}).catch(err => {{
                console.error('Error loading PDF libraries:', err);
                alert('Error al cargar las librerías PDF. Por favor, intenta de nuevo.');
            }});

            function initModal() {{
                // Crear e inyectar estilos
                const style = parent.document.createElement('style');
                style.textContent = `
                    .checkbox-label {{
                        display: flex !important;
                        align-items: center !important;
                        padding: 8px !important;
                        cursor: pointer !important;
                        border-radius: 4px !important;
                        transition: background 0.2s !important;
                    }}
                    .checkbox-label:hover {{
                        background: #f8f9fa !important;
                    }}
                    .column-checkbox {{
                        margin-right: 10px !important;
                        width: 14px !important;
                        height: 14px !important;
                        cursor: pointer !important;
                        accent-color: #111 !important;
                    }}
                    .checkbox-text {{
                        font-size: 14px !important;
                        color: #333 !important;
                    }}
                    .select-title {{
                        font-family: 'Poppins', sans-serif !important;
                        font-size: 12px !important;
                        font-weight: 400 !important;
                        margin-top: 20px !important;
                        margin-bottom: 12px !important;
                        color: #333 !important;
                    }}
                    .checkboxes-container {{
                        max-height: 250px !important;
                        overflow-y: auto !important;
                        border: 1px solid #dee2e6 !important;
                        border-radius: 6px !important;
                        padding: 12px !important;
                        background: #fafafa !important;
                        margin-bottom: 24px !important;
                        display: grid !important;
                        grid-template-columns: 1fr 1fr !important;
                        gap: 4px !important;
                    }}
                    .checkboxes-container::-webkit-scrollbar {{
                        width: 8px !important;
                    }}
                    .checkboxes-container::-webkit-scrollbar-track {{
                        background: #f1f1f1 !important;
                        border-radius: 4px !important;
                    }}
                    .checkboxes-container::-webkit-scrollbar-thumb {{
                        background: #888 !important;
                        border-radius: 4px !important;
                    }}
                    .checkboxes-container::-webkit-scrollbar-thumb:hover {{
                        background: #555 !important;
                    }}
                    .select-all-container {{
                        margin-bottom: 12px !important;
                        padding: 8px !important;
                        background: #e9ecef !important;
                        border-radius: 4px !important;
                    }}
                    .export-buttons-container {{
                        display: grid !important;
                        grid-template-columns: 1fr 1fr !important;
                        gap: 16px !important;
                        margin-top: 24px !important;
                    }}
                    .export-button {{
                        width: 100% !important;
                        padding: 20px 16px !important;
                        border: none !important;
                        border-radius: 8px !important;
                        font-weight: 600 !important;
                        font-size: 16px !important;
                        cursor: pointer !important;
                        display: flex !important;
                        flex-direction: row !important;
                        align-items: center !important;
                        justify-content: flex-start !important;
                        gap: 12px !important;
                        transition: all 0.3s ease !important;
                        text-decoration: none !important;
                        color: #333 !important;
                        background: #f8f9fa !important;
                    }}
                    .export-button:hover {{
                        background: #FFE451 !important;
                        transform: translateY(-2px) !important;
                        box-shadow: 0 4px 12px rgba(255, 228, 81, 0.4) !important;
                    }}
                    .export-icon {{
                        width: 48px !important;
                        height: 48px !important;
                        display: flex !important;
                        align-items: center !important;
                        justify-content: center !important;
                        flex-shrink: 0 !important;
                    }}
                    .separator {{
                        width: 100% !important;
                        height: 1px !important;
                        background: #dee2e6 !important;
                        margin: 24px 0 !important;
                    }}
                    
                    @media (max-width: 640px) {{
                        .checkboxes-container {{
                            grid-template-columns: 1fr !important;
                        }}
                        .export-buttons-container {{
                            grid-template-columns: 1fr !important;
                        }}
                    }}
                `;
                parent.document.head.appendChild(style);

                const overlay = parent.document.createElement('div');
                overlay.id = 'st-export-modal';
                overlay.style.position = 'fixed';
                overlay.style.left = '0';
                overlay.style.top = '0';
                overlay.style.width = '100vw';
                overlay.style.height = '100vh';
                overlay.style.zIndex = '2147483647';
                overlay.style.display = 'flex';
                overlay.style.alignItems = 'center';
                overlay.style.justifyContent = 'center';

                const backdrop = parent.document.createElement('div');
                backdrop.style.position = 'absolute';
                backdrop.style.left = '0';
                backdrop.style.top = '0';
                backdrop.style.width = '100%';
                backdrop.style.height = '100%';
                backdrop.style.background = 'rgba(0,0,0,0.75)';
                backdrop.style.backdropFilter = 'blur(2px)';
                overlay.appendChild(backdrop);

                const modal = parent.document.createElement('div');
                modal.style.position = 'relative';
                modal.style.minWidth = '320px';
                modal.style.maxWidth = '700px';
                modal.style.width = '90%';
                modal.style.maxHeight = '90vh';
                modal.style.overflow = 'auto';
                modal.style.padding = '32px';
                modal.style.borderRadius = '12px';
                modal.style.background = '#ffffff';
                modal.style.boxShadow = '0 8px 32px rgba(0,0,0,0.4)';
                modal.style.zIndex = '2147483647';

                const closeBtn = parent.document.createElement('button');
                closeBtn.innerText = '×';
                closeBtn.setAttribute('aria-label','Cerrar');
                closeBtn.style.position = 'absolute';
                closeBtn.style.top = '12px';
                closeBtn.style.right = '16px';
                closeBtn.style.border = 'none';
                closeBtn.style.background = 'transparent';
                closeBtn.style.fontSize = '32px';
                closeBtn.style.cursor = 'pointer';
                closeBtn.style.lineHeight = '1';
                closeBtn.style.color = '#666';
                modal.appendChild(closeBtn);

                const title = parent.document.createElement('h3');
                title.innerText = 'Exportar Datos';
                title.style.marginTop = '0';
                title.style.marginBottom = '12px';
                title.style.fontSize = '16px';
                title.style.fontWeight = '700';
                modal.appendChild(title);

                // === SECCIÓN DE CHECKBOXES ===
                const indicadoresTitle = parent.document.createElement('div');
                indicadoresTitle.className = 'select-title';
                indicadoresTitle.innerText = 'Selecciona las columnas a exportar:';
                indicadoresTitle.style.fontSize = '8px';
                modal.appendChild(indicadoresTitle);
                
                // Botón seleccionar/deseleccionar todos
                const selectAllContainer = parent.document.createElement('div');
                selectAllContainer.className = 'select-all-container';
                const selectAllLabel = parent.document.createElement('label');
                selectAllLabel.style.display = 'flex';
                selectAllLabel.style.alignItems = 'center';
                selectAllLabel.style.cursor = 'pointer';
                selectAllLabel.style.fontWeight = '600';
                
                const selectAllCheckbox = parent.document.createElement('input');
                selectAllCheckbox.type = 'checkbox';
                selectAllCheckbox.id = 'select-all-checkbox';
                selectAllCheckbox.checked = true;
                selectAllCheckbox.style.marginRight = '10px';
                selectAllCheckbox.style.width = '14px';
                selectAllCheckbox.style.height = '14px';
                selectAllCheckbox.style.cursor = 'pointer';
                selectAllCheckbox.style.accentColor = '#111';
                
                const selectAllText = parent.document.createElement('span');
                selectAllText.style.fontSize = '14px';
                selectAllText.style.color = '#495057';
                selectAllText.innerText = 'Seleccionar todo';
                
                selectAllLabel.appendChild(selectAllCheckbox);
                selectAllLabel.appendChild(selectAllText);
                selectAllContainer.appendChild(selectAllLabel);
                modal.appendChild(selectAllContainer);
                
                const checkboxesContainer = parent.document.createElement('div');
                checkboxesContainer.className = 'checkboxes-container';
                checkboxesContainer.innerHTML = `{checkboxes_html}`;
                modal.appendChild(checkboxesContainer);
                
                // Funcionalidad de seleccionar/deseleccionar todos
                const columnCheckboxes = checkboxesContainer.querySelectorAll('.column-checkbox');
                
                selectAllCheckbox.addEventListener('change', function() {{
                    columnCheckboxes.forEach(cb => cb.checked = this.checked);
                }});
                
                columnCheckboxes.forEach(cb => {{
                    cb.addEventListener('change', function() {{
                        const allChecked = Array.from(columnCheckboxes).every(checkbox => checkbox.checked);
                        const noneChecked = Array.from(columnCheckboxes).every(checkbox => !checkbox.checked);
                        selectAllCheckbox.checked = allChecked;
                        selectAllCheckbox.indeterminate = !allChecked && !noneChecked;
                    }});
                }});

                // Almacenar los datos del DataFrame
                const fullData = {df_json};
                const allColumns = {json.dumps(column_options)};
                const pruebasData = {pruebas_json};

                // Contenedor de botones
                const buttonsContainer = parent.document.createElement('div');
                buttonsContainer.className = 'export-buttons-container';

                // Botón CSV con icono
                const csvBtn = parent.document.createElement('button');
                csvBtn.className = 'export-button';
                csvBtn.innerHTML = `
                    <div class="export-icon">
                        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" stroke="#4CAF50" d="M3.375 19.5h17.25m-17.25 0a1.125 1.125 0 0 1-1.125-1.125M3.375 19.5h7.5c.621 0 1.125-.504 1.125-1.125m-9.75 0V5.625m0 12.75v-1.5c0-.621.504-1.125 1.125-1.125m18.375 2.625V5.625m0 12.75c0 .621-.504 1.125-1.125 1.125m1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125m0 3.75h-7.5A1.125 1.125 0 0 1 12 18.375m9.75-12.75c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125m19.5 0v1.5c0 .621-.504 1.125-1.125 1.125M2.25 5.625v1.5c0 .621.504 1.125 1.125 1.125m0 0h17.25m-17.25 0h7.5c.621 0 1.125.504 1.125 1.125M3.375 8.25c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125m17.25-3.75h-7.5c-.621 0-1.125.504-1.125 1.125m8.625-1.125c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125m-17.25 0h7.5m-7.5 0c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125M12 10.875v-1.5m0 1.5c0 .621-.504 1.125-1.125 1.125M12 10.875c0 .621.504 1.125 1.125 1.125m-2.25 0c.621 0 1.125.504 1.125 1.125M13.125 12h7.5m-7.5 0c-.621 0-1.125.504-1.125 1.125M20.625 12c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125m-17.25 0h7.5M12 14.625v-1.5m0 1.5c0 .621-.504 1.125-1.125 1.125M12 14.625c0 .621.504 1.125 1.125 1.125m-2.25 0c.621 0 1.125.504 1.125 1.125m0 1.5v-1.5m0 0c0-.621.504-1.125 1.125-1.125m0 0h7.5" />
                        </svg>
                    </div>
                    <span style="font-size: 16px; font-weight: 600;">Exportar CSV</span>
                `;
                
                csvBtn.onclick = function(e) {{
                    e.preventDefault();
                    
                    // Obtener columnas seleccionadas
                    const selectedColumns = Array.from(columnCheckboxes)
                        .filter(cb => cb.checked)
                        .map(cb => cb.value);
                    
                    if (selectedColumns.length === 0) {{
                        alert('Por favor, selecciona al menos una columna para exportar.');
                        return;
                    }}
                    
                    // Filtrar datos solo con las columnas seleccionadas
                    const filteredData = fullData.map(row => {{
                        const filteredRow = {{}};
                        selectedColumns.forEach(col => {{
                            if (row.hasOwnProperty(col)) {{
                                filteredRow[col] = row[col];
                            }}
                        }});
                        return filteredRow;
                    }});
                    
                    // Generar CSV
                    let csv = selectedColumns.join(',') + '\\n';
                    filteredData.forEach(row => {{
                        const values = selectedColumns.map(col => {{
                            let val = row[col];
                            if (val === null || val === undefined) val = '';
                            val = String(val).replace(/"/g, '""');
                            if (val.includes(',') || val.includes('\\n') || val.includes('"')) {{
                                val = '"' + val + '"';
                            }}
                            return val;
                        }});
                        csv += values.join(',') + '\\n';
                    }});
                    
                    const blob = new Blob(['\uFEFF', csv], {{ type: 'text/csv;charset=utf-8;' }});
                    const url = URL.createObjectURL(blob);
                    const downloadLink = parent.document.createElement('a');
                    downloadLink.href = url;
                    downloadLink.download = '{filename}';
                    downloadLink.click();
                    URL.revokeObjectURL(url);
                }};
                buttonsContainer.appendChild(csvBtn);

                // Botón PDF
                const pdfBtn = parent.document.createElement('button');
                pdfBtn.className = 'export-button';
                pdfBtn.innerHTML = `
                    <div class="export-icon">
                        <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M12 6C10.8954 6 10 6.89543 10 8V40C10 41.1046 10.8954 42 12 42H36C37.1046 42 38 41.1046 38 40V15L28.5 6H12Z" fill="#E53935"/>
                            <path d="M28.5 6V13.5C28.5 14.6046 29.3954 15 30.5 15H38L28.5 6Z" fill="#B71C1C"/>
                            <text x="24" y="28" font-family="Arial, sans-serif" font-size="9" font-weight="bold" fill="white" text-anchor="middle">PDF</text>
                        </svg>
                    </div>
                    <span style="font-size: 16px; font-weight: 600;">Exportar PDF</span>
                `;
                
                pdfBtn.onclick = function() {{
                    try {{
                        const selectedColumns = Array.from(columnCheckboxes)
                            .filter(cb => cb.checked)
                            .map(cb => cb.value);
                        
                        if (selectedColumns.length === 0) {{
                            alert('Por favor, selecciona al menos una columna para exportar.');
                            return;
                        }}

                        if (typeof parent.window.jspdf === 'undefined') {{
                            alert('Error: La librería PDF no está cargada. Por favor, recarga la página e intenta de nuevo.');
                            return;
                        }}
                        
                        const {{ jsPDF }} = parent.window.jspdf;
                        const doc = new jsPDF({{
                            orientation: 'landscape',
                            unit: 'mm',
                            format: 'a4'
                        }});
                        
                        const primaryColor = [17, 17, 17];
                        const accentColor = [255, 228, 81];
                        const headerBg = [236, 240, 241];
                        
                        // Procesar cada prueba
                        pruebasData.forEach((prueba, index) => {{
                            if (index > 0) {{
                                doc.addPage();
                            }}
                            
                            const pageWidth = doc.internal.pageSize.width;
                            const pageHeight = doc.internal.pageSize.height;
                            const margin = 15;
                            
                                // Header: fondo blanco y texto negro (solicitado)
                                doc.setFillColor(255, 255, 255);
                                doc.rect(0, 0, pageWidth, 30, 'F');

                                doc.setTextColor(0, 0, 0);
                                doc.setFontSize(18);
                                doc.setFont(undefined, 'bold');
                                doc.text('PERSONA BAJO LA LLUVIA', pageWidth / 2, 14, {{ align: 'center' }});

                                doc.setFontSize(9);
                                doc.setFont(undefined, 'normal');
                                doc.text('Fecha de generación: {current_date}', pageWidth / 2, 22, {{ align: 'center' }});
                            
                            // Dividir página en dos columnas
                            const columnWidth = (pageWidth - 3 * margin) / 2;
                            const leftColumnX = margin;
                            const rightColumnX = margin + columnWidth + margin;
                            let currentY = 40;
                            
                            // === COLUMNA IZQUIERDA: IMAGEN DE LA PRUEBA ===
                            doc.setTextColor(0, 0, 0);
                            doc.setFontSize(12);
                            doc.setFont(undefined, 'bold');
                            doc.text('Imagen de la Prueba', leftColumnX, currentY);
                            
                            // Obtener datos demográficos
                            const demData = prueba.demograficos || {{}};
                            
                            // Intentar incrustar la imagen si está disponible en los datos
                            doc.setDrawColor(200, 200, 200);
                            doc.setLineWidth(0.5);
                            const imageY = currentY + 5;
                            const imageHeight = 140;
                            const imageData = demData.image_base64 || demData.image || demData.ruta_imagen;
                            
                            if (imageData && typeof imageData === 'string' && imageData.startsWith('data:')) {{
                                try {{
                                    const comma = imageData.indexOf(',');
                                    const header = imageData.substring(5, comma); // e.g. image/png;base64
                                    const mime = header.split(';')[0];
                                    const format = (mime.split('/')[1] || 'jpeg').toUpperCase();
                                    const b64 = imageData.substring(comma + 1);
                                    doc.addImage(b64, format, leftColumnX, imageY, columnWidth, imageHeight);
                                }} catch (e) {{
                                    // fallback: dibujar placeholder
                                    doc.rect(leftColumnX, imageY, columnWidth, imageHeight);
                                    doc.setFontSize(10);
                                    doc.setTextColor(150, 150, 150);
                                    doc.text('Imagen no disponible', leftColumnX + columnWidth / 2, imageY + imageHeight / 2, {{ align: 'center' }});
                                }}
                            }} else {{
                                // no hay imagen embebida, dibujar placeholder
                                doc.rect(leftColumnX, imageY, columnWidth, imageHeight);
                                doc.setFontSize(10);
                                doc.setTextColor(150, 150, 150);
                                doc.text('Imagen no disponible', leftColumnX + columnWidth / 2, imageY + imageHeight / 2, {{ align: 'center' }});
                            }}
                            
                            // === COLUMNA DERECHA: DATOS DEMOGRÁFICOS ===
                            doc.setTextColor(0, 0, 0);
                            doc.setFontSize(12);
                            doc.setFont(undefined, 'bold');
                            doc.text('Datos del Evaluado', rightColumnX, currentY);
                            
                            let rightY = currentY + 8;
                            doc.setFontSize(10);
                            doc.setFont(undefined, 'normal');
                            
                            const demoFields = [
                                {{ key: 'Nombre del evaluado', label: 'Nombre' }},
                                {{ key: 'Edad', label: 'Edad' }},
                                {{ key: 'Sexo', label: 'Sexo' }},
                                {{ key: 'Grupo', label: 'Grupo' }},
                                {{ key: 'Fecha', label: 'Fecha de evaluación' }}
                            ];
                            
                            demoFields.forEach(field => {{
                                if (selectedColumns.includes(field.key) || selectedColumns.includes(field.label)) {{
                                    const value = demData[field.key] || demData[field.label] || '-';
                                    doc.setFont(undefined, 'bold');
                                    doc.text(field.label + ':', rightColumnX, rightY);
                                    doc.setFont(undefined, 'normal');
                                    doc.text(String(value), rightColumnX + 50, rightY);
                                    rightY += 7;
                                }}
                            }});
                            
                            // Separador
                            rightY += 5;
                            doc.setDrawColor(...primaryColor);
                            doc.setLineWidth(0.5);
                            doc.line(rightColumnX, rightY, rightColumnX + columnWidth, rightY);
                            rightY += 10;
                            
                            // === RESULTADOS (DOS COLUMNAS: CAT1 izquierda, CAT2 derecha) ===
                            doc.setFontSize(12);
                            doc.setFont(undefined, 'bold');
                            doc.text('Resultados', rightColumnX, rightY);
                            rightY += 8;

                            if (prueba.indicadores && prueba.indicadores.length > 0) {{
                                // Agrupar indicadores por categoría (usar 'id_categoria' y 'categoria_nombre' si vienen)
                                const catMap = {{}};
                                prueba.indicadores.forEach(ind => {{
                                    const catId = (ind && ind.id_categoria !== undefined && ind.id_categoria !== null) ? String(ind.id_categoria) : '0';
                                    const catName = (ind && (ind.categoria_nombre || ind.categoria)) ? (ind.categoria_nombre || ind.categoria) : ('Categoría ' + catId);
                                    if (!catMap[catId]) catMap[catId] = {{ name: catName, indicadores: [] }};
                                    // Mostrar el 'significado' (oración) del indicador en lugar del nombre
                                    const significado = ind && (ind.significado || ind.descripcion || ind.descripcion_corta || ind.meaning || ind.nombre || ind.Indicador || ind.indicador);
                                    if (significado) catMap[catId].indicadores.push(String(significado));
                                }});

                                // Preparar dos sub-columnas dentro de la columna de resultados
                                const resColWidth = columnWidth;
                                const gutter = 8;
                                const resHalf = (resColWidth - gutter) / 2;
                                const resLeftX = rightColumnX;
                                const resRightX = rightColumnX + resHalf + gutter;
                                let leftY = rightY;
                                let rightColY = rightY;

                                const cat1 = catMap['1'] || {{ name: 'Categoría 1', indicadores: [] }};
                                const cat2 = catMap['2'] || {{ name: 'Categoría 2', indicadores: [] }};

                                // Títulos de cada categoría
                                doc.setFontSize(10);
                                doc.setFont(undefined, 'bold');
                                doc.setTextColor(...primaryColor);
                                const title1Lines = doc.splitTextToSize(cat1.name, resHalf - 4);
                                doc.text(title1Lines, resLeftX, leftY);
                                leftY += title1Lines.length * 5;

                                const title2Lines = doc.splitTextToSize(cat2.name, resHalf - 4);
                                doc.text(title2Lines, resRightX, rightColY);
                                rightColY += title2Lines.length * 5;

                                // Bullets de indicadores (solo nombres)
                                doc.setFont(undefined, 'normal');
                                doc.setTextColor(60, 60, 60);
                                for (let i = 0; i < cat1.indicadores.length; i++) {{
                                    if (leftY > pageHeight - 40) break;
                                    const text = '• ' + cat1.indicadores[i];
                                    const lines = doc.splitTextToSize(text, resHalf - 6);
                                    doc.text(lines, resLeftX + 4, leftY);
                                    leftY += lines.length * 4.5;
                                }}

                                for (let i = 0; i < cat2.indicadores.length; i++) {{
                                    if (rightColY > pageHeight - 40) break;
                                    const text = '• ' + cat2.indicadores[i];
                                    const lines = doc.splitTextToSize(text, resHalf - 6);
                                    doc.text(lines, resRightX + 4, rightColY);
                                    rightColY += lines.length * 4.5;
                                }}

                                // Avanzar el cursor al máximo de las dos columnas
                                rightY = Math.max(leftY, rightColY) + 6;
                            }} else {{
                                doc.setFont(undefined, 'normal');
                                doc.setTextColor(150, 150, 150);
                                doc.text('Sin resultados', rightColumnX, rightY);
                            }}
                            
                            // Footer
                            doc.setFontSize(8);
                            doc.setTextColor(128, 128, 128);
                            const pageNum = index + 1;
                            const totalPages = pruebasData.length;
                            doc.text(
                                `Página ${{pageNum}} de ${{totalPages}}`,
                                pageWidth / 2,
                                pageHeight - 10,
                                {{ align: 'center' }}
                            );
                            
                            doc.setFontSize(7);
                            doc.text(
                                'Documento confidencial - Uso exclusivo para fines clínicos',
                                pageWidth / 2,
                                pageHeight - 5,
                                {{ align: 'center' }}
                            );
                        }});
                        
                        doc.save('{pdf_filename}');
                    }} catch (error) {{
                        console.error('Error generando PDF:', error);
                        alert('Error al generar el PDF: ' + error.message);
                    }}
                }};
                buttonsContainer.appendChild(pdfBtn);

                modal.appendChild(buttonsContainer);
                overlay.appendChild(modal);
                parent.document.body.appendChild(overlay);

                // Ensure overlay stays on top
                const topKeeper = new MutationObserver(function(mutations) {{
                    if (!parent.document.getElementById('st-export-modal')) return;
                    try {{
                        if (parent.document.body.lastElementChild !== overlay) {{
                            parent.document.body.appendChild(overlay);
                        }}
                    }} catch (e) {{ }}
                }});
                topKeeper.observe(parent.document.body, {{ childList: true }});

                setTimeout(function() {{
                    try {{ if (parent.document.getElementById('st-export-modal')) parent.document.body.appendChild(overlay); }} catch(e){{}}
                }}, 50);

                closeBtn.onclick = function() {{
                    overlay.remove();
                    style.remove();
                    try {{ topKeeper.disconnect(); }} catch(e){{}}
                }};
                backdrop.onclick = function() {{
                    overlay.remove();
                    style.remove();
                    try {{ topKeeper.disconnect(); }} catch(e){{}}
                }};

                function onKey(e) {{
                    if (e.key === 'Escape') {{
                        overlay.remove();
                        style.remove();
                    }}
                }}
                parent.window.addEventListener('keydown', onKey);

                const observer = new MutationObserver(function() {{
                    if (!parent.document.getElementById('st-export-modal')) {{
                        parent.window.removeEventListener('keydown', onKey);
                        style.remove();
                        observer.disconnect();
                    }}
                }});
                observer.observe(parent.document.body, {{ childList: true }});
            }}
        }})();
        </script>
        """

    components.html(html, height=1)