"""
Módulo para el procesamiento y obtención de datos de cobertura de suelo de Dynamic World (GEE).
Calcula las fracciones de cobertura para clases construida, árboles, suelo desnudo, agua y pasto.
"""

import ee
import geemap
import rioxarray
import numpy as np
import geopandas as gpd
import rasterio
from src.gee_data import init_ee, get_aoi_geometry
from src.config import INTERIM_DIR, AOI_BBOX

def extract_dynamic_world(year=2026):
    """
    Carga la colección de Dynamic World en GEE para el AOI y año especificados,
    promedia las probabilidades temporales para las clases clave (built, trees, bare, water, grass)
    y exporta el resultado como un GeoTIFF multibanda en data/interim/.
    
    Args:
        year (int): Año de análisis. Por defecto 2026.
        
    Returns:
        str: Ruta del GeoTIFF multibanda guardado.
    """
    output_path = INTERIM_DIR / f"dw_mty_{year}.tif"
    if output_path.exists():
        print(f"[DYNAMIC WORLD] El archivo ya existe en {output_path}. Omitiendo descarga de GEE.")
        return str(output_path)
        
    print(f"\n[DYNAMIC WORLD] Iniciando extracción de coberturas para el año {year}...")
    
    # 1. Asegurar inicialización y obtener AOI
    try:
        ee.Feature(None)
    except Exception:
        init_ee()
    aoi = get_aoi_geometry()
    
    # 2. Filtrar colección para el mismo rango temporal de primavera (temporada cálida/seca)
    start_date = f"{year}-03-01"
    end_date = f"{year}-05-31"
    
    dw_col = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1") \
               .filterBounds(aoi) \
               .filterDate(start_date, end_date)
               
    count = dw_col.size().getInfo()
    if count == 0:
        raise ValueError(f"No se encontraron imágenes en la colección de Dynamic World para el rango {start_date} a {end_date}.")
    print(f"[DYNAMIC WORLD] Encontradas {count} imágenes en el período especificado.")
    
    # 3. Seleccionar bandas clave y promediar probabilidades (valores de 0 a 1)
    # Bandas requeridas: construido, árboles, suelo desnudo, agua y pasto
    selected_bands = ["built", "trees", "bare", "water", "grass"]
    dw_mean = dw_col.select(selected_bands).mean()
    
    # Convertir a porcentajes (0 a 100) para facilitar análisis posterior
    dw_pct = dw_mean.multiply(100.0)
    
    # 4. Descargar GeoTIFF multibanda locally a resolución de 10m (Sentinel-2 base)
    output_path = INTERIM_DIR / f"dw_mty_{year}.tif"
    print(f"[DYNAMIC WORLD] Descargando GeoTIFF multibanda a resolución de 10m...")
    
    geemap.download_ee_image(
        image=dw_pct,
        filename=str(output_path),
        region=aoi,
        scale=10,
        crs="EPSG:4326"
    )
    
    if output_path.exists():
        with rioxarray.open_rasterio(output_path) as src:
            print(f"[DYNAMIC WORLD] GeoTIFF multibanda descargado. Bandas: {src.rio.count}, Dimensiones: {src.rio.width}x{src.rio.height}")
    else:
        raise FileNotFoundError(f"No se pudo guardar el raster de Dynamic World en: {output_path}")
        
    return str(output_path)

def map_dw_to_grid(malla_gdf):
    """
    Lee el raster multibanda de Dynamic World y muestrea las intensidades de cobertura
    en el centroide de cada celda de la malla base en EPSG:4326.
    Añade las columnas: dw_built_pct, dw_trees_pct, dw_bare_pct, dw_water_pct y dw_grass_pct.
    
    Args:
        malla_gdf (gpd.GeoDataFrame): Malla base a enriquecer.
        
    Returns:
        gpd.GeoDataFrame: Malla enriquecida con las columnas de Dynamic World.
    """
    print("\n[DYNAMIC WORLD] Muestreando coberturas de suelo sobre la malla...")
    
    dw_path = INTERIM_DIR / "dw_mty_2026.tif"
    if not dw_path.exists():
        raise FileNotFoundError(f"No se encontró el GeoTIFF de Dynamic World en: {dw_path}")
        
    # Obtener centroides en la proyección UTM local y re-proyectar a WGS84 para muestreo
    centroids = malla_gdf.to_crs(epsg=32614).geometry.centroid.to_crs(epsg=4326)
    coords = [(geom.x, geom.y) for geom in centroids]
    
    # Orden de bandas descargadas: built, trees, bare, water, grass (1-indexed en rasterio)
    band_names = ["dw_built_pct", "dw_trees_pct", "dw_bare_pct", "dw_water_pct", "dw_grass_pct"]
    
    # Diccionario para almacenar valores muestreados
    sampled_data = {name: [] for name in band_names}
    
    with rasterio.open(dw_path) as src:
        nodata_val = src.nodata
        # Muestreo espacial por cada coordenada
        for values in src.sample(coords):
            for i, val in enumerate(values):
                name = band_names[i]
                if val == nodata_val or np.isnan(val):
                    sampled_data[name].append(np.nan)
                else:
                    # Acotar valores entre 0 y 100
                    sampled_data[name].append(float(np.clip(val, 0.0, 100.0)))
                    
    # Añadir al GeoDataFrame
    for name in band_names:
        malla_gdf[name] = sampled_data[name]
        
    print(f"[DYNAMIC WORLD] Mapeo completado para {len(band_names)} coberturas de suelo.")
    return malla_gdf
