ConTech Mobile - Plataforma de Gestión de Obra

ConTech Mobile es una aplicación web progresiva (PWA) desarrollada en Python con Streamlit, diseñada para digitalizar la gestión de obras de construcción. Permite conectar a la Oficina Técnica, el Terreno y al Cliente en una única interfaz accesible desde cualquier dispositivo móvil o computadora.

🚀 Características Principales

Roles Diferenciados: Acceso personalizado para Jefe de Obra (Admin), Trabajador y Cliente.

Gestión Documental: Subida y visualización de planos (PDF/DWG) con control de versiones.

Calidad y Seguridad (QA/QC): Formularios de inspección con captura fotográfica desde el celular.

Portal del Trabajador: Marcaje de asistencia GPS y reporte de incidentes SOS.

Portal del Cliente: Visualización de avance financiero/físico y gestión de solicitudes.

Chat Interno: Comunicación en tiempo real entre los equipos.

Integración Nube: Conectividad nativa con Google Cloud Platform (GCP) para base de datos (Firestore) y archivos (Cloud Storage).

🛠️ Stack Tecnológico

Frontend/Backend: Python 3 + Streamlit

Base de Datos: Google Cloud Firestore (NoSQL)

Almacenamiento: Google Cloud Storage

Despliegue: Streamlit Community Cloud

💻 Instalación Local (Para Desarrolladores)

Sigue estos pasos para ejecutar el proyecto en tu computadora:

Clonar el repositorio:

git clone [https://github.com/TU_USUARIO/contech-mobile.git](https://github.com/TU_USUARIO/contech-mobile.git)
cd contech-mobile


Crear entorno virtual (Recomendado):

python -m venv venv
# En Windows:
.\venv\Scripts\activate
# En Mac/Linux:
source venv/bin/activate


Instalar dependencias:

pip install -r requirements.txt


Ejecutar la aplicación:

streamlit run construction_app.py


☁️ Configuración de Google Cloud Platform (GCP)

Para que la base de datos y la subida de archivos funcionen en la nube, necesitas configurar GCP.

Paso 1: Crear Credenciales

Ve a la Consola de Google Cloud.

Crea un nuevo proyecto (ej: contech-app).

Habilita las APIs: Cloud Firestore API y Cloud Storage API.

Ve a IAM y administración > Cuentas de servicio > Crear cuenta de servicio.

Dale permisos de Editor (o específicos para Firestore/Storage).

En la cuenta creada, ve a la pestaña Claves > Agregar clave > Crear nueva clave > JSON.

Se descargará un archivo .json a tu computadora. ¡NO SUBAS ESTE ARCHIVO A GITHUB!

Paso 2: Configurar Secretos (Modo Local)

Para probar la conexión a GCP desde tu PC sin exponer tu clave:

Crea una carpeta llamada .streamlit en la raíz de tu proyecto.

Dentro, crea un archivo llamado secrets.toml.

Copia el contenido de tu archivo JSON descargado y pégalo con este formato:

# Archivo: .streamlit/secrets.toml

[gcp_service_account]
type = "service_account"
project_id = "tu-project-id"
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----..."
client_email = "tu-email@..."
client_id = "..."
auth_uri = "[https://accounts.google.com/o/oauth2/auth](https://accounts.google.com/o/oauth2/auth)"
token_uri = "[https://oauth2.googleapis.com/token](https://oauth2.googleapis.com/token)"
auth_provider_x509_cert_url = "[https://www.googleapis.com/oauth2/v1/certs](https://www.googleapis.com/oauth2/v1/certs)"
client_x509_cert_url = "..."


🚀 Despliegue en la Nube (Streamlit Cloud)

Para que la app funcione 24/7 y sea accesible desde celulares:

Sube tu código a GitHub (asegúrate de incluir requirements.txt).

Ve a share.streamlit.io y conecta tu repositorio.

Antes de darle a "Deploy", ve a Advanced Settings (Configuración Avanzada) o, una vez creada la app, ve a Settings > Secrets.

Copia el contenido de tu secrets.toml (las credenciales de GCP) y pégalo en el área de texto de Secrets.

Guarda y reinicia la app.

¡Listo! Streamlit Cloud usará esas credenciales secretas para conectarse a Google sin que tus claves sean públicas en el código.

🔐 Credenciales de Prueba (Demo)

Si no has configurado tu propia base de datos de usuarios en GCP, utiliza estos accesos por defecto:

Rol

Usuario

Contraseña

Jefe de Obra

jefe

admin123

Trabajador

obrero

obra123

Cliente

cliente

cliente123

📱 Uso en Móvil

Abre el enlace de tu app desplegada (ej: https://mi-app.streamlit.app) en Chrome (Android) o Safari (iOS).

Abre el menú del navegador y selecciona "Agregar a la pantalla principal" o "Instalar App".

La aplicación se comportará como una app nativa en pantalla completa.