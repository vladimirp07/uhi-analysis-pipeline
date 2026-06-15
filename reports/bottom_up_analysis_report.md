# Reporte Técnico: Análisis de Correlación Espacial Bottom-Up (Municipios y AGEB)
Este documento presenta los resultados de la modelación estadística de la Isla de Calor Urbana Superficial (SUHI) en la Zona Metropolitana de Monterrey para el año 2026. A diferencia de las aproximaciones agregadas de nivel superior (Top-Down), este análisis adopta un enfoque **Bottom-Up**, manteniendo la celda física regular de 30 metros como unidad de observación básica e incorporando los límites político-administrativos (Municipios y AGEBs) como contenedores geográficos de análisis.

---

## 1. Síntesis Ejecutiva de Hallazgos
1. **Diferenciación de Regímenes Térmicos**: La vegetación presenta asociaciones negativas con la SUHI, principalmente en zonas de baja densidad, mientras que la industria muestra asociaciones positivas, especialmente en San Nicolás y sectores de Monterrey. Esto permite distinguir entre variables asociadas a enfriamiento y variables asociadas a presión térmica.
2. **Escalas de Asociación Variable**: Los resultados muestran que las asociaciones más intensas tienden a aparecer en escalas intermedias y amplias, especialmente entre 250 m y 1000 m, aunque la escala dominante cambia según municipio, densidad y tipo de variable.
3. **Efecto de Saturación en Áreas Densas**: Al segmentar los vecindarios (AGEBs) por su densidad de suelo construido, se observa que en las zonas de alta densidad (>= 60%), la correlación negativa entre la vegetación local y la SUHI diurna disminuye a valores estadísticamente no significativos ($r \approx -0.05$). Los resultados sugieren que en entornos saturados de concreto, la reforestación aislada no muestra asociación estadística significativa con la reducción de la temperatura superficial.

---

## 2. Resultados a Nivel de Municipio

### 2.1. Asociación Térmica Global (Local 30m vs Buffer 500m)

#### A. Bloque Asociación Biofísica de Enfriamiento: Vegetación (`green_pct` vs `green_pct_500m`)
Correlaciones globales de Spearman ($r$) entre la SUHI diurna (`suhi_day_c`) y la vegetación:

| Municipio | Coeficiente Local (30m) | Coeficiente Vecindario (500m) | Celdas de 30m Analizadas |
| :--- | :---: | :---: | :---: |
| San Pedro Garza García | **-0.239** | **-0.247** | 23,217 |
| Guadalupe | **-0.210** | -0.062 | 21,320 |
| San Nicolás de los Garza | -0.088 | -0.098 | 26,009 |
| Monterrey | -0.068 | +0.007 | 107,744 |

#### B. Bloque Asociación Térmica de Calentamiento: Industria (`industrial_osm_pct` vs `industrial_density_500m`)
Correlaciones globales de Spearman ($r$) entre la SUHI diurna (`suhi_day_c`) y la presencia industrial:

| Municipio | Coeficiente Local (30m) | Coeficiente Vecindario (500m) | Celdas de 30m Analizadas |
| :--- | :---: | :---: | :---: |
| San Nicolás de los Garza | **+0.409** | **+0.493** | 26,009 |
| Monterrey | +0.121 | +0.149 | 107,744 |
| Guadalupe | +0.001 | -0.177 | 21,320 |
| San Pedro Garza García | -0.006 | +0.013 | 23,217 |

### 2.2. Coeficientes de Vegetación (Mitigación) por Densidad y Escala de Buffer
Comparación de coeficientes de Spearman ($r$) para el bloque de Mitigación (Vegetación) a diferentes escalas de buffer segmentados por la densidad construida de cada municipio:

| Municipio | Zona de Densidad | Celdas (N) | Local (30m) | Buffer 100m | Buffer 250m | Buffer 500m | Buffer 1000m (1km) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| San Pedro Garza García | Baja | 1,723 | **-0.781** | **-0.811** | **-0.806** | **-0.779** | **-0.720** |
| San Pedro Garza García | Media | 2,298 | -0.319 | **-0.374** | -0.278 | -0.171 | -0.121 |
| San Pedro Garza García | Alta | 19,196 | -0.116 | -0.201 | -0.202 | -0.170 | -0.133 |
| Guadalupe | Baja | 1,510 | -0.278 | **-0.567** | **-0.645** | **-0.644** | **-0.676** |
| Guadalupe | Media | 3,248 | -0.150 | -0.234 | -0.255 | -0.190 | -0.104 |
| Guadalupe | Alta | 16,562 | -0.042 | -0.048 | +0.037 | +0.114 | +0.335 |
| San Nicolás de los Garza | Baja | 120 | **-0.536** | **-0.592** | **-0.632** | **-0.674** | **-0.618** |
| San Nicolás de los Garza | Media | 6,360 | -0.091 | -0.137 | -0.138 | -0.135 | -0.086 |
| San Nicolás de los Garza | Alta | 19,529 | -0.083 | -0.140 | -0.120 | -0.079 | +0.044 |
| Monterrey | Baja | 3,129 | **-0.489** | **-0.609** | **-0.611** | **-0.522** | -0.140 |
| Monterrey | Media | 14,438 | -0.133 | -0.179 | -0.162 | -0.137 | -0.069 |
| Monterrey | Alta | 90,177 | -0.026 | -0.022 | +0.028 | +0.063 | +0.120 |

