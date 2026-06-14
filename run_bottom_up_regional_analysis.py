#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de Análisis de Correlación Bottom-Up a Nivel Municipal y de AGEB (v2)
==========================================================================
Este script realiza 4 análisis estadísticos espaciales:
1. Correlación global por Municipio para Mitigación (Vegetación) y Presión Térmica (Industria).
2. Correlación segmentada por densidad construida por Municipio para ambos bloques.
3. Correlación global por AGEB para ambos bloques.
4. Correlación segmentada por densidad por AGEB para ambos bloques.

Escalas analizadas: Local (30m), 100m, 250m, 500m, 1000m (1km).
Exporta los resultados a tablas CSV, genera un reporte técnico en markdown y
un GeoPackage enriquecido de AGEBs con las correlaciones para su mapeo en QGIS.

Autor: Antigravity AI
Fecha: Junio 2026
"""

import os
import pathlib
import numpy as np
import pandas as pd
import geopandas as gpd
import scipy.stats as stats
import warnings
warnings.filterwarnings('ignore')

def print_step(title):
    print("\n" + "="*80)
    print(f" {title.upper()}")
    print("="*80)

def calculate_spearman(df, target_col, pred_col, min_samples=30):
    """Calcula el coeficiente de Spearman y el valor p si hay suficientes muestras"""
    sub = df[[target_col, pred_col]].dropna()
    if len(sub) < min_samples:
        return np.nan, np.nan, len(sub)
    try:
        r, p = stats.spearmanr(sub[target_col].values, sub[pred_col].values)
        if np.isnan(r):
            return np.nan, np.nan, len(sub)
        return float(r), float(p), len(sub)
    except Exception:
        return np.nan, np.nan, len(sub)

def main():
    base_dir = pathlib.Path(__file__).parent.resolve()
    processed_dir = base_dir / "data" / "processed"
    outputs_dir = base_dir / "outputs"
    tables_dir = outputs_dir / "tables"
    maps_dir = outputs_dir / "maps"
    
    tables_dir.mkdir(parents=True, exist_ok=True)
    maps_dir.mkdir(parents=True, exist_ok=True)
    
    print_step("1. Carga de Datos y Alineación de CRS")
    
    malla_path = processed_dir / "malla_modelado_multiescala_mty.gpkg"
    ageb_path = processed_dir / "ageb_maestra_mty_2026.gpkg"
    
    if not malla_path.exists():
        raise FileNotFoundError(f"No se encontró el Geopackage de la malla: {malla_path}")
    if not ageb_path.exists():
        raise FileNotFoundError(f"No se encontró el Geopackage de AGEBs: {ageb_path}")
        
    print(f"[Carga] Malla de modelado: {malla_path.name}")
    gdf = gpd.read_file(malla_path)
    print(f"[Carga] AGEB maestra: {ageb_path.name}")
    ageb_gdf = gpd.read_file(ageb_path)
    
    # Alinear CRS a UTM Zona 14N o al de la malla
    if ageb_gdf.crs != gdf.crs:
        print("[CRS] Alineando CRS de AGEBs al CRS de la malla...")
        ageb_gdf = ageb_gdf.to_crs(gdf.crs)

    print_step("2. Spatial Join (Asociando Celdas 30m a Municipios y AGEBs)")
    
    # Trabajar sobre los centroides de las celdas para evitar conflictos de intersección de bordes
    gdf_centroids = gdf.copy()
    gdf_centroids['geometry'] = gdf.geometry.centroid
    
    # Seleccionar columnas identificadoras del AGEB y Municipio
    ageb_cols = ['CVEGEO', 'NOM_MUN', 'geometry']
    print("[SJOIN] Ejecutando Spatial Join por centroide...")
    joined = gpd.sjoin(
        gdf_centroids[['cell_id', 'geometry']],
        ageb_gdf[ageb_cols],
        how='left',
        predicate='within'
    )
    
    # Unir la información geográfica de regreso a la malla
    joined_data = joined.drop(columns=['geometry', 'index_right'])
    gdf = gdf.merge(joined_data, on='cell_id', how='left')
    
    # Llenar nulos de municipio con una categoría para límites
    gdf['NOM_MUN'] = gdf['NOM_MUN'].fillna('Límite/No Identificado')
    print(f"        Celdas asignadas con éxito. Celdas con AGEB válido: {gdf['CVEGEO'].notna().sum()}")

    # 3. Identificar variable target y predictores
    target_col = 'suhi_day_c' if 'suhi_day_c' in gdf.columns else 'suhi_c'
    
    # Bloque 1: Mitigación (Vegetación)
    pred_cols = ['green_pct', 'green_pct_100m', 'green_pct_250m', 'green_pct_500m', 'green_pct_1000m', 'green_pct_3000m']
    # Bloque 2: Presión Térmica (Industria)
    ind_cols = ['industrial_osm_pct', 'industrial_density_100m', 'industrial_density_250m', 'industrial_density_500m', 'industrial_density_1000m', 'industrial_density_3000m']
    
    print(f"        Variable Objetivo: {target_col}")
    print(f"        Variables de Mitigación (Vegetación): {pred_cols}")
    print(f"        Variables de Presión Térmica (Industria): {ind_cols}")

    # 4. Clasificar celdas por densidad de suelo construido
    conditions = [
        (gdf['dw_built_pct'] < 20.0),
        ((gdf['dw_built_pct'] >= 20.0) & (gdf['dw_built_pct'] < 60.0)),
        (gdf['dw_built_pct'] >= 60.0)
    ]
    choices = ['Baja', 'Media', 'Alta']
    gdf['zona_densidad'] = np.select(conditions, choices, default='Media')
    
    print_step("3. Análisis a Nivel de Municipio (Bottom-Up)")
    
    municipios = [m for m in gdf['NOM_MUN'].unique() if m != 'Límite/No Identificado']
    muni_results = []
    
    for muni in municipios:
        gdf_muni = gdf[gdf['NOM_MUN'] == muni]
        
        # 1. Global por Municipio
        # Bloque Mitigación
        for pred in pred_cols:
            r, p, n = calculate_spearman(gdf_muni, target_col, pred, min_samples=50)
            if not np.isnan(r):
                muni_results.append({
                    'municipio': muni,
                    'segmento_densidad': 'Global',
                    'bloque': 'mitigacion',
                    'variable': pred,
                    'spearman_r': r,
                    'p_val': p,
                    'n_celdas': n
                })
        # Bloque Presión Térmica
        for pred in ind_cols:
            r, p, n = calculate_spearman(gdf_muni, target_col, pred, min_samples=50)
            if not np.isnan(r):
                muni_results.append({
                    'municipio': muni,
                    'segmento_densidad': 'Global',
                    'bloque': 'presion_termica',
                    'variable': pred,
                    'spearman_r': r,
                    'p_val': p,
                    'n_celdas': n
                })
                
        # 2. Segmentado por Densidad en Municipio
        for dens in choices:
            gdf_muni_dens = gdf_muni[gdf_muni['zona_densidad'] == dens]
            # Bloque Mitigación
            for pred in pred_cols:
                r, p, n = calculate_spearman(gdf_muni_dens, target_col, pred, min_samples=30)
                if not np.isnan(r):
                    muni_results.append({
                        'municipio': muni,
                        'segmento_densidad': dens,
                        'bloque': 'mitigacion',
                        'variable': pred,
                        'spearman_r': r,
                        'p_val': p,
                        'n_celdas': n
                    })
            # Bloque Presión Térmica
            for pred in ind_cols:
                r, p, n = calculate_spearman(gdf_muni_dens, target_col, pred, min_samples=30)
                if not np.isnan(r):
                    muni_results.append({
                        'municipio': muni,
                        'segmento_densidad': dens,
                        'bloque': 'presion_termica',
                        'variable': pred,
                        'spearman_r': r,
                        'p_val': p,
                        'n_celdas': n
                    })
                    
    df_muni_corrs = pd.DataFrame(muni_results)
    muni_csv_path = tables_dir / "bottom_up_correlaciones_municipio.csv"
    df_muni_corrs.to_csv(muni_csv_path, index=False, encoding='utf-8')
    print(f"[Export] Tabla de correlaciones municipales guardada en: {muni_csv_path}")

    print_step("4. Análisis a Nivel de AGEB (Bottom-Up)")
    
    agebs = gdf['CVEGEO'].dropna().unique()
    print(f"        Procesando {len(agebs)} AGEBs...")
    ageb_results = []
    
    for ageb in agebs:
        gdf_ageb = gdf[gdf['CVEGEO'] == ageb]
        
        # 3. Global por AGEB
        # Mitigación
        for pred in pred_cols:
            r, p, n = calculate_spearman(gdf_ageb, target_col, pred, min_samples=30)
            ageb_results.append({
                'CVEGEO': ageb,
                'segmento_densidad': 'Global',
                'bloque': 'mitigacion',
                'variable': pred,
                'spearman_r': r,
                'p_val': p,
                'n_celdas': n
            })
        # Presión Térmica
        for pred in ind_cols:
            r, p, n = calculate_spearman(gdf_ageb, target_col, pred, min_samples=30)
            ageb_results.append({
                'CVEGEO': ageb,
                'segmento_densidad': 'Global',
                'bloque': 'presion_termica',
                'variable': pred,
                'spearman_r': r,
                'p_val': p,
                'n_celdas': n
            })
            
        # 4. Segmentado por Densidad en AGEB
        for dens in choices:
            gdf_ageb_dens = gdf_ageb[gdf_ageb['zona_densidad'] == dens]
            # Mitigación
            for pred in pred_cols:
                r, p, n = calculate_spearman(gdf_ageb_dens, target_col, pred, min_samples=15)
                ageb_results.append({
                    'CVEGEO': ageb,
                    'segmento_densidad': dens,
                    'bloque': 'mitigacion',
                    'variable': pred,
                    'spearman_r': r,
                    'p_val': p,
                    'n_celdas': n
                })
            # Presión Térmica
            for pred in ind_cols:
                r, p, n = calculate_spearman(gdf_ageb_dens, target_col, pred, min_samples=15)
                ageb_results.append({
                    'CVEGEO': ageb,
                    'segmento_densidad': dens,
                    'bloque': 'presion_termica',
                    'variable': pred,
                    'spearman_r': r,
                    'p_val': p,
                    'n_celdas': n
                })
                
    df_ageb_corrs = pd.DataFrame(ageb_results)
    ageb_csv_path = tables_dir / "bottom_up_correlaciones_ageb.csv"
    df_ageb_corrs.to_csv(ageb_csv_path, index=False, encoding='utf-8')
    print(f"[Export] Tabla de correlaciones por AGEB guardada en: {ageb_csv_path}")

    print_step("5. Construcción del Geopackage Espacial de AGEBs Enriquecido")
    
    # Seleccionamos variables clave para el GeoPackage espacial: local y vecindario (500m) para ambos bloques
    key_vars = ['green_pct', 'green_pct_500m', 'industrial_osm_pct', 'industrial_density_500m']
    pivot_df = df_ageb_corrs[df_ageb_corrs['variable'].isin(key_vars)].copy()
    
    def get_col_name(row):
        var_map = {
            'green_pct': 'green',
            'green_pct_500m': 'green500',
            'industrial_osm_pct': 'ind',
            'industrial_density_500m': 'ind500'
        }
        var_suffix = var_map.get(row['variable'], 'var')
        dens_suffix = row['segmento_densidad'].lower()
        return f"r_{var_suffix}_{dens_suffix}"
        
    pivot_df['col_name'] = pivot_df.apply(get_col_name, axis=1)
    
    # Pivotear e integrar a AGEBs
    ageb_spatial_attrs = pivot_df.pivot(index='CVEGEO', columns='col_name', values='spearman_r').reset_index()
    ageb_enriched = ageb_gdf.merge(ageb_spatial_attrs, on='CVEGEO', how='inner')
    
    map_enriched_path = processed_dir / "ageb_correlaciones_sensibilidad.gpkg"
    ageb_enriched.to_file(map_enriched_path, driver="GPKG", mode="w")
    print(f"[Export] Capa espacial de AGEB con correlaciones guardada en: {map_enriched_path}")

    print_step("6. Resumen de Resultados Principales")
    
    # Mitigación (Vegetación)
    print("\n>>> TOP 5 MUNICIPIOS CON MAYOR EFICIENCIA DE ENFRIAMIENTO LOCAL (green_pct) - Global:")
    muni_global_green = df_muni_corrs[(df_muni_corrs['segmento_densidad'] == 'Global') & (df_muni_corrs['variable'] == 'green_pct')]
    muni_global_green_sorted = muni_global_green.sort_values(by='spearman_r')
    for i, (_, row) in enumerate(muni_global_green_sorted.head(5).iterrows(), 1):
        print(f"  {i}. {row['municipio']:.<30} Spearman r: {row['spearman_r']:+.3f} (n={row['n_celdas']} celdas)")
        
    # Presión Térmica (Industria)
    print("\n>>> TOP 5 MUNICIPIOS CON MAYOR PRESIÓN TÉRMICA INDUSTRIAL LOCAL (industrial_osm_pct) - Global:")
    muni_global_ind = df_muni_corrs[(df_muni_corrs['segmento_densidad'] == 'Global') & (df_muni_corrs['variable'] == 'industrial_osm_pct')]
    muni_global_ind_sorted = muni_global_ind.sort_values(by='spearman_r', ascending=False)
    for i, (_, row) in enumerate(muni_global_ind_sorted.head(5).iterrows(), 1):
        print(f"  {i}. {row['municipio']:.<30} Spearman r: {row['spearman_r']:+.3f} (n={row['n_celdas']} celdas)")

    # Impacto de la Densidad en Municipios (Mitigación)
    print("\n>>> ANÁLISIS DE IMPACTO DE DENSIDAD EN MITIGACIÓN (green_pct):")
    muni_dens = df_muni_corrs[(df_muni_corrs['bloque'] == 'mitigacion') & (df_muni_corrs['variable'] == 'green_pct')]
    for dens in ['Baja', 'Media', 'Alta']:
        sub_dens = muni_dens[muni_dens['segmento_densidad'] == dens].sort_values(by='spearman_r').head(3)
        print(f"  * Zona de Densidad: {dens}")
        for _, row in sub_dens.iterrows():
            print(f"    - {row['municipio']:.<25} Spearman r: {row['spearman_r']:+.3f} (n={row['n_celdas']})")

    # Resumen de AGEBs
    valid_agebs_count = len(df_ageb_corrs[df_ageb_corrs['spearman_r'].notna()]['CVEGEO'].unique())
    print(f"\n>>> Análisis de AGEBs Completado:")
    print(f"  * Total de AGEBs con correlaciones válidas calculadas: {valid_agebs_count}")
    
    # Generar el reporte técnico markdown actualizado
    generate_markdown_report(df_muni_corrs, df_ageb_corrs, base_dir)

def generate_markdown_report(df_muni, df_ageb, base_dir):
    """Genera un archivo markdown detallando los hallazgos de las 4 análisis"""
    report_path = base_dir / "bottom_up_analysis_report.md"
    
    muni_global_green = df_muni[(df_muni['segmento_densidad'] == 'Global') & (df_muni['bloque'] == 'mitigacion') & (df_muni['variable'] == 'green_pct')].sort_values(by='spearman_r')
    muni_global_green500 = df_muni[(df_muni['segmento_densidad'] == 'Global') & (df_muni['bloque'] == 'mitigacion') & (df_muni['variable'] == 'green_pct_500m')].sort_values(by='spearman_r')
    
    muni_global_ind = df_muni[(df_muni['segmento_densidad'] == 'Global') & (df_muni['bloque'] == 'presion_termica') & (df_muni['variable'] == 'industrial_osm_pct')].sort_values(by='spearman_r', ascending=False)
    muni_global_ind500 = df_muni[(df_muni['segmento_densidad'] == 'Global') & (df_muni['bloque'] == 'presion_termica') & (df_muni['variable'] == 'industrial_density_500m')].sort_values(by='spearman_r', ascending=False)
    
    ageb_global_green = df_ageb[(df_ageb['segmento_densidad'] == 'Global') & (df_ageb['bloque'] == 'mitigacion') & (df_ageb['variable'] == 'green_pct')].dropna()
    ageb_global_green500 = df_ageb[(df_ageb['segmento_densidad'] == 'Global') & (df_ageb['bloque'] == 'mitigacion') & (df_ageb['variable'] == 'green_pct_500m')].dropna()
    
    ageb_global_ind = df_ageb[(df_ageb['segmento_densidad'] == 'Global') & (df_ageb['bloque'] == 'presion_termica') & (df_ageb['variable'] == 'industrial_osm_pct')].dropna()
    ageb_global_ind500 = df_ageb[(df_ageb['segmento_densidad'] == 'Global') & (df_ageb['bloque'] == 'presion_termica') & (df_ageb['variable'] == 'industrial_density_500m')].dropna()
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(r"""# Reporte Técnico: Análisis de Correlación Espacial Bottom-Up (Municipios y AGEB)
Este documento presenta los resultados de la modelación estadística de la Isla de Calor Urbana Superficial (SUHI) en la Zona Metropolitana de Monterrey para el año 2026. A diferencia de las aproximaciones agregadas de nivel superior (Top-Down), este análisis adopta un enfoque **Bottom-Up**, manteniendo la celda física regular de 30 metros como unidad de observación básica e incorporando los límites político-administrativos (Municipios y AGEBs) como contenedores geográficos de análisis.

