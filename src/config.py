"""
uhi-mty-mvp: Módulo de Configuración Paramétrico
=================================================
Centraliza todos los parámetros globales del proyecto.
"""

from pathlib import Path

# Parámetros temporales y de control
YEAR = 2026
START_DATE_DAY = '2026-03-01'
END_DATE_DAY = '2026-05-31'
START_DATE_NIGHT = '2026-03-01'
END_DATE_NIGHT = '2026-05-31'

# Límites del Área de Interés (AOI) - Bounding Box para la Zona Metropolitana de Monterrey (ZMM)
# Formato: [min_lon, min_lat, max_lon, max_lat]
AOI_BBOX = [-100.395595, 25.640327, -100.237307, 25.736120]

# Definición estándar de rutas de carpetas
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"

RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"

OUTPUTS_DIR = ROOT_DIR / "outputs"
FIGURES_DIR = OUTPUTS_DIR / "00"
MAPS_DIR = OUTPUTS_DIR / "00"
TABLES_DIR = OUTPUTS_DIR / "00"

# Crear carpetas si no existen de forma automática (00 a 05 para cada notebook)
for folder in [RAW_DIR, INTERIM_DIR, PROCESSED_DIR]:
    folder.mkdir(parents=True, exist_ok=True)
for i in range(6):
    (OUTPUTS_DIR / f"{i:02d}").mkdir(parents=True, exist_ok=True)
