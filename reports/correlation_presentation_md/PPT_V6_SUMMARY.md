# Resumen de Diapositivas y Cambios: Presentación Final v6
**Islas de Calor en la Zona Metropolitana de Monterrey**

Este documento detalla la estructura final de diapositivas, las figuras insertadas y los cambios principales aplicados en la versión final de la presentación (`reports/correlation_presentation_md/presentacion_islas_calor_zmm_v6.pptx`).

---

## 1. Cambios Principales en esta Fase

1.  **Título de Portada Simplificado:** Se modificó la portada para mostrar el título directo solicitado: `Islas de Calor en la Zona Metropolitana de Monterrey`. Los detalles del análisis bottom-up se discuten de forma secundaria a lo largo de las diapositivas metodológicas.
2.  **Tabla Editable de Fuentes en PPT (Nativa):** La diapositiva *Datos y Fuentes Espaciales* (Slide 3) fue implementada como una **tabla nativa y editable** dentro de PowerPoint (usando celdas con colores alternados y fuentes Arial legibles). Ya no se utiliza una imagen estática para esta sección.
3.  **Nueva Slide de Procesamiento Térmico (Obtención de SUHI):** Se incorporó la **Slide 4** para detallar la procedencia de la capa térmica (Landsat 8 TIRS B10, spring diurna 2026), su reducción mediante mediana multitemporal con máscara de nubes/sombras (QA_PIXEL), y la calibración matemática a grados Celsius restándole el control de referencia rural periférico.
4.  **Uso de la Capa de SUHI sobre Valle Oriente:** La **Slide 7** (*Propuesta Bottom-Up*) ahora muestra la malla de celdas de 30m sobre el hotspot real de Valle Oriente cargando la capa de **SUHI** (`suhi_day_c` en lugar de la LST absoluta), con una paleta cálida `YlOrRd` (amarillo-rojo) y bordes negros muy ligeros sobre la foto satelital de fondo (`15_hotspot_valle_oriente_celda_30m_suhi.png`).
5.  **Gráficos de Decaimiento a Escala de Vecindario (500m):** Se actualizaron las curvas de decaimiento por densidad (**Slide 16**) para usar las variables a **escala vecindario de 500 metros** (`green_pct_500m` e `industrial_density_500m`), que provee mayor relevancia barrial y de políticas públicas que las variables locales aisladas.
6.  **Slide de Municipios del Estudio:** Se añadió la **Slide 10** dedicada a justificar por qué se separa el análisis por municipio (e.g. San Nicolás es industrial y San Pedro comercial/residencial), incorporando el mapa disuelto y etiquetado a partir de la base del pipeline (`18_mapa_municipios_zmm.png`).
7.  **Inclusión de los Hotspots como Meta del Proyecto:** La **Slide 5** detalla la identificación de hotspots (islas de calor) como un objetivo central de la investigación, utilizando el mapa de hotspots general metropolitano de base (`01_hotspots_zmm.png`).

---

## 2. Estructura Diapositiva por Diapositiva (19 Slides)

