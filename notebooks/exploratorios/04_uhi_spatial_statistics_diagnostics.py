import os
import geopandas as gpd
import pandas as pd
import numpy as np
import libpysal
import esda
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import GroupKFold
from sklearn.cluster import KMeans
from xgboost import XGBRegressor

base_dir = ".."
gpkg_path = os.path.join(base_dir, "data", "processed", "malla_modelado_multiescala_mty.gpkg")
print("Cargando GeoPackage...")
gdf = gpd.read_file(gpkg_path)
print(f"Registros totales en malla: {len(gdf)}")



# Reemplazar infinitos por nan
gdf.replace([np.inf, -np.inf], np.nan, inplace=True)

# Limpiar target
target_col = 'suhi_c'
gdf_clean = gdf.dropna(subset=[target_col]).copy()
print(f"Registros válidos tras limpieza de target: {len(gdf_clean)}")

# Submuestreo sistemático (cada 15 filas)
step = 15
gdf_sub = gdf_clean.iloc[::step].copy().reset_index(drop=True)
N_sub = len(gdf_sub)
print(f"Submuestra representativa (1 de cada {step} celdas): {N_sub} celdas")

# Asegurar centroides en metros
centroids = gdf_sub.geometry.centroid
gdf_sub['x_coord'] = centroids.x
gdf_sub['y_coord'] = centroids.y
coords = np.column_stack((gdf_sub['x_coord'], gdf_sub['y_coord']))



print("Construyendo pesos espaciales KNN (k=8)...")
w = libpysal.weights.KNN.from_array(coords, k=8)
w.transform = 'R' # Estandarizar por filas

print(f"Componentes espaciales: {w.n}")
print(f"Promedio de vecinos: {w.mean_neighbors}")
print(f"Observaciones aisladas (islands): {len(w.islands)}")



# Cargar y mostrar la gráfica de diagnóstico de pesos
from IPython.display import Image, display
fig_weights = os.path.join(base_dir, "outputs", "figures", "spatial_weights_diagnostics.png")
display(Image(filename=fig_weights))



mi_suhi = esda.moran.Moran(gdf_sub[target_col], w)
print("=== RESULTADOS MORAN GLOBAL SUHI ===")
print(f"Moran's I: {mi_suhi.I:.5f}")
print(f"z-score: {mi_suhi.z_sim:.5f}")
print(f"p-value: {mi_suhi.p_sim:.5f}")
print(f"Número de permutaciones: {mi_suhi.permutations}")



fig_moran_suhi = os.path.join(base_dir, "outputs", "figures", "moran_scatter_suhi.png")
display(Image(filename=fig_moran_suhi))



lm_suhi = esda.moran.Moran_Local(gdf_sub[target_col], w, transformation='r', permutations=999, seed=42)

sig_suhi = lm_suhi.p_sim < 0.05
hh_suhi = (lm_suhi.q == 1) & sig_suhi
lh_suhi = (lm_suhi.q == 2) & sig_suhi
ll_suhi = (lm_suhi.q == 3) & sig_suhi
hl_suhi = (lm_suhi.q == 4) & sig_suhi

lisa_class_suhi = np.zeros(N_sub, dtype=int)
lisa_class_suhi[hh_suhi] = 1
lisa_class_suhi[lh_suhi] = 2
lisa_class_suhi[ll_suhi] = 3
lisa_class_suhi[hl_suhi] = 4
gdf_sub['lisa_cluster_suhi'] = lisa_class_suhi

df_summary_suhi = pd.read_csv(os.path.join(base_dir, "outputs", "tables", "08_lisa_clusters_summary.csv"))
print("=== RESUMEN CLUSTERS LISA SUHI ===")
print(df_summary_suhi.to_string(index=False))



fig_lisa_suhi = os.path.join(base_dir, "outputs", "figures", "lisa_clusters_suhi.png")
display(Image(filename=fig_lisa_suhi))



