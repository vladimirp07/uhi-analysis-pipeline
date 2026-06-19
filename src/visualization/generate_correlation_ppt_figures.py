import os
import shutil
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd

def generate_01_hotspots_zmm(output_path):
    """
    Reutiliza el mapa general de hotspots en la ZMM.
    """
    src_hotspots_map = "outputs/05/hotspots_top3_overview_map.png"
    if os.path.exists(src_hotspots_map):
        shutil.copy(src_hotspots_map, output_path)
        print(f"[FIGS] Figure 01 (Hotspots ZMM) copied from {src_hotspots_map}")
    else:
        # Si no existe, crear un placeholder informativo para no fallar
        fig, ax = plt.subplots(figsize=(7, 5), dpi=300)
        ax.text(0.5, 0.5, "Mapa de Hotspots ZMM\n(Original en outputs/05/hotspots_top3_overview_map.png)", 
                ha='center', va='center', fontsize=12, color='#1f3864', weight='bold')
        ax.axis('off')
        plt.tight_layout()
        plt.savefig(output_path, dpi=300)
        plt.close()
        print(f"[FIGS] Figure 01: Source not found, generated placeholder at {output_path}")

def generate_02_hotspot_zoom(output_path):
    """
    Genera un zoom a una zona caliente (Ternium) con la malla de 30m superpuesta,
    mostrando individualmente las celdas, con anotación del tamaño y total de celdas.
    """
    print("[FIGS] Generando Figura 02 (Zoom Hotspot con malla de 30m)...")
    try:
        df = gpd.read_file('data/processed/malla_maestra_mty_2026.gpkg')
        c = df.geometry.centroid
        # Crop muy cercano alrededor de la planta Ternium para ver celdas individuales
        df_crop = df[(c.x > -100.3015) & (c.x < -100.2980) & (c.y > 25.7195) & (c.y < 25.7225)].copy()
        
        fig, ax = plt.subplots(figsize=(7, 5.5), dpi=300)
        
        # Graficar celdas individuales coloreadas por su LST diurno y con borde negro visible
        df_crop.plot(column='lst_day_c', ax=ax, cmap='YlOrRd', edgecolor='black', linewidth=0.5,
                     legend=True, legend_kwds={'label': 'Temperatura LST (°C)', 'shrink': 0.8})
        
        # Identificar una celda representativa para poner la flecha de anotación (cerca del centro)
        center_lon = -100.2995
        center_lat = 25.7210
        # Buscar la celda más cercana
        distances = df_crop.geometry.centroid.distance(gpd.points_from_xy([center_lon], [center_lat])[0])
        target_idx = distances.idxmin()
        target_cell = df_crop.loc[target_idx]
        target_centroid = target_cell.geometry.centroid
        
        # Añadir anotación apuntando a la celda
        ax.annotate("Celda de 30m x 30m\n(Área: 900 m²)", 
                    xy=(target_centroid.x, target_centroid.y), 
                    xytext=(target_centroid.x - 0.0012, target_centroid.y + 0.0008),
                    arrowprops=dict(facecolor='#1f3864', shrink=0.05, width=1.5, headwidth=6, headlength=6),
                    fontsize=8.5, weight='bold', color='#1f3864',
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#1f3864", alpha=0.9, lw=1))
        
        # Añadir cuadro de información global en una esquina
        ax.text(0.05, 0.05, "Malla de Modelado Multiescala\nTotal celdas analizadas ZMM: 181,746\nResolución: 30 metros (Landsat 8 LST)", 
                transform=ax.transAxes, fontsize=8.5, color='#222222', weight='bold',
                bbox=dict(boxstyle="round,pad=0.4", fc="#f2f4f8", ec="#d3d3d3", alpha=0.9))
        
        ax.set_title("Resolución de Celda en el Análisis Bottom-Up\n(Detalle en Zona Industrial, San Nicolás)", 
                     fontsize=10.5, weight='bold', color='#1f3864', pad=12)
        ax.set_xlabel("Longitud", fontsize=8)
        ax.set_ylabel("Latitud", fontsize=8)
        ax.grid(True, linestyle='--', alpha=0.4)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"[FIGS] Figure 02 generated successfully at {output_path}")
    except Exception as e:
        print(f"[ERROR] Error generating Figure 02: {e}")
        # Copiar zoom original de Ternium si falla
        src_zoom_map = "outputs/05/hotspot_ternium_zoom_map.png"
        if os.path.exists(src_zoom_map):
            shutil.copy(src_zoom_map, output_path)
            print(f"[FIGS] Figure 02 fallback: copied from {src_zoom_map}")

