# Islas de Calor en la Zona Metropolitana de Monterrey

Este repositorio alberga el pipeline de análisis geoespacial, biofísico y socioambiental de la **Isla de Calor Urbana Superficial (SUHI - Surface Urban Heat Island)** en la Zona Metropolitana de Monterrey (ZMM) para el año **2026**.

El pipeline está diseñado de manera paramétrica y modular, funcionando como un **validador analítico clave para la misión de un nanosatélite de monitoreo térmico**. Permite verificar y calibrar en tierra los patrones espaciales de anomalías térmicas (SUHI) y su relación con coberturas de suelo y proximidad industrial.

---

## Documentación Central del Proyecto (`docs/`)

La documentación detallada del proyecto se encuentra centralizada y estructurada de la siguiente manera:

### 1. Documentación Pública y Reproducible (`docs/public/`)
*   **[README Técnico](./docs/public/README.md):** Introducción general, objetivos y mapa de navegación de la documentación.
*   **[METHODOLOGY.md](./docs/public/METHODOLOGY.md):** Flujo de procesamiento paso a paso, desde la ingesta de GEE hasta la delimitación y priorización de hotspots.
*   **[DATA_SOURCES.md](./docs/public/DATA_SOURCES.md):** Catálogo de sensores satelitales, resoluciones espaciales, variables derivadas y limitaciones físicas.
*   **[RESULTS_SUMMARY.md](./docs/public/RESULTS_SUMMARY.md):** Resultados diurnos y nocturnos corregidos, hotspots priorizados y segmentación por densidad construida.
*   **[REPRODUCIBILITY.md](./docs/public/REPRODUCIBILITY.md):** Guía de instalación, configuración del entorno, orden de ejecución y outputs esperados.
*   **[FIGURES_INDEX.md](./docs/public/FIGURES_INDEX.md):** Catálogo e índice de figuras analíticas generadas para presentaciones y reportes.

### 2. Documentación Operativa y de Control Local (`docs/private/` - Excluida de Git)
*   **[PROJECT_STATUS.md](./docs/private/PROJECT_STATUS.md):** Estado de avance de componentes, inconsistencias resueltas y pendientes críticas de validación.
*   **[NEXT_STEPS.md](./docs/private/NEXT_STEPS.md):** Planificación de la siguiente fase (modelación 3D SVF, albedos, calor antropogénico, autorregresivos).
*   **[TECHNICAL_NOTES.md](./docs/private/TECHNICAL_NOTES.md):** Notas detalladas sobre bugs resueltos (proyección sinusoidal de MODIS nocturno en GEE) y estabilidad de semillas GWR.
*   **[RESULTS_INTERPRETATION_NOTES.md](./docs/private/RESULTS_INTERPRETATION_NOTES.md):** Discusión de patrones territoriales (spillover intermunicipal, saturación de concreto e injusticia ambiental).
*   **[TODO_RESTART_CHECKLIST.md](./docs/private/TODO_RESTART_CHECKLIST.md):** Lista de verificación para reactivar el entorno y volver a correr el pipeline rápidamente.
*   **[CLOSING_REPORT.md](./docs/private/CLOSING_REPORT.md):** Resumen final de cierre y entrega de la primera versión del pipeline.

---


## 1. Estructura del Proyecto

El repositorio está organizado bajo una estructura modular estándar para proyectos de ciencia de datos geoespaciales:

