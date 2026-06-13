"""
Módulo para la generación de gráficas, visualizaciones y mapas estáticos y dinámicos de los resultados.
Implementa una suite de análisis exploratorio de datos (EDA) y auditorías visuales espaciales.
"""

import matplotlib.pyplot as plt
import geopandas as gpd
import contextily as ctx
import pandas as pd
from src.config import FIGURES_DIR

def plot_study_area_basemap(malla_gdf):
    """
    Grafica únicamente el polígono/contorno del bounding box del área de estudio
    sobre un mapa base satelital de Esri, sin datos térmicos.
    Proyecta temporalmente a Web Mercator (EPSG:3857) para permitir el renderizado
    correcto del mapa base.
    
    Args:
        malla_gdf (gpd.GeoDataFrame): Malla base o maestra del proyecto.
        
    Returns:
        str: Ruta de la imagen del mapa de contexto guardado.
    """
    print("\n[PLOTS] Generando mapa base del área de estudio...")
    
    # 1. Convertir la malla a Web Mercator (EPSG:3857) para alinear con contextily
    malla_3857 = malla_gdf.to_crs(epsg=3857)
    
    # Obtener el polígono del contorno exterior del bounding box completo
    bbox_poly = malla_3857.unary_union.envelope
    
    # 2. Crear la figura y graficar el borde
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # Graficar el límite exterior como una línea discontinua
    gpd.GeoSeries([bbox_poly]).plot(
        ax=ax,
        facecolor="none",
        edgecolor="#ff7f0e",
        linewidth=3.0,
        linestyle="--"
    )
    
    # 3. Añadir el mapa base con reintentos y tolerancia a fallas de red
    print("[PLOTS] Añadiendo mapa base CartoDB.Positron...")
    try:
        ctx.add_basemap(
            ax,
            source=ctx.providers.CartoDB.Positron,
            attribution_size=7
        )
    except Exception as e:
        print(f"[PLOTS] Advertencia: Falló CartoDB.Positron ({e}). Intentando Esri.WorldImagery...")
        try:
            ctx.add_basemap(
                ax,
                source=ctx.providers.Esri.WorldImagery,
                attribution_size=7
            )
        except Exception as esri_err:
            print(f"[PLOTS] Error de red: No se pudo conectar a los servidores de mapas base ({esri_err}).")
            print("[PLOTS] Generando el mapa de contexto únicamente con la caja de contorno de referencia.")

    # 4. Configurar anotaciones y leyenda
    ax.set_title("Ubicación del Área de Estudio - Monterrey (2026)", fontsize=14, fontweight="bold", pad=10)
    ax.set_xlabel("Este (Metros, Web Mercator)", fontsize=10)
    ax.set_ylabel("Norte (Metros, Web Mercator)", fontsize=10)
    ax.grid(True, linestyle="--", alpha=0.5)
    
    # Agregar leyenda con Patch manual para evitar warnings de matplotlib
    import matplotlib.patches as mpatches
    border_patch = mpatches.Patch(
        edgecolor="#ff7f0e",
        facecolor="none",
        linewidth=3.0,
        linestyle="--",
        label="Límite del Área de Estudio (Ternium/Monterrey Centro-Norte)"
    )
    ax.legend(handles=[border_patch], loc="upper right")
    
    # Ajustar límites de visualización con un margen de 5%
    minx, miny, maxx, maxy = bbox_poly.bounds
    width = maxx - minx
    height = maxy - miny
    ax.set_xlim(minx - width * 0.05, maxx + width * 0.05)
    ax.set_ylim(miny - height * 0.05, maxy + height * 0.05)
    
    # 5. Guardar la figura
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    output_path = FIGURES_DIR / "mapa_base_estudio.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    
    print(f"[PLOTS] Mapa base guardado exitosamente en: {output_path}")
    return str(output_path)

def plot_satellite_basemap(malla_gdf):
    """
    Genera y guarda una imagen limpia satelital de la zona de estudio (Ternium y alrededores)
    sin capas de datos o contornos vectoriales encima.
    
    Args:
        malla_gdf (gpd.GeoDataFrame): Malla base o maestra del proyecto.
        
    Returns:
        str: Ruta de la imagen del mapa satelital limpio guardado.
    """
    print("\n[PLOTS] Generando mapa satelital limpio...")
    
    # 1. Proyectar a Web Mercator (EPSG:3857) para contextily
    malla_3857 = malla_gdf.to_crs(epsg=3857)
    bbox_poly = malla_3857.unary_union.envelope
    minx, miny, maxx, maxy = bbox_poly.bounds
    
    # 2. Crear figura
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # Ajustar ejes estrictamente a los límites del área
    ax.set_xlim(minx, maxx)
    ax.set_ylim(miny, maxy)
    
    # 3. Descargar y dibujar el mapa satelital de Esri
    print("[PLOTS] Añadiendo mapa satelital limpio (Esri.WorldImagery)...")
    try:
        ctx.add_basemap(
            ax,
            source=ctx.providers.Esri.WorldImagery,
            attribution_size=6
        )
    except Exception as e:
        print(f"[PLOTS] Advertencia: Falló Esri.WorldImagery ({e}). Intentando CartoDB.Positron...")
        try:
            ctx.add_basemap(
                ax,
                source=ctx.providers.CartoDB.Positron,
                attribution_size=6
            )
        except Exception as err:
            print(f"[PLOTS] Error crítico de red: No se pudo descargar mapa satelital ({err}).")
            
    # Dar formato limpio
    ax.set_title("Contexto Satelital Urbano (Ternium / Monterrey)", fontsize=14, fontweight="bold", pad=10)
    ax.set_axis_off()
    
    # 4. Guardar archivo
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    output_path = FIGURES_DIR / "01_mapa_satelital_limpio.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    
    print(f"[PLOTS] Mapa satelital limpio guardado exitosamente en: {output_path}")
    return str(output_path)

