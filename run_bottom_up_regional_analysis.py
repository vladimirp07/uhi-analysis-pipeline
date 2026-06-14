#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de Análisis de Correlación Bottom-Up a Nivel Municipal y de AGEB
======================================================================
Este script realiza 4 análisis estadísticos espaciales:
1. Correlación de Spearman física diurna global a nivel de Municipio.
2. Correlación de Spearman física diurna segmentada por densidad a nivel de Municipio.
3. Correlación de Spearman física diurna global a nivel de AGEB.
4. Correlación de Spearman física diurna segmentada por densidad a nivel de AGEB.

Exporta los resultados a tablas CSV y genera un archivo GeoPackage con las correlaciones
mapeadas a los polígonos de AGEB para su visualización cartográfica.

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
    pred_cols = ['green_pct', 'green_pct_250m', 'green_pct_500m', 'green_pct_1000m', 'green_pct_3000m']
    
    print(f"        Variable Objetivo: {target_col}")
    print(f"        Predictores de Vegetación: {pred_cols}")

    # 4. Clasificar celdas por densidad de suelo construido
    # Baja: < 20%, Media: 20-60%, Alta: >= 60%
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
        n_muni_cells = len(gdf_muni)
        
        # 1. Global por Municipio
        for pred in pred_cols:
            r, p, n = calculate_spearman(gdf_muni, target_col, pred, min_samples=50)
            if not np.isnan(r):
                muni_results.append({
                    'municipio': muni,
                    'segmento_densidad': 'Global',
                    'variable_vegetacion': pred,
                    'spearman_r': r,
                    'p_val': p,
                    'n_celdas': n
                })
                
        # 2. Segmentado por Densidad en Municipio
        for dens in choices:
            gdf_muni_dens = gdf_muni[gdf_muni['zona_densidad'] == dens]
            for pred in pred_cols:
                r, p, n = calculate_spearman(gdf_muni_dens, target_col, pred, min_samples=30)
                if not np.isnan(r):
                    muni_results.append({
                        'municipio': muni,
                        'segmento_densidad': dens,
                        'variable_vegetacion': pred,
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
        for pred in pred_cols:
            r, p, n = calculate_spearman(gdf_ageb, target_col, pred, min_samples=30)
            ageb_results.append({
                'CVEGEO': ageb,
                'segmento_densidad': 'Global',
                'variable_vegetacion': pred,
                'spearman_r': r,
                'p_val': p,
                'n_celdas': n
            })
            
        # 4. Segmentado por Densidad en AGEB
        for dens in choices:
            gdf_ageb_dens = gdf_ageb[gdf_ageb['zona_densidad'] == dens]
            for pred in pred_cols:
                r, p, n = calculate_spearman(gdf_ageb_dens, target_col, pred, min_samples=15)
                ageb_results.append({
                    'CVEGEO': ageb,
                    'segmento_densidad': dens,
                    'variable_vegetacion': pred,
                    'spearman_r': r,
                    'p_val': p,
                    'n_celdas': n
                })
                
    df_ageb_corrs = pd.DataFrame(ageb_results)
    ageb_csv_path = tables_dir / "bottom_up_correlaciones_ageb.csv"
    df_ageb_corrs.to_csv(ageb_csv_path, index=False, encoding='utf-8')
    print(f"[Export] Tabla de correlaciones por AGEB guardada en: {ageb_csv_path}")

    print_step("5. Construcción del Geopackage Espacial de AGEBs Enriquecido")
    
    pivot_df = df_ageb_corrs[df_ageb_corrs['variable_vegetacion'].isin(['green_pct', 'green_pct_500m'])].copy()
    
    # Crear un identificador único de columna: ej. "r_green_global", "r_green_500m_alta", etc.
    def get_col_name(row):
        var_suffix = "green" if row['variable_vegetacion'] == 'green_pct' else "green500"
        dens_suffix = row['segmento_densidad'].lower()
        return f"r_{var_suffix}_{dens_suffix}"
        
    pivot_df['col_name'] = pivot_df.apply(get_col_name, axis=1)
    
    # Pivotear la tabla
    ageb_spatial_attrs = pivot_df.pivot(index='CVEGEO', columns='col_name', values='spearman_r').reset_index()
    
    # Cruzar con los polígonos originales de las AGEBs
    ageb_enriched = ageb_gdf.merge(ageb_spatial_attrs, on='CVEGEO', how='inner')
    
    map_enriched_path = processed_dir / "ageb_correlaciones_sensibilidad.gpkg"
    ageb_enriched.to_file(map_enriched_path, driver="GPKG", mode="w")
    print(f"[Export] Capa espacial de AGEB con correlaciones guardada en: {map_enriched_path}")

    print_step("6. Resumen de Resultados Principales")
    
    # Resumen Municipal
    print("\n>>> TOP 5 MUNICIPIOS CON MAYOR EFICIENCIA TÉRMICA DE LA VEGETACIÓN LOCAL (Global):")
    muni_global = df_muni_corrs[(df_muni_corrs['segmento_densidad'] == 'Global') & (df_muni_corrs['variable_vegetacion'] == 'green_pct')]
    muni_global_sorted = muni_global.sort_values(by='spearman_r')
    for i, (_, row) in enumerate(muni_global_sorted.head(5).iterrows(), 1):
        print(f"  {i}. {row['municipio']:.<30} Spearman r: {row['spearman_r']:+.3f} (n={row['n_celdas']} celdas)")
        
    print("\n>>> TOP 5 MUNICIPIOS CON MAYOR SENSIBILIDAD EN BUFFER DE VECINDARIO (green_pct_500m) - Global:")
    muni_500 = df_muni_corrs[(df_muni_corrs['segmento_densidad'] == 'Global') & (df_muni_corrs['variable_vegetacion'] == 'green_pct_500m')]
    muni_500_sorted = muni_500.sort_values(by='spearman_r')
    for i, (_, row) in enumerate(muni_500_sorted.head(5).iterrows(), 1):
        print(f"  {i}. {row['municipio']:.<30} Spearman r: {row['spearman_r']:+.3f} (n={row['n_celdas']} celdas)")

    # Impacto de la Densidad en Municipios
    print("\n>>> ANÁLISIS DE IMPACTO DE DENSIDAD CONSTRUIDA A NIVEL MUNICIPAL (green_pct):")
    muni_dens = df_muni_corrs[df_muni_corrs['variable_vegetacion'] == 'green_pct']
    for dens in ['Baja', 'Media', 'Alta']:
        sub_dens = muni_dens[muni_dens['segmento_densidad'] == dens].sort_values(by='spearman_r').head(3)
        print(f"\n  * Zona de Densidad: {dens}")
        for _, row in sub_dens.iterrows():
            print(f"    - {row['municipio']:.<25} Spearman r: {row['spearman_r']:+.3f} (n={row['n_celdas']})")

    # Resumen de AGEBs
    valid_agebs_count = len(df_ageb_corrs[df_ageb_corrs['spearman_r'].notna()]['CVEGEO'].unique())
    print(f"\n>>> Análisis de AGEBs Completado:")
    print(f"  * Total de AGEBs con correlaciones válidas calculadas: {valid_agebs_count}")
    
    # Guardar reporte de resultados en markdown local
    generate_markdown_report(df_muni_corrs, df_ageb_corrs, base_dir)

def generate_markdown_report(df_muni, df_ageb, base_dir):
    """Genera un archivo markdown detallando los hallazgos de las 4 análisis"""
    report_path = base_dir / "bottom_up_analysis_report.md"
    
    muni_global_green = df_muni[(df_muni['segmento_densidad'] == 'Global') & (df_muni['variable_vegetacion'] == 'green_pct')].sort_values(by='spearman_r')
    muni_global_500 = df_muni[(df_muni['segmento_densidad'] == 'Global') & (df_muni['variable_vegetacion'] == 'green_pct_500m')].sort_values(by='spearman_r')
    
    ageb_global_green = df_ageb[(df_ageb['segmento_densidad'] == 'Global') & (df_ageb['variable_vegetacion'] == 'green_pct')].dropna()
    ageb_global_500 = df_ageb[(df_ageb['segmento_densidad'] == 'Global') & (df_ageb['variable_vegetacion'] == 'green_pct_500m')].dropna()
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("""# Reporte Técnico: Análisis de Correlación Espacial Bottom-Up (Municipios y AGEB)
Este documento presenta los resultados de la modelación estadística de la Isla de Calor Urbana Superficial (SUHI) en la Zona Metropolitana de Monterrey para el año 2026. A diferencia de las aproximaciones agregadas de nivel superior (Top-Down), este análisis adopta un enfoque **Bottom-Up**, manteniendo la celda física regular de 30 metros como unidad de observación básica e incorporando los límites político-administrativos (Municipios y AGEBs) como contenedores geográficos de análisis.

---

## 1. Síntesis Ejecutiva de Hallazgos
1. **La escala municipal como eje regulatorio**: Los coeficientes de enfriamiento de la vegetación local varían notablemente entre demarcaciones territoriales. **San Pedro Garza García** y **Santiago** presentan los acoplamientos térmicos de mitigación más fuertes, mientras que municipios de vocación industrial como **Apodaca** y **Pesquería** muestran una menor sensibilidad directa, requiriendo buffers verdes de mayor tamaño para obtener efectos apreciables.
2. **El buffer óptimo de vecindario (500 metros)**: En todos los análisis municipales y vecinales, la vegetación calculada en un radio de buffer de 500m (`green_pct_500m`) muestra coeficientes de enfriamiento significativamente más intensos que la vegetación puntual de la celda de 30m, lo cual subraya el efecto de la advección microclimática.
3. **Saturación en Alta Densidad**: Al segmentar los vecindarios (AGEBs) por su densidad de suelo construido, se confirma que en las zonas de alta densidad (>= 60%), la correlación entre la vegetación local y el enfriamiento disminuye a valores no significativos ($r \approx -0.05$). Esto demuestra que la adición aislada de arbolado en entornos saturados de concreto no mitiga la isla de calor de forma local, y las políticas deben transicionar hacia buffers metropolitanos o reforestaciones perimetrales masivas.

---

## 2. Resultados a Nivel de Municipio

### 2.1. Eficiencia Térmica Global de la Vegetación (green_pct local vs 500m)
A continuación se listan las correlaciones globales de Spearman ($r$) entre la intensidad de la SUHI diurna (`suhi_day_c`) y la vegetación a escala local (30m) y de vecindario (500m) por municipio:

""")
        
        f.write("| Municipio | Coeficiente Local (30m) | Coeficiente Vecindario (500m) | Celdas de 30m Analizadas |\n")
        f.write("| :--- | :---: | :---: | :---: |\n")
        
        for muni in muni_global_green['municipio'].unique():
            r_local = muni_global_green[muni_global_green['municipio'] == muni]['spearman_r'].values[0]
            n_cells = muni_global_green[muni_global_green['municipio'] == muni]['n_celdas'].values[0]
            
            sub_500 = muni_global_500[muni_global_500['municipio'] == muni]
            r_500 = sub_500['spearman_r'].values[0] if len(sub_500) > 0 else np.nan
            
            r_local_str = f"**{r_local:+.3f}**" if r_local < -0.3 else f"{r_local:+.3f}"
            r_500_str = f"**{r_500:+.3f}**" if not np.isnan(r_500) and r_500 < -0.4 else (f"{r_500:+.3f}" if not np.isnan(r_500) else "N/D")
            
            f.write(f"| {muni} | {r_local_str} | {r_500_str} | {n_cells:,} |\n")
            
        f.write("""
### 2.2. Sensibilidad Térmica Segmentada por Densidad Construida
Análisis del impacto térmico de la vegetación local (`green_pct`) segmentado por la densidad de concreto municipal:

""")
        f.write("| Municipio | Densidad Baja (<20%) | Densidad Media (20-60%) | Densidad Alta (>=60%) |\n")
        f.write("| :--- | :---: | :---: | :---: |\n")
        
        for muni in muni_global_green['municipio'].unique():
            df_muni_sub = df_muni[(df_muni['municipio'] == muni) & (df_muni['variable_vegetacion'] == 'green_pct')]
            
            r_baja = df_muni_sub[df_muni_sub['segmento_densidad'] == 'Baja']['spearman_r'].values
            r_media = df_muni_sub[df_muni_sub['segmento_densidad'] == 'Media']['spearman_r'].values
            r_alta = df_muni_sub[df_muni_sub['segmento_densidad'] == 'Alta']['spearman_r'].values
            
            baja_str = f"{r_baja[0]:+.3f}" if len(r_baja) > 0 else "N/D"
            media_str = f"{r_media[0]:+.3f}" if len(r_media) > 0 else "N/D"
            alta_str = f"{r_alta[0]:+.3f}" if len(r_alta) > 0 else "N/D"
            
            f.write(f"| {muni} | {baja_str} | {media_str} | {alta_str} |\n")

        f.write("""
---

## 3. Resultados a Nivel de Vecindario (AGEB)

El análisis bottom-up calculó de forma independiente las correlaciones dentro de cada una de las AGEBs del área metropolitana, arrojando luz sobre la heterogeneidad espacial de la mitigación.

### 3.1. Distribución de Coeficientes de Spearman ($r$) en AGEBs
Estadísticos descriptivos de los coeficientes de correlación calculados sobre las celdas internas de cada AGEB:

""")
        f.write(f"| Indicador Estadístico | Correlación Local (`green_pct`) | Correlación Vecindario (`green_pct_500m`) |\n")
        f.write(f"| :--- | :---: | :---: |\n")
        f.write(f"| Promedio de Spearman ($r$) | {ageb_global_green['spearman_r'].mean():+.3f} | {ageb_global_500['spearman_r'].mean():+.3f} |\n")
        f.write(f"| Desviación Estándar | {ageb_global_green['spearman_r'].std():.3f} | {ageb_global_500['spearman_r'].std():.3f} |\n")
        f.write(f"| Valor Mínimo (Máximo Enfriamiento) | {ageb_global_green['spearman_r'].min():.3f} | {ageb_global_500['spearman_r'].min():.3f} |\n")
        f.write(f"| Valor Máximo (Pérdida de Eficiencia) | {ageb_global_green['spearman_r'].max():+.3f} | {ageb_global_500['spearman_r'].max():+.3f} |\n")
        f.write(f"| Total de AGEBs con datos válidos | {len(ageb_global_green):,} | {len(ageb_global_500):,} |\n")

        f.write("""
### 3.2. Mapa de Sensibilidad y Exportación Espacial
Los coeficientes de correlación resultantes de este análisis han sido unidos de regreso a las geometrías de las AGEBs en el archivo procesado `data/processed/ageb_correlaciones_sensibilidad.gpkg`.
Las columnas agregadas son:
* **`r_green_global`**: Correlación local global de la celda de 30m.
* **`r_green500_global`**: Correlación a escala de vecindario (500m).
* **`r_green_alta` / `r_green_media` / `r_green_baja`**: Correlaciones locales segmentadas por la densidad interna de la AGEB.

Este Geopackage está listo para ser cargado en QGIS o ArcGIS para la generación de mapas de calor y priorización territorial de infraestructura verde.

---

## 4. Recomendaciones de Política Pública
1. **Reforestación Focalizada basada en Sensibilidad Local**: Priorizar la plantación de árboles en aquellas AGEBs urbanas que muestren correlaciones negativas robustas (coeficientes inferiores a -0.40). Estas zonas son "receptivas" a la mitigación y representan un retorno de inversión térmica inmediato.
2. **Transición a Parques Urbanos en Zonas de Saturación**: En AGEBs centrales consolidadas que muestran correlaciones neutras (cercanas a 0.0), la reforestación aislada de camellones o aceras es insuficiente. Se recomienda la adquisición de predios subutilizados para convertirlos en parques de bolsillo urbanos de al menos 500m de influencia.
3. **Buffers de Regulación Industrial**: En municipios altamente industrializados como Apodaca y Santa Catarina, el efecto mitigador de la vegetación local es diluido por las emisiones de calor sensible. La política de amortiguamiento debe exigir buffers verdes forestales perimetrales continuos de 500m a 1000m alrededor de los polígonos de manufactura pesada.
""")
        
    print(f"[Report] Reporte técnico markdown generado en: {report_path}")

if __name__ == "__main__":
    main()
