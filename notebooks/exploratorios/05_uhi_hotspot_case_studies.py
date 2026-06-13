import os
import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import DBSCAN
from shapely.geometry import Point
from IPython.display import Image, display

base_dir = ".."
gpkg_path = os.path.join(base_dir, "data", "processed", "malla_modelado_multiescala_mty.gpkg")

# Cargar malla
gdf = gpd.read_file(gpkg_path)
gdf.replace([np.inf, -np.inf], np.nan, inplace=True)
print(f"Cargadas {len(gdf)} celdas de la malla base.")


target_col = 'suhi_day_c' if 'suhi_day_c' in gdf.columns else 'suhi_c'
gdf_clean = gdf.dropna(subset=[target_col]).copy()
p95 = gdf_clean[target_col].quantile(0.95)
print(f"Umbral térmico del percentil 95: {p95:.3f} °C")

# Celdas calientes
gdf_warm = gdf_clean[gdf_clean[target_col] >= p95].copy()
centroids = gdf_warm.to_crs(epsg=32614).geometry.centroid
coords = np.column_stack((centroids.x, centroids.y))

db = DBSCAN(eps=60, min_samples=3, n_jobs=-1)
gdf_warm['hotspot_cluster_id'] = db.fit_predict(coords)

gdf_clusters = gdf_warm[gdf_warm['hotspot_cluster_id'] != -1].copy()
n_clusters = gdf_clusters['hotspot_cluster_id'].nunique()
print(f"Número de clusters continuos detectados: {n_clusters}")


cluster_metrics = []
for cid in gdf_clusters['hotspot_cluster_id'].unique():
    c_gdf = gdf_clusters[gdf_clusters['hotspot_cluster_id'] == cid]
    n_cells = len(c_gdf)
    
    suhi_mean = c_gdf[target_col].mean()
    suhi_max = c_gdf[target_col].max()
    built_mean = c_gdf['dw_built_pct'].mean() if 'dw_built_pct' in c_gdf.columns else 0
    green_mean = c_gdf['green_pct'].mean() if 'green_pct' in c_gdf.columns else 0
    trees_mean = c_gdf['dw_trees_pct'].mean() if 'dw_trees_pct' in c_gdf.columns else 0
    elev_mean = c_gdf['elevation'].mean() if 'elevation' in c_gdf.columns else 0
    dist_ind = c_gdf['distance_to_industry_osm_m'].mean() if 'distance_to_industry_osm_m' in c_gdf.columns else 0
    
    area_ha = (n_cells * 900) / 10000
    
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

def min_max_norm(series, invert=False):
    if series.max() == series.min():
        return pd.Series(0.5, index=series.index)
    norm = (series - series.min()) / (series.max() - series.min())
    return 1 - norm if invert else norm

df_metrics['suhi_mean_norm'] = min_max_norm(df_metrics['suhi_mean'])
df_metrics['suhi_max_norm'] = min_max_norm(df_metrics['suhi_max'])
df_metrics['area_norm'] = min_max_norm(df_metrics['area_ha'])
df_metrics['built_norm'] = min_max_norm(df_metrics['built_mean'])
df_metrics['low_green_norm'] = min_max_norm(df_metrics['green_mean'], invert=True)

df_metrics['physical_criticality_score'] = (
    0.40 * df_metrics['suhi_mean_norm'] +
    0.20 * df_metrics['suhi_max_norm'] +
    0.15 * df_metrics['area_norm'] +
    0.15 * df_metrics['built_norm'] +
    0.10 * df_metrics['low_green_norm']
)

df_metrics = df_metrics.sort_values(by='physical_criticality_score', ascending=False).reset_index(drop=True)
print("Top 3 Clusters Priorizados por Criticidad Física:")
print(df_metrics[['cluster_id', 'area_ha', 'suhi_mean', 'suhi_max', 'physical_criticality_score']].head(3))
top_3_ids = df_metrics['cluster_id'].head(3).tolist()


# Clasificar zonas en la malla completa
gdf_clean_utm = gdf_clean.to_crs(epsg=32614)
gdf_clean_utm['hotspot_cluster_id'] = -1
warm_mask = gdf_clean_utm[target_col] >= p95
if warm_mask.sum() > 0:
    gdf_clean_utm_centroids = gdf_clean_utm.geometry.centroid
    warm_coords = np.column_stack((gdf_clean_utm_centroids[warm_mask].x, gdf_clean_utm_centroids[warm_mask].y))
    gdf_clean_utm.loc[warm_mask, 'hotspot_cluster_id'] = db.fit_predict(warm_coords)

