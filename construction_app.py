import streamlit as st
import pandas as pd
import time
import os
import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
from io import BytesIO

# INTENTO DE IMPORTAR LIBRERÍAS DE GOOGLE CLOUD
try:
    from google.cloud import firestore
    from google.cloud import storage
    from google.oauth2 import service_account
    import json
    GCP_LIB_AVAILABLE = True
except ImportError:
    GCP_LIB_AVAILABLE = False

# INTENTO DE IMPORTAR LIBRERÍAS DE SEGURIDAD Y COMPRESIÓN
try:
    import bcrypt
    BCrypt_AVAILABLE = True
except ImportError:
    BCrypt_AVAILABLE = False
    st.warning("⚠️ bcrypt no disponible. Las contraseñas no estarán hasheadas. Instala con: pip install bcrypt")

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    st.warning("⚠️ PIL no disponible. Las imágenes no se comprimirán. Instala con: pip install Pillow")

# --- CONFIGURACIÓN DE LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- CONFIGURACIÓN DE LA PÁGINA (MOBILE FRIENDLY) ---
st.set_page_config(
    page_title="ConTech Mobile",
    page_icon="👷‍♂️",
    layout="wide", # En celular se colapsa automáticamente a una columna
    initial_sidebar_state="auto", # En celular arranca cerrado
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "ConTech Mobile - Gestión de Obra v1.0"
    }
)

# --- PWA CONFIGURATION ---
# Inyectar meta tags y manifest para PWA
st.markdown("""
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#1e293b">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="ConTech Mobile">
<meta name="mobile-web-app-capable" content="yes">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<link rel="apple-touch-icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E👷‍♂️%3C/text%3E%3C/svg%3E">
""", unsafe_allow_html=True)

# Registrar Service Worker (solo si está disponible)
st.markdown("""
<script>
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/service-worker.js')
            .then((reg) => {
                console.log('✅ Service Worker registrado:', reg.scope);
            })
            .catch((err) => {
                console.log('⚠️ Error registrando Service Worker:', err);
            });
    });
}

// Detectar si la app está instalada
window.addEventListener('beforeinstallprompt', (e) => {
    console.log('📱 App puede ser instalada');
    e.preventDefault();
});

// Detectar si ya está instalada
if (window.matchMedia('(display-mode: standalone)').matches) {
    console.log('📱 App ejecutándose en modo standalone (instalada)');
}
</script>
""", unsafe_allow_html=True)

# --- ESTILOS CSS OPTIMIZADOS PARA MÓVIL ---
st.markdown("""
<style>
    /* Estilos base */
    .stMetric {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 10px;
        border-radius: 10px;
    }
    .main-header {
        color: #1e293b;
        font-weight: 700;
    }
    
    /* OPTIMIZACIONES PARA CELULAR (Media Queries) */
    @media (max-width: 768px) {
        .main-header {
            font-size: 1.5rem !important;
            text-align: center;
        }
        /* Botones más grandes para dedos (Touch targets) */
        .stButton button {
            min-height: 55px !important;
            font-size: 18px !important;
            border-radius: 12px !important;
            margin-bottom: 10px !important;
            width: 100% !important;
        }
        /* Radio buttons más grandes en móvil */
        .stRadio > div {
            flex-direction: column !important;
        }
        .stRadio label {
            min-height: 44px !important;
            padding: 10px !important;
        }
        /* Tabs más grandes */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            min-height: 48px !important;
            padding: 12px 16px !important;
        }
        /* Dataframes optimizados para móvil */
        .dataframe {
            font-size: 14px !important;
        }
        /* Ocultar elementos no esenciales en móvil si es necesario */
        .desktop-only {
            display: none;
        }
        /* Inputs más grandes */
        .stTextInput input, .stTextArea textarea {
            font-size: 16px !important; /* Evita zoom en iOS */
        }
    }
    
    /* Escritorio */
    @media (min-width: 769px) {
        .main-header {
            font-size: 2.5rem;
        }
    }
    
    /* Mejoras generales */
    .stDataFrame {
        overflow-x: auto;
    }
</style>
""", unsafe_allow_html=True)

# --- CONSTANTES DE CONFIGURACIÓN ---
SESSION_TIMEOUT_MINUTES = 30
MAX_FILE_SIZE_MB = 50
MAX_IMAGE_SIZE_MB = 10
ALLOWED_FILE_TYPES = ['.pdf', '.dwg', '.dwgx', '.dxf']
ALLOWED_IMAGE_TYPES = ['.jpg', '.jpeg', '.png', '.webp']
UPLOAD_DIR = Path("uploads")
PHOTOS_DIR = Path("uploads/photos")
DOCS_DIR = Path("uploads/docs")
DATA_DIR = Path("data")
DB_FILE = DATA_DIR / "database.json"

# Crear directorios si no existen
UPLOAD_DIR.mkdir(exist_ok=True)
PHOTOS_DIR.mkdir(exist_ok=True)
DOCS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

# --- UTILIDADES ---

def hash_password(password: str) -> str:
    """Hashea una contraseña usando bcrypt"""
    if BCrypt_AVAILABLE:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    return password  # Fallback si bcrypt no está disponible

def check_password(password: str, hashed: str) -> bool:
    """Verifica una contraseña contra su hash"""
    if BCrypt_AVAILABLE:
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception as e:
            logger.error(f"Error verificando contraseña: {e}")
            return False
    return password == hashed  # Fallback si bcrypt no está disponible

def validate_file(file, max_size_mb: int, allowed_types: list) -> tuple[bool, str]:
    """Valida un archivo subido"""
    if file is None:
        return False, "No se proporcionó ningún archivo"
    
    # Validar tamaño
    file_size_mb = len(file.getvalue()) / (1024 * 1024)
    if file_size_mb > max_size_mb:
        return False, f"El archivo excede el tamaño máximo de {max_size_mb}MB"
    
    # Validar tipo
    file_ext = Path(file.name).suffix.lower()
    if file_ext not in allowed_types:
        return False, f"Tipo de archivo no permitido. Permitidos: {', '.join(allowed_types)}"
    
    return True, "OK"

def compress_image(image_bytes: bytes, max_size_kb: int = 500) -> bytes:
    """Comprime una imagen manteniendo calidad razonable"""
    if not PIL_AVAILABLE:
        return image_bytes
    
    try:
        img = Image.open(BytesIO(image_bytes))
        
        # Convertir a RGB si es necesario
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        
        # Calcular calidad inicial
        quality = 85
        output = BytesIO()
        
        # Comprimir hasta alcanzar el tamaño deseado
        while quality > 20:
            output.seek(0)
            output.truncate(0)
            img.save(output, format='JPEG', quality=quality, optimize=True)
            size_kb = len(output.getvalue()) / 1024
            
            if size_kb <= max_size_kb:
                break
            quality -= 10
        
        return output.getvalue()
    except Exception as e:
        logger.error(f"Error comprimiendo imagen: {e}")
        return image_bytes

def check_session_timeout() -> bool:
    """Verifica si la sesión ha expirado"""
    if 'last_activity' not in st.session_state:
        st.session_state.last_activity = datetime.now()
        return True
    
    elapsed = datetime.now() - st.session_state.last_activity
    if elapsed > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
        return False
    
    st.session_state.last_activity = datetime.now()
    return True

def format_date(date_obj: datetime) -> str:
    """Formatea una fecha de manera consistente"""
    return date_obj.strftime("%d/%m/%Y %H:%M")

# --- FUNCIONES DE PERSISTENCIA JSON ---

def load_json_db():
    """Carga la base de datos desde archivo JSON"""
    if DB_FILE.exists():
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error cargando base de datos: {e}")
            return get_default_db()
    return get_default_db()

def save_json_db(data):
    """Guarda la base de datos en archivo JSON"""
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        logger.info("Base de datos guardada correctamente")
        return True
    except Exception as e:
        logger.error(f"Error guardando base de datos: {e}")
        return False

