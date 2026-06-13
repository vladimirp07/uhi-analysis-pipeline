import os
import sys
import time
import numpy as np
import pandas as pd
import geopandas as gpd
import scipy.stats as stats
import statsmodels.api as sm
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.multitest import multipletests
from esda.moran import Moran
from libpysal.weights import KNN
from scipy.spatial import distance_matrix
import warnings

# --- MONKEY PATCH PARA EVITAR COLINIALIDAD LOCAL CRÍTICA EN BUCLE DE ESTIMACIÓN GWR ---
import mgwr.gwr
import spglm.iwls
from scipy import linalg

def patched_compute_betas_gwr(y, x, wi):
    xT = (x * wi).T
    xtx = np.dot(xT, x)
    try:
        # Resolver normalmente
        xtx_inv_xt = linalg.solve(xtx, xT)
    except (linalg.LinAlgError, ValueError):
        # Si es singular, aplicar regularización Ridge a la diagonal del sistema local
        ridge = 1e-4 * np.eye(xtx.shape[0])
        xtx_inv_xt = linalg.solve(xtx + ridge, xT)
    betas = np.dot(xtx_inv_xt, y)
    return betas, xtx_inv_xt

# Aplicar el parche en ambos espacios de nombres para asegurar cobertura
mgwr.gwr._compute_betas_gwr = patched_compute_betas_gwr
spglm.iwls._compute_betas_gwr = patched_compute_betas_gwr
# ------------------------------------------------------------------------------------

from mgwr.gwr import GWR
from mgwr.sel_bw import Sel_BW

# Ignorar advertencias de tipo numérico
warnings.filterwarnings('ignore')

def calculate_local_cns(X_scaled, coords, bw_opt):
    """
    Calcula el Condition Number (CN) local para cada observación en la muestra
    basándose en su respectivo bandwidth óptimo.
    """
    n = len(X_scaled)
    dists = distance_matrix(coords, coords)
    local_cns = []
    
    for i in range(n):
        idx = np.argsort(dists[i])[:int(bw_opt)]
        X_local = X_scaled[idx]
        X_local_const = np.column_stack((np.ones(len(idx)), X_local))
        s = np.linalg.svd(X_local_const, compute_uv=False)
        cn = s[0] / s[-1] if s[-1] > 1e-12 else 999999.0
        local_cns.append(cn)
        
    return np.array(local_cns)

