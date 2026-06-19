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
    print("INICIANDO ANÁLISIS DE ANOMALÍAS Y DETECCÓN DE HOTSPOTS DIURNOS REALES")
    print("=" * 80)
    
    outputs_dir = base_dir / "outputs" / "05"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    
    gpkg_path = base_dir / "data" / "processed" / "malla_modelado_multiescala_mty.gpkg"
    gdf = gpd.read_file(gpkg_path)
    
    # Limpiar nulos
    gdf_clean = gdf.dropna(subset=["lst_day_c", "suhi_day_c"]).copy()
    
    # -------------------------------------------------------------
    # 1. MAPA DE LA MANCHA URBANA COMPLETA (TODA LA ZMM DIURNA)
    # -------------------------------------------------------------
    print("[1/3] Generando mapa de toda la ZMM para la SUHI Diurna...")
    
    # --- VERSIÓN 1.1: SOLO POSITIVO (ISLAS CÁLIDAS) ---
    print("      Generando versión Solo Positivo (vmin=0)...")
    fig, ax = plt.subplots(figsize=(12, 12), dpi=300)
    gdf_map_all = gdf_clean.to_crs(epsg=3857)
    gdf_map_all.plot(
        column='suhi_day_c',
        cmap='magma',
        alpha=0.70,
        ax=ax,
        edgecolor='none',
        linewidth=0,
        vmin=0, # Mostrar desde 0 para enfocar en la isla cálida
        legend=True,
        legend_kwds={
            'label': 'Intensidad SUHI Diurna (°C)',
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
    ax.set_title("Intensidad SUHI Diurna en la ZMM (Malla Completa)", fontsize=22, fontweight='bold', pad=15, color='#263238')
    ax.set_axis_off()
    
    fig_all_zmm_path = outputs_dir / "real_day_suhi_zmm_all_cells.png"
    plt.savefig(fig_all_zmm_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"      Mapa de toda la ZMM (Solo Positivo) guardado en: {fig_all_zmm_path}")
    
    # --- VERSIÓN 1.2: GRADIENTE COMPLETO (ISLA FRÍA Y ISLA DE CALOR) ---
    print("      Generando versión Gradiente Completo (vmin=-10, vmax=10)...")
    fig, ax = plt.subplots(figsize=(12, 12), dpi=300)
    gdf_map_all.plot(
        column='suhi_day_c',
        cmap='coolwarm',
        alpha=0.70,
        ax=ax,
        edgecolor='none',
        linewidth=0,
        vmin=-10,
        vmax=10,
        legend=True,
        legend_kwds={
            'label': 'Intensidad SUHI Diurna (°C)',
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
    ax.set_title("Gradiente Térmico de la SUHI Diurna en la ZMM\n(Azul = Isla Fría | Rojo = Isla de Calor)", fontsize=20, fontweight='bold', pad=15, color='#263238')
    ax.set_axis_off()
    
    fig_full_gradient_path = outputs_dir / "real_day_suhi_zmm_full_gradient.png"
    plt.savefig(fig_full_gradient_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"      Mapa de toda la ZMM (Gradiente Completo) guardado en: {fig_full_gradient_path}")
    
    # -------------------------------------------------------------
    # 2. DETECTAR HOTSPOTS DIURNOS (PERCENTIL 95 DAY)
    # -------------------------------------------------------------
    print("[2/3] Detectando hotspots diurnos reales con DBSCAN...")
    p95_day = gdf_clean['suhi_day_c'].quantile(0.95)
    print(f"      Umbral térmico diurno del percentil 95: {p95_day:.3f} °C")
    
    gdf_warm_day = gdf_clean[gdf_clean['suhi_day_c'] >= p95_day].copy()
    print(f"      Número de celdas en el P95 diurno: {len(gdf_warm_day)}")
    
    # DBSCAN en metros (UTM Zona 14N)
    gdf_warm_day_utm = gdf_warm_day.to_crs(epsg=32614)
    centroids = gdf_warm_day_utm.geometry.centroid
    coords = np.column_stack((centroids.x, centroids.y))
    
    db = DBSCAN(eps=60, min_samples=3, n_jobs=-1)
    gdf_warm_day['hotspot_cluster_id'] = db.fit_predict(coords)
    
    # Filtrar celdas agrupadas (hotspots reales)
    gdf_clusters_day = gdf_warm_day[gdf_warm_day['hotspot_cluster_id'] != -1].copy()
    n_clusters = gdf_clusters_day['hotspot_cluster_id'].nunique()
    print(f"      Clusters diurnos contiguos detectados: {n_clusters}")
    
    # -------------------------------------------------------------
    # 3. GENERAR MAPA DE TODOS LOS HOTSPOTS DIURNOS REALES
    # -------------------------------------------------------------
    print("[3/3] Generando mapa satelital de los Hotspots Diurnos Reales...")
    fig, ax = plt.subplots(figsize=(12, 12), dpi=300)
    
    gdf_map_clusters = gdf_clusters_day.to_crs(epsg=3857)
    gdf_map_clusters.plot(
        column='suhi_day_c',
        cmap='magma',
        alpha=0.75,
        ax=ax,
        edgecolor='none',
        linewidth=0,
        vmin=0,
        legend=True,
        legend_kwds={
            'label': 'Intensidad SUHI Diurna (°C)',
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
    
    ax.set_title("Hotspots Térmicos Diurnos en la ZMM (P95)", fontsize=22, fontweight='bold', pad=15, color='#263238')
    ax.set_axis_off()
    
    fig_clusters_path = outputs_dir / "real_day_hotspots_overview_map.png"
    plt.savefig(fig_clusters_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"      Mapa de hotspots diurnos guardado en: {fig_clusters_path}")
    print("=" * 80)
    print("ANÁLISIS COMPLETADO EXITOSAMENTE")
    print("=" * 80)

if __name__ == "__main__":
    main()