gdf_clean_utm['zone'] = 'Resto de la ZMM'
gdf_clean_utm.loc[gdf_clean_utm['hotspot_cluster_id'] == top_3_ids[0], 'zone'] = 'Hotspot 1 (Cluster 44)'
gdf_clean_utm.loc[gdf_clean_utm['hotspot_cluster_id'] == top_3_ids[1], 'zone'] = 'Hotspot 2 (Cluster 66)'
gdf_clean_utm.loc[gdf_clean_utm['hotspot_cluster_id'] == top_3_ids[2], 'zone'] = 'Hotspot 3 (Cluster 5)'
gdf_clean_utm.loc[gdf_clean_utm['hotspot_cluster_id'] == 38, 'zone'] = 'Ternium (Cluster 38)'

# Zona rural de control (green_pct > 75)
gdf_rural = gdf_clean_utm[gdf_clean_utm['green_pct'] > 75.0].copy()
if len(gdf_rural) < 50:
    gdf_rural = gdf_clean_utm[gdf_clean_utm['green_pct'] > 60.0].copy()

comparison_cols = [
    'lst_day_c', 'suhi_day_c', 'green_pct', 'dw_built_pct', 
    'dw_trees_pct', 'dw_bare_pct', 'distance_to_industry_osm_m', 'elevation'
]

summary_data = []
zones = ['Hotspot 1 (Cluster 44)', 'Hotspot 2 (Cluster 66)', 'Hotspot 3 (Cluster 5)', 'Ternium (Cluster 38)', 'Resto de la ZMM']
for z in zones:
    sub = gdf_clean_utm[gdf_clean_utm['zone'] == z]
    row = {'Zona': z, 'Celdas': len(sub)}
    for col in comparison_cols:
        row[col] = sub[col].mean()
    summary_data.append(row)
    
row_rural = {'Zona': 'Zona Rural de Control', 'Celdas': len(gdf_rural)}
for col in comparison_cols:
    row_rural[col] = gdf_rural[col].mean()
summary_data.append(row_rural)

df_comp_summary = pd.DataFrame(summary_data)
print("Tabla Comparativa de Medias por Zona:")
display(df_comp_summary)


ternium_lon, ternium_lat = -100.301894, 25.722502
ternium_point_wgs84 = gpd.GeoSeries([Point(ternium_lon, ternium_lat)], crs="EPSG:4326")
ternium_point_utm = ternium_point_wgs84.to_crs(epsg=32614)
ternium_geom = ternium_point_utm.iloc[0]

ternium_buffers_stats = []
for r in [200, 100]:
    buf_geom = ternium_geom.buffer(r)
    cells_in_buf = gdf_clean_utm[gdf_clean_utm.intersects(buf_geom)].copy()
    
    gdf_clusters_utm = gdf_clusters.to_crs(epsg=32614)
    clusters_in_buf = gdf_clusters_utm[gdf_clusters_utm.intersects(buf_geom)]
    inter_cids = clusters_in_buf['hotspot_cluster_id'].unique().tolist()
    inter_cids_str = ", ".join([str(int(c)) for c in inter_cids]) if len(inter_cids) > 0 else "Ninguno"
    
    suhi_m = cells_in_buf[target_col].mean()
    suhi_max = cells_in_buf[target_col].max()
    built_m = cells_in_buf['dw_built_pct'].mean() if 'dw_built_pct' in cells_in_buf.columns else 0
    green_m = cells_in_buf['green_pct'].mean() if 'green_pct' in cells_in_buf.columns else 0
    trees_m = cells_in_buf['dw_trees_pct'].mean() if 'dw_trees_pct' in cells_in_buf.columns else 0
    
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
print("Sensibilidad del Buffer en la Ubicación Oficial de Ternium:")
display(df_ternium_stats)


fig_sat_overview = os.path.join(base_dir, "outputs", "figures", "hotspots_top3_overview_map.png")
if os.path.exists(fig_sat_overview):
    print("Mapa de Panorama General de Hotspots y Planta Ternium Guerrero:")
    display(Image(filename=fig_sat_overview))
else:
    print(f"No se encontró el mapa general en {fig_sat_overview}. Corra el script run_hotspots_analysis.py para generarlo.")


for i in range(1, 4):
    fig_sat_zoom = os.path.join(base_dir, "outputs", "figures", f"hotspot_{i}_zoom_map.png")
    if os.path.exists(fig_sat_zoom):
        print(f"\nZoom Satelital: Hotspot {i}")
        display(Image(filename=fig_sat_zoom))


fig_sat_ternium = os.path.join(base_dir, "outputs", "figures", "hotspot_ternium_zoom_map.png")
if os.path.exists(fig_sat_ternium):
    print("Zoom Térmico en la Zona de Influencia de Ternium (Radio 100m y Proximidad al Cluster 38):")
    display(Image(filename=fig_sat_ternium))


fig_bar_comp = os.path.join(base_dir, "outputs", "figures", "hotspots_physical_metrics_comparison.png")
if os.path.exists(fig_bar_comp):
    print("Gráfico Comparativo Multizona de Variables Físicas y de Distancia:")
    display(Image(filename=fig_bar_comp))

