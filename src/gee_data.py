"""
Módulo para interactuar con Google Earth Engine (GEE).
Implementa la autenticación, inicialización y filtrado de colecciones de imágenes
reducidas por nubosidad para el área de interés (AOI).
"""

import ee
from src.config import AOI_BBOX

def init_ee():
    """
    Inicializa la API de Google Earth Engine.
    Intenta inicializar; si falla, intenta autenticar e inicializar nuevamente.
    Si ambos fallan, muestra instrucciones claras para la terminal.
    """
    try:
        ee.Initialize()
        print("Google Earth Engine inicializado correctamente.")
    except Exception as e:
        print(f"La inicialización directa de GEE falló: {e}")
        print("Intentando autenticación automática...")
        try:
            ee.Authenticate()
            ee.Initialize()
            print("Autenticación e inicialización de GEE exitosa.")
        except Exception as auth_error:
            print("\n" + "="*80)
            print("ERROR CRÍTICO: No se pudo conectar a Google Earth Engine.")
            print("Por favor, ejecuta el siguiente comando en tu terminal para autenticar tu cuenta:")
            print("    earthengine authenticate")
            print("="*80 + "\n")
            raise auth_error

def get_aoi_geometry():
    """
    Retorna un objeto ee.Geometry.Rectangle correspondiente a los límites del AOI en config.
    
    Returns:
        ee.Geometry.Rectangle: Geometría rectangular del AOI.
    """
    # AOI_BBOX: [min_lon, min_lat, max_lon, max_lat]
    return ee.Geometry.Rectangle(AOI_BBOX)

def get_clear_image_collection(collection_name, start_date, end_date):
    """
    Inicializa GEE, obtiene la colección de imágenes, la filtra por fechas y AOI,
    y la ordena de menor a mayor nubosidad.
    
    Args:
        collection_name (str): ID de la colección en Earth Engine (ej. 'LANDSAT/LC09/C02/T1_L2').
        start_date (str): Fecha de inicio en formato 'YYYY-MM-DD'.
        end_date (str): Fecha de fin en formato 'YYYY-MM-DD'.
        
    Returns:
        ee.ImageCollection: Colección filtrada y ordenada por nubosidad.
    """
    # Asegurar inicialización
    try:
        # Intentar verificar si ya está inicializado llamando a un método simple
        ee.Feature(None)
    except Exception:
        init_ee()
        
    aoi = get_aoi_geometry()
    
    # Filtrar colección
    collection = ee.ImageCollection(collection_name) \
                   .filterBounds(aoi) \
                   .filterDate(start_date, end_date)
    
    # Determinar metadato de nubosidad según la colección
    # Sentinel-2 usa 'CLOUDY_PIXEL_PERCENTAGE', Landsat usa 'CLOUD_COVER'
    if "COPERNICUS" in collection_name or "S2" in collection_name:
        cloud_prop = "CLOUDY_PIXEL_PERCENTAGE"
    else:
        cloud_prop = "CLOUD_COVER"
        
    # Ordenar por menor nubosidad
    collection_sorted = collection.sort(cloud_prop)
    
    return collection_sorted