def generate_03_fuentes_table(output_path):
    """
    Genera una tabla visual de fuentes de datos de forma limpia y profesional.
    """
    print("[FIGS] Generando Figura 03 (Tabla de fuentes de datos)...")
    headers = ["Sensor / Fuente", "Información Técnica", "Uso dentro del Análisis"]
    data = [
        ["Landsat 8 (TIRS)", "Temperatura de Superficie (B10, 100m native)", "Capa térmica (LST) y anomalía SUHI diurna (mediana de primavera 2026)"],
        ["Sentinel-2 (MSI)", "Bandas Ópticas y NIR (10m / 20m)", "NDVI a 10m y porcentaje de cobertura verde (green_pct) remuestreado a 30m"],
        ["Dynamic World", "Clasificación de Cobertura (10m, Sentinel-2)", "Porcentaje de suelo edificado (dw_built_pct) para segmentación de densidad"],
        ["OpenStreetMap", "Polígonos vectoriales de infraestructura", "Huellas de naves industriales (industrial_osm_pct) y buffers multiescala"],
        ["INEGI / Censo 2020", "Límites AGEB y variables demográficas", "Límites político-administrativos, agregación local y población vulnerable"]
    ]
    
    fig, ax = plt.subplots(figsize=(9.5, 3.5), dpi=300)
    ax.axis('off')
    
    table = ax.table(cellText=data, colLabels=headers, loc='center', cellLoc='left')
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    
    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_facecolor('#1f3864')
            cell.set_text_props(color='white', weight='bold', size=8.5)
        else:
            if row % 2 == 0:
                cell.set_facecolor('#f2f4f8')
            else:
                cell.set_facecolor('white')
            cell.set_text_props(color='#222222', size=7.5)
        cell.set_edgecolor('#d3d3d3')
        cell.set_linewidth(0.5)
        cell.set_height(0.18)
        
    table.auto_set_column_width(col=list(range(len(headers))))
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[FIGS] Figure 03 generated at {output_path}")

