"""
Módulo para extraer y procesar características de OpenStreetMap (OSM) utilizando OSMnx.
Proporciona métodos genéricos para descargar geometrías urbanas.
"""

import osmnx as ox
import geopandas as gpd

def download_osm_features(bbox, tags):
    """
    Descarga características de OpenStreetMap basadas en un Bounding Box y etiquetas específicas.
    
    Args:
        bbox (tuple): Bounding Box en formato (north, south, east, west).
        tags (dict): Diccionario de etiquetas de OSM a consultar.
        
    Returns:
        gpd.GeoDataFrame: Geometrías descargadas de OSM.
    """
    print(f"[OSM] Descargando características para las etiquetas: {tags}...")
    try:
        # En OSMnx 2.x, ox.features_from_bbox recibe una tupla bbox y etiquetas
        gdf = ox.features_from_bbox(bbox=bbox, tags=tags)
        print(f"[OSM] Descarga exitosa. Total de elementos obtenidos: {len(gdf)}")
        return gdf
    except Exception as e:
        print(f"[OSM] Error o advertencia al descargar de OSM: {e}")
        # Retornar GeoDataFrame vacío en caso de falla o ausencia de datos
        return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
