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

# --- Funciones de la API (Panel Principal) ---
# (Estas se usarán DESPUÉS de iniciar sesión)

@st.cache_data(ttl=60)
def get_clientes(token, filtro_nombre=""):
    """
    Obtiene todos los clientes de la API, usando un token de autenticación.
    """
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # (Ajuste) Si el filtro está vacío, buscamos la 'a' para traer resultados
        params = {"q": filtro_nombre if filtro_nombre else "a"}
        response = requests.get(f"{CRM_API_URL}/clientes/buscar", params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return []
        elif response.status_code == 401: # Token expiró o es inválido
            st.warning("Tu sesión ha expirado. Por favor, vuelve a iniciar sesión.")
            del st.session_state['token'] # Borra el token para forzar relogin
            st.rerun()
            return None
        else:
            st.error(f"Error al contactar la API (Clientes): {response.status_code}")
            return None
            
    except requests.RequestException as e:
        st.error(f"Error de conexión con la API: {e}")
        return None

def crear_cliente_api(token, payload):
    """
    Llama a la API para crear un nuevo cliente.
    """
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.post(f"{CRM_API_URL}/clientes/", json=payload, headers=headers, timeout=10)
        return response
    except requests.RequestException as e:
        st.error(f"Error de conexión con la API: {e}")
        return None

# --- Función de Login ---
def login_api(email, password):
    """
    Llama al endpoint /login de la API.
    """
    try:
        # FastAPI espera los datos de login como 'form-data', no JSON
        login_data = {
            'username': email,
            'password': password
        }
        response = requests.post(f"{CRM_API_URL}/login", data=login_data, timeout=10)
        
        if response.status_code == 200:
            return response.json() # Devuelve {"access_token": "...", "token_type": "bearer"}
        else:
            return None
            
    except requests.RequestException:
        return None

# --- LÓGICA DE VISUALIZACIÓN ---

# 1. Verificar si el usuario ya inició sesión (revisando la memoria de la sesión)
if 'token' not in st.session_state:

    # --- PANTALLA DE LOGIN ---
    st.title("📡 CRM TroncalNet - Inicio de Sesión")
    
    with st.form("form_login"):
        email = st.text_input("Usuario (Email)", key="login_email")
        password = st.text_input("Contraseña", type="password", key="login_password")
        
        # (Opcional) "Crear cuenta"
        # st.caption("[Crear cuenta](#)") # (Descomentar si quieres un enlace)

        submitted = st.form_submit_button("Continuar")

        if submitted:
            if not email or not password:
                st.warning("Por favor, ingresa tu email y contraseña.")
            else:
                login_response = login_api(email, password)
                
                if login_response:
                    # ¡Éxito! Guardamos el token en la memoria y recargamos
                    st.session_state['token'] = login_response['access_token']
                    st.session_state['user_email'] = email
                    st.success("¡Inicio de sesión exitoso!")
                    st.rerun() # Recarga la página
                else:
                    st.error("Usuario o contraseña incorrecta.")
else:
    # --- PANTALLA PRINCIPAL (YA ESTÁ LOGUEADO) ---
    
    # 1. Obtener el token guardado
    token = st.session_state['token']

    # --- Cabecera y botón de Salir ---
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.title(f"Panel de Administración CRM - TroncalNet")
    with col2:
        # Mostramos el email del usuario logueado
        if 'user_email' in st.session_state:
            st.caption(f"Usuario: {st.session_state['user_email']}")
        # Botón de Cerrar Sesión
        if st.button("Cerrar Sesión"):
            del st.session_state['token'] # Borra el token
            if 'user_email' in st.session_state:
                del st.session_state['user_email']
            st.rerun() # Recarga la página (volverá al login)

    st.markdown("---")

    # --- Sección: Clientes ---
    st.header("Gestión de Clientes")

    filtro = st.text_input("Buscar cliente por nombre, apellido o cédula:")
    
    if st.button("Buscar / Refrescar"):
        st.cache_data.clear()

    # Le pasamos el token a la función
    clientes_data = get_clientes(token, filtro_nombre=filtro)

    if clientes_data is not None:
        df = pd.DataFrame(clientes_data)
        if not df.empty:
            columnas_a_mostrar = {
                'cedula': 'Cédula/RUC',
                'nombres': 'Nombres',
                'apellidos': 'Apellidos',
                'telefono_principal': 'Teléfono',
                'estado_servicio': 'Estado',
                'fecha_creacion': 'Fecha de Creación'
            }
            df_display = df[columnas_a_mostrar.keys()].rename(columns=columnas_a_mostrar)
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

        submitted = st.form_submit_button("Crear Cliente")

        if submitted:
            if not new_cedula or not new_nombres or not new_apellidos:
                st.warning("Por favor, completa los campos obligatorios (*).")
            else:
                payload = {
                    "cedula": new_cedula,
                    "nombres": new_nombres,
                    "apellidos": new_apellidos,
                    "telefono_principal": new_telefono
                }
                
                # Le pasamos el token a la función de crear
                response = crear_cliente_api(token, payload)
                
                if response and response.status_code == 201:
                    st.success(f"¡Cliente {new_nombres} {new_apellidos} creado exitosamente!")
                    st.cache_data.clear()
                elif response and response.status_code == 400:
                    st.error(f"Error: La cédula {new_cedula} ya existe.")
                elif response and response.status_code == 401:
                     st.error("Error de autenticación. Tu sesión puede haber expirado.")
                else:
                    st.error(f"Error al crear cliente: {response.text if response else 'Error de conexión'}")
