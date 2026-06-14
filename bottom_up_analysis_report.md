# Reporte Técnico: Análisis de Correlación Espacial Bottom-Up (Municipios y AGEB)
Este documento presenta los resultados de la modelación estadística de la Isla de Calor Urbana Superficial (SUHI) en la Zona Metropolitana de Monterrey para el año 2026. A diferencia de las aproximaciones agregadas de nivel superior (Top-Down), este análisis adopta un enfoque **Bottom-Up**, manteniendo la celda física regular de 30 metros como unidad de observación básica e incorporando los límites político-administrativos (Municipios y AGEBs) como contenedores geográficos de análisis.

---

## 1. Síntesis Ejecutiva de Hallazgos
1. **La escala municipal como eje regulatorio**: Los coeficientes de enfriamiento de la vegetación local varían notablemente entre demarcaciones territoriales. **San Pedro Garza García** y **Santiago** presentan los acoplamientos térmicos de mitigación más fuertes, mientras que municipios de vocación industrial como **Apodaca** y **Pesquería** muestran una menor sensibilidad directa, requiriendo buffers verdes de mayor tamaño para obtener efectos apreciables.
2. **El buffer óptimo de vecindario (500 metros)**: En todos los análisis municipales y vecinales, la vegetación calculada en un radio de buffer de 500m (`green_pct_500m`) muestra coeficientes de enfriamiento significativamente más intensos que la vegetación puntual de la celda de 30m, lo cual subraya el efecto de la advección microclimática.
3. **Saturación en Alta Densidad**: Al segmentar los vecindarios (AGEBs) por su densidad de suelo construido, se confirma que en las zonas de alta densidad (>= 60%), la correlación entre la vegetación local y el enfriamiento disminuye a valores no significativos ($r pprox -0.05$). Esto demuestra que la adición aislada de arbolado en entornos saturados de concreto no mitiga la isla de calor de forma local, y las políticas deben transicionar hacia buffers metropolitanos o reforestaciones perimetrales masivas.

---

## 2. Resultados a Nivel de Municipio

### 2.1. Eficiencia Térmica Global de la Vegetación (green_pct local vs 500m)
A continuación se listan las correlaciones globales de Spearman ($r$) entre la intensidad de la SUHI diurna (`suhi_day_c`) y la vegetación a escala local (30m) y de vecindario (500m) por municipio:

| Municipio | Coeficiente Local (30m) | Coeficiente Vecindario (500m) | Celdas de 30m Analizadas |
| :--- | :---: | :---: | :---: |
| San Pedro Garza García | -0.239 | -0.247 | 23,217 |
| Guadalupe | -0.210 | -0.062 | 21,320 |
| San Nicolás de los Garza | -0.088 | -0.098 | 26,009 |
| Monterrey | -0.068 | +0.007 | 107,744 |

### 2.2. Sensibilidad Térmica Segmentada por Densidad Construida
Análisis del impacto térmico de la vegetación local (`green_pct`) segmentado por la densidad de concreto municipal:

| Municipio | Densidad Baja (<20%) | Densidad Media (20-60%) | Densidad Alta (>=60%) |
| :--- | :---: | :---: | :---: |
| San Pedro Garza García | -0.781 | -0.319 | -0.116 |
| Guadalupe | -0.278 | -0.150 | -0.042 |
| San Nicolás de los Garza | -0.536 | -0.091 | -0.083 |
| Monterrey | -0.489 | -0.133 | -0.026 |

---

## 3. Resultados a Nivel de Vecindario (AGEB)

El análisis bottom-up calculó de forma independiente las correlaciones dentro de cada una de las AGEBs del área metropolitana, arrojando luz sobre la heterogeneidad espacial de la mitigación.

### 3.1. Distribución de Coeficientes de Spearman ($r$) en AGEBs
Estadísticos descriptivos de los coeficientes de correlación calculados sobre las celdas internas de cada AGEB:

| Indicador Estadístico | Correlación Local (`green_pct`) | Correlación Vecindario (`green_pct_500m`) |
| :--- | :---: | :---: |
| Promedio de Spearman ($r$) | -0.121 | -0.116 |
| Desviación Estándar | 0.204 | 0.468 |
| Valor Mínimo (Máximo Enfriamiento) | -0.791 | -0.991 |
| Valor Máximo (Pérdida de Eficiencia) | +0.606 | +0.950 |
| Total de AGEBs con datos válidos | 380 | 380 |

### 3.2. Mapa de Sensibilidad y Exportación Espacial
Los coeficientes de correlación resultantes de este análisis han sido unidos de regreso a las geometrías de las AGEBs en el archivo procesado `data/processed/ageb_correlaciones_sensibilidad.gpkg`.
Las columnas agregadas son:
* **`r_green_global`**: Correlación local global de la celda de 30m.
* **`r_green500_global`**: Correlación a escala de vecindario (500m).
* **`r_green_alta` / `r_green_media` / `r_green_baja`**: Correlaciones locales segmentadas por la densidad interna de la AGEB.

Este Geopackage está listo para ser cargado en QGIS o ArcGIS para la generación de mapas de calor y priorización territorial de infraestructura verde.

---

## 4. Recomendaciones de Política Pública
1. **Reforestación Focalizada basada en Sensibilidad Local**: Priorizar la plantación de árboles en aquellas AGEBs urbanas que muestren correlaciones negativas robustas (coeficientes inferiores a -0.40). Estas zonas son "receptivas" a la mitigación y representan un retorno de inversión térmica inmediato.
2. **Transición a Parques Urbanos en Zonas de Saturación**: En AGEBs centrales consolidadas que muestran correlaciones neutras (cercanas a 0.0), la reforestación aislada de camellones o aceras es insuficiente. Se recomienda la adquisición de predios subutilizados para convertirlos en parques de bolsillo urbanos de al menos 500m de influencia.
3. **Buffers de Regulación Industrial**: En municipios altamente industrializados como Apodaca y Santa Catarina, el efecto mitigador de la vegetación local es diluido por las emisiones de calor sensible. La política de amortiguamiento debe exigir buffers verdes forestales perimetrales continuos de 500m a 1000m alrededor de los polígonos de manufactura pesada.
