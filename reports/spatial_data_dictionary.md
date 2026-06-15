# Diccionario de Variables Geoespaciales y Metadatos Técnicos (UHI Monterrey 2026)

Este documento es el diccionario de datos oficial y la referencia metodológica del pipeline de análisis de la Isla de Calor Urbana Superficial (SUHI) en la Zona Metropolitana de Monterrey para el año **2026**. Contiene la documentación técnica exhaustiva de todas las variables almacenadas en la malla de modelado multiescala (`data/processed/malla_modelado_multiescala_mty.gpkg`) y el Geopackage de vecindarios (`data/processed/ageb_correlaciones_sensibilidad.gpkg`).

---

## 1. Marco de Referencia Geoespacial
Para asegurar la consistencia geométrica en las intersecciones y cálculos métricos de distancias y buffers, todo el proyecto utiliza el siguiente marco estándar:
*   **Proyección de Trabajo (Métrica):** WGS 84 / UTM Zona 14N (EPSG:32614). Utilizada para calcular distancias euclidianas y filtros de buffers en metros.
*   **Proyección de Almacenamiento (Geográfica):** WGS 84 (EPSG:4326). Utilizada para el almacenamiento final y exportación para visualización en QGIS/ArcGIS o navegadores.
*   **Resolución Espacial Base (Línea de Celda):** Malla regular de $30\text{ m} \times 30\text{ m}$ ($900\text{ m}^2$ por celda).

---

## 2. Diccionario de la Malla de Modelado (Escala Celda 30m)
Capa vectorial: `data/processed/malla_modelado_multiescala_mty.gpkg`

### 2.1. Identificadores y Atributos Geográficos Base

| Columna | Tipo | Origen | Descripción Técnica y Fórmula |
| :--- | :---: | :---: | :--- |
| **`cell_id`** | Entero (`int`) | Interno (`grid.py`) | Identificador único incremental asignado a cada celda de la cuadrícula. |
| **`geometry`** | Polígono | Interno (`grid.py`) | Límites espaciales vectoriales de la celda de $30\text{ m}$ ($900\text{ m}^2$). |
| **`elevation`** | Flotante | SRTM (GEE) | Elevación media de la celda sobre el nivel del mar en metros (m). |
| **`NOM_MUN`** | Cadena | INEGI / Join | Nombre del municipio al que pertenece el centroide de la celda. |
| **`CVEGEO`** | Cadena | INEGI / Join | Clave geoestadística única de 13 dígitos de la AGEB en la que reside el centroide de la celda. |
| **`zona_densidad`** | Cadena | Clasificación | Clasificación construida de la celda: **Baja** (< 20%), **Media** (20-60%) o **Alta** (>= 60%), basada en la fracción impermeable (`dw_built_pct`). |

### 2.2. Bloque Asociación Biofísica de Enfriamiento (Vegetación y Buffers)

| Columna | Tipo | Origen | Descripción Técnica y Fórmula |
| :--- | :---: | :---: | :--- |
| **`green_pct`** | Flotante | Sentinel-2 (MSI) | Porcentaje de superficie de la celda con vegetación activa. Calculado como la fracción de subpíxeles de 10m con NDVI > 0.3 remuestreados a la celda de 30m. |
| **`green_pct_100m`** | Flotante | Filtro Focal | Densidad vegetal promedio en una ventana móvil circular de **$100\text{ m}$** de radio alrededor de la celda. |
| **`green_pct_250m`** | Flotante | Filtro Focal | Densidad vegetal promedio en una ventana móvil circular de **$250\text{ m}$** de radio. |
| **`green_pct_500m`** | Flotante | Filtro Focal | Densidad vegetal promedio en una ventana móvil circular de **$500\text{ m}$** de radio (escala vecindario). |
| **`green_pct_1000m`**| Flotante | Filtro Focal | Densidad vegetal promedio en una ventana móvil circular de **$1000\text{ m}$** (1 km) de radio. |
| **`green_pct_3000m`**| Flotante | Filtro Focal | Densidad vegetal promedio en una ventana móvil circular de **$3000\text{ m}$** (3 km) de radio (escala regional). |

### 2.3. Bloque Asociación Térmica de Calentamiento (Industria y Buffers)