def generate_04_capas_base(output_path):
    """
    Genera una figura compuesta de tres paneles mostrando las tres capas principales
    del análisis: SUHI diurna, cobertura de vegetación (green_pct) y cobertura industrial (industrial_osm_pct).
    """
    print("[FIGS] Generando Figura 04 (Capas base en 3 paneles)...")
    try:
        df = gpd.read_file('data/processed/malla_maestra_mty_2026.gpkg')
        c = df.geometry.centroid
        # Crop que incluye Monterrey y San Nicolás centro/norte
        df_crop = df[(c.x > -100.34) & (c.x < -100.28) & (c.y > 25.67) & (c.y < 25.73)].copy()
        
        # Rellenar nulos (green_pct y industrial_osm_pct ya están en escala 0-100 en el gpkg)
        df_crop['green_pct'] = df_crop['green_pct'].fillna(0)
        df_crop['industrial_osm_pct'] = df_crop['industrial_osm_pct'].fillna(0)
        df_crop['suhi_day_c'] = df_crop['suhi_day_c'].fillna(df_crop['suhi_day_c'].mean())
        
        fig, axes = plt.subplots(1, 3, figsize=(15, 6), dpi=600)
        
        # Panel 1: SUHI / Islas de Calor
        ax = axes[0]
        df_crop.plot(column='suhi_day_c', ax=ax, cmap='coolwarm', edgecolor='none', vmin=-10, vmax=10)
        ax.set_aspect('equal', adjustable='box')
        ax.axis('off')
        ax.set_title("1. Anomalía Térmica SUHI\n(LST - LST Rural)", fontsize=11, weight='bold', color='#1f3864', pad=12)
        
        from mpl_toolkits.axes_grid1 import make_axes_locatable
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("bottom", size="5%", pad="8%")
        cbar = fig.colorbar(ax.collections[0], cax=cax, orientation='horizontal')
        cbar.set_label('Intensidad SUHI (°C)', fontsize=9.5, weight='bold', color='#1f3864')
        cbar.ax.tick_params(labelsize=8.5)
        
        # Panel 2: Vegetación (green_pct)
        ax = axes[1]
        df_crop.plot(column='green_pct', ax=ax, cmap='YlGn', edgecolor='none', vmin=0, vmax=100)
        ax.set_aspect('equal', adjustable='box')
        ax.axis('off')
        ax.set_title("2. Cobertura de Vegetación\n(green_pct de Sentinel-2)", fontsize=11, weight='bold', color='#1f3864', pad=12)
        
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("bottom", size="5%", pad="8%")
        cbar = fig.colorbar(ax.collections[0], cax=cax, orientation='horizontal')
        cbar.set_label('Cobertura Verde (%)', fontsize=9.5, weight='bold', color='#1f3864')
        cbar.ax.tick_params(labelsize=8.5)
        
        # Panel 3: Industria (industrial_osm_pct)
        ax = axes[2]
        df_crop.plot(column='industrial_osm_pct', ax=ax, cmap='Purples', edgecolor='none', vmin=0, vmax=100)
        ax.set_aspect('equal', adjustable='box')
        ax.axis('off')
        ax.set_title("3. Cobertura Industrial\n(industrial_osm_pct de OSM)", fontsize=11, weight='bold', color='#1f3864', pad=12)
        
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("bottom", size="5%", pad="8%")
        cbar = fig.colorbar(ax.collections[0], cax=cax, orientation='horizontal')
        cbar.set_label('Área Industrial (%)', fontsize=9.5, weight='bold', color='#1f3864')
        cbar.ax.tick_params(labelsize=8.5)
        
        plt.suptitle("Capas Base del Análisis de Correlación Bottom-Up (Sector Centro-Norte de la ZMM)", 
                     fontsize=13, weight='bold', color='#1f3864', y=0.98)
        plt.savefig(output_path, dpi=600, bbox_inches='tight')
        plt.close()
        print(f"[FIGS] Figure 04 generated successfully at {output_path}")
    except Exception as e:
        print(f"[ERROR] Error generating Figure 04: {e}")
        # Generar un placeholder descriptivo si falla
        fig, ax = plt.subplots(figsize=(10, 4), dpi=300)
        ax.text(0.5, 0.5, "Figura Compuesta: 3 Capas Base (SUHI, Vegetación, Industria)\n[Error en carga de datos. Verifique archivos GPKG]", 
                ha='center', va='center', fontsize=12, color='#c00000', weight='bold')
        ax.axis('off')
        plt.savefig(output_path, dpi=300)
        plt.close()

