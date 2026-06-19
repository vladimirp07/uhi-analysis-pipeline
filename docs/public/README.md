# Islas de Calor en la Zona Metropolitana de Monterrey

Este documento sirve como el punto de partida oficial para la documentación pública del pipeline de análisis geoespacial, biofísico y socioambiental de la Isla de Calor Urbana Superficial (SUHI) en la Zona Metropolitana de Monterrey (ZMM).

El pipeline está diseñado de manera paramétrica y modular para funcionar como un validador analítico clave en tierra para misiones de monitoreo térmico satelital, permitiendo verificar y modelar con alta resolución espacial (30 metros) los patrones de anomalías térmicas urbanas y su correlación espacio-temporal con las coberturas del suelo, la morfología urbana y la cercanía a infraestructura industrial.

---

## 1. Objetivos del Proyecto

### General
Analizar la distribución espacial y temporal de las islas de calor en la Zona Metropolitana de Monterrey y evaluar su relación con variables físicas, urbanas, ambientales y socioeconómicas, con el fin de entender el fenómeno y proponer estrategias de mitigación localizadas.

### Específicos
1. Identificar islas de calor superficiales en la ZMM.
2. Estudiar su comportamiento espacial y temporal a nivel estacional e histórico.
3. Evaluar la correlación de variables físicas, urbanas y ambientales con la aparición e intensidad de las islas de calor.
4. Integrar variables socioeconómicas para analizar vulnerabilidad territorial y exposición de la población.
5. Construir una base metodológica para construir un modelo microclimático que guíe la planificación del desarrollo urbano sostenible frente al calentamiento local.

---

## 2. Zona de Estudio: Zona Metropolitana de Monterrey (ZMM)

El análisis se delimita en la Zona Metropolitana de Monterrey, una cuenca urbana caracterizada por un clima semiárido extremo, una geografía compleja rodeada por importantes elevaciones montañosas (Sierra Madre Oriental, Cerro de la Silla, Cerro de las Mitras) y una marcada especialización industrial. El área metropolitana consolida un fuerte gradiente altitudinal (promedio urbano de 573 msnm) y un tejido urbano sumamente compacto y mineralizado, lo que intensifica la acumulación térmica diurna y nocturna.

---

## 3. Estructura de la Documentación Pública

La documentación detallada del proyecto se organiza en los siguientes archivos técnicos dentro de esta carpeta:

1.  **[METHODOLOGY.md](./METHODOLOGY.md):** Describe a detalle el flujo metodológico paso a paso, desde la discretización en celdas de 30m hasta la delimitación de hotspots y priorización mediante DBSCAN.
2.  **[DATA_SOURCES.md](./DATA_SOURCES.md):** Contiene el catálogo de fuentes de datos satelitales (Landsat 8, Sentinel-2, MODIS, Dynamic World), geográficas (OpenStreetMap) y censales (INEGI), detallando sus variables derivadas y limitaciones.
3.  **[RESULTS_SUMMARY.md](./RESULTS_SUMMARY.md):** Sintetiza los hallazgos analíticos clave del proyecto, incluyendo el análisis de correlación por densidades de suelo, los hotspots y coldspots priorizados, y la corrección técnica del bug de la anomalía nocturna.
4.  **[REPRODUCIBILITY.md](./REPRODUCIBILITY.md):** Detalla los requerimientos de entorno, dependencias de software, el orden recomendado de ejecución del código y las salidas esperadas del pipeline.
5.  **[FIGURES_INDEX.md](./FIGURES_INDEX.md):** Índice clasificado e ilustrado de las figuras analíticas generadas para la presentación y el reporte científico.

---

## 4. Arquitectura del Repositorio

El proyecto mantiene una estructura modular estándar para garantizar su reproducibilidad y extensibilidad:

```text
UHI_Analysis_pipeline_MVP_v1/
├── docs/                             # Documentación del proyecto (Pública y Privada)
│   ├── public/                       # Documentación técnica reproducible y publicable
│   └── private/                      # Notas internas, pendientes y bitácoras (excluido por gitignore)
├── data/                             # Datos geográficos crudos, intermedios y procesados (excluido)
├── notebooks/                        # Jupyter Notebooks de análisis y visualización interactiva
├── scripts/                          # Scripts de Python autónomos para procesamiento y modelación
├── reports/                          # Reportes técnicos de correlaciones y catálogos de imágenes
├── src/                              # Backend del pipeline (módulos de lógica geoespacial)
├── main.py                           # Orquestador del pipeline base de preparación de datos
└── requirements.txt                  # Dependencias del entorno de Python
```