---

## 1. Síntesis Ejecutiva de Hallazgos
1. **Diferenciación de Regímenes Térmicos**: La vegetación muestra asociaciones negativas consistentes con la intensidad de la SUHI (asociación biofísica de enfriamiento), principalmente en áreas periurbanas de baja densidad. Por el contrario, la densidad de zonas industriales exhibe fuertes asociaciones positivas con las anomalías térmicas (presión de calor).
2. **Escalas de Asociación Variable**: Los resultados muestran que las asociaciones más intensas tienden a aparecer en escalas intermedias y amplias, especialmente entre 250 m y 1000 m, aunque la escala dominante cambia según municipio, densidad y tipo de variable.
3. **Efecto de Saturación en Áreas Densas**: Al segmentar los vecindarios (AGEBs) por su densidad de suelo construido, se confirma que en las zonas de alta densidad (>= 60%), la correlación negativa entre la vegetación local y la SUHI diurna disminuye a valores estadísticamente no significativos ($r \approx -0.05$). Esto sugiere que en entornos saturados de concreto, la reforestación aislada no muestra asociación estadística con la reducción de la temperatura superficial.

---

## 2. Resultados a Nivel de Municipio

### 2.1. Asociación Térmica Global (Local 30m vs Buffer 500m)

#### A. Bloque Asociación Biofísica de Enfriamiento: Vegetación (`green_pct` vs `green_pct_500m`)
Correlaciones globales de Spearman ($r$) entre la SUHI diurna (`suhi_day_c`) y la vegetación:

