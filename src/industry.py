"""
Módulo para el procesamiento y extracción de zonas industriales desde OpenStreetMap.
Calcula el porcentaje de uso de suelo industrial para cada celda de la malla base
y las distancias a la zona industrial y a la planta de Ternium.
"""

import numpy as np
import geopandas as gpd
from shapely.geometry import Point
from src.config import AOI_BBOX, INTERIM_DIR
from src.osm_features import download_osm_features

def extract_industrial_polygons():
    """
    Descarga polígonos industriales de OpenStreetMap para el AOI del proyecto,
    calcula la intersección espacial con la malla de 30m y determina el porcentaje
    de cobertura industrial (industrial_osm_pct) en cada celda de la malla.
    Guarda la capa resultante en formato GeoPackage.
    
    Returns:
        gpd.GeoDataFrame: Malla base enriquecida con el porcentaje industrial.
    """
    output_path = INTERIM_DIR / "malla_industria_2026.gpkg"
    if output_path.exists():
        print(f"[INDUSTRY] El archivo ya existe en {output_path}. Omitiendo procesamiento y descarga de OSM.")
        return gpd.read_file(output_path)
        
    print("\n[INDUSTRY] Iniciando extracción de zonas industriales...")
    
    # 1. Cargar la malla (preferir malla_features_2026.gpkg para acumular LST/NDVI)
    features_path = INTERIM_DIR / "malla_features_2026.gpkg"
    grid_path = INTERIM_DIR / "malla_monterrey_30m.gpkg"
    
    if features_path.exists():
        load_path = features_path
        print("[INDUSTRY] Cargando malla enriquecida con datos satelitales preexistentes...")
    elif grid_path.exists():
        load_path = grid_path
        print("[INDUSTRY] Cargando malla base...")
    else:
        raise FileNotFoundError(f"No se encontró ninguna malla base en {grid_path}")
        
    grid_gdf = gpd.read_file(load_path)
    
    # 2. Configurar límites para OSMnx
    # En OSMnx 2.x, el formato de bbox es (left, bottom, right, top) -> (min_lon, min_lat, max_lon, max_lat)
    bbox = tuple(AOI_BBOX)
    
    # Etiquetas para buscar áreas industriales
    tags = {
        "landuse": "industrial",
        "building": "industrial"
    }
    
    # 3. Descargar datos industriales
    industrial_gdf = download_osm_features(bbox, tags)
    
    # Inicializar columna
    grid_gdf["industrial_osm_pct"] = 0.0
    
    if len(industrial_gdf) > 0:
        # Filtrar solo polígonos y multipolígonos
        industrial_polys = industrial_gdf[industrial_gdf.geometry.type.isin(["Polygon", "MultiPolygon"])]
        
        if len(industrial_polys) > 0:
            print(f"[INDUSTRY] Encontrados {len(industrial_polys)} polígonos industriales.")
            
            # Reproyectar a UTM 14N para cálculos métricos precisos
            grid_utm = grid_gdf.to_crs(epsg=32614)
            industrial_utm = industrial_polys.to_crs(epsg=32614)
            
            # Disolver polígonos industriales en una única geometría para evitar duplicados en intersecciones
            print("[INDUSTRY] Resolviendo superposiciones de polígonos industriales (unary_union)...")
            industrial_union = industrial_utm.geometry.unary_union
            
            # Crear un dataframe temporal para búsqueda espacial por índice
            ind_union_gdf = gpd.GeoDataFrame(geometry=[industrial_union], crs="EPSG:32614")
            
            # Búsqueda espacial rápida usando join para ver qué celdas intersectan
            print("[INDUSTRY] Calculando intersección espacial con la malla...")
            intersecting_cells = gpd.sjoin(grid_utm, ind_union_gdf, how="inner", predicate="intersects")
            intersecting_ids = intersecting_cells["cell_id"].unique()
            
            if len(intersecting_ids) > 0:
                print(f"[INDUSTRY] Calculando porcentaje de cobertura industrial para {len(intersecting_ids)} celdas...")
                subset = grid_utm[grid_utm["cell_id"].isin(intersecting_ids)].copy()
                
                # Calcular intersección geométrica exacta
                intersections = subset.geometry.intersection(industrial_union)
                
                # Calcular porcentaje de cobertura
                inter_areas = intersections.area
                cell_areas = subset.geometry.area
                pcts = (inter_areas / cell_areas) * 100.0
                
                # Asignar valores
                grid_gdf.loc[grid_gdf["cell_id"].isin(intersecting_ids), "industrial_osm_pct"] = np.clip(pcts, 0.0, 100.0)
        else:
            print("[INDUSTRY] No se encontraron geometrías de tipo Polygon/MultiPolygon en los datos industriales.")
    else:
        print("[INDUSTRY] No se obtuvieron datos industriales de OpenStreetMap en este AOI.")
        
    # Guardar en data/interim/malla_industria_2026.gpkg
    output_path = INTERIM_DIR / "malla_industria_2026.gpkg"
    grid_gdf.to_file(output_path, driver="GPKG", mode="w")
    print(f"[INDUSTRY] Capa industrial guardada con éxito en: {output_path}")
    
    # Mostrar breves estadísticas
    active_cells = (grid_gdf["industrial_osm_pct"] > 0.0).sum()
    max_pct = grid_gdf["industrial_osm_pct"].max()
    print(f"[INDUSTRY] Resumen: {active_cells} celdas intersectan con industria. Cobertura máxima en celda: {max_pct:.2f}%")
    
    return grid_gdf

