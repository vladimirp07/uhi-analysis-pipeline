"""
uhi-mty-mvp: Módulo de Métricas SUHI Multitemporal
==================================================
Calcula anomalías térmicas diurnas y nocturnas con líneas base de control vegetal.
"""

import numpy as np
import geopandas as gpd
from src.config import INTERIM_DIR, PROCESSED_DIR

def calculate_suhi_intensity():
    """
    Calcula de forma independiente la intensidad de la isla de calor diurna (suhi_day_c)
    y nocturna (suhi_night_c) utilizando sus respectivas líneas base de control
    basadas en celdas con alta vegetación (green_pct > 75%).
    Guarda el GeoDataFrame final en data/processed/malla_maestra_mty_2026.gpkg.
    
    Returns:
        gpd.GeoDataFrame: Dataset maestro con las métricas finales de SUHI.
    """
    print("\n[UHI_METRICS] Calculando anomalías térmicas SUHI Diurnas y Nocturnas...")
    
    ind_path = INTERIM_DIR / "malla_industria_2026.gpkg"
    feat_path = INTERIM_DIR / "malla_features_2026.gpkg"
    output_path = PROCESSED_DIR / "malla_maestra_mty_2026.gpkg"
    
    if ind_path.exists():
        input_path = ind_path
        print("[UHI_METRICS] Cargando malla enriquecida con datos industriales...")
    elif feat_path.exists():
        input_path = feat_path
        print("[UHI_METRICS] Cargando malla con variables satelitales...")
    else:
        raise FileNotFoundError(f"No se encontró archivo de características intermedias en {feat_path}")
        
    gdf = gpd.read_file(input_path)
    print(f"[UHI_METRICS] Base de datos cargada con {len(gdf)} celdas.")
    
    # Umbrales de vegetación
    threshold_high = 75.0
    threshold_low = 60.0
    
    # --- 1. CÁLCULO DIURNO (DAY) ---
    gdf_valid_day = gdf.dropna(subset=["lst_day_c"])
    
    # Intentar leer la temperatura rural de referencia calculada en GEE (fuera de la ZMM)
    rural_temp_path = INTERIM_DIR / "rural_temp_day.txt"
    if rural_temp_path.exists():
        try:
            with open(rural_temp_path, "r") as f:
                mediana_rural_lst_day = float(f.read().strip())
            print(f"[UHI_METRICS] Usando referencia rural externa de GEE (Pesquería/Cadereyta): {mediana_rural_lst_day:.2f}°C")
        except Exception as e:
            print(f"[UHI_METRICS] Error al leer cache rural: {e}. Usando fallback local.")
            rural_temp_path = None
            
    if not rural_temp_path.exists():
        # Fallback local: Umbrales de vegetación urbana
        threshold_high = 75.0
        threshold_low = 60.0
        rural_candidates_day = gdf_valid_day[gdf_valid_day["green_pct"] > threshold_high]
        if len(rural_candidates_day) < 50:
            print(f"[UHI_METRICS] Pocas celdas diurnas con green_pct > {threshold_high}%. Intentando > {threshold_low}%.")
            rural_candidates_day = gdf_valid_day[gdf_valid_day["green_pct"] > threshold_low]
        if len(rural_candidates_day) == 0:
            print("[UHI_METRICS] Advertencia: Sin celdas diurnas en umbral. Usando el 10% con mayor green_pct.")
            q90 = gdf_valid_day["green_pct"].quantile(0.90)
            rural_candidates_day = gdf_valid_day[gdf_valid_day["green_pct"] >= q90]
            
        mediana_rural_lst_day = float(rural_candidates_day["lst_day_c"].median())
        print(f"[UHI_METRICS] Referencia rural Diurna (local/fallback): {mediana_rural_lst_day:.2f}°C (Basada en {len(rural_candidates_day)} celdas)")
        
    gdf["suhi_day_c"] = gdf["lst_day_c"] - mediana_rural_lst_day
    gdf["suhi_c"] = gdf["suhi_day_c"]  # Copia de compatibilidad en gráficos
    
    # --- 2. CÁLCULO NOCTURNO (NIGHT) ---
    # Desactivado por ahora a petición del usuario. Rellenado con NaN.
    print("[UHI_METRICS] Análisis nocturno desactivado. Rellenando suhi_night_c con NaN.")
    gdf["suhi_night_c"] = np.nan
    
    # Guardar conjunto final procesado (Malla Maestra)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    gdf.to_file(output_path, driver="GPKG", mode="w")
    print(f"[UHI_METRICS] Malla maestra final guardada en: {output_path}")
    
    valid_suhi_day = gdf["suhi_day_c"].dropna()
    print(f"[UHI_METRICS] Resumen SUHI Día: Promedio={valid_suhi_day.mean():.2f}°C, Máximo={valid_suhi_day.max():.2f}°C, Mínimo={valid_suhi_day.min():.2f}°C")
    
    valid_suhi_night = gdf["suhi_night_c"].dropna()
    if len(valid_suhi_night) > 0:
        print(f"[UHI_METRICS] Resumen SUHI Noche: Promedio={valid_suhi_night.mean():.2f}°C, Máximo={valid_suhi_night.max():.2f}°C, Mínimo={valid_suhi_night.min():.2f}°C")
        
    return gdf