| Columna | Tipo | Origen | Descripción Técnica y Fórmula |
| :--- | :---: | :---: | :--- |
| **`industrial_osm_pct`** | Flotante | OpenStreetMap | Porcentaje de área de la celda ocupado por polígonos de zonificación industrial o naves industriales mapeados en OSM. |
| **`industrial_density_100m`**| Flotante | Filtro Focal | Densidad industrial promedio en una ventana circular de **$100\text{ m}$** de radio. |
| **`industrial_density_250m`**| Flotante | Filtro Focal | Densidad industrial promedio en una ventana circular de **$250\text{ m}$** de radio. |
| **`industrial_density_500m`**| Flotante | Filtro Focal | Densidad industrial promedio en una ventana circular de **$500\text{ m}$** de radio (escala vecindario). |
| **`industrial_density_1000m`**| Flotante | Filtro Focal | Densidad industrial promedio en una ventana circular de **$1000\text{ m}$** (1 km) de radio. |
| **`industrial_density_3000m`**| Flotante | Filtro Focal | Densidad industrial promedio en una ventana circular de **$3000\text{ m}$** (3 km) de radio. |

### 2.4. Variables Térmicas y de Distancia Euclidiana

| Columna | Tipo | Origen | Descripción Técnica y Fórmula |
| :--- | :---: | :---: | :--- |
| **`lst_day_c`** / **`lst_c`** | Flotante | Landsat 8 (TIRS) | Temperatura de Superficie Terrestre (LST) diurna promedio de primavera en grados Celsius (°C), calibrada a partir de la Banda 10 mediante algoritmo de emisividad. |
| **`suhi_day_c`** / **`suhi_c`** | Flotante | Calculado | **SUHI Diurna (°C)**. Intensidad de la Isla de Calor: $\text{SUHI}_i = \text{LST}_i - \text{LST}_{\text{rural}}$, donde $\text{LST}_{\text{rural}}$ es el promedio térmico medido en 3 zonas rurales boscosas de control de la periferia. |
| **`distance_to_industry_osm_m`**| Flotante | OSM / Calc | Distancia euclidiana mínima en metros (m) desde el centroide de la celda a la huella industrial más cercana de OSM. |
| **`distance_to_ternium_m`** | Flotante | Point / Calc | Distancia euclidiana en metros a la coordenada de la planta Ternium Guerrero (`Point(-100.299792, 25.720855)`). |
| **`distance_to_water_m`** | Flotante | OSM / Calc | Distancia euclidiana mínima en metros a cuerpos de agua mapeados en OSM. |

### 2.5. Fracciones de Cobertura Dynamic World (Sentinel-2, 10m)

| Columna | Tipo | Origen | Descripción Técnica y Fórmula |
| :--- | :---: | :---: | :--- |
| **`dw_built_pct`** | Flotante | Dynamic World | Porcentaje de la superficie de la celda clasificado como "Edificado / Superficie Impermeable". |
| **`dw_trees_pct`** | Flotante | Dynamic World | Porcentaje de la superficie de la celda clasificado como "Dosel de Árboles / Cobertura Forestal". |
| **`dw_bare_pct`** | Flotante | Dynamic World | Porcentaje de la superficie de la celda clasificado como "Suelo Desnudo / Rocoso / Expuesto". |
| **`dw_water_pct`** | Flotante | Dynamic World | Porcentaje de la superficie de la celda clasificado como "Agua Superficial". |
| **`dw_grass_pct`** | Flotante | Dynamic World | Porcentaje de la superficie de la celda clasificado como "Pastizales / Vegetación Herbácea". |

---

## 3. Diccionario del GeoPackage de Vecindarios (Escala AGEB)
Capa vectorial: `data/processed/ageb_correlaciones_sensibilidad.gpkg`

### 3.1. Atributos Censales y Poblacionales (INEGI 2020)

