# admin_app.py
import streamlit as st
import requests
import pandas as pd
import os
from dotenv import load_dotenv

# --- Configuración de la Página ---
# Esto debe ser lo PRIMERO que Streamlit corre
st.set_page_config(
    page_title="CRM TroncalNet",
    page_icon="📡",
    layout="wide" # Usa todo el ancho de la pantalla
)

# Cargar la URL de la API desde el archivo .env
load_dotenv()
CRM_API_URL = os.getenv("CRM_API_URL")

if not CRM_API_URL:
    st.error("Error: No se encontró la variable CRM_API_URL. Asegúrate de crear un archivo .env.")
    st.stop() # Detiene la ejecución si la API no está configurada

# --- Funciones de la API ---
# (Vamos a 'cachear' los datos para que el panel sea rápido)

@st.cache_data(ttl=60) # Guarda los datos por 60 segundos
def get_clientes(filtro_nombre=""):
    """
    Obtiene todos los clientes de la API, con un filtro opcional.
    """
    try:
        # Usamos el endpoint '/buscar' que ya creamos
        if filtro_nombre:
            response = requests.get(f"{CRM_API_URL}/clientes/buscar", params={"q": filtro_nombre}, timeout=10)
        else:
            # Si no hay filtro, traemos los primeros 100
            # (Modificaremos crud.py para que /clientes/buscar acepte 'q' opcional)
            # Por ahora, esto funcionará si escribes algo
             response = requests.get(f"{CRM_API_URL}/clientes/buscar", params={"q": "a"}, timeout=10)
       
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return [] # No se encontraron clientes
        else:
            st.error(f"Error al contactar la API (Clientes): {response.status_code}")
            return None
            
    except requests.RequestException as e:
        st.error(f"Error de conexión con la API: {e}")
        return None

# --- Título del Panel ---
st.title("📡 Panel de Administración CRM - TroncalNet")
st.markdown("---")

# --- Sección: Clientes ---
st.header("Gestión de Clientes")

# 1. Barra de Búsqueda
filtro = st.text_input("Buscar cliente por nombre, apellido o cédula:")

# 2. Botón para refrescar
if st.button("Buscar / Refrescar"):
    # Limpia la caché para forzar la recarga
    st.cache_data.clear()

# 3. Cargar y mostrar datos
clientes_data = get_clientes(filtro_nombre=filtro)

if clientes_data is None:
    st.warning("No se pudieron cargar los datos de los clientes.")
else:
    # Convertimos el JSON en una tabla bonita (DataFrame de Pandas)
    df = pd.DataFrame(clientes_data)
    
    # Seleccionamos y renombramos las columnas que queremos ver
    columnas_a_mostrar = {
        'cedula': 'Cédula/RUC',
        'nombres': 'Nombres',
        'apellidos': 'Apellidos',
        'telefono_principal': 'Teléfono',
        'estado_servicio': 'Estado',
        'fecha_creacion': 'Fecha de Creación'
    }
    
    # Filtramos el dataframe para mostrar solo esas columnas
    df_display = df[columnas_a_mostrar.keys()].rename(columns=columnas_a_mostrar)
    
    # Mostramos la tabla en la página
    st.dataframe(df_display, use_container_width=True)
    st.caption(f"Mostrando {len(df_display)} clientes.")

st.markdown("---")

# --- (Futuro) Sección: Crear Cliente ---
st.subheader("Crear Nuevo Cliente")

# Creamos un formulario
with st.form("form_crear_cliente", clear_on_submit=True):
    st.write("Completa los datos del nuevo cliente:")
    
    # Creamos columnas para un diseño más limpio
    col1, col2 = st.columns(2)
    with col1:
        new_cedula = st.text_input("Cédula/RUC*", max_chars=13)
        new_nombres = st.text_input("Nombres*")
    with col2:
        new_apellidos = st.text_input("Apellidos*")
        new_telefono = st.text_input("Teléfono Principal", max_chars=15)

    # Botón de envío del formulario
    submitted = st.form_submit_button("Crear Cliente")

    if submitted:
        # Validaciones básicas
        if not new_cedula or not new_nombres or not new_apellidos:
            st.warning("Por favor, completa los campos obligatorios (*).")
        else:
            # Payload para la API (coincide con el schema ClienteCreate)
            payload = {
                "cedula": new_cedula,
                "nombres": new_nombres,
                "apellidos": new_apellidos,
                "telefono_principal": new_telefono
            }
            
            try:
                # Llamada POST a la API
                response = requests.post(f"{CRM_API_URL}/clientes/", json=payload, timeout=10)
                
                if response.status_code == 201: # 201 = Creado
                    st.success(f"¡Cliente {new_nombres} {new_apellidos} creado exitosamente!")
                    # Limpiamos la caché para que la tabla de arriba se actualice
                    st.cache_data.clear()
                elif response.status_code == 400 and "ya está registrada" in response.json().get("detail", ""):
                    st.error(f"Error: La cédula {new_cedula} ya existe.")
                else:
                    st.error(f"Error al crear cliente: {response.text}")
            
            except requests.RequestException as e:
                st.error(f"Error de conexión con la API: {e}")