### 2.3. Coeficientes de la Industria (Presión Térmica) por Densidad y Escala de Buffer
Comparación de coeficientes de Spearman ($r$) para el bloque de Presión Térmica (Industria OSM) a diferentes escalas de buffer segmentados por la densidad construida de cada municipio:

| Municipio | Zona de Densidad | Celdas (N) | Local (30m) | Buffer 100m | Buffer 250m | Buffer 500m | Buffer 1000m (1km) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| San Pedro Garza García | Baja | 1,723 | N/D | N/D | +0.079 | **+0.260** | **+0.579** |
| San Pedro Garza García | Media | 2,298 | N/D | +0.043 | +0.224 | **+0.288** | **+0.565** |
| San Pedro Garza García | Alta | 19,196 | -0.013 | -0.031 | -0.066 | -0.063 | +0.029 |
| Guadalupe | Baja | 1,510 | N/D | +0.047 | +0.093 | +0.205 | **+0.256** |
| Guadalupe | Media | 3,248 | +0.066 | +0.066 | +0.089 | +0.038 | -0.025 |
| Guadalupe | Alta | 16,562 | -0.030 | -0.049 | -0.129 | -0.271 | -0.378 |
| San Nicolás de los Garza | Baja | 120 | **+0.573** | **+0.595** | **+0.624** | **+0.630** | **+0.643** |
| San Nicolás de los Garza | Media | 6,360 | **+0.405** | **+0.444** | **+0.443** | **+0.439** | **+0.424** |
| San Nicolás de los Garza | Alta | 19,529 | **+0.411** | **+0.473** | **+0.500** | **+0.505** | **+0.469** |
| Monterrey | Baja | 3,129 | -0.009 | +0.104 | **+0.379** | **+0.540** | **+0.596** |
| Monterrey | Media | 14,438 | **+0.253** | **+0.316** | **+0.361** | **+0.374** | **+0.304** |
| Monterrey | Alta | 90,177 | +0.093 | +0.116 | +0.124 | +0.088 | +0.021 |

*Nota: N/D indica que no existió suficiente variabilidad espacial de la variable industrial dentro del subconjunto analizado para calcular una correlación estable.*

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

## 4. Recomendaciones de Política Pública e Intervenciones Urbanas

1. **Gestión de la Presión Industrial y Amortiguamiento Intermunicipal**:
   Los municipios con una fuerte asociación positiva entre la SUHI y la presencia industrial en escalas locales e intermedias (como **San Nicolás de los Garza** y zonas específicas de **Monterrey**) deben priorizar la implementación de buffers de absorción forestal a escalas de 250 m a 500 m adyacentes a sus polígonos industriales. 
   Para el caso de **San Pedro Garza García**, la fuerte correlación positiva observada en buffers amplios (500 m y 1000 m) en zonas de baja y media densidad no corresponde a zonas industriales locales (ya que el municipio tiene un uso de suelo predominantemente residencial y comercial), sino a un **efecto de colindancia o desbordamiento espacial (*spatial spillover*)**. El buffer de 1000 m captura el corredor industrial del eje Díaz Ordaz en Santa Catarina y áreas industriales limítrofes de Monterrey, demostrando que la presión térmica industrial trasciende fronteras municipales. Esto sugiere que las políticas de amortiguamiento y control térmico industrial deben coordinarse a nivel metropolitano.

2. **Acción Diferenciada en Zonas de Alta Densidad (Materialidad vs. Vegetación)**:
   En áreas urbanas altamente consolidadas (densidad construida $\ge 60\%$) de los cuatro municipios analizados, la correlación negativa entre la vegetación local y la SUHI diurna tiende a ser cercana a cero ($r \approx -0.05$). Esto sugiere que en entornos saturados de concreto, la arborización dispersa tiene una asociación estadística muy débil con el enfriamiento superficial. En estas zonas se debe priorizar la mitigación pasiva mediante la modificación de la materialidad urbana (aumento de albedo en techos, fachadas y pavimentos fríos) para contrarrestar la inercia térmica.

3. **Planificación de Infraestructura Verde a Escala de Vecindario**:
   En áreas residenciales de densidad media, la asociación biofísica negativa con la vegetación es más intensa a escalas de vecindario (buffers de 250 m a 500 m) que a escala local inmediata (30 m). Por ende, se sugiere el desarrollo de parques y corredores verdes de escala barrial, priorizando radios de influencia entre 250 m y 500 m, y evaluando extensiones mayores en zonas donde los buffers amplios muestran mayor asociación.
