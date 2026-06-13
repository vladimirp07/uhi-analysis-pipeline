# MVP: Pipeline de Análisis Multitemporal de Islas de Calor Urbanas Superficiales (SUHI) en Monterrey (2026)

## 1. Introducción y Contexto

Este repositorio alberga el **Producto Mínimo Viable (MVP) v1** del pipeline de análisis geoespacial y biofísico de la **Isla de Calor Urbana Superficial (SUHI - Surface Urban Heat Island)** en la Zona Metropolitana de Monterrey para el año **2026**. 

### El Fenómeno SUHI como Eje Central
A diferencia de los estudios simplificados de temperatura absoluta, este proyecto se enfoca en la **SUHI (Intensidad de la Isla de Calor)**, la cual se define como la **anomalía térmica espacial** generada por la urbanización. La temperatura de la superficie terrestre (LST) es únicamente la medición física de entrada; el fenómeno geográfico real de interés es la SUHI, calculada al restar a cada celda urbana una línea base de referencia rural (compuesta por áreas con alta densidad vegetal y mínima alteración antropogénica).

### Soporte a Misiones Satelitales    
El diseño paramétrico y modular de este pipeline sirve como **validador analítico y conceptual clave para la misión científica de un nanosatélite de monitoreo térmico**. Permite verificar y calibrar en tierra los patrones espaciales de anomalías térmicas (SUHI) y su relación con coberturas de suelo y proximidad industrial, sentando las bases metodológicas para los algoritmos de detección que procesarán las imágenes capturadas por el sensor térmico del nanosatélite.

---

## 2. Arquitectura de Archivos y Flujo Operativo

### Árbol de Directorios Real del Repositorio

El repositorio está organizado bajo una estructura modular de ciencia de datos geoespaciales:

```text
UHI_Analysis_pipeline_MVP_v1/
├── data/
│   ├── interim/                    # Datos geográficos temporales y rásters intermedios
│   │   ├── cuerpos_agua_2026.gpkg  # Capa de polígonos disueltos de cuerpos de agua
│   │   ├── dw_mty_2026.tif         # Ráster multibanda (built, trees, bare, water, grass) de Dynamic World (10m)
│   │   ├── green_mask_mty_2026.tif # Máscara binaria de vegetación activa (Sentinel-2, 10m)
│   │   ├── green_pct_30m.tif       # Ráster de porcentaje de cobertura verde remuestreado a 30m
│   │   ├── lst_day_2026.tif        # Ráster LST diurno calibrado (Landsat 8, 30m)
│   │   ├── malla_features_2026.gpkg # Malla base enriquecida con LST, NDVI y fracción verde
│   │   ├── malla_industria_2026.gpkg # Malla enriquecida con porcentaje de área industrial
│   │   ├── malla_monterrey_30m.gpkg # Cuadrícula espacial base (30m, UTM EPSG:32614 -> WGS84 EPSG:4326)
│   │   └── ndvi_mty_2026.tif       # Ráster del índice NDVI de Sentinel-2 (10m)
│   ├── processed/                  # Datasets maestros geoespaciales consolidados
│   │   ├── ageb_maestra_mty_2026.gpkg # Capa de polígonos AGEB con variables socio-demográficas y medias físicas
│   │   ├── malla_maestra_mty_2026.gpkg # Malla maestra v1 (LST, cobertura verde e intensidad SUHI)
│   │   ├── malla_maestra_mty_2026_v2.gpkg # Malla maestra v2 (v1 + Dynamic World + distancias euclidianas)
│   │   └── malla_maestra_mty_2026_v3.gpkg # Malla maestra v3 (Copia de compatibilidad física para graficación)
│   └── raw/                        # Insumos espaciales y censales crudos
│       ├── AGEB_ZMM_Dani.json      # Límites geográficos oficiales de AGEB de la ZMM
│       ├── RESAGEBURB2020 - 19 Nuevo León (1).csv # Censo de Población y Vivienda 2020 a nivel de manzana/AGEB
│       └── fd_agebmza_urbana_cpv2020.csv # Descriptor de variables censales
├── notebooks/
│   └── 00_uhi_mvp_orchestrator.ipynb # Jupyter Notebook para ejecución del pipeline interactivo y análisis visual
├── outputs/
│   ├── figures/                    # Entregables visuales y paneles de auditoría espacial
│   │   ├── 01_mapa_satelital_limpio.png
│   │   ├── 02_eda_distribuciones.png
│   │   ├── 03_panel_auditoria_espacial.png
│   │   ├── 04_matriz_correlacion_physical_30m.png
│   │   ├── 05_matriz_correlacion_social_ageb.png
│   │   └── mapa_base_estudio.png
│   ├── maps/                       # Mapas interactivos auto-contenidos (Folium/Kepler)
│   └── tables/                     # Tablas y matrices de resultados en formato plano
│       └── 05_correlaciones_maestras.csv # Coeficientes de correlación Spearman multiescala
├── src/                            # Módulos Python del backend del pipeline
│   ├── config.py                   # Configuración global, límites del AOI y rutas del proyecto
│   ├── gee_data.py                 # Conexión, autenticación e inicialización de Google Earth Engine API
│   ├── grid.py                     # Generación y delimitación geométrica de la malla de 30m en el AOI
│   ├── lst.py                      # Descarga y calibración a Celsius de LST (Landsat 8)
│   ├── ndvi.py                     # Descarga de Sentinel-2, cálculo de NDVI y máscara binaria (>0.3)
│   ├── dynamic_world.py            # Consulta a Dynamic World y cálculo de fracciones de cobertura
│   ├── industry.py                 # Obtención de industria (OSM) y cálculo de porcentajes y distancias
│   ├── water.py                    # Obtención de cuerpos de agua (OSM) y cálculo de distancias
│   ├── ageb_social.py              # Extracción del Censo INEGI 2020, normalización y agregación zonal
│   ├── uhi_metrics.py              # Cálculo de la intensidad de anomalía térmica SUHI con control rural
│   ├── plots.py                    # Funciones para la suite visual de auditoría geoespacial
│   └── stats.py                    # Cálculo de correlaciones Spearman físicas y socioambientales
├── main.py                         # Orquestador del pipeline completo de producción
├── requirements.txt                # Dependencias librerías Python del entorno
└── test_features_suhi.py           # Script autónomo para pruebas de integración del pipeline
```

