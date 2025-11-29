# 🚀 Guía de Despliegue - G&H Constructores

Esta guía te ayudará a desplegar el Sistema de Gestión de Obra de G&H Constructores para que sea accesible desde cualquier móvil.

## 📱 Opción 1: Desplegar en Streamlit Cloud (RECOMENDADO - GRATIS)

### Pasos:

1. **Sube tu código a GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit - G&H Constructores"
   git branch -M main
   git remote add origin https://github.com/TU_USUARIO/contech-mobile.git
   git push -u origin main
   ```

2. **Crea cuenta en Streamlit Cloud**
   - Ve a https://share.streamlit.io
   - Inicia sesión con tu cuenta de GitHub
   - Haz clic en "New app"

3. **Configura la aplicación**
   - **Repository**: Selecciona tu repositorio
   - **Branch**: `main`
   - **Main file path**: `construction_app.py`
   - Haz clic en "Deploy!"

4. **Configura Secrets (Opcional - Solo si usas GCP)**
   - Ve a Settings > Secrets
   - Pega tu configuración de GCP en formato TOML:
   ```toml
   [gcp_service_account]
   type = "service_account"
   project_id = "tu-project-id"
   # ... resto de credenciales
   ```

5. **¡Listo!** Tu app estará disponible en: `https://tu-app.streamlit.app`

### Instalar en Móvil:

**Android (Chrome):**
1. Abre la URL en Chrome
2. Menú (3 puntos) > "Agregar a la pantalla principal"
3. La app aparecerá como una app nativa

**iOS (Safari):**
1. Abre la URL en Safari
2. Compartir > "Añadir a pantalla de inicio"
3. La app aparecerá como una app nativa

---

## 📱 Opción 2: Desplegar en tu propio servidor

### Requisitos:
- Servidor con Python 3.8+
- Dominio o IP pública
- Certificado SSL (para HTTPS - requerido para PWA)

### Pasos:

1. **Instala dependencias en el servidor**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configura Streamlit para producción**
   Crea `.streamlit/config.toml`:
   ```toml
   [server]
   port = 8501
   enableCORS = false
   enableXsrfProtection = true
   ```

3. **Ejecuta con PM2 (recomendado)**
   ```bash
   npm install -g pm2
   pm2 start streamlit -- run construction_app.py
   pm2 save
   pm2 startup
   ```

4. **Configura Nginx como proxy reverso**
   ```nginx
   server {
       listen 80;
       server_name tu-dominio.com;
       
       location / {
           proxy_pass http://localhost:8501;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

5. **Configura SSL con Let's Encrypt**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d tu-dominio.com
   ```

---

## 📱 Opción 3: Usar Railway, Render o Heroku

### Railway (Recomendado - Fácil):
1. Ve a https://railway.app
2. Conecta tu repositorio de GitHub
3. Railway detectará automáticamente que es una app Python
4. Agrega el comando: `streamlit run construction_app.py --server.port $PORT`
5. ¡Despliega!

### Render:
1. Ve a https://render.com
2. Crea un nuevo "Web Service"
3. Conecta tu repositorio
4. Configura:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run construction_app.py --server.port $PORT --server.address 0.0.0.0`
5. ¡Despliega!

---

## 🔧 Configuración Adicional para PWA

### Verificar que PWA funciona:

1. **Abre la app en Chrome DevTools**
   - F12 > Application > Manifest
   - Debe mostrar el manifest correctamente

2. **Verifica Service Worker**
   - F12 > Application > Service Workers
   - Debe estar registrado y activo

3. **Prueba en móvil**
   - Abre la URL en tu móvil
   - Debe aparecer la opción "Agregar a pantalla principal"

---

## 📝 Notas Importantes

- **HTTPS es obligatorio** para PWA en producción
- Los archivos estáticos deben estar en `.streamlit/static/`
- El manifest.json debe ser accesible en la raíz
- El service-worker.js debe estar en la raíz o en static/

---

## 🐛 Solución de Problemas

### La app no se instala en móvil:
- Verifica que uses HTTPS (no HTTP)
- Revisa que el manifest.json sea accesible
- Verifica la consola del navegador para errores

### Service Worker no funciona:
- Verifica que el archivo esté en la ubicación correcta
- Revisa la consola del navegador
- Asegúrate de que el servidor sirva archivos estáticos

### La app no carga:
- Verifica que todas las dependencias estén en requirements.txt
- Revisa los logs del servidor
- Verifica que el puerto esté correctamente configurado

---

## 📞 Soporte

Para más ayuda, consulta:
- Documentación de Streamlit: https://docs.streamlit.io
- Streamlit Cloud: https://docs.streamlit.io/streamlit-community-cloud