| Columna | Tipo | Origen | Descripción Técnica y Fórmula |
| :--- | :---: | :---: | :--- |
| **`CVEGEO`** | Cadena | INEGI | Clave única geoestadística de la AGEB urbana (13 dígitos). |
| **`NOM_MUN`** | Cadena | INEGI | Nombre del municipio al que pertenece el polígono de la AGEB. |
| **`area_km2`** | Flotante | Calculado | Área total de la AGEB calculada en kilómetros cuadrados ($\text{km}^2$). |
| **`POBTOT`** | Entero | Censo 2020 | Población residente total censada en la AGEB. |
| **`POB0_14`** | Entero | Censo 2020 | Población infantil de 0 a 14 años de edad en la AGEB. |
| **`POB65_MAS`** | Entero | Censo 2020 | Población adulta vulnerable de 65 años o más en la AGEB. |
| **`P_60YMAS`** | Entero | Censo 2020 | Población adulta de 60 años o más en la AGEB. |
| **`pop_density_ageb`** | Flotante | INEGI / Calc | Densidad de población: `POBTOT / area_km2` (Habitantes/$\text{km}^2$). |
| **`pct_0_14`** | Flotante | INEGI / Calc | Porcentaje de población infantil: `(POB0_14 / POBTOT) * 100`. |
| **`pct_65_mas`** | Flotante | INEGI / Calc | Porcentaje de población vulnerable de la tercera edad: `(POB65_MAS / POBTOT) * 100`. |
| **`pct_60ymas`** | Flotante | INEGI / Calc | Porcentaje de población mayor de 60 años: `(P_60YMAS / POBTOT) * 100`. |

### 3.2. Variables de Sensibilidad Espacial (Coeficientes de Spearman a escala AGEB)
*Estas variables representan los coeficientes de Spearman ($r$) calculados pixel a pixel sobre las celdas internas de cada AGEB de forma individual.*

| Columna | Tipo | Descripción Técnica |
| :--- | :---: | :--- |
| **`r_green_global`** | Flotante | Correlación local global entre la vegetación local (`green_pct`) y la anomalía SUHI. |
| **`r_green500_global`**| Flotante | Correlación a escala de vecindario entre el buffer de vegetación (`green_pct_500m`) y la anomalía SUHI. |
| **`r_ind_global`** | Flotante | Correlación local global entre la presencia industrial local (`industrial_osm_pct`) y la anomalía SUHI. |
| **`r_ind500_global`** | Flotante | Correlación a escala de vecindario entre la densidad industrial (`industrial_density_500m`) y la anomalía SUHI. |
| **`r_green_baja`** | Flotante | Correlación local de vegetación (`green_pct`) filtrando celdas de densidad construida **Baja**. |
| **`r_green_media`** | Flotante | Correlación local de vegetación (`green_pct`) filtrando celdas de densidad construida **Media**. |
| **`r_green_alta`** | Flotante | Correlación local de vegetación (`green_pct`) filtrando celdas de densidad construida **Alta**. |

---

## 4. Notas Metodológicas y Algoritmos de Cálculo

### 4.1. Algoritmo de Cálculo de Buffers (Filtro Focal)
Las variables multiescala (ej. `green_pct_500m`) no son promedios simples de vecindario administrativo. Se calculan aplicando una **convolución focal circular** sobre el ráster original del predictor en formato TIF antes de su extracción a la malla vectorial:
$$D_{focal}(x, y) = \frac{1}{\pi R^2} \iint_{d \le R} I(x + u, y + v) \,du\,dv$$
Donde $I(x,y)$ es el valor de la celda en la malla fina y $R$ es el radio en metros del buffer ($100\text{ m}$, $250\text{ m}$, $500\text{ m}$, $1000\text{ m}$). Esto modela físicamente el efecto de dispersión y transporte de masas térmicas de áreas de cobertura continuas.

### 4.2. Limitaciones e Incertidumbre de las Fuentes de Datos
1.  **LST Landsat 8 TIRS (B10):** Aunque se remuestrea a 30m por el USGS, su resolución de captura óptica real es de **$100\text{ m}$**. Esto implica que anomalías térmicas muy localizadas (como micro-islas de calor asociadas a naves industriales específicas o intersecciones viales) aparecen suavizadas espacialmente por el efecto del píxel térmico original.
2.  **OSM Industrial (Zonificación):** La base de polígonos de OSM depende de la digitalización colaborativa. Muestra alta completitud en zonas consolidadas de Monterrey y San Nicolás, pero puede presentar cierto desfase de actualización o subrepresentación de parques industriales recientes en la periferia de la ZMM.
3.  **Desfase Censal (INEGI 2020):** Los datos sociodemográficos corresponden al año 2020. Al cruzarse con datos biofísicos térmicos de **2026**, existe un desfase temporal de 6 años que podría subestimar la densidad y exposición de la población en AGEBs periféricas de reciente y acelerada expansión urbana.
