import streamlit as st
import pandas as pd

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
    """Renderiza un popover para seleccionar el formato de exportación."""
        
    csv_data = selected_rows.to_csv(index=False).encode('utf-8-sig')
    
    st.write("Seleccione el formato de exportación:")
    
    st.download_button(
        label="Descargar como CSV",
        data=csv_data,
        file_name="historial_seleccion.csv",
        mime='text/csv; charset=utf-8',
        use_container_width=True
    )

    st.button("Exportar como PDF", disabled=True, use_container_width=True)
