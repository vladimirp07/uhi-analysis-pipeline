# Resumen de Resultados Analíticos: Islas de Calor en la Zona Metropolitana de Monterrey

Este documento presenta una síntesis estructurada de los resultados obtenidos en el análisis de la distribución espacial y temporal de las islas de calor en la Zona Metropolitana de Monterrey (ZMM). La estructura de este resumen sigue el orden y flujo de las fases de procesamiento y modelación del pipeline metodológico implementado para facilitar su consulta y comprensión.

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

### A. Altos Índices de Correlación Espacial Encontrados
El análisis exploratorio de datos (EDA) ha revelado asociaciones de magnitud muy alta al segmentar territorialmente por municipios y tipos de vecindario:
*   **Bloque de Mitigación (Vegetación vs SUHI Diurna)**:
    *   **San Pedro Garza García (Zonas de Baja Densidad)**: Se hallaron **altos índices de correlación negativa** que demuestran la fuerza de la asociación entre la infraestructura verde de vecindario y la atenuación de la anomalía de calor superficial. El coeficiente alcanza **-0.781** a nivel local (30m) y se intensifica hasta **-0.811** a escala de buffer de 100m.
    *   **Guadalupe (Zonas de Baja Densidad)**: La correlación de la vegetación local con la anomalía es de -0.278, pero se incrementa fuertemente hasta **-0.645** en buffer de 250m y **-0.676** a escala de 1000m, evidenciando un efecto acumulativo de vecindario.
    *   **Monterrey (Zonas de Baja Densidad)**: Registra una asociación negativa de **-0.489** local y **-0.611** en buffer de 250m.
*   **Bloque de Presión Térmica (Industria vs SUHI Diurna)**:
    *   **San Nicolás de los Garza**: Muestra la asociación positiva más fuerte y persistente con la SUHI diurna en todas sus escalas y zonas de densidad (ej. zonas residenciales de baja densidad colindantes con industria: **+0.573** local y **+0.643** a 1000m; zonas industriales consolidadas: **+0.411** local y **+0.505** a 500m).
    *   **Monterrey (Zonas de Media Densidad)**: Registra una correlación positiva de **+0.253** local y **+0.374** en buffer de 500m.

### B. Regímenes Microclimáticos según Densidad de Suelo Construido (Dynamic World)
La segmentación de las correlaciones por la fracción de impermeabilidad de la celda (`dw_built_pct`) revela tres comportamientos espaciales diferenciados en la ZMM:
1.  **Baja Densidad (<20% de suelo edificado)**:
    *   Fuerte sensibilidad al enfriamiento por cobertura verde (como se constata con los altos índices de correlación de -0.61 a -0.81).
2.  **Media Densidad (20-60% de suelo edificado)**:
    *   Régimen de transición. El efecto de asociación de la vegetación disminuye (San Pedro: -0.278 a 250m), mientras que la proximidad industrial y la cobertura edificada local comienzan a ejercer una presión térmica directa (ej. Monterrey: **+0.361** en buffer industrial de 250m).
3.  **Alta Densidad (>=60% de suelo edificado)**:
    *   **Saturación Térmica (Efecto Domo de Concreto)**: Las variables de vegetación bidimensionales pierden significancia estadística (coeficientes de Spearman locales cercanos a cero: Guadalupe **-0.042**, Monterrey **-0.026**). Esto sugiere que la reforestación aislada en áreas densamente construidas no se asocia estadísticamente con un descenso de la temperatura superficial local.

### C. Integración de Nuevas Variables en Proceso
Para superar las limitaciones del modelado bidimensional (saturación en alta densidad) y enriquecer la precisión microclimática del modelo, se está trabajando en la integración de nuevas variables territoriales y biofísicas:
*   **Geometría Urbana 3D (Sky View Factor y Altura de Edificaciones)**: Para modelar el atrapamiento de radiación y el sombreado en cañones urbanos.
*   **Propiedades de Materiales (Albedo y Emisividad Térmica)**: Para caracterizar pavimentos, asfalto y techumbres.
*   **Inercia y Almacenamiento Térmico**: Para calibrar el flujo de calor almacenado diurno que se libera durante la noche.

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