### Flujo Operativo y Lógica de Procesamiento

El pipeline se ejecuta secuencialmente a través de `main.py` de la siguiente forma:

1. **Paso 1: Inicialización de Google Earth Engine (GEE)**: Conecta con GEE usando credenciales locales para la obtención remota de datos.
2. **Paso 2: Construcción de la Malla Base de 30m**: Genera una cuadrícula regular de 30 metros de resolución espacial proyectada en UTM Zona 14N (EPSG:32614) que abarca el área de estudio en Monterrey (según los límites definidos en `AOI_BBOX` en `config.py`), y la guarda en WGS84 (EPSG:4326).
3. **Paso 3: Obtención de LST y NDVI**: Descarga desde GEE los compuestos medianos de primavera de Temperatura Superficial Terrestre (LST) de Landsat 8 y NDVI de Sentinel-2 a resoluciones de 30m y 10m respectivamente.
4. **Paso 4: Mapeo Satelital en Malla**: Calcula localmente el porcentaje de cobertura verde (`green_pct`) mediante el remuestreo de la máscara de vegetación de Sentinel-2 (>0.3) de 10m a 30m, y muestrea la LST y la cobertura verde sobre los centroides de cada celda de la cuadrícula.
5. **Paso 5: Fracciones de Dynamic World**: Descarga probabilidades anuales promediadas de clases de cobertura terrestre de Dynamic World (Sentinel-2, 10m) y las mapea a la malla (Built, Trees, Bare, Water, Grass).
6. **Paso 6: Capas OSM e Industria**: Descarga polígonos industriales de OpenStreetMap, resuelve superposiciones y calcula la fracción de área industrial en cada celda (`industrial_osm_pct`).
7. **Paso 7: Calibración e Intensidad de SUHI**: Calcula la Anomalía Térmica SUHI Diurna (`suhi_day_c`) restando a la LST de cada celda la temperatura promedio de 3 zonas de referencia rural fuera de la mancha urbana de la ZMM (Norte: Salinas Victoria, Este: Pesquería/Cadereyta, Sur: Santiago/Allende) calculada en GEE. **Éste es el indicador central del análisis.**
8. **Paso 8: Consolidación Master v2 (Distancias y DW)**: Calcula las distancias euclidianas exactas desde cada centroide de celda a zonas industriales generales, a cuerpos de agua y a la coordenada de la planta Ternium Guerrero, uniendo todos los datos biofísicos y espaciales.
9. **Paso 9: Consolidación Master v3 y Agregación Zonal AGEB**: Carga los polígonos de AGEB urbanas de la ZMM y los datos del Censo de Población INEGI 2020. Mapea los centroides de las celdas a cada polígono de AGEB y calcula estadísticas zonales (promedios físicos de SUHI e isla de calor) que une con variables sociales normalizadas (densidad, grupos de edad, etnicidad).
10. **Paso 10: Visualizaciones y Auditoría de Correlaciones**: Genera mapas base satelitales y de contexto, curvas de distribución y matrices de correlación no paramétrica de Spearman a ambas escalas operativa y zonal, guardando tablas de coeficientes y mapas en `outputs/`.

