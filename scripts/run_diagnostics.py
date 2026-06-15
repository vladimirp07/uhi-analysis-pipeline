import json
import numpy as np
import pandas as pd
import geopandas as gpd

def run_diagnostics():
    print("=== INICIANDO CORRIDA DE DIAGNÓSTICOS ===")
    
    # 1. Cargar datos
    import sys
    import pathlib
    base_dir = pathlib.Path(__file__).resolve().parent.parent
    sys.path.append(str(base_dir))
    census_csv_path = base_dir / "data" / "raw" / "RESAGEBURB2020 - 19 Nuevo León (1).csv"
    ageb_geojson_path = base_dir / "data" / "raw" / "AGEB_ZMM_Dani.json"
    malla_v3_path = base_dir / "data" / "processed" / "malla_maestra_mty_2026_v3.gpkg"
    
    censo = pd.read_csv(census_csv_path)
    agebs = gpd.read_file(ageb_geojson_path)
    malla = gpd.read_file(malla_v3_path)
    
    # --- BLOQUE 1: DIAGNÓSTICO DE INTEGRACIÓN AGEB ---
    print("\n--- 1. INTEGRACIÓN AGEB ---")
    print(f"¿Geometrías reales en GeoJSON?: {not agebs.geometry.is_empty.all() and agebs.crs is not None}")
    print(f"Total polígonos en GeoJSON: {len(agebs)}")
    
    censo_ageb = censo[(censo["MZA"] == 0) & (censo["AGEB"].astype(str) != "0") & (censo["AGEB"].notna())].copy()
    censo_ageb["CVEGEO"] = (
        censo_ageb["ENTIDAD"].astype(str).str.zfill(2) +
        censo_ageb["MUN"].astype(str).str.zfill(3) +
        censo_ageb["LOC"].astype(str).str.zfill(4) +
        censo_ageb["AGEB"].astype(str).str.split('.').str[0].str.zfill(4)
    )
    # Convert variables to numeric
    vars_sociales = ["POBTOT", "POBFEM", "POBMAS", "POB0_14", "POB65_MAS", "P_60YMAS", "P3YM_HLI"]
    for v in vars_sociales:
        censo_ageb[v] = pd.to_numeric(censo_ageb[v], errors="coerce").fillna(0.0)
        
    censo_grouped = censo_ageb.groupby("CVEGEO")[vars_sociales].sum().reset_index()
    
    matched_agebs = agebs.merge(censo_grouped, on="CVEGEO", how="inner")
    unmatched_agebs = len(agebs) - len(matched_agebs)
    print(f"Polígonos que hicieron match con el censo: {len(matched_agebs)}")
    print(f"Polígonos sin datos censales (unmatched): {unmatched_agebs}")
    
    # Celdas y spatial join
    # Verificar cuántas celdas tienen AGEB asignado (en malla, CVEGEO no es nulo)
    cells_with_ageb = malla["CVEGEO"].notna().sum()
    cells_without_ageb = malla["CVEGEO"].isna().sum()
    print(f"Celdas de 30m con AGEB asignado: {cells_with_ageb}")
    print(f"Celdas de 30m sin AGEB asignado: {cells_without_ageb}")
    
    # Como la malla tiene ID único por celda (cell_id), y el sjoin se resolvió con left join en centroides,
    # verificamos duplicados de cell_id en el joined_data antes del merge final.
    # Vamos a recrear el spatial join para auditarlo
    grid_utm = malla.to_crs(epsg=32614)
    centroids = grid_utm.geometry.centroid
    centroids_gdf = gpd.GeoDataFrame(malla[["cell_id"]], geometry=centroids, crs="EPSG:32614")
    
    agebs_utm = agebs.to_crs(epsg=32614)
    # Hacer el sjoin directo
    sjoined = gpd.sjoin(centroids_gdf, agebs_utm, how="left", predicate="within")
    
    # Duplicados
    cell_counts = sjoined["cell_id"].value_counts()
    cells_multiple_ageb = (cell_counts > 1).sum()
    print(f"Celdas con más de un AGEB asignado en sjoin: {cells_multiple_ageb}")
    
    # Centroides fuera de cualquier AGEB
    centroids_outside = sjoined["index_right"].isna().sum()
    print(f"Centroides fuera de cualquier polígono de AGEB: {centroids_outside}")
    
    # Validar CVEGEO longitud
    cvegeo_len_spatial = agebs["CVEGEO"].astype(str).str.len().unique()
    cvegeo_len_censo = censo_grouped["CVEGEO"].astype(str).str.len().unique()
    print(f"Formatos CVEGEO espacial (longitud): {cvegeo_len_spatial}")
    print(f"Formatos CVEGEO censo (longitud): {cvegeo_len_censo}")
    
    # --- BLOQUE 2: DIAGNÓSTICO DE VARIABLES DE PORCENTAJE ---
    print("\n--- 2. VARIABLES DE PORCENTAJE ---")
    pct_cols = ["green_pct", "industrial_osm_pct", "dw_built_pct", "dw_trees_pct", "dw_bare_pct", "dw_water_pct", "dw_grass_pct"]
    
    pct_data = []
    for c in pct_cols:
        if c in malla.columns:
            vals = malla[c].dropna()
            min_val = vals.min()
            max_val = vals.max()
            mean_val = vals.mean()
            less_0 = (vals < 0).sum()
            greater_100 = (vals > 100).sum()
            
            # Detectar escala
            if max_val <= 1.05 and min_val >= -0.05:
                scale = "0-1"
            else:
                scale = "0-100"
                
            pct_data.append({
                "Variable": c,
                "Min": min_val,
                "Max": max_val,
                "Mean": mean_val,
                "Valores < 0": less_0,
                "Valores > 100": greater_100,
                "Escala": scale
            })
            
    df_pct_audit = pd.DataFrame(pct_data)
    print(df_pct_audit.to_string(index=False))
    
    # --- BLOQUE 3: DIAGNÓSTICO DE VARIABLES DEMOGRÁFICAS ---
    print("\n--- 3. VARIABLES DEMOGRÁFICAS ---")
    # Cargar geometries de AGEB urbanos reales y calcular área
    agebs_utm["area_km2"] = agebs_utm.geometry.area / 10**6
    
    # Merge con censo de variables absolutas completo
    censo_vars = censo_ageb.groupby("CVEGEO")[["POBTOT", "POBFEM", "POBMAS", "POB0_14", "POB65_MAS", "P_60YMAS", "P3YM_HLI"]].sum().reset_index()
    cols_to_drop = [c for c in censo_vars.columns if c in agebs_utm.columns and c != "CVEGEO"]
    if cols_to_drop:
        agebs_utm = agebs_utm.drop(columns=cols_to_drop)
    agebs_enriched = agebs_utm.merge(censo_vars, on="CVEGEO", how="inner")
    print("Total filas agebs_enriched:", len(agebs_enriched))
    
    # Calcular derivadas en los polígonos
    # Para evitar divisiones entre cero
    safe_pobtot = agebs_enriched["POBTOT"].replace(0, np.nan)
    agebs_enriched["pop_density_ageb"] = agebs_enriched["POBTOT"] / agebs_enriched["area_km2"]
    agebs_enriched["pct_0_14"] = agebs_enriched["POB0_14"] / safe_pobtot * 100.0
    agebs_enriched["pct_65_mas"] = agebs_enriched["POB65_MAS"] / safe_pobtot * 100.0
    agebs_enriched["pct_60ymas"] = agebs_enriched["P_60YMAS"] / safe_pobtot * 100.0
    agebs_enriched["pct_hli"] = agebs_enriched["P3YM_HLI"] / safe_pobtot * 100.0
    
    # Rellenar nulos de división con 0
    deriv_cols = ["pop_density_ageb", "pct_0_14", "pct_65_mas", "pct_60ymas", "pct_hli"]
    for c in deriv_cols:
        agebs_enriched[c] = agebs_enriched[c].fillna(0.0)
        
    print("Estadísticas de Variables Derivadas calculadas a nivel AGEB:")
    print(agebs_enriched[deriv_cols + ["POBTOT", "area_km2"]].describe().loc[["min", "max", "mean"]])
    
    # --- BLOQUE 5: CONFIRMACIÓN LST Y SUHI ---
    print("\n--- 5. LST Y SUHI ---")
    valid_lst = malla["lst_c"].dropna()
    print(f"LST Min: {valid_lst.min():.2f}°C, Max: {valid_lst.max():.2f}°C, Mean: {valid_lst.mean():.2f}°C")
    
    # Cargar uhi_metrics.py para ver lógica rural
    # Vamos a calcular correlación de Spearman para variables derivadas
    # Necesitamos unir las variables derivadas de los AGEB a cada celda de 30m
    ageb_deriv = agebs_enriched[["CVEGEO", "pop_density_ageb", "pct_0_14", "pct_65_mas", "pct_60ymas", "pct_hli"]]
    malla_joined = grid_utm.merge(ageb_deriv, on="CVEGEO", how="left")
    
    # Rellenar nulos en la malla final
    for c in deriv_cols:
        malla_joined[c] = malla_joined[c].fillna(0.0)
        
    # Calcular correlaciones de Spearman frente a suhi_c
    suhi_corrs = malla_joined[deriv_cols + ["suhi_c", "lst_c"]].corr(method="spearman")
    print("\nCorrelación de Spearman de Variables Derivadas frente a suhi_c y lst_c:")
    print(suhi_corrs[["suhi_c", "lst_c"]].loc[deriv_cols])

if __name__ == "__main__":
    run_diagnostics()