def generate_05_metodologia_diagrama(output_path):
    """
    Genera el diagrama de flujo metodológico de la presentación.
    """
    print("[FIGS] Generando Figura 05 (Diagrama metodológico)...")
    fig, ax = plt.subplots(figsize=(7.5, 7.0), dpi=300)
    
    steps = [
        "1. Discretización Territorial\nCreación de malla de celdas físicas de 30m de resolución",
        "2. Asignación Temática (Spatial Join)\nAsociación de Municipio, AGEB y Zona de Densidad Construida",
        "3. Cálculo Multiescala (Filtro Focal)\nCálculo de vegetación e industria en celda local y buffers\n(100m, 250m, 500m y 1000m)",
        "4. Correlaciones de Spearman\nMedición de fuerza de asociación bivariada no lineal (r)",
        "5. Comparación y Segmentación\nAnálisis segmentado por Municipio y por Clase de Densidad",
        "6. Generación de Hallazgos y Síntesis\nTablas de coeficientes, mapas de sensibilidad e implicaciones"
    ]
    
    box_style = dict(boxstyle="round,pad=0.5", fc="#1f3864", ec="none", alpha=0.95)
    
    for i, step in enumerate(steps):
        y = 5.5 - i
        # Dibujar cuadro de texto
        ax.text(0.5, y, step, ha="center", va="center", color="white",
                weight="bold", fontsize=8.5, bbox=box_style)
        
        # Dibujar flecha de conexión
        if i < 5:
            ax.annotate("", xy=(0.5, y - 0.70), xytext=(0.5, y - 0.30),
                        arrowprops=dict(arrowstyle="->", color="#c55a11", lw=2.5))
            
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.2, 6.0)
    ax.axis('off')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[FIGS] Figure 05 generated at {output_path}")

def generate_06_mapa_densidad(output_path):
    """
    Copia el mapa de zonificación de densidades construido a partir de Dynamic World.
    """
    src_density_map = "outputs/figures/06_mapa_densidades_dw.png"
    if os.path.exists(src_density_map):
        shutil.copy(src_density_map, output_path)
        print(f"[FIGS] Figure 06 (Mapa Densidad) copied from {src_density_map}")
    else:
        fig, ax = plt.subplots(figsize=(7, 5), dpi=300)
        ax.text(0.5, 0.5, "Mapa de Zonificación de Densidades\n(Baja <20%, Media 20-60%, Alta >=60%)\n[Original en outputs/figures/06_mapa_densidades_dw.png]", 
                ha='center', va='center', fontsize=11, color='#1f3864', weight='bold')
        ax.axis('off')
        plt.savefig(output_path, dpi=300)
        plt.close()
        print(f"[FIGS] Figure 06: Source not found, generated placeholder at {output_path}")