---

## 3. Diccionario de Variables Geoespaciales (Estado Actual)

La siguiente tabla documenta de forma estricta las variables y columnas que son calculadas y almacenadas en los archivos finales del pipeline (`malla_maestra_mty_2026_v2.gpkg` y `ageb_maestra_mty_2026.gpkg`), destacando su relación con la intensidad de la isla de calor (SUHI):

| Nombre de Variable / Columna | Tipo de Dato | Escala Operativa | Fuente / Sensor de Origen | Descripción Técnica Objetiva |
| :--- | :---: | :---: | :---: | :--- |
| **`cell_id`** | Entero (`int`) | Malla de 30m | Interno (`grid.py`) | Identificador único numérico incremental asignado a cada celda de la cuadrícula de estudio. |
| **`geometry`** | Geometría (`Polygon`) | Malla de 30m / AGEB | Interno / INEGI | Geometría vectorial que define los límites espaciales (celda o polígono AGEB). |
| **`lst_day_c`** | Flotante (`float`) | Malla de 30m / AGEB | Landsat 8 (TIRS B10) | Temperatura Superficial Terrestre (LST) diurna calibrada en grados Celsius (°C), utilizada como insumo físico base para calcular la SUHI. |
| **`lst_night_c`** | Flotante (`float`) | Malla de 30m / AGEB | Landsat 8 (TIRS B10) | Temperatura Superficial Terrestre (LST) nocturna. Rellenada con `NaN` (desactivada en el actual MVP). |
| **`lst_c`** | Flotante (`float`) | Malla de 30m / AGEB | Landsat 8 (TIRS B10) | Copia directa de `lst_day_c` para compatibilidad en gráficas del pipeline. |
| **`green_pct`** | Flotante (`float`) | Malla de 30m / AGEB | Sentinel-2 (MSI) | Porcentaje de cobertura de vegetación verde activa (NDVI > 0.3). Clave para delimitar el área rural de control para SUHI. |
| **`industrial_osm_pct`** | Flotante (`float`) | Malla de 30m / AGEB | OpenStreetMap (OSM) | Porcentaje de superficie de la celda ocupado por usos de suelo industrial según polígonos de OSM. |
| **`suhi_day_c`** | Flotante (`float`) | Malla de 30m / AGEB | Landsat 8 / Interno | **Indicador de SUHI Diurna (°C)**. Diferencia de LST de cada celda contra el promedio térmico de 3 zonas de referencia rural externa (Norte, Este, Sur) calculado en GEE. |
| **`suhi_c`** | Flotante (`float`) | Malla de 30m / AGEB | Landsat 8 / Interno | Copia directa de `suhi_day_c` utilizada para propósitos de compatibilidad física en gráficos. |
| **`suhi_night_c`** | Flotante (`float`) | Malla de 30m / AGEB | Landsat 8 / Interno | **Indicador de SUHI Nocturna (°C)**. Rellenada con `NaN` (desactivada en el actual MVP). |
| **`dw_built_pct`** | Flotante (`float`) | Malla de 30m / AGEB | Dynamic World (GEE) | Porcentaje de cobertura del suelo "Edificada / Superficie Impermeable" (inductor físico de SUHI). |
| **`dw_trees_pct`** | Flotante (`float`) | Malla de 30m / AGEB | Dynamic World (GEE) | Porcentaje de cobertura del suelo "Árboles / Dosel Arbóreo" (mitigador de SUHI). |
| **`dw_bare_pct`** | Flotante (`float`) | Malla de 30m / AGEB | Dynamic World (GEE) | Porcentaje de cobertura del suelo "Suelo Desnudo / Suelo Expuesto". |
| **`dw_water_pct`** | Flotante (`float`) | Malla de 30m / AGEB | Dynamic World (GEE) | Porcentaje de cobertura del suelo "Agua". |
| **`dw_grass_pct`** | Flotante (`float`) | Malla de 30m / AGEB | Dynamic World (GEE) | Porcentaje de cobertura del suelo "Pastizales / Herbazales". |
| **`distance_to_industry_osm_m`**| Flotante (`float`) | Malla de 30m | OSM / Interno | Distancia euclidiana mínima en metros a zonas industriales (asociada a fuentes antropogénicas de calor). |
| **`distance_to_ternium_m`** | Flotante (`float`) | Malla de 30m | Interno (Point) | Distancia euclidiana en metros a la planta Ternium Guerrero (`Point(-100.299792, 25.720855)`). |
| **`distance_to_water_m`** | Flotante (`float`) | Malla de 30m | OSM / Interno | Distancia euclidiana mínima en metros a cuerpos de agua (sumideros urbanos de calor). |
| **`CVEGEO`** | Cadena (`str`) | Polígono AGEB | INEGI | Clave geoestadística única de identificación de la AGEB (13 dígitos). |
| **`area_km2`** | Flotante (`float`) | Polígono AGEB | INEGI | Área en kilómetros cuadrados (km²) calculada sobre el polígono de la AGEB. |
| **`POBTOT`** | Flotante (`float`) | Polígono AGEB | INEGI (Censo 2020) | Población residente total censada dentro de la AGEB. |
| **`POB0_14`** | Flotante (`float`) | Polígono AGEB | INEGI (Censo 2020) | Población infantil residente de 0 a 14 años de edad en la AGEB. |
| **`POB65_MAS`** | Flotante (`float`) | Polígono AGEB | INEGI (Censo 2020) | Población residente de 65 años y más (población vulnerable a olas de calor). |
| **`P_60YMAS`** | Flotante (`float`) | Polígono AGEB | INEGI (Censo 2020) | Población residente de 60 años y más. |
| **`P3YM_HLI`** | Flotante (`float`) | Polígono AGEB | INEGI (Censo 2020) | Población de 3 años y más que habla alguna lengua indígena en la AGEB. |
| **`pop_density_ageb`** | Flotante (`float`) | Polígono AGEB | INEGI / Interno | Densidad de población (habitantes por km²) de la AGEB: `POBTOT / area_km2`. |
| **`pct_0_14`** | Flotante (`float`) | Polígono AGEB | INEGI / Interno | Porcentaje de población infantil de 0 a 14 años en la AGEB. |
| **`pct_65_mas`** | Flotante (`float`) | Polígono AGEB | INEGI / Interno | Porcentaje de población vulnerable de 65 años o más en la AGEB. |
| **`pct_60ymas`** | Flotante (`float`) | Polígono AGEB | INEGI / Interno | Porcentaje de población adulta de 60 años o más en la AGEB. |
| **`pct_hli`** | Flotante (`float`) | Polígono AGEB | INEGI / Interno | Porcentaje de población indígena en la AGEB. |

