# 📝 Instrucciones para Subir a GitHub

## Paso 1: Crear el Repositorio en GitHub

1. Ve a https://github.com y inicia sesión
2. Haz clic en el botón **"+"** (arriba a la derecha) > **"New repository"**
3. Completa:
   - **Repository name**: `contech-mobile`
   - **Description**: "Aplicación móvil de gestión de obra - ConTech Mobile"
   - **Visibility**: Público o Privado (tú decides)
   - **NO marques** "Initialize with README" (ya tienes archivos)
4. Haz clic en **"Create repository"**

## Paso 2: Subir tu Código

Una vez creado el repositorio, ejecuta estos comandos en tu terminal:

```bash
# Verificar que estás en la rama master
git branch

# Si necesitas agregar archivos nuevos
git add .

# Si hay cambios, hacer commit
git commit -m "Actualización: PWA y mejoras"

# Hacer push a master (no main)
git push -u origin master
```

## Si el repositorio ya existe pero con otro nombre:

Puedes cambiar el remoto:

```bash
# Ver remoto actual
git remote -v

# Cambiar remoto
git remote set-url origin https://github.com/miguellucero123/TU-REPOSITORIO.git

# Hacer push
git push -u origin master
```

## Si quieres renombrar la rama a "main":

```bash
# Renombrar rama master a main
git branch -M main

# Hacer push
git push -u origin main
```

## Solución de Problemas

### Error: "Repository not found"
- Verifica que el repositorio existe en GitHub
- Verifica que tienes permisos de escritura
- Verifica que el nombre del usuario es correcto

### Error: "Authentication failed"
- Necesitas autenticarte. Opciones:
  1. Usar GitHub CLI: `gh auth login`
  2. Usar Personal Access Token en lugar de contraseña
  3. Configurar SSH keys

### Error: "Permission denied"
- Verifica que estás logueado en GitHub
- Verifica que tienes acceso al repositorio