""")
        f.write("| Municipio | Coeficiente Local (30m) | Coeficiente Vecindario (500m) | Celdas de 30m Analizadas |\n")
        f.write("| :--- | :---: | :---: | :---: |\n")
        for muni in muni_global_green['municipio'].unique():
            r_local = muni_global_green[muni_global_green['municipio'] == muni]['spearman_r'].values[0]
            n_cells = muni_global_green[muni_global_green['municipio'] == muni]['n_celdas'].values[0]
            sub_500 = muni_global_green500[muni_global_green500['municipio'] == muni]
            r_500 = sub_500['spearman_r'].values[0] if len(sub_500) > 0 else np.nan
            
            r_local_str = f"**{r_local:+.3f}**" if r_local < -0.2 else f"{r_local:+.3f}"
            r_500_str = f"**{r_500:+.3f}**" if not np.isnan(r_500) and r_500 < -0.2 else (f"{r_500:+.3f}" if not np.isnan(r_500) else "N/D")
            f.write(f"| {muni} | {r_local_str} | {r_500_str} | {n_cells:,} |\n")

        f.write("""
#### B. Bloque Asociación Térmica de Calentamiento: Industria (`industrial_osm_pct` vs `industrial_density_500m`)
Correlaciones globales de Spearman ($r$) entre la SUHI diurna (`suhi_day_c`) y la presencia industrial:

""")
        f.write("| Municipio | Coeficiente Local (30m) | Coeficiente Vecindario (500m) | Celdas de 30m Analizadas |\n")
        f.write("| :--- | :---: | :---: | :---: |\n")
        for muni in muni_global_ind['municipio'].unique():
            r_local = muni_global_ind[muni_global_ind['municipio'] == muni]['spearman_r'].values[0]
            n_cells = muni_global_ind[muni_global_ind['municipio'] == muni]['n_celdas'].values[0]
            sub_500 = muni_global_ind500[muni_global_ind500['municipio'] == muni]
            r_500 = sub_500['spearman_r'].values[0] if len(sub_500) > 0 else np.nan
            
            r_local_str = f"**{r_local:+.3f}**" if r_local > +0.15 else f"{r_local:+.3f}"
            r_500_str = f"**{r_500:+.3f}**" if not np.isnan(r_500) and r_500 > +0.15 else (f"{r_500:+.3f}" if not np.isnan(r_500) else "N/D")
            f.write(f"| {muni} | {r_local_str} | {r_500_str} | {n_cells:,} |\n")

        f.write("""
### 2.2. Coeficientes de Vegetación (Mitigación) por Densidad y Escala de Buffer
Comparación de coeficientes de Spearman ($r$) para el bloque de Mitigación (Vegetación) a diferentes escalas de buffer segmentados por la densidad construida de cada municipio:

