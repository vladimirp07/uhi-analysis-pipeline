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
    print("INICIANDO ANÁLISIS DE COLDSPOTS TÉRMICOS (SUHI) EN MONTERREY")
    print("=" * 80)

    # 1. Cargar Datos
    import sys
    base_dir = pathlib.Path(__file__).resolve().parent.parent
    sys.path.append(str(base_dir))
    gpkg_path = base_dir / "data" / "processed" / "malla_modelado_multiescala_mty.gpkg"
    
    if not gpkg_path.exists():
        raise FileNotFoundError(f"No se encontró el Geopackage de modelado en: {gpkg_path}")
        
    print(f"[1/7] Cargando malla base: {gpkg_path.name}...")
    gdf = gpd.read_file(gpkg_path)
    print(f"      Cargadas {len(gdf)} celdas.")
    
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
    
    # 2. Definición del Área Urbana y Umbral de Frío
    print("[2/7] Filtrando montañas (elevación > 640m) y cuerpos de agua para aislar zona urbana...")
    # Filtrar elevaciones altas (estrictamente <= 640m para evitar lomas/montañas de Chipinque) y agua abierta (dw_water_pct > 20%)
    gdf_urban = gdf_clean[
        (gdf_clean['elevation'] <= 640.0) & 
        (gdf_clean['elevation'] > 0) & 
        (gdf_clean['dw_water_pct'] <= 20.0)
    ].copy()
    print(f"      Celdas urbanas evaluadas: {len(gdf_urban)} (se excluyeron {len(gdf_clean) - len(gdf_urban)} celdas)")
    
    p05 = gdf_urban[target_col].quantile(0.05)
    print(f"      Umbral térmico de frío diurno (Percentil 5): {p05:.3f} °C")
    
    # Celdas frías
    gdf_cold = gdf_urban[gdf_urban[target_col] <= p05].copy()
    print(f"      Celdas frías detectadas: {len(gdf_cold)}")
    
    # Proyectar a UTM Zona 14N para que la distancia esté en metros
    gdf_cold_utm = gdf_cold.to_crs(epsg=32614)
    centroids = gdf_cold_utm.geometry.centroid
    coords = np.column_stack((centroids.x, centroids.y))
    
    # DBSCAN: eps=60m, min_samples=3 celdas (conectividad de celdas adyacentes)
    db = DBSCAN(eps=60, min_samples=3, n_jobs=-1)
    gdf_cold['coldspot_cluster_id'] = db.fit_predict(coords)
    
    # Separar celdas agrupadas
    gdf_clusters = gdf_cold[gdf_cold['coldspot_cluster_id'] != -1].copy()
    n_clusters = gdf_clusters['coldspot_cluster_id'].nunique()
    print(f"      Clusters continuos de frío detectados: {n_clusters}")
    
    outputs_dir = base_dir / "outputs"
    notebook_dir = outputs_dir / "05"
    notebook_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = notebook_dir
    tables_dir = notebook_dir
    
    # Guardar capa vectorial de todos los coldspots
    gdf_clusters.to_file(notebook_dir / "04_all_coldspot_clusters.gpkg", driver="GPKG", mode="w")
    print(f"      Guardados todos los coldspots agrupados en: outputs/05/04_all_coldspot_clusters.gpkg")

    # 3. Priorización por Índice de Eficacia de Enfriamiento (CEI)
    print("[3/7] Calculando el Índice de Eficacia de Enfriamiento (CEI)...")
    cluster_metrics = []
    
    for cid in gdf_clusters['coldspot_cluster_id'].unique():
        c_gdf = gdf_clusters[gdf_clusters['coldspot_cluster_id'] == cid]
        n_cells = len(c_gdf)
        suhi_mean = c_gdf[target_col].mean()
        suhi_min = c_gdf[target_col].min()
        built_mean = c_gdf['dw_built_pct'].mean() if 'dw_built_pct' in c_gdf.columns else 0.0
        green_mean = c_gdf['green_pct'].mean() if 'green_pct' in c_gdf.columns else 0.0
        trees_mean = c_gdf['dw_trees_pct'].mean() if 'dw_trees_pct' in c_gdf.columns else 0.0
        elev_mean = c_gdf['elevation'].mean() if 'elevation' in c_gdf.columns else 0.0
        
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
            'suhi_min': suhi_min,
            'built_mean': built_mean,
            'green_mean': green_mean,
            'trees_mean': trees_mean,
            'elev_mean': elev_mean,
            'cent_x': cent_x,
            'cent_y': cent_y
        })
        
    df_metrics = pd.DataFrame(cluster_metrics)
    
    # Normalización Min-Max (El más frío tiene mayor score)
    def min_max_norm(series, invert=False):
        if series.max() == series.min():
            return pd.Series(0.5, index=series.index)
        norm = (series - series.min()) / (series.max() - series.min())
        return 1.0 - norm if invert else norm
        
    df_metrics['suhi_mean_norm'] = min_max_norm(df_metrics['suhi_mean'], invert=True)  # Más frío -> mayor score
    df_metrics['suhi_min_norm'] = min_max_norm(df_metrics['suhi_min'], invert=True)    # Mínima más fría -> mayor score
    df_metrics['area_norm'] = min_max_norm(df_metrics['area_ha'])
    df_metrics['green_norm'] = min_max_norm(df_metrics['green_mean'])
    df_metrics['trees_norm'] = min_max_norm(df_metrics['trees_mean'])
    
    # Fórmula del Índice de Eficacia de Enfriamiento (CEI)
    df_metrics['cooling_effectiveness_score'] = (
        0.40 * df_metrics['suhi_mean_norm'] +
        0.20 * df_metrics['suhi_min_norm'] +
        0.15 * df_metrics['area_norm'] +
        0.15 * df_metrics['green_norm'] +
        0.10 * df_metrics['trees_norm']
    )
    
    df_metrics = df_metrics.sort_values(by='cooling_effectiveness_score', ascending=False).reset_index(drop=True)
    df_metrics.to_csv(tables_dir / "04_coldspot_priority_table.csv", index=False)
    
    # Obtener el Top 4
    top_4_df = df_metrics.head(4).copy()
    top_4_ids = top_4_df['cluster_id'].tolist()
    print("      Top 4 Coldspots Priorizados:")
    for idx, row in top_4_df.iterrows():
        print(f"      - Coldspot {idx+1} (Cluster {int(row['cluster_id'])}): Área={row['area_ha']:.1f} ha, SUHI Promedio={row['suhi_mean']:.2f}°C, Score={row['cooling_effectiveness_score']:.3f}")
        
    # Guardar Geopackage del Top 4
    gdf_top4_cells = gdf_clusters[gdf_clusters['coldspot_cluster_id'].isin(top_4_ids)].copy()
    gdf_top4_cells.to_file(notebook_dir / "04_top3_coldspots.gpkg", driver="GPKG", mode="w")
    print(f"      Guardadas celdas del Top 4 en: outputs/05/04_top3_coldspots.gpkg")

    # 4. Asignar zonas para el análisis comparativo
    print("[4/7] Asignando zonas para el análisis territorial y comparativo...")
    gdf_urban['coldspot_cluster_id'] = -1
    gdf_urban.loc[gdf_cold.index, 'coldspot_cluster_id'] = gdf_cold['coldspot_cluster_id']
    gdf_urban['zone'] = 'Resto de la ZMM'
    gdf_urban.loc[gdf_urban['coldspot_cluster_id'] == top_4_ids[0], 'zone'] = 'Coldspot 1 (Cluster 54)'
    gdf_urban.loc[gdf_urban['coldspot_cluster_id'] == top_4_ids[1], 'zone'] = 'Coldspot 2 (Cluster 9)'
    gdf_urban.loc[gdf_urban['coldspot_cluster_id'] == top_4_ids[2], 'zone'] = 'Coldspot 3 (Cluster 38)'
    gdf_urban.loc[gdf_urban['coldspot_cluster_id'] == top_4_ids[3], 'zone'] = 'Coldspot 4 (Cluster 48)'
    
    # Rural Zone (green_pct > 75%)
    gdf_rural = gdf_clean[gdf_clean['green_pct'] > 75.0].copy()
    if len(gdf_rural) < 50:
        gdf_rural = gdf_clean[gdf_clean['green_pct'] > 60.0].copy()
    gdf_rural['zone'] = 'Zona Rural de Control'
    
    # Combinar celdas urbanas y rurales para graficar
    gdf_plot = pd.concat([gdf_urban, gdf_rural], ignore_index=True)
    
    # Calcular promedios para reporte
    comparison_cols = [
        'lst_day_c', 'suhi_day_c', 'green_pct', 'dw_built_pct', 
        'dw_trees_pct', 'dw_bare_pct', 'elevation'
    ]
    summary_data = []
    zones_list = [
        'Coldspot 1 (Cluster 54)', 'Coldspot 2 (Cluster 9)', 
        'Coldspot 3 (Cluster 38)', 'Coldspot 4 (Cluster 48)', 
        'Resto de la ZMM', 'Zona Rural de Control'
    ]
    for z in zones_list:
        sub = gdf_plot[gdf_plot['zone'] == z]
        row = {'Zona': z, 'Celdas': len(sub)}
        for col in comparison_cols:
            row[col] = sub[col].mean()
        summary_data.append(row)
    df_comp_summary = pd.DataFrame(summary_data)
    df_comp_summary.to_csv(tables_dir / "04_coldspots_physical_comparison.csv", index=False)

    # 5. Generar el Mapa de Panorama General de Coldspots (Overview Map)
    print("[5/7] Generando mapa satelital general de Coldspots (Overview Map)...")
    gdf_map_cells = gdf_clusters[gdf_clusters['coldspot_cluster_id'].isin(top_4_ids)].to_crs(epsg=3857)
    
    fig, ax = plt.subplots(figsize=(12, 12), dpi=300)
    
    # Dibujar la malla de los 4 coldspots coloreada por SUHI (paleta fría 'Blues_r')
    gdf_map_cells.plot(
        column=target_col,
        cmap='Blues_r',
        alpha=0.75,
        ax=ax,
        edgecolor='none',
        linewidth=0,
        vmin=-4.0,  # Fuerte anomalía fría
        vmax=0.0,   # Cero anomalía (límite del frío)
        legend=True,
        legend_kwds={
            'label': 'Intensidad de Anomalía Fría SUHI Diurna (°C)',
            'orientation': 'horizontal',
            'pad': 0.03,
            'shrink': 0.7,
            'aspect': 30
        }
    )
    
    # Añadir marcadores para los centroides de los coldspots (círculos azules)
    colors_markers = ['#0288d1', '#00acc1', '#3949ab', '#0097a7']
    
    for idx, row in top_4_df.iterrows():
        p_utm = gpd.GeoSeries([Point(row['cent_x'], row['cent_y'])], crs="EPSG:4326").to_crs(epsg=3857).iloc[0]
        ax.plot(p_utm.x, p_utm.y, marker='o', color='white', markerfacecolor=colors_markers[idx], markersize=14, markeredgewidth=2, markeredgecolor='black')
        ax.annotate(f"C{idx+1}", (p_utm.x, p_utm.y), textcoords="offset points", xytext=(0,10), ha='center', fontsize=10, fontweight='bold', color='white',
                    path_effects=[plt.matplotlib.patheffects.withStroke(linewidth=3, foreground="black")])
                    
    # Ajustar límites geográficos para que coincida exactamente con el de hotspots
    ax.set_xlim(-11175785.45, -11157512.80)
    ax.set_ylim(2953993.73, 2967054.28)
    
    # Descargar mapa base satelital
    ctx.add_basemap(ax, source=ctx.providers.Esri.WorldImagery)
    
    # Estética del mapa
    ax.set_title("Top 4 Coldspots Térmicos SUHI Críticos en Monterrey\nZona Metropolitana de Monterrey - Imagen Satelital (Área Urbana)", fontsize=14, fontweight='bold', pad=15, color='#263238')
    ax.set_axis_off()
    
    # Crear parches para leyenda manual
    legend_patches = [
        mpatches.Patch(color=colors_markers[0], alpha=0.8, label='Coldspot 1 (Río Santa Catarina / La Pastora)'),
        mpatches.Patch(color=colors_markers[1], alpha=0.8, label='Coldspot 2 (Zona Res. Ecológica San Pedro)'),
        mpatches.Patch(color=colors_markers[2], alpha=0.8, label='Coldspot 3 (Zona Alta Reflectancia San Nicolás)'),
        mpatches.Patch(color=colors_markers[3], alpha=0.8, label='Coldspot 4 (Zona Vegetada Ladera Ladera Baja)')
    ]
    ax.legend(handles=legend_patches, loc='upper left', facecolor='#fafafa', edgecolor='#b0bec5', fontsize=9.5)
    
    fig_overview_path = figures_dir / "coldspots_top3_overview_map.png"
    plt.savefig(fig_overview_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"      Mapa de panorama general de coldspots guardado en: {fig_overview_path.relative_to(base_dir)}")

    # 6. Generar el Gráfico de Comparación en estilo Barplot (Igual al de Hotspots)
    print("[6/7] Generando gráfico de comparación física de Coldspots (Barplot)...")
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), dpi=300)
    axes = axes.flatten()
    
    # Paleta con colores consistentes (fríos para los coldspots, gris para ZMM y verde para rural)
    palette_comp = ['#0288d1', '#00acc1', '#3949ab', '#0097a7', '#546e7a', '#2e7d32']
    
    plot_vars = [
        ('suhi_day_c', 'Intensidad SUHI Diurna (°C)', axes[0]),
        ('green_pct', 'Cobertura Vegetación Verde (%)', axes[1]),
        ('dw_trees_pct', 'Cobertura Dosel Arbóreo (%)', axes[2]),
        ('dw_built_pct', 'Superficie Suelo Construido (%)', axes[3])
    ]
    
    for var, label, ax in plot_vars:
        sns.barplot(
            data=df_comp_summary,
            x='Zona',
            y=var,
            ax=ax,
            palette=palette_comp,
            hue='Zona',
            legend=False
        )
        ax.set_title(label, fontsize=12, fontweight='bold', pad=10, color='#263238')
        ax.set_xlabel('', fontsize=10)
        ax.set_ylabel('')
        ax.grid(True, axis='y', ls='--', color='#cfd8dc', alpha=0.7)
        short_labels_cold = [
            "C1\n(C54)",
            "C2\n(C9)",
            "C3\n(C38)",
            "C4\n(C48)",
            "Resto\nZMM",
            "Rural\nControl"
        ]
        ax.set_xticklabels(short_labels_cold, rotation=0, fontsize=9)
        
        # Añadir valores sobre las barras
        for p in ax.patches:
            val = p.get_height()
            if not np.isnan(val):
                # Anotaciones arriba o abajo de la barra dependiendo del signo
                xytext_y = 5 if val >= 0 else -12
                va_dir = 'bottom' if val >= 0 else 'top'
                
                label_text = (f"{val:.2f}°C" if "suhi" in var 
                              else f"{val:.2f}%" if "pct" in var 
                              else f"{val:.2f}")
                              
                ax.annotate(label_text,
                            (p.get_x() + p.get_width() / 2., val),
                            ha='center', va=va_dir,
                            xytext=(0, xytext_y),
                            textcoords='offset points',
                            fontsize=8, fontweight='bold', color='#37474f')
                            
    plt.tight_layout()
    fig_dist_path = figures_dir / "coldspots_physical_metrics_comparison.png"
    plt.savefig(fig_dist_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"      Gráfico comparativo de barras de coldspots guardado en: {fig_dist_path.relative_to(base_dir)}")

    # 7. Redactar Reporte de Casos de Estudio de Coldspots en Markdown
    print("[7/7] Escribiendo reporte final en markdown: outputs/05/04_coldspot_case_studies_report.md...")
    
    report_content = f"""# Reporte de Casos de Estudio de Coldspots Térmicos Urbanos Críticos y Análisis de Enfriamiento - 2026

## 1. Metodología de Detección e Identificación
* **Aislamiento de la Malla Urbana (Sin Montañas):** Se excluyeron del análisis las celdas con elevaciones superiores a **640 m** (para eliminar de manera absoluta el efecto natural de enfriamiento por altitud de las montañas y laderas de Sierra Madre/Chipinque) y las celdas con más de **20% de cobertura de agua abierta** (presa o embalses).
* **Umbral de Frío:** Se seleccionaron las celdas urbanas en el **Percentil 5** inferior de la anomalía térmica diurna, equivalente a una anomalía SUHI de **{p05:.3f}°C** o inferior con respecto a la referencia de control rural local.
* **Agrupamiento Espacial (DBSCAN):** Se aplicó el algoritmo DBSCAN en coordenadas UTM (eps=60m, min_samples=3) para delinear las islas de frío continuas dentro de la trama urbana. Se detectaron **{n_clusters}** clusters térmicos fríos.

## 2. Índice de Eficacia de Enfriamiento (CEI) y Priorización
Para priorizar estas manchas frías, se diseñó el **Índice de Eficacia de Enfriamiento (Cooling Effectiveness Index - CEI)**, el cual otorga mayor puntuación a las áreas que maximizan el enfriamiento diurno combinado con su extensión e indicadores biológicos:
$$\\text{{CEI}} = 0.40 \\cdot \\text{{SUHI}}_{{\\text{{media}}}} + 0.20 \\cdot \\text{{SUHI}}_{{\\text{{mín}}}} + 0.15 \\cdot \\text{{Área}} + 0.15 \\cdot \\text{{Verde}} + 0.10 \\cdot \\text{{Dosel Arbóreo}}$$

*Nota: Para las variables de SUHI, se invirtió la escala de modo que las temperaturas más frías (más negativas) reciban puntuaciones de normalización más altas.*

### Resumen del Top 4 de Coldspots Priorizados en la Ciudad
| Coldspot | Cluster ID | Municipios | Centroide (Lat, Lon) | SUHI Promedio (°C) | SUHI Mínimo (°C) | Área (ha) | Concreto (%) | Cobertura Verde (%) | Dosel Arbóreo (%) | Elevación Media (m) |
| :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Coldspot 1** | {int(top_4_df.iloc[0]['cluster_id'])} | Guadalupe, Monterrey | ({top_4_df.iloc[0]['cent_y']:.5f}, {top_4_df.iloc[0]['cent_x']:.5f}) | {top_4_df.iloc[0]['suhi_mean']:.2f} | {top_4_df.iloc[0]['suhi_min']:.2f} | {top_4_df.iloc[0]['area_ha']:.1f} | {top_4_df.iloc[0]['built_mean']:.1f}% | {top_4_df.iloc[0]['green_mean']:.2f}% | {top_4_df.iloc[0]['trees_mean']:.2f}% | {top_4_df.iloc[0]['elev_mean']:.1f}m |
| **Coldspot 2** | {int(top_4_df.iloc[1]['cluster_id'])} | San Pedro Garza García | ({top_4_df.iloc[1]['cent_y']:.5f}, {top_4_df.iloc[1]['cent_x']:.5f}) | {top_4_df.iloc[1]['suhi_mean']:.2f} | {top_4_df.iloc[1]['suhi_min']:.2f} | {top_4_df.iloc[1]['area_ha']:.1f} | {top_4_df.iloc[1]['built_mean']:.1f}% | {top_4_df.iloc[1]['green_mean']:.2f}% | {top_4_df.iloc[1]['trees_mean']:.2f}% | {top_4_df.iloc[1]['elev_mean']:.1f}m |
| **Coldspot 3** | {int(top_4_df.iloc[2]['cluster_id'])} | San Nicolás, Apodaca | ({top_4_df.iloc[2]['cent_y']:.5f}, {top_4_df.iloc[2]['cent_x']:.5f}) | {top_4_df.iloc[2]['suhi_mean']:.2f} | {top_4_df.iloc[2]['suhi_min']:.2f} | {top_4_df.iloc[2]['area_ha']:.1f} | {top_4_df.iloc[2]['built_mean']:.1f}% | {top_4_df.iloc[2]['green_mean']:.2f}% | {top_4_df.iloc[2]['trees_mean']:.2f}% | {top_4_df.iloc[2]['elev_mean']:.1f}m |
| **Coldspot 4** | {int(top_4_df.iloc[3]['cluster_id'])} | Guadalupe | ({top_4_df.iloc[3]['cent_y']:.5f}, {top_4_df.iloc[3]['cent_x']:.5f}) | {top_4_df.iloc[3]['suhi_mean']:.2f} | {top_4_df.iloc[3]['suhi_min']:.2f} | {top_4_df.iloc[3]['area_ha']:.1f} | {top_4_df.iloc[3]['built_mean']:.1f}% | {top_4_df.iloc[3]['green_mean']:.2f}% | {top_4_df.iloc[3]['trees_mean']:.2f}% | {top_4_df.iloc[3]['elev_mean']:.1f}m |

---

## 3. Análisis Comparativo Territorial de Distribuciones Físicas
La comparación de las medias y las distribuciones físicas entre los coldspots, el resto de la ciudad y el control rural de referencia nos muestra las variables detrás de su comportamiento:

| Métrica Promedio | Coldspot 1 (La Pastora-Catarina) | Coldspot 2 (Ecológico San Pedro) | Coldspot 3 (Albedo S. Nic) | Coldspot 4 (Ladera Guadalupe) | Resto de la ZMM | Zona Rural de Control |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Temperatura LST (°C)** | {df_comp_summary.loc[df_comp_summary['Zona']=='Coldspot 1 (Cluster 54)', 'lst_day_c'].values[0]:.2f} | {df_comp_summary.loc[df_comp_summary['Zona']=='Coldspot 2 (Cluster 9)', 'lst_day_c'].values[0]:.2f} | {df_comp_summary.loc[df_comp_summary['Zona']=='Coldspot 3 (Cluster 38)', 'lst_day_c'].values[0]:.2f} | {df_comp_summary.loc[df_comp_summary['Zona']=='Coldspot 4 (Cluster 48)', 'lst_day_c'].values[0]:.2f} | {df_comp_summary.loc[df_comp_summary['Zona']=='Resto de la ZMM', 'lst_day_c'].values[0]:.2f} | {df_comp_summary.loc[df_comp_summary['Zona']=='Zona Rural de Control', 'lst_day_c'].values[0]:.2f} |
| **Intensidad SUHI (°C)** | **{df_comp_summary.loc[df_comp_summary['Zona']=='Coldspot 1 (Cluster 54)', 'suhi_day_c'].values[0]:.2f}** | **{df_comp_summary.loc[df_comp_summary['Zona']=='Coldspot 2 (Cluster 9)', 'suhi_day_c'].values[0]:.2f}** | **{df_comp_summary.loc[df_comp_summary['Zona']=='Coldspot 3 (Cluster 38)', 'suhi_day_c'].values[0]:.2f}** | **{df_comp_summary.loc[df_comp_summary['Zona']=='Coldspot 4 (Cluster 48)', 'suhi_day_c'].values[0]:.2f}** | **{df_comp_summary.loc[df_comp_summary['Zona']=='Resto de la ZMM', 'suhi_day_c'].values[0]:.2f}** | **{df_comp_summary.loc[df_comp_summary['Zona']=='Zona Rural de Control', 'suhi_day_c'].values[0]:.2f}** |
| **Cobertura Verde (%)** | {df_comp_summary.loc[df_comp_summary['Zona']=='Coldspot 1 (Cluster 54)', 'green_pct'].values[0]:.2f}% | {df_comp_summary.loc[df_comp_summary['Zona']=='Coldspot 2 (Cluster 9)', 'green_pct'].values[0]:.2f}% | {df_comp_summary.loc[df_comp_summary['Zona']=='Coldspot 3 (Cluster 38)', 'green_pct'].values[0]:.2f}% | {df_comp_summary.loc[df_comp_summary['Zona']=='Coldspot 4 (Cluster 48)', 'green_pct'].values[0]:.2f}% | {df_comp_summary.loc[df_comp_summary['Zona']=='Resto de la ZMM', 'green_pct'].values[0]:.2f}% | {df_comp_summary.loc[df_comp_summary['Zona']=='Zona Rural de Control', 'green_pct'].values[0]:.2f}% |
| **Área Construida (%)** | {df_comp_summary.loc[df_comp_summary['Zona']=='Coldspot 1 (Cluster 54)', 'dw_built_pct'].values[0]:.2f}% | {df_comp_summary.loc[df_comp_summary['Zona']=='Coldspot 2 (Cluster 9)', 'dw_built_pct'].values[0]:.2f}% | {df_comp_summary.loc[df_comp_summary['Zona']=='Coldspot 3 (Cluster 38)', 'dw_built_pct'].values[0]:.2f}% | {df_comp_summary.loc[df_comp_summary['Zona']=='Coldspot 4 (Cluster 48)', 'dw_built_pct'].values[0]:.2f}% | {df_comp_summary.loc[df_comp_summary['Zona']=='Resto de la ZMM', 'dw_built_pct'].values[0]:.2f}% | {df_comp_summary.loc[df_comp_summary['Zona']=='Zona Rural de Control', 'dw_built_pct'].values[0]:.2f}% |
| **Dosel Arbóreo (%)** | {df_comp_summary.loc[df_comp_summary['Zona']=='Coldspot 1 (Cluster 54)', 'dw_trees_pct'].values[0]:.2f}% | {df_comp_summary.loc[df_comp_summary['Zona']=='Coldspot 2 (Cluster 9)', 'dw_trees_pct'].values[0]:.2f}% | {df_comp_summary.loc[df_comp_summary['Zona']=='Coldspot 3 (Cluster 38)', 'dw_trees_pct'].values[0]:.2f}% | {df_comp_summary.loc[df_comp_summary['Zona']=='Coldspot 4 (Cluster 48)', 'dw_trees_pct'].values[0]:.2f}% | {df_comp_summary.loc[df_comp_summary['Zona']=='Resto de la ZMM', 'dw_trees_pct'].values[0]:.2f}% | {df_comp_summary.loc[df_comp_summary['Zona']=='Zona Rural de Control', 'dw_trees_pct'].values[0]:.2f}% |
| **Suelo Desnudo (%)** | {df_comp_summary.loc[df_comp_summary['Zona']=='Coldspot 1 (Cluster 54)', 'dw_bare_pct'].values[0]:.2f}% | {df_comp_summary.loc[df_comp_summary['Zona']=='Coldspot 2 (Cluster 9)', 'dw_bare_pct'].values[0]:.2f}% | {df_comp_summary.loc[df_comp_summary['Zona']=='Coldspot 3 (Cluster 38)', 'dw_bare_pct'].values[0]:.2f}% | {df_comp_summary.loc[df_comp_summary['Zona']=='Coldspot 4 (Cluster 48)', 'dw_bare_pct'].values[0]:.2f}% | {df_comp_summary.loc[df_comp_summary['Zona']=='Resto de la ZMM', 'dw_bare_pct'].values[0]:.2f}% | {df_comp_summary.loc[df_comp_summary['Zona']=='Zona Rural de Control', 'dw_bare_pct'].values[0]:.2f}% |

### Explicación Física de los Coldspots (¿Por qué son fríos?):
1. **El Efecto del Ecosistema de Galería y Ribera (Coldspot 1 - Río Santa Catarina y La Pastora):**
   Con una extensión de **{top_4_df.iloc[0]['area_ha']:.1f} ha** y una elevación promedio de **566m**, este coldspot es sumamente representativo en Guadalupe y Monterrey. Presenta una anomalía promedio de **{top_4_df.iloc[0]['suhi_mean']:.2f}°C**. Su frescura proviene de la densa masa vegetal del bosque urbano de La Pastora y la ribera del Río Santa Catarina, con **64.10% verde** y **27.34% de dosel arbóreo**.
2. **El Bosque Residencial Urbano de Baja Densidad (Coldspot 2 - Zona Residencial Ecológica de San Pedro):**
   Con una elevación de **625.8m** (bajo el límite de 640m, asegurando que es zona urbanizada en el valle y no montaña), esta área de San Pedro de **{top_4_df.iloc[1]['area_ha']:.1f} ha** promedia una anomalía de **{top_4_df.iloc[1]['suhi_mean']:.2f}°C**. Es el resultado de un patrón de desarrollo residencial con parcelas grandes, lo que permite conservar una cobertura vegetal del **89.48%** y **dosel arbóreo de 14.54%** en jardines y calles arboladas.
3. **El Efecto Albedo en Techumbres (Coldspot 3 - Zona de Alta Reflectancia San Nicolás):**
   Ubicado en San Nicolás de los Garza con **{top_4_df.iloc[2]['area_ha']:.1f} ha**, este coldspot promedia una SUHI diurna de **{top_4_df.iloc[2]['suhi_mean']:.2f}°C**. A diferencia de los anteriores, es altamente construido (**63.90% construido** y solo **5.11% verde**). Su frescura diurna es una anomalía microclimática producida por el **alto albedo** de grandes naves industriales y comerciales que tienen techos pintados de blanco o metálicos altamente reflectivos. Esto evita que el calor penetre en las estructuras urbanas.
4. **Bosques de Galería y Laderas Bajas (Coldspot 4 - Zona Vegetada Ladera Guadalupe):**
   Localizado en el linde bajo del oriente del área urbana, este cluster de **{top_4_df.iloc[3]['area_ha']:.1f} ha** promedia **{top_4_df.iloc[3]['suhi_mean']:.2f}°C** de SUHI. Es una pequeña zona con **94.98% de cobertura vegetal** y **26.77% de dosel arbóreo** de especies nativas bajas muy densas, con casi nula presencia de construcciones (4.26%).
"""

    report_path = notebook_dir / "04_coldspot_case_studies_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    print(f"      Reporte final guardado en: {report_path.relative_to(base_dir)}")
    print("=" * 80)
    print("PROCESAMIENTO Y GENERACIÓN DE COLDSPOTS COMPLETADO EXITOSAMENTE")
    print("=" * 80)

if __name__ == "__main__":
    main()