def plot_eda_distributions(malla_gdf):
    """
    Genera un panel de 2x2 mostrando la distribución de las cuatro variables térmicas
    y urbanas principales utilizando histogramas y curvas de densidad (KDE).
    
    Args:
        malla_gdf (gpd.GeoDataFrame): Malla base enriquecida con features.
        
    Returns:
        str: Ruta del panel de histogramas guardado.
    """
    print("\n[PLOTS] Generando histogramas y curvas de densidad para el EDA...")
    
    # 1. Configurar la matriz de subplots (2x2)
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    axes = axes.flatten()
    
    cols = ["lst_c", "suhi_c", "green_pct", "industrial_osm_pct"]
    titles = [
        "Distribución de Temperatura Superficial (LST)",
        "Distribución de la Isla de Calor Superficial (SUHI)",
        "Distribución de Cobertura Vegetal (Green Pct)",
        "Distribución de Cobertura de Zonas Industriales"
    ]
    x_labels = [
        "Temperatura (°C)",
        "Intensidad SUHI (lst_c - rural_med) (°C)",
        "Porcentaje de Vegetación Verde por Celda (%)",
        "Porcentaje de Suelo Industrial por Celda (%)"
    ]
    colors = ["#d73027", "#f46d43", "#1a9850", "#313695"]
    
    # 2. Iterar sobre cada variable
    for i, col in enumerate(cols):
        ax = axes[i]
        
        # Eliminar valores nulos
        data = malla_gdf[col].dropna()
        
        if len(data) == 0:
            ax.text(0.5, 0.5, "Sin datos disponibles", ha="center", va="center", fontsize=12)
            ax.set_title(titles[i], fontsize=12, fontweight="bold")
            continue
            
        # Dibujar histograma de frecuencias
        ax.hist(data, bins=40, density=True, alpha=0.5, color=colors[i], edgecolor="white", label="Histograma")
        
        # Dibujar curva de densidad (KDE) usando Pandas (scipy.stats por detrás)
        try:
            data.plot.kde(ax=ax, color="black", linewidth=2.0, label="Curva Densidad (KDE)")
        except Exception as e:
            print(f"[PLOTS] No se pudo estimar el KDE para {col}: {e}")
            
        # Calcular estadísticas clave
        mean_val = data.mean()
        median_val = data.median()
        
        # Trazar líneas verticales de media y mediana
        ax.axvline(mean_val, color="blue", linestyle="--", linewidth=1.5, label=f"Media: {mean_val:.2f}°C" if "c" in col else f"Media: {mean_val:.2f}%")
        ax.axvline(median_val, color="darkorange", linestyle="-.", linewidth=1.5, label=f"Mediana: {median_val:.2f}°C" if "c" in col else f"Mediana: {median_val:.2f}%")
        
        # Dar formato
        ax.set_title(titles[i], fontsize=13, fontweight="bold")
        ax.set_xlabel(x_labels[i], fontsize=10)
        ax.set_ylabel("Densidad de Probabilidad", fontsize=10)
        ax.grid(True, linestyle=":", alpha=0.6)
        ax.legend(loc="upper right", fontsize=9)
        
    plt.tight_layout()
    
    # 3. Guardar panel completo
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    output_path = FIGURES_DIR / "02_eda_distribuciones.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    
    print(f"[PLOTS] Panel de distribuciones guardado exitosamente en: {output_path}")
    return str(output_path)

