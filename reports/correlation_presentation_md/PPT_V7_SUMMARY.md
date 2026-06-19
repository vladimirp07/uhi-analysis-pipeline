# Resumen de Diapositivas y Cambios: Presentación v7
**Islas de Calor en la Zona Metropolitana de Monterrey**

Este documento detalla la reestructuración de la presentación (`reports/correlation_presentation_md/presentacion_islas_calor_zmm_v7.pptx`) para cambiar su filosofía y narrativa general. La versión 7 ya no se presenta como un estudio de correlación final y definitivo, sino como un proyecto de investigación amplio sobre islas de calor en la ZMM, en el cual el análisis espacial bottom-up actual funciona como un **primer avance / baseline exploratorio**.

---

## 1. Cambios de Filosofía, Narrativa y Estructura (v6 vs. v7)

1. **Enfoque de Proyecto Amplio:** La investigación se reorienta desde la portada para enmarcarse como un esfuerzo multitemporal y multidisciplinario de largo plazo. El análisis de variables físicas (vegetación e industria) se establece claramente como la primera etapa (baseline físico).
2. **Inclusión de Objetivos de Proyecto Completo:** Se añadieron dos diapositivas consecutivas:
   * **Objetivo General del Proyecto (Slide 4):** Define la meta a largo plazo de evaluar relaciones físicas, urbanas, ambientales y socioeconómicas para inferir estrategias localizadas.
   * **Objetivos Específicos (Slide 5):** Estructura un plan de trabajo de 5 puntos (delimitación física, dinámica espacial/temporal, evaluación de variables urbanas, integración socioeconómica y base metodológica de mitigación).
3. **Slide Clara de Alcance (Slide 6):** Se incorporó una diapositiva titulada `Alcance de este Primer Avance` que acota el estudio actual a SUHI diurna de primavera 2026, municipios piloto, variables iniciales (vegetación e industria) y correlaciones bivariadas bottom-up. Aclara explícitamente que este avance funciona como baseline metodológico y no representa el modelo final del proyecto.
4. **Mapeo de Futuras Variables (Slide 16):** La slide `Qué Falta Integrar` detalla de forma explícita las variables socioeconómicas (vulnerabilidad, censos), morfológicas (cañón urbano, SRTM), atmosféricas (viento, humedad) y temporales (nocturnas y estacionales) que se acoplarán al baseline físico.
5. **Reorganización y Sub-diapositivas para Legibilidad:** Para mantener el diseño limpio sin saturar de texto ni tapar figuras, se mantuvieron y reorganizaron las "figuras buenas" de la versión 6 dividiéndolas en diapositivas complementarias (a y b):
   * **Propuesta Bottom-Up (Slide 10)** y **Flujo Metodológico (Slide 10b)**.
   * **Resultados de Vegetación (Slide 13a)** y **Comportamiento Escalar Vegetal (Slide 13b)**.
   * **Resultados de Industria (Slide 14a)** y **Comportamiento Escalar Industrial (Slide 14b)**.
   * **Saturación a 500m (Slide 15a)** y **Contraste de Mitigación Baja vs. Alta (Slide 15b)**.
6. **Refuerzo del Tono Objetivo y Sobrio:** Se eliminaron términos exagerados o causales. Toda la redacción utiliza expresiones precisas y académicas: *"primer avance"*, *"baseline exploratorio"*, *"se observa"*, *"sugiere"*, *"asociación"*, *"no implica causalidad"*.

---

## 2. Estructura Diapositiva por Diapositiva (22 Slides)

