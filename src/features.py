"""
Módulo para la consolidación de variables espaciales en la cuadrícula de análisis.
Extrae valores de satélite y calcula el dataset maestro final del proyecto.
"""

import numpy as np
import geopandas as gpd
import rasterio
from rasterio.enums import Resampling
import rioxarray
from src.config import INTERIM_DIR, PROCESSED_DIR

def extract_satellite_features():
    """
    Carga la malla de 30m y extrae la información de LST (Día y Noche) y la Máscara de Vegetación Verde.
    Realiza un remuestreo por promedio de la máscara de Sentinel-2 (10m) a 30m para calcular
    el porcentaje de cobertura verde. Luego muestrea todas las capas en los centroides.
    
    Returns:
        gpd.GeoDataFrame: Malla con las variables de satélite mapeadas.
    """
    print("\n[FEATURES] Iniciando extracción de variables satelitales...")
    
    # 1. Rutas de archivos
    grid_path = INTERIM_DIR / "malla_monterrey_30m.gpkg"
    lst_day_path = INTERIM_DIR / "lst_day_2026.tif"
    lst_night_path = INTERIM_DIR / "lst_night_2026.tif"
    mask_path = INTERIM_DIR / "green_mask_mty_2026.tif"
    output_path = INTERIM_DIR / "malla_features_2026.gpkg"
    
    # 2. Cargar malla geográfica
    if not grid_path.exists():
        raise FileNotFoundError(f"No se encontró la malla base en: {grid_path}. Ejecute la inicialización de la malla primero.")
    grid_gdf = gpd.read_file(grid_path)
    print(f"[FEATURES] Malla base cargada con {len(grid_gdf)} celdas.")
    
    # 3. Procesar y remuestrear la máscara de vegetación para obtener la fracción verde
    print("[FEATURES] Procesando máscara de vegetación Sentinel-2 (10m) a 30m...")
    lst_da = rioxarray.open_rasterio(lst_day_path)
    green_da = rioxarray.open_rasterio(mask_path)
    
    # Convertir valores de nodata de la máscara (255) a NaN
    green_float = green_da.where(green_da != 255).astype(float)
    
    # Reproject_match alinea la resolución del raster a la de LST diurno (30m)
    green_30m = green_float.rio.reproject_match(lst_da, resampling=Resampling.average)
    green_pct_da = green_30m * 100.0
    
    # Guardar temporalmente el raster de porcentaje verde de 30m
    green_pct_path = INTERIM_DIR / "green_pct_30m.tif"
    green_pct_da.rio.to_raster(green_pct_path)
    print(f"[FEATURES] Raster temporal de porcentaje verde guardado en: {green_pct_path}")
    
    # 4. Muestreo de los rasters en los centroides de la malla
    print("[FEATURES] Muestreando celdas en los centroides...")
    centroids = grid_gdf.to_crs(epsg=32614).geometry.centroid.to_crs(epsg=4326)
    coords = [(geom.x, geom.y) for geom in centroids]
    
    # Extraer valores LST Diurno
    with rasterio.open(lst_day_path) as src_lst:
        lst_nodata = src_lst.nodata
        lst_day_values = []
        for val in src_lst.sample(coords):
            v = val[0]
            if v == lst_nodata or np.isnan(v):
                lst_day_values.append(np.nan)
            else:
                lst_day_values.append(float(v))
                
    # Extraer valores LST Nocturno (desactivado por ahora, rellenado con NaN)
    lst_night_values = [np.nan] * len(coords)
                
    # Extraer valores Porcentaje Verde
    with rasterio.open(green_pct_path) as src_green:
        green_nodata = src_green.nodata
        green_values = []
        for val in src_green.sample(coords):
            v = val[0]
            if v == green_nodata or np.isnan(v):
                green_values.append(np.nan)
            else:
                green_values.append(float(max(0.0, min(100.0, v))))
                
    # 5. Agregar columnas al GeoDataFrame
    grid_gdf["lst_day_c"] = lst_day_values
    grid_gdf["lst_night_c"] = lst_night_values
    grid_gdf["lst_c"] = lst_day_values  # Copia para compatibilidad en gráficos
    grid_gdf["green_pct"] = green_values
    
    # Guardar
    grid_gdf.to_file(output_path, driver="GPKG", mode="w")
    print(f"[FEATURES] Extracción de variables satelitales completada. Guardado en: {output_path}")
    
    valid_day = grid_gdf["lst_day_c"].notna().sum()
    valid_night = grid_gdf["lst_night_c"].notna().sum()
    print(f"[FEATURES] Datos válidos mapeados: LST Día={valid_day}, LST Noche={valid_night}, Cobertura Verde={len(green_values)}")
    
    return grid_gdf

