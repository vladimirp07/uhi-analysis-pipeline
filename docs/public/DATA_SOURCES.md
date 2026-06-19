# Catálogo de Fuentes de Datos y Diccionario de Variables

Este documento describe de manera rigurosa las fuentes de datos primarias, sensores satelitales, variables derivadas e indicadores socioeconómicos integrados en el pipeline de análisis de la Isla de Calor Urbana Superficial (SUHI) diurna y nocturna de la Zona Metropolitana de Monterrey.

---

## 1. Fuentes de Datos Primarias y Sensores

### A. Landsat 8 y Landsat 9 TIRS (Thermal Infrared Sensor) - USGS / NASA
*   **Variable Objetivo:** Temperatura Superficial Terrestre (LST) diurna (°C).
*   **Resolución Espacial:** Nativa de **100 m**, remuestreada a **30 m** por el USGS mediante interpolación cúbica para alineación con las bandas ópticas.
*   **Temporalidad:** Compuestos mensuales y estacionales para el periodo histórico de **enero de 2025 a junio de 2026** (utilizados en la serie temporal) y medianas de primavera de 2026.
*   **Uso:** Extracción de evolución de LST y análisis de consistencia espacio-temporal.
*   **Limitación Técnica:** El tamaño nativo del píxel térmico (100m) provoca un efecto de suavizado espacial, lo que impide caracterizar anomalías de calor hiper-locales (como la inercia térmica de naves industriales individuales o encajonamientos viales de menos de 100m de ancho).

### B. Sentinel-2 MSI (Multispectral Instrument) - ESA
*   **Variable Derivada:** Índice de Vegetación de Diferencia Normalizada (NDVI) y porcentaje de vegetación verde activa (`green_pct`).
*   **Resolución Espacial:** **10 m** (bandas roja y NIR utilizadas para el cálculo del NDVI).
*   **Temporalidad:** Compuesto de mediana de reflectancias de primavera de 2026.
*   **Algoritmo:** La vegetación activa se define mediante el umbral de $\text{NDVI} > 0.3$. La variable `green_pct` representa la fracción de subpíxeles de 10m con vegetación que se traslapan dentro de cada celda base de 30m.

### C. MODIS Aqua (MYD11A1 / MYD11A2 LST/Emissivity) - NASA
*   **Variable Objetivo:** Temperatura Superficial Terrestre (LST) nocturna (°C).
*   **Resolución Espacial:** Nativa de **1 km**, muestreada a **30 m** (Nearest Neighbor) para la integración local en la malla.
*   **Temporalidad:** Compuestos de primavera de 2026, capturados en el paso descendente del satélite Aqua (aproximadamente a las 1:30 AM hora local).
*   **Uso:** Análisis y modelación de la Isla de Calor Superficial Nocturna (SUHI).
*   **Limitación Técnica:** La resolución espacial gruesa de 1 km nativo es ideal para caracterizar anomalías macro-climáticas a escala regional, pero impide realizar análisis microclimáticos detallados calle por calle.

### D. Dynamic World - Google / WRI
*   **Variables Derivadas:** Coberturas del suelo bidimensionales: fracción impermeable (`dw_built_pct`), dosel arbóreo (`dw_trees_pct`), pastos (`dw_grass_pct`), suelo desnudo (`dw_bare_pct`) y agua (`dw_water_pct`).
*   **Resolución Espacial:** **10 m** (remuestreado a la malla de 30m mediante promedios de píxeles).
*   **Metodología:** Producto derivado de clasificaciones continuas basadas en redes neuronales aplicadas a imágenes Sentinel-2.

### E. OpenStreetMap (OSM)
*   **Variables Derivadas:** Polígonos industriales (`industrial_osm_pct`), distancia a zonas industriales y distancia a cuerpos de agua permanentes.
*   **Tipo de Dato:** Vectorial descargado vía API Overpass.
*   **Limitación Técnica:** Depende de la digitalización colaborativa de los usuarios. Muestra excelente completitud en los municipios centrales (Monterrey, San Nicolás), pero puede presentar subrepresentación o retrasos en la delimitación de parques industriales recientes en la periferia metropolitana.

### F. Censo de Población y Vivienda 2020 - INEGI
*   **Variables Derivadas:** Densidad de población, población vulnerable (niños y adultos mayores de 65 años) y rezago de activos en el hogar (viviendas sin bienes).
*   **Escala de Agregación:** Polígonos oficiales de Área Geoestadística Básica (AGEB) urbana.
*   **Limitación Técnica:** Desfase temporal de 6 años respecto a los datos satelitales térmicos de **2026**, lo que podría subestimar la densidad demográfica y la vulnerabilidad en las periferias de expansión acelerada de la ZMM.

### G. SRTM (Shuttle Radar Topography Mission) - NASA
*   **Variables Derivadas:** Elevación media sobre el nivel del mar en metros (m) y pendiente del terreno.
*   **Resolución Espacial:** **30 m** (1 arc-second).

---

## 2. Diccionario de Variables en la Malla de Modelado (30m)
El archivo consolidado principal se almacena en `data/processed/malla_modelado_multiescala_mty.gpkg`. Sus variables clave son:

| Variable | Tipo | Unidad | Sensor/Origen | Descripción Técnica |
| :--- | :---: | :---: | :---: | :--- |
| **`cell_id`** | Entero | ID | Interno | Identificador secuencial único de la celda de 30m. |
| **`lst_day_c`** | Real | °C | Landsat 8/9 | Temperatura de superficie diurna calibrada en primavera. |
| **`lst_night_c`** | Real | °C | MODIS | Temperatura de superficie nocturna (1:30 AM) calibrada. |
| **`suhi_day_c`** | Real | °C | Calculado | Anomalía térmica diurna: $\text{LST}_{\text{celda}} - \text{LST}_{\text{rural\_diurna}}$. |
| **`suhi_night_c`** | Real | °C | Calculado | Anomalía térmica nocturna: $\text{LST}_{\text{celda}} - \text{LST}_{\text{rural\_nocturna}}$. |
| **`green_pct`** | Real | % | Sentinel-2 | Porcentaje de vegetación verde activa dentro de la celda. |
| **`dw_built_pct`** | Real | % | Dynamic World | Fracción de la celda cubierta por superficie impermeable. |
| **`dw_trees_pct`** | Real | % | Dynamic World | Fracción de la celda cubierta por dosel forestal/árboles. |
| **`industrial_osm_pct`** | Real | % | OSM | Porcentaje de la celda ocupado por polígonos industriales. |
| **`distance_to_industry_osm_m`** | Real | metros | OSM | Distancia euclidiana mínima a la zona industrial más cercana. |
| **`distance_to_ternium_m`** | Real | metros | Coordenada | Distancia euclidiana a la planta Ternium Guerrero. |
| **`elevation`** | Real | metros | SRTM | Altura sobre el nivel del mar de la celda. |
| **`green_pct_500m`** | Real | % | Filtro Focal | Densidad vegetal promedio en un radio circular de 500m. |
| **`industrial_density_500m`** | Real | % | Filtro Focal | Densidad industrial promedio en un radio circular de 500m. |
| **`indice_vulnerabilidad_termica`** | Real | Índice (0-1)| Calculado | Índice multivariado normalizado (calor + población - verde). |
