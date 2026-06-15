# Reporte Técnico: Análisis de Correlación Espacial Bottom-Up (Municipios y AGEB)
Este documento presenta los resultados de la modelación estadística de la Isla de Calor Urbana Superficial (SUHI) en la Zona Metropolitana de Monterrey para el año 2026. A diferencia de las aproximaciones agregadas de nivel superior (Top-Down), este análisis adopta un enfoque **Bottom-Up**, manteniendo la celda física regular de 30 metros como unidad de observación básica e incorporando los límites político-administrativos (Municipios y AGEBs) como contenedores geográficos de análisis.

---

## Índice de Contenidos
1. [Síntesis Ejecutiva de Hallazgos](#1-síntesis-ejecutiva-de-hallazgos)
2. [Notas Metodológicas e Interpretación Estadística](#2-notas-metodológicas-e-interpretación-estadística)
3. [Resultados a Nivel de Municipio](#3-resultados-a-nivel-de-municipio)
   * 3.1 [Asociación Térmica Global (Local 30m vs Buffer 500m)](#31-asociación-térmica-global-local-30m-vs-buffer-500m)
   * 3.2 [Coeficientes de Vegetación (Mitigación) por Densidad y Escala de Buffer](#32-coeficientes-de-vegetación-mitigación-por-densidad-y-escala-de-buffer)
   * 3.3 [Coeficientes de la Industria (Presión Térmica) por Densidad y Escala de Buffer](#33-coeficientes-de-la-industria-presión-térmica-por-densidad-y-escala-de-buffer)
4. [Resultados a Nivel de Vecindario (AGEB)](#4-resultados-a-nivel-de-vecindario-ageb)
   * 4.1 [Distribución de Coeficientes de Spearman ($r$) en AGEBs](#41-distribución-de-coeficientes-de-spearman-r-en-agebs)
   * 4.2 [Mapa de Sensibilidad y Exportación Espacial](#42-mapa-de-sensibilidad-y-exportación-espacial)
5. [Recomendaciones de Intervención Urbana y Política Pública](#5-recomendaciones-de-intervención-urbana-y-política-pública)

---

## 1. Síntesis Ejecutiva de Hallazgos
1. **Diferenciación de Regímenes Térmicos**: La vegetación presenta asociaciones negativas con la SUHI, principalmente en zonas de baja densidad, mientras que la industria muestra asociaciones positivas, especialmente en San Nicolás y sectores de Monterrey. Esto permite distinguir entre variables asociadas a enfriamiento y variables asociadas a presión térmica.
2. **Escalas de Asociación Variable**: Los resultados sugieren que las asociaciones más intensas tienden a aparecer en escalas intermedias y amplias, especialmente entre 250 m y 1000 m, aunque la escala de mayor correlación cambia según municipio, densidad construida y tipo de variable.
3. **Asociación Limitada en Áreas Densas (Saturación Construida)**: Al segmentar los vecindarios (AGEBs) por su densidad de suelo construido, se observa que en las zonas de alta densidad (>= 60%), la correlación de la vegetación local con la SUHI diurna tiende a valores estadísticamente no significativos ($r \approx -0.05$). Los resultados sugieren que en entornos con alto porcentaje de suelo impermeable, la presencia aislada de vegetación no muestra asociación estadística fuerte con la variación de la temperatura superficial.

---

## 2. Notas Metodológicas e Interpretación Estadística

* **Naturaleza de la Correlación de Spearman**: Este análisis utiliza el coeficiente de correlación de rangos de Spearman ($r$) para cuantificar las relaciones espaciales. Este coeficiente evalúa exclusivamente la fuerza y dirección de una **asociación monotónica** (sea creciente o decreciente) entre dos variables continuas. **Es fundamental precisar que la presencia de correlación estadística no implica causalidad física ni una relación causa-efecto directa**. Los patrones térmicos urbanos (SUHI) están determinados por múltiples factores concurrentes (como el calor antropogénico, el albedo de los materiales, la geometría del cañón urbano, el sombreado y el viento local). Por lo tanto, los resultados se expresan estrictamente en términos de "asociación" y "presión térmica", evitando términos como "efectos" o "causas".
* **Umbral Mínimo de Muestras (Celdas)**: Para garantizar la validez estadística y reducir el ruido en muestras pequeñas, se definieron umbrales mínimos de celdas de 30 m para realizar el cálculo del coeficiente:
  - **Nivel Municipio**:
    * Análisis Global (Tablas 2.1A y 2.1B): Mínimo de 50 celdas ($N \ge 50$).
    * Análisis Segmentado por Densidad (Tablas 2.2 y 2.3): Mínimo de 30 celdas ($N \ge 30$).
  - **Nivel AGEB**:
    * Análisis Global (Tabla 3.1): Mínimo de 30 celdas ($N \ge 30$).
    * Análisis Segmentado por Densidad: Mínimo de 15 celdas ($N \ge 15$).
* **Significado de la Etiqueta N/D (No Disponible)**: La abreviación N/D en las tablas indica que la correlación no pudo definirse o calcularse de forma estable debido a una de dos razones: (a) la cantidad de celdas con datos en el segmento correspondiente fue inferior al umbral mínimo requerido, o (b) la variable independiente carecía de suficiente variabilidad espacial en el área analizada (por ejemplo, valor de densidad industrial constante de cero en todas las celdas del segmento residencial de baja densidad).

---

## 3. Resultados a Nivel de Municipio

### 3.1. Asociación Térmica Global (Local 30m vs Buffer 500m)

#### A. Bloque Asociación Biofísica de Enfriamiento: Vegetación (`green_pct` vs `green_pct_500m`)
Correlaciones globales de Spearman ($r$) entre la SUHI diurna (`suhi_day_c`) y la vegetación.

**Tabla 2.1A: Coeficientes de correlación global de Spearman ($r$) para la vegetación local (30m) y de vecindario (500m) según Municipio.**

| Municipio | Coeficiente Local (30m) | Coeficiente Vecindario (500m) | Celdas de 30m Analizadas |
| :--- | :---: | :---: | :---: |
| San Pedro Garza García | **-0.239** | **-0.247** | 23,217 |
| Guadalupe | **-0.210** | -0.062 | 21,320 |
| San Nicolás de los Garza | -0.088 | -0.098 | 26,009 |
| Monterrey | -0.068 | +0.007 | 107,744 |

#### B. Bloque Asociación Térmica de Calentamiento: Industria (`industrial_osm_pct` vs `industrial_density_500m`)
Correlaciones globales de Spearman ($r$) entre la SUHI diurna (`suhi_day_c`) y la presencia industrial.

**Tabla 2.1B: Coeficientes de correlación global de Spearman ($r$) para la industria local (30m) y de vecindario (500m) según Municipio.**

| Municipio | Coeficiente Local (30m) | Coeficiente Vecindario (500m) | Celdas de 30m Analizadas |
| :--- | :---: | :---: | :---: |
| San Nicolás de los Garza | **+0.409** | **+0.493** | 26,009 |
| Monterrey | +0.121 | +0.149 | 107,744 |
| Guadalupe | +0.001 | -0.177 | 21,320 |
| San Pedro Garza García | -0.006 | +0.013 | 23,217 |

### 3.2. Coeficientes de Vegetación (Mitigación) por Densidad y Escala de Buffer
Comparación de coeficientes de Spearman ($r$) para el bloque de Mitigación (Vegetación) a diferentes escalas de buffer segmentados por la densidad construida de cada municipio.

**Tabla 2.2: Coeficientes de correlación de Spearman ($r$) de la vegetación por zona de densidad construida y escala de buffer.**

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

### 3.3. Coeficientes de la Industria (Presión Térmica) por Densidad y Escala de Buffer
Comparación de coeficientes de Spearman ($r$) para el bloque de Presión Térmica (Industria OSM) a diferentes escalas de buffer segmentados por la densidad construida de cada municipio.

**Tabla 2.3: Coeficientes de correlación de Spearman ($r$) de la industria por zona de densidad construida y escala de buffer.**

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

*Nota: N/D indica que no existió suficiente variabilidad espacial de la variable industrial dentro del subconjunto analizado para calcular una correlación estable (por ejemplo, por no contar con áreas industriales o celdas suficientes).*

---

## 4. Resultados a Nivel de Vecindario (AGEB)

El análisis bottom-up calculó de forma independiente las correlaciones dentro de cada una de las AGEBs del área metropolitana, arrojando luz sobre la heterogeneidad espacial de las variables de mitigación y presión térmica.

### 4.1. Distribución de Coeficientes de Spearman ($r$) en AGEBs
Estadísticos descriptivos de los coeficientes de correlación calculados sobre las celdas internas de cada AGEB.

**Tabla 3.1: Resumen de estadísticos descriptivos para coeficientes de Spearman ($r$) en AGEBs.**

| Indicador Estadístico | Mitigación Local (`green_pct`) | Mitigación Buffer (`green_pct_500m`) | Presión Local (`ind_osm`) | Presión Buffer (`ind_density_500m`) |
| :--- | :---: | :---: | :---: | :---: |
| Promedio de Spearman ($r$) | -0.121 | -0.116 | +0.143 | +0.131 |
| Desviación Estándar | 0.204 | 0.468 | 0.282 | 0.438 |
| Valor Mínimo | -0.791 | -0.991 | -0.536 | -0.850 |
| Valor Máximo | +0.606 | +0.950 | +0.838 | +0.927 |
| total de AGEBs con datos válidos | 380 | 380 | 99 | 217 |

### 4.2. Mapa de Sensibilidad y Exportación Espacial
Los coeficientes de correlación resultantes de este análisis han sido unidos de regreso a las geometrías de las AGEBs en el archivo procesado `data/processed/ageb_correlaciones_sensibilidad.gpkg`.
Las columnas agregadas son:
* **`r_green_global`**: Correlación local global de la celda de 30m.
* **`r_green500_global`**: Correlación a escala de vecindario (500m).
* **`r_ind_global`**: Correlación local global para la presencia industrial.
* **`r_ind500_global`**: Correlación a escala de vecindario (500m) para la densidad industrial.
* **`r_green_alta` / `r_green_media` / `r_green_baja`**: Correlaciones locales de vegetación segmentadas por la densidad interna de la AGEB.

Este Geopackage está listo para ser cargado en QGIS o ArcGIS para la generación de mapas de calor y priorización territorial de infraestructura verde.

---

## 5. Recomendaciones de Intervención Urbana y Política Pública

1. **Gestión de la Presión Térmica Industrial y Amortiguamiento Intermunicipal** (Respaldado por la **Tabla 2.1B** y la **Tabla 2.3**):
   Los resultados de las correlaciones para el bloque de industria (ver **Tabla 2.1B** y **Tabla 2.3**) revelan que existe una asociación positiva significativa entre la presencia industrial y la temperatura superficial (SUHI) en municipios con un perfil industrial consolidado como **San Nicolás de los Garza** (con coeficientes globales de $r = +0.409$ local y $r = +0.493$ a 500m) y zonas específicas de **Monterrey** ($r = +0.121$ local y $r = +0.149$ a 500m). Para mitigar esta asociación positiva (presión térmica industrial), se sugiere priorizar el establecimiento de barreras forestales amortiguadoras en radios de 250 m a 500 m en torno a los polígonos industriales.
   Por otro lado, en el caso de **San Pedro Garza García**, donde el uso de suelo es predominantemente residencial y comercial, la **Tabla 2.3** revela asociaciones positivas notables en buffers amplios ($r = +0.260$ a 500m y $r = +0.579$ a 1000m en zonas de baja densidad; $r = +0.288$ a 500m y $r = +0.565$ a 1000m en zonas de media densidad). Dado que el municipio no alberga zonas industriales de gran escala, este patrón estadístico sugiere un **fenómeno de colindancia o desbordamiento espacial (*spatial spillover*)**, donde la inercia térmica proviene de zonas industriales colindantes externas (como el corredor industrial de Díaz Ordaz en Santa Catarina o límites con Monterrey). Esto indica que la gestión del microclima y de la presión térmica industrial requiere de una planificación y coordinación coordinada a nivel metropolitano, y no de forma aislada por demarcación municipal.

2. **Mitigación Diferenciada en Zonas de Alta Densidad Construida (Materialidad vs. Vegetación)** (Respaldado por la **Tabla 2.2**):
   Al analizar la vegetación segmentada por la densidad construida (ver **Tabla 2.2**), se observa que en las zonas de alta densidad ($\ge 60\%$), la asociación entre la vegetación local y la SUHI disminuye notablemente y tiende a valores cercanos a cero o incluso a asociaciones positivas débiles debido a factores microclimáticos y constructivos (por ejemplo, en Guadalupe el coeficiente local es de $-0.042$ y a 500m es de $+0.114$; en Monterrey es de $-0.026$ local y $+0.063$ a 500m). Estos resultados sugieren que en entornos urbanos consolidados con alta densidad de impermeabilización, la arborización dispersa muestra una asociación estadística no significativa o muy débil con la variación de la temperatura superficial local. Por lo tanto, en lugar de depender únicamente de la reforestación aislada, se recomienda implementar estrategias de mitigación pasiva basadas en la materialidad urbana, tales como el incremento del albedo en techos (techos fríos), fachadas reflejantes y el uso de pavimentos permeables o de alta reflectancia.

3. **Planificación de Infraestructura Verde a Escala de Vecindario** (Respaldado por la **Tabla 2.2**):
   En zonas de densidad residencial baja y media, la vegetación presenta asociaciones negativas importantes con la temperatura superficial. Sin embargo, los coeficientes en la **Tabla 2.2** muestran que estas asociaciones negativas a menudo se intensifican al transitar de la escala local (30 m) a escalas de vecindario (buffers de 250 m y 500 m) (por ejemplo, en Guadalupe Baja la asociación pasa de $-0.278$ local a $-0.645$ a 250m; en Monterrey Baja pasa de $-0.489$ a $-0.611$ a 250m). Esto sugiere que la configuración de la infraestructura verde urbana obtiene una mayor asociación estadística con el enfriamiento cuando se planifica a escala barrial o de vecindario (radios de influencia de 250 m a 500 m) mediante redes interconectadas de parques y corredores arbolados, en lugar de intervenciones puntuales o aisladas en celdas individuales.
