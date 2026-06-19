# Resumen de Resultados Analíticos del Proyecto SUHI Monterrey (Versión Oficial Depurada)

Este documento presenta una síntesis estructurada de los resultados del proyecto de análisis de la Isla de Calor Urbana Superficial (SUHI) diurna y nocturna en la Zona Metropolitana de Monterrey (ZMM). La estructura de este resumen sigue el orden y flujo de las fases de procesamiento y modelación del pipeline metodológico implementado para facilitar su consulta y comprensión.

---

## 1. Calibración y Procesamiento Térmico Base (Fases 1 a 5)

*   **Malla regular de 30m y área de estudio**: Se estructuraron 181,746 celdas útiles en proyección UTM Zona 14N, asegurando mediciones métricas exactas y uniformes a lo largo de la cuenca metropolitana.
*   **Anomalía Térmica Nocturna (MODIS, 1:30 AM)**:
    *   **Calibración de la proyección GEE**: Al especificar la proyección sinusoidal nativa de MODIS (`SR-ORG:6974`) antes de realizar la reducción temporal por medianas y el remuestreo bilineal a 30m, se eliminó la distorsión por arrastre de las bajas temperaturas de las cumbres de la Sierra Madre Oriental sobre la planicie urbana.
    *   **Confirmación de la Isla Cálida Nocturna**: Se determinó que la SUHI nocturna urbana es de signo positivo y se sitúa en un rango de **+1.81 °C a +2.82 °C** en comparación con el baseline rural de control. En resolución nativa de 1 km, el núcleo urbano registra una anomalía de **+3.17 °C** (LST urbana de 19.76 °C vs LST rural de 16.59 °C), confirmando la retención de calor nocturno residual en la infraestructura construida.
*   **Evolución Temporal de LST Absoluta Diurna (Landsat 8 y 9, 2025-2026)**:
    *   Se evaluó la dinámica térmica diurna estacional en los puntos críticos de calor urbano (hotspots) desde enero de 2025 hasta junio de 2026.
    *   **Variabilidad estacional**: Se observa un ciclo térmico estacional marcado. Las temperaturas superficiales absolutas del suelo urbano descienden a rangos de 15-20 °C en invierno (diciembre a febrero) y ascienden a registros críticos superiores a los 35-40 °C en primavera y verano (marzo a agosto).
    *   **Atenuación localizada**: En el sector de oficinas administrativas de la Planta Ternium Guerrero (Hotspot 4), se identificó un comportamiento térmico diurno más moderado en comparación con las áreas de proceso industrial de San Nicolás (Hotspot 2), debido al sombreado y efecto de la cobertura verde local.

---

## 2. Análisis de Correlación Espacial Multiescala (Fases 6 a 8)

Para evaluar la heterogeneidad espacial y mitigar el Problema de la Unidad de Área Modificable (MAUP), se calcularon coeficientes de correlación de rangos de Spearman ($r$) sobre variables de mitigación (vegetación `green_pct`) y presión térmica (industria `industrial_osm_pct`) a escala local (celda de 30m) y en buffers radiales de vecindario (100m, 250m, 500m, 1000m y 3000m).

### A. Coeficientes Globales a Nivel de Municipio
*   **Bloque de Mitigación (Vegetación vs SUHI Diurna)**:
    *   **San Pedro Garza García**: Muestra la asociación negativa más robusta de la ZMM, con un coeficiente de **-0.239** a nivel local (30m) y de **-0.247** a escala de vecindario (500m), consistente con su estructura de arbolado de vecindario.
    *   **Guadalupe**: Registra un coeficiente de **-0.210** a nivel local (30m), que se debilita a -0.062 a escala de vecindario (500m).
    *   **Monterrey y San Nicolás**: Presentan coeficientes globales locales débiles (-0.068 y -0.088 respectivamente), indicando que el análisis agregado global oculta dinámicas internas.
*   **Bloque de Presión Térmica (Industria vs SUHI Diurna)**:
    *   **San Nicolás de los Garza**: Registra la mayor asociación positiva global con la SUHI diurna, situándose en **+0.409** a nivel local (30m) y ascendiendo a **+0.493** a escala de vecindario (500m), confirmando el rol térmico de sus extensos distritos industriales.
    *   **Monterrey**: Presenta un coeficiente positivo de **+0.121** local y de **+0.149** a 500m.

