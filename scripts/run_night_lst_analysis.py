import os
import pathlib
import sys
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
import matplotlib.pyplot as plt
import contextily as ctx
from shapely.geometry import Point
import matplotlib.patches as mpatches

# Add base directory to path
base_dir = pathlib.Path(__file__).resolve().parent.parent
sys.path.append(str(base_dir))

# Google Earth Engine imports
import ee
import geemap
from src.gee_data import init_ee, get_aoi_geometry
from src.config import START_DATE_NIGHT, END_DATE_NIGHT, INTERIM_DIR, PROCESSED_DIR, YEAR

def main():
    print("=" * 80)
    # 1. GEE Night LST Collection from MODIS Daily Aqua (MYD11A1)
    print("[1/5] Conectando a GEE y consultando colección MODIS Aqua LST Night...")
    init_ee()
    aoi = get_aoi_geometry()
    
    # Rango de fechas para primavera 2026 (config)
    col_night = ee.ImageCollection("MODIS/061/MYD11A1") \
                  .filterBounds(aoi) \
                  .filterDate(START_DATE_NIGHT, END_DATE_NIGHT)
                  
    count = col_night.size().getInfo()
    print(f"      Escenas MODIS Aqua encontradas: {count}")
    if count == 0:
        raise ValueError("No se encontraron escenas MODIS Aqua en el periodo nocturno.")
        
    # Obtener proyección nativa para evitar que la reducción median() la pierda
    native_proj = col_night.first().select("LST_Night_1km").projection()
    
    # Calcular mediana temporal
    lst_night_median = col_night.select("LST_Night_1km").median()
    
    # Asignar proyección nativa antes de resamplear y luego calibrar a Celsius
    # MODIS LST Night se multiplica por 0.02 (factor de escala) y se resta 273.15 para Celsius
    lst_night_30m = lst_night_median.setDefaultProjection(native_proj) \
                                    .resample("bilinear") \
                                    .multiply(0.02) \
                                    .subtract(273.15) \
                                    .rename("LST_C")
    
    # Descargar raster local
    night_tif_path = INTERIM_DIR / "lst_night_2026.tif"
    print(f"[2/5] Descargando LST nocturno suavizado (30m) a: {night_tif_path}...")
    geemap.download_ee_image(
        image=lst_night_30m,
        filename=str(night_tif_path),
        region=aoi,
        scale=30,
        crs="EPSG:4326"
    )
    
    # 2. Calcular la Temperatura Rural Nocturna de Referencia
    print("[3/5] Calculando temperatura rural nocturna de control...")
    rural_zones = {
        "Este (Pesquería/Cadereyta)": [-100.10, 25.60, -99.90, 25.80],
        "Norte (Salinas Victoria)": [-100.30, 25.95, -100.10, 26.15],
        "Sur (Santiago/Allende)": [-100.15, 25.30, -99.95, 25.50]
    }
    
    zone_temps = []
    for name, coords in rural_zones.items():
        geom = ee.Geometry.Rectangle(coords)
        col_rural = ee.ImageCollection("MODIS/061/MYD11A1") \
                      .filterBounds(geom) \
                      .filterDate(START_DATE_NIGHT, END_DATE_NIGHT)
        median_modis = col_rural.select("LST_Night_1km").median().multiply(0.02).subtract(273.15)
        rural_median_info = median_modis.reduceRegion(
            reducer=ee.Reducer.median(),
            geometry=geom,
            scale=1000,
            maxPixels=1e9
        ).getInfo()
        temp = rural_median_info.get("LST_Night_1km")
        if temp is not None:
            print(f"      Zona rural nocturna - {name}: {temp:.2f}°C")
            zone_temps.append(temp)
            
    avg_rural_night = sum(zone_temps) / len(zone_temps) if zone_temps else 18.0
    print(f"      Temperatura rural de referencia promedio: {avg_rural_night:.2f}°C")
    
    # 3. Mapear datos a la Malla Maestra
    print("[4/5] Muestreando LST nocturno y calculando SUHI nocturno en la malla...")
    gpkg_path = base_dir / "data" / "processed" / "malla_modelado_multiescala_mty.gpkg"
    if not gpkg_path.exists():
        raise FileNotFoundError(f"No se encontró el geopackage en {gpkg_path}")
        
    gdf = gpd.read_file(gpkg_path)
    centroids = gdf.to_crs(epsg=32614).geometry.centroid.to_crs(epsg=4326)
    coords = [(geom.x, geom.y) for geom in centroids]
    
    with rasterio.open(night_tif_path) as src_lst:
        lst_nodata = src_lst.nodata
        lst_night_values = []
        for val in src_lst.sample(coords):
            v = val[0]
            if v == lst_nodata or np.isnan(v):
                lst_night_values.append(np.nan)
            else:
                lst_night_values.append(float(v))
                
    gdf["lst_night_c"] = lst_night_values
    gdf["suhi_night_c"] = gdf["lst_night_c"] - avg_rural_night
    
    # Guardar malla actualizada
    gdf.to_file(gpkg_path, driver="GPKG", mode="w")
    print(f"      Malla guardada con éxito en: {gpkg_path}")
    
    # 4. Generación de las Figuras Nocturnas en outputs/05/
    print("[5/5] Generando figuras de la SUHI nocturna (mismo estilo que diurnas)...")
    outputs_dir = base_dir / "outputs" / "05"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    
    # Cargar celdas de hotspots priorizados (usar la columna de clusters del Top 4 y Ternium de la malla)
    # Nota: Los hotspots se detectaron con DBSCAN en el script original (H1, H2, H3 son clusters prioritarios, H4 es Ternium)
    # Para ser consistentes con el script de hotspots, cargamos las celdas agrupadas
    clusters_path = base_dir / "outputs" / "05" / "04_all_hotspot_clusters.gpkg"
    if not clusters_path.exists():
        raise FileNotFoundError(f"Debe ejecutar scripts/run_hotspots_analysis.py primero para detectar los clusters")
        
    gdf_clusters = gpd.read_file(clusters_path)
    # Añadir valores nocturnos a las celdas agrupadas cruzando por ID (o muestreando de nuevo)
    # Como gdf_clusters ya tiene los centroides, podemos cruzarlo por el índice/id
    # Para simplificar y evitar problemas, hacemos un spatial join o cruzamos por 'geometry' o ID único si está disponible.
    # En run_hotspots_analysis.py las celdas son un subconjunto de la malla maestra.
    # Cruzamos por las coordenadas del centroide
    gdf_clusters_night = gdf_clusters.copy()
    
    # Mapeamos los valores de suhi_night_c a gdf_clusters_night usando sample
    centroids_c = gdf_clusters_night.to_crs(epsg=32614).geometry.centroid.to_crs(epsg=4326)
    coords_c = [(geom.x, geom.y) for geom in centroids_c]
    
    with rasterio.open(night_tif_path) as src_lst:
        lst_nodata = src_lst.nodata
        lst_night_values_c = []
        for val in src_lst.sample(coords_c):
            v = val[0]
            if v == lst_nodata or np.isnan(v):
                lst_night_values_c.append(np.nan)
            else:
                lst_night_values_c.append(float(v))
    gdf_clusters_night["lst_night_c"] = lst_night_values_c
    gdf_clusters_night["suhi_night_c"] = gdf_clusters_night["lst_night_c"] - avg_rural_night
    
    # Definir los mismos Top 3 IDs y Ternium (Cluster 38)
    # Los hotspots priorizados en run_hotspots_analysis.py son:
    # Cluster 44 (H1), Cluster 66 (H2), Cluster 5 (H3), Cluster 38 (H4)
    top_3_ids = [44, 66, 5]
    map_ids = top_3_ids + [38]
    
    # 4A. Generar Mapa Top 4 Hotspots Nocturno
    print("      Generando Mapa del Top 4 Hotspots Nocturno...")
    gdf_map_cells_night = gdf_clusters_night[gdf_clusters_night['hotspot_cluster_id'].isin(map_ids)].to_crs(epsg=3857)
    
    fig, ax = plt.subplots(figsize=(12, 12), dpi=300)
    
    # Dibujar la malla coloreada por SUHI nocturna
    gdf_map_cells_night.plot(
        column='suhi_night_c',
        cmap='magma',
        alpha=0.75,
        ax=ax,
        edgecolor='none',
        linewidth=0,
        vmin=0,
        legend=True,
        legend_kwds={
            'label': 'Intensidad SUHI Nocturna (°C)',
            'orientation': 'vertical',
            'pad': 0.02,
            'shrink': 0.6,
            'aspect': 30
        }
    )
    
    # Ajustar tamaño de textos en el colorbar
    cax = fig.axes[-1]
    cax.tick_params(labelsize=14)
    cax.yaxis.label.set_size(16)
    
    # Marcadores de hotspots (mismas posiciones que en diurnas)
    colors_markers = ['#b71c1c', '#e65100', '#f57c00', '#ffb300']
    
    # Centros aproximados del Top 3 (desde run_hotspots_analysis.py)
    # H1 (Cluster 44), H2 (Cluster 66), H3 (Cluster 5)
    # Para consistencia exacta, extraemos los centroides de cada cluster en el mapa
    for idx, cid in enumerate(top_3_ids):
        c_gdf = gdf_clusters_night[gdf_clusters_night['hotspot_cluster_id'] == cid]
        c_cent = c_gdf.to_crs(epsg=4326).geometry.union_all().centroid
        p_utm = gpd.GeoSeries([c_cent], crs="EPSG:4326").to_crs(epsg=3857).iloc[0]
        ax.plot(p_utm.x, p_utm.y, marker='o', color='white', markerfacecolor=colors_markers[idx], markersize=18, markeredgewidth=2, markeredgecolor='black')
        ax.annotate(f"H{idx+1}", (p_utm.x, p_utm.y), textcoords="offset points", xytext=(0,12), ha='center', fontsize=14, fontweight='bold', color='white',
                    path_effects=[plt.matplotlib.patheffects.withStroke(linewidth=3, foreground="black")])
                    
    # H4 (Ternium - Cluster 38)
    c38_gdf = gdf_clusters_night[gdf_clusters_night['hotspot_cluster_id'] == 38]
    c38_cent = c38_gdf.to_crs(epsg=4326).geometry.union_all().centroid
    t_utm = gpd.GeoSeries([c38_cent], crs="EPSG:4326").to_crs(epsg=3857).iloc[0]
    ax.plot(t_utm.x, t_utm.y, marker='o', color='white', markerfacecolor=colors_markers[3], markersize=18, markeredgewidth=2, markeredgecolor='black')
    ax.annotate("H4", (t_utm.x, t_utm.y), textcoords="offset points", xytext=(0,12), ha='center', fontsize=14, fontweight='bold', color='white',
                path_effects=[plt.matplotlib.patheffects.withStroke(linewidth=3, foreground="black")])
                
    # Ajustar límites geográficos para coincidir exactamente
    ax.set_xlim(-11175785.45, -11157512.80)
    ax.set_ylim(2953993.73, 2967054.28)
    
    # Descargar mapa base satelital
    ctx.add_basemap(ax, source=ctx.providers.Esri.WorldImagery)
    
    # Estética del mapa
    ax.set_title("Top 4 Hotspots Térmicos - Nocturno", fontsize=22, fontweight='bold', pad=15, color='#263238')
    ax.set_axis_off()
    
    # Crear la leyenda manual compacta (misma que diurnas)
    legend_patches = [
        mpatches.Patch(color=colors_markers[0], alpha=0.8, label='Hotspot 1 (Centro Mty / S. Nicolás)'),
        mpatches.Patch(color=colors_markers[1], alpha=0.8, label='Hotspot 2 (Zona Ind. San Nicolás)'),
        mpatches.Patch(color=colors_markers[2], alpha=0.8, label='Hotspot 3 (Eje Valle Oriente / San Pedro)'),
        mpatches.Patch(color=colors_markers[3], alpha=0.8, label='Hotspot 4 (San Nicolás - Cluster 38)')
    ]
    ax.legend(handles=legend_patches, loc='upper left', facecolor='#fafafa', edgecolor='#b0bec5', fontsize=8.5)
    
    fig_overview_path = outputs_dir / "hotspots_night_overview_map.png"
    plt.savefig(fig_overview_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"      Mapa Top 4 Nocturno guardado en: {fig_overview_path}")
    
    # 4B. Generar Mapa de Todos los Hotspots Nocturnos
    print("      Generando Mapa de Todos los Hotspots Nocturnos...")
    gdf_map_cells_all_night = gdf_clusters_night.to_crs(epsg=3857)
    
    fig, ax = plt.subplots(figsize=(12, 12), dpi=300)
    
    # Dibujar la malla de todos los hotspots coloreada por SUHI nocturna
    gdf_map_cells_all_night.plot(
        column='suhi_night_c',
        cmap='magma',
        alpha=0.75,
        ax=ax,
        edgecolor='none',
        linewidth=0,
        vmin=0,
        legend=True,
        legend_kwds={
            'label': 'Intensidad SUHI Nocturna (°C)',
            'orientation': 'vertical',
            'pad': 0.02,
            'shrink': 0.6,
            'aspect': 30
        }
    )
    
    # Ajustar tamaño de textos en el colorbar
    cax = fig.axes[-1]
    cax.tick_params(labelsize=14)
    cax.yaxis.label.set_size(16)
    
    # Ajustar límites geográficos para coincidir exactamente
    ax.set_xlim(-11175785.45, -11157512.80)
    ax.set_ylim(2953993.73, 2967054.28)
    
    # Descargar mapa base satelital
    ctx.add_basemap(ax, source=ctx.providers.Esri.WorldImagery)
    
    # Estética del mapa
    ax.set_title("Hotspots Térmicos Nocturnos en la ZMM", fontsize=22, fontweight='bold', pad=15, color='#263238')
    ax.set_axis_off()
    
    fig_all_overview_path = outputs_dir / "all_hotspots_night_overview_map.png"
    plt.savefig(fig_all_overview_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"      Mapa de todas las islas nocturnas guardado en: {fig_all_overview_path}")
    print("=" * 80)
    print("PROCESAMIENTO Y GENERACIÓN DE PRODUCTOS NOCTURNOS COMPLETADO EXITOSAMENTE")
    print("=" * 80)

if __name__ == "__main__":
    main()
