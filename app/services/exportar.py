import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import base64

def exportar_datos(selected_rows: pd.DataFrame, file_type: str, filename: str):
    if file_type == "csv":
        """Exporta los datos del DataFrame a un archivo CSV descargable."""
        csv = selected_rows.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="Descargar datos como CSV",
            data=csv,
            file_name=filename,
            mime='text/csv; charset=utf-8',
        )
    elif file_type == "pdf":
        """Exporta los datos del DataFrame a un archivo PDF descargable."""
        #TODO: Implementar exportación a PDF
        pass
    
def render_export_popover(selected_rows: pd.DataFrame):
    # Prepare CSV data as base64 so the injected HTML can provide a download link
    csv_bytes = selected_rows.to_csv(index=False).encode("utf-8-sig")
    csv_b64 = base64.b64encode(csv_bytes).decode("utf-8")
    csv_href = f"data:text/csv;charset=utf-8-sig;base64,{csv_b64}"
    filename = "historial_export.csv"
    
    # Lista de opciones/indicadores para el dropdown (simulación de columnas del DF principal)
    column_options = selected_rows.columns.tolist() if not selected_rows.empty else [
        "ID_Registro", "Nombre", "Apellido", "Edad", "Sexo", "Estado civil", 
        "Escolaridad", "Ocupación", "Grupo", "Ver más"
    ]
    
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
    
    # Convertir los datos del DataFrame a JSON para uso en JavaScript
    import json
    df_json = selected_rows.to_json(orient='records')
    
    # Obtener fecha actual
    from datetime import datetime
    current_date = datetime.now().strftime("%d/%m/%Y %H:%M")
    
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
              width: 18px !important;
              height: 18px !important;
              cursor: pointer !important;
              accent-color: #111 !important;
          }}
          .checkbox-text {{
              font-size: 14px !important;
              color: #333 !important;
          }}
          .select-title {{
              font-family: 'Poppins', sans-serif !important;
              font-size: 16px !important;
              font-weight: 600 !important;
              margin-top: 20px !important;
              margin-bottom: 12px !important;
              color: #333 !important;
          }}
          .checkboxes-container {{
              max-height: 300px !important;
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
        overlay.style.zIndex = '999999';
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
        modal.style.zIndex = '1000000';

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
        title.style.marginBottom = '24px';
        title.style.fontSize = '24px';
        title.style.fontWeight = '700';
        modal.appendChild(title);

        // === SECCIÓN DE CHECKBOXES ===
        const indicadoresTitle = parent.document.createElement('div');
        indicadoresTitle.className = 'select-title';
        indicadoresTitle.innerText = 'Selecciona las columnas a exportar:';
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
        selectAllCheckbox.style.width = '18px';
        selectAllCheckbox.style.height = '18px';
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

        // Separador
        const separator = parent.document.createElement('div');
        separator.className = 'separator';
        modal.appendChild(separator);

        // Almacenar los datos del DataFrame
        const fullData = {df_json};
        const allColumns = {json.dumps(column_options)};

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
          
          // Crear el enlace de descarga
          const blob = new Blob([csv], {{ type: 'text/csv;charset=utf-8;' }});
          const url = URL.createObjectURL(blob);
          const downloadLink = parent.document.createElement('a');
          downloadLink.href = url;
          downloadLink.download = '{filename}';
          downloadLink.click();
          URL.revokeObjectURL(url);
        }};
        buttonsContainer.appendChild(csvBtn);

        // Botón PDF con icono
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
            
            // Verificar que jsPDF esté disponible
            if (typeof parent.window.jspdf === 'undefined') {{
              alert('Error: La librería PDF no está cargada. Por favor, recarga la página e intenta de nuevo.');
              return;
            }}
            
            // Crear PDF con jsPDF
            const {{ jsPDF }} = parent.window.jspdf;
            const doc = new jsPDF({{
              orientation: selectedColumns.length > 6 ? 'landscape' : 'portrait',
              unit: 'mm',
              format: 'a4'
            }});
            
            const primaryColor = '#111'; // Azul médico
            const headerBg = '#ECF0F1'; // Gris claro

            doc.setFillColor(...primaryColor);
            doc.rect(0, 0, doc.internal.pageSize.width, 35, 'F');
            
            // Título
            doc.setTextColor(255, 255, 255);
            doc.setFontSize(20);
            doc.setFont(undefined, 'bold');
            doc.text('EXPORTACIÓN DE EXPEDIENTES', doc.internal.pageSize.width / 2, 15, {{ align: 'center' }});
            
            // Subtítulo
            doc.setFontSize(11);
            doc.setFont(undefined, 'normal');
            doc.text('Historial Clínico', doc.internal.pageSize.width / 2, 23, {{ align: 'center' }});
            
            // Fecha y hora
            doc.setFontSize(9);
            doc.text('Fecha de generación: {current_date}', doc.internal.pageSize.width / 2, 30, {{ align: 'center' }});
            
            // Información adicional
            doc.setTextColor(0, 0, 0);
            doc.setFontSize(10);
            doc.text(`Total de registros: ${{filteredData.length}}`, 14, 45);
            doc.text(`Columnas exportadas: ${{selectedColumns.length}}`, 14, 52);
            
            // Línea separadora
            doc.setDrawColor(...primaryColor);
            doc.setLineWidth(0.5);
            doc.line(14, 56, doc.internal.pageSize.width - 14, 56);
            
            // Preparar datos para la tabla
            const tableData = filteredData.map(row => 
              selectedColumns.map(col => {{
                let val = row[col];
                if (val === null || val === undefined) return '-';
                return String(val);
              }})
            );
            
            // Generar tabla con autoTable
            doc.autoTable({{
              head: [selectedColumns],
              body: tableData,
              startY: 62,
              theme: 'striped',
              headStyles: {{
                fillColor: primaryColor,
                textColor: [255, 255, 255],
                fontStyle: 'bold',
                fontSize: 9,
                halign: 'center',
                valign: 'middle',
                minCellHeight: 10
              }},
              bodyStyles: {{
                fontSize: 8,
                cellPadding: 3,
                valign: 'middle'
              }},
              alternateRowStyles: {{
                fillColor: headerBg
              }},
              styles: {{
                lineColor: [189, 195, 199],
                lineWidth: 0.1,
                overflow: 'linebreak'
              }},
              margin: {{ top: 62, left: 14, right: 14, bottom: 20 }},
              didDrawPage: function(data) {{
                // Pie de página en cada página
                const pageCount = doc.internal.getNumberOfPages();
                const pageNumber = doc.internal.getCurrentPageInfo().pageNumber;
                
                doc.setFontSize(8);
                doc.setTextColor(128, 128, 128);
                doc.text(
                  `Página ${{pageNumber}} de ${{pageCount}}`,
                  doc.internal.pageSize.width / 2,
                  doc.internal.pageSize.height - 10,
                  {{ align: 'center' }}
                );
                
                // Nota al pie
                doc.setFontSize(7);
                doc.text(
                  'Documento confidencial - Uso exclusivo para fines clínicos',
                  doc.internal.pageSize.width / 2,
                  doc.internal.pageSize.height - 5,
                  {{ align: 'center' }}
                );
              }}
            }});
            
            // Descargar el PDF
            doc.save('expediente.pdf');
          }} catch (error) {{
            console.error('Error generando PDF:', error);
            alert('Error al generar el PDF: ' + error.message);
          }}
        }};
        buttonsContainer.appendChild(pdfBtn);

        modal.appendChild(buttonsContainer);
        overlay.appendChild(modal);
        parent.document.body.appendChild(overlay);

        closeBtn.onclick = function() {{
          overlay.remove();
          style.remove();
        }};
        backdrop.onclick = function() {{
          overlay.remove();
          style.remove();
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