# Crear bloques KMeans para la CV espacial
gdf_sub['spatial_block'] = KMeans(n_clusters=5, random_state=42, n_init=10).fit_predict(coords)

# Definir predictores
excluded_cols = [
    'cell_id', 'geometry', 'lst_day_c', 'lst_c', 'lst_night_c',
    'suhi_day_c', 'suhi_night_c', 'suhi_c', 'x_coord', 'y_coord',
    'spatial_block', 'distance_to_ternium_m', 'lisa_cluster_suhi'
]
predictor_cols = [col for col in gdf_sub.columns if col not in excluded_cols and gdf_sub[col].dtype in [np.float64, np.int64]]

X = gdf_sub[predictor_cols].fillna(gdf_sub[predictor_cols].median())
y = gdf_sub[target_col]

# Ejecutar GroupKFold para predicciones out-of-fold
spatial_cv = GroupKFold(n_splits=5)
gdf_sub['preds'] = np.nan

for train_idx, test_idx in spatial_cv.split(X, y, groups=gdf_sub['spatial_block']):
    xgb_fold = XGBRegressor(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42, n_jobs=-1)
    xgb_fold.fit(X.iloc[train_idx], y.iloc[train_idx])
    gdf_sub.iloc[test_idx, gdf_sub.columns.get_loc('preds')] = xgb_fold.predict(X.iloc[test_idx])

# Calcular métricas de error
gdf_sub['residual'] = gdf_sub[target_col] - gdf_sub['preds']
gdf_sub['abs_error'] = gdf_sub['residual'].abs()
gdf_sub['std_residual'] = (gdf_sub['residual'] - gdf_sub['residual'].mean()) / gdf_sub['residual'].std()

print("Métricas de Error del Modelo en validación espacial:")
print(f"  MAE Medio: {gdf_sub['abs_error'].mean():.4f} °C")
print(f"  RMSE Medio: {np.sqrt((gdf_sub['residual']**2).mean()):.4f} °C")



fig_res_map = os.path.join(base_dir, "outputs", "figures", "residuals_map_best_model.png")
fig_ae_map = os.path.join(base_dir, "outputs", "figures", "absolute_error_map.png")
print("Distribución de Residuos:")
display(Image(filename=fig_res_map))
print("Distribución de Errores Absolutos:")
display(Image(filename=fig_ae_map))



mi_res = esda.moran.Moran(gdf_sub['residual'], w)
print("=== RESULTADOS MORAN GLOBAL RESIDUOS ===")
print(f"Moran's I Residuos: {mi_res.I:.5f}")
print(f"z-score: {mi_res.z_sim:.5f}")
print(f"p-value: {mi_res.p_sim:.5f}")



fig_moran_res = os.path.join(base_dir, "outputs", "figures", "moran_scatter_residuals.png")
display(Image(filename=fig_moran_res))



lm_res = esda.moran.Moran_Local(gdf_sub['residual'], w, transformation='r', permutations=999, seed=42)

sig_res = lm_res.p_sim < 0.05
hh_res = (lm_res.q == 1) & sig_res
lh_res = (lm_res.q == 2) & sig_res
ll_res = (lm_res.q == 3) & sig_res
hl_res = (lm_res.q == 4) & sig_res

lisa_class_res = np.zeros(N_sub, dtype=int)
lisa_class_res[hh_res] = 1
lisa_class_res[lh_res] = 2
lisa_class_res[ll_res] = 3
lisa_class_res[hl_res] = 4
gdf_sub['lisa_cluster_res'] = lisa_class_res

df_summary_res = pd.read_csv(os.path.join(base_dir, "outputs", "tables", "08_residuals_lisa_summary.csv"))
print("=== RESUMEN CLUSTERS LISA RESIDUOS ===")
print(df_summary_res.to_string(index=False))



fig_lisa_res = os.path.join(base_dir, "outputs", "figures", "lisa_clusters_residuals.png")
display(Image(filename=fig_lisa_res))


