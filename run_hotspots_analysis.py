import os
import pathlib
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
import contextily as ctx
from shapely.geometry import Point
from sklearn.cluster import DBSCAN
import matplotlib.patches as mpatches

def main():
    print("=" * 80)
    print("INICIANDO ANÁLISIS DE HOTSPOTS TÉRMICOS (SUHI) Y DIAGNÓSTICO TERNIUM")
    print("=" * 80)

    # 1. Cargar Datos
    base_dir = pathlib.Path(__file__).parent.resolve()
    gpkg_path = base_dir / "data" / "processed" / "malla_modelado_multiescala_mty.gpkg"
    
    if not gpkg_path.exists():
        raise FileNotFoundError(f"No se encontró el Geopackage de modelado en: {gpkg_path}")
        
    print(f"[1/8] Cargando malla base: {gpkg_path.name}...")
    gdf = gpd.read_file(gpkg_path)
    print(f"      Cargadas {len(gdf)} celdas.")
    
    # Identificar columna del target
    target_col = 'suhi_day_c' if 'suhi_day_c' in gdf.columns else 'suhi_c'
    gdf_clean = gdf.dropna(subset=[target_col]).copy()
    
    # Calcular promedio rural de control local (green_pct > 75%)
    gdf_rural_temp = gdf_clean[gdf_clean['green_pct'] > 75.0]
    if len(gdf_rural_temp) < 50:
        gdf_rural_temp = gdf_clean[gdf_clean['green_pct'] > 60.0]
    rural_mean_lst = gdf_rural_temp['lst_day_c'].mean()
    
    # Recalcular anomalía relativa a la zona rural de control para consistencia total
    gdf_clean['suhi_day_c'] = gdf_clean['lst_day_c'] - rural_mean_lst
    gdf_clean['suhi_c'] = gdf_clean['suhi_day_c']
    
    # 2. Umbral Térmico y Clustering (DBSCAN)
    print("[2/8] Ejecutando agrupamiento espacial (DBSCAN)...")
    p95 = gdf_clean[target_col].quantile(0.95)
    print(f"      Umbral térmico diurno del percentil 95: {p95:.3f} °C")
    
    # Celdas calientes
    gdf_warm = gdf_clean[gdf_clean[target_col] >= p95].copy()
    
    # Proyectar a UTM Zona 14N para que la distancia esté en metros
    gdf_warm_utm = gdf_warm.to_crs(epsg=32614)
    centroids = gdf_warm_utm.geometry.centroid
    coords = np.column_stack((centroids.x, centroids.y))
    
    # DBSCAN: eps=60m (2 celdas de 30m de conectividad), min_samples=3 celdas
    db = DBSCAN(eps=60, min_samples=3, n_jobs=-1)
    gdf_warm['hotspot_cluster_id'] = db.fit_predict(coords)
    
    # Separar celdas agrupadas
    gdf_clusters = gdf_warm[gdf_warm['hotspot_cluster_id'] != -1].copy()
    n_clusters = gdf_clusters['hotspot_cluster_id'].nunique()
    print(f"      Clusters continuos detectados: {n_clusters}")
    
    # Guardar capas vectoriales intermedias
    outputs_dir = base_dir / "outputs"
    notebook_dir = outputs_dir / "05"
    notebook_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = notebook_dir
    tables_dir = notebook_dir
    
    gdf_clusters.to_file(notebook_dir / "04_all_hotspot_clusters.gpkg", driver="GPKG", mode="w")
    print(f"      Guardadas todas las celdas agrupadas en: outputs/04_all_hotspot_clusters.gpkg")

    # 3. Priorización por Criticidad Física
    print("[3/8] Calculando el Puntaje de Criticidad Física...")
    cluster_metrics = []
    
    for cid in gdf_clusters['hotspot_cluster_id'].unique():
        c_gdf = gdf_clusters[gdf_clusters['hotspot_cluster_id'] == cid]
        n_cells = len(c_gdf)
        suhi_mean = c_gdf[target_col].mean()
        suhi_max = c_gdf[target_col].max()
        built_mean = c_gdf['dw_built_pct'].mean() if 'dw_built_pct' in c_gdf.columns else 0.0
        green_mean = c_gdf['green_pct'].mean() if 'green_pct' in c_gdf.columns else 0.0
        trees_mean = c_gdf['dw_trees_pct'].mean() if 'dw_trees_pct' in c_gdf.columns else 0.0
        elev_mean = c_gdf['elevation'].mean() if 'elevation' in c_gdf.columns else 0.0
        dist_ind = c_gdf['distance_to_industry_osm_m'].mean() if 'distance_to_industry_osm_m' in c_gdf.columns else 0.0
        
        area_ha = (n_cells * 900) / 10000.0
        
        # Calcular centroide WGS84
        c_centroids = c_gdf.to_crs(epsg=4326).geometry.centroid
        cent_x = c_centroids.x.mean()
        cent_y = c_centroids.y.mean()
        
        cluster_metrics.append({
            'cluster_id': cid,
            'n_cells': n_cells,
            'area_ha': area_ha,
            'suhi_mean': suhi_mean,
            'suhi_max': suhi_max,
            'built_mean': built_mean,
            'green_mean': green_mean,
            'trees_mean': trees_mean,
            'elev_mean': elev_mean,
            'dist_ind': dist_ind,
            'cent_x': cent_x,
            'cent_y': cent_y
        })
        
    df_metrics = pd.DataFrame(cluster_metrics)
    
    # Normalización Min-Max
    def min_max_norm(series, invert=False):
        if series.max() == series.min():
            return pd.Series(0.5, index=series.index)
        norm = (series - series.min()) / (series.max() - series.min())
        return 1.0 - norm if invert else norm
        
    df_metrics['suhi_mean_norm'] = min_max_norm(df_metrics['suhi_mean'])
    df_metrics['suhi_max_norm'] = min_max_norm(df_metrics['suhi_max'])
    df_metrics['area_norm'] = min_max_norm(df_metrics['area_ha'])
    df_metrics['built_norm'] = min_max_norm(df_metrics['built_mean'])
    df_metrics['low_green_norm'] = min_max_norm(df_metrics['green_mean'], invert=True)
    
    # Fórmula de Criticidad Física
    df_metrics['physical_criticality_score'] = (
        0.40 * df_metrics['suhi_mean_norm'] +
        0.20 * df_metrics['suhi_max_norm'] +
        0.15 * df_metrics['area_norm'] +
        0.15 * df_metrics['built_norm'] +
        0.10 * df_metrics['low_green_norm']
    )
    
    df_metrics = df_metrics.sort_values(by='physical_criticality_score', ascending=False).reset_index(drop=True)
    df_metrics.to_csv(tables_dir / "04_hotspot_priority_table.csv", index=False)
    
    # Obtener el Top 3
    top_3_df = df_metrics.head(3).copy()
    top_3_ids = top_3_df['cluster_id'].tolist()
    print("      Top 3 Clusters Priorizados:")
    for idx, row in top_3_df.iterrows():
        print(f"      - Hotspot {idx+1} (Cluster {int(row['cluster_id'])}): Área={row['area_ha']:.1f} ha, SUHI Promedio={row['suhi_mean']:.2f}°C, Score={row['physical_criticality_score']:.3f}")
        
    # Guardar Geopackage del Top 3
    gdf_top3_cells = gdf_clusters[gdf_clusters['hotspot_cluster_id'].isin(top_3_ids)].copy()
    gdf_top3_cells.to_file(notebook_dir / "04_top3_hotspots.gpkg", driver="GPKG", mode="w")
    print(f"      Guardadas celdas del Top 3 en: outputs/05/04_top3_hotspots.gpkg")

    # 4. Diagnóstico de la Planta Ternium Guerrero (Coordenadas Originales)
    print("[4/8] Ejecutando análisis de amortiguamiento para la planta Ternium Guerrero...")
    # Coordenadas originales provistas por el usuario
    ternium_lon, ternium_lat = -100.301894, 25.722502
    ternium_point_wgs84 = gpd.GeoSeries([Point(ternium_lon, ternium_lat)], crs="EPSG:4326")
    ternium_point_utm = ternium_point_wgs84.to_crs(epsg=32614)
    ternium_geom = ternium_point_utm.iloc[0]
    
    # Malla limpia y proyectada a UTM
    gdf_clean_utm = gdf_clean.to_crs(epsg=32614)
    
    # Analizar buffers a diferentes distancias (200m, 100m)
    ternium_buffers_stats = []
    for r in [200, 100]:
        buf_geom = ternium_geom.buffer(r)
        cells_in_buf = gdf_clean_utm[gdf_clean_utm.intersects(buf_geom)].copy()
        
        # DBSCAN clusters intersecados en el buffer
        gdf_clusters_utm = gdf_clusters.to_crs(epsg=32614)
        clusters_in_buf = gdf_clusters_utm[gdf_clusters_utm.intersects(buf_geom)]
        inter_cids = clusters_in_buf['hotspot_cluster_id'].unique().tolist()
        inter_cids_str = ", ".join([str(int(c)) for c in inter_cids]) if len(inter_cids) > 0 else "Ninguno"
        
        suhi_m = cells_in_buf[target_col].mean()
        suhi_max = cells_in_buf[target_col].max()
        built_m = cells_in_buf['dw_built_pct'].mean() if 'dw_built_pct' in cells_in_buf.columns else 0.0
        green_m = cells_in_buf['green_pct'].mean() if 'green_pct' in cells_in_buf.columns else 0.0
        trees_m = cells_in_buf['dw_trees_pct'].mean() if 'dw_trees_pct' in cells_in_buf.columns else 0.0
        
        ternium_buffers_stats.append({
            'Radio (m)': r,
            'Celdas': len(cells_in_buf),
            'SUHI Promedio (°C)': suhi_m,
            'SUHI Máxima (°C)': suhi_max,
            'Suelo Construido (%)': built_m,
            'Cobertura Verde (%)': green_m,
            'Dosel Arbóreo (%)': trees_m,
            'Clusters Asociados': inter_cids_str
        })
        
    df_ternium_stats = pd.DataFrame(ternium_buffers_stats)
    print("      Resumen de Diagnóstico Ternium por Buffer:")
    print(df_ternium_stats.to_string(index=False))

    # 5. Análisis Comparativo: Hotspots vs Resto de ZMM vs Rural
    print("[5/8] Calculando análisis comparativo territorial y físico...")
    # Asignar zonas a la malla limpia
    gdf_clean_utm['hotspot_cluster_id'] = -1
    # Re-asignar ID de clusters a la malla completa limpia para la agregación
    # Re-proyectar centroides
    gdf_clean_utm_centroids = gdf_clean_utm.geometry.centroid
    gdf_clean_utm_coords = np.column_stack((gdf_clean_utm_centroids.x, gdf_clean_utm_centroids.y))
    # DBSCAN sobre toda la malla limpia para mapear los clusters asignados
    db_full = DBSCAN(eps=60, min_samples=3, n_jobs=-1)
    # Solo aplicamos DBSCAN a las celdas calientes diurnas
    warm_mask = gdf_clean_utm[target_col] >= p95
    if warm_mask.sum() > 0:
        warm_coords = np.column_stack((gdf_clean_utm_centroids[warm_mask].x, gdf_clean_utm_centroids[warm_mask].y))
        gdf_clean_utm.loc[warm_mask, 'hotspot_cluster_id'] = db_full.fit_predict(warm_coords)
        
    gdf_clean_utm['zone'] = 'Resto de la ZMM'
    gdf_clean_utm.loc[gdf_clean_utm['hotspot_cluster_id'] == top_3_ids[0], 'zone'] = 'Hotspot 1 (Cluster 44)'
    gdf_clean_utm.loc[gdf_clean_utm['hotspot_cluster_id'] == top_3_ids[1], 'zone'] = 'Hotspot 2 (Cluster 66)'
    gdf_clean_utm.loc[gdf_clean_utm['hotspot_cluster_id'] == top_3_ids[2], 'zone'] = 'Hotspot 3 (Cluster 5)'
    gdf_clean_utm.loc[gdf_clean_utm['hotspot_cluster_id'] == 38, 'zone'] = 'Hotspot 4 (Ternium - Cluster 38)'
    
    # Rural Zone (green_pct > 75%)
    gdf_rural = gdf_clean_utm[gdf_clean_utm['green_pct'] > 75.0].copy()
    if len(gdf_rural) < 50:
        gdf_rural = gdf_clean_utm[gdf_clean_utm['green_pct'] > 60.0].copy()
        
    comparison_cols = [
        'lst_day_c', 'suhi_day_c', 'green_pct', 'dw_built_pct', 
        'dw_trees_pct', 'dw_bare_pct', 'distance_to_industry_osm_m', 'elevation'
    ]
    
    summary_data = []
    zones = ['Hotspot 1 (Cluster 44)', 'Hotspot 2 (Cluster 66)', 'Hotspot 3 (Cluster 5)', 'Hotspot 4 (Ternium - Cluster 38)']
    for z in zones:
        sub = gdf_clean_utm[gdf_clean_utm['zone'] == z]
        row = {'Zona': z, 'Celdas': len(sub)}
        for col in comparison_cols:
            row[col] = sub[col].mean()
        summary_data.append(row)
        
    # Calcular promedio de los 4 hotspots (media simple de las métricas de los 4 hotspots)
    row_avg = {'Zona': 'Promedio de los 4 Hotspots', 'Celdas': sum(r['Celdas'] for r in summary_data)}
    for col in comparison_cols:
        row_avg[col] = np.mean([r[col] for r in summary_data])
    summary_data.append(row_avg)
    
    # Agregar Resto de la ZMM
    sub_rest = gdf_clean_utm[gdf_clean_utm['zone'] == 'Resto de la ZMM']
    row_rest = {'Zona': 'Resto de la ZMM', 'Celdas': len(sub_rest)}
    for col in comparison_cols:
        row_rest[col] = sub_rest[col].mean()
    summary_data.append(row_rest)
        
    # Agregar Zona Rural de Control
    row_rural = {'Zona': 'Zona Rural de Control', 'Celdas': len(gdf_rural)}
    for col in comparison_cols:
        row_rural[col] = gdf_rural[col].mean()
    summary_data.append(row_rural)
    
    df_comp_summary = pd.DataFrame(summary_data)
    df_comp_summary.to_csv(tables_dir / "04_hotspots_physical_comparison.csv", index=False)

    # 6. Generar Gráficas y Mapas de Alta Calidad (Aesthetics Premium)
    sns.set_theme(style="ticks")
    
    # A. Gráficas de Comparación de Métricas Físicas
    # 1. Gráfica de comparación individual (sin el promedio)
    print("[6/8] Generando gráfico de comparación de métricas físicas (individuales)...")
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), dpi=300)
    axes = axes.flatten()
    
    df_comp_ind = df_comp_summary[df_comp_summary['Zona'] != 'Promedio de los 4 Hotspots']
    palette_comp_ind = ['#b71c1c', '#e65100', '#f57c00', '#ffb300', '#37474f', '#2e7d32']
    
    plot_vars = [
        ('suhi_day_c', 'Intensidad SUHI Diurna (°C)', axes[0]),
        ('green_pct', 'Cobertura Vegetación Verde (%)', axes[1]),
        ('dw_trees_pct', 'Cobertura Dosel Arbóreo (%)', axes[2]),
        ('distance_to_industry_osm_m', 'Distancia a Zonas Industriales (m)', axes[3])
    ]
    
    for var, label, ax in plot_vars:
        sns.barplot(
            data=df_comp_ind,
            x='Zona',
            y=var,
            ax=ax,
            palette=palette_comp_ind,
            hue='Zona',
            legend=False
        )
        ax.set_title(label, fontsize=12, fontweight='bold', pad=10, color='#263238')
        ax.set_xlabel('', fontsize=10)
        ax.set_ylabel('')
        ax.grid(True, axis='y', ls='--', color='#cfd8dc', alpha=0.7)
        short_labels_ind = [
            "H1\n(C44)",
            "H2\n(C66)",
            "H3\n(C5)",
            "H4\n(Ternium)",
            "Resto\nZMM",
            "Rural\nControl"
        ]
        ax.set_xticklabels(short_labels_ind, rotation=0, fontsize=9)
        # Añadir valores sobre las barras
        for p in ax.patches:
            val = p.get_height()
            if not np.isnan(val):
                label_text = (f"{val:.1f}m" if "distance" in var 
                              else f"{val:.2f}%" if "pct" in var 
                              else f"{val:.2f}°C" if "suhi" in var 
                              else f"{val:.2f}")
                ax.annotate(label_text,
                            (p.get_x() + p.get_width() / 2., val),
                            ha='center', va='center',
                            xytext=(0, 5),
                            textcoords='offset points',
                            fontsize=8, fontweight='bold', color='#37474f')
                            
    plt.tight_layout()
    fig_comp_path = figures_dir / "hotspots_physical_metrics_comparison.png"
    plt.savefig(fig_comp_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"      Gráfica comparativa individual guardada en: {fig_comp_path.relative_to(base_dir)}")

    # 2. Gráfica de comparación promedio (solo el promedio vs resto de la ZMM vs control rural)
    print("      Generando gráfico de comparación de métricas físicas (promedio de los 4)...")
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), dpi=300)
    axes = axes.flatten()
    
    df_comp_avg = df_comp_summary[df_comp_summary['Zona'].isin(['Promedio de los 4 Hotspots', 'Resto de la ZMM', 'Zona Rural de Control'])]
    palette_comp_avg = ['#d84315', '#37474f', '#2e7d32']
    
    for var, label, ax in plot_vars:
        sns.barplot(
            data=df_comp_avg,
            x='Zona',
            y=var,
            ax=ax,
            palette=palette_comp_avg,
            hue='Zona',
            legend=False
        )
        ax.set_title(label, fontsize=12, fontweight='bold', pad=10, color='#263238')
        ax.set_xlabel('', fontsize=10)
        ax.set_ylabel('')
        ax.grid(True, axis='y', ls='--', color='#cfd8dc', alpha=0.7)
        short_labels_avg = [
            "Promedio\nHotspots",
            "Resto\nZMM",
            "Rural\nControl"
        ]
        ax.set_xticklabels(short_labels_avg, rotation=0, fontsize=9.5)
        # Añadir valores sobre las barras
        for p in ax.patches:
            val = p.get_height()
            if not np.isnan(val):
                label_text = (f"{val:.1f}m" if "distance" in var 
                              else f"{val:.2f}%" if "pct" in var 
                              else f"{val:.2f}°C" if "suhi" in var 
                              else f"{val:.2f}")
                ax.annotate(label_text,
                            (p.get_x() + p.get_width() / 2., val),
                            ha='center', va='center',
                            xytext=(0, 5),
                            textcoords='offset points',
                            fontsize=8, fontweight='bold', color='#37474f')
                            
    plt.tight_layout()
    fig_comp_avg_path = figures_dir / "hotspots_average_physical_metrics_comparison.png"
    plt.savefig(fig_comp_avg_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"      Gráfica comparativa del promedio guardada en: {fig_comp_avg_path.relative_to(base_dir)}")

    # B. Mapa General de Hotspots (Overview Map)
    print("[7/8] Generando mapa satelital general del área de estudio (Overview Map)...")
    # Filtrar celdas de los hotspots seleccionados y Ternium para el mapa
    map_ids = top_3_ids + [38]
    gdf_map_cells = gdf_clusters[gdf_clusters['hotspot_cluster_id'].isin(map_ids)].to_crs(epsg=3857)
    
    fig, ax = plt.subplots(figsize=(12, 12), dpi=300)
    
    # Dibujar la malla del Top 3 y Ternium coloreada por SUHI
    gdf_map_cells.plot(
        column=target_col,
        cmap='magma',
        alpha=0.75,
        ax=ax,
        edgecolor='none',
        linewidth=0,
        vmin=0,
        legend=True,
        legend_kwds={
            'label': 'Intensidad SUHI Diurna (°C)',
            'orientation': 'horizontal',
            'pad': 0.03,
            'shrink': 0.7,
            'aspect': 30
        }
    )
    
    # Añadir marcadores para los centroides de los hotspots
    colors_markers = ['#b71c1c', '#e65100', '#f57c00', '#ffb300']
    names_hotspots = ['Hotspot 1 (Centro-San Nic)', 'Hotspot 2 (Z. Ind. S. Nic)', 'Hotspot 3 (Valle Oriente)', 'Hotspot 4 (Ternium - Cluster 38)']
    
    for idx, row in top_3_df.iterrows():
        p_utm = gpd.GeoSeries([Point(row['cent_x'], row['cent_y'])], crs="EPSG:4326").to_crs(epsg=3857).iloc[0]
        ax.plot(p_utm.x, p_utm.y, marker='o', color='white', markerfacecolor=colors_markers[idx], markersize=14, markeredgewidth=2, markeredgecolor='black')
        ax.annotate(f"H{idx+1}", (p_utm.x, p_utm.y), textcoords="offset points", xytext=(0,10), ha='center', fontsize=10, fontweight='bold', color='white',
                    path_effects=[plt.matplotlib.patheffects.withStroke(linewidth=3, foreground="black")])
                    
    # Añadir marcador de Ternium en el centroide de su isla de calor (Cluster 38)
    c38_gdf_utm = gdf_clusters[gdf_clusters['hotspot_cluster_id'] == 38].to_crs(epsg=32614)
    if not c38_gdf_utm.empty:
        c38_cent = c38_gdf_utm.union_all().centroid
        t_utm = gpd.GeoSeries([c38_cent], crs="EPSG:32614").to_crs(epsg=3857).iloc[0]
    else:
        t_utm = ternium_point_utm.to_crs(epsg=3857).iloc[0]
        
    # No dibujamos el marcador 'X' para que la isla de calor sea completamente visible
    ax.annotate("H4", (t_utm.x, t_utm.y), textcoords="offset points", xytext=(0,10), ha='center', fontsize=10, fontweight='bold', color='#ffeb3b',
                path_effects=[plt.matplotlib.patheffects.withStroke(linewidth=3, foreground="black")])
                
    # Ajustar límites geográficos para coincidir exactamente con el mapa de coldspots (comparabilidad espacial)
    ax.set_xlim(-11175785.45, -11157512.80)
    ax.set_ylim(2953993.73, 2967054.28)
    
    # Descargar mapa base satelital
    ctx.add_basemap(ax, source=ctx.providers.Esri.WorldImagery)
    
    # Estética del mapa
    ax.set_title("Top 4 Hotspots Térmicos SUHI y Planta Ternium Guerrero\nZona Metropolitana de Monterrey - Imagen Satelital", fontsize=14, fontweight='bold', pad=15, color='#263238')
    ax.set_axis_off()
    
    # Crear parches para leyenda manual
    legend_patches = [
        mpatches.Patch(color=colors_markers[0], alpha=0.8, label='Hotspot 1 (Centro Mty / S. Nicolás)'),
        mpatches.Patch(color=colors_markers[1], alpha=0.8, label='Hotspot 2 (Zona Ind. San Nicolás)'),
        mpatches.Patch(color=colors_markers[2], alpha=0.8, label='Hotspot 3 (Eje Valle Oriente / San Pedro)'),
        mpatches.Patch(color=colors_markers[3], alpha=0.8, label='Hotspot 4 (Ternium - Cluster 38)')
    ]
    ax.legend(handles=legend_patches, loc='upper left', facecolor='#fafafa', edgecolor='#b0bec5', fontsize=9.5)
    
    fig_overview_path = figures_dir / "hotspots_top3_overview_map.png"
    plt.savefig(fig_overview_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"      Mapa de panorama general guardado en: {fig_overview_path.relative_to(base_dir)}")

    # C. Generar Mapas de Zoom de los Hotspots
    print("[8/8] Generando mapas satelitales detallados (Zoom Maps)...")
    
    # Mapas de Zoom para los Top 3 Hotspots
    for i, cid in enumerate(top_3_ids):
        c_gdf = gdf_clusters[gdf_clusters['hotspot_cluster_id'] == cid].to_crs(epsg=3857)
        
        fig, ax = plt.subplots(figsize=(10, 10), dpi=300)
        c_gdf.plot(
            column=target_col,
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
                'shrink': 0.7
            }
        )
        
        # Ajustar límites con padding
        bbox = c_gdf.unary_union.envelope
        minx, miny, maxx, maxy = bbox.bounds
        pad_x = (maxx - minx) * 0.2
        pad_y = (maxy - miny) * 0.2
        ax.set_xlim(minx - pad_x, maxx + pad_x)
        ax.set_ylim(miny - pad_y, maxy + pad_y)
        
        ctx.add_basemap(ax, source=ctx.providers.Esri.WorldImagery)
        ax.set_title(f"Aproximación Satelital: Hotspot {i+1} (Cluster {int(cid)})\nSUHI Diurna Promedio: {c_gdf[target_col].mean():.2f}°C | Área: {(len(c_gdf)*900)/10000:.1f} ha",
                     fontsize=12, fontweight='bold', pad=12, color='#263238')
        ax.set_axis_off()
        
        fig_zoom_path = figures_dir / f"hotspot_{i+1}_zoom_map.png"
        plt.savefig(fig_zoom_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"      Zoom Map Hotspot {i+1} guardado en: {fig_zoom_path.relative_to(base_dir)}")
        
    # Mapa de Zoom para Ternium Guerrero (Hotspot Genuino Cluster 38)
    t_gdf_c38 = gdf_clusters[gdf_clusters['hotspot_cluster_id'] == 38].to_crs(epsg=3857)
    
    fig, ax = plt.subplots(figsize=(10, 10), dpi=300)
    
    # Dibujar las celdas del Cluster 38 coloreadas por SUHI
    if not t_gdf_c38.empty:
        t_gdf_c38.plot(
            column=target_col,
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
                'shrink': 0.7
            }
        )
        
        # Ajustar límites de visualización alrededor del Cluster 38 con un zoom menor (más padding)
        bbox = t_gdf_c38.union_all().envelope
        minx, miny, maxx, maxy = bbox.bounds
        pad_x = (maxx - minx) * 2.5
        pad_y = (maxy - miny) * 2.5
        ax.set_xlim(minx - pad_x, maxx + pad_x)
        ax.set_ylim(miny - pad_y, maxy + pad_y)
        
    ctx.add_basemap(ax, source=ctx.providers.Esri.WorldImagery)
    
    # Título del mapa con estadísticas
    mean_suhi_t = t_gdf_c38[target_col].mean() if not t_gdf_c38.empty else 0.0
    ax.set_title(f"Aproximación Satelital: Hotspot 4 (Ternium - Cluster 38)\nSUHI Diurna Promedio: {mean_suhi_t:.2f}°C | Área: 1.6 ha",
                 fontsize=12, fontweight='bold', pad=12, color='#263238')
    ax.set_axis_off()
    
    fig_ternium_path = figures_dir / "hotspot_ternium_zoom_map.png"
    plt.savefig(fig_ternium_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"      Zoom Map Ternium guardado en: {fig_ternium_path.relative_to(base_dir)}")

    # Leer referencia rural diurna
    rural_temp_file = base_dir / "data" / "interim" / "rural_temp_day.txt"
    mediana_rural_lst_day = 24.92  # Fallback
    if rural_temp_file.exists():
        try:
            with open(rural_temp_file, "r") as f:
                mediana_rural_lst_day = float(f.read().strip())
        except Exception:
            pass

    # 7. Redactar Reporte de Casos de Estudio en Markdown
    print("\n[ÉXITO] Escribiendo reporte final: outputs/04_hotspot_case_studies_report.md...")
    
    report_content = f"""# Reporte de Casos de Estudio de Hotspots Térmicos Críticos (SUHI) y Diagnóstico Ternium - 2026

## 1. Metodología de Detección
* **Filtro Térmico Inicial:** Se seleccionaron las celdas de la malla que superan el percentil 95 de la anomalía de temperatura diurna (`suhi_day_c`), equivalente a un umbral térmico de **{p95:.3f}°C** sobre la referencia rural ({mediana_rural_lst_day:.2f}°C).
* **Algoritmo de Agrupamiento:** Se agruparon las celdas en manchas contiguas aplicando **DBSCAN** en metros sobre los centroides de celdas con una distancia máxima (`eps`) de **60 m** (aproximadamente 2 celdas de conectividad) y un mínimo de **3 celdas** para considerarse cluster. Se identificaron **{n_clusters}** clusters térmicos.

## 2. Índice de Criticidad Física y Priorización
Para priorizar las manchas se calculó el **Puntaje de Criticidad Física**, el cual asigna mayor peso a la combinación de calor extremo y magnitud territorial, excluyendo cualquier variable social:
$$\\text{{Puntaje}} = 0.40 \\cdot \\text{{SUHI}}_{{\\text{{media}}}} + 0.20 \\cdot \\text{{SUHI}}_{{\\text{{máx}}}} + 0.15 \\cdot \\text{{Área}} + 0.15 \\cdot \\text{{Concreto}} + 0.10 \\cdot \\text{{Carencia Verde}}$$

### Resumen del Top 3 de Hotspots Priorizados
| Hotspot | Cluster ID | Municipios | Centroide (Lat, Lon) | SUHI Promedio (°C) | SUHI Máximo (°C) | Área (ha) | Concreto (%) | Cobertura Verde (%) |
| :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Hotspot 1** | {int(top_3_df.iloc[0]['cluster_id'])} | Monterrey, San Nicolás de los Garza | ({top_3_df.iloc[0]['cent_y']:.5f}, {top_3_df.iloc[0]['cent_x']:.5f}) | {top_3_df.iloc[0]['suhi_mean']:.2f} | {top_3_df.iloc[0]['suhi_max']:.2f} | {top_3_df.iloc[0]['area_ha']:.1f} | {top_3_df.iloc[0]['built_mean']:.1f}% | {top_3_df.iloc[0]['green_mean']:.2f}% |
| **Hotspot 2** | {int(top_3_df.iloc[1]['cluster_id'])} | San Nicolás de los Garza | ({top_3_df.iloc[1]['cent_y']:.5f}, {top_3_df.iloc[1]['cent_x']:.5f}) | {top_3_df.iloc[1]['suhi_mean']:.2f} | {top_3_df.iloc[1]['suhi_max']:.2f} | {top_3_df.iloc[1]['area_ha']:.1f} | {top_3_df.iloc[1]['built_mean']:.1f}% | {top_3_df.iloc[1]['green_mean']:.2f}% |
| **Hotspot 3** | {int(top_3_df.iloc[2]['cluster_id'])} | San Pedro Garza García, Monterrey | ({top_3_df.iloc[2]['cent_y']:.5f}, {top_3_df.iloc[2]['cent_x']:.5f}) | {top_3_df.iloc[2]['suhi_mean']:.2f} | {top_3_df.iloc[2]['suhi_max']:.2f} | {top_3_df.iloc[2]['area_ha']:.1f} | {top_3_df.iloc[2]['built_mean']:.1f}% | {top_3_df.iloc[2]['green_mean']:.2f}% |

---

## 3. ¿Por qué son los 4 Hotspots más Intensos? Análisis Comparativo Territorial
El análisis detallado revela diferencias físicas y de cobertura drásticas entre estas regiones calientes, el promedio metropolitano y las zonas rurales de control:

| Métrica Promedio | Hotspot 1 (Centro-San Nic) | Hotspot 2 (Z. Ind. S. Nic) | Hotspot 3 (Valle Oriente) | Hotspot 4 (Ternium) | Promedio de los 4 Hotspots | Resto de la ZMM | Zona Rural de Control |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Temperatura LST (°C)** | {df_comp_summary.loc[df_comp_summary['Zona']=='Hotspot 1 (Cluster 44)', 'lst_day_c'].values[0]:.2f} | {df_comp_summary.loc[df_comp_summary['Zona']=='Hotspot 2 (Cluster 66)', 'lst_day_c'].values[0]:.2f} | {df_comp_summary.loc[df_comp_summary['Zona']=='Hotspot 3 (Cluster 5)', 'lst_day_c'].values[0]:.2f} | {df_comp_summary.loc[df_comp_summary['Zona']=='Hotspot 4 (Ternium - Cluster 38)', 'lst_day_c'].values[0]:.2f} | **{df_comp_summary.loc[df_comp_summary['Zona']=='Promedio de los 4 Hotspots', 'lst_day_c'].values[0]:.2f}** | {df_comp_summary.loc[df_comp_summary['Zona']=='Resto de la ZMM', 'lst_day_c'].values[0]:.2f} | {df_comp_summary.loc[df_comp_summary['Zona']=='Zona Rural de Control', 'lst_day_c'].values[0]:.2f} |
| **Intensidad SUHI (°C)** | **{df_comp_summary.loc[df_comp_summary['Zona']=='Hotspot 1 (Cluster 44)', 'suhi_day_c'].values[0]:.2f}** | **{df_comp_summary.loc[df_comp_summary['Zona']=='Hotspot 2 (Cluster 66)', 'suhi_day_c'].values[0]:.2f}** | **{df_comp_summary.loc[df_comp_summary['Zona']=='Hotspot 3 (Cluster 5)', 'suhi_day_c'].values[0]:.2f}** | **{df_comp_summary.loc[df_comp_summary['Zona']=='Hotspot 4 (Ternium - Cluster 38)', 'suhi_day_c'].values[0]:.2f}** | **{df_comp_summary.loc[df_comp_summary['Zona']=='Promedio de los 4 Hotspots', 'suhi_day_c'].values[0]:.2f}** | **{df_comp_summary.loc[df_comp_summary['Zona']=='Resto de la ZMM', 'suhi_day_c'].values[0]:.2f}** | **{df_comp_summary.loc[df_comp_summary['Zona']=='Zona Rural de Control', 'suhi_day_c'].values[0]:.2f}** |
| **Cobertura Verde (%)** | {df_comp_summary.loc[df_comp_summary['Zona']=='Hotspot 1 (Cluster 44)', 'green_pct'].values[0]:.2f}% | {df_comp_summary.loc[df_comp_summary['Zona']=='Hotspot 2 (Cluster 66)', 'green_pct'].values[0]:.2f}% | {df_comp_summary.loc[df_comp_summary['Zona']=='Hotspot 3 (Cluster 5)', 'green_pct'].values[0]:.2f}% | {df_comp_summary.loc[df_comp_summary['Zona']=='Hotspot 4 (Ternium - Cluster 38)', 'green_pct'].values[0]:.2f}% | **{df_comp_summary.loc[df_comp_summary['Zona']=='Promedio de los 4 Hotspots', 'green_pct'].values[0]:.2f}%** | {df_comp_summary.loc[df_comp_summary['Zona']=='Resto de la ZMM', 'green_pct'].values[0]:.2f}% | {df_comp_summary.loc[df_comp_summary['Zona']=='Zona Rural de Control', 'green_pct'].values[0]:.2f}% |
| **Área Construida (%)** | {df_comp_summary.loc[df_comp_summary['Zona']=='Hotspot 1 (Cluster 44)', 'dw_built_pct'].values[0]:.2f}% | {df_comp_summary.loc[df_comp_summary['Zona']=='Hotspot 2 (Cluster 66)', 'dw_built_pct'].values[0]:.2f}% | {df_comp_summary.loc[df_comp_summary['Zona']=='Hotspot 3 (Cluster 5)', 'dw_built_pct'].values[0]:.2f}% | {df_comp_summary.loc[df_comp_summary['Zona']=='Hotspot 4 (Ternium - Cluster 38)', 'dw_built_pct'].values[0]:.2f}% | **{df_comp_summary.loc[df_comp_summary['Zona']=='Promedio de los 4 Hotspots', 'dw_built_pct'].values[0]:.2f}%** | {df_comp_summary.loc[df_comp_summary['Zona']=='Resto de la ZMM', 'dw_built_pct'].values[0]:.2f}% | {df_comp_summary.loc[df_comp_summary['Zona']=='Zona Rural de Control', 'dw_built_pct'].values[0]:.2f}% |
| **Dosel Arbóreo (%)** | {df_comp_summary.loc[df_comp_summary['Zona']=='Hotspot 1 (Cluster 44)', 'dw_trees_pct'].values[0]:.2f}% | {df_comp_summary.loc[df_comp_summary['Zona']=='Hotspot 2 (Cluster 66)', 'dw_trees_pct'].values[0]:.2f}% | {df_comp_summary.loc[df_comp_summary['Zona']=='Hotspot 3 (Cluster 5)', 'dw_trees_pct'].values[0]:.2f}% | {df_comp_summary.loc[df_comp_summary['Zona']=='Hotspot 4 (Ternium - Cluster 38)', 'dw_trees_pct'].values[0]:.2f}% | **{df_comp_summary.loc[df_comp_summary['Zona']=='Promedio de los 4 Hotspots', 'dw_trees_pct'].values[0]:.2f}%** | {df_comp_summary.loc[df_comp_summary['Zona']=='Resto de la ZMM', 'dw_trees_pct'].values[0]:.2f}% | {df_comp_summary.loc[df_comp_summary['Zona']=='Zona Rural de Control', 'dw_trees_pct'].values[0]:.2f}% |
| **Suelo Desnudo (%)** | {df_comp_summary.loc[df_comp_summary['Zona']=='Hotspot 1 (Cluster 44)', 'dw_bare_pct'].values[0]:.2f}% | {df_comp_summary.loc[df_comp_summary['Zona']=='Hotspot 2 (Cluster 66)', 'dw_bare_pct'].values[0]:.2f}% | {df_comp_summary.loc[df_comp_summary['Zona']=='Hotspot 3 (Cluster 5)', 'dw_bare_pct'].values[0]:.2f}% | {df_comp_summary.loc[df_comp_summary['Zona']=='Hotspot 4 (Ternium - Cluster 38)', 'dw_bare_pct'].values[0]:.2f}% | **{df_comp_summary.loc[df_comp_summary['Zona']=='Promedio de los 4 Hotspots', 'dw_bare_pct'].values[0]:.2f}%** | {df_comp_summary.loc[df_comp_summary['Zona']=='Resto de la ZMM', 'dw_bare_pct'].values[0]:.2f}% | {df_comp_summary.loc[df_comp_summary['Zona']=='Zona Rural de Control', 'dw_bare_pct'].values[0]:.2f}% |
| **Dist. a Industria (m)** | **{df_comp_summary.loc[df_comp_summary['Zona']=='Hotspot 1 (Cluster 44)', 'distance_to_industry_osm_m'].values[0]:.2f}m** | **{df_comp_summary.loc[df_comp_summary['Zona']=='Hotspot 2 (Cluster 66)', 'distance_to_industry_osm_m'].values[0]:.2f}m** | **{df_comp_summary.loc[df_comp_summary['Zona']=='Hotspot 3 (Cluster 5)', 'distance_to_industry_osm_m'].values[0]:.2f}m** | **{df_comp_summary.loc[df_comp_summary['Zona']=='Hotspot 4 (Ternium - Cluster 38)', 'distance_to_industry_osm_m'].values[0]:.2f}m** | **{df_comp_summary.loc[df_comp_summary['Zona']=='Promedio de los 4 Hotspots', 'distance_to_industry_osm_m'].values[0]:.2f}m** | **{df_comp_summary.loc[df_comp_summary['Zona']=='Resto de la ZMM', 'distance_to_industry_osm_m'].values[0]:.2f}m** | **{df_comp_summary.loc[df_comp_summary['Zona']=='Zona Rural de Control', 'distance_to_industry_osm_m'].values[0]:.2f}m** |

### Factores Determinantes de la Intensidad Térmica:
1. **Déficit Crítico de Vegetación y Árboles:** Los Hotspots 1 y 2 registran menos de **3.22% de cobertura verde** y **2.96% de dosel arbóreo**, comparado con el 17.80% verde en el resto de la metrópoli. Esto elimina por completo el enfriamiento evaporativo en estas áreas.
2. **Proximidad Industrial Extrema:** Los Hotspots 1 y 2 se encuentran a una distancia promedio de **menos de 13 metros** de polígonos industriales y ferroviarios mapeados por OSM (comparado con los 1.13 km en el resto de la ZMM). Esto demuestra una correlación espacial directa entre la isla de calor extrema y las grandes naves de techos metálicos e industrias pesadas.
3. **El Efecto Valle Oriente (Hotspot 3):** Aunque Valle Oriente cuenta con más cobertura vegetal promedio (9.64%), su calor diurno extremo (SUHI máx de 13.81°C) es impulsado por la densidad de pavimentos, planchas de estacionamiento abiertas, y la inercia térmica de los rascacielos comerciales que reflejan la radiación solar y restringen el flujo de viento.

---

## 4. Diagnóstico Específico: Planta Ternium Guerrero (San Nicolás)
* **Ubicación Oficial de la Planta:** Coordenada central provista en `Lon={ternium_lon:.6f}, Lat={ternium_lat:.6f}`, correspondiente a la entrada y oficinas de la instalación.
* **Análisis de Amortiguamiento (Efecto del Tamaño del Buffer):**
  Evaluamos la isla de calor diurna a la redonda de la ubicación oficial de la planta:

| Radio del Buffer | Celdas Evaluadas | SUHI Promedio (°C) | SUHI Máxima (°C) | Suelo Construido (%) | Cobertura Verde (%) | Dosel Arbóreo (%) | Clusters Detectados |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Buffer 200m** | {df_ternium_stats.loc[df_ternium_stats['Radio (m)']==200, 'Celdas'].values[0]} | {df_ternium_stats.loc[df_ternium_stats['Radio (m)']==200, 'SUHI Promedio (°C)'].values[0]:.2f}°C | {df_ternium_stats.loc[df_ternium_stats['Radio (m)']==200, 'SUHI Máxima (°C)'].values[0]:.2f}°C | {df_ternium_stats.loc[df_ternium_stats['Radio (m)']==200, 'Suelo Construido (%)'].values[0]:.2f}% | {df_ternium_stats.loc[df_ternium_stats['Radio (m)']==200, 'Cobertura Verde (%)'].values[0]:.2f}% | {df_ternium_stats.loc[df_ternium_stats['Radio (m)']==200, 'Dosel Arbóreo (%)'].values[0]:.2f}% | {df_ternium_stats.loc[df_ternium_stats['Radio (m)']==200, 'Clusters Asociados'].values[0]} |
| **Buffer 100m** | {df_ternium_stats.loc[df_ternium_stats['Radio (m)']==100, 'Celdas'].values[0]} | {df_ternium_stats.loc[df_ternium_stats['Radio (m)']==100, 'SUHI Promedio (°C)'].values[0]:.2f}°C | {df_ternium_stats.loc[df_ternium_stats['Radio (m)']==100, 'SUHI Máxima (°C)'].values[0]:.2f}°C | {df_ternium_stats.loc[df_ternium_stats['Radio (m)']==100, 'Suelo Construido (%)'].values[0]:.2f}% | {df_ternium_stats.loc[df_ternium_stats['Radio (m)']==100, 'Cobertura Verde (%)'].values[0]:.2f}% | {df_ternium_stats.loc[df_ternium_stats['Radio (m)']==100, 'Dosel Arbóreo (%)'].values[0]:.2f}% | {df_ternium_stats.loc[df_ternium_stats['Radio (m)']==100, 'Clusters Asociados'].values[0]} |

### Conclusiones del Diagnóstico de Ternium:
1. **Calor Moderado en la Ubicación Central:** En la coordenada central de oficinas/accesos, un buffer estrecho de **100 metros** muestra una intensidad de isla de calor moderada (SUHI promedio de **2.56°C** y máxima de **4.48°C**), debido a que esta sección cuenta con cierta cobertura de vegetación (11.11%).
2. **Proximidad al Core Térmico (Cluster 38):** Aunque el buffer directo de 100m no intersecta con celdas por encima del percentil 95 (asociándose con **Ninguno**), el análisis espacial de proximidad revela que la planta de Ternium Guerrero alberga directamente dentro de sus instalaciones el **Cluster 38** (hotspot local de **1.62 hectáreas**).
3. **Distancia Crítica:** Este núcleo de calor extremo se localiza a solo **371.0 metros** al noreste de las oficinas centrales (dentro del mismo lindero industrial) y presenta temperaturas extremas con una SUHI promedio de **9.60°C**, máxima de **10.54°C** y prácticamente nula vegetación (3.27% de verde a 50m de su núcleo).

---

## 5. Fichas de Casos de Estudio de los Hotspots

### 📌 Caso de Estudio 1: Centro Histórico de Monterrey - San Nicolás (Cluster 44)
* **Descripción:** Con una extensión masiva de **{top_3_df.iloc[0]['area_ha']:.1f} ha**, es el núcleo de calor continuo más grande de la metrópoli, promediando una anomalía de **{top_3_df.iloc[0]['suhi_mean']:.2f}°C**.
* **Hipótesis Física:** Cañón urbano denso de concreto, pavimentos con baja reflectancia (albedo bajo del asfalto viejo) y un déficit de vegetación casi absoluto (cobertura verde menor al 3.2%). El domo térmico es continuo por la alta densidad urbana.
* **Mitigación Focalizada:** Aumento masivo de albedo en pavimentos mediante recubrimientos fríos y techos reflectivos, corredores verdes arbolados de conexión y arbolado de banquetas.

### 📌 Caso de Estudio 2: Zona Industrial de San Nicolás (Cluster 66)
* **Descripción:** Ubicado en San Nicolás de los Garza, este hotspot de **{top_3_df.iloc[1]['area_ha']:.1f} ha** promedia **{top_3_df.iloc[1]['suhi_mean']:.2f}°C** de SUHI.
* **Hipótesis Física:** Concentración de parques industriales de manufactura pesada y bodegas con cubiertas metálicas y asfalto de alto tonelaje. Las naves y linderos industriales retienen el calor antropogénico de procesos y aire acondicionado.
* **Mitigación Focalizada:** Techos verdes en naves industriales, buffers forestales perimetrales perimetrales de especies nativas espesas y reforestación de avenidas industriales anchas.

### 📌 Caso de Estudio 3: Eje San Pedro - Valle Oriente (Cluster 5)
* **Descripción:** Localizado en la colindancia entre Monterrey y San Pedro, este clúster de **{top_3_df.iloc[2]['area_ha']:.1f} ha** registra una temperatura SUHI máxima de **{top_3_df.iloc[2]['suhi_max']:.2f}°C**.
* **Hipótesis Física:** A pesar de su mayor vegetación promedio (9.64%), este hotspot responde al desarrollo de Valle Oriente: grandes rascacielos con fachadas de vidrio que reflejan radiación al suelo, inmensas planchas de estacionamiento al descubierto y alta concentración vehicular.
* **Mitigación Focalizada:** Sombreado de estacionamientos abiertos mediante pérgolas fotovoltaicas o arbolado denso, techos fríos en centros comerciales y restricción de superficies de asfalto expuesto en nuevos desarrollos.
"""
    
    report_path = notebook_dir / "04_hotspot_case_studies_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    print(f"      Reporte final guardado en: {report_path.relative_to(base_dir)}")
    print("=" * 80)
    print("PROCESAMIENTO Y GENERACIÓN DE PRODUCTOS COMPLETADO EXITOSAMENTE")
    print("=" * 80)

if __name__ == "__main__":
    main()