def calculate_distance_to_industry(malla_gdf):
    """
    Calcula la distancia mínima en metros desde el centroide de cada celda
    de la malla al polígono industrial general más cercano de OSM.
    Proyecta las geometrías a UTM Zona 14N (EPSG:32614) para medir en metros.
    
    Args:
        malla_gdf (gpd.GeoDataFrame): GeoDataFrame de la malla.
        
    Returns:
        np.ndarray: Distancias calculadas en metros.
    """
    print("\n[INDUSTRY] Calculando distancias al polígono industrial más cercano...")
    
    # 1. Bbox y etiquetas para OSMnx
    bbox = tuple(AOI_BBOX)
    tags = {
        "landuse": "industrial",
        "building": "industrial"
    }
    
    # 2. Descargar datos industriales
    industrial_gdf = download_osm_features(bbox, tags)
    
    # 3. Obtener centroides en UTM 14N
    grid_utm = malla_gdf.to_crs(epsg=32614)
    centroids = grid_utm.geometry.centroid
    
    if len(industrial_gdf) > 0:
        # Filtrar polígonos
        industrial_polys = industrial_gdf[industrial_gdf.geometry.type.isin(["Polygon", "MultiPolygon"])]
        if len(industrial_polys) > 0:
            # Reproyectar
            industrial_utm = industrial_polys.to_crs(epsg=32614)
            print("[INDUSTRY] Disolviendo huellas industriales para optimizar cálculo de distancias...")
            industrial_union = industrial_utm.geometry.unary_union
            
            # Calcular distancias
            distances = centroids.distance(industrial_union)
            return distances.values
            
    print("[INDUSTRY] Advertencia: No se encontraron zonas industriales. Retornando distancias NaN.")
    return np.full(len(malla_gdf), np.nan)

def calculate_distance_to_ternium(malla_gdf):
    """
    Calcula la distancia en metros desde el centroide de cada celda de la malla
    al centroide aproximado de la planta de Ternium Guerrero (Point(-100.305, 25.710)).
    
    Args:
        malla_gdf (gpd.GeoDataFrame): GeoDataFrame de la malla.
        
    Returns:
        np.ndarray: Distancias en metros.
    """
    print("\n[INDUSTRY] Calculando distancias al centro de la planta Ternium Guerrero...")
    
    # 1. Definir punto de referencia y proyectarlo a UTM 14N
    ternium_point = gpd.GeoDataFrame(
        geometry=[Point(-100.299792, 25.720855)],
        crs="EPSG:4326"
    ).to_crs(epsg=32614).geometry.iloc[0]
    
    # 2. Obtener centroides en UTM 14N
    grid_utm = malla_gdf.to_crs(epsg=32614)
    centroids = grid_utm.geometry.centroid
    
    # 3. Calcular distancias
    distances = centroids.distance(ternium_point)
    return distances.values
