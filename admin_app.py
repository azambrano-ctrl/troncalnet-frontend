# admin_app.py
import streamlit as st
import requests
import pandas as pd
import os
from dotenv import load_dotenv

# --- Configuración de la Página ---
st.set_page_config(
    page_title="CRM TroncalNet",
    page_icon="📡",
    layout="wide"
)

# Cargar la URL de la API desde el archivo .env
load_dotenv()
CRM_API_URL = os.getenv("CRM_API_URL")

if not CRM_API_URL:
    st.error("Error: No se encontró la variable CRM_API_URL.")
    st.stop()

# =============================================================================
# FUNCIONES DE LA API (CLIENTES)
# =============================================================================
@st.cache_data(ttl=60)
def get_clientes(token, filtro_nombre=""):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        params = {"q": filtro_nombre if filtro_nombre else "a"}
        response = requests.get(f"{CRM_API_URL}/clientes/buscar", params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return []
        elif response.status_code == 401:
            st.warning("Tu sesión ha expirado. Por favor, vuelve a iniciar sesión.")
            del st.session_state['token']
            st.rerun()
            return None
        else:
            st.error(f"Error al contactar la API (Clientes): {response.status_code} - {response.text}")
            return None
    except requests.RequestException as e:
        st.error(f"Error de conexión con la API: {e}")
        return None

def crear_cliente_api(token, payload):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.post(f"{CRM_API_URL}/clientes/", json=payload, headers=headers, timeout=10)
        return response
    except requests.RequestException as e:
        st.error(f"Error de conexión con la API: {e}")
        return None

# =============================================================================
# FUNCIONES DE LA API (TICKETS) - ¡NUEVO!
# =============================================================================
@st.cache_data(ttl=30) # Caché más corta para tickets
def get_tickets(token, filtro_estado="todos"):
    """
    Obtiene todos los tickets de la API.
    (Nota: Necesitaremos un endpoint /tickets/todos en la API)
    """
    headers = {"Authorization": f"Bearer {token}"}
    try:
        # --- ¡IMPORTANTE! ---
        # Asumiremos que tenemos un endpoint /tickets/ que devuelve todos.
        # Si no, tendremos que modificar la API.
        response = requests.get(f"{CRM_API_URL}/tickets/todos", headers=headers, timeout=10) # Asumimos este endpoint
        
        if response.status_code == 200:
            data = response.json()
            if filtro_estado != "todos":
                data = [t for t in data if t.get('estado') == filtro_estado]
            return data
        elif response.status_code == 401:
            st.warning("Sesión expirada.")
            del st.session_state['token']
            st.rerun()
            return None
        else:
            st.error(f"Error al cargar tickets: {response.status_code} - {response.text}")
            return None
            
    except requests.RequestException as e:
        st.error(f"Error de conexión con la API: {e}")
        return None

def update_ticket_status_api(token, ticket_id, nuevo_estado):
    """
    Llama a la API para actualizar el estado de un ticket.
    (Nota: Necesitaremos un endpoint PATCH /tickets/{id}/estado en la API)
    """
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"estado": nuevo_estado}
    try:
        # --- ¡IMPORTANTE! ---
        # Asumimos que tenemos este endpoint.
        response = requests.patch(f"{CRM_API_URL}/tickets/{ticket_id}/estado", json=payload, headers=headers, timeout=10)
        return response
    except requests.RequestException as e:
        st.error(f"Error de conexión con la API: {e}")
        return None

