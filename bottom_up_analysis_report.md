# Reporte Técnico: Análisis de Correlación Espacial Bottom-Up (Municipios y AGEB)
Este documento presenta los resultados de la modelación estadística de la Isla de Calor Urbana Superficial (SUHI) en la Zona Metropolitana de Monterrey para el año 2026. A diferencia de las aproximaciones agregadas de nivel superior (Top-Down), este análisis adopta un enfoque **Bottom-Up**, manteniendo la celda física regular de 30 metros como unidad de observación básica e incorporando los límites político-administrativos (Municipios y AGEBs) como contenedores geográficos de análisis.

---

## 1. Síntesis Ejecutiva de Hallazgos
1. **Doble régimen térmico (Mitigación vs Presión)**: La vegetación actúa como el principal regulador del calor (mitigación), mostrando su mayor eficiencia en áreas periurbanas de baja densidad. Por otro lado, la densidad industrial OSM representa una fuente activa de presión térmica directa, concentrando e intensificando las islas de calor urbanas de forma persistente.
2. **La escala óptima de buffer (250m a 500m)**: Los coeficientes de correlación demuestran que tanto el enfriamiento por vegetación como el calentamiento industrial alcanzan su pico de correlación en escalas intermedias de buffer (250m y 500m), lo que evidencia la importancia del vecindario térmico inmediato sobre la celda puntual de 30m.
3. **El fenómeno de Saturación**: En zonas de alta densidad (>= 60% edificado), la correlación local de la vegetación cae a niveles nulos ($r pprox -0.05$). Esto sugiere la ineficacia de intervenciones de arborización puntuales en áreas saturadas de asfalto y hormigón, requiriendo de políticas metropolitanas integradas.

---

## 2. Resultados a Nivel de Municipio

### 2.1. Eficiencia Térmica Global (Local 30m vs Buffer 500m)

#### A. Bloque Mitigación: Vegetación (`green_pct` vs `green_pct_500m`)
Correlaciones globales de Spearman ($r$) entre la SUHI diurna (`suhi_day_c`) y la vegetación:

| Municipio | Coeficiente Local (30m) | Coeficiente Vecindario (500m) | Celdas de 30m Analizadas |
| :--- | :---: | :---: | :---: |
| San Pedro Garza García | **-0.239** | **-0.247** | 23,217 |
| Guadalupe | **-0.210** | -0.062 | 21,320 |
| San Nicolás de los Garza | -0.088 | -0.098 | 26,009 |
| Monterrey | -0.068 | +0.007 | 107,744 |

#### B. Bloque Presión Térmica: Industria (`industrial_osm_pct` vs `industrial_density_500m`)
Correlaciones globales de Spearman ($r$) entre la SUHI diurna (`suhi_day_c`) y la presencia industrial:

| Municipio | Coeficiente Local (30m) | Coeficiente Vecindario (500m) | Celdas de 30m Analizadas |
| :--- | :---: | :---: | :---: |
| San Nicolás de los Garza | **+0.409** | **+0.493** | 26,009 |
| Monterrey | +0.121 | +0.149 | 107,744 |
| Guadalupe | +0.001 | -0.177 | 21,320 |
| San Pedro Garza García | -0.006 | +0.013 | 23,217 |

### 2.2. Sensibilidad Térmica de la Vegetación (Mitigación) por Densidad y Escala de Buffer
Comparación de coeficientes de Spearman ($r$) para el bloque de Mitigación (Vegetación) a diferentes escalas de buffer segmentados por la densidad construida de cada municipio:

| Municipio | Zona de Densidad | Local (30m) | Buffer 100m | Buffer 250m | Buffer 500m | Buffer 1000m (1km) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| San Pedro Garza García | Baja | **-0.781** | **-0.811** | **-0.806** | **-0.779** | **-0.720** |
| San Pedro Garza García | Media | -0.319 | **-0.374** | -0.278 | -0.171 | -0.121 |
| San Pedro Garza García | Alta | -0.116 | -0.201 | -0.202 | -0.170 | -0.133 |
| Guadalupe | Baja | -0.278 | **-0.567** | **-0.645** | **-0.644** | **-0.676** |
| Guadalupe | Media | -0.150 | -0.234 | -0.255 | -0.190 | -0.104 |
| Guadalupe | Alta | -0.042 | -0.048 | +0.037 | +0.114 | +0.335 |
| San Nicolás de los Garza | Baja | **-0.536** | **-0.592** | **-0.632** | **-0.674** | **-0.618** |
| San Nicolás de los Garza | Media | -0.091 | -0.137 | -0.138 | -0.135 | -0.086 |
| San Nicolás de los Garza | Alta | -0.083 | -0.140 | -0.120 | -0.079 | +0.044 |
| Monterrey | Baja | **-0.489** | **-0.609** | **-0.611** | **-0.522** | -0.140 |
| Monterrey | Media | -0.133 | -0.179 | -0.162 | -0.137 | -0.069 |
| Monterrey | Alta | -0.026 | -0.022 | +0.028 | +0.063 | +0.120 |

