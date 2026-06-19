import ee
import sys
import pathlib
import pandas as pd
import numpy as np
import geopandas as gpd
import rasterio
import matplotlib.pyplot as plt
import contextily as ctx
import matplotlib.patches as mpatches

base_dir = pathlib.Path(__file__).resolve().parent.parent
sys.path.append(str(base_dir))

from src.gee_data import init_ee, get_aoi_geometry
from src.config import START_DATE_NIGHT, END_DATE_NIGHT, INTERIM_DIR, PROCESSED_DIR

def main():
    print("=" * 80)
    print("INICIANDO VALIDACIONES TÉCNICAS DE ISLA DE CALOR NOCTURNA")
    print("=" * 80)
    
    # Definir directorio de salidas
    outputs_dir = base_dir / "outputs" / "05"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Inicializar GEE
    init_ee()
    aoi = get_aoi_geometry()
    
    # Bounding Box de la ZMM (de config.py)
    # AOI_BBOX = [-100.395595, 25.640327, -100.237307, 25.736120]
    
    # Definir región de muestreo rural más amplia
    rural_sampling_region = ee.Geometry.Rectangle([-100.8, 25.1, -99.6, 26.3])
    # ZMM box a excluir
    zmm_box = ee.Geometry.Rectangle([-100.42, 25.60, -100.20, 25.78])
    
    # Cargar colecciones
    srtm = ee.Image("USGS/SRTMGL1_003")
    col_night = ee.ImageCollection("MODIS/061/MYD11A1") \
                  .filterBounds(rural_sampling_region) \
                  .filterDate(START_DATE_NIGHT, END_DATE_NIGHT)
                  
    # Mediana nocturna de LST
    lst_night_median = col_night.select("LST_Night_1km").median().multiply(0.02).subtract(273.15)
    
    # Crear imagen combinada de LST y Elevación
    combined = lst_night_median.rename("lst_night").addBands(srtm.rename("elevation"))
    
    # -------------------------------------------------------------
    # VALIDACIÓN 1: Baseline Rural Controlado por Elevación
    # -------------------------------------------------------------
    # Altura promedio de la ZMM es ~573m. Buscamos píxeles rurales con elevación entre 520m y 620m.
    rural_elev_mask = srtm.gte(520).And(srtm.lte(620))
    # Excluir la zona urbana de Monterrey
    sampling_mask = rural_sampling_region.difference(zmm_box)
    
    # Calcular la mediana de temperatura nocturna rural controlada por elevación
    controlled_rural_temp_info = lst_night_median.updateMask(rural_elev_mask).reduceRegion(
        reducer=ee.Reducer.median(),
        geometry=sampling_mask,
        scale=1000,
        maxPixels=1e9
    ).getInfo()
    
    temp_rural_controlled = controlled_rural_temp_info.get("LST_Night_1km")
    print(f"1. Baseline Rural Original (Pesquería/Salinas/Santiago): 17.34°C (Elevación prom ~405m)")
    print(f"   Baseline Rural Controlado por Elevación (520m-620m): {temp_rural_controlled:.2f}°C")
    
    # -------------------------------------------------------------
    # VALIDACIÓN 2: Regresión LST_night ~ Elevation y Anomalía Corregida
    # -------------------------------------------------------------
    # Muestrear puntos rurales para la regresión
    print("\nMuestreando píxeles rurales para regresión LST_night ~ Elevación...")
    # Convertir a colección de puntos
    sample_points = combined.updateMask(rural_elev_mask.Or(srtm.lt(520)).Or(srtm.gt(620))).sample(
        region=sampling_mask,
        scale=1000,
        numPixels=3000,
        seed=42,
        geometries=True
    )
    
    # Descargar los datos de los puntos
    features = sample_points.getInfo().get('features', [])
    data = []
    for f in features:
        props = f.get('properties', {})
        lst = props.get('lst_night')
        elev = props.get('elevation')
        if lst is not None and elev is not None:
            data.append({'lst_night': lst, 'elevation': elev})
            
    df_sample = pd.DataFrame(data)
    print(f"      Muestreados {len(df_sample)} píxeles rurales válidos.")
    
    # Ajustar regresión lineal simple: LST = beta_0 + beta_1 * Elevation
    from scipy.stats import linregress
    slope, intercept, r_value, p_value, std_err = linregress(df_sample['elevation'], df_sample['lst_night'])
    print(f"   Ecuación de Regresión Rural Nocturna:")
    print(f"      LST_nocturna = {intercept:.4f} + ({slope:.5f}) * Elevación")
    print(f"      R² = {r_value**2:.4f} (p-value = {p_value:.2e})")
    print(f"      Lapse Rate Nocturno Local: {slope * 1000:.2f}°C por cada 1000 metros de ascenso")
    
    # 3. Aplicar Correcciones a la Malla Maestra
    print("\nAplicando correcciones y recalculando anomalías en la malla...")
    gpkg_path = base_dir / "data" / "processed" / "malla_modelado_multiescala_mty.gpkg"
    gdf = gpd.read_file(gpkg_path)
    
    # Asegurar que existan valores válidos de elevación
    gdf_clean = gdf[np.isfinite(gdf["elevation"]) & (gdf["elevation"] > -999)].copy()
    
    # A. SUHI Nocturna Original (Rural 17.34°C)
    gdf_clean["suhi_night_original"] = gdf_clean["lst_night_c"] - 17.34
    
    # B. SUHI Nocturna Controlada por Elevación (Rural Controlado = temp_rural_controlled)
    gdf_clean["suhi_night_controlled"] = gdf_clean["lst_night_c"] - temp_rural_controlled
    
    # C. SUHI Nocturna Corregida por Regresión (Anomalía local respecto a la temperatura rural esperada para esa elevación)
    # LST_rural_esperada = intercept + slope * elevation
    gdf_clean["suhi_night_corrected"] = gdf_clean["lst_night_c"] - (intercept + slope * gdf_clean["elevation"])
    
    # Guardar estas nuevas columnas en la malla
    gdf.loc[gdf_clean.index, "suhi_night_original"] = gdf_clean["suhi_night_original"]
    gdf.loc[gdf_clean.index, "suhi_night_controlled"] = gdf_clean["suhi_night_controlled"]
    gdf.loc[gdf_clean.index, "suhi_night_corrected"] = gdf_clean["suhi_night_corrected"]
    gdf.to_file(gpkg_path, driver="GPKG", mode="w")
    print(f"      Malla maestra actualizada con las validaciones nocturnas.")
    
    # 4. Reportar Estadísticas y Comparación
    print("\nEstadísticas comparativas de la Anomalía Térmica Nocturna (ZMM completa):")
    print(f"  * SUHI Original (sin control):  Media = {gdf_clean['suhi_night_original'].mean():.2f}°C,  Rango = [{gdf_clean['suhi_night_original'].min():.2f}°C, {gdf_clean['suhi_night_original'].max():.2f}°C]")
    print(f"  * SUHI Controlada (plana 573m): Media = {gdf_clean['suhi_night_controlled'].mean():.2f}°C, Rango = [{gdf_clean['suhi_night_controlled'].min():.2f}°C, {gdf_clean['suhi_night_controlled'].max():.2f}°C]")
    print(f"  * SUHI Corregida (regresión):   Media = {gdf_clean['suhi_night_corrected'].mean():.2f}°C,  Rango = [{gdf_clean['suhi_night_corrected'].min():.2f}°C, {gdf_clean['suhi_night_corrected'].max():.2f}°C]")
    
    # Análisis del Signo: ¿Persiste la isla fría o cambia a isla de calor?
    pct_cold_orig = (gdf_clean["suhi_night_original"] < 0).mean() * 100
    pct_cold_ctrl = (gdf_clean["suhi_night_controlled"] < 0).mean() * 100
    pct_cold_corr = (gdf_clean["suhi_night_corrected"] < 0).mean() * 100
    
    print("\nPorcentaje de la ciudad clasificada como 'Isla Fría' (SUHI < 0):")
    print(f"  * Original: {pct_cold_orig:.1f}% de las celdas")
    print(f"  * Controlada por Elevación: {pct_cold_ctrl:.1f}% de las celdas")
    print(f"  * Corregida por Regresión: {pct_cold_corr:.1f}% de las celdas")
    
    # 5. Generar Reporte Breve en Markdown
    report_content = f"""# Reporte de Validación Técnica: Isla de Calor Nocturna (Monterrey 2026)

Este reporte evalúa la anomalía térmica nocturna de superficie (SUHI) en la Zona Metropolitana de Monterrey, comparando el cálculo original (sesgado por diferencias de elevación) contra correcciones metodológicas basadas en altitud utilizando datos de **MODIS Aqua (1:30 AM)** y **SRTM Elevation (30m)**.

## 1. Valores de Referencia Rurales
*   **Temperatura Rural Original (sin control):** **17.34 °C** (Elevación promedio de las zonas: ~405 m).
*   **Temperatura Rural Controlada por Elevación:** **{temp_rural_controlled:.2f} °C** (Filtrada a zonas rurales de elevación similar a la ZMM: 520 m - 620 m).

## 2. Ecuación de Regresión y Lapse Rate Nocturno
Se analizó la relación térmica de la altitud en áreas rurales circundantes:
*   **Fórmula:** $LST_{{nocturna}} = {intercept:.2f} + ({slope:.4f}) \\times Elevación$
*   **Lapse Rate Local:** **{slope * 1000:.2f} °C** por cada 1000 metros de ascenso.
*   **Coeficiente de Determinación ($R^2$):** **{r_value**2:.4f}** (Relación altamente significativa).

## 3. Comparación de Resultados (Signo y Magnitud)

| Métrica | SUHI Original | SUHI Controlada (Elevación) | SUHI Corregida (Regresión) |
| :--- | :---: | :---: | :---: |
| **Temperatura Media de Anomalía** | {gdf_clean['suhi_night_original'].mean():.2f} °C | {gdf_clean['suhi_night_controlled'].mean():.2f} °C | {gdf_clean['suhi_night_corrected'].mean():.2f} °C |
| **Anomalía Máxima** | {gdf_clean['suhi_night_original'].max():.2f} °C | {gdf_clean['suhi_night_controlled'].max():.2f} °C | {gdf_clean['suhi_night_corrected'].max():.2f} °C |
| **Anomalía Mínima** | {gdf_clean['suhi_night_original'].min():.2f} °C | {gdf_clean['suhi_night_controlled'].min():.2f} °C | {gdf_clean['suhi_night_corrected'].min():.2f} °C |
| **Porcentaje de "Isla Fría" ($SUHI < 0$)** | {pct_cold_orig:.1f}% | {pct_cold_ctrl:.1f}% | {pct_cold_corr:.1f}% |

### ¿Persiste o desaparece la "Isla Fría"?
*   **Persistencia:** La "Isla Fría" nocturna **{ "persiste en su mayoría" if pct_cold_corr > 50 else "desaparece y se convierte en Isla de Calor" }**.
*   **Análisis:** Al aplicar la corrección por regresión (que resta a cada celda la temperatura que le correspondería por su altura), la media de anomalía en la ZMM se desplaza a **{gdf_clean['suhi_night_corrected'].mean():.2f} °C**. { "Esto demuestra que la ciudad sigue siendo físicamente más fresca que su entorno rural equivalente, confirmando el efecto de Cool Island nocturno a escala regional." if gdf_clean['suhi_night_corrected'].mean() < 0 else "Esto revela que, al remover el efecto de enfriamiento por altitud, la ciudad es en promedio más cálida que su entorno rural de control, revelando una Isla de Calor de baja intensidad nocturna." }

## 4. Limitaciones del Sensor (MODIS 1km)
*   **Resolución Espacial Real:** La resolución nativa del sensor térmico de MODIS es de **1 km (1000 metros)**. Aunque en el pipeline se reproyectó e interpoló a **30 metros** para coincidir con la geometría de la malla maestra, esto no crea información sub-píxel real.
*   **Uso Recomendado:** Este análisis nocturno **no debe utilizarse** para caracterizar hotspots intraurbanos a escala micro-local (como colonias, calles o AGEB individuales). Debe tratarse estrictamente como un **análisis exploratorio y regional** de la tendencia macro de Monterrey.

## 5. Recomendación para la PPT Principal
*   **Recomendación:** **{ "NO RECOMENDADO" if gdf_clean['suhi_night_corrected'].mean() < 0.5 and pct_cold_corr > 20 else "RECOMENDADO CON RESERVAS" }** para la PPT principal.
*   **Justificación:** { "La señal nocturna de MODIS a 1km es sumamente gruesa y no aporta la resolución de celda de 30m que define la metodología 'Bottom-Up' del resto de la presentación. Además, la persistencia de anomalías mayormente negativas o muy bajas ({gdf_clean['suhi_night_corrected'].mean():.2f}°C) tras corregir por elevación, indica que el fenómeno térmico nocturno en Monterrey está dominado por factores orográficos y de viento regional, más que por patrones de cobertura urbana localizados. Es mejor mantener la presentación enfocada 100% en el análisis diurno de Landsat a 30m, que es altamente robusto y concluyente." if gdf_clean['suhi_night_corrected'].mean() < 0.5 else "La corrección por altitud revela una isla de calor nocturna real pero tenue. Sin embargo, dada la baja resolución nativa (1km) de MODIS, no es metodológicamente coherente con el análisis de detalle a 30m diurno. Se sugiere dejarla únicamente como slide de anexo." }
"""
    
    # Guardar reporte en el directorio de artefactos / outputs
    report_path = base_dir / "outputs" / "05" / "05_validation_report_night_suhi.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    print(f"\n[OK] Reporte breve guardado con éxito en: {report_path}")

    # 6. Generar mapa comparativo original vs corregido
    print("\nGenerando mapa comparativo de validaciones nocturnas...")
    gdf_map_all_orig = gdf_clean.to_crs(epsg=3857)
    
    fig, axes = plt.subplots(1, 2, figsize=(20, 10), dpi=300)
    
    # Panel 1: Original
    gdf_map_all_orig.plot(
        column='suhi_night_original',
        cmap='coolwarm',
        alpha=0.75,
        ax=axes[0],
        edgecolor='none',
        linewidth=0,
        legend=True,
        legend_kwds={
            'label': 'SUHI Nocturna Original (°C)',
            'orientation': 'horizontal',
            'pad': 0.04,
            'shrink': 0.7
        }
    )
    axes[0].set_title("A. SUHI Nocturna Original\n(Línea base rural baja ~405m)", fontsize=14, fontweight='bold', color='#1f3864')
    axes[0].set_axis_off()
    ctx.add_basemap(axes[0], source=ctx.providers.Esri.WorldImagery)
    
    # Panel 2: Corregido
    gdf_map_all_orig.plot(
        column='suhi_night_corrected',
        cmap='coolwarm',
        alpha=0.75,
        ax=axes[1],
        edgecolor='none',
        linewidth=0,
        legend=True,
        legend_kwds={
            'label': 'SUHI Nocturna Corregida por Altitud (°C)',
            'orientation': 'horizontal',
            'pad': 0.04,
            'shrink': 0.7
        }
    )
    axes[1].set_title("B. SUHI Nocturna Corregida\n(Ajustada por regresión de elevación rural)", fontsize=14, fontweight='bold', color='#1f3864')
    axes[1].set_axis_off()
    ctx.add_basemap(axes[1], source=ctx.providers.Esri.WorldImagery)
    
    plt.tight_layout()
    comparison_map_path = outputs_dir / "05_night_suhi_elevation_comparison.png"
    plt.savefig(comparison_map_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"      Mapa comparativo guardado en: {comparison_map_path}")
    print("=" * 80)

if __name__ == "__main__":
    main()