### B. Regímenes Microclimáticos según Densidad de Suelo Construido (Dynamic World)
La segmentación de las correlaciones por la fracción de impermeabilidad de la celda (`dw_built_pct`) revela tres comportamientos espaciales diferenciados en la ZMM:
1.  **Baja Densidad (<20% de suelo edificado)**:
    *   Existe una correlación negativa intensa y significativa entre la vegetación de vecindario y la SUHI diurna (ej. San Pedro: **-0.811** en buffer de 100m y **-0.779** en buffer de 500m; Monterrey: **-0.611** en buffer de 250m). Esto confirma que en áreas abiertas o residenciales suburbanas, el incremento de la cobertura verde se asocia fuertemente con un descenso de la temperatura local.
2.  **Media Densidad (20-60% de suelo edificado)**:
    *   Representa un régimen de transición. El efecto de asociación de la vegetación disminuye (San Pedro: -0.278 a 250m; Guadalupe: -0.255 a 250m), mientras que la proximidad industrial y la cobertura edificada local comienzan a ejercer una presión térmica directa (ej. Monterrey: **+0.361** en buffer industrial de 250m; San Nicolás: **+0.443** en buffer industrial de 250m).
3.  **Alta Densidad (>=60% de suelo edificado)**:
    *   **Saturación Térmica (Efecto Domo de Concreto)**: En las áreas de alta densidad de construcción, las variables de vegetación bidimensionales pierden significancia estadística (coeficientes de Spearman locales cercanos a cero: Guadalupe **-0.042**, Monterrey **-0.026**, San Nicolás **-0.083**). Los resultados sugieren que la reforestación aislada en áreas densamente construidas no se asocia estadísticamente con un descenso de la temperatura superficial local, requiriendo estrategias pasivas basadas en la materialidad (albedos, techos fríos).

---

## 3. Delimitación de Hotspots Térmicos (DBSCAN - Fase 10)

*   **Identificación espacial**: El algoritmo DBSCAN ($eps=60\text{ m}$, $min\_samples=3$ celdas) aisló los conglomerados de calor diurnos más intensos sobre la trama urbana de la ZMM.
*   **Priorización física**: Los clusters se ordenaron mediante un Puntaje de Criticidad Física que pondera la intensidad de la anomalía de calor, la extensión espacial del cluster y el déficit local de áreas verdes.
*   **Casos clave identificados**: Los sectores prioritarios corresponden a la Zona Industrial de San Nicolás (Cluster 66), el sector Centro-San Nicolás (Cluster 44), el corredor comercial y edificado de Valle Oriente en San Pedro (Cluster 5), y la planta industrial Ternium Guerrero (Cluster 38).

---

## 4. Integración Socio-Térmica (Fases 8 y 9)

*   **Análisis a nivel de vecindario (AGEB)**: La agregación demográfica del Censo INEGI 2020 a las celdas microclimáticas de la malla permitió derivar variables de vulnerabilidad socio-térmica.
*   **Índices sintéticos para la toma de decisiones**:
    *   **Índice de Vulnerabilidad Térmica (IVT)**: Muestra una correlación positiva moderada con la SUHI diurna en zonas de alta densidad ($r = +0.410$), evidenciando que los vecindarios con mayor concentración de población vulnerable (adultos mayores, infantes, carencia de servicios) coinciden con zonas de mayor acumulación de calor superficial.
    *   Estos índices permiten focalizar los programas de infraestructura verde y mitigación pasiva en los sectores donde la inercia térmica impacta a poblaciones con menor capacidad de adaptación.

---

## 5. Nota sobre Resultados Concretos y Acceso Privado

Los análisis más específicos generados en el proyecto —incluyendo las correlaciones Spearman a nivel desagregado para cada una de las 383 AGEBs del área metropolitana, las regresiones descriptivas locales de control y las capas geográficas detalladas a nivel de manzana— se conservan en la presentación ejecutiva (`presentacion_islas_calor_zmm_v7.pptx`) y en las bitácoras técnicas de la carpeta privada (`docs/private/`), dado que se encuentran en fase de validación de campo e interpretación interna del equipo.

Toda esta información detallada, bases de datos procesadas (`.gpkg`) y reportes por municipio se comparten con gusto bajo solicitud para soportar la toma de decisiones territoriales y la planificación urbana.
