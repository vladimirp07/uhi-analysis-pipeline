# Presentación: Análisis de Correlación Espacial Bottom-Up de la SUHI en Monterrey

---

# 1. Contexto: Isla de Calor Urbana Superficial (SUHI) en Monterrey

*   **Desafío**: La Zona Metropolitana de Monterrey (ZMM) experimenta una intensa presión térmica urbana.
*   **Enfoque de Análisis**: Transición de análisis agregados (Top-Down) a un análisis de grano fino (**Bottom-Up**).
*   **Objetivo**: Evaluar la asociación espacial bivariada entre la temperatura superficial diurna, la vegetación y la presencia industrial a escala micrométrica.
*   **Relevancia**: Informar la toma de decisiones territoriales con base en correlaciones locales de celdas físicas de 30 metros.

---

# 2. Metodología General del Análisis Bottom-Up

*   **Fuentes de Datos y Sensores:** Landsat 8/9 (TIRS diurno, 30m), MODIS Aqua (MYD11A1 nocturno, remuestreado a 30m), Sentinel-2 (NDVI y Cobertura Verde, 10m), Dynamic World (Zonificación de Densidad, 10m), OpenStreetMap (Áreas Industriales vectoriales) y SRTM GL1 (30m) para topografía.
*   **Línea de Base Rural (Control EPA):** Se definieron 3 zonas rurales externas de referencia (altitud similar y $NDVI > 0.4$) para calcular la anomalía térmica: $\text{SUHI} = LST_{\text{urbana}} - LST_{\text{rural\_baseline}}$.
*   **Mallado Territorial (Malla Maestra):** Discretización del territorio de la ZMM en cuadrícula regular con celdas físicas de **30 x 30 metros** (181,746 celdas analizadas).
*   **Análisis Multiescala (Buffers):** Coberturas verde e industrial calculadas localmente y en **buffers circulares concéntricos de 100m, 250m, 500m y 1000m**.
*   **Segmentación por Densidad Construida:** Clasificación en Baja (< 20%), Media (20% - 60%) y Alta ($\ge$ 60% construida).
*   **Correlaciones de Spearman ($r$) y Robustez:** Correlación bivariada no lineal a nivel de celdas agrupadas por Municipio y por AGEB. Robustez mediante filtros de representatividad estadística: $N \ge 30$ celdas (AGEB) y $N \ge 50$ (Municipio).

---

# 3. Variables y Escalas de Análisis Multiescala (Buffers)

*   **Variable Objetivo**: Temperatura superficial diurna (`suhi_day_c`).
*   **Bloque Mitigación**: Porcentaje de vegetación (`green_pct`).
*   **Bloque Presión Industrial**: Presencia industrial (`industrial_osm_pct`) e industrial ponderada por densidad.
*   **Escalas Analizadas**:
    *   *Local*: 30 m de resolución.
    *   *Buffers de Vecindario*: 100 m, 250 m, 500 m y 1000 m (1 km).
*   **Significado de N/D (No Disponible)**: Señala segmentos con variabilidad nula o con cantidad de celdas por debajo del umbral mínimo.

---

# 4. Resultados: Vegetación y Enfriamiento

*   **Asociación Negativa (Enfriamiento)**: A nivel global, una mayor cobertura de vegetación se asocia con temperaturas superficiales más bajas.
*   **Coeficientes de Spearman Globales ($r$)** (Local 30m vs. Vecindario 500m):
    *   **San Pedro Garza García**: $r = -0.239$ (local) / $r = -0.247$ (500m)
    *   **Guadalupe**: $r = -0.210$ (local) / $r = -0.062$ (500m)
    *   **San Nicolás de los Garza**: $r = -0.088$ (local) / $r = -0.098$ (500m)
    *   **Monterrey**: $r = -0.068$ (local) / $r = +0.007$ (500m)
*   **Sensibilidad**: La asociación de enfriamiento es más intensa a escalas de vecindario (250m–500m) en áreas residenciales de densidad baja y media (ej. Guadalupe Baja alcanza $r = -0.645$ a 250m).