---

## 4. Escalas de Análisis y Mitigación del MAUP

El diseño arquitectónico del pipeline implementa un esquema analítico a **dos escalas geográficas**:

### 1. Escala Micro (Malla Regular de 30m)
*   **Finalidad**: Análisis físico-ambiental continuo. La física térmica de la isla de calor y los patrones de vegetación ocurren de manera altamente localizada e independiente de las demarcaciones político-administrativas. 
*   **Ventaja**: El uso de una cuadrícula espacial regular (malla regular) de 30 metros de resolución permite mantener la variabilidad espacial fina (evitando la pérdida de información por suavizado espacial) y garantiza la precisión en la medición de métricas euclidianas exactas (como las distancias métricas a industrias, cuerpos de agua o la planta de Ternium).

### 2. Escala Macro (Agregación Administrativa por AGEB)
*   **Finalidad**: Análisis socioambiental y de justicia ambiental. Las variables demográficas y de vulnerabilidad socioeconómica del Censo INEGI no pueden asociarse directamente a un píxel por motivos éticos y metodológicos de agregación de datos y protección a la privacidad.
*   **Implementación**: Mediante un cruce de unión espacial por centroides (`Spatial Join`), se determina qué celdas de la malla de 30m pertenecen a qué polígonos de AGEB. Se calculan las estadísticas zonales (medias de LST, NDVI, coberturas y, de manera crucial, la intensidad de la **SUHI**) que a su vez se combinan con los atributos censales consolidados.