def generate_07_heatmap(output_path):
    """
    Genera una matriz/heatmap detallado de los coeficientes de vegetación para los
    4 municipios y las 3 densidades en todas las escalas de buffer.
    """
    print("[FIGS] Generando Figura 07 (Heatmap de vegetación)...")
    sns.set_theme(style="white")
    
    # Índices jerárquicos
    index = pd.MultiIndex.from_tuples([
        ('San Pedro', 'Baja (<20%)'),
        ('San Pedro', 'Media (20-60%)'),
        ('San Pedro', 'Alta (>=60%)'),
        ('Guadalupe', 'Baja (<20%)'),
        ('Guadalupe', 'Media (20-60%)'),
        ('Guadalupe', 'Alta (>=60%)'),
        ('San Nicolás', 'Baja (<20%)'),
        ('San Nicolás', 'Media (20-60%)'),
        ('San Nicolás', 'Alta (>=60%)'),
        ('Monterrey', 'Baja (<20%)'),
        ('Monterrey', 'Media (20-60%)'),
        ('Monterrey', 'Alta (>=60%)'),
    ], names=['Municipio', 'Densidad'])
    
    columns = ['Local (30m)', 'Buffer 100m', 'Buffer 250m', 'Buffer 500m', 'Buffer 1000m']
    
    # Coeficientes reales
    data = [
        [-0.781, -0.811, -0.806, -0.779, -0.720],  # SP Baja
        [-0.319, -0.374, -0.278, -0.171, -0.121],  # SP Media
        [-0.116, -0.201, -0.202, -0.170, -0.133],  # SP Alta
        [-0.278, -0.567, -0.645, -0.644, -0.676],  # GD Baja
        [-0.150, -0.234, -0.255, -0.190, -0.104],  # GD Media
        [-0.042, -0.048, +0.037, +0.114, +0.335],  # GD Alta
        [-0.536, -0.592, -0.632, -0.674, -0.618],  # SN Baja
        [-0.091, -0.137, -0.138, -0.135, -0.086],  # SN Media
        [-0.083, -0.140, -0.120, -0.079, +0.044],  # SN Alta
        [-0.489, -0.609, -0.611, -0.522, -0.140],  # MY Baja
        [-0.133, -0.179, -0.162, -0.137, -0.069],  # MY Media
        [-0.026, -0.022, +0.028, +0.063, +0.120]   # MY Alta
    ]
    
    df_heatmap = pd.DataFrame(data, index=index, columns=columns)
    
    fig, ax = plt.subplots(figsize=(8.5, 6.0), dpi=300)
    
    # Usar RdYlGn_r para que correlaciones negativas (atenuación/enfriamiento) se muestren en verde
    # y valores cercanos a cero o positivos se muestren en amarillo/rojo.
    sns.heatmap(df_heatmap, annot=True, fmt="+.3f", cmap="RdYlGn_r", center=0, vmin=-0.85, vmax=0.4,
                cbar_kws={'label': 'Coeficiente de Correlación de Spearman (r)'}, ax=ax,
                annot_kws={"size": 9.5, "weight": "bold"})
    
    ax.set_title('Matriz de Coeficientes de Spearman (r): Vegetación vs SUHI diurna\n(Segmentado por Municipio, Densidad Construida y Escala de Buffer)', 
                 fontsize=10.5, fontweight='bold', pad=15, color='#1f3864')
    
    plt.ylabel('Segmentos (Municipio y Zona de Densidad)', fontsize=9.5, fontweight='bold')
    plt.xlabel('Escala de Análisis (Radio de Buffer)', fontsize=9.5, fontweight='bold')
    plt.xticks(rotation=15)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[FIGS] Figure 07 generated at {output_path}")

def generate_08_veg_baja(output_path):
    """
    Gráfico de líneas comparando las escalas de buffer para vegetación en baja densidad.
    """
    print("[FIGS] Generando Figura 08 (Vegetación en baja densidad)...")
    sns.set_theme(style="whitegrid")
    scales = ['Local (30m)', '100m', '250m', '500m', '1000m']
    san_pedro = [-0.781, -0.811, -0.806, -0.779, -0.720]
    guadalupe = [-0.278, -0.567, -0.645, -0.644, -0.676]
    san_nicolas = [-0.536, -0.592, -0.632, -0.674, -0.618]
    monterrey = [-0.489, -0.609, -0.611, -0.522, -0.140]
    
    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=300)
    ax.plot(scales, san_pedro, marker='o', linewidth=3, label='San Pedro Garza García', color='#1f3864')
    ax.plot(scales, guadalupe, marker='s', linewidth=3, label='Guadalupe', color='#c55a11')
    ax.plot(scales, san_nicolas, marker='^', linewidth=3, label='San Nicolás de los Garza', color='#2e7d32')
    ax.plot(scales, monterrey, marker='d', linewidth=3, label='Monterrey', color='#7030a0')
    
    ax.set_title('Asociación de la Vegetación según Escala de Buffer\n(Zonas de Baja Densidad Construida, <20%)', 
                 fontsize=11, fontweight='bold', pad=15, color='#1f3864')
    ax.set_xlabel('Escala de Análisis (Radio de Buffer)', fontsize=9, labelpad=10)
    ax.set_ylabel('Coeficiente de Correlación de Spearman (r)', fontsize=9, labelpad=10)
    ax.set_ylim(-0.9, 0.0)
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend(frameon=True, fontsize=8, loc='lower right')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[FIGS] Figure 08 generated at {output_path}")

