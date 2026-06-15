#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de Análisis de Regiones de Densidad y SUHI con Nuevas Variables
====================================================================
Este script realiza el análisis por regiones de densidad de la superficie construida,
incorporando variables de vegetación (NDVI, buffers), urbanas, sociales de vulnerabilidad
y nuevas variables derivadas (presión urbana, vulnerabilidad térmica, etc.).
Genera matrices de correlación por zona, gráficos multiescala y tablas de resultados.

Autor: Antigravity AI
Fecha: Junio 2026
"""

import os
import pathlib
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
import rasterio
from scipy.spatial import KDTree
from sklearn.preprocessing import MinMaxScaler

def print_step(title):
    print("\n" + "="*80)
    print(f" {title.upper()}")
    print("="*80)

def main():
    import sys
    base_dir = pathlib.Path(__file__).resolve().parent.parent
    sys.path.append(str(base_dir))
    processed_dir = base_dir / "data" / "processed"
    interim_dir = base_dir / "data" / "interim"
    outputs_dir = base_dir / "outputs"
    figures_dir = outputs_dir / "figures"
    tables_dir = outputs_dir / "tables"
    
    figures_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)
    
    print_step("1. Carga de Datos Geográficos y Censales")
    
    # 1.1 Cargar cuadrícula multiescala
    malla_path = processed_dir / "malla_modelado_multiescala_mty.gpkg"
    if not malla_path.exists():
        raise FileNotFoundError(f"No se encontró el geopackage de modelado: {malla_path}")
    print(f"[Carga] Cargando malla base: {malla_path.name}...")
    gdf = gpd.read_file(malla_path)
    print(f"        Se cargaron {len(gdf)} celdas de 30m.")
    
    # 1.2 Cargar capa de AGEB con datos socioeconómicos
    ageb_path = processed_dir / "ageb_maestra_mty_2026.gpkg"
    if not ageb_path.exists():
        raise FileNotFoundError(f"No se encontró el geopackage de AGEBs: {ageb_path}")
    print(f"[Carga] Cargando AGEB maestra: {ageb_path.name}...")
    ageb_gdf = gpd.read_file(ageb_path)
    print(f"        Se cargaron {len(ageb_gdf)} polígonos de AGEB.")

    print_step("2. Extracción de NDVI de Sentinel-2")
    
    # 2.1 Muestrear NDVI en los centroides de la malla
    ndvi_raster_path = interim_dir / "ndvi_mty_2026.tif"
    if ndvi_raster_path.exists():
        print(f"[NDVI] Muestreando NDVI desde {ndvi_raster_path.name}...")
        centroids_4326 = gdf.geometry.centroid.to_crs(epsg=4326)
        coords_4326 = [(geom.x, geom.y) for geom in centroids_4326]
        
        with rasterio.open(ndvi_raster_path) as src:
            nodata_val = src.nodata
            ndvi_vals = []
            for val in src.sample(coords_4326):
                v = val[0]
                if v == nodata_val or np.isnan(v) or v < -1.0 or v > 1.0:
                    ndvi_vals.append(np.nan)
                else:
                    ndvi_vals.append(float(v))
        gdf['ndvi'] = ndvi_vals
        print(f"       NDVI muestreado con éxito. Valores válidos: {gdf['ndvi'].notna().sum()}")
    else:
        print("[NDVI] ADVERTENCIA: No se encontró ndvi_mty_2026.tif. Usando green_pct/100 como fallback de NDVI.")
        gdf['ndvi'] = gdf['green_pct'] / 100.0

    print_step("3. Spatial Join con Datos Socioeconómicos a nivel de AGEB")
    
    # 3.1 Alinear CRS
    if ageb_gdf.crs != gdf.crs:
        print("[CRS] Alineando CRS de AGEB al de la malla...")
        ageb_gdf = ageb_gdf.to_crs(gdf.crs)
        
    # 3.2 Realizar Spatial Join usando los centroides de la malla para asociarlos a un AGEB único
    print("[SJOIN] Ejecutando Spatial Join de centroides de la malla con polígonos de AGEB...")
    gdf_centroids = gdf.copy()
    gdf_centroids['geometry'] = gdf.geometry.centroid
    
    # Seleccionar columnas sociales relevantes del AGEB (evitando colisión de nombres de temperatura)
    social_cols = [
        'CVEGEO', 'POBTOT', 'pop_density_ageb', 'pct_0_14', 'pct_65_mas', 
        'pct_60ymas', 'pct_hli', 'pct_psinder', 'graproes', 'pct_vph_refri', 
        'pct_vph_tinaco', 'pct_vph_cister', 'pct_vph_snbien', 'pct_vph_ndeaed', 
        'area_km2', 'geometry'
    ]
    
    joined_centroids = gpd.sjoin(
        gdf_centroids[['cell_id', 'geometry']], 
        ageb_gdf[social_cols], 
        how='left', 
        predicate='within'
    )
    
    # Unir de regreso a la malla por cell_id
    joined_data = joined_centroids.drop(columns=['geometry', 'index_right'])
    gdf = gdf.merge(joined_data, on='cell_id', how='left')
    print(f"        Malla asociada exitosamente. Celdas con AGEB asignado: {gdf['CVEGEO'].notna().sum()}")

    print_step("4. Derivación de Nuevas Variables Espaciales y Socioambientales")
    
    # 4.1 Distancia a Áreas Verdes (dist_to_green_core_m)
    # Definimos áreas verdes como celdas con green_pct >= 50%
    print("[Derived] Calculando distancia a núcleos de vegetación (green_pct >= 50%)...")
    green_core = gdf[gdf['green_pct'] >= 50.0].copy()
    if len(green_core) > 0:
        coords_green = np.column_stack((green_core['x_coord'], green_core['y_coord']))
        tree_green = KDTree(coords_green)
        coords_all = np.column_stack((gdf['x_coord'], gdf['y_coord']))
        dists, _ = tree_green.query(coords_all, k=1)
        gdf['dist_to_green_core_m'] = dists
    else:
        print("          No se encontraron celdas con green_pct >= 50. Usando green_pct >= 30...")
        green_core = gdf[gdf['green_pct'] >= 30.0].copy()
        if len(green_core) > 0:
            coords_green = np.column_stack((green_core['x_coord'], green_core['y_coord']))
            tree_green = KDTree(coords_green)
            coords_all = np.column_stack((gdf['x_coord'], gdf['y_coord']))
            dists, _ = tree_green.query(coords_all, k=1)
            gdf['dist_to_green_core_m'] = dists
        else:
            gdf['dist_to_green_core_m'] = 9999.0
    print(f"          Distancia promedio calculada: {gdf['dist_to_green_core_m'].mean():.2f} metros.")
            
    # 4.2 Built-Green Ratio
    # Mide la proporción de concreto vs vegetación en la celda
    gdf['built_green_ratio'] = gdf['dw_built_pct'] / (gdf['green_pct'] + 0.1)
    
    # 4.3 Acceso a áreas verdes por habitante (m2 de vegetación verde por persona)
    # Calculado a nivel AGEB: (green_fraction * area_m2) / POBTOT
    print("[Derived] Calculando acceso a áreas verdes per cápita a nivel AGEB...")
    gdf['green_area_m2'] = (gdf['green_pct'] / 100.0) * (gdf['area_km2'] * 1_000_000.0)
    gdf['acceso_verde_capita'] = (gdf['green_area_m2'] / (gdf['POBTOT'] + 1.0)).fillna(0.0)
    # Limitar valores extremos por outliers demográficos
    gdf['acceso_verde_capita'] = gdf['acceso_verde_capita'].clip(upper=1000.0)
    
    # 4.4 Interacciones
    # Interacción Densidad Construida * Vegetación
    gdf['interact_built_green'] = (gdf['dw_built_pct'] / 100.0) * (gdf['green_pct'] / 100.0)
    # Interacción Industria * Baja Vegetación
    gdf['interact_ind_low_green'] = (gdf['industrial_osm_pct'] / 100.0) * (1.0 - (gdf['green_pct'] / 100.0))
    # Distancia combinada a industria y áreas verdes (suma de distancias)
    gdf['dist_comb_ind_green'] = gdf['distance_to_industry_osm_m'] + gdf['dist_to_green_core_m']
    
    # 4.5 Índice Simple de Presión Urbana (built + built - green)
    # Normalizamos cada componente a [0, 1] antes de calcular para evitar sesgo de escalas
    scaler = MinMaxScaler()
    built_norm = scaler.fit_transform(gdf[['dw_built_pct']].fillna(0))
    green_norm = scaler.fit_transform(gdf[['green_pct']].fillna(0))
    gdf['indice_presion_urbana'] = (built_norm + built_norm - green_norm).flatten()
    
    # 4.6 Índice Simple de Vulnerabilidad Térmica (calor + pop_density - acceso_verde)
    print("[Derived] Calculando Índice de Vulnerabilidad Térmica...")
    suhi_norm = scaler.fit_transform(gdf[['suhi_day_c']].fillna(gdf['suhi_day_c'].mean()))
    pop_norm = scaler.fit_transform(gdf[['pop_density_ageb']].fillna(0))
    verde_norm = scaler.fit_transform(gdf[['acceso_verde_capita']].fillna(0))
    gdf['indice_vulnerabilidad_termica'] = (suhi_norm + pop_norm - verde_norm).flatten()
    
    print("        Variables derivadas creadas con éxito.")

    print_step("5. Segmentación por Zonas de Densidad Construida")
    
    # Clasificación original
    # 1. Baja densidad: < 20%
    # 2. Media densidad: 20-60%
    # 3. Alta densidad: >= 60%
    conditions = [
        (gdf['dw_built_pct'] < 20.0),
        ((gdf['dw_built_pct'] >= 20.0) & (gdf['dw_built_pct'] < 60.0)),
        (gdf['dw_built_pct'] >= 60.0)
    ]
    choices = ['Baja Densidad (<20%)', 'Media Densidad (20-60%)', 'Alta Densidad (>=60%)']
    gdf['zona_densidad'] = np.select(conditions, choices, default='Media Densidad (20-60%)')
    
    for zone in choices:
        count = (gdf['zona_densidad'] == zone).sum()
        pct = (gdf['zona_densidad'] == zone).mean() * 100
        print(f"        * {zone}: {count} celdas ({pct:.2f}%)")

    print_step("6. Cálculo de Correlaciones de Spearman por Región")
    
    # Definir variables a evaluar
    target_col = 'suhi_day_c'
    variables_explicativas = {
        'Físicas/Biofísicas': ['green_pct', 'dw_trees_pct', 'dw_grass_pct', 'dw_bare_pct', 'ndvi'],
        'Urbanas': ['dw_built_pct', 'built_green_ratio', 'distance_to_industry_osm_m', 'dist_to_green_core_m', 'elevation'],
        'Buffers': [
            'green_pct_250m', 'green_pct_500m', 'green_pct_1000m', 'green_pct_3000m',
            'dw_built_250m', 'dw_built_500m', 'dw_built_1000m', 'dw_built_3000m',
            'dw_trees_250m', 'dw_trees_500m', 'dw_trees_1000m', 'dw_trees_3000m',
            'industrial_density_250m', 'industrial_density_500m', 'industrial_density_1000m', 'industrial_density_3000m'
        ],
        'Sociales/Vulnerabilidad': ['pop_density_ageb', 'pct_psinder', 'graproes', 'pct_vph_refri', 'pct_vph_tinaco', 'pct_vph_cister', 'pct_vph_snbien', 'pct_vph_ndeaed', 'acceso_verde_capita'],
        'Derivadas Interacciones': ['interact_built_green', 'interact_ind_low_green', 'dist_comb_ind_green', 'indice_presion_urbana', 'indice_vulnerabilidad_termica']
    }
    
    # Consolidar lista plana de todas las explicativas válidas en el df
    todas_vars = []
    for g, vlist in variables_explicativas.items():
        todas_vars.extend([v for v in vlist if v in gdf.columns])
    todas_vars = list(set(todas_vars))
    
    # Calcular correlaciones por zona
    corrs_list = []
    
    for zone in choices:
        gdf_zone = gdf[gdf['zona_densidad'] == zone].copy()
        n_obs = len(gdf_zone)
        
        # Calcular correlación Spearman de cada variable contra el target (suhi_day_c)
        for var in todas_vars:
            df_sub = gdf_zone[[target_col, var]].dropna()
            if len(df_sub) > 10:
                corr_val, p_val = stats_spearman(df_sub[target_col].values, df_sub[var].values)
                corrs_list.append({
                    'zona': zone,
                    'variable': var,
                    'correlacion': corr_val,
                    'p_val': p_val,
                    'n_obs': len(df_sub)
                })
                
    df_corrs_all = pd.DataFrame(corrs_list)
    df_corrs_all['abs_correlacion'] = df_corrs_all['correlacion'].abs()
    
    # Guardar CSV
    csv_out_path = tables_dir / "correlaciones_por_zona_nuevas_variables.csv"
    df_corrs_all.to_csv(csv_out_path, index=False, encoding='utf-8')
    print(f"[Export] Tabla de correlaciones guardada en: {csv_out_path}")
    
    print_step("7. Generación de Gráficos y Reportes por Zona")
    
    # 7.1 Generar matrices de correlación resumidas para cada zona
    variables_resumidas = [
        'suhi_day_c', 'green_pct', 'ndvi', 'dw_built_pct', 'dw_bare_pct',
        'distance_to_industry_osm_m', 'dist_to_green_core_m', 'elevation',
        'pop_density_ageb', 'acceso_verde_capita', 'indice_presion_urbana',
        'indice_vulnerabilidad_termica', 'built_green_ratio'
    ]
    
    for zone in choices:
        gdf_zone = gdf[gdf['zona_densidad'] == zone][variables_resumidas].dropna()
        corr_matrix = gdf_zone.corr(method='spearman')
        
        plt.figure(figsize=(12, 10), dpi=300)
        sns.heatmap(
            corr_matrix, 
            annot=True, 
            cmap="coolwarm", 
            fmt=".2f", 
            vmin=-1, 
            vmax=1, 
            linewidths=0.5,
            cbar_kws={'label': 'Coeficiente de Spearman'}
        )
        
        # Traducir nombre de zona para el título del archivo
        safe_zone_name = zone.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("<", "baja_").replace(">=", "alta_").replace("-", "_")
        
        plt.title(f"Matriz de Correlación - {zone}\n(UHI Monterrey 2026 - Nuevas Variables)", fontsize=13, fontweight='bold', pad=15)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        fig_path = figures_dir / f"06_correlacion_{safe_zone_name}.png"
        plt.savefig(fig_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"        * Heatmap guardado en: {fig_path}")

    # 7.2 Gráfico multiescala: Cómo cambia la correlación con la escala del buffer por zona
    print("[Plots] Generando comparación de escalas de buffer...")
    buffer_green_cols = ['green_pct_250m', 'green_pct_500m', 'green_pct_1000m', 'green_pct_3000m']
    buffer_built_cols = ['dw_built_250m', 'dw_built_500m', 'dw_built_1000m', 'dw_built_3000m']
    
    scales_m = [250, 500, 1000, 3000]
    
    fig, axes = plt.subplots(1, 2, figsize=(16, 6), sharey=False, dpi=300)
    colors = {'Baja Densidad (<20%)': '#2e7d32', 'Media Densidad (20-60%)': '#f57c00', 'Alta Densidad (>=60%)': '#d84315'}
    
    # Panel Izquierdo: Green Buffer
    ax_green = axes[0]
    for zone in choices:
        zone_corrs = []
        for col in buffer_green_cols:
            c = df_corrs_all[(df_corrs_all['zona'] == zone) & (df_corrs_all['variable'] == col)]['correlacion'].values[0]
            zone_corrs.append(c)
        ax_green.plot(scales_m, zone_corrs, marker='o', linewidth=2.5, label=zone, color=colors[zone])
    ax_green.set_xscale('log')
    ax_green.set_xticks(scales_m)
    ax_green.get_xaxis().set_major_formatter(plt.ScalarFormatter())
    ax_green.set_title("Sensibilidad al Radio del Buffer de Vegetación (green_pct)", fontsize=11, fontweight='bold')
    ax_green.set_xlabel("Escala del Buffer (metros - Log)", fontsize=10)
    ax_green.set_ylabel("Correlación de Spearman con SUHI Diurno", fontsize=10)
    ax_green.grid(True, which="both", ls="--", alpha=0.5)
    ax_green.legend()
    
    # Panel Derecho: Built Buffer
    ax_built = axes[1]
    for zone in choices:
        zone_corrs = []
        for col in buffer_built_cols:
            c = df_corrs_all[(df_corrs_all['zona'] == zone) & (df_corrs_all['variable'] == col)]['correlacion'].values[0]
            zone_corrs.append(c)
        ax_built.plot(scales_m, zone_corrs, marker='s', linewidth=2.5, label=zone, color=colors[zone])
    ax_built.set_xscale('log')
    ax_built.set_xticks(scales_m)
    ax_built.get_xaxis().set_major_formatter(plt.ScalarFormatter())
    ax_built.set_title("Sensibilidad al Radio del Buffer Impermeable (dw_built_pct)", fontsize=11, fontweight='bold')
    ax_built.set_xlabel("Escala del Buffer (metros - Log)", fontsize=10)
    ax_built.set_ylabel("Correlación de Spearman con SUHI Diurno", fontsize=10)
    ax_built.grid(True, which="both", ls="--", alpha=0.5)
    ax_built.legend()
    
    plt.suptitle("Análisis Multiescala de Buffers Urbanos y Biofísicos por Zona de Densidad", fontsize=13, fontweight='bold', y=0.98)
    plt.tight_layout()
    fig_scale_path = figures_dir / "06_buffer_scales_comparison.png"
    plt.savefig(fig_scale_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"        * Gráfico multiescala guardado en: {fig_scale_path}")

    # 7.3 Análisis de Saturación Térmica en Alta Densidad
    print("[Plots] Generando gráfico de saturación térmica...")
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    
    # Tomar muestra para visualización rápida
    sample_df = gdf.sample(n=min(10000, len(gdf)), random_state=42)
    
    sns.scatterplot(
        data=sample_df, 
        x='dw_built_pct', 
        y='suhi_day_c', 
        hue='zona_densidad',
        palette=colors,
        alpha=0.4, 
        s=10, 
        ax=ax
    )
    
    # Línea de tendencia polinómica para mostrar la forma de la relación
    clean_all = gdf[['dw_built_pct', 'suhi_day_c']].dropna()
    poly_fit = np.polyfit(clean_all['dw_built_pct'], clean_all['suhi_day_c'], 2)
    poly_func = np.poly1d(poly_fit)
    x_line = np.linspace(0, 100, 100)
    y_line = poly_func(x_line)
    
    ax.plot(x_line, y_line, color='black', linestyle='--', linewidth=2, label='Tendencia General (Polinómica 2do Grado)')
    
    ax.set_title("Análisis de Saturación Térmica de la Densidad Construida (dw_built_pct)", fontsize=12, fontweight='bold', pad=15)
    ax.set_xlabel("Densidad Construida DW (%)", fontsize=11)
    ax.set_ylabel("Intensidad SUHI Diurna (°C)", fontsize=11)
    ax.axvline(x=60.0, color='red', linestyle=':', label='Límite de Alta Densidad (60%)')
    ax.legend(loc='lower right')
    ax.grid(True, alpha=0.3)
    
    fig_sat_path = figures_dir / "06_lst_saturation_analysis.png"
    plt.savefig(fig_sat_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"        * Gráfico de saturación guardado en: {fig_sat_path}")

    # 7.4 Mapa de Índices Derivados (Presión Urbana y Vulnerabilidad Térmica)
    print("[Plots] Generando mapa espacial de índices derivados...")
    fig, axes = plt.subplots(1, 2, figsize=(18, 8), dpi=300)
    
    # Mapear con Web Mercator para basemap
    gdf_sample_3857 = sample_df.to_crs(epsg=3857)
    
    # Mapa 1: Presión Urbana
    ax_pres = axes[0]
    sc1 = ax_pres.scatter(
        gdf_sample_3857.geometry.centroid.x, 
        gdf_sample_3857.geometry.centroid.y, 
        c=gdf_sample_3857['indice_presion_urbana'], 
        cmap='viridis', 
        s=4, 
        alpha=0.7
    )
    fig.colorbar(sc1, ax=ax_pres, label='Índice de Presión Urbana (built*2 - green)')
    ax_pres.set_title("Índice de Presión Urbana en la ZMM", fontsize=11, fontweight='bold')
    ax_pres.set_axis_off()
    
    # Mapa 2: Vulnerabilidad Térmica
    ax_vuln = axes[1]
    sc2 = ax_vuln.scatter(
        gdf_sample_3857.geometry.centroid.x, 
        gdf_sample_3857.geometry.centroid.y, 
        c=gdf_sample_3857['indice_vulnerabilidad_termica'], 
        cmap='YlOrRd', 
        s=4, 
        alpha=0.7
    )
    fig.colorbar(sc2, ax=ax_vuln, label='Índice de Vulnerabilidad Térmica')
    ax_vuln.set_title("Índice de Vulnerabilidad Térmica en la ZMM", fontsize=11, fontweight='bold')
    ax_vuln.set_axis_off()
    
    plt.suptitle("Distribución Espacial de Índices Socioambientales Derivados", fontsize=14, fontweight='bold', y=0.96)
    plt.tight_layout()
    fig_indices_path = figures_dir / "06_derived_indices_map.png"
    plt.savefig(fig_indices_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"        * Mapa de índices guardado en: {fig_indices_path}")

    # 7.5 Imprimir Top 5 de variables con mayor correlación absoluta para cada zona
    print_step("8. Resumen de Hallazgos por Región")
    for zone in choices:
        zone_df = df_corrs_all[df_corrs_all['zona'] == zone].sort_values(by='abs_correlacion', ascending=False)
        top_5 = zone_df.head(6)
        print(f"\n>>> Top 5 de variables con mayor correlación en: {zone}")
        rank = 1
        for _, row in top_5.iterrows():
            if row['variable'] == target_col:
                continue
            print(f"  {rank}. {row['variable']:.<35} Spearman r: {row['correlacion']:+.3f} (p={row['p_val']:.2e}, n={row['n_obs']})")
            rank += 1
                
    # Guardar GeoPackage final enriquecido para la siguiente etapa
    output_gpkg = processed_dir / "malla_modelado_multiescala_mty_enriquecida.gpkg"
    gdf.to_file(output_gpkg, driver="GPKG", mode="w")
    print(f"\n[Export] Malla enriquecida guardada en: {output_gpkg}")
    
    print("\nPROCESO COMPLETADO EXITOSAMENTE.")

def stats_spearman(x, y):
    """Calcula de forma rápida y robusta el coeficiente de Spearman y su valor p"""
    import scipy.stats as stats
    try:
        corr_val, p_val = stats.spearmanr(x, y)
        if np.isnan(corr_val):
            return 0.0, 1.0
        return float(corr_val), float(p_val)
    except Exception:
        df = pd.DataFrame({'x': x, 'y': y})
        corr_val = df['x'].corr(df['y'], method='spearman')
        return float(corr_val), 0.0

if __name__ == "__main__":
    main()