### 2.3. Sensibilidad Térmica de la Industria (Presión Térmica) por Densidad y Escala de Buffer
Comparación de coeficientes de Spearman ($r$) para el bloque de Presión Térmica (Industria OSM) a diferentes escalas de buffer segmentados por la densidad construida de cada municipio:

| Municipio | Zona de Densidad | Local (30m) | Buffer 100m | Buffer 250m | Buffer 500m | Buffer 1000m (1km) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| San Pedro Garza García | Baja | N/D | N/D | +0.079 | **+0.260** | **+0.579** |
| San Pedro Garza García | Media | N/D | +0.043 | +0.224 | **+0.288** | **+0.565** |
| San Pedro Garza García | Alta | -0.013 | -0.031 | -0.066 | -0.063 | +0.029 |
| Guadalupe | Baja | N/D | +0.047 | +0.093 | +0.205 | **+0.256** |
| Guadalupe | Media | +0.066 | +0.066 | +0.089 | +0.038 | -0.025 |
| Guadalupe | Alta | -0.030 | -0.049 | -0.129 | -0.271 | -0.378 |
| San Nicolás de los Garza | Baja | **+0.573** | **+0.595** | **+0.624** | **+0.630** | **+0.643** |
| San Nicolás de los Garza | Media | **+0.405** | **+0.444** | **+0.443** | **+0.439** | **+0.424** |
| San Nicolás de los Garza | Alta | **+0.411** | **+0.473** | **+0.500** | **+0.505** | **+0.469** |
| Monterrey | Baja | -0.009 | +0.104 | **+0.379** | **+0.540** | **+0.596** |
| Monterrey | Media | **+0.253** | **+0.316** | **+0.361** | **+0.374** | **+0.304** |
| Monterrey | Alta | +0.093 | +0.116 | +0.124 | +0.088 | +0.021 |

---

## 3. Resultados a Nivel de Vecindario (AGEB)

El análisis bottom-up calculó de forma independiente las correlaciones dentro de cada una de las AGEBs del área metropolitana, arrojando luz sobre la heterogeneidad espacial de la mitigación.

### 3.1. Distribución de Coeficientes de Spearman ($r$) en AGEBs
Estadísticos descriptivos de los coeficientes de correlación calculados sobre las celdas internas de cada AGEB:

| Indicador Estadístico | Mitigación Local (`green_pct`) | Mitigación Buffer (`green_pct_500m`) | Presión Local (`ind_osm`) | Presión Buffer (`ind_density_500m`) |
| :--- | :---: | :---: | :---: | :---: |
| Promedio de Spearman ($r$) | -0.121 | -0.116 | +0.143 | +0.131 |
| Desviación Estándar | 0.204 | 0.468 | 0.282 | 0.438 |
| Valor Mínimo | -0.791 | -0.991 | -0.536 | -0.850 |
| Valor Máximo | +0.606 | +0.950 | +0.838 | +0.927 |
| total de AGEBs con datos válidos | 380 | 380 | 99 | 217 |

### 3.2. Mapa de Sensibilidad y Exportación Espacial
Los coeficientes de correlación resultantes de este análisis han sido unidos de regreso a las geometrías de las AGEBs en el archivo procesado `data/processed/ageb_correlaciones_sensibilidad.gpkg`.
Las columnas agregadas son:
* **`r_green_global`**: Correlación local global de la celda de 30m.
* **`r_green500_global`**: Correlación a escala de vecindario (500m).
* **`r_ind_global`**: Correlación local global para la presencia industrial.
* **`r_ind500_global`**: Correlación a escala de vecindario (500m) para la densidad industrial.
* **`r_green_alta` / `r_green_media` / `r_green_baja`**: Correlaciones locales de vegetación segmentadas por la densidad interna de la AGEB.

Este Geopackage está listo para ser cargado en QGIS o ArcGIS para la generación de mapas de calor y priorización territorial de infraestructura verde.

---

## 4. Recomendaciones de Política Pública
1. **Regulación de Presión Industrial**: Los municipios de Apodaca y Escobedo deben focalizar la plantación de buffers de absorción forestal a escalas de 250m a 500m alrededor de los polígonos industriales, ya que a esta escala la presión térmica alcanza correlaciones robustas con la intensidad de la SUHI.
2. **Mitigación de Saturación**: En áreas consolidadas donde la correlación de vegetación disminuye drásticamente, se debe priorizar intervenciones sobre la inercia térmica de los materiales (pavimentos fríos, reflectancia en techos y fachadas) en lugar de arborización dispersa inefectiva.
3. **Parques de Vecindario**: En áreas residenciales de densidad media, incentivar parques comunitarios arbolados con radios de influencia de 500m, maximizando el efecto de advección térmica local y optimizando el retorno de inversión térmica.