def consolidate_master_features():
    """
    Consolida las variables satelitales, de cobertura de suelo (Dynamic World) y métricas
    de distancia (Ternium, zonas industriales, cuerpos de agua) en un solo dataset maestro
    extendido y guarda el archivo resultante en data/processed/malla_maestra_mty_2026_v2.gpkg.
    
    Returns:
        gpd.GeoDataFrame: Malla maestra final unificada (v2).
    """
    print("\n[FEATURES] Iniciando consolidación del Dataset Maestro v2...")
    
    # 1. Cargar la malla maestra v1 (contiene LST, green_pct, suhi_c, industrial_osm_pct)
    malla_v1_path = PROCESSED_DIR / "malla_maestra_mty_2026.gpkg"
    
    if not malla_v1_path.exists():
        raise FileNotFoundError(f"No se encontró la malla maestra v1 en: {malla_v1_path}. Corra la fase 1 primero.")
        
    gdf = gpd.read_file(malla_v1_path)
    print(f"[FEATURES] Malla maestra v1 cargada con {len(gdf)} celdas.")
    
    # 2. Descargar y mapear coberturas de suelo de Dynamic World
    from src.dynamic_world import extract_dynamic_world, map_dw_to_grid
    try:
        extract_dynamic_world(year=2026)
        gdf = map_dw_to_grid(gdf)
    except Exception as e:
        print(f"[FEATURES] Error crítico al procesar Dynamic World: {e}")
        # Rellenar con NaN para evitar fallas catastróficas
        for col in ["dw_built_pct", "dw_trees_pct", "dw_bare_pct", "dw_water_pct", "dw_grass_pct"]:
            gdf[col] = np.nan
            
    # 3. Calcular distancias a zonas industriales y planta de Ternium
    from src.industry import calculate_distance_to_industry, calculate_distance_to_ternium
    try:
        gdf["distance_to_industry_osm_m"] = calculate_distance_to_industry(gdf)
        gdf["distance_to_ternium_m"] = calculate_distance_to_ternium(gdf)
    except Exception as e:
        print(f"[FEATURES] Error crítico al calcular distancias de industria: {e}")
        gdf["distance_to_industry_osm_m"] = np.nan
        gdf["distance_to_ternium_m"] = np.nan
        
    # 4. Calcular distancias a cuerpos de agua
    from src.water import calculate_distance_to_water
    try:
        gdf["distance_to_water_m"] = calculate_distance_to_water(gdf)
    except Exception as e:
        print(f"[FEATURES] Error crítico al calcular distancias de agua: {e}")
        gdf["distance_to_water_m"] = np.nan
        
    # 5. Guardar el dataset maestro unificado v2
    output_path = PROCESSED_DIR / "malla_maestra_mty_2026_v2.gpkg"
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    gdf.to_file(output_path, driver="GPKG", mode="w")
    
    print(f"[FEATURES] Dataset Maestro v2 creado con éxito. Guardado en: {output_path}")
    print(f"[FEATURES] Columnas finales: {list(gdf.columns)}")
    
    return gdf

def consolidate_master_features_v3():
    """
    Consolida las variables a nivel AGEB mediante agregación zonal
    e inicializa la malla de 30m v3 como una copia de compatibilidad física.
    
    Returns:
        gpd.GeoDataFrame: Malla maestra escala 30m.
    """
    print("\n[FEATURES] Iniciando consolidación a escala AGEB (Zonal Statistics)...")
    
    # 1. Cargar la malla maestra v2
    malla_v2_path = PROCESSED_DIR / "malla_maestra_mty_2026_v2.gpkg"
    if not malla_v2_path.exists():
        raise FileNotFoundError(f"No se encontró la malla maestra v2 en: {malla_v2_path}. Corra la fase 2 primero.")
        
    gdf = gpd.read_file(malla_v2_path)
    print(f"[FEATURES] Malla maestra v2 cargada con {len(gdf)} celdas.")
    
    # 2. Invocar la agregación de AGEB (crea ageb_maestra_mty_2026.gpkg)
    from src.ageb_social import aggregate_to_ageb_scale
    aggregate_to_ageb_scale(gdf)
    
    # 3. Guardar la malla maestra v3 para compatibilidad física en plots
    output_path = PROCESSED_DIR / "malla_maestra_mty_2026_v3.gpkg"
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    gdf.to_file(output_path, driver="GPKG", mode="w")
    
    print(f"[FEATURES] Malla v3 guardada para compatibilidad física en: {output_path}")
    return gdf
