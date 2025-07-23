# 🚀 Guía de Inicio Rápido - Polioxxo

Esta guía te ayudará a ejecutar el proyecto rápidamente.

## ⚡ Instalación Rápida

```bash
# 1. Clonar el repositorio
git clone https://github.com/JorgeLuisRamirezGarcia25/polioxxo.git
cd polioxxo

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows

# 3. Instalar dependencias
pip install -r requirements.txt
```

## 🎯 Uso Básico

### Ejecutar todo el pipeline:
```bash
python scripts/main.py
```

### Comandos individuales:
```bash
# Solo descargar datos
python scripts/main.py --download-only

# Solo procesar datos
python scripts/main.py --process-only

# Solo crear mapa
python scripts/main.py --map-only

# Solo análisis estadístico
python scripts/main.py --analyze-only

# Limpiar archivos generados
python scripts/main.py --clean
```

## 📊 Outputs

Después de ejecutar el pipeline completo encontrarás:

- **Mapa interactivo**: `maps/mapa_oxxos_cdmx.html`
- **Datos procesados**: `data/processed/*.gpkg`
- **Reportes y gráficos**: `reports/`
- **Logs**: `logs/polioxxo.log`

## 🔧 Solución Rápida de Problemas

**Error de conexión**: Verifica tu conexión a internet
**Archivos faltantes**: Ejecuta `python scripts/main.py --download-only`
**Memoria insuficiente**: El sistema está optimizado para datasets grandes

## 📖 Documentación Completa

Ver [README.md](README.md) para documentación completa del proyecto.