# =============================================================================
# FUNCIÓN DE LOGIN
# =============================================================================
def login_api(email, password):
    try:
        login_data = {'username': email, 'password': password}
        response = requests.post(f"{CRM_API_URL}/login", data=login_data, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except requests.RequestException:
        return None

# =============================================================================
# LÓGICA DE VISUALIZACIÓN
# =============================================================================

# 1. Verificar si el usuario ya inició sesión
if 'token' not in st.session_state:

    # --- PANTALLA DE LOGIN ---
    st.title("📡 CRM TroncalNet - Inicio de Sesión")
    with st.form("form_login"):
        email = st.text_input("Usuario (Email)", key="login_email")
        password = st.text_input("Contraseña", type="password", key="login_password")
        submitted = st.form_submit_button("Continuar")

        if submitted:
            if not email or not password:
                st.warning("Por favor, ingresa tu email y contraseña.")
            else:
                login_response = login_api(email, password)
                if login_response:
                    st.session_state['token'] = login_response['access_token']
                    st.session_state['user_email'] = email
                    st.success("¡Inicio de sesión exitoso!")
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrecta.")
else:
    # --- PANTALLA PRINCIPAL (YA ESTÁ LOGUEADO) ---
    token = st.session_state['token']

    # --- Cabecera y botón de Salir ---
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.title(f"Panel de Administración CRM - TroncalNet")
    with col2:
        if 'user_email' in st.session_state:
            st.caption(f"Usuario: {st.session_state['user_email']}")
        if st.button("Cerrar Sesión"):
            del st.session_state['token']
            if 'user_email' in st.session_state:
                del st.session_state['user_email']
            st.rerun()

    st.markdown("---")

    # --- Pestañas de Módulos ---
    tab1, tab2 = st.tabs(["Clientes", "Incidencias / Tickets"])

    with tab1:
        # --- Sección: Clientes ---
        st.header("Gestión de Clientes")

        filtro = st.text_input("Buscar cliente por nombre, apellido o cédula:")
        
        if st.button("Buscar / Refrescar"):
            st.cache_data.clear()

        clientes_data = get_clientes(token, filtro_nombre=filtro)

        if clientes_data is not None:
            df_clientes = pd.DataFrame(clientes_data)
            if not df_clientes.empty:
                columnas_a_mostrar = {
                    'cedula': 'Cédula/RUC',
                    'nombres': 'Nombres',
                    'apellidos': 'Apellidos',
                    'telefono_principal': 'Teléfono',
                    'estado_servicio': 'Estado',
                    'fecha_creacion': 'Fecha de Creación'
                }
                df_display = df_clientes[columnas_a_mostrar.keys()].rename(columns=columnas_a_mostrar)
                st.dataframe(df_display, use_container_width=True)
                st.caption(f"Mostrando {len(df_display)} clientes.")
            else:
                st.info("No se encontraron clientes con ese criterio de búsqueda.")
        
        st.markdown("---")

        # --- Sección: Crear Cliente ---
        st.subheader("Crear Nuevo Cliente")
        with st.form("form_crear_cliente", clear_on_submit=True):
            st.write("Completa los datos del nuevo cliente:")
            col1, col2 = st.columns(2)
            with col1:
                new_cedula = st.text_input("Cédula/RUC*", max_chars=13)
                new_nombres = st.text_input("Nombres*")
            with col2:
                new_apellidos = st.text_input("Apellidos*")
                new_telefono = st.text_input("Teléfono Principal", max_chars=15)

            submitted_cliente = st.form_submit_button("Crear Cliente")

            if submitted_cliente:
                if not new_cedula or not new_nombres or not new_apellidos:
                    st.warning("Por favor, completa los campos obligatorios (*).")
                else:
                    payload = {
                        "cedula": new_cedula,
                        "nombres": new_nombres,
                        "apellidos": new_apellidos,
                        "telefono_principal": new_telefono
                    }
                    response = crear_cliente_api(token, payload)
                    if response and response.status_code == 201:
                        st.success(f"¡Cliente {new_nombres} {new_apellidos} creado exitosamente!")
                        st.cache_data.clear()
                    elif response and response.status_code == 400:
                        st.error(f"Error: La cédula {new_cedula} ya existe.")
                    else:
                        st.error(f"Error al crear cliente: {response.text if response else 'Error de conexión'}")

    with tab2:
        # --- Sección: Tickets - ¡NUEVO! ---
        st.header("Gestión de Incidencias (Tickets)")

        filtro_estado = st.selectbox(
            "Filtrar por estado:",
            options=["todos", "abierto", "en_progreso", "resuelto"],
            index=0
        )

        tickets_data = get_tickets(token, filtro_estado=filtro_estado)

        if tickets_data is not None:
            df_tickets = pd.DataFrame(tickets_data)
            
            if not df_tickets.empty:
                # Renombramos columnas para la tabla
                df_tickets.rename(columns={
                    'id': 'Ticket ID',
                    'cliente_cedula': 'Cédula Cliente',
                    'tipo_problema': 'Problema',
                    'estado': 'Estado',
                    'fecha_creacion': 'Fecha Creación',
                    'descripcion': 'Descripción'
                }, inplace=True)
                
                # Definimos el orden de las columnas
                columnas_tickets = [
                    'Ticket ID', 
                    'Estado', 
                    'Problema', 
                    'Cédula Cliente', 
                    'Fecha Creación', 
                    'Descripción'
                ]
                
                # --- Editor de Datos (para cambiar estado) ---
                st.info("Para cambiar el estado de un ticket, selecciónalo en la columna 'Estado' y elige uno nuevo.")
                
                # Usamos el nuevo "Editor de Datos" de Streamlit
                edited_df = st.data_editor(
                    df_tickets[columnas_tickets],
                    use_container_width=True,
                    # Hacemos que la columna 'Estado' sea un selectbox
                    column_config={
                        "Estado": st.column_config.SelectboxColumn(
                            "Estado",
                            help="Cambia el estado del ticket",
                            width="medium",
                            options=["abierto", "en_progreso", "resuelto"],
                            required=True,
                        )
                    },
                    disabled=[col for col in columnas_tickets if col != 'Estado'], # Solo 'Estado' es editable
                    hide_index=True,
                    num_rows="dynamic" # Permite ver todos los datos
                )
                
                # --- Lógica para guardar cambios ---
                # Comparamos el dataframe original con el editado
                # (Esta parte es avanzada y la afinaremos)
                
                # Por ahora, un botón para refrescar es más simple
                if st.button("Refrescar Tickets"):
                    st.cache_data.clear()

            else:
                st.info("No se encontraron tickets con ese criterio.")