def generate_09_ind_buffers(output_path):
    """
    Gráfico de líneas comparando las escalas de buffer para industria en casos clave.
    """
    print("[FIGS] Generando Figura 09 (Industria por buffers)...")
    sns.set_theme(style="whitegrid")
    scales = ['Local (30m)', '100m', '250m', '500m', '1000m']
    
    san_nicolas_baja = [0.573, 0.595, 0.624, 0.630, 0.643]
    san_nicolas_alta = [0.411, 0.473, 0.500, 0.505, 0.469]
    monterrey_baja = [-0.009, 0.104, 0.379, 0.540, 0.596]
    monterrey_media = [0.253, 0.316, 0.361, 0.374, 0.304]
    # San Pedro tiene N/D en local e 100m, se representa como None en la lista
    san_pedro_baja = [None, None, 0.079, 0.260, 0.579]
    
    fig, ax = plt.subplots(figsize=(7.2, 4.5), dpi=300)
    ax.plot(scales, san_nicolas_baja, marker='o', linewidth=2.5, linestyle='-', label='San Nicolás (Baja)', color='#2e7d32')
    ax.plot(scales, san_nicolas_alta, marker='o', linewidth=2.5, linestyle='--', label='San Nicolás (Alta)', color='#a5d6a7')
    ax.plot(scales, monterrey_baja, marker='s', linewidth=2.5, linestyle='-', label='Monterrey (Baja)', color='#7030a0')
    ax.plot(scales, monterrey_media, marker='s', linewidth=2.5, linestyle='--', label='Monterrey (Media)', color='#b39ddb')
    ax.plot(scales, san_pedro_baja, marker='^', linewidth=2.5, linestyle=':', label='San Pedro (Baja, Spillover)', color='#1f3864')
    
    ax.set_title('Asociación de la Industria según Escala de Buffer\n(Casos Seleccionados de Presión y Spillover)', 
                 fontsize=11, fontweight='bold', pad=15, color='#1f3864')
    ax.set_xlabel('Escala de Análisis (Radio de Buffer)', fontsize=9, labelpad=10)
    ax.set_ylabel('Coeficiente de Correlación de Spearman (r)', fontsize=9, labelpad=10)
    ax.set_ylim(-0.1, 0.75)
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend(frameon=True, fontsize=8, loc='upper left')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[FIGS] Figure 09 generated at {output_path}")