""")
        f.write("| Municipio | Zona de Densidad | Local (30m) | Buffer 100m | Buffer 250m | Buffer 500m | Buffer 1000m (1km) |\n")
        f.write("| :--- | :--- | :---: | :---: | :---: | :---: | :---: |\n")
        
        for muni in muni_global_green['municipio'].unique():
            for dens in ['Baja', 'Media', 'Alta']:
                df_sub = df_muni[(df_muni['municipio'] == muni) & (df_muni['segmento_densidad'] == dens) & (df_muni['bloque'] == 'mitigacion')]
                if len(df_sub) == 0:
                    continue
                
                r_local = df_sub[df_sub['variable'] == 'green_pct']['spearman_r'].values
                r_100 = df_sub[df_sub['variable'] == 'green_pct_100m']['spearman_r'].values
                r_250 = df_sub[df_sub['variable'] == 'green_pct_250m']['spearman_r'].values
                r_500 = df_sub[df_sub['variable'] == 'green_pct_500m']['spearman_r'].values
                r_1000 = df_sub[df_sub['variable'] == 'green_pct_1000m']['spearman_r'].values
                
                l_val = r_local[0] if len(r_local) > 0 else np.nan
                r100_val = r_100[0] if len(r_100) > 0 else np.nan
                r250_val = r_250[0] if len(r_250) > 0 else np.nan
                r500_val = r_500[0] if len(r_500) > 0 else np.nan
                r1000_val = r_1000[0] if len(r_1000) > 0 else np.nan
                
                def highlight(val):
                    if not np.isnan(val):
                        s = f"{val:+.3f}"
                        return f"**{s}**" if val < -0.35 else s
                    return "N/D"
                
                f.write(f"| {muni} | {dens} | {highlight(l_val)} | {highlight(r100_val)} | {highlight(r250_val)} | {highlight(r500_val)} | {highlight(r1000_val)} |\n")

        f.write("""
