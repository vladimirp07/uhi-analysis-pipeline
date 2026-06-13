"""
Módulo para el procesamiento y obtención del Índice de Vegetación de Diferencia Normalizada (NDVI).
Descarga y procesa imágenes de Sentinel-2 Level 2A desde Google Earth Engine.
"""

import ee
import geemap
import rioxarray
import numpy as np
from src.gee_data import init_ee, get_aoi_geometry, get_clear_image_collection
from src.config import INTERIM_DIR

def download_mty_ndvi(year=2026):
    """
    Descarga y procesa la capa de NDVI para Monterrey usando Sentinel-2 L2A.
    Filtra por la temporada cálida/seca del año especificado (1 de marzo al 31 de mayo),
    calcula el NDVI (B8 y B4) y genera una máscara binaria de vegetación verde (>0.3).
    Guarda ambos rasters resultantes como GeoTIFFs.
    
    Args:
        year (int): Año de análisis. Por defecto 2026.
        
    Returns:
        tuple: Rutas de los archivos GeoTIFF creados (ndvi_path, mask_path).
    """
    print(f"\n[NDVI] Iniciando procesamiento de NDVI para el año {year}...")
    
    # 1. Asegurar inicialización y obtener AOI
    init_ee()
    aoi = get_aoi_geometry()
    
    # Rango de fechas: temporada cálida/seca
    start_date = f"{year}-03-01"
    end_date = f"{year}-05-31"
    
    # 2. Obtener colección Sentinel-2 L2A filtrada y ordenada por nubosidad
    collection_id = "COPERNICUS/S2_SR_HARMONIZED"
    print(f"[NDVI] Buscando escena con menor nubosidad en {collection_id} del {start_date} al {end_date}...")
    collection = get_clear_image_collection(collection_id, start_date, end_date)
    
    # Verificar si hay imágenes en la colección
    count = collection.size().getInfo()
    if count == 0:
        raise ValueError(f"No se encontraron imágenes en la colección {collection_id} para el rango de fechas {start_date} a {end_date}.")
        
    # Seleccionar la primera escena
    best_image = ee.Image(collection.first())
    scene_id = best_image.get("system:index").getInfo()
    cloud_cover = best_image.get("CLOUDY_PIXEL_PERCENTAGE").getInfo()
    print(f"[NDVI] Escena seleccionada: {scene_id} (Nubosidad: {cloud_cover:.2f}%)")
    
    # 3. Calcular NDVI usando normalizedDifference: (B8 - B4) / (B8 + B4)
    # Sentinel-2 B8 es NIR (842 nm, 10m) y B4 es Red (665 nm, 10m)
    ndvi = best_image.normalizedDifference(["B8", "B4"]).rename("NDVI")
    
    # 4. Descargar el raster de NDVI como GeoTIFF
    ndvi_path = INTERIM_DIR / f"ndvi_mty_{year}.tif"
    print(f"[NDVI] Descargando raster de NDVI (resolución: 10m)...")
    
    geemap.download_ee_image(
        image=ndvi,
        filename=str(ndvi_path),
        region=aoi,
        scale=10,
        crs="EPSG:4326"
    )
    
    # 5. Generar la máscara de vegetación verde (NDVI > 0.3) localmente con rioxarray
    mask_path = INTERIM_DIR / f"green_mask_mty_{year}.tif"
    print(f"[NDVI] Generando máscara de vegetación localmente (NDVI > 0.3)...")
    
    if ndvi_path.exists():
        # Leer el NDVI descargado usando rioxarray
        with rioxarray.open_rasterio(ndvi_path) as ndvi_ds:
            # Identificar píxeles nodata e infinitos del raster original
            orig_nodata = ndvi_ds.rio.nodata
            is_nodata = (ndvi_ds.isnull() | 
                         (ndvi_ds == orig_nodata) | 
                         (ndvi_ds == -np.inf) | 
                         (ndvi_ds == np.inf))
            
            # Crear máscara binaria (1 para NDVI > 0.3, 0 para no-vegetación)
            green_mask = (ndvi_ds > 0.3).astype("uint8")
            
            # Reasignar el valor nodata de 255 a los píxeles nodata originales
            green_mask = green_mask.where(~is_nodata, 255).astype("uint8")
            
            # Configurar el metadato de nodata a 255 para que coincida con uint8
            green_mask.rio.write_nodata(255, inplace=True)
            
            # Asegurar conservar metadatos espaciales y guardar
            green_mask.rio.to_raster(mask_path)
            print(f"[NDVI] Máscara de vegetación guardada con éxito en: {mask_path}")
            print(f"[NDVI] Dimensiones de la máscara: {green_mask.rio.width}x{green_mask.rio.height}")
    else:
        raise FileNotFoundError(f"No se pudo encontrar el GeoTIFF de NDVI base en {ndvi_path}")
        
    return str(ndvi_path), str(mask_path)
