# 🏗️ G&H Constructores - Sistema de Gestión de Obra

Aplicación web progresiva (PWA) desarrollada en Python con Streamlit, diseñada para digitalizar la gestión de obras de construcción. **Se puede instalar en cualquier móvil como una app nativa.**

![G&H Constructores](https://img.shields.io/badge/G%26H-Constructores-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)
![Streamlit](https://img.shields.io/badge/Streamlit-Latest-red)

## 📱 Características Principales

- ✅ **Instalable en móviles** - Funciona como app nativa (PWA)
- 👥 **Roles diferenciados** - Admin, Trabajador y Cliente
- 📊 **Dashboards profesionales** - Métricas, gráficos y visualizaciones detalladas
- 🏗️ **Gestión de múltiples proyectos** - Trabaja con varios proyectos simultáneamente
- 📂 **Gestión documental** - Subida de planos y documentos
- ✅ **Control de calidad** - Inspecciones con fotos
- 💰 **Gestión de presupuesto** - Seguimiento en tiempo real por proyecto
- 💡 **Sistema de mejoras** - Sugerencias y optimizaciones
- 🎨 **Interfaz profesional** - Diseño moderno con sistema de temas SCSS
- ☁️ **Base de datos local/cloud** - Persistencia de datos por proyecto

## 🚀 Instalación Rápida

### Opción 1: Ejecutar Localmente

```bash
# Clonar repositorio
git clone https://github.com/TU_USUARIO/contech-mobile.git
cd contech-mobile

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar aplicación
streamlit run construction_app.py
```

La app estará disponible en: `http://localhost:8501`

### Opción 2: Desplegar en Streamlit Cloud (GRATIS)

1. **Sube tu código a GitHub**
2. **Ve a https://share.streamlit.io**
3. **Conecta tu repositorio**
4. **¡Despliega!** Tu app estará en: `https://tu-app.streamlit.app`

📖 **Guía completa de despliegue**: Ver [DEPLOY.md](DEPLOY.md)

## 📱 Instalar en Móvil

### Android (Chrome):
1. Abre la URL de tu app en Chrome
2. Menú (⋮) > **"Agregar a la pantalla principal"**
3. La app aparecerá como una app nativa

### iOS (Safari):
1. Abre la URL de tu app en Safari
2. Compartir (□↑) > **"Añadir a pantalla de inicio"**
3. La app aparecerá como una app nativa

## 🔐 Credenciales de Prueba

| Rol | Usuario | Contraseña |
|-----|---------|------------|
| 👔 Jefe de Obra | `jefe` | `admin123` |
| 👷 Trabajador | `obrero` | `obra123` |
| 🏢 Cliente | `cliente` | `cliente123` |

## 🎯 Funcionalidades por Rol

### 👔 Jefe de Obra (Admin)
- Dashboard ejecutivo con KPIs detallados
- **Gestión de múltiples proyectos** - Crear y cambiar entre proyectos
- Gestión de actividades del proyecto
- Registro de personal
- Control de presupuesto por proyecto
- Creación de hitos
- Gestión de mejoras y sugerencias
- Visualización de inspecciones
- Formularios integrados para ingreso de datos

### 👷 Trabajador
- Dashboard personal
- Registro de entrada/salida
- Resumen semanal de horas
- Tareas asignadas
- Reporte de incidentes con foto
- Notificaciones personales

### 🏢 Cliente
- Portal con avance del proyecto
- Visualización de actividades
- Galería de fotos
- Hitos del proyecto
- Mejoras implementadas
- Solicitudes y cambios

## 🛠️ Stack Tecnológico

- **Frontend/Backend**: Python 3.8+ con Streamlit
- **Base de Datos**: JSON local (con soporte para Google Cloud Firestore)
- **Almacenamiento**: Sistema de archivos local (con soporte para Cloud Storage)
- **PWA**: Progressive Web App (instalable en móviles)
- **Despliegue**: Streamlit Cloud, Railway, Render, o servidor propio

## 📦 Estructura del Proyecto

```
App_gyh/
├── construction_app.py      # Aplicación principal
├── logogyh.jpeg            # Logo de G&H Constructores
├── requirements.txt          # Dependencias
├── manifest.json             # Configuración PWA
├── service-worker.js         # Service Worker para offline
├── .streamlit/
│   ├── config.toml          # Configuración Streamlit
│   └── static/             # Archivos estáticos (icons.svg, manifest.json, service-worker.js)
├── data/
│   └── database.json        # Base de datos local (se crea automáticamente, almacena múltiples proyectos)
├── uploads/
│   ├── docs/               # Documentos subidos
│   └── photos/             # Fotos de inspecciones
├── DEPLOY.md                # Guía de despliegue
└── README.md                # Este archivo
```

## 🔧 Configuración

### Variables de Entorno

Para producción, establece:
```bash
export STREAMLIT_ENV=production
```

### Google Cloud Platform (Opcional)

Si quieres usar GCP en lugar de almacenamiento local:

1. Crea un proyecto en Google Cloud
2. Habilita Firestore y Cloud Storage
3. Crea una cuenta de servicio
4. Agrega las credenciales en `.streamlit/secrets.toml` o en Streamlit Cloud Secrets

## 📊 Base de Datos

La aplicación usa una base de datos JSON local (`data/database.json`) que se crea automáticamente. **Cada proyecto tiene sus propios datos independientes:**

- **Proyectos**: Información de múltiples proyectos (nombre, ubicación, presupuesto, fechas)
- **Actividades**: Tareas y actividades por proyecto
- **Personal**: Registro de trabajadores por proyecto
- **Presupuesto**: Control de gastos por categoría y proyecto
- **Hitos**: Eventos importantes del proyecto
- **Mejoras**: Sugerencias y optimizaciones por proyecto
- **Alertas**: Notificaciones del sistema

## 🚀 Despliegue

### Streamlit Cloud (Recomendado - Gratis)

1. Sube tu código a GitHub
2. Ve a https://share.streamlit.io
3. Conecta tu repositorio
4. ¡Despliega!

### Otros Servicios

- **Railway**: https://railway.app
- **Render**: https://render.com
- **Heroku**: https://heroku.com

📖 **Ver [DEPLOY.md](DEPLOY.md) para instrucciones detalladas**

## 📱 Uso en Móvil

Una vez desplegada la aplicación:

1. **Abre la URL en tu móvil** (Chrome en Android, Safari en iOS)
2. **Agrega a la pantalla principal** desde el menú del navegador
3. **¡Listo!** La app funcionará como una app nativa

### Características Móviles

- ✅ Pantalla completa
- ✅ Sin barra de navegación del navegador
- ✅ Icono en la pantalla de inicio
- ✅ Funcionalidad offline básica
- ✅ Optimizado para touch

## 🐛 Solución de Problemas

### La app no se instala en móvil
- Verifica que uses **HTTPS** (no HTTP)
- Asegúrate de que el manifest.json sea accesible
- Revisa la consola del navegador para errores

### Service Worker no funciona
- Verifica que el archivo esté en la ubicación correcta
- Revisa la consola del navegador
- Asegúrate de que el servidor sirva archivos estáticos

### La app no carga
- Verifica que todas las dependencias estén en `requirements.txt`
- Revisa los logs del servidor
- Verifica que el puerto esté correctamente configurado

## 📝 Licencia

Este proyecto es de código abierto. Siéntete libre de usarlo y modificarlo.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📞 Soporte

Para más información:
- 📖 Documentación de Streamlit: https://docs.streamlit.io
- ☁️ Streamlit Cloud: https://docs.streamlit.io/streamlit-community-cloud
- 🐛 Reportar bugs: Abre un issue en GitHub

---

## 🆕 Novedades v2.0

- ✨ **Sistema de múltiples proyectos** - Gestiona varios proyectos simultáneamente
- 🎨 **Interfaz profesional mejorada** - Sistema de temas SCSS, iconos SVG profesionales
- 🏢 **Branding G&H Constructores** - Logo y nombre de empresa integrados
- 📊 **Dashboards mejorados** - Información más detallada y profesional
- 💬 **Feedback mejorado** - Mensajes de éxito, validaciones y spinners
- 📱 **UX optimizada** - Mejor experiencia en móviles y escritorio

---

**Desarrollado con ❤️ para G&H Constructores**

