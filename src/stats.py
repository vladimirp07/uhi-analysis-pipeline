"""
uhi-mty-mvp: Análisis Estadístico Multitemporal
================================================
Calcula las matrices de correlación de Spearman para variables diurnas y nocturnas.
"""

import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
from src.config import FIGURES_DIR, PROCESSED_DIR


def plot_correlation_matrix(malla_gdf):
    """
    Selecciona las variables numéricas de la malla y genera dos matrices de correlación de Spearman separadas:
    1. Física/Ambiental (escala de 30m): LST Día/Noche, SUHI Día/Noche, vegetación, industria, distancias.
    2. Socioambiental (escala de AGEB): promedios térmicos zonales contra las variables normalizadas del INEGI.
    
    Guarda las imágenes en outputs/figures/.
    
    Args:
        malla_gdf (gpd.GeoDataFrame): Malla maestra escala 30m (v3).
        
    Returns:
        pd.DataFrame: Matriz de correlación física calculada.
    """
    print("\n[STATS] Generando matrices de correlación a dos escalas...")
    
    # 1. MATRIZ 1: Física/Ambiental (escala 30m)
    physical_cols = [
        "lst_day_c", "suhi_day_c",
        "green_pct", "industrial_osm_pct",
        "dw_built_pct", "dw_trees_pct", "dw_bare_pct", "dw_water_pct", "dw_grass_pct",
        "distance_to_industry_osm_m", "distance_to_ternium_m", "distance_to_water_m"
    ]
    
    valid_phys = [c for c in physical_cols if c in malla_gdf.columns]
    df_phys = pd.DataFrame(malla_gdf[valid_phys].drop(columns=["geometry"], errors="ignore")).dropna()
    corr_phys = df_phys.corr(method="spearman")
    
    # Graficar Matriz 1
    plt.figure(figsize=(15, 12))
    sns.heatmap(
        corr_phys,
        annot=True,
        cmap="coolwarm",
        fmt=".2f",
        vmin=-1.0,
        vmax=1.0,
        linewidths=0.5,
        cbar_kws={"label": "Coeficiente de Correlación de Spearman"}
    )
    plt.title("Matriz de Correlación Física/Ambiental (Escala 30m) - Monterrey 2026", fontsize=14, fontweight="bold", pad=15)
    plt.xticks(rotation=45, ha="right")
    plt.yticks(rotation=0)
    plt.tight_layout()
    
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    out_phys = FIGURES_DIR / "04_correlacion_spearman_ambiental_30m.png"
    plt.savefig(out_phys, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[STATS] Heatmap de correlación ambiental Spearman (30m) guardado en: {out_phys}")

    
    # 2. MATRIZ 2: Socioambiental (escala AGEB)
    ageb_file_path = PROCESSED_DIR / "ageb_maestra_mty_2026.gpkg"
    if not ageb_file_path.exists():
        print(f"[STATS] El archivo a escala AGEB no existe en {ageb_file_path}. Ejecutando agregación zonal...")
        from src.ageb_social import aggregate_to_ageb_scale
        ageb_gdf = aggregate_to_ageb_scale(malla_gdf)
    else:
        print(f"[STATS] Cargando capa maestra a escala AGEB desde: {ageb_file_path}")
        ageb_gdf = gpd.read_file(ageb_file_path)

        
    social_cols = [
        "lst_day_c", "suhi_day_c",
        "green_pct", "industrial_osm_pct", "dw_built_pct", "dw_trees_pct",
        "pop_density_ageb", "pct_0_14", "pct_65_mas", "pct_60ymas", "pct_hli",
        "pct_psinder", "graproes", "pct_vph_refri", "pct_vph_tinaco", "pct_vph_cister",
        "pct_vph_snbien", "pct_vph_ndeaed"
    ]

    
    valid_social = [c for c in social_cols if c in ageb_gdf.columns]
    df_social = pd.DataFrame(ageb_gdf[valid_social].drop(columns=["geometry"], errors="ignore")).dropna()
    corr_social = df_social.corr(method="spearman")
    
    # Graficar Matriz 2
    plt.figure(figsize=(14, 11))
    sns.heatmap(
        corr_social,
        annot=True,
        cmap="coolwarm",
        fmt=".2f",
        vmin=-1.0,
        vmax=1.0,
        linewidths=0.5,
        cbar_kws={"label": "Coeficiente de Correlación de Spearman"}
    )
    plt.title("Matriz de Correlación Socioambiental (Escala AGEB) - Monterrey 2026", fontsize=14, fontweight="bold", pad=15)
    plt.xticks(rotation=45, ha="right")
    plt.yticks(rotation=0)
    plt.tight_layout()
    
    out_social = FIGURES_DIR / "05_correlacion_spearman_socioambiental_ageb.png"
    plt.savefig(out_social, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[STATS] Heatmap de correlación socioambiental Spearman (AGEB) guardado en: {out_social}")

    
    # 3. Reporte de Validación en Terminal
    print("\n" + "="*80)
    print("   REPORTE DE AUDITORÍA: ARQUITECTURA DE DOS ESCALAS MULTITEMPORAL (SPEARMAN)")
    print("="*80)
    
    # Top 3 correlaciones físicas diurnas con suhi_day_c a escala 30m
    if "suhi_day_c" in corr_phys.columns:
        exclude = ["suhi_day_c", "suhi_night_c", "lst_day_c", "lst_night_c", "lst_c", "suhi_c"]
        suhi_day_phys = corr_phys["suhi_day_c"].drop(labels=exclude, errors="ignore").abs().sort_values(ascending=False).head(3)
        print(">>> Top 3 de correlaciones físicas DIURNAS a escala 30m:")
        for var, val in suhi_day_phys.items():
            print(f"  * {var:.<40} Coeficiente: {corr_phys.loc['suhi_day_c', var]:+.3f} (Abs: {val:.3f})")
            
    # Top 3 correlaciones físicas nocturnas con suhi_night_c a escala 30m
    if "suhi_night_c" in corr_phys.columns:
        exclude = ["suhi_day_c", "suhi_night_c", "lst_day_c", "lst_night_c", "lst_c", "suhi_c"]
        suhi_night_phys = corr_phys["suhi_night_c"].drop(labels=exclude, errors="ignore").abs().sort_values(ascending=False).head(3)
        print("\n>>> Top 3 de correlaciones físicas NOCTURNAS a escala 30m:")
        for var, val in suhi_night_phys.items():
            print(f"  * {var:.<40} Coeficiente: {corr_phys.loc['suhi_night_c', var]:+.3f} (Abs: {val:.3f})")
            
    # Top 3 correlaciones sociales diurnas con suhi_day_c a escala AGEB
    if "suhi_day_c" in corr_social.columns:
        demographic_cols = [
            "pop_density_ageb", "pct_0_14", "pct_65_mas", "pct_60ymas", "pct_hli",
            "pct_psinder", "graproes", "pct_vph_refri", "pct_vph_tinaco", "pct_vph_cister",
            "pct_vph_snbien", "pct_vph_ndeaed"
        ]
        valid_demog = [d for d in demographic_cols if d in corr_social.columns]

        
        suhi_day_soc = corr_social.loc[valid_demog, "suhi_day_c"].abs().sort_values(ascending=False).head(3)
        print("\n>>> Top 3 de correlaciones sociales DIURNAS a escala AGEB:")
        for var, val in suhi_day_soc.items():
            print(f"  * {var:.<40} Coeficiente: {corr_social.loc['suhi_day_c', var]:+.3f} (Abs: {val:.3f})")
            
    # Top 3 correlaciones sociales nocturnas con suhi_night_c a escala AGEB
    if "suhi_night_c" in corr_social.columns:
        demographic_cols = [
            "pop_density_ageb", "pct_0_14", "pct_65_mas", "pct_60ymas", "pct_hli",
            "pct_psinder", "graproes", "pct_vph_refri", "pct_vph_tinaco", "pct_vph_cister",
            "pct_vph_snbien", "pct_vph_ndeaed"
        ]
        valid_demog = [d for d in demographic_cols if d in corr_social.columns]

        
        suhi_night_soc = corr_social.loc[valid_demog, "suhi_night_c"].abs().sort_values(ascending=False).head(3)
        print("\n>>> Top 3 de correlaciones sociales NOCTURNAS a escala AGEB:")
        for var, val in suhi_night_soc.items():
            print(f"  * {var:.<40} Coeficiente: {corr_social.loc['suhi_night_c', var]:+.3f} (Abs: {val:.3f})")
            
    print(f"\n>>> Confirmación de cobertura de polígonos:")
    print(f"  * Polígonos de AGEB integrados en el análisis final: {len(ageb_gdf)}")
    print("="*80 + "\n")
    
    # 4. Guardar tabla de correlaciones consolidada en outputs/tables/05_correlaciones_maestras.csv
    try:
        tables_dir = FIGURES_DIR.parent / "tables"
        tables_dir.mkdir(parents=True, exist_ok=True)
        csv_path = tables_dir / "05_correlaciones_maestras.csv"
        
        rows = []
        # Agregar correlaciones escala 30m
        exclude_lst_suhi = ["lst_c", "suhi_c", "lst_day_c", "lst_night_c", "suhi_day_c", "suhi_night_c"]
        for var in corr_phys.index:
            if var not in exclude_lst_suhi:
                rows.append({
                    "variable": var,
                    "scale": "30m",
                    "correlation_suhi_day": corr_phys.loc[var, "suhi_day_c"] if "suhi_day_c" in corr_phys.columns else np.nan,
                    "correlation_suhi_night": corr_phys.loc[var, "suhi_night_c"] if "suhi_night_c" in corr_phys.columns else np.nan,
                    "correlation_lst_day": corr_phys.loc[var, "lst_day_c"] if "lst_day_c" in corr_phys.columns else np.nan,
                    "correlation_lst_night": corr_phys.loc[var, "lst_night_c"] if "lst_night_c" in corr_phys.columns else np.nan
                })
        # Agregar correlaciones escala AGEB
        for var in corr_social.index:
            if var not in exclude_lst_suhi:
                rows.append({
                    "variable": var,
                    "scale": "AGEB",
                    "correlation_suhi_day": corr_social.loc[var, "suhi_day_c"] if "suhi_day_c" in corr_social.columns else np.nan,
                    "correlation_suhi_night": corr_social.loc[var, "suhi_night_c"] if "suhi_night_c" in corr_social.columns else np.nan,
                    "correlation_lst_day": corr_social.loc[var, "lst_day_c"] if "lst_day_c" in corr_social.columns else np.nan,
                    "correlation_lst_night": corr_social.loc[var, "lst_night_c"] if "lst_night_c" in corr_social.columns else np.nan
                })
                
        df_out = pd.DataFrame(rows)
        # Ordenar por el valor absoluto de la correlación con SUHI diurno para facilitar lectura
        df_out["abs_corr_suhi_day"] = df_out["correlation_suhi_day"].abs()
        df_out = df_out.sort_values(by="abs_corr_suhi_day", ascending=False).drop(columns=["abs_corr_suhi_day"])
        
        df_out.to_csv(csv_path, index=False, encoding="utf-8")
        print(f"[STATS] Tabla de correlaciones consolidadas (Día/Noche) guardada en: {csv_path}")
    except Exception as e:
        print(f"[STATS] Advertencia: No se pudo guardar la tabla CSV: {e}")
        
    return corr_phys
