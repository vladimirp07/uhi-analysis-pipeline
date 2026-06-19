# Catálogo de Figuras: Análisis de Correlación Espacial Bottom-Up (Monterrey 2026)

Este documento es el catálogo oficial de la biblioteca de figuras generadas para la futura presentación (v6) del análisis de correlación espacial bottom-up entre la Isla de Calor Urbana Superficial (SUHI), la vegetación (`green_pct`) y la industria (`industrial_osm_pct`) en la Zona Metropolitana de Monterrey (ZMM). 

Todas las figuras están guardadas en la carpeta:
`reports/correlation_presentation_md/figures/`

Las figuras han sido generadas mediante el script:
`src/visualization/generate_correlation_ppt_figures.py`

---

## Índice del Catálogo

### A. Contexto del Problema
1. [01_hotspots_zmm.png](#1-01_hotspots_zmmpng---contexto-de-hotspots-en-la-zmm)
2. [02_hotspot_zoom_celda_30m.png](#2-02_hotspot_zoom_celda_30mpng---resolución-de-celda-30m)

### B. Fuentes y Capas Base
3. [03_fuentes_datos_table.png](#3-03_fuentes_datos_tablepng---tabla-de-fuentes-de-datos)
4. [04_capas_base_analisis.png](#4-04_capas_base_analisispng---visualización-de-las-3-capas-base)

### C. Metodología y Segmentación
5. [05_metodologia_diagrama.png](#5-05_metodologia_diagramapng---diagrama-de-flujo-metodológico)
6. [06_mapa_densidad_baja_media_alta.png](#6-06_mapa_densidad_baja_media_altapng---mapa-de-zonificación-de-densidades)

### D. Resultados Principales
7. [07_heatmap_spearman_vegetacion.png](#7-07_heatmap_spearman_vegetacionpng---matriz-completa-de-mitigación)
8. [08_vegetacion_buffers_baja.png](#8-08_vegetacion_buffers_bajapng---curvas-de-mitigación-en-baja-densidad)
9. [09_industria_buffers.png](#9-09_industria_bufferspng---curvas-de-presión-térmica-industrial)
10. [10_decaimiento_vegetacion_densidad.png](#10-10_decaimiento_vegetacion_densidadpng---decaimiento-del-enfriamiento)
11. [11_decaimiento_industria_densidad.png](#11-11_decaimiento_industria_densidadpng---transición-térmica-industrial)
12. [12_baja_vs_alta_vegetacion.png](#12-12_baja_vs_alta_vegetacionpng---contraste-baja-vs-alta-densidad)

---

## Detalles Técnicos de las Figuras

### 1. `01_hotspots_zmm.png` - Contexto de Hotspots en la ZMM
* **Ruta de Archivo:** `reports/correlation_presentation_md/figures/01_hotspots_zmm.png`
* **Tipo de Gráfico:** Mapa espacial metropolitano (Reutilización).
* **Descripción Técnica:** Muestra la delimitación física de los núcleos críticos de calor superficial (hotspots térmicos) sobre la mancha urbana de la ZMM, identificados a partir del análisis espacial de autocorrelación local (Getis-Ord Gi*).
* **Propósito en la PPT:** Contextualizar el problema físico temprano en la presentación (Slide 3, después de Motivación), aclarando visualmente que los hotspots se muestran aquí como contexto espacial histórico y no como resultado directo de las correlaciones bottom-up.

### 2. `02_hotspot_zoom_celda_30m.png` - Resolución de Celda 30m
* **Ruta de Archivo:** `reports/correlation_presentation_md/figures/02_hotspot_zoom_celda_30m.png`
* **Tipo de Gráfico:** Crop de malla fina vectorial con anotación visual (Generado de datos reales).
* **Descripción Técnica:** Visualización ampliada de la cuadrícula de 30m en una sección industrial de San Nicolás de los Garza. Las celdas están coloreadas según su LST diurna y bordeadas individualmente. Incluye una anotación visual que destaca el tamaño físico de la celda de análisis ($30\text{ m} \times 30\text{ m} = 900\text{ m}^2$) y una nota con el total de celdas analizadas en la ZMM (181,746).
* **Propósito en la PPT:** Apoyar la slide de Propuesta (Slide 5) para mostrar pedagógicamente qué es una celda de 30m y contrastar la riqueza del enfoque "celda por celda" frente a los análisis tradicionales basados en promedios municipales globales.

### 3. `03_fuentes_datos_table.png` - Tabla de Fuentes de Datos
* **Ruta de Archivo:** `reports/correlation_presentation_md/figures/03_fuentes_datos_table.png`
* **Tipo de Gráfico:** Tabla visual estilizada en alta definición (Generado).
* **Descripción Técnica:** Tabla estructurada con columnas *Sensor / Fuente*, *Información Técnica* y *Uso dentro del Análisis*. Detalla la procedencia de la capa térmica (Landsat 8 TIRS, spring diurna median composite), de la vegetación (Sentinel-2 MSI NDVI), la zonificación (Dynamic World built fraction), la industria (OSM) y la población (INEGI Censo 2020).
* **Propósito en la PPT:** Reemplazar la slide de texto débil de fuentes de datos (Slide 7) por un cuadro ordenado e informativo, con colores corporativos del congreso.

### 4. `04_capas_base_analisis.png` - Visualización de las 3 Capas Base
* **Ruta de Archivo:** `reports/correlation_presentation_md/figures/04_capas_base_analisis.png`
* **Tipo de Gráfico:** Figura espacial de 3 paneles paralelos (Generado de datos reales).
* **Descripción Técnica:** Composición espacial de un sector de la ZMM (Monterrey-San Nicolás) mostrando en paralelo: (1) la anomalía térmica SUHI diurna en grados Celsius, (2) el porcentaje de vegetación real (`green_pct` derivado de Sentinel-2), y (3) el porcentaje de presencia industrial (`industrial_osm_pct` derivado de OSM).
* **Propósito en la PPT:** Servir en la slide de Capas Principales (Slide 8) para que el espectador entienda visualmente la información espacial de entrada que se cruza estadísticamente.

### 5. `05_metodologia_diagrama.png` - Diagrama de Flujo Metodológico
* **Ruta de Archivo:** `reports/correlation_presentation_md/figures/05_metodologia_diagrama.png`
* **Tipo de Gráfico:** Diagrama de flujo vertical estilizado (Generado).
* **Descripción Técnica:** Esquematiza los 6 pasos del pipeline metodológico: (1) Discretización en celdas de 30m, (2) Spatial Join de agregación territorial, (3) Cálculo de variables focales multiescala (buffers radiales de 100m, 250m, 500m y 1000m), (4) Medición bivariada con Spearman ($r$), (5) Segmentación por Municipio y Densidad, y (6) Generación de Síntesis y Mapas de Sensibilidad.
* **Propósito en la PPT:** Reemplazar la metodología textual por un diagrama comprensible de un solo vistazo (Slide 9).

### 6. `06_mapa_densidad_baja_media_alta.png` - Mapa de Zonificación de Densidades
* **Ruta de Archivo:** `reports/correlation_presentation_md/figures/06_mapa_densidad_baja_media_alta.png`
* **Tipo de Gráfico:** Mapa espacial metropolitano clasificado (Reutilización).
* **Descripción Técnica:** Representa la clasificación espacial de la ZMM en tres clases según la fracción de suelo impermeable (`dw_built_pct` de Dynamic World): Baja densidad (< 20%), Media densidad (20-60%) y Alta densidad (>= 60%).
* **Propósito en la PPT:** Insertar en la slide de zonificación de densidad (Slide 11) para argumentar por qué importa separar el análisis en estas tres zonas ("el comportamiento térmico no es el mismo en zonas abiertas que en áreas densas").

### 7. `07_heatmap_spearman_vegetacion.png` - Matriz Completa de Mitigación
* **Ruta de Archivo:** `reports/correlation_presentation_md/figures/07_heatmap_spearman_vegetacion.png`
* **Tipo de Gráfico:** Heatmap/Matriz de correlación anotada (Generado).
* **Descripción Técnica:** Matriz de $12 \times 5$ que cruza los 4 municipios en sus 3 niveles de densidad (filas) con las 5 escalas de buffer analizadas (columnas) para la variable de vegetación. Utiliza la paleta divergente reversa `RdYlGn_r` (donde la atenuación o enfriamiento más fuerte aparece en verde intenso y la pérdida de asociación en rojo/amarillo).
* **Propósito en la PPT:** Centralizar en la Slide de Resultados de Vegetación (Slide 12) la visión completa del comportamiento de la mitigación térmica, mostrando patrones claros de escala y saturación.

### 8. `08_vegetacion_buffers_baja.png` - Curvas de Mitigación en Baja Densidad
* **Ruta de Archivo:** `reports/correlation_presentation_md/figures/08_vegetacion_buffers_baja.png`
* **Tipo de Gráfico:** Gráfico de líneas multivariable (Generado).
* **Descripción Técnica:** Muestra el comportamiento del coeficiente de correlación de Spearman ($r$) para la vegetación en zonas de baja densidad a medida que se amplía el radio del buffer de análisis (desde 30m locales hasta 1000m). Compara las curvas de los 4 municipios (San Pedro, Guadalupe, San Nicolás y Monterrey).
* **Propósito en la PPT:** Ilustrar el cambio escalar de la vegetación (Slide 12 o Slide 14 de decaimiento), demostrando que la mayor asociación de enfriamiento ocurre en escalas vecinales (250m - 500m) en municipios como Guadalupe y San Nicolás.

### 9. `09_industria_buffers.png` - Curvas de Presión Térmica Industrial
* **Ruta de Archivo:** `reports/correlation_presentation_md/figures/09_industria_buffers.png`
* **Tipo de Gráfico:** Gráfico de líneas multivariable (Generado).
* **Descripción Técnica:** Muestra la correlación de la industria en diferentes buffers para casos críticos de estudio: San Nicolás en Baja y Alta densidad, Monterrey en Baja y Media densidad, y San Pedro en Baja densidad (donde se observa el fenómeno de colindancia intermunicipal o *spillover*).
* **Propósito en la PPT:** Respaldar los hallazgos del bloque de calentamiento/presión térmica industrial (Slide 13), mostrando la inercia térmica a buffers grandes.

### 10. `10_decaimiento_vegetacion_densidad.png` - Decaimiento del Enfriamiento
* **Ruta de Archivo:** `reports/correlation_presentation_md/figures/10_decaimiento_vegetacion_densidad.png`
* **Tipo de Gráfico:** Gráfico de líneas multivariable con anotaciones de datos (Generado).
* **Descripción Técnica:** Grafica cómo el coeficiente local de vegetación (30m) transita de valores fuertemente negativos en Baja densidad (ej. $-0.781$ en San Pedro, $-0.489$ en Monterrey) hacia valores casi nulos en Alta densidad (ej. $-0.116$ en San Pedro, $-0.026$ en Monterrey).
* **Propósito en la PPT:** Demostrar visualmente el fenómeno de saturación construida en entornos urbanos consolidados (Slide 14).

### 11. `11_decaimiento_industria_densidad.png` - Transición Térmica Industrial
* **Ruta de Archivo:** `reports/correlation_presentation_md/figures/11_decaimiento_industria_densidad.png`
* **Tipo de Gráfico:** Gráfico de líneas multivariable con anotaciones de datos (Generado).
* **Descripción Técnica:** Grafica la correlación de la industria a escala de vecindario (500m) para los 4 municipios a través de las tres clases de densidad construida (Baja, Media, Alta). Muestra la estabilidad de la presión térmica industrial en San Nicolás y el desvanecimiento del spillover en San Pedro a alta densidad.
* **Propósito en la PPT:** Explicar el comportamiento de la inercia industrial y su interacción con el entorno edificado general (Slide 13 o Slide 14).

### 12. `12_baja_vs_alta_vegetacion.png` - Contraste Baja vs Alta Densidad
* **Ruta de Archivo:** `reports/correlation_presentation_md/figures/12_baja_vs_alta_vegetacion.png`
* **Tipo de Gráfico:** Gráfico de barras agrupadas con etiquetas de datos (Generado).
* **Descripción Técnica:** Gráfico de barras yuxtapuestas que compara directamente los coeficientes de vegetación local (30m) para cada uno de los 4 municipios en Baja vs. Alta densidad, etiquetando con precisión los valores numéricos de Spearman para resaltar la brecha térmica.
* **Propósito en la PPT:** Apoyar la explicación de la saturación térmica (Slide 15), ofreciendo una visualización muy rápida y directa de digerir.