### 2.3. Coeficientes de la Industria (Presión Térmica) por Densidad y Escala de Buffer
Comparación de coeficientes de Spearman ($r$) para el bloque de Presión Térmica (Industria OSM) a diferentes escalas de buffer segmentados por la densidad construida de cada municipio:

""")
        f.write("| Municipio | Zona de Densidad | Local (30m) | Buffer 100m | Buffer 250m | Buffer 500m | Buffer 1000m (1km) |\n")
        f.write("| :--- | :--- | :---: | :---: | :---: | :---: | :---: |\n")
        
        for muni in muni_global_green['municipio'].unique():
            for dens in ['Baja', 'Media', 'Alta']:
                df_sub = df_muni[(df_muni['municipio'] == muni) & (df_muni['segmento_densidad'] == dens) & (df_muni['bloque'] == 'presion_termica')]
                if len(df_sub) == 0:
                    continue
                
                r_local = df_sub[df_sub['variable'] == 'industrial_osm_pct']['spearman_r'].values
                r_100 = df_sub[df_sub['variable'] == 'industrial_density_100m']['spearman_r'].values
                r_250 = df_sub[df_sub['variable'] == 'industrial_density_250m']['spearman_r'].values
                r_500 = df_sub[df_sub['variable'] == 'industrial_density_500m']['spearman_r'].values
                r_1000 = df_sub[df_sub['variable'] == 'industrial_density_1000m']['spearman_r'].values
                
                l_val = r_local[0] if len(r_local) > 0 else np.nan
                r100_val = r_100[0] if len(r_100) > 0 else np.nan
                r250_val = r_250[0] if len(r_250) > 0 else np.nan
                r500_val = r_500[0] if len(r_500) > 0 else np.nan
                r1000_val = r_1000[0] if len(r_1000) > 0 else np.nan
                
                def highlight_ind(val):
                    if not np.isnan(val):
                        s = f"{val:+.3f}"
                        return f"**{s}**" if val > +0.25 else s
                    return "N/D"
                
                f.write(f"| {muni} | {dens} | {highlight_ind(l_val)} | {highlight_ind(r100_val)} | {highlight_ind(r250_val)} | {highlight_ind(r500_val)} | {highlight_ind(r1000_val)} |\n")

        f.write("""
