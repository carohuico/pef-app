import streamlit as st

def agregar_dibujo(id_evaluado):
    st.html(f"""
    <div id="modal" class="modal">
        <div class="modal-content">
            <span class="close-button" onclick="closeModal()">&times;</span>
            <h2>Agregar Dibujo para Evaluado ID: {id_evaluado}</h2>
            <form id="drawing-form">
                <label for="drawing-data">Datos del Dibujo (JSON):</label><
                <textarea id="drawing-data" name="drawing-data" rows="10" cols="50"></textarea>
                <br><br>
                <button type="button" onclick="submitDrawing()">Guardar Dibujo</button>
            </form>
        </div>
    </div>
    <style>
        .modal {{
            display: block;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            overflow: auto;
            background-color: rgb(0,0,0);
            background-color: rgba(0,0,0,0.4);
        }}
        .modal-content {{
            background-color: #fefefe;
            margin: 15% auto;
            padding: 20px;
            border: 1px solid #888;
            width: 80%;
        }}
        .close-button {{
            color: #aaa;
            float: right;
            font-size: 28px;
            font-weight: bold;
        }}
        .close-button:hover,
        .close-button:focus {{
            color: black;
            text-decoration: none;
            cursor: pointer;
        }}
    </style>
    <script>
        function closeModal() {{
            document.getElementById("modal").style.display = "none";
        }}
        function submitDrawing() {{
            const drawingData = document.getElementById("drawing-data").value;
            // Aquí puedes agregar la lógica para enviar los datos del dibujo al backend
            alert("Dibujo guardado: " + drawingData);
            closeModal();
        }}
    </script>
    """)
    