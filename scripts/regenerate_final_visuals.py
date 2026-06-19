import os
import sys
import pathlib
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
from shapely.geometry import box, Point
from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.patches as mpatches

# Add base directory to path
base_dir = pathlib.Path(__file__).resolve().parent.parent
sys.path.append(str(base_dir))

def main():
    print("=" * 80)
    print("REGENERANDO CASOS DE ESTUDIO (ZOOM) Y MAPA DE ZONAS RURALES DE LA EPA")
    print("=" * 80)
    
    outputs_dir = base_dir / "outputs" / "05"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    
    # -------------------------------------------------------------
    # 1. REGENERACIÓN DE MAPAS DE ZOOM CON ESCALA AJUSTADA
    # -------------------------------------------------------------
    print("[1/2] Cargando malla maestra y clusters diurnos...")
    gpkg_path = base_dir / "data" / "processed" / "malla_modelado_multiescala_mty.gpkg"
    gdf_malla = gpd.read_file(gpkg_path)
    
    clusters_path = outputs_dir / "04_all_hotspot_clusters.gpkg"
    if not clusters_path.exists():
        raise FileNotFoundError(f"Debe ejecutar scripts/run_hotspots_analysis.py primero.")
        
    gdf_clusters = gpd.read_file(clusters_path)
    
    # Cruzamos con la malla maestra para obtener suhi_day_c calculado con el baseline de la EPA (32.09°C)
    gdf_clusters_recalc = gdf_clusters[['cell_id', 'hotspot_cluster_id']].merge(
        gdf_malla[['cell_id', 'geometry', 'lst_day_c', 'suhi_day_c']], 
        on='cell_id', 
        how='inner'
    )
    gdf_clusters_recalc = gpd.GeoDataFrame(gdf_clusters_recalc, geometry='geometry', crs=gdf_malla.crs)
    
    # Top 3 IDs y Ternium (Cluster 38)
    top_3_ids = [44, 66, 5]
    map_ids = top_3_ids + [38]
    
    for i, cid in enumerate(top_3_ids):
        print(f"      Regenerando Zoom Map: Hotspot {i+1} (Cluster {cid})...")
        c_gdf = gdf_clusters_recalc[gdf_clusters_recalc['hotspot_cluster_id'] == cid].to_crs(epsg=3857)
        
        fig, ax = plt.subplots(figsize=(10, 10), dpi=300)
        
        # Dibujar celdas
        im = c_gdf.plot(
            column='suhi_day_c',
            cmap='magma',
            alpha=0.75,
            ax=ax,
            edgecolor='none',
            linewidth=0,
            vmin=0,
            vmax=10 # Forzar escala unificada a 10°C para comparabilidad directa
        )
        
        # Ajustar límites con padding
        bbox = c_gdf.unary_union.envelope
        minx, miny, maxx, maxy = bbox.bounds
        pad_x = (maxx - minx) * 0.2
        pad_y = (maxy - miny) * 0.2
        ax.set_xlim(minx - pad_x, maxx + pad_x)
        ax.set_ylim(miny - pad_y, maxy + pad_y)
        
        ctx.add_basemap(ax, source=ctx.providers.Esri.WorldImagery)
        
        mean_suhi = c_gdf['suhi_day_c'].mean()
        ax.set_title(f"Aproximación Satelital: Hotspot {i+1} (Cluster {int(cid)})\nSUHI Diurna Promedio (EPA): {mean_suhi:.2f}°C | Área: {(len(c_gdf)*900)/10000:.1f} ha",
                     fontsize=12, fontweight='bold', pad=12, color='#263238')
        ax.set_axis_off()
        
        # Forzar colorbar a tener exactamente la misma altura que el plot
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.1)
        cbar = fig.colorbar(ax.collections[0], cax=cax)
        cbar.set_label('Intensidad SUHI Diurna (°C)', fontsize=10, fontweight='bold', labelpad=10)
        cbar.ax.tick_params(labelsize=9)
        
        fig_zoom_path = outputs_dir / f"hotspot_{i+1}_zoom_map.png"
        plt.savefig(fig_zoom_path, dpi=300, bbox_inches='tight')
        plt.close()
        
    # Zoom Map Ternium (Hotspot 4 - Cluster 38)
    print(f"      Regenerando Zoom Map: Hotspot 4 (Ternium - Cluster 38)...")
    t_gdf_c38 = gdf_clusters_recalc[gdf_clusters_recalc['hotspot_cluster_id'] == 38].to_crs(epsg=3857)
    
    fig, ax = plt.subplots(figsize=(10, 10), dpi=300)
    
    if not t_gdf_c38.empty:
        t_gdf_c38.plot(
            column='suhi_day_c',
            cmap='magma',
            alpha=0.75,
            ax=ax,
            edgecolor='none',
            linewidth=0,
            vmin=0,
            vmax=10
        )
        bbox = t_gdf_c38.unary_union.envelope
        minx, miny, maxx, maxy = bbox.bounds
        pad_x = (maxx - minx) * 2.5
        pad_y = (maxy - miny) * 2.5
        ax.set_xlim(minx - pad_x, maxx + pad_x)
        ax.set_ylim(miny - pad_y, maxy + pad_y)
        
    ctx.add_basemap(ax, source=ctx.providers.Esri.WorldImagery)
    
    mean_suhi_t = t_gdf_c38['suhi_day_c'].mean() if not t_gdf_c38.empty else 0.0
    ax.set_title(f"Aproximación Satelital: Hotspot 4 (Ternium - Cluster 38)\nSUHI Diurna Promedio (EPA): {mean_suhi_t:.2f}°C | Área: 1.6 ha",
                 fontsize=12, fontweight='bold', pad=12, color='#263238')
    ax.set_axis_off()
    
    # Forzar colorbar a tener la misma altura que el plot
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.1)
    cbar = fig.colorbar(ax.collections[0], cax=cax)
    cbar.set_label('Intensidad SUHI Diurna (°C)', fontsize=10, fontweight='bold', labelpad=10)
    cbar.ax.tick_params(labelsize=9)
    
    fig_ternium_path = outputs_dir / "hotspot_ternium_zoom_map.png"
    plt.savefig(fig_ternium_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    # -------------------------------------------------------------
    # 2. GENERAR MAPA DE LAS 3 ZONAS DE REFERENCIA RURALES DE LA EPA
    # -------------------------------------------------------------
    print("[2/2] Generando mapa de las 3 zonas rurales de referencia de la EPA...")
    
    # Coordenadas de las 3 zonas
    rural_zones = {
        "Este (Pesquería/Cadereyta)": box(-100.10, 25.60, -99.90, 25.80),
        "Norte (Salinas Victoria)": box(-100.30, 25.95, -100.10, 26.15),
        "Sur (Santiago/Allende)": box(-100.15, 25.30, -99.95, 25.50)
    }
    
    rural_gdf = gpd.GeoDataFrame(
        {"name": list(rural_zones.keys()), "geometry": list(rural_zones.values())},
        crs="EPSG:4326"
    )
    
    # Bounding Box de la ZMM para referencia
    zmm_poly = box(-100.42, 25.60, -100.20, 25.78)
    zmm_gdf = gpd.GeoDataFrame(
        {"name": ["Zona Metropolitana de Monterrey (ZMM)"], "geometry": [zmm_poly]},
        crs="EPSG:4326"
    )
    
    # Plotear mapa regional
    fig, ax = plt.subplots(figsize=(16, 10), dpi=300)
    
    # Proyectar a Web Mercator para basemap
    rural_gdf_3857 = rural_gdf.to_crs(epsg=3857)
    zmm_gdf_3857 = zmm_gdf.to_crs(epsg=3857)
    
    # Dibujar ZMM con borde azul y relleno transparente
    zmm_gdf_3857.plot(
        ax=ax,
        facecolor='none',
        edgecolor='#1f77b4',
        linewidth=3,
        linestyle='--',
        label='ZMM'
    )
    
    # Dibujar zonas rurales con borde rojo y relleno naranja semi-transparente
    rural_gdf_3857.plot(
        ax=ax,
        facecolor='#ff7f0e',
        alpha=0.3,
        edgecolor='#d62728',
        linewidth=2
    )
    
    # Añadir etiquetas de texto en los centros
    for _, row in zmm_gdf_3857.iterrows():
        cent = row['geometry'].centroid
        ax.text(
            cent.x, cent.y, "ZMM",
            color='#1f77b4', fontsize=12, fontweight='bold', ha='center', va='center',
            bbox=dict(facecolor='white', alpha=0.8, edgecolor='#1f77b4', boxstyle='round,pad=0.3')
        )
        
    for _, row in rural_gdf_3857.iterrows():
        cent = row['geometry'].centroid
        name_short = row['name'].split(" ")[0]
        ax.text(
            cent.x, cent.y, f"Control Rural\n{name_short}",
            color='#d62728', fontsize=10, fontweight='bold', ha='center', va='center',
            bbox=dict(facecolor='white', alpha=0.8, edgecolor='#d62728', boxstyle='round,pad=0.3')
        )
        
    # Ajustar límites de la vista
    # Envolver todo para encuadre
    combined_envelope = gpd.GeoSeries(list(rural_zones.values()) + [zmm_poly]).union_all().envelope
    envelope_gdf = gpd.GeoDataFrame(geometry=[combined_envelope], crs="EPSG:4326").to_crs(epsg=3857)
    e_minx, e_miny, e_maxx, e_maxy = envelope_gdf.unary_union.bounds
    
    # Calcular rangos y centros en metros (Web Mercator)
    x_center = (e_minx + e_maxx) / 2
    y_center = (e_miny + e_maxy) / 2
    y_range = e_maxy - e_miny
    
    # Forzar relación de aspecto 16:10 expandiendo el rango X
    # Añadimos un 15% de padding vertical
    y_range_padded = y_range * 1.15
    x_range_forced = y_range_padded * (16 / 10)
    
    l_minx = x_center - (x_range_forced / 2)
    l_maxx = x_center + (x_range_forced / 2)
    l_miny = y_center - (y_range_padded / 2)
    l_maxy = y_center + (y_range_padded / 2)
    
    ax.set_xlim(l_minx, l_maxx)
    ax.set_ylim(l_miny, l_maxy)
    
    # Usar un basemap topográfico/carretero regional
    ctx.add_basemap(ax, source=ctx.providers.Esri.WorldTopoMap)
    
    ax.set_title("Zonas de Control Rural de Referencia (EPA Methodology)", fontsize=18, fontweight='bold', pad=15, color='#263238')
    ax.set_axis_off()
    
    # Añadir leyenda manual
    legend_patches = [
        mpatches.Patch(facecolor='none', edgecolor='#1f77b4', linewidth=3, linestyle='--', label='Área de Estudio (ZMM)'),
        mpatches.Patch(facecolor='#ff7f0e', alpha=0.3, edgecolor='#d62728', linewidth=2, label='Zonas Rurales de Control')
    ]
    ax.legend(handles=legend_patches, loc='lower right', facecolor='#fafafa', edgecolor='#b0bec5', fontsize=10)
    
    fig_rural_map_path = outputs_dir / "rural_reference_zones_map.png"
    plt.savefig(fig_rural_map_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"      Mapa regional de zonas rurales guardado en: {fig_rural_map_path}")
    print("=" * 80)
    print("PROCESO DE REGENERACIÓN FINALIZADO CON ÉXITO")
    print("=" * 80)

if __name__ == "__main__":
    main()
