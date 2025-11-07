# app.py
import solara
import solara.express as px
import requests
import pandas as pd
import os
from dotenv import load_dotenv

# --- Configuración de la Página (BLOQUE INCORRECTO ELIMINADO) ---
# (La configuración ahora se maneja en solara.AppLayout)

# Cargar la URL de la API desde el archivo .env
load_dotenv()
CRM_API_URL = os.getenv("CRM_API_URL")

# --- Estado de la Aplicación (Memoria) ---
token = solara.reactive(None) 
user = solara.reactive(None) 
error_login = solara.reactive("") 

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
                token_data = response.json()
                token.set(token_data['access_token']) 
                error_login.set("")
            else:
                error_login.set("Email o contraseña incorrecta.")
        except requests.RequestException as e:
            error_login.set(f"Error de conexión: {e}")

    with solara.Card(style={"max-width": "500px", "margin": "auto", "margin-top": "100px"}):
        solara.Image("https://i.imgur.com/aMJn64K.png", width="200px", style={"margin": "auto"}) 
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
    solara.Text("Aquí irá la tabla de clientes...")
    
@solara.component
def PageIncidencias():
    """Página para gestionar Incidencias (como tu foto)."""
    solara.Title("Registro de Incidencias")
    
    with solara.Sidebar():
        solara.Text("Filtros de Búsqueda")
        solara.Select(label="Responsable", values=["Todos", "Curillo", "Granizo"])
        solara.Select(label="Estado", values=["Todos", "Abierto", "Resuelto"])

    data = {
        "ID": ["39139", "39138"],
        "TIPO": ["SOPORTE INTERNET", "SOPORTE TVCABLE"],
        "CLIENTE": ["RIVERA MORA LUIS HERNAN", "CEDEÑO DELGADO ROSA MERCEDES"],
        "FCH. RECEPCION": ["06/11/2025 16:45", "06/11/2025 16:17"],
        "ESTADO": ["Abierto", "Abierto"]
    }
    df = pd.DataFrame(data)
    
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
        
        with solara.Sidebar():
            with solara.ExpansionPanel(title="Incidencias", expand=True):
                with solara.ExpansionPanel(title="Transacción", expand=True):
                    solara.Button("Registro incidencias", text=True, icon_name="mdi-table", href="/incidencias")
                    solara.Button("Mis incidencias", text=True, icon_name="mdi-account-box")
            
            with solara.ExpansionPanel(title="Parámetros"):
                solara.Button("Clientes", text=True, icon_name="mdi-account-group", href="/clientes")
                solara.Button("Facturación", text=True, icon_name="mdi-file-document")

        solara.Router.instance().render()
        
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
    solara.Route(path="/", component=PageIncidencias), # Página principal
    solara.Route(path="/clientes", component=PageClientes),
    solara.Route(path="/incidencias", component=PageIncidencias),
]

@solara.component
def Page():
    """
    Componente principal que decide si mostrar el LOGIN o el LAYOUT.
    """
    router = solara.use_router()
    
    if not token.value:
        return LoginForm()
    
    return Layout()
