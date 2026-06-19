# Guía de Reproducibilidad del Pipeline SUHI Monterrey

Este documento describe las dependencias, configuraciones de entorno y el flujo secuencial recomendado para ejecutar el pipeline de análisis de la Isla de Calor Urbana Superficial (SUHI) diurna y nocturna en la Zona Metropolitana de Monterrey y reproducir la totalidad de las bases de datos, análisis y figuras del proyecto.

---

## 1. Requerimientos de Software y Dependencias

El pipeline requiere un entorno de ejecución de Python 3.9 o superior. Las dependencias del proyecto se encuentran descritas en el archivo [requirements.txt](../../requirements.txt). 

Las bibliotecas geoespaciales principales incluyen:
*   `geopandas` y `shapely` para el procesamiento vectorial de celdas, buffers y uniones espaciales.
*   `earthengine-api` para la descarga y reducción de imágenes multiespectrales y térmicas de Google Earth Engine.
*   `scikit-learn` para el agrupamiento espacial con DBSCAN.
*   `numpy` y `pandas` para la manipulación matricial y tabular.
*   `matplotlib` y `seaborn` para la visualización y exportación de gráficos.

Para instalar las dependencias, ejecute el siguiente comando en la terminal:
```bash
pip install -r requirements.txt
```

---

## 2. Autenticación de Google Earth Engine (GEE)

Debido a que el pipeline realiza descargas directas de datos satelitales (Landsat 8/9, Sentinel-2 y Dynamic World) mediante la API de Earth Engine, es obligatorio contar con una cuenta de desarrollador registrada de GEE. 

Antes de ejecutar el script orquestador, inicialice y autentique su entorno local con:
```bash
earthengine authenticate
```
Siga las instrucciones en pantalla en el navegador para autorizar sus credenciales de Google.

---

## 3. Secuencia de Ejecución Recomendada

Para reproducir los datos y resultados principales desde cero, siga estrictamente el siguiente orden de ejecución:

```text
Fase 1: Preparación (main.py)
   │
   ▼
Fase 2: Enriquecimiento (run_density_zones_analysis.py)
   │
   ├─► Fase 3A: Clusters Térmicos (run_hotspots_analysis.py)
   ├─► Fase 3B: Relación Multiescala (run_bottom_up_regional_analysis.py)
   │
   ▼
Fase 4: Análisis Nocturno (run_night_lst_analysis_v2.py)
```

### Paso 1: Orquestación y Preparación de Datos Base
Ejecute el script orquestador principal para conectarse a GEE, generar la cuadrícula de 30m, descargar LST, NDVI, coberturas y polígonos de OSM, calibrar la SUHI diurna e integrar el Censo INEGI 2020:
```bash
python main.py
```
*   **Salidas esperadas:** 
    *   `data/processed/malla_modelado_multiescala_mty.gpkg` (181,746 celdas).
    *   `data/processed/ageb_maestra_mty_2026.gpkg` (AGEBs con datos demográficos).

### Paso 2: Enriquecimiento de Variables e Índices Derivados
Ejecute el script de análisis por zonas de densidad para calcular los nuevos índices normalizados y variables derivadas complejas (IPU, IVT, acceso verde per cápita):
```bash
python scripts/run_density_zones_analysis.py
```
*   **Salidas esperadas:**
    *   `data/processed/malla_modelado_multiescala_mty_enriquecida.gpkg` (Malla enriquecida).
    *   `outputs/tables/correlaciones_por_zona_nuevas_variables.csv` (Coeficientes de Spearman segmentados).

### Paso 3: Agrupamiento Espacial (Hotspots)
Ejecute el script de DBSCAN para delimitar núcleos críticos de calor diurnos y realizar el diagnóstico de Ternium Guerrero:
```bash
python scripts/run_hotspots_analysis.py
```
*   **Salidas esperadas:**
    *   `outputs/05/04_all_hotspot_clusters.gpkg` (Capa vectorial de clusters).
    *   `outputs/05/04_top3_hotspots.gpkg` (Capa vectorial de hotspots priorizados).
    *   `outputs/05/04_hotspot_priority_table.csv` (Tabla de prioridades).

### Paso 4: Análisis Bottom-Up Multiescala
Ejecute el script de correlación bottom-up por municipios, AGEBs y buffers radiales:
```bash
python scripts/run_bottom_up_regional_analysis.py
```
*   **Salidas esperadas:**
    *   `data/processed/ageb_correlaciones_sensibilidad.gpkg` (AGEBs unidas a coeficientes de Spearman).
    *   `reports/bottom_up_analysis_report.md` (Reporte técnico consolidado).

### Paso 5: Análisis Térmico Nocturno (MODIS)
Ejecute la validación de MODIS LST nocturna y la generación de la SUHI a 30m NN:
```bash
python scripts/run_night_lst_analysis_v2.py
```
*   **Salidas esperadas:**
    *   `outputs/05/real_night_suhi_zmm_30m_nearest.png` (Mapa de anomalía nocturna).

---