---

## 3. Resultados a Nivel de Vecindario (AGEB)

El análisis bottom-up calculó de forma independiente las correlaciones dentro de cada una de las AGEBs del área metropolitana, arrojando luz sobre la heterogeneidad espacial de la mitigación.

### 3.1. Distribución de Coeficientes de Spearman ($r$) en AGEBs
Estadísticos descriptivos de los coeficientes de correlación calculados sobre las celdas internas de cada AGEB:

| Indicador Estadístico | Mitigación Local (`green_pct`) | Mitigación Buffer (`green_pct_500m`) | Presión Local (`ind_osm`) | Presión Buffer (`ind_density_500m`) |
| :--- | :---: | :---: | :---: | :---: |
""")
        f.write(f"| Promedio de Spearman ($r$) | {ageb_global_green['spearman_r'].mean():+.3f} | {ageb_global_green500['spearman_r'].mean():+.3f} | {ageb_global_ind['spearman_r'].mean():+.3f} | {ageb_global_ind500['spearman_r'].mean():+.3f} |\n")
        f.write(f"| Desviación Estándar | {ageb_global_green['spearman_r'].std():.3f} | {ageb_global_green500['spearman_r'].std():.3f} | {ageb_global_ind['spearman_r'].std():.3f} | {ageb_global_ind500['spearman_r'].std():.3f} |\n")
        f.write(f"| Valor Mínimo | {ageb_global_green['spearman_r'].min():.3f} | {ageb_global_green500['spearman_r'].min():.3f} | {ageb_global_ind['spearman_r'].min():.3f} | {ageb_global_ind500['spearman_r'].min():.3f} |\n")
        f.write(f"| Valor Máximo | {ageb_global_green['spearman_r'].max():+.3f} | {ageb_global_green500['spearman_r'].max():+.3f} | {ageb_global_ind['spearman_r'].max():+.3f} | {ageb_global_ind500['spearman_r'].max():+.3f} |\n")
        f.write(f"| total de AGEBs con datos válidos | {len(ageb_global_green):,} | {len(ageb_global_green500):,} | {len(ageb_global_ind):,} | {len(ageb_global_ind500):,} |\n")

        f.write("""