---

# 5. Resultados: Presión Térmica Industrial

*   **Asociación Positiva (Calentamiento)**: Mayor presencia industrial se asocia con un incremento de la temperatura superficial diurna.
*   **Coeficientes de Spearman Globales ($r$)** (Local 30m vs. Vecindario 500m):
    *   **San Nicolás de los Garza**: $r = +0.409$ (local) / $r = +0.493$ (500m)
    *   **Monterrey**: $r = +0.121$ (local) / $r = +0.149$ (500m)
    *   **Guadalupe**: $r = +0.001$ (local) / $r = -0.177$ (500m)
    *   **San Pedro Garza García**: $r = -0.006$ (local) / $r = +0.013$ (500m)
*   **San Pedro y Colindancia (Spillover)**: En San Pedro (Baja densidad), la correlación es nula a escala local pero alcanza **$r = +0.579$** a escala de 1000m. Esto sugiere inercia térmica por desbordamiento espacial de zonas industriales colindantes en Santa Catarina y Monterrey.

---

# 6. Asociación Limitada en Áreas Densas (Saturación Construida)

*   **Pérdida de Asociación en Alta Densidad**: En zonas con densidad construida $\ge 60\%$, la correlación vegetación-temperatura se reduce a valores cercanos a cero.
*   **Coeficientes de Vegetación por Densidad** (Local 30m):
    *   *Baja Densidad (< 20%)*: San Pedro ($r = -0.781$), Monterrey ($r = -0.489$), San Nicolás ($r = -0.536$).
    *   *Alta Densidad ($\ge 60\%$)*: San Pedro ($r = -0.116$), Guadalupe ($r = -0.042$), Monterrey ($r = -0.026$).
*   **Significado**: En vecindarios saturados de concreto, la reforestación aislada muestra una asociación estadística muy débil o no significativa con la variación de la temperatura superficial local.

---

# 7. Recomendaciones de Política Pública e Intervenciones Urbanas

*   **Barreras Forestales Industriales** (Tablas 2.1B y 2.3): Implementar buffers forestales de amortiguamiento térmico en radios de 250 m a 500 m en polígonos de San Nicolás y Monterrey.
*   **Planificación Metropolitana del Microclima**: Coordinar buffers forestales intermunicipales debido al efecto de desbordamiento espacial (*spatial spillover*) identificado en San Pedro.
*   **Mitigación Pasiva en Alta Densidad** (Tabla 2.2): En vecindarios altamente impermeabilizados, priorizar cambios de materialidad (aumento de albedo en techos fríos y fachadas reflejantes) sobre arborización dispersa.
*   **Infraestructura Verde Barrial** (Tabla 2.2): Diseñar redes de parques y corredores arbolados barriales enfocando radios de influencia de 250 m a 500 m.

---

# 8. Siguientes Pasos

*   **Alineación Espacial**: Integrar resultados del modelo correlacional con la delimitación de zonas críticas de calor (hotspots).
*   **Geovisualización**: Incorporar la capa enriquecida de AGEBs (`ageb_correlaciones_sensibilidad.gpkg`) en sistemas de información geográfica municipales (QGIS/ArcGIS).
*   **Modelación Multitemporal**: Ampliar el análisis para capturar variaciones estacionales (invierno/verano) y tendencias interanuales.

---

## Notas para conversión futura
Este archivo Markdown (`presentation_outline.md`) ha sido estructurado para facilitar su posterior conversión automatizada a formato PowerPoint (.pptx).
Para realizar la conversión utilizando **Pandoc**, ejecute el siguiente comando en su terminal:

```bash
pandoc presentation_outline.md -o presentacion_correlacion.pptx
```

Si dispone de una plantilla personalizada de PowerPoint (`plantilla.pptx`) para aplicar estilos específicos, tipografías y paletas de colores institucionales, utilice el siguiente comando:

```bash
pandoc presentation_outline.md -o presentacion_correlacion.pptx --reference-doc=plantilla.pptx
```