| Slide # | Título de la Diapositiva | Figura / Elemento Insertado | Notas de Diseño y Narrativa |
| :---: | :--- | :--- | :--- |
| **1** | Portada | *Ninguno* (Layout Portada) | Título simplificado: *Islas de Calor en la Zona Metropolitana de Monterrey*. |
| **2** | Motivación: Impacto Real del Calor Urbano | *Ninguno* (Texto Completo) | Describe los impactos en consumo eléctrico, confort, salud, calidad ambiental y desigualdad territorial. |
| **3** | Datos y Fuentes Espaciales del Análisis | **Tabla Editable Nativa** | Organiza sensores, información técnica y uso. Incluye Landsat 8, Sentinel-2, Dynamic World, OSM e INEGI. |
| **4** | Procesamiento Térmico: Obtención de la Capa SUHI | *Ninguno* (Texto Completo) | Explica el compuesto mediana, máscara QA_PIXEL, calibración a °C y la resta de la temperatura rural de referencia. |
| **5** | Identificación de Hotspots en la ZMM | `01_hotspots_zmm.png` | Ubicación espacial del calor térmico metropolitano. Hotspots definidos como meta del proyecto. |
| **6** | Objetivos del Análisis de Correlación | *Ninguno* (Texto Completo) | Objetivo general y específicos (óptimo de escala, efecto de densidad construida y spillover). |
| **7** | Propuesta: Enfoque Bottom-Up (Celda de 30m) | `15_hotspot_valle_oriente_celda_30m_suhi.png` | Cuadrícula de 30m con borde negro sobre satélite de Valle Oriente. Coloreado por SUHI con paleta cálida (YlOrRd). |
| **8** | Metodología General de Análisis | `05_metodologia_diagrama.png` | Diagrama de flujo vertical simplificado en 6 pasos, reemplazando texto repetitivo. |
| **9** | Capas Principales de Información | `04_capas_base_analisis.png` | Panel triple horizontal mostrando LST/SUHI, `green_pct` (Sentinel-2) e `industrial_osm_pct` (OSM). |
| **10** | ¿Por qué analizar a escala de Municipio? | `18_mapa_municipios_zmm.png` | Mapa de los 4 municipios disueltos con colores pasteles sobre base CartoDB Positron. |
| **11** | ¿Por qué clasificar por Densidad Construida? | `06_mapa_densidad_baja_media_alta.png` | Mapa metropolitano clasificado en 3 niveles de impermeabilización (<20%, 20-60%, >=60%). Justifica la segmentación física. |
| **12** | Resultados: Vegetación y Atenuación Térmica | `13_heatmap_spearman_vegetacion_v3.png` | Matriz de $2 \times 2$ con heatmap de vegetación. Óptimo barrial y pérdida de enfriamiento en alta densidad. |
| **13** | Resultados: Curvas Escalares de la Vegetación | `08_vegetacion_buffers_baja.png` | Gráfico de líneas multivariable de vegetación por buffer en baja densidad para los 4 municipios. |
| **14** | Resultados: Presión Térmica Industrial | `14_heatmap_spearman_industria_v2.png` | Matriz de $2 \times 2$ con heatmap de industria. Valores positivos asociados a calentamiento y celdas `"N/D"`. |
| **15** | Resultados: Curvas Escalares de la Industria | `09_industria_buffers.png` | Gráfico de líneas multivariable de industria, mostrando la presión térmica e inercia regional (spillover) de San Pedro. |
| **16** | Decaimiento de Asociación a 500m por Densidad | `16_decaimiento_cobertura_verde_500m.png` y `17_decaimiento_industria_500m.png` | Curvas de transición y decaimiento por densidad para vegetación e industria a escala de vecindario (500m). |
| **17** | Saturación Térmica en Alta Densidad | `12_baja_vs_alta_vegetacion.png` | Gráfico de barras agrupadas comparativo de vegetación local en baja vs alta densidad para lectura directa. |
| **18** | Implicaciones para la Planificación Urbana | *Ninguno* (Texto Completo) | Recomendaciones: buffers de 250-500m, reforestación barrial coordinada y albedo/materiales en alta densidad. |
| **19** | Siguientes Pasos y Líneas de Investigación | *Ninguno* (Texto Completo) | Propuestas futuras: integración espacial con hotspots, modelación estacional y nocturna, y uso SIG de AGEBs. |

---

## 3. Notas de Diseño y Narrativa

*   **Tono Científico y Objetivo:** Se evitó cualquier tipo de lenguaje exagerado (como "urgente", "demuestra definitivamente", "dominancia total"). Toda la redacción está enmarcada en términos estadísticos rigurosos y relaciones monotónicas ("se observa", "sugiere", "asociación", "patrón espacial", "no implica causalidad").
*   **Composición Visual Simétrica:** Las diapositivas con figuras combinan un bloque de texto a la izquierda con negritas estilizadas y la figura correspondiente a la derecha de forma proporcional, manteniendo la consistencia de escalas y colores para una comparabilidad directa en la defensa.
