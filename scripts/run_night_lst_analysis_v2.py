import os
import pathlib
import sys
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
import matplotlib.pyplot as plt
import contextily as ctx
from shapely.geometry import box
import ee
import geemap

# Add base directory to path
base_dir = pathlib.Path(__file__).resolve().parent.parent
sys.path.append(str(base_dir))

from src.gee_data import init_ee, get_aoi_geometry
from src.config import START_DATE_NIGHT, END_DATE_NIGHT, INTERIM_DIR, PROCESSED_DIR

def main():
    print("=" * 80)
    print("INICIANDO PROCESAMIENTO NOCTURNO MODIS SIN SUAVIZADO ARTIFICIAL")
    print("=" * 80)
    
    # 1. Inicializar GEE
    init_ee()
    aoi = get_aoi_geometry()
    
    # Rango de fechas para primavera 2026 (config)
    col_night = ee.ImageCollection("MODIS/061/MYD11A1") \
                  .filterBounds(aoi) \
                  .filterDate(START_DATE_NIGHT, END_DATE_NIGHT)
                  
    count = col_night.size().getInfo()
    print(f"      Escenas MODIS Aqua encontradas: {count}")
    if count == 0:
        raise ValueError("No se encontraron escenas MODIS Aqua en el periodo nocturno.")
        
    # Obtener proyección nativa
    native_proj = col_night.first().select("LST_Night_1km").projection()
    
    # Calcular mediana temporal
    lst_night_median = col_night.select("LST_Night_1km").median()
    
    # Calibrar a Celsius (NO SE USA .resample("bilinear"))
    # Esto asegura que la exportación posterior use nearest neighbor y no suavice
    lst_night_raw = lst_night_median.setDefaultProjection(native_proj) \
                                   .multiply(0.02) \
                                   .subtract(273.15) \
                                   .rename("LST_C")
    
    # Descargar raster 1: 30m Nearest Neighbor (Alineado)
    night_tif_30m_path = INTERIM_DIR / "lst_night_2026_nearest_30m.tif"
    print(f"[1/5] Descargando LST nocturno 30m Nearest Neighbor a: {night_tif_30m_path}...")
    geemap.download_ee_image(
        image=lst_night_raw,
        filename=str(night_tif_30m_path),
        region=aoi,
        scale=30,
        crs="EPSG:4326"
    )
    
    # Descargar raster 2: 1km Native
    night_tif_1km_path = INTERIM_DIR / "lst_night_2026_native_1km.tif"
    print(f"[2/5] Descargando LST nocturno 1km Nativo a: {night_tif_1km_path}...")
    geemap.download_ee_image(
        image=lst_night_raw,
        filename=str(night_tif_1km_path),
        region=aoi,
        scale=1000,
        crs="EPSG:4326"
    )
    
    # 2. Calcular la Temperatura Rural Nocturna de Referencia (en resolución nativa 1km)
    print("[3/5] Calculando temperatura rural nocturna de control...")
    rural_zones = {
        "Este (Pesquería/Cadereyta)": [-100.10, 25.60, -99.90, 25.80],
        "Norte (Salinas Victoria)": [-100.30, 25.95, -100.10, 26.15],
        "Sur (Santiago/Allende)": [-100.15, 25.30, -99.95, 25.50]
    }
    
    zone_temps = []
    for name, coords in rural_zones.items():
        geom = ee.Geometry.Rectangle(coords)
        col_rural = ee.ImageCollection("MODIS/061/MYD11A1") \
                      .filterBounds(geom) \
                      .filterDate(START_DATE_NIGHT, END_DATE_NIGHT)
        median_modis = col_rural.select("LST_Night_1km").median().multiply(0.02).subtract(273.15)
        rural_median_info = median_modis.reduceRegion(
            reducer=ee.Reducer.median(),
            geometry=geom,
            scale=1000,
            maxPixels=1e9
        ).getInfo()
        temp = rural_median_info.get("LST_Night_1km")
        if temp is not None:
            print(f"      Zona rural nocturna - {name}: {temp:.2f}°C")
            zone_temps.append(temp)
            
    avg_rural_night = sum(zone_temps) / len(zone_temps) if zone_temps else 17.34
    print(f"      Temperatura rural de referencia promedio: {avg_rural_night:.2f}°C")
    
    # 3. Muestrear datos a la Malla Maestra de 30m (Nearest Neighbor)
    print("[4/5] Muestreando LST nocturno y actualizando la malla de 30m...")
    gpkg_path = base_dir / "data" / "processed" / "malla_modelado_multiescala_mty.gpkg"
    if not gpkg_path.exists():
        raise FileNotFoundError(f"No se encontró el geopackage en {gpkg_path}")
        
    gdf_30m = gpd.read_file(gpkg_path)
    centroids = gdf_30m.to_crs(epsg=32614).geometry.centroid.to_crs(epsg=4326)
    coords = [(geom.x, geom.y) for geom in centroids]
    
    with rasterio.open(night_tif_30m_path) as src_lst:
        lst_nodata = src_lst.nodata
        lst_night_values = []
        for val in src_lst.sample(coords):
            v = val[0]
            if v == lst_nodata or np.isnan(v):
                lst_night_values.append(np.nan)
            else:
                lst_night_values.append(float(v))
                
    gdf_30m["lst_night_c"] = lst_night_values
    # SUHI = LST_urbana - LST_rural
    gdf_30m["suhi_night_c"] = gdf_30m["lst_night_c"] - avg_rural_night
    
    # Guardar malla de 30m actualizada
    gdf_30m.to_file(gpkg_path, driver="GPKG", mode="w")
    print(f"      Malla de 30m guardada con éxito en: {gpkg_path}")
    
    # 4. Construir malla vectorial nativa de 1km para graficar la resolución nativa
    print("      Construyendo malla vectorial nativa de 1km desde el raster...")
    with rasterio.open(night_tif_1km_path) as src:
        data = src.read(1)
        nodata = src.nodata
        polygons = []
        lst_vals = []
        for r in range(src.height):
            for c in range(src.width):
                val = data[r, c]
                if val != nodata and not np.isnan(val):
                    x, y = src.xy(r, c)
                    dx = src.transform[0]
                    dy = src.transform[4]
                    w_half = abs(dx) / 2.0
                    h_half = abs(dy) / 2.0
                    rect = box(x - w_half, y - h_half, x + w_half, y + h_half)
                    polygons.append(rect)
                    lst_vals.append(float(val))
                    
        gdf_1km = gpd.GeoDataFrame({'lst_night_c': lst_vals}, geometry=polygons, crs=src.crs)
        # SUHI = LST_urbana - LST_rural
        gdf_1km["suhi_night_c"] = gdf_1km["lst_night_c"] - avg_rural_night
        
    outputs_dir = base_dir / "outputs" / "05"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    
    # 5. Generación de las Figuras
    print("[5/5] Generando figuras de la SUHI nocturna...")
    
    # Coordenadas geográficas límites en Web Mercator (EPSG:3857) para centrar en Monterrey/San Nicolás
    xlim_3857 = (-11175785.45, -11157512.80)
    ylim_3857 = (2953993.73, 2967054.28)
    
    # =========================================================================
    # VERSIÓN A: RESOLUCIÓN NATIVA 1 KM
    # =========================================================================
    print("      [A.1] Graficando SUHI Nocturna General ZMM (Resolución Nativa 1km)...")
    gdf_1km_3857 = gdf_1km.to_crs(epsg=3857)
    
    fig, ax = plt.subplots(figsize=(12, 12), dpi=300)
    gdf_1km_3857.plot(
        column='suhi_night_c',
        cmap='magma',
        alpha=0.70,
        ax=ax,
        edgecolor='#333333', # Bordes finos oscuros para enfatizar píxeles nativos de 1km
        linewidth=0.5,
        vmin=0,
        legend=True,
        legend_kwds={
            'label': 'Intensidad SUHI Nocturna (°C)',
            'orientation': 'vertical',
            'pad': 0.02,
            'shrink': 0.6,
            'aspect': 30
        }
    )
    cax = fig.axes[-1]
    cax.tick_params(labelsize=14)
    cax.yaxis.label.set_size(16)
    ax.set_xlim(xlim_3857)
    ax.set_ylim(ylim_3857)
    ctx.add_basemap(ax, source=ctx.providers.Esri.WorldImagery)
    ax.set_title("Intensidad SUHI Nocturna en la ZMM (Nativa MODIS 1 km)", fontsize=20, fontweight='bold', pad=15, color='#263238')
    ax.set_axis_off()
    
    fig_general_1km = outputs_dir / "real_night_suhi_zmm_1km_native.png"
    plt.savefig(fig_general_1km, dpi=300, bbox_inches='tight')
    plt.close()
    
    # Hotspots Native 1km (Percentil 95)
    print("      [A.2] Graficando Hotspots SUHI Nocturna P95 (Resolución Nativa 1km)...")
    p95_1km = gdf_1km['suhi_night_c'].quantile(0.95)
    gdf_1km_h95 = gdf_1km_3857[gdf_1km_3857['suhi_night_c'] >= p95_1km].copy()
    
    fig, ax = plt.subplots(figsize=(12, 12), dpi=300)
    # Dibujar contorno de fondo transparente de la malla urbana 1km para contexto
    gdf_1km_3857.plot(ax=ax, color='none', edgecolor='#ffffff', linewidth=0.2, alpha=0.3)
    gdf_1km_h95.plot(
        column='suhi_night_c',
        cmap='magma',
        alpha=0.85,
        ax=ax,
        edgecolor='black',
        linewidth=0.8,
        vmin=0,
        legend=True,
        legend_kwds={
            'label': 'Intensidad SUHI Nocturna (°C)',
            'orientation': 'vertical',
            'pad': 0.02,
            'shrink': 0.6,
            'aspect': 30
        }
    )
    cax = fig.axes[-1]
    cax.tick_params(labelsize=14)
    cax.yaxis.label.set_size(16)
    ax.set_xlim(xlim_3857)
    ax.set_ylim(ylim_3857)
    ctx.add_basemap(ax, source=ctx.providers.Esri.WorldImagery)
    ax.set_title(f"Hotspots Térmicos Nocturnos P95 (Nativa MODIS 1 km)\n(Umbral P95: {p95_1km:.2f}°C)", fontsize=18, fontweight='bold', pad=15, color='#263238')
    ax.set_axis_off()
    
    fig_hotspots_1km = outputs_dir / "real_night_hotspots_1km_native.png"
    plt.savefig(fig_hotspots_1km, dpi=300, bbox_inches='tight')
    plt.close()

    # =========================================================================
    # VERSIÓN B: RESOLUCIÓN 30 M ALINEADA (SIN SUAVIZADO / NEAREST NEIGHBOR)
    # =========================================================================
    print("      [B.1] Graficando SUHI Nocturna General ZMM (Alineada 30m Nearest)...")
    gdf_30m_clean = gdf_30m.dropna(subset=["lst_night_c", "suhi_night_c"]).copy()
    gdf_30m_3857 = gdf_30m_clean.to_crs(epsg=3857)
    
    fig, ax = plt.subplots(figsize=(12, 12), dpi=300)
    gdf_30m_3857.plot(
        column='suhi_night_c',
        cmap='magma',
        alpha=0.70,
        ax=ax,
        edgecolor='none',
        linewidth=0,
        vmin=0,
        legend=True,
        legend_kwds={
            'label': 'Intensidad SUHI Nocturna (°C)',
            'orientation': 'vertical',
            'pad': 0.02,
            'shrink': 0.6,
            'aspect': 30
        }
    )
    cax = fig.axes[-1]
    cax.tick_params(labelsize=14)
    cax.yaxis.label.set_size(16)
    ax.set_xlim(xlim_3857)
    ax.set_ylim(ylim_3857)
    ctx.add_basemap(ax, source=ctx.providers.Esri.WorldImagery)
    ax.set_title("Intensidad SUHI Nocturna en la ZMM (Alineada 30 m, sin suavizado)", fontsize=19, fontweight='bold', pad=15, color='#263238')
    ax.set_axis_off()
    
    fig_general_30m = outputs_dir / "real_night_suhi_zmm_30m_nearest.png"
    plt.savefig(fig_general_30m, dpi=300, bbox_inches='tight')
    plt.close()
    
    # Hotspots 30m Nearest (Percentil 95)
    print("      [B.2] Graficando Hotspots SUHI Nocturna P95 (Alineada 30m Nearest)...")
    p95_30m = gdf_30m_clean['suhi_night_c'].quantile(0.95)
    gdf_30m_h95 = gdf_30m_3857[gdf_30m_3857['suhi_night_c'] >= p95_30m].copy()
    
    fig, ax = plt.subplots(figsize=(12, 12), dpi=300)
    gdf_30m_h95.plot(
        column='suhi_night_c',
        cmap='magma',
        alpha=0.85,
        ax=ax,
        edgecolor='none',
        linewidth=0,
        vmin=0,
        legend=True,
        legend_kwds={
            'label': 'Intensidad SUHI Nocturna (°C)',
            'orientation': 'vertical',
            'pad': 0.02,
            'shrink': 0.6,
            'aspect': 30
        }
    )
    cax = fig.axes[-1]
    cax.tick_params(labelsize=14)
    cax.yaxis.label.set_size(16)
    ax.set_xlim(xlim_3857)
    ax.set_ylim(ylim_3857)
    ctx.add_basemap(ax, source=ctx.providers.Esri.WorldImagery)
    ax.set_title(f"Hotspots Térmicos Nocturnos P95 (Alineada 30 m, sin suavizado)\n(Umbral P95: {p95_30m:.2f}°C)", fontsize=18, fontweight='bold', pad=15, color='#263238')
    ax.set_axis_off()
    
    fig_hotspots_30m = outputs_dir / "real_night_hotspots_30m_nearest.png"
    plt.savefig(fig_hotspots_30m, dpi=300, bbox_inches='tight')
    plt.close()
    
    # =========================================================================
    # COPIAR FIGURAS AL DIRECTORIO DE CONVERSACIÓN PARA REVISIÓN
    # =========================================================================
    import shutil
    conv_dir = base_dir
    
    # Copy all 4 to conversation base directory as artifacts
    # Wait, we should copy them under the conversation artifacts folder or base_dir
    # Let's copy them to base_dir or artifact folder.
    # The artifact folder is: C:\Users\Eydan\.gemini\antigravity-cli\brain\348ea4a3-d4fa-49d5-a8b1-60c486e95898\
    artifact_dest = pathlib.Path("C:/Users/Eydan/.gemini/antigravity-cli/brain/348ea4a3-d4fa-49d5-a8b1-60c486e95898")
    artifact_dest.mkdir(parents=True, exist_ok=True)
    
    shutil.copy(fig_general_1km, artifact_dest / "real_night_suhi_zmm_1km_native.png")
    shutil.copy(fig_hotspots_1km, artifact_dest / "real_night_hotspots_1km_native.png")
    shutil.copy(fig_general_30m, artifact_dest / "real_night_suhi_zmm_30m_nearest.png")
    shutil.copy(fig_hotspots_30m, artifact_dest / "real_night_hotspots_30m_nearest.png")
    
    print("\n[OK] ¡Las 4 figuras nocturnas han sido generadas y copiadas exitosamente!")
    print("=" * 80)

if __name__ == "__main__":
    main()