def generate_10_decaimiento_veg(output_path):
    """
    Gráfico de líneas que muestra la pérdida de fuerza de la asociación (decaimiento)
    de la vegetación al pasar de baja a media y alta densidad.
    """
    print("[FIGS] Generando Figura 10 (Decaimiento vegetación)...")
    sns.set_theme(style="whitegrid")
    densities = ['Baja (<20%)', 'Media (20-60%)', 'Alta (>=60%)']
    
    # Coeficientes locales (30m) para vegetación
    san_pedro = [-0.781, -0.319, -0.116]
    guadalupe = [-0.278, -0.150, -0.042]
    san_nicolas = [-0.536, -0.091, -0.083]
    monterrey = [-0.489, -0.133, -0.026]
    
    fig, ax = plt.subplots(figsize=(7.2, 4.6), dpi=300)
    ax.plot(densities, san_pedro, marker='o', linewidth=3, label='San Pedro Garza García', color='#1f3864')
    ax.plot(densities, guadalupe, marker='s', linewidth=3, label='Guadalupe', color='#c55a11')
    ax.plot(densities, san_nicolas, marker='^', linewidth=3, label='San Nicolás de los Garza', color='#2e7d32')
    ax.plot(densities, monterrey, marker='d', linewidth=3, label='Monterrey', color='#7030a0')
    
    ax.set_title('Decaimiento de la Asociación de Enfriamiento (Vegetación Local 30m)\nal Incrementar la Densidad de Suelo Construido', 
                 fontsize=10.5, fontweight='bold', pad=15, color='#1f3864')
    ax.set_xlabel('Zona de Densidad Construida', fontsize=9, labelpad=10)
    ax.set_ylabel('Coeficiente de Correlación de Spearman (r)', fontsize=9, labelpad=10)
    ax.set_ylim(-0.9, 0.05)
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend(frameon=True, fontsize=8, loc='lower right')
    
    # Añadir valores sobre los marcadores
    for x_idx, (sp, gp, sn, mty) in enumerate(zip(san_pedro, guadalupe, san_nicolas, monterrey)):
        ax.annotate(f'{sp:+.3f}', (x_idx, sp), textcoords="offset points", xytext=(-10,-12), ha='center', fontsize=7.5, fontweight='bold', color='#1f3864')
        ax.annotate(f'{gp:+.3f}', (x_idx, gp), textcoords="offset points", xytext=(15,-5), ha='center', fontsize=7.5, fontweight='bold', color='#c55a11')
        ax.annotate(f'{sn:+.3f}', (x_idx, sn), textcoords="offset points", xytext=(-12,8), ha='center', fontsize=7.5, fontweight='bold', color='#2e7d32')
        ax.annotate(f'{mty:+.3f}', (x_idx, mty), textcoords="offset points", xytext=(15,5), ha='center', fontsize=7.5, fontweight='bold', color='#7030a0')
        
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[FIGS] Figure 10 generated at {output_path}")

def generate_11_decaimiento_ind(output_path):
    """
    Gráfico de líneas que muestra el comportamiento/decaimiento de la asociación de la industria
    al pasar de baja a media y alta densidad.
    """
    print("[FIGS] Generando Figura 11 (Decaimiento industria)...")
    sns.set_theme(style="whitegrid")
    densities = ['Baja (<20%)', 'Media (20-60%)', 'Alta (>=60%)']
    
    # Coeficientes a escala vecindario (500m) para industria (es más estable y representativo de buffers)
    san_nicolas = [0.630, 0.439, 0.505]
    monterrey = [0.540, 0.374, 0.088]
    san_pedro = [0.260, 0.288, -0.063]
    guadalupe = [0.205, 0.038, -0.271]
    
    fig, ax = plt.subplots(figsize=(7.2, 4.6), dpi=300)
    ax.plot(densities, san_nicolas, marker='o', linewidth=3, label='San Nicolás de los Garza', color='#2e7d32')
    ax.plot(densities, monterrey, marker='s', linewidth=3, label='Monterrey', color='#7030a0')
    ax.plot(densities, san_pedro, marker='^', linewidth=3, label='San Pedro (Spillover)', color='#1f3864')
    ax.plot(densities, guadalupe, marker='d', linewidth=3, label='Guadalupe', color='#c55a11')
    
    ax.set_title('Transición de la Asociación Industrial (Escala Vecindario 500m)\nsegún Densidad de Suelo Construido', 
                 fontsize=10.5, fontweight='bold', pad=15, color='#1f3864')
    ax.set_xlabel('Zona de Densidad Construida', fontsize=9, labelpad=10)
    ax.set_ylabel('Coeficiente de Correlación de Spearman (r)', fontsize=9, labelpad=10)
    ax.set_ylim(-0.35, 0.75)
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend(frameon=True, fontsize=8, loc='lower left')
    
    # Añadir valores sobre los marcadores
    for x_idx, (sn, mty, sp, gp) in enumerate(zip(san_nicolas, monterrey, san_pedro, guadalupe)):
        ax.annotate(f'{sn:+.3f}', (x_idx, sn), textcoords="offset points", xytext=(0,8), ha='center', fontsize=7.5, fontweight='bold', color='#2e7d32')
        ax.annotate(f'{mty:+.3f}', (x_idx, mty), textcoords="offset points", xytext=(15,5), ha='center', fontsize=7.5, fontweight='bold', color='#7030a0')
        ax.annotate(f'{sp:+.3f}', (x_idx, sp), textcoords="offset points", xytext=(-15,-12), ha='center', fontsize=7.5, fontweight='bold', color='#1f3864')
        ax.annotate(f'{gp:+.3f}', (x_idx, gp), textcoords="offset points", xytext=(12,-8), ha='center', fontsize=7.5, fontweight='bold', color='#c55a11')
        
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[FIGS] Figure 11 generated at {output_path}")

