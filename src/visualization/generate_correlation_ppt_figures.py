import os
import shutil
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def generate_vegetacion_line_chart(output_path):
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
    
    ax.set_title('Asociación de la Vegetación según Escala de Buffer\n(Zonas de Baja Densidad Construida)', fontsize=11, fontweight='bold', pad=15, color='#1f3864')
    ax.set_xlabel('Escala de Análisis (Radio de Buffer)', fontsize=9, labelpad=10)
    ax.set_ylabel('Coeficiente de Correlación de Spearman (r)', fontsize=9, labelpad=10)
    ax.set_ylim(-0.9, 0.0)
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend(frameon=True, fontsize=8, loc='lower right')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[FIGS] Figure 1 (Vegetacion) generated at: {output_path}")

def generate_industria_line_chart(output_path):
    sns.set_theme(style="whitegrid")
    scales = ['Local (30m)', '100m', '250m', '500m', '1000m']
    san_nicolas_baja = [0.573, 0.595, 0.624, 0.630, 0.643]
    san_nicolas_alta = [0.411, 0.473, 0.500, 0.505, 0.469]
    monterrey_baja = [-0.009, 0.104, 0.379, 0.540, 0.596]
    monterrey_media = [0.253, 0.316, 0.361, 0.374, 0.304]
    san_pedro_baja = [0.0, 0.0, 0.079, 0.260, 0.579] # N/D treated as 0 or handled gracefully
    
    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=300)
    ax.plot(scales, san_nicolas_baja, marker='o', linewidth=2.5, linestyle='-', label='San Nicolás (Baja)', color='#1f3864')
    ax.plot(scales, san_nicolas_alta, marker='o', linewidth=2.5, linestyle='--', label='San Nicolás (Alta)', color='#2f5597')
    ax.plot(scales, monterrey_baja, marker='s', linewidth=2.5, linestyle='-', label='Monterrey (Baja)', color='#c55a11')
    ax.plot(scales, monterrey_media, marker='s', linewidth=2.5, linestyle='--', label='Monterrey (Media)', color='#f4b183')
    ax.plot(scales, san_pedro_baja, marker='^', linewidth=2.5, linestyle=':', label='San Pedro (Baja, Spillover)', color='#7030a0')
    
    ax.set_title('Asociación de la Industria según Escala de Buffer\n(Casos Seleccionados)', fontsize=11, fontweight='bold', pad=15, color='#1f3864')
    ax.set_xlabel('Escala de Análisis (Radio de Buffer)', fontsize=9, labelpad=10)
    ax.set_ylabel('Coeficiente de Correlación de Spearman (r)', fontsize=9, labelpad=10)
    ax.set_ylim(-0.1, 0.7)
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend(frameon=True, fontsize=8, loc='upper left')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[FIGS] Figure 2 (Industria) generated at: {output_path}")