```text
UHI_Analysis_pipeline_MVP_v1/
├── data/                             # Datos geográficos (raw, interim, processed) - en gitignore
├── notebooks/                        # Jupyter Notebooks principales para ejecución interactiva
│   ├── exploratorios/                # Notebooks de desarrollo y exploración no validados (GWR)
│   ├── 01_uhi_spatial_correlation_regional.ipynb
│   └── 02_uhi_hotspot_case_studies.ipynb
├── scripts/                          # Scripts ejecutables autónomos de análisis avanzado
│   ├── exploratorios/                # Desarrollos exploratorios y auditorías locales no validadas (GWR)
│   │   ├── run_gwr_sensitivity_audit.py
│   │   └── validate_gwr.py
│   ├── __init__.py
│   ├── run_bottom_up_regional_analysis.py # Análisis multiescala por densidad, buffers y municipios
│   ├── run_density_zones_analysis.py # Análisis segmentado por densidad de impermeabilidad
│   ├── run_diagnostics.py            # Diagnóstico de calidad de datos y emparejamiento censal
│   ├── run_hotspots_analysis.py      # Detección de hotspots térmicos críticos (DBSCAN)
│   └── run_scale_correlation_analysis.py # Análisis multiescala del efecto de escala (MAUP)
├── reports/                          # NUEVO: Reportes y entregables técnicos generados
│   └── bottom_up_analysis_report.md  # Reporte de análisis regional bottom-up y recomendaciones
├── outputs/                          # Figuras, mapas interactivos (Folium) y tablas CSV generadas
├── src/                              # Backend del pipeline (módulos reutilizables)
│   ├── config.py                     # Parámetros, bbox y constantes de rutas
│   ├── gee_data.py                   # Conexión e inicialización de Google Earth Engine API
│   ├── grid.py                       # Generación de la malla regular de 30 metros
│   ├── lst.py                        # Descarga y calibración de temperatura (Landsat 8)
│   ├── ndvi.py                       # Extracción de reflectancias Sentinel-2 e índice NDVI
│   ├── dynamic_world.py              # Extracción de coberturas terrestres (Dynamic World, GEE)
│   ├── industry.py                   # Descarga y cálculo de densidad industrial (OSM)
│   ├── water.py                      # Descarga y cálculo de distancias a cuerpos de agua (OSM)
│   ├── ageb_social.py                # Integración del Censo INEGI 2020 a nivel AGEB
│   ├── uhi_metrics.py                # Cálculo de SUHI con áreas de control rural
│   ├── plots.py                      # Suite de graficación espacial y visualización
│   └── stats.py                      # Funciones de cálculo de matrices de Spearman
├── main.py                           # Orquestador del pipeline base de preparación de datos
└── requirements.txt                  # Dependencias del entorno de ejecución Python
```

---

## 2. Diferencia entre Componentes

*   **`main.py` (Orquestador Base):** Es el punto de entrada oficial para la **extracción, procesamiento y preparación de los datos**. Se encarga de descargar insumos satelitales vía GEE, generar la cuadrícula espacial de 30m, calcular la anomalía térmica de la SUHI restando el promedio de control rural, integrar el Censo INEGI 2020 a nivel de AGEB y consolidar las bases de datos maestras (`data/processed/malla_modelado_multiescala_mty.gpkg` y `data/processed/ageb_maestra_mty_2026.gpkg`).
*   **`src/` (Módulos Reutilizables):** Contiene la lógica interna y las funciones empaquetadas (módulos de Python). No contiene scripts de ejecución directa; proporciona las herramientas de backend que importan tanto `main.py` como los scripts en `scripts/`.
*   **`scripts/` (Análisis Avanzado):** Alberga los scripts ejecutables independientes de análisis de datos. Consumen las bases de datos preparadas por `main.py` y ejecutan tareas analíticas específicas como detección de clusters espaciales (DBSCAN), correlaciones multiescala por amortiguamiento (buffers) y generación de reportes específicos en la carpeta `reports/`.

---

## 3. Flujo de Procesamiento (De Inicio a Fin)

El pipeline de preparación de datos orquestado por `main.py` ejecuta secuencialmente las siguientes fases:

1.  **Conexión GEE (Paso 1):** Conexión con Google Earth Engine para autenticación y consulta remota.
2.  **Construcción de Malla (Paso 2):** Generación de la cuadrícula base regular de 30 metros proyectada en UTM Zona 14N (EPSG:32614) que define las unidades de observación del modelo.
3.  **Descarga Satelital (Paso 3 y 4):** Descarga del compuesto de mediana de primavera de Temperatura Superficial Terrestre (LST) de Landsat 8 y del NDVI máximo de Sentinel-2. Se calcula el porcentaje de cobertura verde (`green_pct`) mediante remuestreo de celdas de 10m a 30m.
4.  **Clasificación de Suelo (Paso 5 y 6):** Descarga de coberturas de suelo de Dynamic World (Built, Trees, Bare, Water, Grass) y descarga de polígonos industriales y cuerpos de agua de OpenStreetMap (OSM) para calcular la densidad de ocupación industrial local.
5.  **Calibración SUHI (Paso 7):** Cálculo de la anomalía de la SUHI diurna (`suhi_day_c`) restando a la LST urbana la mediana de 3 zonas rurales externas en la Zona Metropolitana de Monterrey.
6.  **Medición Euclidiana (Paso 8):** Cálculo de distancias mínimas en metros a zonas industriales generales, cuerpos de agua y a la planta de Ternium Guerrero.
7.  **Integración Demográfica (Paso 9):** Spatial join de centroides de la malla de 30m a polígonos de AGEB. Agrega datos absolutos del Censo INEGI 2020 y calcula tasas e indicadores demográficos normalizados (densidad poblacional, porcentaje de adultos mayores y niños).
8.  **Visualizaciones (Paso 10):** Generación automática de matrices de Spearman globales (a escala celda y AGEB), histogramas del EDA y paneles de auditoría espacial.