def generate_12_baja_vs_alta(output_path):
    """
    Gráfico comparativo de barras de la correlación local de vegetación (30m) en baja vs alta densidad.
    """
    print("[FIGS] Generando Figura 12 (Comparativa de vegetación local baja vs alta)...")
    sns.set_theme(style="whitegrid")
    municipios = ['San Pedro', 'Guadalupe', 'San Nicolás', 'Monterrey']
    baja_densidad = [-0.781, -0.278, -0.536, -0.489]
    alta_densidad = [-0.116, -0.042, -0.083, -0.026]
    
    x = np.arange(len(municipios))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(7.2, 4.5), dpi=300)
    rects1 = ax.bar(x - width/2, baja_densidad, width, label='Baja Densidad (<20%)', color='#70ad47')
    rects2 = ax.bar(x + width/2, alta_densidad, width, label='Alta Densidad (>=60%)', color='#c00000')
    
    ax.set_title('Efecto de la Densidad en la Mitigación Térmica (Vegetación Local 30m)\nComparativa Baja vs Alta Densidad Construida por Municipio', 
                 fontsize=10.5, fontweight='bold', pad=15, color='#1f3864')
    ax.set_ylabel('Coeficiente de Correlación de Spearman (r)', fontsize=9, labelpad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(municipios, fontsize=9)
    ax.set_ylim(-0.9, 0.1)
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend(frameon=True, fontsize=8.5, loc='lower right')
    
    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:+.3f}',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3 if height >= 0 else -12),
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=8, fontweight='bold')
                        
    autolabel(rects1)
    autolabel(rects2)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[FIGS] Figure 12 generated at {output_path}")

def main():
    figures_dir = "reports/correlation_presentation_md/figures"
    os.makedirs(figures_dir, exist_ok=True)
    
    # Generar las 12 figuras ordenadas
    generate_01_hotspots_zmm(os.path.join(figures_dir, "01_hotspots_zmm.png"))
    generate_02_hotspot_zoom(os.path.join(figures_dir, "02_hotspot_zoom_celda_30m.png"))
    generate_03_fuentes_table(os.path.join(figures_dir, "03_fuentes_datos_table.png"))
    generate_04_capas_base(os.path.join(figures_dir, "04_capas_base_analisis.png"))
    generate_05_metodologia_diagrama(os.path.join(figures_dir, "05_metodologia_diagrama.png"))
    generate_06_mapa_densidad(os.path.join(figures_dir, "06_mapa_densidad_baja_media_alta.png"))
    generate_07_heatmap(os.path.join(figures_dir, "07_heatmap_spearman_vegetacion.png"))
    generate_08_veg_baja(os.path.join(figures_dir, "08_vegetacion_buffers_baja.png"))
    generate_09_ind_buffers(os.path.join(figures_dir, "09_industria_buffers.png"))
    generate_10_decaimiento_veg(os.path.join(figures_dir, "10_decaimiento_vegetacion_densidad.png"))
    generate_11_decaimiento_ind(os.path.join(figures_dir, "11_decaimiento_industria_densidad.png"))
    generate_12_baja_vs_alta(os.path.join(figures_dir, "12_baja_vs_alta_vegetacion.png"))
    
    print("\n[FIGS] ¡Generación de las 12 figuras prioritarias completada con éxito!")

if __name__ == "__main__":
    main()