def analyze_single_model(gdf_sample, pred_cols, target_col, model_label):
    """
    Ejecuta bandwidth selection y ajuste GWR para una especificación y calcula
    todas las estadísticas clave asociadas.
    """
    print(f"   [MODELO] Iniciando {model_label} con variables: {pred_cols}...")
    t0 = time.time()
    
    # 1. Preparar datos y coordenadas
    coords = np.column_stack((gdf_sample.geometry.centroid.x, gdf_sample.geometry.centroid.y))
    y = gdf_sample[target_col].values.reshape(-1, 1)
    X = gdf_sample[pred_cols].values
    
    # 2. Estandarizar predictores
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # 3. Optimizar bandwidth (Sel_BW) con n_jobs=1 para asegurar que se use el parche
    print("      Optimizando bandwidth adaptativo (kernel bisquare, AICc)...")
    selector = Sel_BW(coords, y, X_scaled, kernel='bisquare', fixed=False, n_jobs=1)
    bw_opt = selector.search(criterion='AICc', bw_min=30)
    print(f"      Bandwidth óptimo determinado: {bw_opt}")
    
    # 4. Ajustar modelo GWR
    print("      Ajustando GWR...")
    model = GWR(coords, y, X_scaled, bw_opt, kernel='bisquare', fixed=False, n_jobs=1)
    results = model.fit()
    
    # 5. R2 y AICc
    r2_gwr = results.R2
    aicc = results.aicc
    betas = results.params # Forma: (N, p + 1)
    tvalues = results.tvalues
    df_resid = results.df_resid
    
    # 6. Residuos y Moran's I
    X_gwr = np.column_stack((np.ones(len(gdf_sample)), X_scaled))
    y_pred = np.sum(betas * X_gwr, axis=1)
    residuals = y.flatten() - y_pred
    
    w = KNN.from_dataframe(gdf_sample, k=8)
    w.transform = 'R'
    mi = Moran(residuals, w)
    moran_i = mi.I
    moran_p = mi.p_sim
    
    # 7. Condition Number local
    print("      Calculando Condition Numbers locales...")
    local_cns = calculate_local_cns(X_scaled, coords, bw_opt)
    pct_cn_ge_30 = np.sum(local_cns >= 30) / len(gdf_sample) * 100
    
    # 8. Analizar coeficientes por variable
    pvalues = 2 * (1 - stats.t.cdf(np.abs(tvalues), df_resid))
    
    var_stats = {}
    for var_idx, var_name in enumerate(pred_cols):
        beta_col = betas[:, var_idx + 1] # 0 es el intercept
        pval_col = pvalues[:, var_idx + 1]
        
        # FDR correction
        reject, pvals_fdr, _, _ = multipletests(pval_col, alpha=0.05, method='fdr_bh')
        
        # Robust definition: FDR < 0.05 and CN < 30
        is_robust = reject & (local_cns < 30)
        
        median_beta = np.median(beta_col)
        pct_sig = np.sum(reject) / len(gdf_sample) * 100
        pct_robust = np.sum(is_robust) / len(gdf_sample) * 100
        
        # Robust signs
        pct_beta_neg_robust = np.sum(is_robust & (beta_col < 0)) / len(gdf_sample) * 100
        pct_beta_pos_robust = np.sum(is_robust & (beta_col > 0)) / len(gdf_sample) * 100
        
        var_stats[var_name] = {
            'median_beta': median_beta,
            'pct_sig': pct_sig,
            'pct_robust': pct_robust,
            'pct_beta_neg_robust': pct_beta_neg_robust,
            'pct_beta_pos_robust': pct_beta_pos_robust
        }
        
    elapsed = time.time() - t0
    print(f"      Completado en {elapsed:.2f} s. R2: {r2_gwr:.4f} | AICc: {aicc:.2f} | CN>=30: {pct_cn_ge_30:.2f}% | Moran's I: {moran_i:.4f}")
    
    return {
        'r2_gwr': r2_gwr,
        'aicc': aicc,
        'bw_opt': bw_opt,
        'moran_i': moran_i,
        'moran_p': moran_p,
        'pct_cn_ge_30': pct_cn_ge_30,
        'var_stats': var_stats
    }

