import sys, os
from pathlib import Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from services.queries.q_inicio import GET_RECIENTES, GET_EVALUADOS_EXISTENTES
from services.db import fetch_df
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from components.loader import show_loader

def inicio():
    show_loader('show_inicio_loader', min_seconds=1.0)
    # ---------- CSS (externo) ----------
    _css_general = Path(__file__).parent.parent / 'assets' / 'general.css'
    _css_sidebar = Path(__file__).parent.parent / 'assets' / 'sidebar_component.css'
    _css_inicio = Path(__file__).parent.parent / 'assets' / 'inicio.css'
    
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

    # ---------- DIALOG: Aviso de privacidad (se muestra al abrir Inicio) ----------
    @st.dialog("Aviso de privacidad")
    def disclaimer_dialog():
        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("""
        <style>
        .stDialog button[aria-label="Close"],
        .stModal button[aria-label="Close"],
        [data-testid="stDialogCloseButton"],
        button[title="Close"],
        button[aria-label="Cerrar"],
        button[aria-label="close"] {
            display: none !important;
        }
        </style>
        """, unsafe_allow_html=True)

        # Ejecutar JS para bloquear clics fuera del diálogo y la tecla Escape mientras esté abierto
        components.html("""
        <script>
        (function(){
            function blockInteractions(){
                const dialog = document.querySelector('.stDialog, .stModal, [data-testid="stDialog"]');
                if(!dialog) return;

                document.addEventListener('click', function(e){
                    const openDlg = document.querySelector('.stDialog, .stModal, [data-testid="stDialog"]');
                    if(!openDlg) return;
                    if(!e.target.closest('.stDialog') && !e.target.closest('.stModal') && !e.target.closest('[data-testid="stDialog"]')){
                        e.stopImmediatePropagation();
                        e.preventDefault();
                    }
                }, true);

                // Bloquear Escape
                document.addEventListener('keydown', function(e){
                    const openDlg = document.querySelector('.stDialog, .stModal, [data-testid="stDialog"]');
                    if(!openDlg) return;
                    if(e.key === 'Escape'){
                        e.stopImmediatePropagation();
                        e.preventDefault();
                    }
                }, true);
            }

            const observer = new MutationObserver(blockInteractions);
            observer.observe(document.body, {childList: true, subtree: true});
            blockInteractions();
        })();
        </script>
        """, height=0)

        st.write("Bajo protesta de decir verdad, hago constar que cuento con las credenciales profesionales que me acreditan como Licenciado(a) en Psicología, ya que reconozco y entiendo que el uso de esta plataforma lo requiere.")
        st.markdown("<br>", unsafe_allow_html=True)

        st.checkbox("Confirmo que cuento con las credenciales profesionales", key="disclaimer_checkbox")

        if st.button(":material/check: Aceptar", use_container_width=True, type="primary", key="disclaimer_accept"):
                if st.session_state.get("disclaimer_checkbox", False):
                    st.session_state['disclaimer_accepted'] = True
                    st.session_state['disclaimer_error'] = False
                    st.rerun()
                else:
                    st.session_state['disclaimer_error'] = True
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        # Placeholder que aparece debajo del botón y ocupa todo el ancho
        msg_ph = st.empty()
        if st.session_state.get('disclaimer_error', False):
            msg_ph.warning("Debes marcar la casilla para aceptar el aviso de privacidad.")

    # Mostrar el disclaimer si no se ha aceptado aún
    try:
        if not st.session_state.get('disclaimer_accepted', False):
            disclaimer_dialog()
    except Exception:
        # En caso de error mostrando diálogo, forzar cierre de sesión por seguridad
        st.session_state["active_view"] = "salir"
        st.rerun()
    
    # ---------- DIÁLOGO SELECCIÓN EVALUADO ----------
    @st.dialog("Nueva evaluación")
    def dialog_seleccionar_evaluado():
        st.markdown("¿A qué evaluado deseas agregar el dibujo?")
        
        try:
            try:
                import services.auth as auth
                is_esp = auth.is_especialista()
            except Exception:
                is_esp = False

            if is_esp:
                user = st.session_state.get("user", {})
                id_usuario = user.get("id_usuario")
                try:
                    id_usuario = int(id_usuario)
                except Exception:
                    id_usuario = None

                if id_usuario is None:
                    df_evaluados = fetch_df(GET_EVALUADOS_EXISTENTES)
                else:
                    base_sql = GET_EVALUADOS_EXISTENTES
                    # Normalizar: quitar punto y coma/trailing whitespace antes de inyectar WHERE
                    base_stripped = base_sql.rstrip()
                    while base_stripped.endswith(';'):
                        base_stripped = base_stripped[:-1].rstrip()

                    # Insertar filtro WHERE antes de ORDER BY si existe
                    if "ORDER BY" in base_stripped.upper():
                        idx = base_stripped.upper().rfind("ORDER BY")
                        filtered_sql = base_stripped[:idx] + "\nWHERE id_usuario = @id_usuario\n" + base_stripped[idx:]
                    else:
                        filtered_sql = base_stripped + "\nWHERE id_usuario = @id_usuario"
                    df_evaluados = fetch_df(filtered_sql, {"id_usuario": id_usuario})
            else:
                df_evaluados = fetch_df(GET_EVALUADOS_EXISTENTES)

            if df_evaluados.empty:
                evaluado_options = ["No hay evaluados registrados"]
                ids_evaluados = []
            else:
                evaluado_options = df_evaluados['nombre_completo'].tolist()
                ids_evaluados = df_evaluados['id_evaluado'].tolist()
        except Exception:
            evaluado_options = ["Error al cargar evaluados"]
            ids_evaluados = []
        
        selected_evaluado = st.selectbox(
            "Selecciona un evaluado",
            evaluado_options,
            label_visibility="collapsed"
        )
        
        # Mostrar la opción de crear nuevo evaluado solo a admin o especialista
        try:
            import services.auth as auth
            can_create = auth.is_admin() or auth.is_especialista()
        except Exception:
            can_create = False

        if can_create:
            try:
                import services.auth as auth
                # Admin: abrir directamente el formulario de registrar (la asignación se gestiona dentro)
                if auth.is_admin():
                    if st.button(":material/add: Crear nuevo evaluado", type="secondary", use_container_width=True):
                        if 'assigned_id_usuario' in st.session_state:
                            try:
                                del st.session_state['assigned_id_usuario']
                            except Exception:
                                st.session_state['assigned_id_usuario'] = None
                        st.session_state["active_view"] = "registrar"
                        st.session_state["current_step"] = 1
                        st.session_state["already_registered"] = False
                        st.rerun()
                else:
                    # Especialista: crear evaluado y asignarlo a sí mismo
                    user = st.session_state.get("user", {})
                    uid = user.get("id_usuario")
                    if st.button(":material/add: Crear nuevo evaluado", type="secondary", use_container_width=True):
                        try:
                            st.session_state['assigned_id_usuario'] = int(uid)
                        except Exception:
                            st.session_state['assigned_id_usuario'] = uid
                        st.session_state["active_view"] = "registrar"
                        st.session_state["current_step"] = 1
                        st.session_state["already_registered"] = False
                        st.rerun()
            except Exception:
                pass
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Seleccionar", type="primary", use_container_width=True):
            if selected_evaluado not in ["No hay evaluados registrados", "Error al cargar evaluados"]:
                # Obtener el id del evaluado seleccionado
                idx = evaluado_options.index(selected_evaluado)
                id_evaluado = ids_evaluados[idx]
                
                st.session_state["id_evaluado"] = id_evaluado
                try:
                    df_assigned = fetch_df("SELECT id_usuario FROM Evaluado WHERE id_evaluado = :id", {"id": id_evaluado})
                    if not df_assigned.empty:
                        try:
                            assigned = df_assigned.at[0, "id_usuario"]
                            try:
                                assigned = int(assigned)
                            except Exception:
                                pass
                            st.session_state['assigned_id_usuario'] = assigned
                        except Exception:
                            st.session_state['assigned_id_usuario'] = None
                    else:
                        st.session_state['assigned_id_usuario'] = None
                except Exception:
                    st.session_state['assigned_id_usuario'] = None

                # Ir al paso 2 (evaluado ya registrado)
                st.session_state["already_registered"] = True
                st.session_state["active_view"] = "registrar"
                st.session_state["current_step"] = 2
                st.rerun()
        
    # ---------- LAYOUT ----------
    col1, col2 = st.columns([2, 1])
    try:
        if st.session_state.get('created_ok', False):
             st.markdown("""
                <div class="success">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" style="flex:0 0 14px;">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
                </svg>
                <span>Evaluación registrada correctamente</span>
                </div>
            """, unsafe_allow_html=True)
        st.session_state['created_ok'] = False
    except Exception:
        pass

    with col1:
        st.markdown('<div class="page-header">Evaluaciones</div>', unsafe_allow_html=True)
    
    with col1:
        # Render steps using a responsive grid: 2 columns on desktop, 1 column on mobile
        steps_html = """
        <div class="steps-grid">
            <div class="step-card">
                <h4>01<br>Registrar</h4>
                <p class="step-desc">Registra los datos de la persona a evaluar.</p>
            </div>
            <div class="step-card">
                <h4>02<br>Subir dibujo</h4>
                <p class="step-desc">Sube tu dibujo como archivo de imagen o desde una cámara.</p>
            </div>
            <div class="step-card">
                <h4>03<br>Resultados</h4>
                <p class="step-desc">Descubre los resultados del dibujo que subiste.</p>
            </div>
            <div class="step-card">
                <h4>04<br>Exportar</h4>
                <p class="step-desc">Descarga tus resultados en un documento CSV o PDF.</p>
            </div>
        </div>
        """
        st.markdown(steps_html, unsafe_allow_html=True)

    with col2:

        button_label = ":material/add_2: Nueva evaluación"
        if st.button(button_label, key="new_eval", type="primary"):
            dialog_seleccionar_evaluado()
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""<h5>Recientes</h5>""", unsafe_allow_html=True)

        try:
            import services.auth as auth
            is_esp = auth.is_especialista()
            is_o = auth.is_operador()
        except Exception:
            is_esp = False
            is_o = False

        # Operadores no tienen acceso a evaluaciones recientes
        if is_o:
            st.markdown("<p>No tienes acceso a las evaluaciones recientes.</p>", unsafe_allow_html=True)
        else:
            try:
                if is_esp:
                    user = st.session_state.get("user", {})
                    id_usuario = user.get("id_usuario")
                    try:
                        id_usuario = int(id_usuario)
                    except Exception:
                        id_usuario = None
                    if id_usuario is None:
                        recientes = pd.DataFrame()
                    else:
                        base_sql = GET_RECIENTES
                        if "ORDER BY" in base_sql.upper():
                            idx = base_sql.upper().rfind("ORDER BY")
                            filtered_sql = base_sql[:idx] + "\nWHERE e.id_usuario = @id_usuario\n" + base_sql[idx:]
                        else:
                            filtered_sql = base_sql + "\nWHERE e.id_usuario = @id_usuario"
                        recientes = fetch_df(filtered_sql, {"id_usuario": id_usuario})
                else:
                    recientes = fetch_df(GET_RECIENTES)
            except Exception:
                try:
                    recientes = fetch_df(GET_RECIENTES)
                except Exception:
                    recientes = pd.DataFrame()

            if recientes.empty:
                st.markdown("<p>No hay evaluaciones recientes.</p>", unsafe_allow_html=True)
            else:
                for _, r in recientes.iterrows():
                    id_prueba = r.get('id_prueba')
                    id_evaluado = r.get('id_evaluado')
                    nombre = r.get('nombre', '')
                    apellido = r.get('apellido', '')
                    fecha = r.get('fecha', '')

                    label = f"**{nombre} {apellido}**  \n{fecha}"
                    key = f"recent_btn_{id_prueba}"
                    
                    if st.button(label, key=key, type="secondary", use_container_width=True):
                        try:
                            st.session_state['open_prueba_id'] = int(id_prueba)
                        except Exception:
                            st.session_state['open_prueba_id'] = id_prueba

                        st.session_state['selected_evaluation_id'] = id_evaluado
                        # Venimos desde inicio, no desde ajustes
                        st.session_state['from_ajustes'] = False
                        st.session_state['active_view'] = 'individual'
                        st.rerun()

            # Mostrar 'Ver más' sólo a quienes tengan acceso al historial
            try:
                if not is_o:
                    if st.button("Ver más >", key="view_more", type="secondary", use_container_width=True):
                        st.session_state["active_view"] = "historial"
                        st.rerun()
            except Exception:
                pass