| Slide # | Título de la Diapositiva | Figura / Elemento Insertado | Notas de Diseño y Narrativa |
| :---: | :--- | :--- | :--- |
| **1** | Portada | *Ninguno* (Layout Portada) | Título principal: *Islas de Calor en la Zona Metropolitana de Monterrey*. Subtítulo que enmarca el proyecto y el primer avance. |
| **2** | Motivación: Impacto Real del Calor Urbano | *Ninguno* (Texto Completo) | Contextualiza la urgencia del calor urbano (energía, salud, ecosistemas, desigualdad territorial) con tono sobrio. |
| **3** | Contexto Espacial: Hotspots Térmicos en la ZMM | `01_hotspots_zmm.png` | Mapa metropolitano de hotspots. Sirve de marco geográfico inicial del problema físico. |
| **4** | Objetivo General del Proyecto | *Ninguno* (Texto Completo) | Plantea el objetivo global integrador del proyecto a largo plazo. |
| **5** | Objetivos Específicos del Proyecto | *Ninguno* (Texto Completo) | Lista numerada de las 5 metas de investigación del proyecto completo. |
| **6** | Alcance de este Primer Avance | *Ninguno* (Texto Completo) | Acota temporalidad, geografía, variables y método del baseline. Aclara límites del avance. |
| **7** | Datos y Fuentes Espaciales | **Tabla Editable Nativa** | Información técnica y uso de los sensores y bases de datos empleados (Landsat 8, Sentinel-2, Dynamic World, OSM, INEGI). |
| **8** | Construcción de SUHI e Identificación de Hotspots | *Ninguno* (Texto Completo) | Detalla el procesamiento térmico (compuestos mediana, QA_PIXEL, calibración USGS, y resta de control rural). |
| **9** | Capas Principales de Información | `04_capas_base_analisis.png` | Visualización en triple panel horizontal de las variables de entrada: SUHI diurna, cobertura vegetal e industria. |
| **10** | Propuesta Metodológica: Enfoque Bottom-Up (Celda 30m) | `15_hotspot_valle_oriente_celda_30m_suhi.png` | Justifica el modelado a nivel de celda de 30m. Muestra el hotspot de Valle Oriente con la malla regular y SUHI diurna. |
| **10b** | Flujo de Trabajo del Pipeline Metodológico | `05_metodologia_diagrama.png` | Diagrama de flujo vertical que ilustra de forma clara los 6 pasos del pipeline estadístico. |
| **11** | ¿Por qué segmentar por Municipio y Densidad? | `18_mapa_municipios_zmm.png` y `06_mapa_densidad_baja_media_alta.png` | Argumenta la necesidad de subdividir por límites políticos y niveles de impermeabilización. Muestra ambos mapas lado a lado. |
| **12** | Baseline Actual: Cobertura de Vegetación e Industria | *Ninguno* (Texto Completo) | Introduce conceptualmente el cruce bivariado inicial (enfriamiento vs. presión de inercia térmica). |
| **13a** | Resultados Iniciales: Cobertura de Vegetación | `13_heatmap_spearman_vegetacion_v3.png` | Matriz de heatmaps dividida en 4 municipios. Enfatiza la asociación negativa (RdYlGn_r) y la pérdida local en zonas densas. |
| **13b** | Comportamiento Escalar de la Cobertura Vegetal | `08_vegetacion_buffers_baja.png` | Curvas de coeficientes de Spearman por radio de buffer. Muestra que el enfriamiento óptimo ocurre a escalas de vecindario. |
| **14a** | Resultados Iniciales: Ocupación Industrial | `14_heatmap_spearman_industria_v2.png` | Matriz de heatmaps de industria. Resalta la asociación positiva constante en San Nicolás y celdas "N/D". |
| **14b** | Comportamiento Escalar de la Presión Industrial | `09_industria_buffers.png` | Curvas de correlación de industria, evidenciando el fenómeno de inercia térmica regional y colindancia (spillover) en San Pedro. |
| **15a** | Saturación Térmica: Decaimiento por Densidad a 500m | `16_decaimiento_cobertura_verde_500m.png` y `17_decaimiento_industria_500m.png` | Muestra lado a lado la transición por densidad a escala de 500m para ambas variables físicas. |
| **15b** | Contraste de Mitigación en Baja vs. Alta Densidad | `12_baja_vs_alta_vegetacion.png` | Gráfico de barras agrupadas comparativo de vegetación a 30m local. Resalta de un vistazo la saturación del enfriamiento. |
| **16** | Próximos Pasos: Qué Falta Integrar | *Ninguno* (Texto Completo) | Describe las futuras variables socioeconómicas, topográficas, atmosféricas y nocturnas/estacionales. |
| **17** | Implicaciones para la Planificación Urbana | *Ninguno* (Texto Completo) | Traduce las asociaciones detectadas en propuestas espaciales (franjas buffer de 250-500m, redes forestales vecinales, techos fríos). |
| **18** | Siguientes Pasos de Trabajo | *Ninguno* (Texto Completo) | Líneas inmediatas: acoplamiento con hotspots de riesgo, uso SIG del geopackage por AGEB y modelación de vulnerabilidad. |

---

## 3. Limitaciones y Decisiones de Diseño Importantes

* **Independencia de Figuras y Texto:** Ninguna imagen interfiere con los cuadros de texto. Las imágenes side-by-side se posicionan de manera estricta en el bloque derecho (`Inches(6.4)` o `Inches(6.5)`) y las cajas de texto en el izquierdo (`Inches(0.6)` con un ancho acotado de `Inches(5.6)`), lo que evita empalmes.
* **Separación de Gráficos Complejos:** La separación de las matrices de correlación (heatmaps) de sus respectivas curvas escalares (line plots) evita la fatiga visual del espectador y permite al ponente explicar primero el patrón macro (municipio-densidad) y posteriormente el micro (escala de influencia focal).
* **Mantenimiento de la Estética Corporativa:** Se conserva la tipografía limpia (Arial), tamaños de fuente contrastantes (Títulos 32-36pt, cuerpo 12.5pt, sub-bullets 11pt) y la paleta de colores institucional del congreso (fondos blancos, encabezados de tablas en Navy azul `#1F3864`, y alternancia `#F2F4F8`).
* **Tabla de Datos Nativa:** Se mantuvo la tabla de fuentes de datos como un objeto nativo y editable de PowerPoint. Esto facilita correcciones directas de texto dentro de la presentación si el equipo lo requiere, sin tener que regenerar imágenes externas.