def main():
    base_dir = "."
    gpkg_path = os.path.join(base_dir, "data", "processed", "malla_modelado_multiescala_mty.gpkg")
    
    if not os.path.exists(gpkg_path):
        print(f"Error: No se encontró el archivo de datos {gpkg_path}")
        sys.exit(1)
        
    print(f"Cargando GeoPackage: {gpkg_path}...")
    gdf = gpd.read_file(gpkg_path)
    print(f"Cargadas {len(gdf)} celdas.")
    
    # Determinar target
    target_col = 'suhi_day_c' if 'suhi_day_c' in gdf.columns else 'suhi_c'
    print(f"Variable objetivo (target): {target_col}")
    
    # Definir modelos
    models_def = {
        'Base': ['green_pct', 'dw_built_pct', 'elevation', 'distance_to_industry_osm_m'],
        'Model A': ['green_pct', 'dw_built_pct'],
        'Model B': ['green_pct', 'elevation'],
        'Model C': ['dw_built_pct', 'elevation'],
        'Model D': ['green_pct', 'dw_built_pct', 'elevation']
    }
    
    # Unir todas las variables predictoras para limpiar nulos
    all_preds = ['green_pct', 'dw_built_pct', 'elevation', 'distance_to_industry_osm_m']
    gdf_clean = gdf.dropna(subset=[target_col] + all_preds).copy()
    print(f"Celdas sin nulos en variables de interés: {len(gdf_clean)}")
    
    # Asegurar directorios
    os.makedirs(os.path.join(base_dir, "outputs", "tables"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "outputs", "reports"), exist_ok=True)
    
    # ==========================================
    # TAREA 2 & 3: Comparación de Modelos GWR Reducidos (Semilla 42, N = 5000)
    # ==========================================
    print("\n" + "="*50)
    print("EJECUTANDO COMPARACIÓN DE MODELOS REDUCIDOS (SEMILLA 42)")
    print("="*50)
    
    gdf_sample_42 = gdf_clean.sample(n=5000, random_state=42).copy()
    
    model_comparison_results = []
    
    for model_label, pred_cols in models_def.items():
        res = analyze_single_model(gdf_sample_42, pred_cols, target_col, model_label)
        
        # Construir fila para tabla comparativa
        row = {
            'model_name': model_label,
            'variables': ', '.join(pred_cols),
            'r2_gwr': res['r2_gwr'],
            'aicc': res['aicc'],
            'bw_opt': res['bw_opt'],
            'moran_i': res['moran_i'],
            'moran_p': res['moran_p'],
            'pct_cn_ge_30': res['pct_cn_ge_30']
        }
        
        # Rellenar estadísticas por variable
        for var in all_preds:
            if var in res['var_stats']:
                row[f'{var}_median_beta'] = res['var_stats'][var]['median_beta']
                row[f'{var}_pct_sig_fdr'] = res['var_stats'][var]['pct_sig']
                row[f'{var}_pct_robust'] = res['var_stats'][var]['pct_robust']
                row[f'{var}_pct_neg_robust'] = res['var_stats'][var]['pct_beta_neg_robust']
                row[f'{var}_pct_pos_robust'] = res['var_stats'][var]['pct_beta_pos_robust']
            else:
                row[f'{var}_median_beta'] = np.nan
                row[f'{var}_pct_sig_fdr'] = np.nan
                row[f'{var}_pct_robust'] = np.nan
                row[f'{var}_pct_neg_robust'] = np.nan
                row[f'{var}_pct_pos_robust'] = np.nan
                
        model_comparison_results.append(row)
        
    df_comparison = pd.DataFrame(model_comparison_results)
    comparison_csv_path = os.path.join(base_dir, "outputs", "tables", "gwr_sensitivity_model_comparison.csv")
    df_comparison.to_csv(comparison_csv_path, index=False)
    print(f"\n[OK] Comparación guardada en: {comparison_csv_path}")
    
    # ==========================================
    # TAREA 4: Estabilidad por Semillas (Base, Model A, Model D; 3 Semillas, N = 5000)
    # ==========================================
    print("\n" + "="*50)
    print("EJECUTANDO PRUEBAS DE ESTABILIDAD CON SEMILLAS")
    print("="*50)
    
    stability_models = ['Base', 'Model A', 'Model D']
    seeds = [42, 100, 2026]
    
    stability_results = []
    
    for seed in seeds:
        print(f"\n>>> Procesando Semilla {seed} (N = 5000)...")
        gdf_sample_seed = gdf_clean.sample(n=5000, random_state=seed).copy()
        
        for model_label in stability_models:
            pred_cols = models_def[model_label]
            res = analyze_single_model(gdf_sample_seed, pred_cols, target_col, f"{model_label} (Semilla {seed})")
            
            # Variables específicas requeridas
            green_stats = res['var_stats'].get('green_pct', {})
            dw_built_stats = res['var_stats'].get('dw_built_pct', {})
            
            row = {
                'model_name': model_label,
                'seed': seed,
                'green_pct_median_beta': green_stats.get('median_beta', np.nan),
                'green_pct_neg_robust_pct': green_stats.get('pct_beta_neg_robust', np.nan),
                'green_pct_pos_robust_pct': green_stats.get('pct_beta_pos_robust', np.nan),
                'dw_built_pct_median_beta': dw_built_stats.get('median_beta', np.nan),
                'dw_built_pct_pos_robust_pct': dw_built_stats.get('pct_beta_pos_robust', np.nan),
                'pct_cn_ge_30': res['pct_cn_ge_30'],
                'r2_gwr': res['r2_gwr'],
                'aicc': res['aicc'],
                'moran_i': res['moran_i']
            }
            stability_results.append(row)
            
    df_stability = pd.DataFrame(stability_results)
    stability_csv_path = os.path.join(base_dir, "outputs", "tables", "gwr_sensitivity_seed_stability.csv")
    df_stability.to_csv(stability_csv_path, index=False)
    print(f"\n[OK] Tabla de estabilidad guardada en: {stability_csv_path}")
    print("\nAuditoría de Sensibilidad GWR finalizada exitosamente.")

if __name__ == "__main__":
    main()
