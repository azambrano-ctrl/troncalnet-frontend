# app.py
import solara
import solara.lab
import requests
import pandas as pd
import os
from dotenv import load_dotenv

# --- Cargar la URL de la API ---
load_dotenv()
CRM_API_URL = os.getenv("CRM_API_URL")

if not CRM_API_URL:
    # Si estamos en Render, Render provee la variable
    CRM_API_URL = os.environ.get("CRM_API_URL")
    if not CRM_API_URL:
        # Si aun así no la encuentra, detenemos la app
        print("ERROR: No se encontró la variable CRM_API_URL.")
        # En Solara, mostramos el error en la UI
        solara.Error("Error de Configuración: CRM_API_URL no encontrada.")
        # st.stop() # Esto es de Streamlit, no aplica aquí

# --- Estado de la Aplicación (Memoria) ---
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
        if not CRM_API_URL:
            error_login.set("Error: La URL de la API no está configurada.")
            return

        try:
            login_data = {'username': email.value, 'password': password.value}
            response = requests.post(f"{CRM_API_URL}/login", data=login_data, timeout=10)
            
            if response.status_code == 200:
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
    
    # --- Estado local para esta página ---
    filtro, set_filtro = solara.use_state("")
    clientes, set_clientes = solara.use_state(None)
    error_msg, set_error_msg = solara.use_state("")

    def buscar_clientes():
        set_error_msg("")
        if not token.value:
            set_error_msg("Sesión expirada. Por favor, inicie sesión de nuevo.")
            return
        
        headers = {"Authorization": f"Bearer {token.value}"}
        params = {"q": filtro if filtro else "a"} # Busca 'a' si está vacío
        
        try:
            response = requests.get(f"{CRM_API_URL}/clientes/buscar", params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                set_clientes(response.json())
            elif response.status_code == 404:
                set_clientes([]) # Lista vacía
            elif response.status_code == 401:
                token.set(None) # Forzar relogin
            else:
                set_error_msg(f"Error al cargar clientes: {response.status_code}")
        except requests.RequestException as e:
            set_error_msg(f"Error de conexión: {e}")

    # Cargar clientes al iniciar la página
    solara.use_effect(buscar_clientes, [token.value]) # Se ejecuta cuando el token cambia

    # --- UI de la página ---
    with solara.Sidebar():
        solara.Text("Filtros de Búsqueda")
        solara.InputText("Buscar por Cédula, Nombre o Apellido", value=filtro, on_value=set_filtro)
        solara.Button("Buscar", on_click=buscar_clientes, icon_name="mdi-magnify")

    if error_msg:
        solara.Error(error_msg)
    
    if clientes is None:
        solara.ProgressLinear(True) # Muestra barra de carga
    elif not clientes:
        solara.Info("No se encontraron clientes con ese criterio.")
    else:
        df = pd.DataFrame(clientes)
        # (Aquí puedes añadir la lógica para crear clientes)
        solara.DataFrame(df)

@solara.component
def PageIncidencias():
    """Página para gestionar Incidencias (como tu foto)."""
    solara.Title("Registro de Incidencias")
    
    # --- Estado local ---
    tickets, set_tickets = solara.use_state(None)
    error_msg, set_error_msg = solara.use_state("")

    def buscar_tickets():
        set_error_msg("")
        if not token.value:
            set_error_msg("Sesión expirada. Por favor, inicie sesión de nuevo.")
            return
        
        headers = {"Authorization": f"Bearer {token.value}"}
        
        try:
            # Llama al endpoint /tickets/ que creamos (devuelve todos)
            response = requests.get(f"{CRM_API_URL}/tickets/", headers=headers, timeout=10)
            if response.status_code == 200:
                set_tickets(response.json())
            elif response.status_code == 401:
                token.set(None) # Forzar relogin
            else:
                set_error_msg(f"Error al cargar tickets: {response.status_code}")
        except requests.RequestException as e:
            set_error_msg(f"Error de conexión: {e}")

    # Cargar tickets al iniciar la página
    solara.use_effect(buscar_tickets, [token.value])

    # --- UI de la página ---
    with solara.Sidebar():
        solara.Text("Filtros de Búsqueda")
        solara.Select(label="Responsable", values=["Todos", "Curillo", "Granizo"])
        solara.Select(label="Estado", values=["Todos", "Abierto", "Resuelto"])

    if error_msg:
        solara.Error(error_msg)

    if tickets is None:
        solara.ProgressLinear(True) # Muestra barra de carga
    elif not tickets:
        solara.Info("No se han registrado incidencias.")
    else:
        df = pd.DataFrame(tickets)
        # Renombramos columnas para la tabla
        df_display = df.rename(columns={
            'id': 'Ticket ID',
            'cliente_cedula': 'Cédula Cliente',
            'tipo_problema': 'Problema',
            'estado': 'Estado',
            'fecha_creacion': 'Fecha Creación',
            'descripcion': 'Descripción'
        })
        # (Añadiremos la lógica para editar el estado más adelante)
        solara.DataFrame(df_display)

# ====================================
# LAYOUT PRINCIPAL (La página entera)
# ====================================
@solara.component
def Layout():
    """Define el menú lateral y el contenido principal."""
    
    # --- Lógica de Rutas (Movida aquí) ---
    router = solara.use_router()
    
    with solara.AppLayout(
        title="CRM TroncalNet", 
        navigation=True, 
        sidebar_open=True
    ) as main:
        
        with solara.Sidebar():
            with solara.ExpansionPanel(title="Incidencias", expand=True):
                with solara.ExpansionPanel(title="Transacción", expand=True):
                    # Usamos router.push para cambiar de página
                    solara.Button("Registro incidencias", text=True, icon_name="mdi-table", on_click=lambda: router.push("/incidencias"))
                    solara.Button("Mis incidencias", text=True, icon_name="mdi-account-box", on_click=lambda: router.push("/mis-incidencias"))
            
            with solara.ExpansionPanel(title="Parámetros"):
                solara.Button("Clientes", text=True, icon_name="mdi-account-group", on_click=lambda: router.push("/clientes"))
                solara.Button("Facturación", text=True, icon_name="mdi-file-document", on_click=lambda: router.push("/facturacion"))

        # --- Contenido Principal ---
        # El router decide qué página mostrar aquí
        solara.Router.instance().render()
        
        if token.value:
            def do_logout():
                token.set(None)
                user.set(None)
            solara.Button("Cerrar Sesión", on_click=do_logout, icon_name="mdi-logout", text=True, style={"position": "absolute", "bottom": "10px", "left": "10px"})

# ====================================
# CONTROLADOR DE RUTAS
# ====================================

routes = [
    solara.Route(path="/", component=PageIncidencias), 
    solara.Route(path="/clientes", component=PageClientes),
    solara.Route(path="/incidencias", component=PageIncidencias),
    # (Añadimos rutas de ejemplo para los botones nuevos)
    solara.Route(path="/mis-incidencias", component=lambda: solara.Error("Página 'Mis Incidencias' en construcción.")),
    solara.Route(path="/facturacion", component=lambda: solara.Error("Página 'Facturación' en construcción.")),
]

# ====================================
# COMPONENTE PRINCIPAL (App)
# ====================================
@solara.component
def App():
    """
    Componente principal que decide si mostrar el LOGIN o el LAYOUT.
    Solara buscará este componente por defecto.
    """
    # Si no hay token, mostrar el Login
    if not token.value:
        return LoginForm()
    
    # Si hay token, mostrar el Layout principal con sus rutas
    return solara.RoutingProvider(routes=routes, children=[Layout()])