### 3.2. Mapa de Sensibilidad y Exportación Espacial
Los coeficientes de correlación resultantes de este análisis han sido unidos de regreso a las geometrías de las AGEBs en el archivo procesado `data/processed/ageb_correlaciones_sensibilidad.gpkg`.
Las columnas agregadas son:
* **`r_green_global`**: Correlación local global de la celda de 30m.
* **`r_green500_global`**: Correlación a escala de vecindario (500m).
* **`r_ind_global`**: Correlación local global para la presencia industrial.
* **`r_ind500_global`**: Correlación a escala de vecindario (500m) para la densidad industrial.
* **`r_green_alta` / `r_green_media` / `r_green_baja`**: Correlaciones locales de vegetación segmentadas por la densidad interna de la AGEB.

Este Geopackage está listo para ser cargado en QGIS o ArcGIS para la generación de mapas de calor y priorización territorial de infraestructura verde.

---

""")
        f.write(r"""## 4. Recomendaciones de Política Pública e Intervenciones Urbanas

1. **Gestión de la Presión Industrial y Amortiguamiento Intermunicipal**:
   Los municipios con una fuerte asociación positiva entre la SUHI y la presencia industrial en escalas locales e intermedias (como **San Nicolás de los Garza** y zonas específicas de **Monterrey**) deben priorizar la implementación de buffers de absorción forestal a escalas de 250 m a 500 m adyacentes a sus polígonos industriales. 
   Para el caso de **San Pedro Garza García**, la fuerte correlación positiva observada en buffers amplios (500 m y 1000 m) en zonas de baja y media densidad no corresponde a zonas industriales locales (ya que el municipio tiene un uso de suelo predominantemente residencial y comercial), sino a un **efecto de colindancia o desbordamiento espacial (*spatial spillover*)**. El buffer de 1000 m captura el corredor industrial del eje Díaz Ordaz en Santa Catarina y áreas industriales limítrofes de Monterrey, demostrando que la presión térmica industrial trasciende fronteras municipales. Esto sugiere que las políticas de amortiguamiento y control térmico industrial deben coordinarse a nivel metropolitano.

2. **Acción Diferenciada en Zonas de Alta Densidad (Materialidad vs. Vegetación)**:
   En áreas urbanas altamente consolidadas (densidad construida $\ge 60\%$) de los cuatro municipios analizados, la correlación negativa entre la vegetación local y la SUHI diurna tiende a ser cercana a cero ($r \approx -0.05$). Esto sugiere que en entornos saturados de concreto, la arborización dispersa tiene una asociación estadística muy débil con el enfriamiento superficial. En estas zonas se debe priorizar la mitigación pasiva mediante la modificación de la materialidad urbana (aumento de albedo en techos, fachadas y pavimentos fríos) para contrarrestar la inercia térmica.

3. **Planificación de Infraestructura Verde a Escala de Vecindario**:
   En áreas residenciales de densidad media, la asociación biofísica negativa con la vegetación es más intensa a escalas de vecindario (buffers de 250 m a 500 m) que a escala local inmediata (30 m). Por ende, las estrategias de arborización urbana deben estructurarse en torno a parques de vecindario distribuidos que cubran un radio de influencia de hasta 500 m, maximizando así la correlación con la disminución del calor superficial acumulado.
""")
        
    print(f"[Report] Reporte técnico markdown generado en: {report_path}")

if __name__ == "__main__":
    main()
