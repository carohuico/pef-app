# Instrucciones para correr el proyecto Streamlit
Este proyecto utiliza Streamlit para crear una aplicación web interactiva. A continuación, se detallan los pasos necesarios para ejecutar el proyecto en tu entorno local.
## Requisitos previos
Antes de comenzar, asegúrate de tener instalado lo siguiente en tu sistema:
- Python 3.7 o superior
- pip (el gestor de paquetes de Python)
- Virtualenv (opcional, pero recomendado)
## Pasos para ejecutar el proyecto
1. **Clona el repositorio**  
   Abre una terminal y clona el repositorio del proyecto utilizando el siguiente comando:
   ```bash
   git clone <URL_DEL_REPOSITORIO>
   cd <NOMBRE_DEL_DIRECTORIO_CLONADO>
   ```

2. **Crea un entorno virtual (opcional)**
    Es recomendable crear un entorno virtual para aislar las dependencias del proyecto. Puedes hacerlo con el siguiente comando:
    ```bash
    python -m venv venv
    source venv/bin/activate  # En Windows usa `venv\Scripts\activate`
    ```
3. **Instala las dependencias**  
   Instala las dependencias necesarias utilizando pip y el archivo `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```
4. **Ejecuta la aplicación Streamlit**
    Inicia la aplicación Streamlit con el siguiente comando:
    ```bash
    streamlit run app.py
    ```
    Asegúrate de reemplazar `app.py` con el nombre del archivo principal de tu aplicación si es diferente.