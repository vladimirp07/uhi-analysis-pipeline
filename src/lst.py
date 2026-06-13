"""
uhi-mty-mvp: Procesamiento Térmico Multitemporal
================================================
Descarga y procesa imágenes Landsat 8 para capturas diurnas y nocturnas (2026).
"""

import ee
import geemap
import rioxarray
from src.gee_data import init_ee, get_aoi_geometry
from src.config import INTERIM_DIR, START_DATE_DAY, END_DATE_DAY, START_DATE_NIGHT, END_DATE_NIGHT, YEAR

def mask_l8_clouds(image):
    """
    Aplica máscara de nubes y sombras de nubes a una imagen Landsat 8 Level 2.
    """
    qa = image.select("QA_PIXEL")
    cloud_shadow_mask = qa.bitwiseAnd(1 << 4).eq(0)
    cloud_mask = qa.bitwiseAnd(1 << 3).eq(0)
    mask = cloud_shadow_mask.And(cloud_mask)
    return image.updateMask(mask)

def download_mty_lst_multitemporal():
    """
    Descarga y procesa las capas de Temperatura Superficial Terrestre (LST)
    multitemporales (Día y Noche) para Monterrey usando Landsat 8 Level 2 de GEE.
    Calcula además una línea base rural automática fuera de la mancha urbana.
    
    Returns:
        tuple: Rutas de los archivos GeoTIFF creados (day_path, night_path).
    """
    print("\n[LST] Iniciando descarga de LST multitemporal (Día y Noche)...")
    init_ee()
    aoi = get_aoi_geometry()
    
    # 1. Calcular temperatura rural de referencia en GEE (Promedio de 3 zonas alrededor de la ZMM)
    try:
        print("[LST] Calculando temperatura rural de referencia multizona en GEE (3 zonas)...")
        rural_zones = {
            "Este (Pesquería/Cadereyta)": [-100.10, 25.60, -99.90, 25.80],
            "Norte (Salinas Victoria)": [-100.30, 25.95, -100.10, 26.15],
            "Sur (Santiago/Allende)": [-100.15, 25.30, -99.95, 25.50]
        }
        
        zone_temps = []
        for name, coords in rural_zones.items():
            geom = ee.Geometry.Rectangle(coords)
            col_rural = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2") \
                          .filterBounds(geom) \
                          .filterDate(START_DATE_DAY, END_DATE_DAY) \
                          .filter(ee.Filter.gt("SUN_ELEVATION", 0)) \
                          .map(mask_l8_clouds)
            
            median_l8 = col_rural.median()
            ndvi_l8 = median_l8.normalizedDifference(["SR_B5", "SR_B4"])
            lst_l8 = median_l8.select("ST_B10").multiply(0.00341802).add(149.0).subtract(273.15)
            
            # Filtro de vegetación densa (NDVI > 0.4) para evitar áreas secas o desérticas extremas
            rural_lst = lst_l8.updateMask(ndvi_l8.gt(0.4))
            
            rural_median_info = rural_lst.reduceRegion(
                reducer=ee.Reducer.median(),
                geometry=geom,
                scale=30,
                maxPixels=1e9
            ).getInfo()
            
            temp = rural_median_info.get("ST_B10")
            if temp is not None:
                print(f"[LST] Referencia Rural - {name}: {temp:.2f}°C")
                zone_temps.append(temp)
            else:
                print(f"[LST] Advertencia: No se pudo obtener la temperatura rural para {name}")
                
        if zone_temps:
            avg_rural_temp = sum(zone_temps) / len(zone_temps)
            rural_temp_path = INTERIM_DIR / "rural_temp_day.txt"
            with open(rural_temp_path, "w") as f:
                f.write(f"{avg_rural_temp:.4f}")
            print(f"[LST] Temperatura de referencia rural promedio guardada en cache: {avg_rural_temp:.2f}°C (Basada en {len(zone_temps)} zonas)")
        else:
            print("[LST] Advertencia: No se pudieron obtener temperaturas rurales para ninguna de las zonas de GEE.")
    except Exception as e:
        print(f"[LST] Advertencia: Error al calcular la temperatura rural multizona en GEE: {e}")
    
    # 2. CAPTURA DIURNA (DAY)
    day_output = INTERIM_DIR / f"lst_day_{YEAR}.tif"
    if day_output.exists():
        print(f"[LST] El raster diurno ya existe localmente: {day_output}")
    else:
        print(f"[LST] Consultando Landsat 8 diurno en GEE ({START_DATE_DAY} a {END_DATE_DAY})...")
        col_day = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2") \
                    .filterBounds(aoi) \
                    .filterDate(START_DATE_DAY, END_DATE_DAY) \
                    .filter(ee.Filter.gt("SUN_ELEVATION", 0)) \
                    .map(mask_l8_clouds)
                    
        count_day = col_day.size().getInfo()
        print(f"[LST] Escenas diurnas encontradas: {count_day}")
        if count_day == 0:
            raise ValueError(f"No se encontraron escenas diurnas en Landsat 8 para {START_DATE_DAY} - {END_DATE_DAY}")
            
        # Reducción por mediana y calibración a Celsius
        img_day = col_day.select("ST_B10").median()
        lst_day = img_day.multiply(0.00341802).add(149.0).subtract(273.15).rename("LST_C")
        
        print(f"[LST] Descargando LST diurno a 30m en: {day_output}...")
        geemap.download_ee_image(
            image=lst_day,
            filename=str(day_output),
            region=aoi,
            scale=30,
            crs="EPSG:4326"
        )
        
        if day_output.exists():
            with rioxarray.open_rasterio(day_output) as src:
                print(f"[LST] GeoTIFF diurno validado. Dimensiones: {src.rio.width}x{src.rio.height}")
                
    # 2. CAPTURA NOCTURNA (NIGHT)
    night_output = INTERIM_DIR / f"lst_night_{YEAR}.tif"
    print("[LST] Análisis nocturno desactivado. Omitiendo descarga de LST nocturno.")
    if night_output.exists():
        try:
            night_output.unlink()
        except Exception:
            pass
            
    return str(day_output), ""

def download_mty_lst(year=2026):
    """
    Wrapper legacy para compatibilidad con la firma de llamada anterior.
    """
    print("[LST] [Legacy Wrapper] download_mty_lst() redirigiendo a download_mty_lst_multitemporal()...")
    download_mty_lst_multitemporal()
