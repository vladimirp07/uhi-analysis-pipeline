# Metodología General del Análisis Bottom-Up

1. **Fuentes de Datos y Sensores:**
   * **Térmica (SUHI):** Landsat 8/9 (TIRS diurno, 30m) y MODIS Aqua (MYD11A1 nocturno, remuestreado a 30m).
   * **Coberturas:** Sentinel-2 (NDVI y Cobertura Verde, 10m), Dynamic World (Zonificación de Densidad, 10m) y OpenStreetMap (Áreas Industriales vectoriales).
   * **Auxiliar:** Modelo Digital de Elevación SRTM GL1 (30m) para gradiente vertical y límites cartográficos de AGEB (INEGI).

2. **Control Metodológico (Baseline Rural - Directrices EPA):**
   * Definición de **3 zonas de control rural de referencia** con características de vegetación ($NDVI > 0.4$) y altitud equivalentes.
   * La intensidad SUHI por celda se calcula como la anomalía térmica local: $\text{SUHI} = LST_{\text{urbana}} - LST_{\text{rural\_baseline}}$.

3. **Discretización Territorial (Malla Maestra):**
   * Mallado de alta resolución con celdas físicas regulares de **30 x 30 metros** en la ZMM. Un total de **181,746 celdas analizadas**.

4. **Análisis Multiescala (Buffers Focalizados):**
   * Para cada celda de 30m, se calculan las coberturas verde e industrial a nivel local y en **buffers circulares concéntricos de 100m, 250m, 500m y 1000m**.

5. **Segmentación y Robustez Estadística:**
   * Clasificación por **Densidad Construida** (Baja <20%, Media 20-60%, Alta $\ge$ 60% de suelo impermeable).
   * Cálculo de coeficientes de **correlación de Spearman ($r$)** a nivel de celdas físicas agrupadas por Municipio y por AGEB.
   * Filtros de representatividad estadística para validez de $r$: $N \ge 30$ (AGEB) y $N \ge 50$ (Municipio).
