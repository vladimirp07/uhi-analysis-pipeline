"""
Módulo para el procesamiento, agregación zonal y análisis a escala de AGEBs (INEGI).
"""

import os
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
from src.config import INTERIM_DIR, PROCESSED_DIR

def aggregate_to_ageb_scale(malla_gdf=None):
    """
    Realiza la agregación zonal de variables físicas de la cuadrícula de 30m
    a nivel de polígono de AGEB, conservando además las variables demográficas normalizadas.
    Guarda el resultado en data/processed/ageb_maestra_mty_2026.gpkg.
    
    Args:
        malla_gdf (gpd.GeoDataFrame, optional): Malla maestra escala 30m.
        
    Returns:
        gpd.GeoDataFrame: Polígonos de AGEB con promedios físicos y datos demográficos.
    """
    print("\n[AGEB SOCIAL] Iniciando agregación espacial a escala AGEB (Zonal Statistics)...")
    
    # 1. Cargar la malla de 30m si no se pasa como argumento
    if malla_gdf is None:
        malla_path = PROCESSED_DIR / "malla_maestra_mty_2026_v2.gpkg"
        if not malla_path.exists():
            raise FileNotFoundError(f"No se encontró la malla maestra v2 en: {malla_path}")
        malla_gdf = gpd.read_file(malla_path)
        
    print(f"[AGEB SOCIAL] Malla base de 30m cargada con {len(malla_gdf)} celdas.")
    
    # 2. Cargar el censo real de AGEBs (CSV)
    csv_path = Path(__file__).resolve().parent.parent / "data" / "raw" / "RESAGEBURB2020 - 19 Nuevo León (1).csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"No se encontró el censo CSV en: {csv_path}")
        
    print(f"[AGEB SOCIAL] Cargando censo CSV desde: {csv_path}")
    censo_df = pd.read_csv(csv_path)
    
    # Filtrar a nivel AGEB
    censo_ageb = censo_df[(censo_df["MZA"] == 0) & (censo_df["AGEB"].astype(str) != "0") & (censo_df["AGEB"].notna())].copy()
    
    # Construir la clave geoestadística única de 13 dígitos
    censo_ageb["CVEGEO"] = (
        censo_ageb["ENTIDAD"].astype(str).str.zfill(2) +
        censo_ageb["MUN"].astype(str).str.zfill(3) +
        censo_ageb["LOC"].astype(str).str.zfill(4) +
        censo_ageb["AGEB"].astype(str).str.split('.').str[0].str.zfill(4)
    )
    
    # Seleccionar variables clave y convertirlas a numéricas
    vars_sum = [
        "POBTOT", "POB0_14", "POB65_MAS", "P_60YMAS", "P3YM_HLI", "PSINDER",
        "VIVPAR_HAB", "VPH_REFRI", "VPH_TINACO", "VPH_CISTER", "VPH_SNBIEN", "VPH_NDEAED"
    ]
    vars_mean = ["GRAPROES"]
    
    for v in vars_sum + vars_mean:
        censo_ageb[v] = pd.to_numeric(censo_ageb[v], errors="coerce").fillna(0.0)
        
    # Agrupar por CVEGEO usando suma para conteos y promedio para promedios
    agg_dict = {v: "sum" for v in vars_sum}
    agg_dict["GRAPROES"] = "mean"
    censo_grouped = censo_ageb.groupby("CVEGEO").agg(agg_dict).reset_index()
    print(f"[AGEB SOCIAL] Censo procesado. Total de AGEBs en catálogo censal: {len(censo_grouped)}")

    
    # 3. Cargar los polígonos oficiales reales de la ZMM
    json_path = Path(__file__).resolve().parent.parent / "data" / "raw" / "AGEB_ZMM_Dani.json"
    if not json_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo de límites espaciales en: {json_path}")
        
    print(f"[AGEB SOCIAL] Cargando polígonos de AGEB oficiales desde: {json_path.name}")
    agebs_gdf = gpd.read_file(json_path)
    inegi_utm = agebs_gdf.to_crs(epsg=32614)
    
    # Ajustar columna clave
    if "CVEGEO" in inegi_utm.columns:
        inegi_utm["CVEGEO"] = inegi_utm["CVEGEO"].astype(str)
    elif "CVEGEO_1" in inegi_utm.columns:
        inegi_utm["CVEGEO"] = inegi_utm["CVEGEO_1"].astype(str)
        
    # Eliminar duplicados antes de cruzar
    cols_to_drop = [c for c in censo_grouped.columns if c in inegi_utm.columns and c != "CVEGEO"]
    if cols_to_drop:
        inegi_utm = inegi_utm.drop(columns=cols_to_drop)
        
    # Calcular el área en kilómetros cuadrados para densidad demográfica
    inegi_utm["area_km2"] = inegi_utm.geometry.area / 10**6
    
    # Realizar el merge censo -> polígonos
    ageb_enriched = inegi_utm.merge(censo_grouped, on="CVEGEO", how="inner")
    print(f"[AGEB SOCIAL] Polígonos de AGEB vinculados al censo: {len(ageb_enriched)}")
    
    # Calcular variables demográficas y socioeconómicas derivadas (normalizadas)
    safe_pobtot = ageb_enriched["POBTOT"].replace(0, np.nan)
    safe_vivpar = ageb_enriched["VIVPAR_HAB"].replace(0, np.nan)
    
    ageb_enriched["pop_density_ageb"] = ageb_enriched["POBTOT"] / ageb_enriched["area_km2"]
    ageb_enriched["pct_0_14"] = (ageb_enriched["POB0_14"] / safe_pobtot * 100.0).fillna(0.0)
    ageb_enriched["pct_65_mas"] = (ageb_enriched["POB65_MAS"] / safe_pobtot * 100.0).fillna(0.0)
    ageb_enriched["pct_60ymas"] = (ageb_enriched["P_60YMAS"] / safe_pobtot * 100.0).fillna(0.0)
    ageb_enriched["pct_hli"] = (ageb_enriched["P3YM_HLI"] / safe_pobtot * 100.0).fillna(0.0)
    
    # Nuevas variables demográficas y socioeconómicas
    ageb_enriched["pct_psinder"] = (ageb_enriched["PSINDER"] / safe_pobtot * 100.0).fillna(0.0)
    ageb_enriched["graproes"] = ageb_enriched["GRAPROES"]
    ageb_enriched = ageb_enriched.drop(columns=["GRAPROES"])
    
    # Nuevas variables de vivienda (normalizadas por Viviendas Particulares Habitadas)
    ageb_enriched["pct_vph_refri"] = (ageb_enriched["VPH_REFRI"] / safe_vivpar * 100.0).fillna(0.0)
    ageb_enriched["pct_vph_tinaco"] = (ageb_enriched["VPH_TINACO"] / safe_vivpar * 100.0).fillna(0.0)
    ageb_enriched["pct_vph_cister"] = (ageb_enriched["VPH_CISTER"] / safe_vivpar * 100.0).fillna(0.0)
    ageb_enriched["pct_vph_snbien"] = (ageb_enriched["VPH_SNBIEN"] / safe_vivpar * 100.0).fillna(0.0)
    ageb_enriched["pct_vph_ndeaed"] = (ageb_enriched["VPH_NDEAED"] / safe_vivpar * 100.0).fillna(0.0)

    
    # 4. Agregación Zonal: Cruzar centroides de las celdas de 30m con los polígonos de AGEB
    grid_utm = malla_gdf.to_crs(epsg=32614)
    centroids = grid_utm.geometry.centroid
    
    physical_cols = [
        "lst_c", "suhi_c", "lst_day_c", "lst_night_c", "suhi_day_c", "suhi_night_c",
        "green_pct", "industrial_osm_pct", "dw_built_pct", "dw_trees_pct"
    ]
    valid_phys_cols = [c for c in physical_cols if c in grid_utm.columns]
    
    centroids_gdf = gpd.GeoDataFrame(
        grid_utm[valid_phys_cols],
        geometry=centroids,
        crs="EPSG:32614"
    )
    
    print("[AGEB SOCIAL] Ejecutando Spatial Join de centroides de celdas dentro de polígonos de AGEB...")
    joined = gpd.sjoin(centroids_gdf, ageb_enriched[["CVEGEO", "geometry"]], how="inner", predicate="within")
    
    # Calcular promedios zonales por AGEB
    print("[AGEB SOCIAL] Calculando promedios zonales para las variables físicas...")
    ageb_stats = joined.groupby("CVEGEO")[valid_phys_cols].mean().reset_index()
    
    # Unir estadísticas físicas promedio con los polígonos enriquecidos
    ageb_maestra = ageb_enriched.merge(ageb_stats, on="CVEGEO", how="inner")
    print(f"[AGEB SOCIAL] AGEB maestra consolidada con estadísticas zonales: {len(ageb_maestra)} polígonos.")
    
    # 5. Guardar archivo final
    output_path = PROCESSED_DIR / "ageb_maestra_mty_2026.gpkg"
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    ageb_maestra.to_file(output_path, driver="GPKG", mode="w")
    print(f"[AGEB SOCIAL] Archivo de escala AGEB guardado exitosamente en: {output_path}")
    
    return ageb_maestra

def merge_inegi_ageb(malla_gdf, inegi_shp_path=None):
    """
    Wrapper legacy para compatibilidad con versiones previas del pipeline.
    Invoca la agregación zonal y retorna la malla sin modificar.
    """
    print("[AGEB SOCIAL] [Legacy Wrapper] merge_inegi_ageb() invocado. Redirigiendo a aggregate_to_ageb_scale()...")
    aggregate_to_ageb_scale(malla_gdf)
    return malla_gdf
