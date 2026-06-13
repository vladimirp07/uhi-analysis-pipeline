"""
Módulo para el procesamiento e identificación de cuerpos de agua.
Descarga cuerpos de agua desde OpenStreetMap y calcula las distancias de proximidad.
"""

import numpy as np
import geopandas as gpd
from src.config import AOI_BBOX, INTERIM_DIR
from src.osm_features import download_osm_features

def extract_water_bodies():
    """
    Descarga polígonos de cuerpos de agua de OpenStreetMap para el AOI,
    los disuelve en una única geometría en UTM Zona 14N y los guarda en un archivo GeoPackage.
    
    Returns:
        gpd.GeoDataFrame: Capa de polígonos de cuerpos de agua en UTM 14N.
    """
    print("\n[WATER] Iniciando extracción de cuerpos de agua desde OSM...")
    
    # 1. Configurar límites para OSMnx
    bbox = tuple(AOI_BBOX)
    
    # Etiquetas de OSM asociadas a cuerpos de agua
    tags = {
        "natural": "water",
        "waterway": "riverbank",
        "landuse": "reservoir"
    }
    
    # 2. Descargar datos
    water_gdf = download_osm_features(bbox, tags)
    
    # Filtrar solo polígonos
    if len(water_gdf) > 0:
        water_polys = water_gdf[water_gdf.geometry.type.isin(["Polygon", "MultiPolygon"])]
        
        if len(water_polys) > 0:
            print(f"[WATER] Encontrados {len(water_polys)} polígonos de agua.")
            
            # Reproyectar a UTM 14N
            water_utm = water_polys.to_crs(epsg=32614)
            
            # Disolver en una sola geometría para simplificar cálculos
            print("[WATER] Disolviendo capas de agua (unary_union)...")
            water_union = water_utm.geometry.unary_union
            
            # Guardar en data/interim/
            output_gdf = gpd.GeoDataFrame(geometry=[water_union], crs="EPSG:32614")
            output_path = INTERIM_DIR / "cuerpos_agua_2026.gpkg"
            output_gdf.to_file(output_path, driver="GPKG", mode="w")
            print(f"[WATER] Capa de agua guardada exitosamente en: {output_path}")
            return output_gdf
            
    print("[WATER] Advertencia: No se encontraron cuerpos de agua en el AOI.")
    # Guardar capa vacía
    output_gdf = gpd.GeoDataFrame(geometry=[], crs="EPSG:32614")
    output_path = INTERIM_DIR / "cuerpos_agua_2026.gpkg"
    output_gdf.to_file(output_path, driver="GPKG", mode="w")
    return output_gdf

def calculate_distance_to_water(malla_gdf):
    """
    Calcula la distancia mínima en metros desde el centroide de cada celda de la malla
    al cuerpo de agua más cercano de OSM.
    Proyecta a UTM Zona 14N (EPSG:32614) para medir en metros.
    
    Args:
        malla_gdf (gpd.GeoDataFrame): GeoDataFrame de la malla.
        
    Returns:
        np.ndarray: Distancias en metros.
    """
    print("\n[WATER] Calculando distancias al cuerpo de agua más cercano...")
    
    # 1. Intentar cargar desde interim
    water_path = INTERIM_DIR / "cuerpos_agua_2026.gpkg"
    
    if water_path.exists():
        water_gdf = gpd.read_file(water_path)
    else:
        water_gdf = extract_water_bodies()
        
    # 2. Calcular distancias
    grid_utm = malla_gdf.to_crs(epsg=32614)
    centroids = grid_utm.geometry.centroid
    
    if len(water_gdf) > 0 and not water_gdf.geometry.is_empty.all():
        water_union = water_gdf.geometry.iloc[0]
        distances = centroids.distance(water_union)
        return distances.values
        
    print("[WATER] Advertencia: No hay cuerpos de agua registrados para medir distancias. Retornando NaN.")
    return np.full(len(malla_gdf), np.nan)