### Mitigación del MAUP (Modifiable Areal Unit Problem)
El MAUP es un sesgo estadístico que surge al agrupar observaciones individuales en unidades geográficas agregadas y arbitrarias, lo que puede distorsionar significativamente los coeficientes de correlación y otros análisis multivariados (diluyendo o exagerando asociaciones). Este pipeline mitiga este problema de la siguiente forma:
*   **Análisis Paralelo Multiescala**: En lugar de fusionar o interpolar artificialmente los datos censales a 30m, el pipeline mantiene dos procesos y dos suites estadísticas paralelas (Spearman Físico a 30m y Spearman Socioambiental a nivel AGEB). Esto aísla los fenómenos puramente físicos de los procesos demográficos y geodemográficos complejos.
*   **Normalización Demográfica**: Todas las variables demográficas a nivel AGEB se calculan y analizan como tasas normalizadas (porcentajes de población y densidades demográficas) en lugar de recuentos absolutos agregados. Esto contrarresta la distorsión del MAUP inducida por el efecto escala (diferentes tamaños de población entre AGEBs) y el efecto de agrupación espacial (formas irregulares de los polígonos).

---

## 5. Metodología Estadística y Auditoría de Datos

Como parte de la rigurosidad científica del pipeline, se ha estructurado una auditoría metodológica sobre el origen temporal de los datos, las correlaciones aplicadas y la calidad intrínseca de los sensores.

### 5.1. Temporalidad y Agregación Multitemporal
Para capturar de forma representativa la intensidad de la SUHI evitando anomalías transitorias de un solo día (ej. frentes fríos locales o días con alta nubosidad), el pipeline utiliza una agregación multitemporal basada en Earth Engine:
*   **Ventana de Análisis**: Primavera (Temporada Seca/Cálida: 1 de marzo al 31 de mayo de 2026). Éste es el periodo de mayor estrés térmico en el norte de México.
*   **Procesamiento LST (Landsat 8)**: Se consultan todas las escenas de la colección del sensor TIRS disponibles para este rango de fechas. Se aplica una reducción temporal por **mediana** a nivel de píxel. La mediana matemática limpia efectivamente los valores extremos causados por nubes no detectadas, sombras de nubes o anomalías del sensor, preservando el valor térmico central más probable de la temporada seca.
*   **Procesamiento NDVI (Sentinel-2)**: En lugar de un compuesto, el algoritmo selecciona la **escena única con menor cobertura de nubes** (`first()` de la colección ordenada por nubosidad). Esto garantiza la integridad espectral de las bandas roja e infrarroja cercana para el cálculo del NDVI, evitando el "suavizado" artificial de los índices vegetales que causan los compuestos medianos en áreas con rápido crecimiento estacional.
*   **Procesamiento Dynamic World**: Promedia las probabilidades de cobertura temporal de primavera mediante la **media** aritmética. Esto permite representar la probabilidad persistente de cada celda a pertenecer a una cobertura específica durante la temporada (por ejemplo, qué tan consistentemente una superficie actúa como construida u arbolada).

### 5.2. Análisis de Correlación y Propuestas Avanzadas
Actualmente se calcula la **Correlación de Rangos de Spearman (No Paramétrica)** para ambas escalas operativas (celda de 30m y polígono AGEB). Esta elección metodológica se debe a que las variables ambientales y la temperatura no poseen relaciones lineales ni distribuciones normales (ej. la distancia industrial tiene un decaimiento térmico exponencial o logarítmico).

#### 5.2.1. Top 10 de Correlaciones de Mayor Impacto (Actualizado 2026)
A continuación se detallan las variables físicas y sociales que presentan mayor correlación (en magnitud absoluta) con la intensidad de la Isla de Calor Urbana Superficial (`suhi_c`), calculadas directamente sobre las bases de datos maestras:

##### A. Variables Físicas (Escala Malla 30m)
*Estas variables explican el comportamiento biofísico y estructural directo sobre la anomalía térmica.*

| # | Variable | Spearman ($r$) | Tipo de Impacto | Interpretación de Impacto Territorial |
| :---: | :--- | :---: | :---: | :--- |
| **1** | **`green_pct`** | **-0.230** | Mitigador | Cobertura verde activa. Principal regulador térmico por evapotranspiración. |
| **2** | **`dw_trees_pct`** | **-0.210** | Mitigador | Cobertura forestal de dosel arbóreo (Dynamic World). |
| **3** | **`dw_grass_pct`** | **-0.173** | Mitigador | Cobertura de pastos y vegetación herbácea. |
| **4** | **`industrial_osm_pct`** | **+0.172** | Intensificador | Uso de suelo industrial activo (alta emisión de calor). |
| **5** | **`dw_built_pct`** | **+0.158** | Intensificador | Superficie urbana impermeable/construida (asfalto, concreto). |
| **6** | **`distance_to_industry_osm_m`** | **-0.141** | Mitigador Ind. | A mayor distancia de industrias, disminuye la SUHI. |
| **7** | **`dw_bare_pct`** | **+0.098** | Intensificador | Suelo desnudo/expuesto. Absorbe calor sin inercia de concreto. |
| **8** | **`distance_to_ternium_m`** | **-0.060** | Mitigador Ind. | A mayor distancia de la planta Ternium Guerrero, menor calor. |
| **9** | **`distance_to_water_m`** | **-0.057** | Mitigador Ind. | Distancia a cuerpos de agua (débil por la escasez local de agua). |
| **10** | **`dw_water_pct`** | **-0.040** | Mitigador | Presencia local de agua superficial. |

##### B. Variables Sociales y de Vulnerabilidad (Escala AGEB)
*Estas variables reflejan justicia ambiental y distribución de la exposición social ante la SUHI.*

| # | Variable | Spearman ($r$) | Relación Térmica | Significado de Justicia Ambiental / Exposición |
| :---: | :--- | :---: | :---: | :--- |
| **1** | **`pct_vph_snbien`** | **-0.170** | Menor Calor | **Efecto Periferia:** Las viviendas de menor nivel socioeconómico se ubican en la periferia de la ZMM, cerca de límites rurales más frescos. |
| **2** | **`pct_0_14`** | **-0.169** | Menor Calor | Los fraccionamientos familiares periféricos son térmicamente más frescos. |
| **3** | **`pct_65_mas`** | **+0.169** | **Mayor Calor** | **¡Vulnerabilidad Crítica!** Los adultos mayores viven en las zonas centrales más antiguas de la ciudad, que son las más calientes. |
| **4** | **`pct_60ymas`** | **+0.151** | **Mayor Calor** | Refuerza el patrón de exposición del sector demográfico mayor de 60 años. |
| **5** | **`pop_density_ageb`** | **-0.117** | Menor Calor | Densidades compactas residenciales son menos cálidas que las extensas zonas industriales sin población. |
| **6** | **`graproes`** | **+0.116** | **Mayor Calor** | Población con mayor educación se concentra en distritos comerciales centrales densos. |
| **7** | **`pct_vph_refri`** | **+0.106** | **Mayor Calor** | Proxy de riqueza/centralidad urbana correlacionado con mayores temperaturas. |
| **8** | **`POB65_MAS`** | **+0.102** | **Mayor Calor** | Conteo absoluto de adultos mayores expuestos térmicamente en el centro. |
| **9** | **`POB0_14`** | **-0.094** | Menor Calor | Conteo absoluto de población infantil en zonas periféricas. |
| **10** | **`pct_psinder`** | **-0.085** | Menor Calor | Marginación en salud correlacionada con las áreas periféricas más templadas. |

