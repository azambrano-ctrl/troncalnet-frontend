# app.py
import solara
import solara.express as px
import requests
import pandas as pd
import os
from dotenv import load_dotenv

# --- Cargar la URL de la API ---
load_dotenv()
CRM_API_URL = os.getenv("CRM_API_URL")

# --- Estado de la Aplicación (Memoria) ---
# Usamos 'reactive' para que la UI se actualice sola
token = solara.reactive(None) # Guarda el token de login
user = solara.reactive(None) # Guarda los datos del usuario
error_login = solara.reactive("") # Muestra errores de login

# ====================================
# COMPONENTES (Pequeñas partes de la UI)
# ====================================

@solara.component
def LoginForm():
    """Formulario de inicio de sesión."""
    email = solara.use_reactive("")
    password = solara.use_reactive("", password=True)
    
    def try_login():
        if not email.value or not password.value:
            error_login.set("Por favor, ingresa email y contraseña.")
            return

        try:
            login_data = {'username': email.value, 'password': password.value}
            response = requests.post(f"{CRM_API_URL}/login", data=login_data, timeout=10)
            
            if response.status_code == 200:
                # ¡Éxito!
                token_data = response.json()
                token.set(token_data['access_token']) # Guardamos el token
                error_login.set("")
                # (Aquí podríamos llamar a /users/me para guardar el 'user')
            else:
                error_login.set("Email o contraseña incorrecta.")
        except requests.RequestException as e:
            error_login.set(f"Error de conexión: {e}")

    # --- Estructura Visual del Login (similar a tu foto) ---
    with solara.Card(style={"max-width": "500px", "margin": "auto", "margin-top": "100px"}):
        solara.Image("https://i.imgur.com/aMJn64K.png", width="200px", style={"margin": "auto"}) # Logo
        solara.Title("Inicio de Sesión - CRM TroncalNet")
        solara.InputText("Usuario (Email)", value=email)
        solara.InputText("Contraseña", value=password)
        
        if error_login.value:
            solara.Error(error_login.value)
            
        with solara.Row():
            solara.Button("Continuar", on_click=try_login, color="primary", style={"flex-grow": "1"})
        
        solara.Text("¿Olvidó su clave?", style={"text-align": "center", "font-size": "small"})


@solara.component
def PageClientes():
    """Página para gestionar Clientes."""
    solara.Title("Gestión de Clientes")
    # (Aquí iría la lógica de la tabla de clientes)
    solara.Text("Aquí irá la tabla de clientes...")
    
@solara.component
def PageIncidencias():
    """Página para gestionar Incidencias (como tu foto)."""
    solara.Title("Registro de Incidencias")
    
    # --- Filtros (como en tu foto) ---
    with solara.Sidebar():
        solara.Text("Filtros de Búsqueda")
        solara.Select(label="Responsable", values=["Todos", "Curillo", "Granizo"])
        solara.Select(label="Estado", values=["Todos", "Abierto", "Resuelto"])
        # (Aquí añadiríamos los filtros de fecha)

    # --- Tabla de Incidencias ---
    # (Esto es solo un ejemplo de la tabla que vimos)
    data = {
        "ID": ["39139", "39138"],
        "TIPO": ["SOPORTE INTERNET", "SOPORTE TVCABLE"],
        "CLIENTE": ["RIVERA MORA LUIS HERNAN", "CEDEÑO DELGADO ROSA MERCEDES"],
        "FCH. RECEPCION": ["06/11/2025 16:45", "06/11/2025 16:17"],
        "ESTADO": ["Abierto", "Abierto"]
    }
    df = pd.DataFrame(data)
    
    # Usamos Solara Express (px) para mostrar un DataFrame de Pandas
    px.dataframe(df, style={"height": "400px"})

# ====================================
# LAYOUT PRINCIPAL (La página entera)
# ====================================
@solara.component
def Layout():
    """Define el menú lateral y el contenido principal."""
    
    with solara.AppLayout(
        title="CRM TroncalNet", 
        navigation=True, 
        sidebar_open=True
    ) as main:
        
        # --- Menú Lateral (Sidebar) ---
        # (Esto crea el menú como el de tu foto)
        with solara.Sidebar():
            with solara.ExpansionPanel(title="Incidencias", expand=True):
                with solara.ExpansionPanel(title="Transacción", expand=True):
                    solara.Button("Registro incidencias", text=True, icon_name="mdi-table", href="/incidencias")
                    solara.Button("Mis incidencias", text=True, icon_name="mdi-account-box")
            
            with solara.ExpansionPanel(title="Parámetros"):
                solara.Button("Clientes", text=True, icon_name="mdi-account-group", href="/clientes")
                solara.Button("Facturación", text=True, icon_name="mdi-file-document")

        # --- Contenido Principal ---
        # (Aquí es donde se mostrarán las páginas)
        solara.Router.instance().render()
        
        # Botón de Logout (si estamos logueados)
        if token.value:
            def do_logout():
                token.set(None)
                user.set(None)
            solara.Button("Cerrar Sesión", on_click=do_logout, icon_name="mdi-logout", text=True, style={"position": "absolute", "bottom": "10px", "left": "10px"})

# ====================================
# CONTROLADOR DE RUTAS
# ====================================

# Definimos las "rutas" (URLs) de nuestra aplicación
routes = [
    solara.Route(path="/", component=PageIncidencias, name="Inicio"), # Página principal
    solara.Route(path="/clientes", component=PageClientes, name="Clientes"),
    solara.Route(path="/incidencias", component=PageIncidencias, name="Incidencias"),
]

@solara.component
def Page():
    """
    Componente principal que decide si mostrar el LOGIN o el LAYOUT.
    """
    # Usamos el router
    router = solara.use_router()
    
    # Si no hay token, mostrar el Login
    if not token.value:
        return LoginForm()
    
    # Si hay token, mostrar el Layout principal
    return Layout()
