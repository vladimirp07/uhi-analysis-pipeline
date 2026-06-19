import os
import sys
import pathlib
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
from shapely.geometry import Point
from sklearn.cluster import DBSCAN
import matplotlib.patches as mpatches

# Add base directory to path
base_dir = pathlib.Path(__file__).resolve().parent.parent
sys.path.append(str(base_dir))

def main():
    print("=" * 80)
    print("INICIANDO ANÁLISIS DE ANOMALÍAS Y DETECCÓN DE HOTSPOTS NOCTURNOS REALES")
    print("=" * 80)
    
    outputs_dir = base_dir / "outputs" / "05"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    
    gpkg_path = base_dir / "data" / "processed" / "malla_modelado_multiescala_mty.gpkg"
    gdf = gpd.read_file(gpkg_path)
    
    # Limpiar nulos
    gdf_clean = gdf.dropna(subset=["lst_night_c", "suhi_night_c"]).copy()
    
    # -------------------------------------------------------------
    # 1. MAPA DE LA MANCHA URBANA COMPLETA (TODA LA ZMM)
    # -------------------------------------------------------------
    print("[1/3] Generando mapa de toda la ZMM para la SUHI Nocturna...")
    fig, ax = plt.subplots(figsize=(12, 12), dpi=300)
    
    # Dibujar todas las celdas de la malla
    gdf_map_all = gdf_clean.to_crs(epsg=3857)
    gdf_map_all.plot(
        column='suhi_night_c',
        cmap='magma',
        alpha=0.70,
        ax=ax,
        edgecolor='none',
        linewidth=0,
        vmin=0, # Mostrar desde 0 para enfocar en la isla cálida
        legend=True,
        legend_kwds={
            'label': 'Intensidad SUHI Nocturna (°C)',
            'orientation': 'vertical',
            'pad': 0.02,
            'shrink': 0.6,
            'aspect': 30
        }
    )
    
    # Ajustar colorbar
    cax = fig.axes[-1]
    cax.tick_params(labelsize=14)
    cax.yaxis.label.set_size(16)
    
    ax.set_xlim(-11175785.45, -11157512.80)
    ax.set_ylim(2953993.73, 2967054.28)
    ctx.add_basemap(ax, source=ctx.providers.Esri.WorldImagery)
    
    ax.set_title("Intensidad SUHI Nocturna en la ZMM (Malla Completa)", fontsize=22, fontweight='bold', pad=15, color='#263238')
    ax.set_axis_off()
    
    fig_all_zmm_path = outputs_dir / "real_night_suhi_zmm_all_cells.png"
    plt.savefig(fig_all_zmm_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"      Mapa de toda la ZMM guardado en: {fig_all_zmm_path}")
    
    # -------------------------------------------------------------
    # 2. DETECTAR ACTUALES HOTSPOTS NOCTURNOS (PERCENTIL 95 NIGHT)
    # -------------------------------------------------------------
    print("[2/3] Detectando hotspots nocturnos reales con DBSCAN...")
    p95_night = gdf_clean['suhi_night_c'].quantile(0.95)
    print(f"      Umbral térmico nocturno del percentil 95: {p95_night:.3f} °C")
    
    gdf_warm_night = gdf_clean[gdf_clean['suhi_night_c'] >= p95_night].copy()
    print(f"      Número de celdas en el P95 nocturno: {len(gdf_warm_night)}")
    
    # DBSCAN en metros (UTM Zona 14N)
    gdf_warm_night_utm = gdf_warm_night.to_crs(epsg=32614)
    centroids = gdf_warm_night_utm.geometry.centroid
    coords = np.column_stack((centroids.x, centroids.y))
    
    db = DBSCAN(eps=60, min_samples=3, n_jobs=-1)
    gdf_warm_night['hotspot_cluster_id'] = db.fit_predict(coords)
    
    # Filtrar celdas agrupadas (hotspots reales)
    gdf_clusters_night = gdf_warm_night[gdf_warm_night['hotspot_cluster_id'] != -1].copy()
    n_clusters = gdf_clusters_night['hotspot_cluster_id'].nunique()
    print(f"      Clusters nocturnos contiguos detectados: {n_clusters}")
    
    # Guardar clusters nocturnos para referencia
    clusters_output_path = outputs_dir / "05_real_night_hotspot_clusters.gpkg"
    gdf_clusters_night.to_file(clusters_output_path, driver="GPKG", mode="w")
    
    # -------------------------------------------------------------
    # 3. GENERAR MAPA DE TODOS LOS HOTSPOTS NOCTURNOS REALES
    # -------------------------------------------------------------
    print("[3/3] Generando mapa satelital de los Hotspots Nocturnos Reales...")
    fig, ax = plt.subplots(figsize=(12, 12), dpi=300)
    
    gdf_map_clusters = gdf_clusters_night.to_crs(epsg=3857)
    gdf_map_clusters.plot(
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
    
    cax = fig.axes[-1]
    cax.tick_params(labelsize=14)
    cax.yaxis.label.set_size(16)
    
    ax.set_xlim(-11175785.45, -11157512.80)
    ax.set_ylim(2953993.73, 2967054.28)
    ctx.add_basemap(ax, source=ctx.providers.Esri.WorldImagery)
    
    ax.set_title("Hotspots Térmicos Nocturnos Reales en la ZMM (P95)", fontsize=22, fontweight='bold', pad=15, color='#263238')
    ax.set_axis_off()
    
    fig_clusters_path = outputs_dir / "real_night_hotspots_overview_map.png"
    plt.savefig(fig_clusters_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"      Mapa de hotspots nocturnos reales guardado en: {fig_clusters_path}")
    print("=" * 80)
    print("ANÁLISIS COMPLETADO EXITOSAMENTE")
    print("=" * 80)

if __name__ == "__main__":
    main()