#### Propuestas Estadísticas Avanzadas (Próximos Pasos):
Para superar las limitaciones de la correlación simple, se propone incorporar en futuras iteraciones:
1.  **Autocorrelación Espacial (Moran's I Global y Local)**: El fenómeno SUHI viola el supuesto estadístico de independencia de las observaciones. Calcular el Índice de Moran permitiría mapear estadísticamente los **Hotspots (LISA - Local Indicators of Spatial Association)** de calor urbano (zonas industriales y de alta densidad edificada) y **Coldspots** (zonas arboladas y de control rural).
2.  **Modelos de Regresión Espacial (SAR y GWR)**: OLS estándar (mínimos cuadrados) sufre de autocorrelación en los residuos en datos espaciales. Se propone implementar modelos de **Regresión Espacial Autorregresiva (SAR)** o **Regresión Ponderada Geográficamente (GWR)** para evaluar el impacto local y espacialmente variable de coberturas como `dw_built_pct` y `dw_trees_pct` sobre la intensidad de `suhi_day_c`.
3.  **Índice de Vulnerabilidad Térmica (TVI)**: Construcción de un índice multivariado ponderado que combine el Peligro Físico (intensidad SUHI) con la Sensibilidad Social (densidad de población de adultos mayores `pct_65_mas` y densidad de población infantil `pct_0_14` por AGEB).

### 5.3. Auditoría de Calidad y Naturaleza de las Fuentes de Datos

| Sensor / Fuente | Naturaleza de la Medida | Resolución Espacial | Limitaciones e Incertidumbre Espectral |
| :--- | :--- | :---: | :--- |
| **Landsat 8 (TIRS)** | Radianza Térmica (Banda 10) | 100m (resampleado a 30m) | **Incertidumbre de Resolución:** El sensor térmico adquiere a 100m de resolución y es remuestreado por el USGS a 30m mediante interpolación de convolución cúbica. Esto genera una dispersión y dilución física de puntos de calor muy localizados (micro-islas de calor). Adicionalmente, la corrección de emisividad depende de estimaciones auxiliares del vapor de agua atmosférico. |
| **Sentinel-2 (MSI)** | Reflectancia Óptica (B8 y B4) | 10m | **Alta Precisión:** Adquisición a 10m. La corrección atmosférica integrada (Level 2A) es altamente robusta. Limitada únicamente por la presencia de cobertura nubosa persistente o sombras topográficas. |
| **Dynamic World (GEE)** | Clasificación de Cobertura (Deep Learning) | 10m | **Incertidumbre del Modelo:** Al ser un clasificador probabilístico basado en redes neuronales convolucionales aplicadas sobre Sentinel-2, está sujeto a errores de clasificación espectral. Áreas mixtas (suelo desnudo con vegetación seca o techos con materiales específicos) pueden presentar clasificaciones erróneas. |
| **OpenStreetMap (OSM)** | Vectores Colaborativos (Crowdsourcing) | Variable | **Heterogeneidad de Datos:** Alta completitud en el centro de la zona metropolitana para zonas industriales y cuerpos de agua de gran tamaño. Existe riesgo de omisión o retraso de actualización en áreas industriales periféricas recientes y en pequeños canales de escurrimiento temporales. |
| **INEGI (Censo 2020)** | Datos Sociodemográficos Tabulares | Polígono AGEB | **Desfase Temporal:** El censo fue levantado en 2020. Al contrastar con datos térmicos de 2026, existe un desfase temporal de 6 años que no refleja el acelerado crecimiento demográfico y la expansión urbana de la periferia de Monterrey en los últimos años. |

### 5.4. Variables Socioeconómicas y Pobreza (Próximos Pasos con el Censo Completo)  
Dado que el Censo Decenal de Población y Vivienda del INEGI no recolecta ingresos económicos directos (por la alta tasa de omisión y subdeclaración), los estudios de vulnerabilidad socioambiental ante la isla de calor (SUHI) utilizan **variables proxy de bienestar material, educación e infraestructura**. 

Una vez que se reemplace la base de datos censal por el **CSV completo de 230 columnas de INEGI**, el pipeline podrá incorporar automáticamente las siguientes variables socioeconómicas críticas para mapear la justicia distributiva del calor:

1.  **Educación (`GRAPROES`):** *Grado Promedio de Escolaridad*. Es el estimador más fuerte y estable en México del nivel socioeconómico de la población en zonas urbanas. A mayor escolaridad, mayor capacidad de adaptación, mejor aislamiento térmico en viviendas y mayor acceso a aire acondicionado.
2.  **Riqueza y Bienes (`VPH_AUTOMOV` y `VPH_INTERNET`):** *Porcentaje de viviendas con automóvil o acceso a Internet*. Actúan como indicadores directos de ingresos familiares medios y altos en la ZMM.
3.  **Pobreza Extrema e Infraestructura (`VPH_ND_HU`):** *Porcentaje de viviendas particulares habitadas que no disponen de energía eléctrica, agua entubada ni drenaje*. Identifica directamente núcleos de pobreza extrema y precariedad habitacional extrema ante olas de calor.
4.  **Vulnerabilidad Laboral (`PDER_SS`):** *Porcentaje de población sin afiliación a servicios de salud*. Identifica sectores con empleo informal y menores recursos para solventar complicaciones de salud derivadas del calor extremo.

---

## 6. Hoja de Ruta de Correcciones (Roadmap)

A continuación, se detalla la hoja de ruta para la depuración y consolidación del MVP, priorizada por nivel de criticidad técnica:

### 🔴 Criticidad Alta (Bloqueante para el Análisis Completo)
*   **Reemplazo del Archivo de Censo Truncado:**
    *   *Problema:* El archivo actual `RESAGEBURB2020 - 19 Nuevo León (1).csv` está truncado a la línea 30,000 y limitado a 62 columnas. Esto causa la pérdida de información para el 60% del estado (incluyendo más del 55% de las AGEB de Monterrey) y omite todas las variables de vivienda e ingresos del censo.
    *   *Corrección:* Descargar el archivo CSV completo para Nuevo León desde el portal oficial de INEGI y guardarlo en `data/raw/` con el mismo nombre, asegurando que contenga las más de 80,000 filas y las 230+ columnas del censo.

### 🟡 Criticidad Media (Mejora y Rigurosidad del Modelo)
*   **Integración de Proxies de Ingresos y Pobreza:**
    *   *Problema:* El modelo actual de vulnerabilidad socioambiental solo incluye índices demográficos por grupos de edad, omitiendo la dimensión de desigualdad económica y de infraestructura en las viviendas.
    *   *Corrección:* Modificar el módulo `src/ageb_social.py` para extraer, normalizar y calcular los promedios/tasas de `GRAPROES` (grado de escolaridad), `VPH_AUTOMOV` (indicador de riqueza familiar), `VPH_ND_HU` (pobreza extrema habitacional) y `PDER_SS` (informalidad laboral) a nivel de AGEB una vez reemplazado el censo completo.

### 🟢 Criticidad Baja (Precisión y Enriquecimiento de Capas)
*   **Migración de Capas Industriales de OSM a DENUE (INEGI):**
    *   *Problema:* Los polígonos industriales obtenidos de OpenStreetMap (`industrial_osm_pct`) dependen de la digitalización colaborativa de voluntarios, lo que puede causar desfases de actualización en periferias urbanas y clasifica erróneamente naves de almacenamiento logístico (no emisores térmicos) como industria activa.
    *   *Corrección:* Reemplazar la descarga de OSM por la base de datos oficial del DENUE (INEGI), filtrando establecimientos industriales activos de manufactura pesada a través de códigos SCIAN específicos y modelando buffers de calor antropogénico basados en número de empleados.

---

## 7. Siguientes Pasos (Evolución Científica)

Para la evolución metodológica del pipeline hacia un modelo científico y de planificación urbana avanzado, se proponen los siguientes pasos:

1.  **Mapeo de Clústeres de Calor (Moran's I & LISA):**
    Implementar en `src/stats.py` rutinas para calcular la autocorrelación espacial de la SUHI. Esto permitirá delimitar estadísticamente **Hotspots** (islas de calor significativas) y **Coldspots** (zonas de amortiguamiento o enfriamiento térmico regular), superando las limitaciones de las correlaciones asociales simples de Spearman.
2.  **Modelado de Regresión Geográficamente Ponderada (GWR):**
    Transicionar de correlaciones globales a modelos **GWR**, lo que permitirá determinar cómo la capacidad de mitigación térmica de los árboles (`dw_trees_pct`) varía espacialmente en función del sector geográfico de la Zona Metropolitana de Monterrey.
3.  **Desarrollo del Índice de Vulnerabilidad Térmica (TVI):**
    Construir un mapa de vulnerabilidad integrado superponiendo el peligro físico (anomalías de la intensidad de la **SUHI**) con la sensibilidad social (tasas de pobreza extrema, analfabetismo y densidad de población de adultos mayores). Esto permitirá priorizar las intervenciones de reforestación urbana en los sectores más críticos de la ZMM.