def generate_density_bar_chart(output_path):
    sns.set_theme(style="whitegrid")
    municipios = ['San Pedro', 'Guadalupe', 'San Nicolás', 'Monterrey']
    baja_densidad = [-0.781, -0.278, -0.536, -0.489]
    alta_densidad = [-0.116, -0.042, -0.083, -0.026]
    
    x = np.arange(len(municipios))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=300)
    rects1 = ax.bar(x - width/2, baja_densidad, width, label='Baja Densidad (<20%)', color='#70ad47')
    rects2 = ax.bar(x + width/2, alta_densidad, width, label='Alta Densidad (>=60%)', color='#c00000')
    
    ax.set_title('Vegetación Local (30m): Baja vs Alta Densidad Construida', fontsize=11, fontweight='bold', pad=15, color='#1f3864')
    ax.set_ylabel('Coeficiente de Spearman (r)', fontsize=9, labelpad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(municipios, fontsize=9)
    ax.set_ylim(-0.9, 0.1)
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend(frameon=True, fontsize=9, loc='lower right')
    
    # Add values on top of bars
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
    print(f"[FIGS] Figure 3 (Bar Chart) generated at: {output_path}")

def generate_heatmap(output_path):
    sns.set_theme(style="white")
    municipios = ['San Pedro', 'Guadalupe', 'San Nicolás', 'Monterrey']
    buffers = ['Local (30m)', '100m', '250m', '500m', '1000m']
    
    matrix = np.array([
        [-0.781, -0.811, -0.806, -0.779, -0.720],
        [-0.278, -0.567, -0.645, -0.644, -0.676],
        [-0.536, -0.592, -0.632, -0.674, -0.618],
        [-0.489, -0.609, -0.611, -0.522, -0.140]
    ])
    
    fig, ax = plt.subplots(figsize=(7.5, 4.5), dpi=300)
    sns.heatmap(matrix, annot=True, fmt="+.3f", cmap="YlGn_r", xticklabels=buffers, yticklabels=municipios, 
                cbar_kws={'label': 'Coeficiente de Spearman (r)'}, ax=ax, annot_kws={"size": 10, "weight": "bold"})
    
    ax.set_title('Matriz de Asociación de Enfriamiento (Vegetación Baja Densidad)', fontsize=11, fontweight='bold', pad=15, color='#1f3864')
    plt.xticks(rotation=15)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[FIGS] Figure 4 (Heatmap) generated at: {output_path}")

def draw_flowchart(output_path):
    fig, ax = plt.subplots(figsize=(7, 6.5), dpi=300)
    
    steps = [
        "1. Discretización Territorial\nMalla regular de celdas de 30 metros",
        "2. Asignación Temática\nMunicipio, AGEB y Densidad por celda (Spatial Join)",
        "3. Cálculo Multiescala\nCoberturas en celda local y buffers circulares\n(100m, 250m, 500m y 1000m)",
        "4. Modelo Bivariado\nCoeficientes de correlación de Spearman (r)",
        "5. Segmentación territorial\nComparación por Municipio y Zona de Densidad",
        "6. Resultados y Síntesis\nTablas nativas, mapas y recomendaciones"
    ]
    
    box_style = dict(boxstyle="round,pad=0.5", fc="#1f3864", ec="none", alpha=0.9)
    
    for i, step in enumerate(steps):
        y = 5 - i
        # Draw Box
        ax.text(0.5, y, step, ha="center", va="center", color="white",
                weight="bold", fontsize=9, bbox=box_style)
        
        # Draw Arrow
        if i < 5:
            ax.annotate("", xy=(0.5, y - 0.72), xytext=(0.5, y - 0.28),
                        arrowprops=dict(arrowstyle="->", color="#c55a11", lw=2.5))
            
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.5, 5.5)
    ax.axis('off')
    
    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[FIGS] Figure 5 (Flowchart) generated at: {output_path}")

def main():
    figures_dir = r"reports/correlation_presentation_md/figures"
    os.makedirs(figures_dir, exist_ok=True)
    
    # 1. Generate new figures
    generate_vegetacion_line_chart(os.path.join(figures_dir, "vegetacion_baja_densidad_buffers.png"))
    generate_industria_line_chart(os.path.join(figures_dir, "industria_buffers.png"))
    generate_density_bar_chart(os.path.join(figures_dir, "comparacion_baja_alta_densidad.png"))
    generate_heatmap(os.path.join(figures_dir, "heatmap_resumen_coeficientes.png"))
    draw_flowchart(os.path.join(figures_dir, "diagrama_metodologico.png"))
    
    # 2. Reuse and copy existing maps
    src_density_map = r"outputs/figures/06_mapa_densidades_dw.png"
    dst_density_map = os.path.join(figures_dir, "mapa_zonas_densidad.png")
    if os.path.exists(src_density_map):
        shutil.copy(src_density_map, dst_density_map)
        print(f"[REUSE] Copied density map from {src_density_map} to {dst_density_map}")
    else:
        print(f"[WARN] Source density map not found: {src_density_map}")
        
    src_hotspots_map = r"outputs/05/hotspots_top3_overview_map.png"
    dst_hotspots_map = os.path.join(figures_dir, "hotspots_overview.png")
    if os.path.exists(src_hotspots_map):
        shutil.copy(src_hotspots_map, dst_hotspots_map)
        print(f"[REUSE] Copied hotspots map from {src_hotspots_map} to {dst_hotspots_map}")
    else:
        print(f"[WARN] Source hotspots map not found: {src_hotspots_map}")
        
    src_zoom_map = r"outputs/05/hotspot_ternium_zoom_map.png"
    dst_zoom_map = os.path.join(figures_dir, "hotspot_ternium_zoom.png")
    if os.path.exists(src_zoom_map):
        shutil.copy(src_zoom_map, dst_zoom_map)
        print(f"[REUSE] Copied hotspot zoom map from {src_zoom_map} to {dst_zoom_map}")
    else:
        print(f"[WARN] Source hotspot zoom map not found: {src_zoom_map}")

if __name__ == "__main__":
    main()