---

## 4. Análisis Especializados (scripts/)

Una vez que `main.py` genera las bases consolidadas, se pueden correr los análisis independientes en la carpeta `scripts/`:

*   **Análisis Regional Bottom-Up (`run_bottom_up_regional_analysis.py`):** Realiza un análisis multiescala de correlaciones de Spearman segmentado por el tipo de densidad construida (Baja, Media, Alta) y 5 escalas de buffers (30m, 100m, 250m, 500m, 1000m) para cada uno de los 4 municipios (Monterrey, San Pedro, Guadalupe, San Nicolás) y a nivel individual de 383 AGEBs. Genera un reporte técnico de política pública en `reports/bottom_up_analysis_report.md`.
*   **Análisis por Zonas de Densidad (`run_density_zones_analysis.py`):** Segmenta el comportamiento de las correlaciones a escala ZMM para aislar los efectos de la vegetación en periferias y de la industria en zonas de densidad construida intermedia.
*   **Detección de Hotspots Térmicos (`run_hotspots_analysis.py`):** Utiliza el algoritmo de agrupamiento espacial DBSCAN para aislar núcleos de calor críticos (hotspots) dentro de la trama urbana y priorizarlos mediante un Puntaje de Criticidad Física.
*   **Análisis de Efecto de Escala (`run_scale_correlation_analysis.py`):** Evalúa el Problema de la Unidad de Área Modificable (MAUP) mediante análisis de correlación Spearman multiescala.

---

## 5. Notebooks del Proyecto

*   **`01_uhi_spatial_correlation_regional.ipynb`:** Orquestación interactiva del análisis de correlación. Muestra el scatterplot de línea base (cobertura verde vs SUHI), las matrices globales de Spearman y llama dinámicamente al motor de análisis bottom-up municipal.
*   **`02_uhi_hotspot_case_studies.ipynb`:** Análisis interactivo y mapas de Folium para los casos de estudio de islas de calor urbanas del algoritmo DBSCAN.
*   **`exploratorios/`:** Carpeta que contiene notebooks de desarrollo e investigación histórica (diagnósticos, optimización y machine learning espacial) actualmente en proceso de actualización.

---

## 6. Diccionario de Variables Clave

| Variable | Escala | Tipo | Origen | Descripción Técnica |
| :--- | :---: | :---: | :---: | :--- |
| **`lst_day_c`** | 30m / AGEB | Físico | Landsat 8 (B10) | Temperatura Superficial Terrestre diurna calibrada en grados Celsius (°C). |
| **`green_pct`** | 30m / AGEB | Físico | Sentinel-2 | Porcentaje de vegetación verde activa de la celda (NDVI > 0.3). |
| **`industrial_osm_pct`**| 30m / AGEB | Físico | OSM / GEE | Porcentaje de cobertura de uso de suelo industrial en la celda. |
| **`suhi_day_c`** | 30m / AGEB | Físico | Calculado | **SUHI Diurna (°C)**. LST de la celda menos promedio rural de control local. |
| **`dw_built_pct`** | 30m / AGEB | Físico | Dynamic World | Porcentaje de cobertura de superficie impermeable / edificada. |
| **`dw_trees_pct`** | 30m / AGEB | Físico | Dynamic World | Porcentaje de cobertura de dosel forestal / árboles. |
| **`POB65_MAS`** | AGEB | Social | INEGI 2020 | Población de adultos mayores vulnerables de 65 años o más. |
| **`pop_density_ageb`** | AGEB | Social | INEGI / Calc | Densidad de población de la AGEB (habitantes por km²). |
