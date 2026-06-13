#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de Análisis de Correlación Espacial Avanzado para la SUHI de Monterrey
===========================================================================
Este script realiza dos análisis fundamentales:
1. Análisis de Efecto de Escala (MAUP) mediante correlación Spearman multiescala.
2. Regresión Geográficamente Ponderada (GWR) para evaluar la heterogeneidad espacial
   de la vegetación, la superficie construida y la industria sobre la SUHI.

Autor: Científico de Datos Geoespaciales Senior
Fecha: Junio 2026
"""

import os
import sys
import time
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
import contextily as ctx
import scipy.stats as stats
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.multitest import multipletests
from scipy.spatial import distance_matrix

# --- MONKEY PATCH PARA EVITAR COLINIALIDAD LOCAL CRÍTICA EN BUCLE DE ESTIMACIÓN GWR ---
import mgwr.gwr
import spglm.iwls
from scipy import linalg

def patched_compute_betas_gwr(y, x, wi):
    xT = (x * wi).T
    xtx = np.dot(xT, x)
    try:
        xtx_inv_xt = linalg.solve(xtx, xT)
    except (linalg.LinAlgError, ValueError):
        ridge = 1e-4 * np.eye(xtx.shape[0])
        xtx_inv_xt = linalg.solve(xtx + ridge, xT)
    betas = np.dot(xtx_inv_xt, y)
    return betas, xtx_inv_xt

mgwr.gwr._compute_betas_gwr = patched_compute_betas_gwr
spglm.iwls._compute_betas_gwr = patched_compute_betas_gwr
# ------------------------------------------------------------------------------------

from mgwr.gwr import GWR
from mgwr.sel_bw import Sel_BW

def print_step(step_num, title):
    print("\n" + "="*80)
    print(f"PASO {step_num}: {title.upper()}")
    print("="*80)

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # -------------------------------------------------------------------------
    # PARTE 1: ANÁLISIS DE EFECTO DE ESCALA (MAUP)
    # -------------------------------------------------------------------------
    print_step(1, "Análisis de Efecto de Escala (MAUP) - Correlaciones Spearman")
    
    gpkg_path = os.path.join(base_dir, "data", "processed", "malla_maestra_mty_2026_v2.gpkg")
    if not os.path.exists(gpkg_path):
        processed_dir = os.path.join(base_dir, "data", "processed")
        gpkg_files = [f for f in os.listdir(processed_dir) if f.endswith(".gpkg")]
        if gpkg_files:
            gpkg_path = os.path.join(processed_dir, gpkg_files[0])
            print(f"[Info] Usando archivo geográfico alternativo: {gpkg_path}")
        else:
            raise FileNotFoundError(f"No se encontraron archivos .gpkg en {processed_dir}")

    fig_maup_path = os.path.join(base_dir, "outputs", "00", "06_maup_scale_correlation.png")
    csv_maup_path = os.path.join(base_dir, "outputs", "00", "06_maup_scale_correlation_metrics.csv")
    
    print(f"[MAUP] Cargando GeoPackage maestro: {os.path.basename(gpkg_path)}...")
    gdf = gpd.read_file(gpkg_path)
    print(f"      Se cargaron {len(gdf)} celdas.")

    print("[MAUP] Reproyectando a UTM Zona 14N (EPSG:32614)...")
    gdf_utm = gdf.to_crs(epsg=32614)
    centroids = gdf_utm.geometry.centroid
    gdf_utm['x_coord'] = centroids.x
    gdf_utm['y_coord'] = centroids.y

    target_col = 'suhi_day_c' if 'suhi_day_c' in gdf_utm.columns else ('suhi_c' if 'suhi_c' in gdf_utm.columns else 'lst_day_c')
    pred_cols = ['green_pct', 'dw_built_pct', 'dw_trees_pct', 'industrial_osm_pct']
    pred_cols = [c for c in pred_cols if c in gdf_utm.columns]
    
    print(f"      Target: {target_col} | Predictores: {pred_cols}")

    scales = [30, 50, 100, 300, 1000]
    results_maup = []

    for scale in scales:
        print(f"[MAUP] Procesando agregación a escala {scale}m...")
        if scale == 30:
            df_scale = gdf_utm.copy()
        else:
            df_scale = gdf_utm.copy()
            df_scale['x_grid'] = (df_scale['x_coord'] // scale) * scale
            df_scale['y_grid'] = (df_scale['y_coord'] // scale) * scale
            agg_dict = {target_col: 'mean'}
            for col in pred_cols:
                agg_dict[col] = 'mean'
            df_scale = df_scale.groupby(['x_grid', 'y_grid']).agg(agg_dict).reset_index()
        
        df_clean = df_scale[[target_col] + pred_cols].dropna()
        n_obs = len(df_clean)
        
        corrs = {}
        for col in pred_cols:
            corr_val = df_clean[target_col].corr(df_clean[col], method='spearman')
            corrs[col] = corr_val
            
        results_maup.append({
            'escala_m': scale,
            'n_celdas': n_obs,
            **corrs
        })

    df_results_maup = pd.DataFrame(results_maup)
    os.makedirs(os.path.dirname(fig_maup_path), exist_ok=True)
    df_results_maup.to_csv(csv_maup_path, index=False)
    print(f"[MAUP] Métricas de escala guardadas en: {csv_maup_path}")
    print(df_results_maup.to_string(index=False))

    # Graficar MAUP
    sns.set_theme(style="ticks")
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    style_dict = {
        'green_pct': {'label': 'Cobertura Verde Sentinel-2 (green_pct)', 'color': '#2e7d32', 'marker': 'o', 'ls': '-'},
        'dw_trees_pct': {'label': 'Dosel Arbóreo Dynamic World (dw_trees_pct)', 'color': '#4caf50', 'marker': 's', 'ls': '--'},
        'dw_built_pct': {'label': 'Impermeable / Construido DW (dw_built_pct)', 'color': '#d84315', 'marker': '^', 'ls': '-'},
        'industrial_osm_pct': {'label': 'Área Industrial OSM (industrial_osm_pct)', 'color': '#ff8f00', 'marker': 'D', 'ls': '-.'}
    }
    
    x = df_results_maup['escala_m']
    for col in pred_cols:
        if col in style_dict:
            y_vals = df_results_maup[col]
            ax.plot(x, y_vals, label=style_dict[col]['label'], color=style_dict[col]['color'],
                    marker=style_dict[col]['marker'], linestyle=style_dict[col]['ls'],
                    linewidth=2.5, markersize=8, alpha=0.9)
            for idx, scale in enumerate(scales):
                if scale in [30, 100, 1000]:
                    val = y_vals.iloc[idx]
                    ax.annotate(f"{val:.3f}", xy=(scale, val), xytext=(0, 7 if val > 0 else -15),
                                textcoords="offset points", fontsize=9, fontweight='bold',
                                color=style_dict[col]['color'], ha='center')

    ax.set_xscale('log')
    ax.set_xticks(scales)
    ax.get_xaxis().set_major_formatter(plt.ScalarFormatter())
    ax.set_title("Efecto de Escala (MAUP) sobre las Correlaciones de la SUHI\nZona Metropolitana de Monterrey - 2026", 
                 fontsize=13, fontweight='bold', pad=15, color='#263238')
    ax.set_xlabel("Escala de Agregación de la Malla (metros - Escala Logarítmica)", fontsize=11, labelpad=10)
    ax.set_ylabel("Coeficiente de Correlación de Spearman (r con SUHI)", fontsize=11, labelpad=10)
    ax.axhline(y=0, color='#90a4ae', linestyle=':', linewidth=1)
    ax.grid(True, which="both", ls="--", color='#cfd8dc', alpha=0.5)
    ax.legend(loc='lower left', frameon=True, facecolor='#fafafa', edgecolor='#b0bec5', fontsize=9.5)
    sns.despine(trim=False)
    plt.tight_layout()
    plt.savefig(fig_maup_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[MAUP] Gráfica MAUP guardada en: {fig_maup_path}")

    # -------------------------------------------------------------------------
    # PARTE 2: REGRESIÓN GEOGRÁFICAMENTE PONDERADA (GWR) - ESPECIFICACIÓN OFICIAL MODELO A
    # -------------------------------------------------------------------------
    print_step(2, "Preparación de Datos para Regresión Espacial Local GWR Oficial (Modelo A)")
    
    # Cargar la malla multiescala enriquecida para modelado
    model_gpkg_path = os.path.join(base_dir, "data", "processed", "malla_modelado_multiescala_mty.gpkg")
    if not os.path.exists(model_gpkg_path):
        print(f"[Advertencia] No se encontró {model_gpkg_path}. Intentando buscar en el directorio...")
        model_gpkg_path = os.path.join(base_dir, "..", "data", "processed", "malla_modelado_multiescala_mty.gpkg")
        if not os.path.exists(model_gpkg_path):
            raise FileNotFoundError("No se encontró el Geopackage de modelado malla_modelado_multiescala_mty.gpkg")
            
    print(f"[GWR] Cargando malla enriquecida para modelado: {os.path.basename(model_gpkg_path)}...")
    gdf_model = gpd.read_file(model_gpkg_path)
    
    # Definir variables oficiales (Modelo A)
    target_col = 'suhi_day_c' if 'suhi_day_c' in gdf_model.columns else 'suhi_c'
    pred_cols_gwr = ['green_pct', 'dw_built_pct']
    
    # Limpiar nulos
    gdf_clean_gwr = gdf_model.dropna(subset=[target_col] + pred_cols_gwr).copy()
    print(f"[GWR] Celdas válidas sin nulos: {len(gdf_clean_gwr)}")
    
    # Tomamos un submuestreo de 5000 celdas para garantizar un cálculo interactivo y rápido en CPU
    sample_size = 5000
    if len(gdf_clean_gwr) > sample_size:
        print(f"[GWR] Seleccionando una submuestra aleatoria de {sample_size} celdas para el análisis espacial...")
        gdf_sample = gdf_clean_gwr.sample(n=sample_size, random_state=42).copy()
    else:
        gdf_sample = gdf_clean_gwr.copy()
        
    # Extraer coordenadas en WGS84 para el análisis de distancia en mgwr
    coords = np.column_stack((gdf_sample.geometry.centroid.x, gdf_sample.geometry.centroid.y))
    
    # Extraer variables
    y = gdf_sample[target_col].values.reshape(-1, 1)
    X = gdf_sample[pred_cols_gwr].values
    
    # Estandarizar variables independientes (Escala Z)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    print(f"[GWR] Predictores estandarizados: {pred_cols_gwr}")
    
    # -------------------------------------------------------------------------
    print_step(3, "Búsqueda de Ancho de Banda Óptimo (Bandwidth)")
    # Usamos kernel adaptativo bisquare para peso espacial, optimizado por AICc y bw_min=30
    print("[GWR] Buscando ancho de banda óptimo con kernel adaptativo bisquare (AICc)...")
    start_bw = time.time()
    selector = Sel_BW(coords, y, X_scaled, kernel='bisquare', fixed=False, n_jobs=1)
    bw_opt = selector.search(criterion='AICc', bw_min=30)
    end_bw = time.time()
    print(f"[GWR] Ancho de banda óptimo encontrado: {bw_opt} celdas vecinas (Tiempo: {end_bw - start_bw:.2f}s)")
    
    # -------------------------------------------------------------------------
    print_step(4, "Ajuste del Modelo GWR Oficial y Extracción de Resultados")
    print("[GWR] Ajustando el modelo GWR con el ancho de banda óptimo...")
    start_fit = time.time()
    model_gwr = GWR(coords, y, X_scaled, bw_opt, kernel='bisquare', fixed=False, n_jobs=1)
    results_gwr = model_gwr.fit()
    end_fit = time.time()
    
    print(f"[GWR] Modelo ajustado con éxito (Tiempo: {end_fit - start_fit:.2f}s)")
    print(f"      R² del GWR Local: {results_gwr.R2:.4f}")
    print(f"      AICc del GWR: {results_gwr.aicc:.2f}")
    
    # -------------------------------------------------------------------------
    print_step(5, "Extracción de Coeficientes y Filtro Estadístico Estricto")
    print("[GWR] Extrayendo coeficientes locales (Betas), significancia FDR y colinealidad local CN...")
    
    df_resid = results_gwr.df_resid
    pvalues = 2 * (1 - stats.t.cdf(np.abs(results_gwr.tvalues), df_resid))
    
    # Calcular Condition Numbers locales
    dists = distance_matrix(coords, coords)
    local_cns = []
    for i in range(len(gdf_sample)):
        idx = np.argsort(dists[i])[:int(bw_opt)]
        X_local = X_scaled[idx]
        X_local_const = np.column_stack((np.ones(len(idx)), X_local))
        s = np.linalg.svd(X_local_const, compute_uv=False)
        cn = s[0] / s[-1] if s[-1] > 1e-12 else 999999.0
        local_cns.append(cn)
    local_cns = np.array(local_cns)
    
    gdf_sample['local_cn'] = local_cns
    gdf_sample['gwr_local_r2'] = results_gwr.localR2
    
    # Variables y sus respectivos índices en params/tvalues
    var_indices = {
        'intercept': 0,
        'green_pct': 1,
        'dw_built_pct': 2
    }
    
    # Guardar coeficientes y pvalues
    for var_name, idx in var_indices.items():
        gdf_sample[f'coef_{var_name}'] = results_gwr.params[:, idx]
        gdf_sample[f'tval_{var_name}'] = results_gwr.tvalues[:, idx]
        gdf_sample[f'pval_{var_name}'] = pvalues[:, idx]
        
    # Aplicar corrección FDR (Benjamini-Hochberg) y definir robustez (FDR < 0.05 y CN < 30)
    for var_name in ['green_pct', 'dw_built_pct']:
        pval_col = gdf_sample[f'pval_{var_name}'].values
        reject, pvals_fdr, _, _ = multipletests(pval_col, alpha=0.05, method='fdr_bh')
        gdf_sample[f'p_fdr_{var_name}'] = pvals_fdr
        gdf_sample[f'sig_fdr_{var_name}'] = reject.astype(int)
        
        # Filtro de robustez estricto
        gdf_sample[f'robust_{var_name}'] = (reject & (local_cns < 30)).astype(int)
        
    output_gwr_gpkg = os.path.join(base_dir, "outputs", "malla_gwr_coefficients_official_gwr.gpkg")
    os.makedirs(os.path.dirname(output_gwr_gpkg), exist_ok=True)
    gdf_sample.to_file(output_gwr_gpkg, driver="GPKG", mode="w")
    print(f"[GWR] GeoPackage con coeficientes locales guardado en: {output_gwr_gpkg}")
    
    # -------------------------------------------------------------------------
    # PARTE 3: SPATIAL JOIN Y GENERACIÓN DE MAPAS HEXAGONALES Y PANELES
    # -------------------------------------------------------------------------
    print_step(6, "Generación de Mapas Explicativos y Paneles de Diagnóstico Robustos")
    
    # Cargar AGEBs para obtener municipios (para el boxplot)
    ageb_path = os.path.join(base_dir, "data", "raw", "AGEB_ZMM_Dani.json")
    if os.path.exists(ageb_path):
        print("[GWR] Cargando AGEBs para cruce espacial con municipios...")
        gdf_ageb = gpd.read_file(ageb_path)
        gdf_ageb = gdf_ageb.to_crs(gdf_sample.crs)
        gdf_sample_joined = gpd.sjoin(gdf_sample, gdf_ageb[['NOM_MUN', 'geometry']], how='left', predicate='intersects')
        gdf_sample_joined = gdf_sample_joined[~gdf_sample_joined.index.duplicated(keep='first')].copy()
        gdf_sample_joined['NOM_MUN'] = gdf_sample_joined['NOM_MUN'].fillna('Otro / Límite')
    else:
        print("[Advertencia] No se encontró AGEB_ZMM_Dani.json. Usando municipio genérico para boxplot.")
        gdf_sample_joined = gdf_sample.copy()
        gdf_sample_joined['NOM_MUN'] = 'ZMM'
        
    # Reproyectar a Web Mercator (EPSG:3857) para visualización correcta sobre mapas de fondo
    gdf_sample_3857 = gdf_sample_joined.to_crs(epsg=3857)
    gdf_sample_3857['geometry'] = gdf_sample_3857.geometry.centroid
    
    from matplotlib.colors import TwoSlopeNorm
    
    # -------------------------------------------------------------------------
    # VEGETACIÓN (green_pct)
    # -------------------------------------------------------------------------
    print("      Generando mapa hexagonal y panel de Vegetación (green_pct)...")
    
    fig, ax = plt.subplots(figsize=(12, 10), dpi=300)
    
    robust_veg = gdf_sample_3857[gdf_sample_3857['robust_green_pct'] == 1]
    non_robust_veg = gdf_sample_3857[gdf_sample_3857['robust_green_pct'] == 0]
    
    # Graficar no robustos en gris
    if len(non_robust_veg) > 0:
        non_robust_veg.plot(ax=ax, color='#cfd8dc', alpha=0.35, marker='h', markersize=25, label='No Robust (p_FDR >= 0.05 o CN >= 30)')
        
    # Graficar robustos con colormap centrado en 0
    if len(robust_veg) > 0:
        vmin_v = min(robust_veg['coef_green_pct'].min(), -0.1)
        vmax_v = max(robust_veg['coef_green_pct'].max(), 0.1)
        norm_v = TwoSlopeNorm(vmin=vmin_v, vcenter=0.0, vmax=vmax_v)
        
        robust_veg.plot(
            ax=ax, column='coef_green_pct', cmap='RdBu_r', marker='h', markersize=55,
            legend=False, norm=norm_v, label='Robust Cooling/Warming (p_FDR < 0.05 & CN < 30)'
        )
        
        fig = ax.get_figure()
        cax = fig.add_axes([0.92, 0.2, 0.02, 0.6])
        sm = plt.cm.ScalarMappable(cmap='RdBu_r', norm=norm_v)
        cb = fig.colorbar(sm, cax=cax, label='Coeficiente Beta Local (green_pct)')
        cb.ax.tick_params(labelsize=10)
        
    ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron, alpha=0.95)
    ax.set_title("Efecto Espacial de Enfriamiento de la Vegetación (green_pct) - GWR Oficial\nSolo Muestra Coeficientes Robustos (FDR < 0.05 y CN < 30) - Monterrey 2026",
                 fontsize=11, fontweight='bold', pad=15, color='#263238')
    ax.set_axis_off()
    
    fig_veg_path = os.path.join(base_dir, "outputs", "00", "06_gwr_vegetation_coef_official_gwr.png")
    plt.savefig(fig_veg_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"      Mapa de Vegetación guardado en: {fig_veg_path}")
    
    # Panel de Diagnóstico
    fig, axes = plt.subplots(1, 3, figsize=(20, 6), dpi=300)
    
    # Subplot 2.1: Mapa simplificado
    ax_map = axes[0]
    if len(non_robust_veg) > 0:
        non_robust_veg.plot(ax=ax_map, color='#cfd8dc', alpha=0.3, marker='h', markersize=10)
    if len(robust_veg) > 0:
        robust_veg.plot(ax=ax_map, column='coef_green_pct', cmap='RdBu_r', marker='h', markersize=20, norm=norm_v)
    ctx.add_basemap(ax_map, source=ctx.providers.CartoDB.Positron, alpha=0.85)
    ax_map.set_title("Mapa de Coeficientes Locales Robustos", fontsize=11, fontweight='bold')
    ax_map.set_axis_off()
    
    # Subplot 2.2: Histograma
    ax_hist = axes[1]
    sns.histplot(data=gdf_sample_joined, x='coef_green_pct', kde=True, ax=ax_hist, color='#1e88e5', alpha=0.6)
    ax_hist.axvline(x=0, color='#e53935', linestyle='--', linewidth=1.5, label='Sin Efecto (Beta=0)')
    ax_hist.set_title("Distribución (Todos los Coeficientes)", fontsize=11, fontweight='bold')
    ax_hist.set_xlabel("Coeficiente Local Beta (green_pct)", fontsize=10)
    ax_hist.set_ylabel("Frecuencia", fontsize=10)
    ax_hist.legend(fontsize=9)
    
    # Subplot 2.3: Boxplot por Municipio
    ax_box = axes[2]
    mun_counts = gdf_sample_joined['NOM_MUN'].value_counts()
    valid_muns = mun_counts[mun_counts > 10].index
    box_df = gdf_sample_joined[gdf_sample_joined['NOM_MUN'].isin(valid_muns)].copy()
    
    order = box_df.groupby('NOM_MUN')['coef_green_pct'].median().sort_values().index
    sns.boxplot(data=box_df, x='coef_green_pct', y='NOM_MUN', ax=ax_box, order=order, palette='crest', hue='NOM_MUN', legend=False)
    ax_box.axvline(x=0, color='#e53935', linestyle='--', linewidth=1.5)
    ax_box.set_title("Variabilidad por Municipio", fontsize=11, fontweight='bold')
    ax_box.set_xlabel("Coeficiente Local Beta (green_pct)", fontsize=10)
    ax_box.set_ylabel("", fontsize=10)
    ax_box.tick_params(labelsize=9)
    
    plt.suptitle("Panel de Diagnóstico Territorial: Coeficiente Local de la Vegetación (green_pct) - Modelo A", fontsize=13, fontweight='bold', y=0.98)
    plt.tight_layout()
    
    fig_veg_panel_path = os.path.join(base_dir, "outputs", "00", "06_gwr_vegetation_panel_official_gwr.png")
    plt.savefig(fig_veg_panel_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"      Panel de Diagnóstico de Vegetación guardado en: {fig_veg_panel_path}")
    
    # -------------------------------------------------------------------------
    # SUELO CONSTRUIDO (dw_built_pct)
    # -------------------------------------------------------------------------
    print("      Generando mapa hexagonal y panel de Suelo Construido (dw_built_pct)...")
    
    fig, ax = plt.subplots(figsize=(12, 10), dpi=300)
    
    robust_built = gdf_sample_3857[gdf_sample_3857['robust_dw_built_pct'] == 1]
    non_robust_built = gdf_sample_3857[gdf_sample_3857['robust_dw_built_pct'] == 0]
    
    # Graficar no robustos en gris
    if len(non_robust_built) > 0:
        non_robust_built.plot(ax=ax, color='#cfd8dc', alpha=0.35, marker='h', markersize=25, label='No Robust (p_FDR >= 0.05 o CN >= 30)')
        
    # Graficar robustos con colormap centrado en 0 (RdBu_r para calentamiento en rojo)
    if len(robust_built) > 0:
        vmin_b = min(robust_built['coef_dw_built_pct'].min(), -0.1)
        vmax_b = max(robust_built['coef_dw_built_pct'].max(), 0.1)
        norm_b = TwoSlopeNorm(vmin=vmin_b, vcenter=0.0, vmax=vmax_b)
        
        robust_built.plot(
            ax=ax, column='coef_dw_built_pct', cmap='RdBu_r', marker='h', markersize=55,
            legend=False, norm=norm_b, label='Robust Heating/Cooling (p_FDR < 0.05 & CN < 30)'
        )
        
        fig = ax.get_figure()
        cax = fig.add_axes([0.92, 0.2, 0.02, 0.6])
        sm = plt.cm.ScalarMappable(cmap='RdBu_r', norm=norm_b)
        cb = fig.colorbar(sm, cax=cax, label='Coeficiente Beta Local (dw_built_pct)')
        cb.ax.tick_params(labelsize=10)
        
    ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron, alpha=0.95)
    ax.set_title("Efecto Espacial de Calentamiento del Suelo Construido (dw_built_pct) - GWR Oficial\nSolo Muestra Coeficientes Robustos (FDR < 0.05 y CN < 30) - Monterrey 2026",
                 fontsize=11, fontweight='bold', pad=15, color='#263238')
    ax.set_axis_off()
    
    fig_built_path = os.path.join(base_dir, "outputs", "00", "06_gwr_built_coef_official_gwr.png")
    plt.savefig(fig_built_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"      Mapa de Suelo Construido guardado en: {fig_built_path}")
    
    # Panel de Diagnóstico
    fig, axes = plt.subplots(1, 3, figsize=(20, 6), dpi=300)
    
    # Subplot 2.1: Mapa simplificado
    ax_map = axes[0]
    if len(non_robust_built) > 0:
        non_robust_built.plot(ax=ax_map, color='#cfd8dc', alpha=0.3, marker='h', markersize=10)
    if len(robust_built) > 0:
        robust_built.plot(ax=ax_map, column='coef_dw_built_pct', cmap='RdBu_r', marker='h', markersize=20, norm=norm_b)
    ctx.add_basemap(ax_map, source=ctx.providers.CartoDB.Positron, alpha=0.85)
    ax_map.set_title("Mapa de Coeficientes Locales Robustos", fontsize=11, fontweight='bold')
    ax_map.set_axis_off()
    
    # Subplot 2.2: Histograma
    ax_hist = axes[1]
    sns.histplot(data=gdf_sample_joined, x='coef_dw_built_pct', kde=True, ax=ax_hist, color='#e53935', alpha=0.6)
    ax_hist.axvline(x=0, color='#1e88e5', linestyle='--', linewidth=1.5, label='Sin Efecto (Beta=0)')
    ax_hist.set_title("Distribución (Todos los Coeficientes)", fontsize=11, fontweight='bold')
    ax_hist.set_xlabel("Coeficiente Local Beta (dw_built_pct)", fontsize=10)
    ax_hist.set_ylabel("Frecuencia", fontsize=10)
    ax_hist.legend(fontsize=9)
    
    # Subplot 2.3: Boxplot por Municipio
    ax_box = axes[2]
    box_df = gdf_sample_joined[gdf_sample_joined['NOM_MUN'].isin(valid_muns)].copy()
    
    order = box_df.groupby('NOM_MUN')['coef_dw_built_pct'].median().sort_values(ascending=False).index
    sns.boxplot(data=box_df, x='coef_dw_built_pct', y='NOM_MUN', ax=ax_box, order=order, palette='flare', hue='NOM_MUN', legend=False)
    ax_box.axvline(x=0, color='#1e88e5', linestyle='--', linewidth=1.5)
    ax_box.set_title("Variabilidad por Municipio", fontsize=11, fontweight='bold')
    ax_box.set_xlabel("Coeficiente Local Beta (dw_built_pct)", fontsize=10)
    ax_box.set_ylabel("", fontsize=10)
    ax_box.tick_params(labelsize=9)
    
    plt.suptitle("Panel de Diagnóstico Territorial: Coeficiente Local del Suelo Construido (dw_built_pct) - Modelo A", fontsize=13, fontweight='bold', y=0.98)
    plt.tight_layout()
    
    fig_built_panel_path = os.path.join(base_dir, "outputs", "00", "06_gwr_built_panel_official_gwr.png")
    plt.savefig(fig_built_panel_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"      Panel de Diagnóstico de Suelo Construido guardado en: {fig_built_panel_path}")
    
    print("\n" + "="*80)
    print(" ANÁLISIS DE CORRELACIÓN ESPACIAL GWR OFICIAL (MODELO A) COMPLETADO")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