def plot_spatial_audit_panel(malla_gdf):
    """
    Genera y guarda un panel visual de 3x3 mapas (9 variables geoespaciales)
    para la auditoría de distribuciones espaciales físicas, satelitales y de distancias.
    
    Args:
        malla_gdf (gpd.GeoDataFrame): Malla maestra consolidada.
        
    Returns:
        str: Ruta del panel de mapas espaciales guardado.
    """
    print("\n[PLOTS] Generando panel de auditoría espacial ampliado (3x3)...")
    
    # 1. Crear figura con 3x3 subplots
    fig, axes = plt.subplots(3, 3, figsize=(22, 22), sharex=True, sharey=True)
    axes = axes.flatten()
    
    # Parámetros comunes de las leyendas para que estén correctamente escalados
    legend_kw = {"orientation": "horizontal", "pad": 0.02, "shrink": 0.8}
    
    configs = [
        {"col": "lst_day_c", "cmap": "magma", "label": "LST Diurna (°C)", "title": "A. Temp. Superficial (LST)"},
        {"col": "suhi_day_c", "cmap": "coolwarm", "label": "Intensidad SUHI (°C)", "title": "B. Anomalía Térmica (SUHI)"},
        {"col": "green_pct", "cmap": "YlGn", "label": "Cobertura Verde (%)", "title": "C. Cobertura Verde (NDVI)"},
        {"col": "dw_built_pct", "cmap": "Reds", "label": "Suelo Construido (%)", "title": "D. Suelo Construido (DW)"},
        {"col": "dw_trees_pct", "cmap": "Greens", "label": "Cobertura Arbórea (%)", "title": "E. Cobertura Arbórea (DW)"},
        {"col": "dw_bare_pct", "cmap": "YlOrBr", "label": "Suelo Desnudo (%)", "title": "F. Suelo Desnudo (DW)"},
        {"col": "industrial_osm_pct", "cmap": "Purples", "label": "Área Industrial (%)", "title": "G. Cobertura Industrial (OSM)"},
        {"col": "distance_to_industry_osm_m", "cmap": "viridis_r", "label": "Distancia (m)", "title": "H. Distancia a Zonas Industriales"},
        {"col": "distance_to_water_m", "cmap": "Blues_r", "label": "Distancia (m)", "title": "I. Distancia a Cuerpos de Agua"}
    ]
    
    for i, cfg in enumerate(configs):
        ax = axes[i]
        col_name = cfg["col"]
        
        # Validar si la columna existe en el GeoDataFrame
        if col_name in malla_gdf.columns:
            malla_gdf.plot(
                column=col_name,
                cmap=cfg["cmap"],
                legend=True,
                legend_kwds={"label": cfg["label"], **legend_kw},
                ax=ax,
                missing_kwds={"color": "#e0e0e0"}
            )
        else:
            ax.text(0.5, 0.5, f"Columna {col_name}\nno encontrada", ha="center", va="center", color="red", fontsize=10)
            
        ax.set_title(cfg["title"], fontsize=12, fontweight="bold", pad=8)
        ax.set_axis_off()
        
    plt.tight_layout()
    
    # 2. Guardar el panel de mapas
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    output_path = FIGURES_DIR / "03_panel_auditoria_espacial.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    
    # 3. Exportar mapas individuales complementarios para flexibilidad en la auditoría
    try:
        # Individual LST
        fig_lst, ax_lst = plt.subplots(figsize=(10, 10))
        malla_gdf.plot(column="lst_c" if "lst_c" in malla_gdf.columns else "lst_day_c", cmap="magma", legend=True, ax=ax_lst, missing_kwds={"color": "#e0e0e0"})
        ax_lst.set_title("Temperatura Superficial Terrestre (LST) - Monterrey 2026", fontsize=12, fontweight="bold")
        ax_lst.set_axis_off()
        plt.savefig(FIGURES_DIR / "mapa_lst_auditoria.png", dpi=300, bbox_inches="tight")
        plt.close()
        
        # Individual Industrial
        fig_ind, ax_ind = plt.subplots(figsize=(10, 10))
        malla_gdf.plot(column="industrial_osm_pct", cmap="Blues", legend=True, ax=ax_ind, missing_kwds={"color": "#e0e0e0"})
        ax_ind.set_title("Cobertura de Suelo Industrial - Monterrey 2026", fontsize=12, fontweight="bold")
        ax_ind.set_axis_off()
        plt.savefig(FIGURES_DIR / "mapa_industria_auditoria.png", dpi=300, bbox_inches="tight")
        plt.close()
        
        # Individual Vegetado
        fig_veg, ax_veg = plt.subplots(figsize=(10, 10))
        malla_gdf.plot(column="green_pct", cmap="YlGn", legend=True, ax=ax_veg, missing_kwds={"color": "#e0e0e0"})
        ax_veg.set_title("Cobertura Verde (NDVI > 0.3) - Monterrey 2026", fontsize=12, fontweight="bold")
        ax_veg.set_axis_off()
        plt.savefig(FIGURES_DIR / "mapa_vegetacion_auditoria.png", dpi=300, bbox_inches="tight")
        plt.close()
    except Exception as e:
        print(f"[PLOTS] Advertencia al guardar mapas individuales: {e}")
        
    print(f"[PLOTS] Panel de mapas de auditoría espacial guardado en: {output_path}")
    return str(output_path)
