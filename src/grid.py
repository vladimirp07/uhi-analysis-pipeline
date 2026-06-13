"""
Módulo para la creación de mallas espaciales.
Genera una cuadrícula regular de 30 metros para el análisis espacial detallado de UHI
en Monterrey, basándose en la proyección UTM local.
"""

import numpy as np
import geopandas as gpd
from shapely.geometry import Polygon, box
from src.config import AOI_BBOX, INTERIM_DIR

def create_30m_grid():
    """
    Crea una malla regular de celdas cuadradas de 30 metros x 30 metros sobre el AOI.
    Proyecta el AOI temporalmente a UTM Zona 14N (EPSG:32614) para generar dimensiones
    métricas correctas, construye los polígonos, los convierte a GeoDataFrame,
    los re-proyecta a EPSG:4326, les asigna un identificador único (cell_id) y
    guarda la malla resultante en un archivo GeoPackage.
    
    Returns:
        gpd.GeoDataFrame: GeoDataFrame con la malla espacial generada en EPSG:4326.
    """
    # 1. Crear polígono del AOI en WGS84
    # AOI_BBOX: [min_lon, min_lat, max_lon, max_lat]
    aoi_polygon = box(*AOI_BBOX)
    aoi_gdf = gpd.GeoDataFrame(geometry=[aoi_polygon], crs="EPSG:4326")
    
    # Proyectar a UTM Zona 14N para operar con metros reales en Monterrey
    aoi_utm = aoi_gdf.to_crs(epsg=32614)
    minx, miny, maxx, maxy = aoi_utm.total_bounds
    
    # 2. Generar secuencias de coordenadas en intervalos de 30 metros
    x_coords = np.arange(minx, maxx, 30)
    y_coords = np.arange(miny, maxy, 30)
    
    # 3. Crear polígonos de 30m x 30m
    polygons = []
    for x in x_coords:
        for y in y_coords:
            # Polígono de 4 vértices cerrándose en el primero
            poly = Polygon([
                (x, y),
                (x + 30, y),
                (x + 30, y + 30),
                (x, y + 30),
                (x, y)
            ])
            polygons.append(poly)
            
    # 4. Crear GeoDataFrame en UTM 14N
    grid_gdf = gpd.GeoDataFrame(geometry=polygons, crs="EPSG:32614")
    
    # 5. Volver a proyectar a coordenadas geográficas (WGS84)
    grid_gdf = grid_gdf.to_crs(epsg=4326)
    
    # 6. Asignar ID incremental único a cada celda
    grid_gdf['cell_id'] = np.arange(len(grid_gdf)) + 1
    
    # Reordenar columnas para una estructura limpia
    grid_gdf = grid_gdf[['cell_id', 'geometry']]
    
    # 7. Guardar en formato GeoPackage en el directorio interim
    output_path = INTERIM_DIR / "malla_monterrey_30m.gpkg"
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    grid_gdf.to_file(output_path, driver="GPKG", mode="w")
    
    print(f"Malla de 30m creada con éxito. Total de celdas: {len(grid_gdf)}")
    print(f"GeoPackage guardado en: {output_path}")
    
    return grid_gdf
