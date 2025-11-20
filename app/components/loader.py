import streamlit as st
import time


def start_loader(flag_key: str = 'show_historial_loader'):
    """Muestra inmediatamente el overlay loader si el flag está activo.

    Devuelve un handle (dict) con `placeholder` y `start_time` que debe
    ser pasado a `stop_loader` cuando termine el trabajo pesado.
    Si el flag no está activo, devuelve None.
    """
    if not st.session_state.get(flag_key, False):
        return None

    loader_placeholder = st.empty()
    start_time = time.time()

    with loader_placeholder.container():
        st.markdown(
            """
<style>
    @keyframes loaderJump {
        0%, 60%, 100% { transform: translateY(0); }
        30% { transform: translateY(-12px); }
    }

    .historial-loader-overlay {
        position: fixed;
        top: var(--main-offset, 0px);
        left: var(--sidebar-width, 200px);
        width: calc(100vw - var(--sidebar-width, 200px));
        height: calc(100vh - var(--main-offset, 0px));
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        background: rgba(255, 255, 255, 0.92);
        z-index: 999999;
    }

    .historial-loader-content { text-align: center; display: flex; flex-direction: column; align-items: center; justify-content: center; }
    .historial-loader-text { font-family: 'Poppins', sans-serif; font-weight: 600; font-size: 20px; color: #333; margin-bottom: 20px; }
    .historial-loader-dots { display: flex; gap: 12px; justify-content: center; align-items: center; }
    .historial-loader-dots span { width: 16px; height: 16px; background: #FFC107; border-radius: 50%; display: inline-block; animation: loaderJump 0.8s infinite ease-in-out; }
    .historial-loader-dots span:nth-child(2) { animation-delay: 0.15s; }
    .historial-loader-dots span:nth-child(3) { animation-delay: 0.3s; }
</style>

<div class="historial-loader-overlay">
    <div class="historial-loader-content">
        <div class="historial-loader-text">Cargando...</div>
        <div class="historial-loader-dots">
            <span></span>
            <span></span>
            <span></span>
        </div>
    </div>
</div>

<script>
(function() {
    var overlay = document.querySelector('.historial-loader-overlay');
    if (!overlay) return;

    function positionLoader() {
        var sidebar = document.querySelector('[data-testid="stSidebar"]');

        if (sidebar) {
            var rect = sidebar.getBoundingClientRect();
            overlay.style.left = rect.width + "px";
            overlay.style.width = "calc(100vw - " + rect.width + "px)";
        } else {
            overlay.style.left = "300px";
            overlay.style.width = "calc(100vw - 300px)";
        }

        overlay.style.top = "0";
        overlay.style.height = "100vh";
        overlay.style.display = 'flex';
        overlay.style.alignItems = 'center';
        overlay.style.justifyContent = 'center';
    }

    positionLoader();
    setTimeout(positionLoader, 50);
    setTimeout(positionLoader, 100);
    setTimeout(positionLoader, 200);
    setTimeout(positionLoader, 300);
    window.addEventListener('resize', positionLoader);
})();
</script>
            """,
            unsafe_allow_html=True,
        )

    # Resetear el flag inmediatamente después de mostrarlo
    try:
        st.session_state[flag_key] = False
    except Exception:
        pass

    return {"placeholder": loader_placeholder, "start_time": start_time}


def stop_loader(handle, min_seconds: float = 2.0):
    """Detiene y limpia el loader mostrado por `start_loader`.

    Garantiza que el loader haya sido visible al menos `min_seconds`.
    """
    if not handle:
        return

    try:
        start_time = handle.get('start_time')
        placeholder = handle.get('placeholder')
        if start_time is None:
            try:
                placeholder.empty()
            except Exception:
                pass
            return

        elapsed = time.time() - start_time
        if elapsed < float(min_seconds):
            time.sleep(float(min_seconds) - elapsed)

        try:
            placeholder.empty()
        except Exception:
            pass
    except Exception:
        try:
            handle.get('placeholder').empty()
        except Exception:
            pass


def show_loader(flag_key: str = 'show_historial_loader', min_seconds: float = 2.0) -> None:
    """Compatibilidad: muestra el loader y espera `min_seconds` antes de limpiar.

    Implementado usando start_loader/stop_loader internamente.
    """
    h = start_loader(flag_key)
    stop_loader(h, min_seconds=min_seconds)
