"""
uhi-mty-mvp: Orquestador Principal de Producción Multitemporal
==============================================================
Punto de entrada oficial para la ejecución completa del pipeline
de análisis multitemporal (Día y Noche) de SUHI en Monterrey (2026).
"""

import os
import time
from datetime import datetime
from pathlib import Path
import geopandas as gpd

# Importación de módulos internos del proyecto
from src.config import INTERIM_DIR, PROCESSED_DIR
from src.gee_data import init_ee
from src.grid import create_30m_grid
from src.lst import download_mty_lst_multitemporal
from src.ndvi import download_mty_ndvi
from src.features import extract_satellite_features, consolidate_master_features, consolidate_master_features_v3
from src.dynamic_world import extract_dynamic_world
from src.industry import extract_industrial_polygons
from src.uhi_metrics import calculate_suhi_intensity
from src.plots import (
    plot_study_area_basemap,
    plot_satellite_basemap,
    plot_eda_distributions,
    plot_spatial_audit_panel
)
from src.stats import plot_correlation_matrix

def print_step(step_num, title):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{timestamp}] ========================================== ")
    print(f"[{timestamp}] PASO {step_num}/10: {title}")
    print(f"[{timestamp}] ========================================== ")

def main():
    start_time = time.time()
    timestamp_start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print("*" * 80)
    print(f"INICIANDO PIPELINE DE PRODUCCIÓN MULTITEMPORAL - UHI MONTERREY 2026")
    print(f"Hora de inicio: {timestamp_start}")
    print("*" * 80)
    
    # --- PASO 1: Google Earth Engine ---
    print_step("1", "Inicialización de Google Earth Engine API")
    lst_day_path = INTERIM_DIR / "lst_day_2026.tif"
    ndvi_path = INTERIM_DIR / "ndvi_mty_2026.tif"
    dw_path = INTERIM_DIR / "dw_mty_2026.tif"
    
    print("[PIPELINE] Conectando a GEE para inicialización y cálculo de línea base rural...")
    try:
        init_ee()
    except Exception as e:
        print(f"[PIPELINE] Advertencia al conectar con GEE: {e}. Se utilizarán fallbacks locales si es necesario.")
        
    # --- PASO 2: Malla Base 30m ---
    print_step("2", "Construcción de la Malla Base de 30m (UTM 14N)")
    grid_file = INTERIM_DIR / "malla_monterrey_30m.gpkg"
    if grid_file.exists():
        print(f"[PIPELINE] La malla base ya existe en: {grid_file}. Cargando...")
        grid_gdf = gpd.read_file(grid_file)
    else:
        print("[PIPELINE] Generando cuadrícula espacial regular de 30m...")
        grid_gdf = create_30m_grid()
        
    # --- PASO 3: Descarga de LST y NDVI ---
    print_step("3", "Obtención de LST (Día, Landsat 8) y NDVI (Sentinel-2)")
    print("[PIPELINE] Ejecutando verificación de LST y cálculo de referencia rural...")
    download_mty_lst_multitemporal()
        
    mask_path = INTERIM_DIR / "green_mask_mty_2026.tif"
    if ndvi_path.exists() and mask_path.exists():
        print(f"[PIPELINE] NDVI y máscara de vegetación ya existen en: {INTERIM_DIR}")
    else:
        print("[PIPELINE] Descargando NDVI e inicializando máscara de Sentinel-2...")
        download_mty_ndvi(year=2026)
        
    # --- PASO 4: Mapeo Satelital en Malla ---
    print_step("4", "Extracción de Variables Satelitales a Malla Base")
    print("[PIPELINE] Extrayendo LST diurno y porcentaje verde sobre la malla base...")
    extract_satellite_features()
    
    # --- PASO 5: Dynamic World ---
    print_step("5", "Extracción de Fracciones de Cobertura Dynamic World")
    if dw_path.exists():
        print(f"[PIPELINE] Raster Dynamic World ya existe en: {dw_path}")
    else:
        print("[PIPELINE] Descargando raster multibanda de Dynamic World...")
        extract_dynamic_world(year=2026)
        
    # --- PASO 6: Capas OSM e Industria ---
    print_step("6", "Procesamiento de Zonas Industriales (OSM)")
    extract_industrial_polygons()
    
    # --- PASO 7: Calibración SUHI ---
    print_step("7", "Cálculo de la Anomalía Térmica SUHI Diurna (Control Rural)")
    malla_suhi_gdf = calculate_suhi_intensity()
    
    # --- PASO 8: Consolidación Master v2 (Distancias y DW) ---
    print_step("8", "Consolidación de Dataset Maestro v2 (Distancias Euclidianas)")
    malla_v2_gdf = consolidate_master_features()
    
    # --- PASO 9: Consolidación Master v3 y Agregación Zonal AGEB ---
    print_step("9", "Agregación Zonal y Consolidación de Capa AGEB Maestra (INEGI)")
    malla_v3_gdf = consolidate_master_features_v3()
    
    # --- PASO 10: Visualizaciones y Auditoría de Correlaciones ---
    print_step("10", "Generación de Entregables, Gráficas y Matrices de Correlación")
    print("[PIPELINE] Generando mapa base del área de estudio...")
    plot_study_area_basemap(malla_v3_gdf)
    
    print("[PIPELINE] Generando mapa satelital limpio...")
    plot_satellite_basemap(malla_v3_gdf)
    
    print("[PIPELINE] Generando histogramas del EDA...")
    plot_eda_distributions(malla_v3_gdf)
    
    print("[PIPELINE] Generando panel visual de auditoría espacial...")
    plot_spatial_audit_panel(malla_v3_gdf)
    
    print("[PIPELINE] Generando matrices de correlación física (30m) y socioambiental (AGEB)...")
    plot_correlation_matrix(malla_v3_gdf)
    
    # --- CONCLUSIÓN ---
    elapsed_time = time.time() - start_time
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)
    
    print("\n" + "*" * 80)
    print(f"PIPELINE DE PRODUCCIÓN MULTITEMPORAL COMPLETADO CON ÉXITO")
    print(f"Tiempo transcurrido total: {minutes}m {seconds}s")
    print(f"Todos los productos se guardaron en data/processed/ y outputs/")
    print("*" * 80 + "\n")

if __name__ == "__main__":
    main()