def get_default_db():
    """Retorna estructura por defecto de la base de datos"""
    return {
        "projects": [],
        "activities": [],
        "personnel": [],
        "improvements": [],
        "budget": {
            "total": 9500000,
            "executed": 0,
            "categories": {
                "Mano de Obra": {"budget": 4500000, "executed": 0},
                "Materiales": {"budget": 3200000, "executed": 0},
                "Equipos": {"budget": 1800000, "executed": 0},
                "Subcontratos": {"budget": 2500000, "executed": 0},
                "Otros": {"budget": 800000, "executed": 0}
            }
        },
        "milestones": [],
        "alerts": []
    }

# --- GESTOR DE DATOS ---

class DataManager:
    def __init__(self):
        self.use_gcp = False
        self.db = None
        self.bucket = None
        
        if GCP_LIB_AVAILABLE:
            try:
                if "gcp_service_account" in st.secrets:
                    creds_dict = dict(st.secrets["gcp_service_account"])
                    creds = service_account.Credentials.from_service_account_info(creds_dict)
                    self.db = firestore.Client(credentials=creds)
                    
                    # Inicializar bucket si está configurado
                    if "gcp_bucket_name" in st.secrets:
                        self.bucket = storage.Client(credentials=creds).bucket(st.secrets["gcp_bucket_name"])
                    
                    self.use_gcp = True
                    logger.info("Conexión a GCP establecida correctamente")
            except Exception as e:
                logger.error(f"Error conectando a GCP: {e}")
                self.use_gcp = False
        
        # Estado Local
        if not self.use_gcp:
            if 'local_docs' not in st.session_state:
                st.session_state.local_docs = [
                    {"Archivo": "Plano_Estructural.pdf", "Versión": "v4.2", "Fecha": "28 Nov", "Estado": "Aprobado"},
                    {"Archivo": "Detalles_Sanitarios.dwg", "Versión": "v2.1", "Fecha": "27 Nov", "Estado": "Revisión"}
                ]
            if 'local_inspections' not in st.session_state:
                st.session_state.local_inspections = [
                    {"Fecha": "Hoy 10:30", "Actividad": "Recepción Enfierradura", "Auditor": "María Torres", "Resultado": "Aprobado"}
                ]

    def save_inspection(self, data, photo=None):
        """Guarda una inspección con foto opcional"""
        try:
            # Procesar y guardar foto si existe
            photo_path = None
            if photo:
                try:
                    # Comprimir imagen
                    photo_bytes = photo.getvalue()
                    compressed_photo = compress_image(photo_bytes)
                    
                    # Generar nombre único
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    photo_filename = f"inspection_{timestamp}.jpg"
                    
                    if self.use_gcp and self.bucket:
                        # Subir a Cloud Storage
                        blob = self.bucket.blob(f"inspections/{photo_filename}")
                        blob.upload_from_string(compressed_photo, content_type='image/jpeg')
                        photo_path = f"gs://{self.bucket.name}/inspections/{photo_filename}"
                        logger.info(f"Foto subida a GCS: {photo_path}")
                    else:
                        # Guardar localmente
                        photo_path = PHOTOS_DIR / photo_filename
                        photo_path.write_bytes(compressed_photo)
                        photo_path = str(photo_path)
                        logger.info(f"Foto guardada localmente: {photo_path}")
                    
                    data["Tiene_Foto"] = "Sí"
                    data["Foto_Path"] = photo_path
                except Exception as e:
                    logger.error(f"Error guardando foto: {e}")
                    data["Tiene_Foto"] = "Error"
                    st.warning("La inspección se guardó pero hubo un error con la foto")
            else:
                data["Tiene_Foto"] = "No"
            
            # Agregar timestamp consistente
            data["Timestamp"] = datetime.now().isoformat()
            data["Fecha"] = format_date(datetime.now())

            if self.use_gcp:
                try:
                    self.db.collection("inspections").add(data)
                    st.toast("Guardado en Nube", icon="☁️")
                    logger.info("Inspección guardada en Firestore")
                except Exception as e:
                    logger.error(f"Error guardando en Firestore: {e}")
                    st.error("Error al guardar en la nube. Guardando localmente...")
                    st.session_state.local_inspections.insert(0, data)
                    st.toast("Guardado Localmente (fallback)", icon="💾")
            else:
                st.session_state.local_inspections.insert(0, data)
                st.toast("Guardado Localmente", icon="💾")
                logger.info("Inspección guardada localmente")
                
        except Exception as e:
            logger.error(f"Error en save_inspection: {e}")
            st.error(f"Error al guardar la inspección: {str(e)}")

    def get_inspections(self):
        """Obtiene todas las inspecciones"""
        try:
            if self.use_gcp:
                docs = self.db.collection("inspections").order_by("Timestamp", direction=firestore.Query.DESCENDING).limit(100).stream()
                return [doc.to_dict() for doc in docs]
            return st.session_state.local_inspections
        except Exception as e:
            logger.error(f"Error obteniendo inspecciones: {e}")
            st.error("Error al cargar inspecciones")
            return st.session_state.local_inspections if 'local_inspections' in st.session_state else []

    def upload_file(self, uploaded_file, metadata):
        """Sube un archivo con validación"""
        try:
            # Validar archivo
            is_valid, message = validate_file(uploaded_file, MAX_FILE_SIZE_MB, ALLOWED_FILE_TYPES)
            if not is_valid:
                st.error(message)
                return False
            
            # Generar nombre único
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_ext = Path(uploaded_file.name).suffix
            safe_filename = f"{timestamp}_{Path(uploaded_file.name).stem}{file_ext}"
            
            # Guardar archivo
            file_path = None
            if self.use_gcp and self.bucket:
                try:
                    blob = self.bucket.blob(f"docs/{safe_filename}")
                    blob.upload_from_string(uploaded_file.getvalue(), content_type=uploaded_file.type)
                    file_path = f"gs://{self.bucket.name}/docs/{safe_filename}"
                    logger.info(f"Archivo subido a GCS: {file_path}")
                except Exception as e:
                    logger.error(f"Error subiendo a GCS: {e}")
                    st.warning("Error subiendo a la nube. Guardando localmente...")
                    file_path = DOCS_DIR / safe_filename
                    file_path.write_bytes(uploaded_file.getvalue())
                    file_path = str(file_path)
            else:
                file_path = DOCS_DIR / safe_filename
                file_path.write_bytes(uploaded_file.getvalue())
                file_path = str(file_path)
                logger.info(f"Archivo guardado localmente: {file_path}")
            
            # Registrar en base de datos
            new_doc = {
                "Archivo": uploaded_file.name,
                "Versión": metadata.get("version", "v1.0"),
                "Fecha": datetime.now().strftime("%d/%m/%Y"),
                "Estado": "Pendiente",
                "File_Path": file_path,
                "Timestamp": datetime.now().isoformat()
            }
            
            if self.use_gcp:
                try:
                    self.db.collection("documents").add(new_doc)
                except Exception as e:
                    logger.error(f"Error guardando documento en Firestore: {e}")
                    if 'local_docs' not in st.session_state:
                        st.session_state.local_docs = []
                    st.session_state.local_docs.insert(0, new_doc)
            else:
                if 'local_docs' not in st.session_state:
                    st.session_state.local_docs = []
                st.session_state.local_docs.insert(0, new_doc)
            
            st.toast("Archivo registrado", icon="📂")
            return True
            
        except Exception as e:
            logger.error(f"Error en upload_file: {e}")
            st.error(f"Error al subir archivo: {str(e)}")
            return False

    def get_docs(self):
        """Obtiene todos los documentos"""
        try:
            if self.use_gcp:
                docs = self.db.collection("documents").order_by("Timestamp", direction=firestore.Query.DESCENDING).limit(100).stream()
                return [doc.to_dict() for doc in docs]
            return st.session_state.local_docs
        except Exception as e:
            logger.error(f"Error obteniendo documentos: {e}")
            return st.session_state.local_docs if 'local_docs' in st.session_state else []
    
    # --- MÉTODOS PARA GESTIÓN DE PROYECTOS Y DATOS ---
    
    def get_db(self):
        """Obtiene la base de datos completa"""
        if self.use_gcp:
            # En GCP se obtendría de Firestore
            return get_default_db()
        if 'json_db' not in st.session_state:
            st.session_state.json_db = load_json_db()
        return st.session_state.json_db
    
    def save_db(self, db_data):
        """Guarda la base de datos"""
        if self.use_gcp:
            # En GCP se guardaría en Firestore
            pass
        else:
            st.session_state.json_db = db_data
            save_json_db(db_data)
    
    def add_activity(self, activity_data):
        """Agrega una nueva actividad"""
        db = self.get_db()
        activity_data["id"] = len(db["activities"]) + 1
        activity_data["created_at"] = datetime.now().isoformat()
        db["activities"].append(activity_data)
        self.save_db(db)
        return True
    
    def get_activities(self):
        """Obtiene todas las actividades"""
        db = self.get_db()
        return db.get("activities", [])
    
    def add_personnel(self, personnel_data):
        """Agrega personal a la base de datos"""
        db = self.get_db()
        personnel_data["id"] = len(db["personnel"]) + 1
        personnel_data["created_at"] = datetime.now().isoformat()
        db["personnel"].append(personnel_data)
        self.save_db(db)
        return True
    
    def get_personnel(self):
        """Obtiene todo el personal"""
        db = self.get_db()
        return db.get("personnel", [])
    
    def add_improvement(self, improvement_data):
        """Agrega una mejora o sugerencia"""
        db = self.get_db()
        improvement_data["id"] = len(db["improvements"]) + 1
        improvement_data["created_at"] = datetime.now().isoformat()
        improvement_data["status"] = "Pendiente"
        db["improvements"].append(improvement_data)
        self.save_db(db)
        return True
    
    def get_improvements(self):
        """Obtiene todas las mejoras"""
        db = self.get_db()
        return db.get("improvements", [])
    
    def update_improvement_status(self, improvement_id, new_status):
        """Actualiza el estado de una mejora"""
        db = self.get_db()
        for improvement in db.get("improvements", []):
            if improvement.get("id") == improvement_id:
                improvement["status"] = new_status
                improvement["updated_at"] = datetime.now().isoformat()
                self.save_db(db)
                return True
        return False
    
    def update_budget(self, category, amount):
        """Actualiza el presupuesto ejecutado"""
        db = self.get_db()
        if category in db["budget"]["categories"]:
            db["budget"]["categories"][category]["executed"] += amount
            db["budget"]["executed"] += amount
            self.save_db(db)
            return True
        return False
    
    def get_budget(self):
        """Obtiene información del presupuesto"""
        db = self.get_db()
        return db.get("budget", get_default_db()["budget"])
    
    def add_milestone(self, milestone_data):
        """Agrega un hito del proyecto"""
        db = self.get_db()
        milestone_data["id"] = len(db["milestones"]) + 1
        milestone_data["created_at"] = datetime.now().isoformat()
        db["milestones"].append(milestone_data)
        self.save_db(db)
        return True
    
    def get_milestones(self):
        """Obtiene todos los hitos"""
        db = self.get_db()
        return db.get("milestones", [])
    
    def add_alert(self, alert_data):
        """Agrega una alerta"""
        db = self.get_db()
        alert_data["id"] = len(db["alerts"]) + 1
        alert_data["created_at"] = datetime.now().isoformat()
        db["alerts"].append(alert_data)
        self.save_db(db)
        return True
    
    def get_alerts(self):
        """Obtiene todas las alertas"""
        db = self.get_db()
        return db.get("alerts", [])

