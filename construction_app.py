import streamlit as st
import pandas as pd
import time
import os
import logging
import json
import base64
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
    page_title="G&H Constructores - Gestión de Obra",
    page_icon="🏗️",
    layout="wide", # En celular se colapsa automáticamente a una columna
    initial_sidebar_state="auto", # En celular arranca cerrado
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "G&H Constructores - Sistema de Gestión de Obra v2.0"
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

# --- SISTEMA DE TEMAS ESCALONADO Y ESTILOS PROFESIONALES ---
st.markdown("""
<style>
    /* ============================================
       VARIABLES CSS - SISTEMA DE TEMAS ESCALONADO
       ============================================ */
    :root {
        /* Tema Principal - Azul Profesional G&H Constructores */
        --primary-color: #1e40af;
        --primary-dark: #1e3a8a;
        --primary-light: #3b82f6;
        --secondary-color: #64748b;
        --accent-color: #0ea5e9;
        --company-primary: #1e40af;
        --company-secondary: #64748b;
        
        /* Colores de Fondo */
        --bg-primary: #ffffff;
        --bg-secondary: #f8fafc;
        --bg-tertiary: #f1f5f9;
        --bg-card: #ffffff;
        
        /* Colores de Texto */
        --text-primary: #0f172a;
        --text-secondary: #475569;
        --text-muted: #94a3b8;
        
        /* Bordes y Sombras */
        --border-color: #e2e8f0;
        --border-radius: 12px;
        --border-radius-sm: 8px;
        --border-radius-lg: 16px;
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        
        /* Estados */
        --success-color: #10b981;
        --warning-color: #f59e0b;
        --error-color: #ef4444;
        --info-color: #3b82f6;
        
        /* Espaciado */
        --spacing-xs: 4px;
        --spacing-sm: 8px;
        --spacing-md: 16px;
        --spacing-lg: 24px;
        --spacing-xl: 32px;
        
        /* Transiciones */
        --transition-fast: 150ms ease-in-out;
        --transition-base: 250ms ease-in-out;
        --transition-slow: 350ms ease-in-out;
    }
    
    /* Tema Oscuro (si se implementa) */
    [data-theme="dark"] {
        --bg-primary: #0f172a;
        --bg-secondary: #1e293b;
        --bg-tertiary: #334155;
        --text-primary: #f1f5f9;
        --text-secondary: #cbd5e1;
        --border-color: #334155;
    }
    
    /* ============================================
       ESTILOS BASE Y RESET
       ============================================ */
    * {
        box-sizing: border-box;
    }
    
    /* Logo de la empresa */
    .company-logo {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: var(--spacing-md) 0;
        margin-bottom: var(--spacing-lg);
    }
    
    .company-logo img {
        max-height: 80px;
        width: auto;
        object-fit: contain;
    }
    
    .company-header {
        text-align: center;
        margin-bottom: var(--spacing-lg);
    }
    
    .company-name {
        font-size: 1.8rem;
        font-weight: 700;
        color: var(--primary-color);
        letter-spacing: 0.05em;
        margin: var(--spacing-sm) 0;
    }
    
    .company-tagline {
        font-size: 0.9rem;
        color: var(--text-secondary);
        font-weight: 400;
    }
    
    .main-header {
        color: var(--text-primary);
        font-weight: 700;
        font-size: 2rem;
        margin-bottom: var(--spacing-lg);
        letter-spacing: -0.02em;
        display: flex;
        align-items: center;
        gap: var(--spacing-sm);
    }
    
    .main-header .icon {
        display: inline-block;
        vertical-align: middle;
    }
    
    /* ============================================
       MÉTRICAS Y CARDS
       ============================================ */
    .stMetric {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        padding: var(--spacing-lg);
        border-radius: var(--border-radius);
        box-shadow: var(--shadow-sm);
        transition: all var(--transition-base);
        position: relative;
        overflow: hidden;
    }
    
    .stMetric::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: var(--primary-color);
        transition: width var(--transition-base);
    }
    
    .stMetric:hover {
        box-shadow: var(--shadow-md);
        transform: translateY(-2px);
    }
    
    .stMetric:hover::before {
        width: 6px;
    }
    
    /* ============================================
       BOTONES PROFESIONALES MEJORADOS
       ============================================ */
    .stButton > button {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-dark) 100%);
        color: white !important;
        border: none !important;
        border-radius: var(--border-radius) !important;
        padding: var(--spacing-md) var(--spacing-lg) !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        transition: all var(--transition-base) !important;
        box-shadow: var(--shadow-sm) !important;
        position: relative;
        overflow: hidden;
        min-height: 48px !important;
        cursor: pointer !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 8px !important;
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 0;
        height: 0;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.2);
        transform: translate(-50%, -50%);
        transition: width 0.6s, height 0.6s;
        pointer-events: none;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: var(--shadow-md) !important;
        background: linear-gradient(135deg, var(--primary-light) 0%, var(--primary-color) 100%) !important;
    }
    
    .stButton > button:hover::before {
        width: 300px;
        height: 300px;
    }
    
    .stButton > button:active {
        transform: translateY(0) !important;
        box-shadow: var(--shadow-sm) !important;
    }
    
    .stButton > button:focus {
        outline: 2px solid var(--primary-light) !important;
        outline-offset: 2px !important;
    }
    
    .stButton > button:disabled {
        opacity: 0.6 !important;
        cursor: not-allowed !important;
    }
    
    /* Botón Secundario */
    .stButton > button[kind="secondary"] {
        background: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
    }
    
    .stButton > button[kind="secondary"]:hover {
        background: var(--bg-tertiary) !important;
        border-color: var(--primary-color) !important;
    }
    
    /* Botones de descarga */
    .stDownloadButton > button {
        background: linear-gradient(135deg, var(--success-color) 0%, #059669 100%) !important;
    }
    
    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #059669 0%, var(--success-color) 100%) !important;
    }
    
    /* ============================================
       INPUTS Y FORMULARIOS
       ============================================ */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {
        border: 2px solid var(--border-color);
        border-radius: var(--border-radius-sm);
        padding: var(--spacing-md);
        font-size: 16px;
        transition: all var(--transition-base);
        background: var(--bg-primary);
        color: var(--text-primary);
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 3px rgba(30, 64, 175, 0.1);
        outline: none;
    }
    
    .stTextInput > div > div > input:hover,
    .stTextArea > div > div > textarea:hover {
        border-color: var(--primary-light);
    }
    
    /* ============================================
       TABS PROFESIONALES
       ============================================ */
    .stTabs [data-baseweb="tab-list"] {
        gap: var(--spacing-sm);
        border-bottom: 2px solid var(--border-color);
        padding-bottom: var(--spacing-sm);
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: var(--spacing-md) var(--spacing-lg);
        border-radius: var(--border-radius-sm) var(--border-radius-sm) 0 0;
        transition: all var(--transition-base);
        font-weight: 500;
        color: var(--text-secondary);
        min-height: 48px;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: var(--bg-secondary);
        color: var(--primary-color);
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--bg-primary);
        color: var(--primary-color);
        border-bottom: 3px solid var(--primary-color);
        font-weight: 600;
    }
    
    /* ============================================
       DATAFRAMES Y TABLAS
       ============================================ */
    .stDataFrame {
        border-radius: var(--border-radius);
        overflow: hidden;
        box-shadow: var(--shadow-sm);
        border: 1px solid var(--border-color);
    }
    
    .dataframe {
        font-size: 14px;
    }
    
    .dataframe thead {
        background: var(--bg-secondary);
        color: var(--text-primary);
        font-weight: 600;
    }
    
    .dataframe tbody tr {
        transition: background var(--transition-fast);
    }
    
    .dataframe tbody tr:hover {
        background: var(--bg-secondary);
    }
    
    /* ============================================
       RADIO BUTTONS Y CHECKBOXES
       ============================================ */
    .stRadio > div {
        gap: var(--spacing-sm);
    }
    
    .stRadio label {
        padding: var(--spacing-md);
        border-radius: var(--border-radius-sm);
        transition: all var(--transition-base);
        cursor: pointer;
        min-height: 44px;
        display: flex;
        align-items: center;
    }
    
    .stRadio label:hover {
        background: var(--bg-secondary);
    }
    
    .stRadio input[type="radio"]:checked + label {
        background: var(--primary-color);
        color: white;
        font-weight: 600;
    }
    
    /* ============================================
       ALERTAS Y NOTIFICACIONES
       ============================================ */
    .stAlert {
        border-radius: var(--border-radius);
        border-left: 4px solid;
        padding: var(--spacing-lg);
        box-shadow: var(--shadow-sm);
    }
    
    .stAlert[data-baseweb="alert"] {
        border-left-color: var(--info-color);
    }
    
    /* ============================================
       ICONOS SVG PROFESIONALES
       ============================================ */
    .icon {
        width: 20px;
        height: 20px;
        display: inline-block;
        vertical-align: middle;
        margin-right: var(--spacing-sm);
        fill: currentColor;
    }
    
    .icon-lg {
        width: 24px;
        height: 24px;
    }
    
    .icon-sm {
        width: 16px;
        height: 16px;
    }
    
    /* ============================================
       BOTONES DE ACCIÓN CON ICONOS
       ============================================ */
    .action-button {
        display: inline-flex;
        align-items: center;
        gap: var(--spacing-sm);
        padding: var(--spacing-sm) var(--spacing-md);
        border-radius: var(--border-radius-sm);
        border: 1px solid var(--border-color);
        background: var(--bg-primary);
        color: var(--text-primary);
        cursor: pointer;
        transition: all var(--transition-base);
        font-size: 14px;
        font-weight: 500;
    }
    
    .action-button:hover {
        background: var(--bg-secondary);
        border-color: var(--primary-color);
        color: var(--primary-color);
        transform: translateY(-1px);
        box-shadow: var(--shadow-sm);
    }
    
    .action-button.download {
        background: linear-gradient(135deg, var(--success-color) 0%, #059669 100%);
        color: white;
        border: none;
    }
    
    .action-button.download:hover {
        background: linear-gradient(135deg, #059669 0%, var(--success-color) 100%);
        box-shadow: var(--shadow-md);
    }
    
    /* ============================================
       CARDS Y CONTENEDORES
       ============================================ */
    .card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: var(--border-radius);
        padding: var(--spacing-lg);
        box-shadow: var(--shadow-sm);
        transition: all var(--transition-base);
    }
    
    .card:hover {
        box-shadow: var(--shadow-md);
        transform: translateY(-2px);
    }
    
    /* ============================================
       OPTIMIZACIONES MÓVIL
       ============================================ */
    @media (max-width: 768px) {
        .main-header {
            font-size: 1.5rem !important;
            text-align: center;
        }
        
        .stButton > button {
            min-height: 55px !important;
            font-size: 18px !important;
            width: 100% !important;
            margin-bottom: var(--spacing-md) !important;
        }
        
        .stRadio > div {
            flex-direction: column !important;
        }
        
        .stRadio label {
            min-height: 48px !important;
            padding: var(--spacing-md) !important;
        }
        
        .stTabs [data-baseweb="tab"] {
            min-height: 48px !important;
            padding: var(--spacing-md) var(--spacing-lg) !important;
            font-size: 14px;
        }
        
        .dataframe {
            font-size: 12px !important;
        }
        
        .stTextInput input,
        .stTextArea textarea {
            font-size: 16px !important;
        }
        
        .desktop-only {
            display: none !important;
        }
    }
    
    /* ============================================
       ANIMACIONES Y TRANSICIONES
       ============================================ */
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes slideIn {
        from {
            transform: translateX(-20px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    .fade-in {
        animation: fadeIn var(--transition-base);
    }
    
    .slide-in {
        animation: slideIn var(--transition-base);
    }
    
    /* ============================================
       MEJORAS GENERALES
       ============================================ */
    .stDataFrame {
        overflow-x: auto;
    }
    
    /* Scrollbar personalizado */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--bg-secondary);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--border-color);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--text-muted);
    }
    
    /* ============================================
       ESTILOS PROFESIONALES ADICIONALES
       ============================================ */
    
    /* Sidebar mejorado */
    .css-1d391kg {
        background: linear-gradient(180deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
    }
    
    /* Mejoras en contenedores */
    .stContainer {
        padding: var(--spacing-md);
    }
    
    /* Cards con sombra profesional */
    .project-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: var(--border-radius);
        padding: var(--spacing-lg);
        margin-bottom: var(--spacing-md);
        box-shadow: var(--shadow-sm);
        transition: all var(--transition-base);
    }
    
    .project-card:hover {
        box-shadow: var(--shadow-md);
        transform: translateY(-2px);
        border-color: var(--primary-color);
    }
    
    /* Mejoras en formularios */
    .stForm {
        background: var(--bg-secondary);
        padding: var(--spacing-lg);
        border-radius: var(--border-radius);
        border: 1px solid var(--border-color);
    }
    
    /* Badges y etiquetas */
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .badge-success {
        background: var(--success-color);
        color: white;
    }
    
    .badge-warning {
        background: var(--warning-color);
        color: white;
    }
    
    .badge-error {
        background: var(--error-color);
        color: white;
    }
    
    .badge-info {
        background: var(--info-color);
        color: white;
    }
    
    /* Mejoras en tablas */
    .dataframe {
        border-collapse: separate;
        border-spacing: 0;
    }
    
    .dataframe th {
        background: linear-gradient(180deg, var(--primary-color) 0%, var(--primary-dark) 100%);
        color: white;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 0.5px;
        padding: var(--spacing-md);
    }
    
    .dataframe td {
        padding: var(--spacing-md);
        border-bottom: 1px solid var(--border-color);
    }
    
    .dataframe tr:last-child td {
        border-bottom: none;
    }
    
    /* Mejoras en selectores */
    .stSelectbox > div > div {
        background: var(--bg-primary);
        border: 2px solid var(--border-color);
        border-radius: var(--border-radius-sm);
    }
    
    .stSelectbox > div > div:hover {
        border-color: var(--primary-light);
    }
    
    /* Mejoras en expanders */
    .streamlit-expanderHeader {
        font-weight: 600;
        color: var(--text-primary);
    }
    
    /* Efectos de hover mejorados */
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(30, 64, 175, 0.3);
    }
    
    /* Mejoras en métricas */
    .stMetric {
        background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-secondary) 100%);
    }
    
    /* Footer profesional */
    .footer {
        text-align: center;
        padding: var(--spacing-lg);
        color: var(--text-muted);
        font-size: 0.875rem;
        border-top: 1px solid var(--border-color);
        margin-top: var(--spacing-xl);
    }
    
    /* ============================================
       MEJORAS ADICIONALES - ANIMACIONES Y ESTADOS
       ============================================ */
    
    /* Animación de carga en botones */
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .button-loading {
        position: relative;
        pointer-events: none;
    }
    
    .button-loading::after {
        content: '';
        position: absolute;
        width: 16px;
        height: 16px;
        margin: auto;
        border: 2px solid transparent;
        border-top-color: white;
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
    }
    
    /* Tooltips mejorados */
    .tooltip-container {
        position: relative;
        display: inline-block;
    }
    
    .tooltip-text {
        visibility: hidden;
        width: 200px;
        background-color: var(--text-primary);
        color: var(--bg-primary);
        text-align: center;
        border-radius: var(--border-radius-sm);
        padding: var(--spacing-sm) var(--spacing-md);
        position: absolute;
        z-index: 1000;
        bottom: 125%;
        left: 50%;
        margin-left: -100px;
        opacity: 0;
        transition: opacity var(--transition-base);
        font-size: 0.875rem;
        box-shadow: var(--shadow-lg);
    }
    
    .tooltip-container:hover .tooltip-text {
        visibility: visible;
        opacity: 1;
    }
    
    /* Indicadores de estado mejorados */
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: var(--spacing-sm);
        animation: pulse 2s infinite;
    }
    
    .status-indicator.success {
        background-color: var(--success-color);
    }
    
    .status-indicator.warning {
        background-color: var(--warning-color);
    }
    
    .status-indicator.error {
        background-color: var(--error-color);
    }
    
    .status-indicator.info {
        background-color: var(--info-color);
    }
    
    @keyframes pulse {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: 0.5;
        }
    }
    
    /* Mejoras en notificaciones */
    .notification-toast {
        position: fixed;
        top: 20px;
        right: 20px;
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: var(--border-radius);
        padding: var(--spacing-md) var(--spacing-lg);
        box-shadow: var(--shadow-lg);
        z-index: 9999;
        animation: slideInRight 0.3s ease-out;
        max-width: 400px;
    }
    
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    /* Mejoras en campos de formulario */
    .form-field-required::after {
        content: ' *';
        color: var(--error-color);
        font-weight: bold;
    }
    
    .form-field-error {
        border-color: var(--error-color) !important;
        box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1) !important;
    }
    
    .form-field-success {
        border-color: var(--success-color) !important;
        box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1) !important;
    }
    
    /* Mejoras en cards interactivas */
    .interactive-card {
        cursor: pointer;
        transition: all var(--transition-base);
    }
    
    .interactive-card:hover {
        transform: translateY(-4px);
        box-shadow: var(--shadow-lg);
    }
    
    .interactive-card:active {
        transform: translateY(-2px);
    }
    
    /* Mejoras en spinners */
    .spinner-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.3);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
    }
    
    .spinner {
        width: 50px;
        height: 50px;
        border: 4px solid var(--bg-secondary);
        border-top-color: var(--primary-color);
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    /* Mejoras en mensajes de éxito/error */
    .message-box {
        padding: var(--spacing-md) var(--spacing-lg);
        border-radius: var(--border-radius);
        margin-bottom: var(--spacing-md);
        display: flex;
        align-items: center;
        gap: var(--spacing-md);
    }
    
    .message-box.success {
        background: rgba(16, 185, 129, 0.1);
        border-left: 4px solid var(--success-color);
        color: #065f46;
    }
    
    .message-box.error {
        background: rgba(239, 68, 68, 0.1);
        border-left: 4px solid var(--error-color);
        color: #991b1b;
    }
    
    .message-box.warning {
        background: rgba(245, 158, 11, 0.1);
        border-left: 4px solid var(--warning-color);
        color: #92400e;
    }
    
    .message-box.info {
        background: rgba(59, 130, 246, 0.1);
        border-left: 4px solid var(--info-color);
        color: #1e40af;
    }
    
    /* Mejoras en tablas con hover mejorado */
    .dataframe tbody tr {
        transition: all var(--transition-fast);
    }
    
    .dataframe tbody tr:hover {
        background: var(--bg-secondary) !important;
        transform: scale(1.01);
        box-shadow: var(--shadow-sm);
    }
    
    /* Mejoras en inputs con focus mejorado */
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus {
        border-color: var(--primary-color) !important;
        box-shadow: 0 0 0 3px rgba(30, 64, 175, 0.15) !important;
        outline: none !important;
    }
    
    /* Mejoras en badges de estado */
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .status-badge.pending {
        background: rgba(245, 158, 11, 0.2);
        color: #92400e;
    }
    
    .status-badge.completed {
        background: rgba(16, 185, 129, 0.2);
        color: #065f46;
    }
    
    .status-badge.in-progress {
        background: rgba(59, 130, 246, 0.2);
        color: #1e40af;
    }
    
    .status-badge.cancelled {
        background: rgba(239, 68, 68, 0.2);
        color: #991b1b;
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

# --- FUNCIONES HELPER PARA ICONOS SVG PROFESIONALES ---

def get_icon_symbol(icon_name: str) -> str:
    """Retorna solo el símbolo Unicode del icono (para usar en botones de Streamlit)"""
    icon_symbols = {
        "dashboard": "📊",
        "documents": "📄",
        "quality": "✅",
        "chat": "💬",
        "user": "👤",
        "upload": "⬆️",
        "download": "⬇️",
        "add": "➕",
        "calendar": "📅",
        "chart": "📈",
        "money": "💰",
        "team": "👥",
        "building": "🏗️",
        "location": "📍",
        "camera": "📷",
        "check": "✓",
        "alert": "⚠️",
        "project": "📁",
        "settings": "⚙️",
        "edit": "✏️",
        "delete": "🗑️",
        "save": "💾",
        "search": "🔍",
        "filter": "🔽",
        "refresh": "🔄",
    }
    return icon_symbols.get(icon_name, "")

def get_icon(icon_name: str, size: str = "md") -> str:
    """Retorna el HTML de un icono para usar en markdown (NO para botones)"""
    size_map = {"sm": "16px", "md": "20px", "lg": "24px"}
    icon_size = size_map.get(size, "20px")
    symbol = get_icon_symbol(icon_name)
    if symbol:
        return f'<span style="font-size: {icon_size}; display: inline-block; vertical-align: middle; margin-right: 4px;">{symbol}</span>'
    return ""

def render_header_with_icon(title: str, icon_name: str = "dashboard") -> None:
    """Renderiza un header con icono profesional"""
    icon_html = get_icon(icon_name, "lg")
    st.markdown(
        f'<div class="main-header fade-in">{icon_html} {title}</div>',
        unsafe_allow_html=True
    )

def create_download_button(data, filename: str, label: str = "Descargar") -> None:
    """Crea un botón de descarga profesional"""
    if isinstance(data, pd.DataFrame):
        csv = data.to_csv(index=False).encode('utf-8')
        st.download_button(
            label=f'{get_icon_symbol("download")} {label}',
            data=csv,
            file_name=filename,
            mime="text/csv",
            use_container_width=True,
            help=f"Descargar {filename}"
        )
    elif isinstance(data, dict):
        json_str = json.dumps(data, indent=2, ensure_ascii=False, default=str).encode('utf-8')
        st.download_button(
            label=f'{get_icon_symbol("download")} {label}',
            data=json_str,
            file_name=filename,
            mime="application/json",
            use_container_width=True,
            help=f"Descargar {filename}"
        )

def show_success_message(message: str, duration: int = 3) -> None:
    """Muestra un mensaje de éxito mejorado"""
    st.success(f'{get_icon_symbol("check")} {message}')
    time.sleep(duration)

def show_error_message(message: str) -> None:
    """Muestra un mensaje de error mejorado"""
    st.error(f'{get_icon_symbol("alert")} {message}')

def show_warning_message(message: str) -> None:
    """Muestra un mensaje de advertencia mejorado"""
    st.warning(f'{get_icon_symbol("alert")} {message}')

def show_info_message(message: str) -> None:
    """Muestra un mensaje informativo mejorado"""
    st.info(f'{get_icon_symbol("alert")} {message}')

def confirm_action(message: str, action_label: str = "Confirmar") -> bool:
    """Muestra un diálogo de confirmación"""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.warning(f'⚠️ {message}')
        col_confirm, col_cancel = st.columns(2)
        with col_confirm:
            if st.button(f'{get_icon_symbol("check")} {action_label}', type="primary", use_container_width=True, key=f"confirm_{int(time.time())}"):
                return True
        with col_cancel:
            if st.button("Cancelar", use_container_width=True, key=f"cancel_{int(time.time())}"):
                return False
    return False

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
        "current_project_id": None
    }

def get_default_project_data():
    """Retorna estructura por defecto de un proyecto"""
    return {
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
    
    def get_current_project_id(self):
        """Obtiene el ID del proyecto actual"""
        if 'current_project_id' not in st.session_state:
            db = self.get_db()
            if db.get("current_project_id"):
                st.session_state.current_project_id = db["current_project_id"]
            else:
                # Si hay proyectos, seleccionar el primero
                projects = db.get("projects", [])
                if projects:
                    st.session_state.current_project_id = projects[0]["id"]
                else:
                    st.session_state.current_project_id = None
        return st.session_state.current_project_id
    
    def get_current_project_data(self):
        """Obtiene los datos del proyecto actual"""
        project_id = self.get_current_project_id()
        if not project_id:
            return get_default_project_data()
        
        db = self.get_db()
        projects = db.get("projects", [])
        for project in projects:
            if project.get("id") == project_id:
                if "data" not in project:
                    project["data"] = get_default_project_data()
                return project["data"]
        return get_default_project_data()
    
    def save_current_project_data(self, project_data):
        """Guarda los datos del proyecto actual"""
        project_id = self.get_current_project_id()
        if not project_id:
            return False
        
        db = self.get_db()
        projects = db.get("projects", [])
        for project in projects:
            if project.get("id") == project_id:
                project["data"] = project_data
                self.save_db(db)
                return True
        return False
    
    def create_project(self, project_name, description="", location="", start_date=None, budget_total=0):
        """Crea un nuevo proyecto"""
        db = self.get_db()
        projects = db.get("projects", [])
        
        new_project = {
            "id": len(projects) + 1,
            "name": project_name,
            "description": description,
            "location": location,
            "start_date": start_date.strftime("%d/%m/%Y") if start_date else datetime.now().strftime("%d/%m/%Y"),
            "created_at": datetime.now().isoformat(),
            "status": "Activo",
            "budget_total": budget_total,
            "data": get_default_project_data()
        }
        
        if budget_total > 0:
            new_project["data"]["budget"]["total"] = budget_total
        
        projects.append(new_project)
        db["projects"] = projects
        
        # Si es el primer proyecto, establecerlo como actual
        if len(projects) == 1:
            db["current_project_id"] = new_project["id"]
            st.session_state.current_project_id = new_project["id"]
        
        self.save_db(db)
        return new_project["id"]
    
    def get_projects(self):
        """Obtiene todos los proyectos"""
        db = self.get_db()
        return db.get("projects", [])
    
    def set_current_project(self, project_id):
        """Establece el proyecto actual"""
        db = self.get_db()
        db["current_project_id"] = project_id
        st.session_state.current_project_id = project_id
        self.save_db(db)
    
    def get_project(self, project_id):
        """Obtiene un proyecto por ID"""
        db = self.get_db()
        projects = db.get("projects", [])
        for project in projects:
            if project.get("id") == project_id:
                return project
        return None
    
    def add_activity(self, activity_data):
        """Agrega una nueva actividad al proyecto actual"""
        project_data = self.get_current_project_data()
        activity_data["id"] = len(project_data["activities"]) + 1
        activity_data["created_at"] = datetime.now().isoformat()
        project_data["activities"].append(activity_data)
        self.save_current_project_data(project_data)
        return True
    
    def get_activities(self):
        """Obtiene todas las actividades del proyecto actual"""
        project_data = self.get_current_project_data()
        return project_data.get("activities", [])
    
    def add_personnel(self, personnel_data):
        """Agrega personal al proyecto actual"""
        project_data = self.get_current_project_data()
        personnel_data["id"] = len(project_data["personnel"]) + 1
        personnel_data["created_at"] = datetime.now().isoformat()
        project_data["personnel"].append(personnel_data)
        self.save_current_project_data(project_data)
        return True
    
    def get_personnel(self):
        """Obtiene todo el personal del proyecto actual"""
        project_data = self.get_current_project_data()
        return project_data.get("personnel", [])
    
    def add_improvement(self, improvement_data):
        """Agrega una mejora o sugerencia al proyecto actual"""
        project_data = self.get_current_project_data()
        improvement_data["id"] = len(project_data["improvements"]) + 1
        improvement_data["created_at"] = datetime.now().isoformat()
        improvement_data["status"] = "Pendiente"
        project_data["improvements"].append(improvement_data)
        self.save_current_project_data(project_data)
        return True
    
    def get_improvements(self):
        """Obtiene todas las mejoras del proyecto actual"""
        project_data = self.get_current_project_data()
        return project_data.get("improvements", [])
    
    def update_improvement_status(self, improvement_id, new_status):
        """Actualiza el estado de una mejora"""
        project_data = self.get_current_project_data()
        for improvement in project_data.get("improvements", []):
            if improvement.get("id") == improvement_id:
                improvement["status"] = new_status
                improvement["updated_at"] = datetime.now().isoformat()
                self.save_current_project_data(project_data)
                return True
        return False
    
    def update_budget(self, category, amount):
        """Actualiza el presupuesto ejecutado del proyecto actual"""
        project_data = self.get_current_project_data()
        budget = project_data.get("budget", get_default_project_data()["budget"])
        if category in budget["categories"]:
            budget["categories"][category]["executed"] += amount
            budget["executed"] += amount
            project_data["budget"] = budget
            self.save_current_project_data(project_data)
            return True
        return False
    
    def get_budget(self):
        """Obtiene información del presupuesto del proyecto actual"""
        project_data = self.get_current_project_data()
        return project_data.get("budget", get_default_project_data()["budget"])
    
    def add_milestone(self, milestone_data):
        """Agrega un hito del proyecto actual"""
        project_data = self.get_current_project_data()
        milestone_data["id"] = len(project_data["milestones"]) + 1
        milestone_data["created_at"] = datetime.now().isoformat()
        project_data["milestones"].append(milestone_data)
        self.save_current_project_data(project_data)
        return True
    
    def get_milestones(self):
        """Obtiene todos los hitos del proyecto actual"""
        project_data = self.get_current_project_data()
        return project_data.get("milestones", [])
    
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
    
    def export_data(self, data_type: str):
        """Exporta datos en formato JSON o CSV"""
        db = self.get_db()
        if data_type == "all":
            return db
        elif data_type == "activities":
            return db.get("activities", [])
        elif data_type == "personnel":
            return db.get("personnel", [])
        elif data_type == "improvements":
            return db.get("improvements", [])
        elif data_type == "milestones":
            return db.get("milestones", [])
        return {}

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
    # Mostrar logo de la empresa con mejor presentación
    try:
        logo_path = "logogyh.jpeg"
        if Path(logo_path).exists():
            logo_base64 = base64.b64encode(Path(logo_path).read_bytes()).decode()
            st.markdown(f"""
            <div style='text-align: center; padding: 2rem 0; background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%); border-radius: 16px; margin-bottom: 2rem;'>
                <img src="data:image/jpeg;base64,{logo_base64}" alt="G&H Constructores" style="max-height: 100px; width: auto; margin-bottom: 1rem;" />
                <div style='font-size: 2rem; font-weight: 700; color: #1e40af; letter-spacing: 0.1em; margin-top: 0.5rem;'>
                    G&H CONSTRUCTORES
                </div>
                <div style='font-size: 1rem; color: #64748b; margin-top: 0.5rem;'>
                    Sistema de Gestión de Obra
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style='text-align: center; padding: 2rem 0; background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%); border-radius: 16px; margin-bottom: 2rem;'>
                <div style='font-size: 2.5rem; font-weight: 700; color: #1e40af; letter-spacing: 0.1em;'>
                    G&H CONSTRUCTORES
                </div>
                <div style='font-size: 1.1rem; color: #64748b; margin-top: 0.5rem;'>
                    Sistema de Gestión de Obra
                </div>
            </div>
            """, unsafe_allow_html=True)
    except Exception as e:
        logger.warning(f"No se pudo cargar el logo: {e}")
        st.markdown("""
        <div style='text-align: center; padding: 2rem 0; background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%); border-radius: 16px; margin-bottom: 2rem;'>
            <div style='font-size: 2.5rem; font-weight: 700; color: #1e40af; letter-spacing: 0.1em;'>
                G&H CONSTRUCTORES
            </div>
            <div style='font-size: 1.1rem; color: #64748b; margin-top: 0.5rem;'>
                Sistema de Gestión de Obra
            </div>
        </div>
        """, unsafe_allow_html=True)
    
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
    render_header_with_icon("Dashboard Ejecutivo", "dashboard")
    
    # Mostrar información del proyecto actual
    current_project_id = dm.get_current_project_id()
    if current_project_id:
        current_project = dm.get_project(current_project_id)
        if current_project:
            st.info(f'{get_icon("building", "sm")} **Proyecto:** {current_project.get("name", "Sin nombre")} | 📍 {current_project.get("location", "N/A")}')
    else:
        st.warning(f'{get_icon("alert", "sm")} No hay proyecto seleccionado. Ve a "Proyectos" para crear o seleccionar uno.')
        return
    
    # --- KPIs PRINCIPALES ---
    st.markdown(f'<h3>{get_icon("chart", "md")} Indicadores Clave (KPIs)</h3>', unsafe_allow_html=True)
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
        st.markdown(f'<h3>{get_icon("chart", "md")} Curva de Avance</h3>', unsafe_allow_html=True)
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
    st.markdown(f'<h3>{get_icon("building", "md")} Estado de Actividades Principales</h3>', unsafe_allow_html=True)
    
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
        st.markdown(f'<h3>{get_icon("team", "md")} Personal en Obra</h3>', unsafe_allow_html=True)
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
        st.markdown(f'<h3>{get_icon("quality", "md")} Inspecciones Recientes</h3>', unsafe_allow_html=True)
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
    st.markdown(f'<h3>{get_icon("alert", "md")} Alertas y Notificaciones</h3>', unsafe_allow_html=True)
    
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
    st.markdown(f'<h3>{get_icon("documents", "md")} Documentos Recientes</h3>', unsafe_allow_html=True)
    
    # Obtener documentos primero
    docs = dm.get_docs()
    
    # Botón de descarga
    if docs:
        col_docs, col_download = st.columns([3, 1])
        with col_download:
            docs_df = pd.DataFrame(docs)
            csv = docs_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label=f'{get_icon("download", "sm")} Exportar',
                data=csv,
                file_name=f"documentos_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True,
                key="export_docs"
            )
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
    st.markdown(f'<h3>{get_icon("calendar", "md")} Resumen del Día</h3>', unsafe_allow_html=True)
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
    st.markdown(f'<h3>{get_icon("add", "md")} Gestión de Información del Proyecto</h3>', unsafe_allow_html=True)
    
    tab_act, tab_pers, tab_bud, tab_mil, tab_imp = st.tabs([
        f"{get_icon('building', 'sm')} Actividades",
        f"{get_icon('team', 'sm')} Personal",
        f"{get_icon('money', 'sm')} Presupuesto",
        f"{get_icon('calendar', 'sm')} Hitos",
        f"{get_icon('check', 'sm')} Mejoras"
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
                    with st.spinner("Guardando actividad..."):
                        if dm.add_activity(activity_data):
                            show_success_message(f'Actividad "{act_name}" agregada correctamente', 2)
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            show_error_message("Error al guardar la actividad. Intenta nuevamente.")
                else:
                    show_error_message("Completa los campos obligatorios (*)")
        
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
        st.markdown(f'<h4>{get_icon("user", "sm")} Registrar Personal</h4>', unsafe_allow_html=True)
        with st.form("form_personnel", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                pers_name = st.text_input("Nombre Completo *", placeholder="Ej: Juan Pérez", help="Nombre completo del trabajador")
                pers_role = st.selectbox("Rol/Cargo *", ["Albañil", "Carpintero", "Electricista", "Plomero", "Supervisor", "Ingeniero", "Arquitecto", "Otro"], help="Cargo o especialidad")
                pers_team = st.text_input("Equipo", placeholder="Ej: Equipo Alfa", help="Equipo o cuadrilla asignada")
            with col2:
                pers_phone = st.text_input("Teléfono", placeholder="+56 9 1234 5678", help="Número de contacto")
                pers_email = st.text_input("Email", placeholder="juan.perez@empresa.cl", help="Correo electrónico")
                pers_status = st.selectbox("Estado", ["Activo", "Inactivo", "Vacaciones", "Licencia"], help="Estado actual del trabajador")
            
            # Campos adicionales
            pers_dni = st.text_input("DNI/RUT", placeholder="12.345.678-9", help="Documento de identidad")
            pers_start_date = st.date_input("Fecha de Ingreso", value=datetime.now().date(), help="Fecha en que comenzó a trabajar")
            
            submitted = st.form_submit_button(f'{get_icon_symbol("add")} Registrar Personal', type="primary", use_container_width=True)
            
            if submitted:
                if pers_name and pers_role:
                    with st.spinner("Registrando personal..."):
                        personnel_data = {
                            "nombre": pers_name,
                            "rol": pers_role,
                            "equipo": pers_team,
                            "telefono": pers_phone,
                            "email": pers_email,
                            "dni": pers_dni,
                            "fecha_ingreso": pers_start_date.strftime("%d/%m/%Y"),
                            "estado": pers_status,
                            "created_by": st.session_state.user_info['name']
                        }
                        if dm.add_personnel(personnel_data):
                            st.success(f'{get_icon("check", "sm")} **Personal "{pers_name}" registrado correctamente**')
                            time.sleep(0.5)
                            st.rerun()
                else:
                    st.error(f'{get_icon("alert", "sm")} **Completa los campos obligatorios (*)**')
        
        st.divider()
        
        # Sección de personal registrado con opción de descarga
        col_header, col_export = st.columns([3, 1])
        with col_header:
            st.markdown(f'<h4>{get_icon("team", "sm")} Personal Registrado</h4>', unsafe_allow_html=True)
        with col_export:
            personnel = dm.get_personnel()
            if personnel:
                pers_df = pd.DataFrame(personnel)
                if not pers_df.empty:
                    csv = pers_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label=f'{get_icon("download", "sm")} Exportar',
                        data=csv,
                        file_name=f"personal_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        use_container_width=True,
                        key="export_personnel"
                    )
        
        personnel = dm.get_personnel()
        if personnel:
            pers_df = pd.DataFrame(personnel)
            if not pers_df.empty:
                display_cols = ["nombre", "rol", "equipo", "estado", "fecha_ingreso"]
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
                    if budget_amount > budget['categories'][budget_category]['budget']:
                        show_warning_message(f"El monto excede el presupuesto asignado para {budget_category}")
                    else:
                        with st.spinner("Registrando gasto..."):
                            if dm.update_budget(budget_category, budget_amount):
                                show_success_message(f'Gasto de ${budget_amount:,.0f} registrado en {budget_category}', 2)
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                show_error_message("Error al registrar el gasto. Intenta nuevamente.")
                else:
                    show_error_message("Ingresa un monto válido mayor a cero")
        
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
                    with st.spinner("Agregando hito..."):
                        if dm.add_milestone(milestone_data):
                            st.success(f'{get_icon("check", "sm")} **Hito "{mil_name}" agregado correctamente**')
                            time.sleep(0.5)
                            st.rerun()
                else:
                    st.error(f'{get_icon("alert", "sm")} **Completa el nombre del hito**')
        
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
                    with st.spinner("Enviando sugerencia..."):
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
                            st.success(f'{get_icon("check", "sm")} **Sugerencia de mejora "{imp_title}" enviada correctamente**')
                            time.sleep(0.5)
                            st.rerun()
                else:
                    st.error(f'{get_icon("alert", "sm")} **Completa los campos obligatorios (*)**')
        
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
                        if st.button(f"{get_icon_symbol('check')} Aprobar", key=f"approve_{imp['id']}", use_container_width=True):
                            if dm.update_improvement_status(imp['id'], "Aprobada"):
                                st.success(f'{get_icon("check", "sm")} **Mejora aprobada**')
                                time.sleep(0.5)
                                st.rerun()
                    with col2:
                        if st.button(f"{get_icon_symbol('check')} Implementar", key=f"implement_{imp['id']}", use_container_width=True):
                            if dm.update_improvement_status(imp['id'], "Implementada"):
                                st.success(f'{get_icon("check", "sm")} **Mejora marcada como implementada**')
                                time.sleep(0.5)
                                st.rerun()
        else:
            st.info("No hay mejoras registradas aún")

def view_docs():
    render_header_with_icon("Planos y Documentos", "documents")
    
    # Subida Dual: Archivo (Escritorio) o Cámara (Móvil)
    tab1, tab2 = st.tabs([
        f"{get_icon('upload', 'sm')} Subir Archivo",
        f"{get_icon('camera', 'sm')} Escanear Documento"
    ])
    
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
            
            col_upload, col_version = st.columns([2, 1])
            with col_version:
                file_version = st.text_input("Versión", value="v1.0", placeholder="v1.0")
            
            if st.button(f'{get_icon_symbol("upload")} Guardar Archivo', use_container_width=True, type="primary", key="btn_guardar_archivo_docs"):
                with st.spinner("Subiendo archivo..."):
                    if dm.upload_file(uploaded_file, {"version": file_version}):
                        st.success(f'{get_icon("check", "sm")} **Archivo "{uploaded_file.name}" guardado correctamente**')
                        time.sleep(0.5)
                        st.rerun()
             
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
            
    # Sección de archivos con descarga
    col_files, col_download_files = st.columns([3, 1])
    with col_files:
        st.markdown(f'<h3>{get_icon("documents", "sm")} Archivos Recientes</h3>', unsafe_allow_html=True)
    with col_download_files:
        docs = dm.get_docs()
        if docs:
            df = pd.DataFrame(docs)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label=f'{get_icon("download", "sm")} Exportar',
                data=csv,
                file_name=f"documentos_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True,
                key="export_documents"
            )
    
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
    render_header_with_icon("Calidad (QA/QC)", "quality")
    
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
        st.markdown(f'<p><strong>{get_icon("camera", "sm")} Evidencia Fotográfica</strong></p>', unsafe_allow_html=True)
        photo = st.camera_input("Tomar foto", help="La foto se comprimirá automáticamente", label_visibility="collapsed")
        
        submitted = st.form_submit_button(f'{get_icon_symbol("check")} Guardar Reporte', type="primary", use_container_width=True)
        
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
                    st.success(f'{get_icon("check", "sm")} **Inspección guardada correctamente**')
                    time.sleep(0.5)
                    st.rerun()

    # Historial con descarga
    col_hist, col_download_hist = st.columns([3, 1])
    with col_hist:
        st.markdown(f'<h3>{get_icon("calendar", "sm")} Historial</h3>', unsafe_allow_html=True)
    with col_download_hist:
        inspections = dm.get_inspections()
        if inspections:
            df = pd.DataFrame(inspections)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label=f'{get_icon("download", "sm")} Exportar',
                data=csv,
                file_name=f"inspecciones_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True,
                key="export_inspections"
            )
    
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
    render_header_with_icon("Mi Jornada", "user")
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
    st.markdown(f'<h3>{get_icon("location", "sm")} Registro de Asistencia</h3>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(f'{get_icon_symbol("location")} MARCAR ENTRADA', type="primary", use_container_width=True, key="btn_entrada"):
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
        if st.button(f'{get_icon_symbol("check")} MARCAR SALIDA', use_container_width=True, key="btn_salida"):
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
    st.markdown(f'<h3>{get_icon("chart", "sm")} Resumen Semanal</h3>', unsafe_allow_html=True)
    
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
    st.markdown(f'<h3>{get_icon("calendar", "sm")} Mis Tareas de Hoy</h3>', unsafe_allow_html=True)
    
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
    st.markdown(f'<h3>{get_icon("alert", "sm")} Notificaciones</h3>', unsafe_allow_html=True)
    
    st.info("📢 **Nueva asignación**: Revisión de enfierradura Torre B - Piso 3")
    st.warning("⏰ **Recordatorio**: Reunión de seguridad a las 15:00")
    st.success("✅ **Completado**: Tu tarea de ayer fue aprobada")
    
    st.divider()
    
    # --- REPORTE DE INCIDENTES ---
    st.markdown(f'<h3>{get_icon("alert", "sm")} Reportar Incidente o Observación</h3>', unsafe_allow_html=True)
    
    with st.expander(f"{get_icon('camera', 'sm')} Reportar con Foto", expanded=False):
        incident_photo = st.camera_input("Tomar foto del incidente")
        incident_desc = st.text_area("Descripción del incidente", placeholder="Describe qué ocurrió, dónde y cuándo...")
        
        if st.button(f'{get_icon_symbol("check")} ENVIAR REPORTE', type="primary", use_container_width=True, key="btn_enviar_reporte_incidente", help="Envía el reporte de incidente al equipo de seguridad"):
            if incident_photo or incident_desc.strip():
                if confirm_action("¿Estás seguro de enviar este reporte de incidente? Se notificará inmediatamente al equipo de seguridad."):
                    with st.spinner("Enviando reporte..."):
                        show_error_message("🚨 Reporte enviado a Prevención de Riesgos")
                        show_success_message("Tu reporte ha sido registrado. El equipo de seguridad se contactará contigo.", 3)
                        logger.warning(f"Incidente reportado por {st.session_state.user_info['name']}")
                        if incident_photo:
                            try:
                                photo_bytes = incident_photo.getvalue()
                                compressed = compress_image(photo_bytes)
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                incident_path = PHOTOS_DIR / f"incident_{timestamp}.jpg"
                                incident_path.write_bytes(compressed)
                                logger.info(f"Foto de incidente guardada: {incident_path}")
                                show_success_message("Foto del incidente guardada correctamente", 2)
                            except Exception as e:
                                logger.error(f"Error guardando foto de incidente: {e}")
                                show_error_message(f"Error al guardar la foto: {str(e)}")
                        time.sleep(1)
                        st.rerun()
            else:
                show_warning_message("Toma una foto o escribe una descripción del incidente")
    
    # --- INFORMACIÓN DEL TRABAJADOR ---
    st.divider()
    st.markdown(f'<h3>{get_icon("user", "sm")} Mi Información</h3>', unsafe_allow_html=True)
    
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
    render_header_with_icon("Portal del Cliente", "building")
    
    # Mostrar información del proyecto actual
    current_project_id = dm.get_current_project_id()
    if current_project_id:
        current_project = dm.get_project(current_project_id)
        if current_project:
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); color: white; padding: 1.5rem; border-radius: 12px; margin-bottom: 1.5rem;'>
                <div style='font-size: 1.1rem; font-weight: 600; margin-bottom: 0.5rem;'>
                    {get_icon("building", "sm")} {current_project.get("name", "Sin nombre")}
                </div>
                <div style='font-size: 0.9rem; opacity: 0.9;'>
                    📍 {current_project.get("location", "N/A")} | 📅 Inicio: {current_project.get("start_date", "N/A")}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.write(f"Bienvenido, **{st.session_state.user_info['name']}**")
    
    # --- KPIs PRINCIPALES PARA CLIENTE ---
    st.markdown(f'<h3>{get_icon("chart", "sm")} Resumen del Proyecto</h3>', unsafe_allow_html=True)
    
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
        st.markdown(f'<h3>{get_icon("chart", "sm")} Curva de Avance</h3>', unsafe_allow_html=True)
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
    st.markdown(f'<h3>{get_icon("building", "sm")} Estado de Actividades</h3>', unsafe_allow_html=True)
    
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
    st.markdown(f'<h3>{get_icon("camera", "sm")} Galería de Avances</h3>', unsafe_allow_html=True)
    
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
    st.markdown(f'<h3>{get_icon("documents", "sm")} Mis Solicitudes y Cambios</h3>', unsafe_allow_html=True)
    
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
    
    if st.button(f'{get_icon_symbol("add")} Nueva Solicitud', use_container_width=True, key="btn_nueva_solicitud_cliente"):
        st.info(f'{get_icon("chat", "sm")} Usa el chat para enviar nuevas solicitudes o contacta directamente al equipo')
    
    st.divider()
    
    # --- HITOS Y CALENDARIO ---
    st.markdown(f'<h3>{get_icon("calendar", "sm")} Próximos Hitos Importantes</h3>', unsafe_allow_html=True)
    
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
    st.markdown(f'<h3>{get_icon("check", "sm")} Mejoras y Optimizaciones del Proyecto</h3>', unsafe_allow_html=True)
    
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
    st.markdown(f'<h3>{get_icon("documents", "sm")} Documentos Recientes</h3>', unsafe_allow_html=True)
    
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
    st.markdown(f'<h3>{get_icon("building", "sm")} Información del Proyecto</h3>', unsafe_allow_html=True)
    
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
    
    st.info(f'{get_icon("chat", "sm")} Para consultas urgentes, utiliza el chat o contacta directamente al equipo de obra')

def view_projects():
    """Vista para gestionar proyectos"""
    render_header_with_icon("Gestión de Proyectos", "project")
    
    # Mostrar proyecto actual con mejor presentación
    current_project_id = dm.get_current_project_id()
    if current_project_id:
        current_project = dm.get_project(current_project_id)
        if current_project:
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); color: white; padding: 1.5rem; border-radius: 12px; margin-bottom: 1.5rem;'>
                <div style='font-size: 1.1rem; font-weight: 600; margin-bottom: 0.5rem;'>
                    {get_icon("building", "sm")} Proyecto Actual
                </div>
                <div style='font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;'>
                    {current_project.get("name", "Sin nombre")}
                </div>
                <div style='font-size: 0.9rem; opacity: 0.9;'>
                    📍 {current_project.get("location", "N/A")} | 📅 {current_project.get("start_date", "N/A")} | 💰 ${current_project.get("budget_total", 0):,.0f}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info(f'{get_icon("alert", "sm")} **No hay proyecto seleccionado.** Crea tu primer proyecto a continuación.')
    
    st.divider()
    
    # Tabs para crear y gestionar proyectos
    tab_create, tab_list = st.tabs([
        f"{get_icon('add', 'sm')} Crear Proyecto",
        f"{get_icon('project', 'sm')} Mis Proyectos"
    ])
    
    with tab_create:
        st.markdown("### Crear Nuevo Proyecto")
        with st.form("form_create_project", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                proj_name = st.text_input("Nombre del Proyecto *", placeholder="Ej: Edificio Residencial Altos del Parque")
                proj_location = st.text_input("Ubicación", placeholder="Ej: Av. Principal 1234")
                proj_start = st.date_input("Fecha de Inicio", value=datetime.now().date())
            with col2:
                proj_budget = st.number_input("Presupuesto Total ($)", min_value=0.0, value=0.0, step=1000.0)
                proj_status = st.selectbox("Estado", ["Activo", "En Planificación", "Pausado", "Completado"])
            
            proj_description = st.text_area("Descripción", placeholder="Descripción del proyecto...", height=100)
            
            submitted = st.form_submit_button(f'{get_icon_symbol("add")} Crear Proyecto', type="primary", use_container_width=True)
            
            if submitted:
                if proj_name:
                    project_id = dm.create_project(
                        project_name=proj_name,
                        description=proj_description,
                        location=proj_location,
                        start_date=proj_start,
                        budget_total=proj_budget
                    )
                    if project_id:
                        st.success(f'{get_icon("check", "sm")} Proyecto "{proj_name}" creado correctamente')
                        dm.set_current_project(project_id)
                        st.rerun()
                else:
                    st.error(f'{get_icon("alert", "sm")} El nombre del proyecto es obligatorio')
    
    with tab_list:
        st.markdown("### Lista de Proyectos")
        projects = dm.get_projects()
        
        if projects:
            for project in projects:
                is_current = project.get("id") == current_project_id
                status_color = {
                    "Activo": "🟢",
                    "En Planificación": "🟡",
                    "Pausado": "🟠",
                    "Completado": "✅"
                }.get(project.get("status", "Activo"), "🟢")
                
                with st.expander(f"{status_color} {project.get('name', 'Sin nombre')} - {project.get('status', 'Activo')} {'(Actual)' if is_current else ''}"):
                    col_info, col_actions = st.columns([3, 1])
                    with col_info:
                        st.write(f"**Ubicación:** {project.get('location', 'N/A')}")
                        st.write(f"**Fecha Inicio:** {project.get('start_date', 'N/A')}")
                        st.write(f"**Presupuesto:** ${project.get('budget_total', 0):,.0f}")
                        if project.get('description'):
                            st.write(f"**Descripción:** {project.get('description')}")
                    
                    with col_actions:
                        if not is_current:
                            if st.button(f"{get_icon_symbol('check')} Seleccionar", key=f"btn_select_project_{project['id']}", use_container_width=True):
                                dm.set_current_project(project['id'])
                                st.success(f"Proyecto '{project.get('name')}' seleccionado")
                                st.rerun()
        else:
            st.info("No hay proyectos creados. Crea tu primer proyecto en la pestaña 'Crear Proyecto'")

def view_chat():
    render_header_with_icon("Chat", "chat")
    
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
            # Logo de la empresa en el sidebar
            try:
                logo_path = "logogyh.jpeg"
                if Path(logo_path).exists():
                    logo_base64 = base64.b64encode(Path(logo_path).read_bytes()).decode()
                    st.markdown(f"""
                    <div style='text-align: center; padding: 1rem 0;'>
                        <img src="data:image/jpeg;base64,{logo_base64}" alt="G&H Constructores" style="max-height: 60px; width: auto;" />
                    </div>
                    """, unsafe_allow_html=True)
            except Exception as e:
                logger.warning(f"No se pudo cargar el logo en sidebar: {e}")
            
            st.write(f"👤 **{st.session_state.user_info['name']}**")
            st.caption(f"Rol: {st.session_state.user_info['role']}")
            
            # Selector de Proyecto (solo para ADMIN)
            role = st.session_state.user_info['role']
            if role == "ADMIN":
                st.divider()
                st.markdown("### Proyecto Actual")
                projects = dm.get_projects()
                current_project_id = dm.get_current_project_id()
                
                if projects:
                    project_names = [f"{p.get('name', 'Sin nombre')} ({p.get('status', 'Activo')})" for p in projects]
                    project_ids = [p.get('id') for p in projects]
                    
                    try:
                        current_index = project_ids.index(current_project_id) if current_project_id in project_ids else 0
                    except ValueError:
                        current_index = 0
                    
                    selected_project_idx = st.selectbox(
                        "Seleccionar Proyecto:",
                        range(len(project_names)),
                        index=current_index,
                        format_func=lambda x: project_names[x],
                        key="project_selector"
                    )
                    
                    if project_ids[selected_project_idx] != current_project_id:
                        dm.set_current_project(project_ids[selected_project_idx])
                        st.rerun()
                    
                    # Mostrar info del proyecto actual
                    if current_project_id:
                        current_project = dm.get_project(current_project_id)
                        if current_project:
                            st.caption(f"📍 {current_project.get('location', 'N/A')}")
                            st.caption(f"📅 {current_project.get('start_date', 'N/A')}")
                else:
                    st.info("No hay proyectos. Crea uno en 'Proyectos'")
            
            # Mostrar tiempo de sesión restante
            st.divider()
            if 'last_activity' in st.session_state:
                elapsed = datetime.now() - st.session_state.last_activity
                remaining = SESSION_TIMEOUT_MINUTES - (elapsed.total_seconds() / 60)
                if remaining > 0:
                    st.caption(f"⏱️ Sesión: {int(remaining)} min restantes")
            
            if st.button("Cerrar Sesión", use_container_width=True):
                logout()
            st.divider()
            
            menu_options = []
            
            if role == "ADMIN":
                menu_options = ["Dashboard", "Proyectos", "Documentos", "Calidad", "Chat"]
            elif role == "WORKER":
                menu_options = ["Mi Jornada", "Chat"]
            elif role == "CLIENT":
                menu_options = ["Portal", "Chat"]
                
            selected_page = st.radio("Ir a:", menu_options)

        # Renderizar vista seleccionada
        if role == "ADMIN":
            if selected_page == "Dashboard": view_dashboard_admin()
            elif selected_page == "Proyectos": view_projects()
            elif selected_page == "Documentos": view_docs()
            elif selected_page == "Calidad": view_qa()
            elif selected_page == "Chat": view_chat()
        elif role == "WORKER":
            if selected_page == "Mi Jornada": view_worker()
            elif selected_page == "Chat": view_chat()
        elif role == "CLIENT":
            if selected_page == "Portal": view_client()
            elif selected_page == "Chat": view_chat()