dm = DataManager()

# --- AUTENTICACIÓN ---

# Base de datos de usuarios con contraseñas hasheadas
def init_users_db():
    """Inicializa la base de datos de usuarios con contraseñas hasheadas"""
    users = {
    "jefe": {"password": "admin123", "role": "ADMIN", "name": "Ing. Carlos Méndez"},
    "obrero": {"password": "obra123", "role": "WORKER", "name": "Juan Pérez"},
    "cliente": {"password": "cliente123", "role": "CLIENT", "name": "Inmobiliaria S.A."}
}

    # Hashear contraseñas si bcrypt está disponible
    if BCrypt_AVAILABLE:
        for username, user_data in users.items():
            if not user_data["password"].startswith("$2b$"):  # No está hasheado
                users[username]["password"] = hash_password(user_data["password"])
    
    return users

USERS_DB = init_users_db()

# Inicializar estado de sesión
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_info' not in st.session_state:
    st.session_state.user_info = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'last_activity' not in st.session_state:
    st.session_state.last_activity = datetime.now()

def login():
    st.markdown("<br><h2 style='text-align: center;'>🏗️ ConTech Mobile</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Acceso Seguro de Obra</p>", unsafe_allow_html=True)
    
    # Usar columnas para centrar en escritorio, en móvil ocupará ancho completo
    col1, col2, col3 = st.columns([1, 6, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Usuario", autocomplete="username")
            password = st.text_input("Contraseña", type="password", autocomplete="current-password")
            submit = st.form_submit_button("Ingresar", type="primary", use_container_width=True)
            
            if submit:
                if username in USERS_DB:
                    if check_password(password, USERS_DB[username]["password"]):
                        st.session_state.authenticated = True
                        st.session_state.user_info = {
                            "username": username,
                            "role": USERS_DB[username]["role"],
                            "name": USERS_DB[username]["name"]
                        }
                        st.session_state.last_activity = datetime.now()
                        st.rerun()
                    else:
                        st.error("Credenciales incorrectas")
                        logger.warning(f"Intento de login fallido para usuario: {username}")
                else:
                    st.error("Credenciales incorrectas")
                    logger.warning(f"Intento de login con usuario inexistente: {username}")
        
        # Solo mostrar credenciales en modo desarrollo
        if os.getenv("STREAMLIT_ENV") != "production":
            with st.expander("ℹ️ Ver Credenciales Demo"):
                st.write("- Jefe: `jefe` / `admin123`")
                st.write("- Obrero: `obrero` / `obra123`")
                st.write("- Cliente: `cliente` / `cliente123`")

def logout():
    st.session_state.authenticated = False
    st.session_state.user_info = None
    st.session_state.last_activity = None
    st.rerun()

# --- VISTAS ---

def view_dashboard_admin():
    st.markdown("<div class='main-header'>📊 Dashboard Ejecutivo</div>", unsafe_allow_html=True)
    
    # --- KPIs PRINCIPALES ---
    st.subheader("📈 Indicadores Clave (KPIs)")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    with kpi1:
        st.metric(
            label="Avance Físico",
            value="45.2%",
            delta="+2.5%",
            delta_color="normal",
            help="Porcentaje de avance físico del proyecto"
        )
        st.progress(0.452)
    
    with kpi2:
        budget = dm.get_budget()
        budget_percent = (budget['executed'] / budget['total'] * 100) if budget['total'] > 0 else 0
        st.metric(
            label="Presupuesto Ejecutado",
            value=f"{budget_percent:.1f}%",
            delta=f"${budget['executed']:,.0f}",
            delta_color="normal",
            help="Porcentaje del presupuesto utilizado"
        )
        st.progress(budget_percent / 100)
    
    with kpi3:
        st.metric(
            label="Asistencia Hoy",
            value="92%",
            delta="-1%",
            delta_color="inverse",
            help="Porcentaje de asistencia del personal hoy"
        )
        st.progress(0.92)
    
    with kpi4:
        st.metric(
            label="Días Sin Accidentes",
            value="128",
            delta="+7 días",
            delta_color="normal",
            help="Días consecutivos sin accidentes"
        )
    
    # --- SEGUNDA FILA DE KPIs ---
    kpi5, kpi6, kpi7, kpi8 = st.columns(4)
    
    with kpi5:
        st.metric(
            label="RFI Pendientes",
            value="12",
            delta="-3",
            delta_color="normal",
            help="Request for Information pendientes"
        )
        st.caption("3 críticos")
    
    with kpi6:
        st.metric(
            label="Inspecciones del Mes",
            value="47",
            delta="+5",
            delta_color="normal",
            help="Total de inspecciones realizadas este mes"
        )
        st.caption("85% aprobadas")
    
    with kpi7:
        st.metric(
            label="Personal en Obra",
            value="68",
            delta="+3",
            delta_color="normal",
            help="Personal presente hoy"
        )
        st.caption("Capacidad: 75")
    
    with kpi8:
        st.metric(
            label="Documentos Pendientes",
            value="8",
            delta="-2",
            delta_color="normal",
            help="Documentos esperando aprobación"
        )
        st.caption("2 urgentes")
    
    st.divider()
    
    # --- GRÁFICOS Y VISUALIZACIONES ---
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("📊 Curva de Avance")
        # Datos simulados para la curva S
        days = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
        progress_data = pd.DataFrame({
            'Fecha': days[:len(days)//2],
            'Avance_Planificado': [min(100, i*0.15) for i in range(len(days)//2)],
            'Avance_Real': [min(100, i*0.14) for i in range(len(days)//2)]
        })
        st.line_chart(
            progress_data.set_index('Fecha'),
            use_container_width=True
        )
        st.caption("Línea azul: Planificado | Línea naranja: Real")
    
    with col_chart2:
        st.subheader("💰 Ejecución Presupuestaria")
        budget = dm.get_budget()
        budget_cats = budget['categories']
        budget_data = pd.DataFrame({
            'Categoría': list(budget_cats.keys()),
            'Presupuestado': [budget_cats[cat]['budget'] for cat in budget_cats],
            'Ejecutado': [budget_cats[cat]['executed'] for cat in budget_cats]
        })
        budget_data['% Ejecutado'] = (budget_data['Ejecutado'] / budget_data['Presupuestado'] * 100).round(1)
        st.bar_chart(
            budget_data.set_index('Categoría')[['% Ejecutado']],
            use_container_width=True
        )
        st.caption("Porcentaje ejecutado por categoría")
    
    st.divider()
    
    # --- ESTADO DE PROYECTOS/ACTIVIDADES ---
    st.subheader("🏗️ Estado de Actividades Principales")
    
    activities = dm.get_activities()
    if activities:
        activities_df = pd.DataFrame(activities)
        if not activities_df.empty:
            # Mapear columnas
            display_df = pd.DataFrame({
                'Actividad': activities_df.get('nombre', ''),
                'Responsable': activities_df.get('responsable', ''),
                'Avance': activities_df.get('avance', 0),
                'Estado': activities_df.get('estado', ''),
                'Fecha_Inicio': activities_df.get('fecha_inicio', ''),
                'Fecha_Fin_Plan': activities_df.get('fecha_fin', '')
            })
            
            st.dataframe(
                display_df,
                column_config={
                    "Avance": st.column_config.ProgressColumn(
                        "Avance (%)",
                        format="%d%%",
                        min_value=0,
                        max_value=100,
                    ),
                    "Estado": st.column_config.TextColumn(
                        "Estado",
                        help="Estado actual de la actividad"
                    ),
                },
                use_container_width=True,
                hide_index=True,
                height=250
            )
        else:
            st.info("No hay actividades registradas. Usa el formulario para agregar actividades.")
    else:
        # Datos de ejemplo si no hay actividades
        activities_df = pd.DataFrame({
            'Actividad': ['Ejemplo: Hormigonado Torre A'],
            'Responsable': ['Equipo Alfa'],
            'Avance': [0],
            'Estado': ['Pendiente'],
            'Fecha_Inicio': [datetime.now().strftime("%d/%m/%Y")],
            'Fecha_Fin_Plan': ['--']
        })
        st.dataframe(activities_df, use_container_width=True, hide_index=True, height=100)
        st.info("💡 Agrega actividades usando el formulario en la sección 'Gestión de Información'")
    
    st.divider()
    
    # --- PERSONAL Y ASISTENCIA ---
    col_personal, col_inspecciones = st.columns(2)
    
    with col_personal:
        st.subheader("👥 Personal en Obra")
        personnel = dm.get_personnel()
        if personnel:
            pers_df = pd.DataFrame(personnel)
            if not pers_df.empty and 'rol' in pers_df.columns:
                # Agrupar por rol
                role_counts = pers_df[pers_df['estado'] == 'Activo']['rol'].value_counts()
                if not role_counts.empty:
                    personal_data = pd.DataFrame({
                        'Equipo': role_counts.index,
                        'Total': role_counts.values,
                        'Presentes': role_counts.values,  # Simplificado, en producción vendría de asistencia
                        'Ausentes': [0] * len(role_counts)
                    })
                    personal_data['% Asistencia'] = 100.0  # Simplificado
                    
                    st.dataframe(
                        personal_data[['Equipo', 'Total']],
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("No hay personal activo registrado")
            else:
                st.info("No hay personal registrado. Usa el formulario para agregar personal.")
        else:
            st.info("💡 Registra personal usando el formulario en 'Gestión de Información'")
    
    with col_inspecciones:
        st.subheader("✅ Inspecciones Recientes")
        inspections = dm.get_inspections()
        if inspections:
            recent_inspections = pd.DataFrame(inspections[:5])
            if 'Fecha' in recent_inspections.columns and 'Resultado' in recent_inspections.columns:
                st.dataframe(
                    recent_inspections[['Fecha', 'Actividad', 'Resultado']],
                    use_container_width=True,
                    hide_index=True,
                    height=200
                )
                
                # Resumen de resultados
                if 'Resultado' in recent_inspections.columns:
                    results_summary = recent_inspections['Resultado'].value_counts()
                    st.bar_chart(results_summary)
            else:
                st.info("No hay datos suficientes de inspecciones")
        else:
            st.info("No hay inspecciones registradas aún")
    
    st.divider()
    
    # --- ALERTAS Y NOTIFICACIONES ---
    st.subheader("⚠️ Alertas y Notificaciones")
    
    alert_col1, alert_col2 = st.columns(2)
    
    with alert_col1:
        st.error("🔴 **CRÍTICO**: Hormigón Torre A retrasado - Impacto en cronograma")
        st.warning("🟡 **IMPORTANTE**: Visita Inspectores Municipales - Mañana 10:00 AM")
        st.info("🔵 **INFORMATIVO**: Nuevo plano estructural v4.3 disponible")
    
    with alert_col2:
        st.warning("🟡 **ATENCIÓN**: RFI #45 requiere respuesta urgente")
        st.info("🔵 **RECORDATORIO**: Reunión de coordinación - Viernes 15:00")
        st.success("🟢 **COMPLETADO**: Inspección de seguridad aprobada")
    
    st.divider()
    
    # --- DOCUMENTOS Y PLANOS ---
    st.subheader("📂 Documentos Recientes")
    docs = dm.get_docs()
    if docs:
        recent_docs = pd.DataFrame(docs[:5])
        display_cols = ["Archivo", "Versión", "Fecha", "Estado"]
        available_cols = [col for col in display_cols if col in recent_docs.columns]
        st.dataframe(
            recent_docs[available_cols],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No hay documentos registrados aún")
    
    st.divider()
    
    # --- RESUMEN DEL DÍA ---
    st.subheader("📅 Resumen del Día")
    summary_col1, summary_col2, summary_col3 = st.columns(3)
    
    with summary_col1:
        st.metric("Inspecciones Hoy", "5")
        st.metric("Documentos Subidos", "3")
    
    with summary_col2:
        st.metric("Incidentes Reportados", "0")
        st.metric("RFI Respondidos", "2")
    
    with summary_col3:
        st.metric("Reuniones Programadas", "1")
        st.metric("Tareas Completadas", "8")
    
    st.divider()
    
    # --- FORMULARIOS PARA INGRESAR INFORMACIÓN ---
    st.subheader("➕ Gestión de Información del Proyecto")
    
    tab_act, tab_pers, tab_bud, tab_mil, tab_imp = st.tabs([
        "🏗️ Actividades", "👥 Personal", "💰 Presupuesto", "📅 Hitos", "💡 Mejoras"
    ])
    
    # TAB: ACTIVIDADES
    with tab_act:
        st.write("**Agregar Nueva Actividad**")
        with st.form("form_activity", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                act_name = st.text_input("Nombre de la Actividad *", placeholder="Ej: Hormigonado Torre A - Piso 8")
                act_responsible = st.text_input("Responsable *", placeholder="Ej: Equipo Alfa")
                act_location = st.text_input("Ubicación", placeholder="Ej: Torre A - Piso 8")
            with col2:
                act_progress = st.number_input("Avance (%)", min_value=0, max_value=100, value=0)
                act_status = st.selectbox("Estado *", ["Pendiente", "En Curso", "Retrasado", "Completado"])
                act_priority = st.selectbox("Prioridad", ["Baja", "Media", "Alta", "Crítica"])
            
            act_start = st.date_input("Fecha de Inicio", value=datetime.now().date())
            act_end = st.date_input("Fecha de Fin Planificada")
            act_notes = st.text_area("Notas adicionales", placeholder="Observaciones, comentarios...")
            
            submitted = st.form_submit_button("Guardar Actividad", type="primary", use_container_width=True)
            
            if submitted:
                if act_name and act_responsible:
                    activity_data = {
                        "nombre": act_name,
                        "responsable": act_responsible,
                        "ubicacion": act_location,
                        "avance": act_progress,
                        "estado": act_status,
                        "prioridad": act_priority,
                        "fecha_inicio": act_start.strftime("%d/%m/%Y"),
                        "fecha_fin": act_end.strftime("%d/%m/%Y") if act_end else None,
                        "notas": act_notes,
                        "created_by": st.session_state.user_info['name']
                    }
                    if dm.add_activity(activity_data):
                        st.success("✅ Actividad agregada correctamente")
                        st.rerun()
                else:
                    st.error("⚠️ Completa los campos obligatorios (*)")
        
        st.divider()
        st.write("**Actividades Registradas**")
        activities = dm.get_activities()
        if activities:
            activities_df = pd.DataFrame(activities)
            if not activities_df.empty:
                display_cols = ["nombre", "responsable", "avance", "estado", "fecha_inicio", "fecha_fin"]
                available_cols = [col for col in display_cols if col in activities_df.columns]
                if available_cols:
                    st.dataframe(
                        activities_df[available_cols],
                        use_container_width=True,
                        hide_index=True,
                        height=200
                    )
        else:
            st.info("No hay actividades registradas aún")
    
    # TAB: PERSONAL
    with tab_pers:
        st.write("**Registrar Personal**")
        with st.form("form_personnel", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                pers_name = st.text_input("Nombre Completo *", placeholder="Ej: Juan Pérez")
                pers_role = st.selectbox("Rol/Cargo *", ["Albañil", "Carpintero", "Electricista", "Plomero", "Supervisor", "Ingeniero", "Arquitecto", "Otro"])
                pers_team = st.text_input("Equipo", placeholder="Ej: Equipo Alfa")
            with col2:
                pers_phone = st.text_input("Teléfono", placeholder="+56 9 1234 5678")
                pers_email = st.text_input("Email")
                pers_status = st.selectbox("Estado", ["Activo", "Inactivo", "Vacaciones"])
            
            submitted = st.form_submit_button("Registrar Personal", type="primary", use_container_width=True)
            
            if submitted:
                if pers_name and pers_role:
                    personnel_data = {
                        "nombre": pers_name,
                        "rol": pers_role,
                        "equipo": pers_team,
                        "telefono": pers_phone,
                        "email": pers_email,
                        "estado": pers_status,
                        "created_by": st.session_state.user_info['name']
                    }
                    if dm.add_personnel(personnel_data):
                        st.success("✅ Personal registrado correctamente")
                        st.rerun()
                else:
                    st.error("⚠️ Completa los campos obligatorios (*)")
        
        st.divider()
        st.write("**Personal Registrado**")
        personnel = dm.get_personnel()
        if personnel:
            pers_df = pd.DataFrame(personnel)
            if not pers_df.empty:
                display_cols = ["nombre", "rol", "equipo", "estado"]
                available_cols = [col for col in display_cols if col in pers_df.columns]
                if available_cols:
                    st.dataframe(
                        pers_df[available_cols],
                        use_container_width=True,
                        hide_index=True,
                        height=200
                    )
        else:
            st.info("No hay personal registrado aún")
    
    # TAB: PRESUPUESTO
    with tab_bud:
        st.write("**Actualizar Presupuesto Ejecutado**")
        budget = dm.get_budget()
        
        st.write(f"**Presupuesto Total:** ${budget['total']:,.0f}")
        st.write(f"**Ejecutado:** ${budget['executed']:,.0f} ({budget['executed']/budget['total']*100:.1f}%)")
        st.progress(budget['executed']/budget['total'])
        
        with st.form("form_budget", clear_on_submit=True):
            budget_category = st.selectbox("Categoría *", list(budget['categories'].keys()))
            budget_amount = st.number_input("Monto Ejecutado ($)", min_value=0.0, value=0.0, step=1000.0)
            budget_notes = st.text_area("Descripción", placeholder="Detalle del gasto...")
            
            submitted = st.form_submit_button("Registrar Gasto", type="primary", use_container_width=True)
            
            if submitted:
                if budget_amount > 0:
                    if dm.update_budget(budget_category, budget_amount):
                        st.success(f"✅ Gasto de ${budget_amount:,.0f} registrado en {budget_category}")
                        st.rerun()
                else:
                    st.error("⚠️ Ingresa un monto válido")
        
        st.divider()
        st.write("**Desglose por Categoría**")
        budget_cats = budget['categories']
        budget_df = pd.DataFrame({
            'Categoría': list(budget_cats.keys()),
            'Presupuestado': [budget_cats[cat]['budget'] for cat in budget_cats],
            'Ejecutado': [budget_cats[cat]['executed'] for cat in budget_cats]
        })
        budget_df['% Ejecutado'] = (budget_df['Ejecutado'] / budget_df['Presupuestado'] * 100).round(1)
        budget_df['Restante'] = budget_df['Presupuestado'] - budget_df['Ejecutado']
        
        st.dataframe(
            budget_df,
            use_container_width=True,
            hide_index=True
        )
    
    # TAB: HITOS
    with tab_mil:
        st.write("**Agregar Hito del Proyecto**")
        with st.form("form_milestone", clear_on_submit=True):
            mil_name = st.text_input("Nombre del Hito *", placeholder="Ej: Finalización Estructura Torre A")
            mil_date = st.date_input("Fecha Planificada *", value=datetime.now().date())
            mil_description = st.text_area("Descripción", placeholder="Detalles del hito...")
            mil_status = st.selectbox("Estado", ["Planificado", "En Progreso", "Completado", "Retrasado"])
            
            submitted = st.form_submit_button("Agregar Hito", type="primary", use_container_width=True)
            
            if submitted:
                if mil_name:
                    milestone_data = {
                        "nombre": mil_name,
                        "fecha": mil_date.strftime("%d/%m/%Y"),
                        "descripcion": mil_description,
                        "estado": mil_status,
                        "created_by": st.session_state.user_info['name']
                    }
                    if dm.add_milestone(milestone_data):
                        st.success("✅ Hito agregado correctamente")
                        st.rerun()
                else:
                    st.error("⚠️ Completa el nombre del hito")
        
        st.divider()
        st.write("**Hitos del Proyecto**")
        milestones = dm.get_milestones()
        if milestones:
            mil_df = pd.DataFrame(milestones)
            if not mil_df.empty:
                display_cols = ["nombre", "fecha", "estado"]
                available_cols = [col for col in display_cols if col in mil_df.columns]
                if available_cols:
                    st.dataframe(
                        mil_df[available_cols],
                        use_container_width=True,
                        hide_index=True,
                        height=200
                    )
        else:
            st.info("No hay hitos registrados aún")
    
    # TAB: MEJORAS
    with tab_imp:
        st.write("**Sugerir Mejora o Cambio**")
        with st.form("form_improvement", clear_on_submit=True):
            imp_title = st.text_input("Título de la Mejora *", placeholder="Ej: Optimizar proceso de hormigonado")
            imp_category = st.selectbox("Categoría *", ["Proceso", "Seguridad", "Calidad", "Eficiencia", "Costo", "Otro"])
            imp_description = st.text_area("Descripción Detallada *", placeholder="Describe la mejora propuesta, beneficios esperados...", height=150)
            imp_priority = st.selectbox("Prioridad", ["Baja", "Media", "Alta", "Crítica"])
            imp_estimated_impact = st.text_area("Impacto Estimado", placeholder="Ahorro de tiempo, reducción de costos, mejora de calidad...")
            
            submitted = st.form_submit_button("Enviar Sugerencia", type="primary", use_container_width=True)
            
            if submitted:
                if imp_title and imp_description:
                    improvement_data = {
                        "titulo": imp_title,
                        "categoria": imp_category,
                        "descripcion": imp_description,
                        "prioridad": imp_priority,
                        "impacto_estimado": imp_estimated_impact,
                        "autor": st.session_state.user_info['name'],
                        "rol_autor": st.session_state.user_info['role']
                    }
                    if dm.add_improvement(improvement_data):
                        st.success("✅ Sugerencia de mejora enviada correctamente")
                        st.rerun()
                else:
                    st.error("⚠️ Completa los campos obligatorios (*)")
        
        st.divider()
        st.write("**Mejoras y Sugerencias**")
        improvements = dm.get_improvements()
        if improvements:
            for imp in improvements:
                status_color = {
                    "Pendiente": "🟡",
                    "En Evaluación": "🔵",
                    "Aprobada": "🟢",
                    "Rechazada": "🔴",
                    "Implementada": "✅"
                }.get(imp.get("status", "Pendiente"), "🟡")
                
                with st.expander(f"{status_color} {imp.get('titulo', 'Sin título')} - {imp.get('status', 'Pendiente')}"):
                    st.write(f"**Categoría:** {imp.get('categoria', 'N/A')}")
                    st.write(f"**Prioridad:** {imp.get('prioridad', 'N/A')}")
                    st.write(f"**Autor:** {imp.get('autor', 'N/A')}")
                    st.write(f"**Descripción:** {imp.get('descripcion', 'Sin descripción')}")
                    if imp.get('impacto_estimado'):
                        st.write(f"**Impacto Estimado:** {imp['impacto_estimado']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"Marcar como Aprobada", key=f"approve_{imp['id']}"):
                            if dm.update_improvement_status(imp['id'], "Aprobada"):
                                st.success("Mejora aprobada")
                                st.rerun()
                    with col2:
                        if st.button(f"Marcar como Implementada", key=f"implement_{imp['id']}"):
                            if dm.update_improvement_status(imp['id'], "Implementada"):
                                st.success("Mejora marcada como implementada")
                                st.rerun()
        else:
            st.info("No hay mejoras registradas aún")

def view_docs():
    st.title("📂 Planos")
    
    # Subida Dual: Archivo (Escritorio) o Cámara (Móvil)
    tab1, tab2 = st.tabs(["📤 Subir Archivo", "📸 Escanear Documento"])
    
    with tab1:
        uploaded_file = st.file_uploader(
            "PDF / DWG", 
            label_visibility="collapsed",
            type=['pdf', 'dwg', 'dwgx', 'dxf'],
            help=f"Tamaño máximo: {MAX_FILE_SIZE_MB}MB"
        )
        if uploaded_file:
            file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
            st.caption(f"📄 {uploaded_file.name} ({file_size_mb:.2f} MB)")
            
            if st.button("Guardar Archivo", use_container_width=True, type="primary"):
                with st.spinner("Subiendo archivo..."):
                    dm.upload_file(uploaded_file, {"version": "v1.0"})
             
    with tab2:
        # Cámara nativa del celular
        img_file = st.camera_input("Tomar foto a documento")
        if img_file:
            # Validar imagen
            is_valid, message = validate_file(img_file, MAX_IMAGE_SIZE_MB, ALLOWED_IMAGE_TYPES + ['.jpg', '.jpeg', '.png'])
            if is_valid:
                st.success("Foto capturada. Procesando...")
                # Aquí se podría implementar OCR
                if st.button("Guardar como Documento", use_container_width=True, type="primary"):
                    # Convertir imagen a formato de archivo para subir
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"scanned_doc_{timestamp}.jpg"
                    img_file.name = filename
                    dm.upload_file(img_file, {"version": "v1.0", "source": "camera"})
            else:
                st.error(message)
            
    st.subheader("Archivos Recientes")
    docs = dm.get_docs()
    if docs:
        # Limitar a 20 registros para mejor rendimiento en móvil
        df = pd.DataFrame(docs[:20])
        # Mostrar solo columnas esenciales en móvil
        display_cols = ["Archivo", "Versión", "Fecha", "Estado"]
        available_cols = [col for col in display_cols if col in df.columns]
        st.dataframe(df[available_cols], use_container_width=True, hide_index=True, height=300)
    else:
        st.info("No hay archivos registrados aún")

def view_qa():
    st.title("✅ Calidad (QA/QC)")
    
    # Formulario Mobile-Friendly
    with st.form("qa_form", clear_on_submit=True):
        st.subheader("Nueva Inspección")
        
        insp_type = st.selectbox("Actividad", ["Enfierradura", "Hormigonado", "Seguridad", "Instalaciones"])
        location = st.text_input("Ubicación (Eje/Piso)", placeholder="Ej: Torre A - Piso 5")
        result = st.radio(
            "Resultado", 
            ["Aprobado", "Con Observaciones", "Rechazado"], 
            horizontal=False  # Vertical en móvil es mejor
        )
        
        # Cámara esencial para QA en terreno
        st.write("📷 Evidencia Fotográfica")
        photo = st.camera_input("Tomar foto", help="La foto se comprimirá automáticamente")
        
        submitted = st.form_submit_button("Guardar Reporte", type="primary", use_container_width=True)
        
        if submitted:
            if not location.strip():
                st.warning("Por favor, ingresa una ubicación")
            else:
                with st.spinner("Guardando inspección..."):
                    new_inspection = {
                        "Fecha": format_date(datetime.now()),
                        "Actividad": f"{insp_type} - {location}",
                        "Auditor": st.session_state.user_info['name'],
                        "Resultado": result,
                        "Tipo": insp_type,
                        "Ubicacion": location
                    }
                    dm.save_inspection(new_inspection, photo)

    st.subheader("Historial")
    inspections = dm.get_inspections()
    if inspections:
        # Limitar a 20 registros
        df = pd.DataFrame(inspections[:20])
        # Columnas esenciales
        display_cols = ["Fecha", "Actividad", "Auditor", "Resultado", "Tiene_Foto"]
        available_cols = [col for col in display_cols if col in df.columns]
        st.dataframe(df[available_cols], use_container_width=True, hide_index=True, height=300)
    else:
        st.info("No hay inspecciones registradas aún")

def view_worker():
    st.markdown("<div class='main-header'>👷 Mi Jornada</div>", unsafe_allow_html=True)
    st.write(f"Bienvenido, **{st.session_state.user_info['name']}**")
    
    # --- ESTADO ACTUAL DE LA JORNADA ---
    current_date = datetime.now().strftime("%d/%m/%Y")
    current_time = datetime.now().strftime("%H:%M")
    
    status_col1, status_col2, status_col3 = st.columns(3)
    
    with status_col1:
        if 'last_entry' in st.session_state:
            st.metric("⏰ Entrada", st.session_state.last_entry)
        else:
            st.metric("⏰ Entrada", "No registrada")
    
    with status_col2:
        if 'last_entry' in st.session_state and 'last_exit' not in st.session_state:
            # Calcular horas trabajadas
            entry_time = datetime.strptime(st.session_state.last_entry, "%H:%M")
            current = datetime.now()
            worked_hours = (current - entry_time.replace(
                year=current.year, month=current.month, day=current.day
            )).total_seconds() / 3600
            st.metric("⏱️ Horas Trabajadas", f"{worked_hours:.1f}h")
        else:
            st.metric("⏱️ Horas Trabajadas", "0h")
    
    with status_col3:
        if 'last_exit' in st.session_state:
            st.metric("🏠 Salida", st.session_state.last_exit)
        else:
            st.metric("🏠 Salida", "No registrada")
    
    st.divider()
    
    # --- BOTONES DE ACCIÓN PRINCIPAL ---
    st.subheader("📍 Registro de Asistencia")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📍 MARCAR ENTRADA", type="primary", use_container_width=True):
            current_time = datetime.now().strftime("%H:%M")
            st.session_state.last_entry = current_time
            st.session_state.entry_date = current_date
            if 'last_exit' in st.session_state:
                del st.session_state.last_exit
            st.toast(f"Entrada registrada: {current_time}", icon="✅")
            st.success(f"✅ Entrada Registrada a las {current_time}")
            st.rerun()
            logger.info(f"Entrada registrada por {st.session_state.user_info['name']} a las {current_time}")
            
    with col2:
        if st.button("🏠 MARCAR SALIDA", use_container_width=True):
            if 'last_entry' not in st.session_state:
                st.warning("⚠️ Debes marcar entrada primero")
            else:
                current_time = datetime.now().strftime("%H:%M")
                st.session_state.last_exit = current_time
                
                # Calcular horas trabajadas
                entry_time = datetime.strptime(st.session_state.last_entry, "%H:%M")
                exit_time = datetime.strptime(current_time, "%H:%M")
                worked_hours = (exit_time - entry_time).total_seconds() / 3600
                if worked_hours < 0:
                    worked_hours += 24
                
                st.session_state.worked_hours_today = worked_hours
                st.toast(f"Salida registrada: {current_time}", icon="🏠")
                st.info(f"Salida Registrada a las {current_time} - {worked_hours:.1f} horas trabajadas")
                logger.info(f"Salida registrada por {st.session_state.user_info['name']} a las {current_time} - {worked_hours:.1f}h")
                st.rerun()

    st.divider()
    
    # --- RESUMEN SEMANAL ---
    st.subheader("📊 Resumen Semanal")
    
    if 'weekly_hours' not in st.session_state:
        st.session_state.weekly_hours = {
            'Lunes': 8.0,
            'Martes': 8.5,
            'Miércoles': 7.5,
            'Jueves': 8.0,
            'Viernes': 0.0,
            'Sábado': 0.0,
            'Domingo': 0.0
        }
    
    weekly_df = pd.DataFrame({
        'Día': list(st.session_state.weekly_hours.keys()),
        'Horas': list(st.session_state.weekly_hours.values())
    })
    
    col_chart, col_summary = st.columns([2, 1])
    
    with col_chart:
        st.bar_chart(weekly_df.set_index('Día'), use_container_width=True)
    
    with col_summary:
        total_hours = sum(st.session_state.weekly_hours.values())
        st.metric("Total Semanal", f"{total_hours:.1f}h")
        avg_hours = total_hours / len([h for h in st.session_state.weekly_hours.values() if h > 0]) if any(st.session_state.weekly_hours.values()) else 0
        st.metric("Promedio Diario", f"{avg_hours:.1f}h")
        st.caption(f"Fecha: {current_date}")
    
    st.divider()
    
    # --- TAREAS Y ASIGNACIONES ---
    st.subheader("📋 Mis Tareas de Hoy")
    
    tasks_data = pd.DataFrame({
        'Tarea': [
            'Enfierradura Torre A - Piso 5',
            'Revisión de instalaciones eléctricas',
            'Limpieza de área de trabajo'
        ],
        'Estado': ['En Progreso', 'Pendiente', 'Completada'],
        'Prioridad': ['Alta', 'Media', 'Baja'],
        'Hora_Límite': ['17:00', '18:00', '16:00']
    })
    
    st.dataframe(
        tasks_data,
        use_container_width=True,
        hide_index=True,
        height=150
    )
    
    st.divider()
    
    # --- NOTIFICACIONES PERSONALES ---
    st.subheader("🔔 Notificaciones")
    
    st.info("📢 **Nueva asignación**: Revisión de enfierradura Torre B - Piso 3")
    st.warning("⏰ **Recordatorio**: Reunión de seguridad a las 15:00")
    st.success("✅ **Completado**: Tu tarea de ayer fue aprobada")
    
    st.divider()
    
    # --- REPORTE DE INCIDENTES ---
    st.subheader("🚨 Reportar Incidente o Observación")
    
    with st.expander("📸 Reportar con Foto", expanded=False):
        incident_photo = st.camera_input("Tomar foto del incidente")
        incident_desc = st.text_area("Descripción del incidente", placeholder="Describe qué ocurrió, dónde y cuándo...")
        
        if st.button("ENVIAR REPORTE", type="primary", use_container_width=True):
            if incident_photo or incident_desc.strip():
                with st.spinner("Enviando reporte..."):
                    st.error("🚨 Reporte enviado a Prevención de Riesgos")
                    st.success("Tu reporte ha sido registrado. El equipo de seguridad se contactará contigo.")
                    logger.warning(f"Incidente reportado por {st.session_state.user_info['name']}")
                    if incident_photo:
                        try:
                            photo_bytes = incident_photo.getvalue()
                            compressed = compress_image(photo_bytes)
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            incident_path = PHOTOS_DIR / f"incident_{timestamp}.jpg"
                            incident_path.write_bytes(compressed)
                            logger.info(f"Foto de incidente guardada: {incident_path}")
                        except Exception as e:
                            logger.error(f"Error guardando foto de incidente: {e}")
            else:
                st.warning("⚠️ Toma una foto o escribe una descripción")
    
    # --- INFORMACIÓN DEL TRABAJADOR ---
    st.divider()
    st.subheader("ℹ️ Mi Información")
    
    info_col1, info_col2 = st.columns(2)
    
    with info_col1:
        st.write("**Equipo:** Albañilería")
        st.write("**Supervisor:** Ing. Carlos Méndez")
        st.write("**Zona de Trabajo:** Torre A")
    
    with info_col2:
        st.write("**Días Trabajados (Mes):** 18")
        st.write("**Horas Totales (Mes):** 144h")
        st.write("**Última Asistencia:** " + (st.session_state.get('entry_date', 'N/A')))

def view_client():
    st.markdown("<div class='main-header'>🏢 Portal del Cliente</div>", unsafe_allow_html=True)
    st.write(f"Bienvenido, **{st.session_state.user_info['name']}**")
    
    # --- KPIs PRINCIPALES PARA CLIENTE ---
    st.subheader("📊 Resumen del Proyecto")
    
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    
    with kpi_col1:
        st.metric("Avance Físico", "65.3%", "+2.1%")
        st.progress(0.653)
        st.caption("Meta: 70% al 31/03")
    
    with kpi_col2:
        budget = dm.get_budget()
        budget_percent = (budget['executed'] / budget['total'] * 100) if budget['total'] > 0 else 0
        st.metric("Avance Financiero", f"{budget_percent:.1f}%", f"${budget['executed']:,.0f}")
        st.progress(budget_percent / 100)
        st.caption("Presupuesto ejecutado")
    
    with kpi_col3:
        st.metric("Días Transcurridos", "245", "+7")
        st.caption("De 365 días totales")
    
    with kpi_col4:
        st.metric("Días Restantes", "120", "-7")
        st.caption("Hasta finalización")
    
    st.divider()
    
    # --- CURVA DE AVANCE Y PRESUPUESTO ---
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("📈 Curva de Avance")
        progress_data = pd.DataFrame({
            'Mes': ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun'],
            'Planificado': [10, 25, 45, 65, 80, 100],
            'Real': [8, 22, 42, 65, 0, 0]
        })
        st.line_chart(
            progress_data.set_index('Mes'),
            use_container_width=True
        )
        st.caption("Comparación planificado vs real")
    
    with col_chart2:
        st.subheader("💰 Ejecución Presupuestaria")
        budget = dm.get_budget()
        budget_cats = budget['categories']
        budget_data = pd.DataFrame({
            'Categoría': list(budget_cats.keys()),
            'Presupuesto': [budget_cats[cat]['budget'] for cat in budget_cats],
            'Ejecutado': [budget_cats[cat]['executed'] for cat in budget_cats]
        })
        budget_data['%'] = (budget_data['Ejecutado'] / budget_data['Presupuesto'] * 100).round(1)
        st.bar_chart(
            budget_data.set_index('Categoría')[['%']],
            use_container_width=True
        )
        st.caption("Porcentaje ejecutado por categoría")
    
    st.divider()
    
    # --- ESTADO DE ACTIVIDADES PRINCIPALES ---
    st.subheader("🏗️ Estado de Actividades")
    
    activities = dm.get_activities()
    if activities:
        activities_df = pd.DataFrame(activities)
        if not activities_df.empty:
            display_df = pd.DataFrame({
                'Actividad': activities_df.get('nombre', ''),
                'Avance': activities_df.get('avance', 0),
                'Estado': activities_df.get('estado', ''),
                'Fecha_Fin_Plan': activities_df.get('fecha_fin', '')
            })
            
            st.dataframe(
                display_df,
                column_config={
                    "Avance": st.column_config.ProgressColumn(
                        "Avance (%)",
                        format="%d%%",
                        min_value=0,
                        max_value=100,
                    ),
                },
                use_container_width=True,
                hide_index=True,
                height=200
            )
        else:
            st.info("No hay actividades registradas aún")
    else:
        st.info("💡 Las actividades se mostrarán aquí cuando el equipo las registre")
    
    st.divider()
    
    # --- GALERÍA DE FOTOS ---
    st.subheader("📸 Galería de Avances")
    
    gallery_col1, gallery_col2, gallery_col3 = st.columns(3)
    
    with gallery_col1:
        st.image("https://via.placeholder.com/400x300?text=Torre+A+-+Piso+8", use_container_width=True)
        st.caption("Torre A - Piso 8 (Hormigonado)")
    
    with gallery_col2:
        st.image("https://via.placeholder.com/400x300?text=Instalaciones+Sanitarias", use_container_width=True)
        st.caption("Instalaciones Sanitarias - Piso 5")
    
    with gallery_col3:
        st.image("https://via.placeholder.com/400x300?text=Fachada+Principal", use_container_width=True)
        st.caption("Fachada Principal - Avance 30%")
    
    if st.button("Ver más fotos", use_container_width=True):
        st.info("📸 Galería completa disponible en la sección de Documentos")
    
    st.divider()
    
    # --- SOLICITUDES Y CAMBIOS ---
    st.subheader("📝 Mis Solicitudes y Cambios")
    
    requests_df = pd.DataFrame({
        'Solicitud': [
            'Cambio de acabados - Piso Hall',
            'Modificación de parking - Nivel -1',
            'Actualización de planos - Torre B',
            'Solicitud de visita técnica'
        ],
        'Fecha': ['15/03/2024', '20/03/2024', '22/03/2024', '25/03/2024'],
        'Estado': ['✅ Aprobado', '⏳ En Evaluación', '✅ Aprobado', '📋 Pendiente'],
        'Responsable': ['Ing. Carlos M.', 'Arq. María T.', 'Ing. Carlos M.', 'Equipo Técnico']
    })
    
    st.dataframe(
        requests_df,
        use_container_width=True,
        hide_index=True,
        height=200
    )
    
    if st.button("➕ Nueva Solicitud", use_container_width=True):
        st.info("💡 Usa el chat para enviar nuevas solicitudes o contacta directamente al equipo")
    
    st.divider()
    
    # --- HITOS Y CALENDARIO ---
    st.subheader("📅 Próximos Hitos Importantes")
    
    milestones = dm.get_milestones()
    if milestones:
        milestones_df = pd.DataFrame(milestones)
        if not milestones_df.empty:
            display_cols = ["nombre", "fecha", "estado"]
            available_cols = [col for col in display_cols if col in milestones_df.columns]
            if available_cols:
                st.dataframe(
                    milestones_df[available_cols],
                    use_container_width=True,
                    hide_index=True,
                    height=150
                )
        else:
            st.info("No hay hitos registrados aún")
    else:
        st.info("💡 Los hitos del proyecto se mostrarán aquí")
    
    st.divider()
    
    # --- MEJORAS Y SUGERENCIAS ---
    st.subheader("💡 Mejoras y Optimizaciones del Proyecto")
    
    improvements = dm.get_improvements()
    if improvements:
        # Filtrar solo mejoras aprobadas o implementadas para el cliente
        client_improvements = [imp for imp in improvements if imp.get('status') in ['Aprobada', 'Implementada']]
        
        if client_improvements:
            for imp in client_improvements[:5]:  # Mostrar máximo 5
                status_icon = "✅" if imp.get('status') == 'Implementada' else "🟢"
                with st.expander(f"{status_icon} {imp.get('titulo', 'Sin título')} - {imp.get('status', 'N/A')}"):
                    st.write(f"**Categoría:** {imp.get('categoria', 'N/A')}")
                    st.write(f"**Descripción:** {imp.get('descripcion', 'Sin descripción')}")
                    if imp.get('impacto_estimado'):
                        st.write(f"**Impacto:** {imp['impacto_estimado']}")
        else:
            st.info("No hay mejoras aprobadas para mostrar")
    else:
        st.info("💡 Las mejoras implementadas se mostrarán aquí")
    
    st.divider()
    
    # --- DOCUMENTOS RELEVANTES ---
    st.subheader("📂 Documentos Recientes")
    
    docs = dm.get_docs()
    if docs:
        recent_docs = pd.DataFrame(docs[:5])
        display_cols = ["Archivo", "Versión", "Fecha", "Estado"]
        available_cols = [col for col in display_cols if col in recent_docs.columns]
        st.dataframe(
            recent_docs[available_cols],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No hay documentos disponibles aún")
    
    st.divider()
    
    # --- RESUMEN Y CONTACTO ---
    st.subheader("ℹ️ Información del Proyecto")
    
    info_col1, info_col2 = st.columns(2)
    
    with info_col1:
        st.write("**Proyecto:** Edificio Residencial Altos del Parque")
        st.write("**Ubicación:** Av. Principal 1234")
        st.write("**Jefe de Obra:** Ing. Carlos Méndez")
        st.write("**Teléfono:** +56 9 1234 5678")
    
    with info_col2:
        st.write("**Fecha Inicio:** 01/01/2024")
        st.write("**Fecha Fin Planificada:** 30/06/2024")
        st.write("**Presupuesto Total:** $9,500,000")
        st.write("**Email Contacto:** obra@constructora.cl")
    
    st.info("💬 Para consultas urgentes, utiliza el chat o contacta directamente al equipo de obra")

def view_chat():
    st.title("💬 Chat")
    
    # Contenedor de chat con altura fija para móvil
    chat_container = st.container()
    with chat_container:
        if not st.session_state.messages:
            st.info("💬 Inicia una conversación...")
        else:
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])

    if prompt := st.chat_input("Escribir..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Simular respuesta (aquí se podría integrar con un bot o API)
        st.session_state.messages.append({
            "role": "assistant", 
            "content": "Mensaje recibido. El chat está en desarrollo."
        })
        st.rerun()

# --- ROUTER PRINCIPAL ---

if not st.session_state.authenticated:
    login()
else:
    # Verificar timeout de sesión
    if not check_session_timeout():
        st.warning("⏱️ Tu sesión ha expirado por inactividad. Por favor, inicia sesión nuevamente.")
        logout()
    else:
        with st.sidebar:
            st.write(f"👤 **{st.session_state.user_info['name']}**")
            st.caption(f"Rol: {st.session_state.user_info['role']}")
            
            # Mostrar tiempo de sesión restante
            if 'last_activity' in st.session_state:
                elapsed = datetime.now() - st.session_state.last_activity
                remaining = SESSION_TIMEOUT_MINUTES - (elapsed.total_seconds() / 60)
                if remaining > 0:
                    st.caption(f"⏱️ Sesión: {int(remaining)} min restantes")
            
            if st.button("Cerrar Sesión", use_container_width=True):
                logout()
            st.divider()
            
            role = st.session_state.user_info['role']
            menu_options = []
            
            if role == "ADMIN":
                menu_options = ["Dashboard", "Documentos", "Calidad", "Chat"]
            elif role == "WORKER":
                menu_options = ["Mi Jornada", "Chat"]
            elif role == "CLIENT":
                menu_options = ["Portal", "Chat"]
                
            selected_page = st.radio("Ir a:", menu_options)

        # Renderizar vista seleccionada
        if role == "ADMIN":
            if selected_page == "Dashboard": view_dashboard_admin()
            elif selected_page == "Documentos": view_docs()
            elif selected_page == "Calidad": view_qa()
            elif selected_page == "Chat": view_chat()
        elif role == "WORKER":
            if selected_page == "Mi Jornada": view_worker()
            elif selected_page == "Chat": view_chat()
        elif role == "CLIENT":
            if selected_page == "Portal": view_client()
            elif selected_page == "Chat": view_chat()
