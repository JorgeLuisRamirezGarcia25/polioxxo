#!/usr/bin/env python3
"""
Script de análisis estadístico avanzado de Oxxos en CDMX
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import logging
from scripts.utils import setup_logging, get_project_paths
import numpy as np

def load_processed_data():
    """Carga los datos procesados"""
    logger = setup_logging('polioxxo.analyze')
    paths = get_project_paths()
    
    try:
        # Cargar datos combinados
        datos_path = paths['data_processed'] / 'datos_combinados.gpkg'
        if not datos_path.exists():
            raise FileNotFoundError(f"Datos no encontrados: {datos_path}")
        
        datos = gpd.read_file(datos_path)
        logger.info(f"Cargados datos de {len(datos)} alcaldías")
        
        # Cargar Oxxos
        oxxos_path = paths['data_processed'] / 'oxxos_con_alcaldia.gpkg'
        if not oxxos_path.exists():
            raise FileNotFoundError(f"Oxxos no encontrados: {oxxos_path}")
        
        oxxos = gpd.read_file(oxxos_path)
        logger.info(f"Cargados {len(oxxos)} Oxxos")
        
        return datos, oxxos
        
    except Exception as e:
        logger.error(f"Error cargando datos: {e}")
        return None, None

def analyze_distribution():
    """Analiza la distribución de Oxxos por alcaldía"""
    logger = setup_logging('polioxxo.analyze')
    
    datos, oxxos = load_processed_data()
    if datos is None or oxxos is None:
        return False
    
    logger.info("=== ANÁLISIS DE DISTRIBUCIÓN ===")
    
    # Estadísticas básicas
    stats = {
        'total_oxxos': len(oxxos),
        'total_alcaldias': len(datos),
        'promedio_oxxos': datos['num_oxxos'].mean(),
        'mediana_oxxos': datos['num_oxxos'].median(),
        'max_oxxos': datos['num_oxxos'].max(),
        'min_oxxos': datos['num_oxxos'].min(),
        'desv_std': datos['num_oxxos'].std()
    }
    
    for key, value in stats.items():
        if isinstance(value, float):
            logger.info(f"{key}: {value:.2f}")
        else:
            logger.info(f"{key}: {value:,}")
    
    # Top 5 alcaldías
    top_5 = datos.nlargest(5, 'num_oxxos')[['alcaldia', 'num_oxxos', 'partido_ganador']]
    logger.info("\nTOP 5 ALCALDÍAS CON MÁS OXXOS:")
    for _, row in top_5.iterrows():
        logger.info(f"  {row['alcaldia']}: {row['num_oxxos']} ({row['partido_ganador']})")
    
    # Bottom 5 alcaldías
    bottom_5 = datos.nsmallest(5, 'num_oxxos')[['alcaldia', 'num_oxxos', 'partido_ganador']]
    logger.info("\nTOP 5 ALCALDÍAS CON MENOS OXXOS:")
    for _, row in bottom_5.iterrows():
        logger.info(f"  {row['alcaldia']}: {row['num_oxxos']} ({row['partido_ganador']})")
    
    return stats

def analyze_political_correlation():
    """Analiza correlación entre partidos políticos y número de Oxxos"""
    logger = setup_logging('polioxxo.analyze')
    
    datos, _ = load_processed_data()
    if datos is None:
        return False
    
    logger.info("\n=== ANÁLISIS POR PARTIDO POLÍTICO ===")
    
    # Análisis por partido
    por_partido = datos.groupby('partido_ganador').agg({
        'num_oxxos': ['count', 'sum', 'mean', 'std'],
        'votos_totales': ['mean', 'sum']
    }).round(2)
    
    logger.info("\nESTADÍSTICAS POR PARTIDO:")
    for partido in datos['partido_ganador'].unique():
        subset = datos[datos['partido_ganador'] == partido]
        alcaldias_count = len(subset)
        total_oxxos = subset['num_oxxos'].sum()
        promedio_oxxos = subset['num_oxxos'].mean()
        
        logger.info(f"\n{partido}:")
        logger.info(f"  Alcaldías: {alcaldias_count}")
        logger.info(f"  Total Oxxos: {total_oxxos:,}")
        logger.info(f"  Promedio Oxxos por alcaldía: {promedio_oxxos:.1f}")
    
    return por_partido

def create_visualizations():
    """Crea visualizaciones del análisis"""
    logger = setup_logging('polioxxo.analyze')
    
    datos, _ = load_processed_data()
    if datos is None:
        return False
    
    paths = get_project_paths()
    plots_dir = paths['reports'] 
    plots_dir.mkdir(exist_ok=True)
    
    # Configurar estilo
    plt.style.use('default')
    sns.set_palette("husl")
    
    try:
        # 1. Distribución de Oxxos por alcaldía
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Gráfico de barras
        datos_sorted = datos.sort_values('num_oxxos', ascending=True)
        bars = ax1.barh(datos_sorted['alcaldia'], datos_sorted['num_oxxos'])
        ax1.set_xlabel('Número de Oxxos')
        ax1.set_title('Distribución de Oxxos por Alcaldía')
        ax1.tick_params(axis='y', labelsize=8)
        
        # Colorear por partido
        colors = {'MORENA': '#8B4513', 'PAN': '#0080FF', 'PRI': '#FF0000'}
        for i, (bar, partido) in enumerate(zip(bars, datos_sorted['partido_ganador'])):
            bar.set_color(colors.get(partido, '#808080'))
        
        # Histograma
        ax2.hist(datos['num_oxxos'], bins=8, edgecolor='black', alpha=0.7)
        ax2.set_xlabel('Número de Oxxos')
        ax2.set_ylabel('Frecuencia')
        ax2.set_title('Histograma de Distribución')
        ax2.axvline(datos['num_oxxos'].mean(), color='red', linestyle='--', label=f'Media: {datos["num_oxxos"].mean():.1f}')
        ax2.legend()
        
        plt.tight_layout()
        plt.savefig(plots_dir / 'distribucion_oxxos.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 2. Análisis por partido político
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Total de Oxxos por partido
        partido_stats = datos.groupby('partido_ganador')['num_oxxos'].sum().sort_values(ascending=False)
        ax1.bar(partido_stats.index, partido_stats.values, color=[colors.get(p, '#808080') for p in partido_stats.index])
        ax1.set_ylabel('Total de Oxxos')
        ax1.set_title('Total de Oxxos por Partido')
        
        # Número de alcaldías por partido
        alcaldias_por_partido = datos['partido_ganador'].value_counts()
        ax2.pie(alcaldias_por_partido.values, labels=alcaldias_por_partido.index, autopct='%1.1f%%', 
                colors=[colors.get(p, '#808080') for p in alcaldias_por_partido.index])
        ax2.set_title('Distribución de Alcaldías por Partido')
        
        plt.tight_layout()
        plt.savefig(plots_dir / 'analisis_partidos.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 3. Correlación entre votos y Oxxos
        plt.figure(figsize=(10, 6))
        
        # Scatter plot
        for partido in datos['partido_ganador'].unique():
            subset = datos[datos['partido_ganador'] == partido]
            plt.scatter(subset['votos_totales'], subset['num_oxxos'], 
                       label=partido, alpha=0.7, s=60, color=colors.get(partido, '#808080'))
        
        plt.xlabel('Votos Totales')
        plt.ylabel('Número de Oxxos')
        plt.title('Relación entre Votos Totales y Número de Oxxos')
        plt.legend()
        
        # Línea de tendencia
        z = np.polyfit(datos['votos_totales'], datos['num_oxxos'], 1)
        p = np.poly1d(z)
        plt.plot(datos['votos_totales'], p(datos['votos_totales']), 
                "r--", alpha=0.8, label=f'Tendencia (R² = {np.corrcoef(datos["votos_totales"], datos["num_oxxos"])[0,1]**2:.3f})')
        
        plt.tight_layout()
        plt.savefig(plots_dir / 'correlacion_votos_oxxos.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Visualizaciones guardadas en: {plots_dir}")
        return True
        
    except Exception as e:
        logger.error(f"Error creando visualizaciones: {e}")
        return False

def create_detailed_report():
    """Crea un reporte detallado del análisis"""
    logger = setup_logging('polioxxo.analyze')
    
    datos, oxxos = load_processed_data()
    if datos is None or oxxos is None:
        return False
    
    paths = get_project_paths()
    
    # Realizar análisis
    stats = analyze_distribution()
    political_analysis = analyze_political_correlation()
    
    # Crear reporte
    report_content = f"""
=== REPORTE DETALLADO DE ANÁLISIS ===
Análisis de Oxxos en CDMX por Alcaldías y Partidos Políticos

RESUMEN EJECUTIVO:
- Total de Oxxos analizados: {len(oxxos):,}
- Total de alcaldías: {len(datos)}
- Promedio de Oxxos por alcaldía: {datos['num_oxxos'].mean():.1f}
- Alcaldía con más Oxxos: {datos.loc[datos['num_oxxos'].idxmax(), 'alcaldia']} ({datos['num_oxxos'].max()} Oxxos)
- Alcaldía with menos Oxxos: {datos.loc[datos['num_oxxos'].idxmin(), 'alcaldia']} ({datos['num_oxxos'].min()} Oxxos)

DISTRIBUCIÓN POR PARTIDO:
"""
    
    for partido in datos['partido_ganador'].unique():
        subset = datos[datos['partido_ganador'] == partido]
        total_alcaldias = len(subset)
        total_oxxos = subset['num_oxxos'].sum()
        promedio_oxxos = subset['num_oxxos'].mean()
        
        report_content += f"""
{partido}:
  - Alcaldías controladas: {total_alcaldias} ({total_alcaldias/len(datos)*100:.1f}%)
  - Total de Oxxos: {total_oxxos:,} ({total_oxxos/len(oxxos)*100:.1f}%)
  - Promedio de Oxxos por alcaldía: {promedio_oxxos:.1f}
"""
    
    report_content += f"""

RANKING DE ALCALDÍAS (por número de Oxxos):
"""
    
    for i, (_, row) in enumerate(datos.sort_values('num_oxxos', ascending=False).iterrows(), 1):
        report_content += f"{i:2d}. {row['alcaldia']}: {row['num_oxxos']} Oxxos ({row['partido_ganador']})\n"
    
    report_content += f"""

ESTADÍSTICAS DESCRIPTIVAS:
- Media: {datos['num_oxxos'].mean():.2f}
- Mediana: {datos['num_oxxos'].median():.2f}
- Desviación estándar: {datos['num_oxxos'].std():.2f}
- Mínimo: {datos['num_oxxos'].min()}
- Máximo: {datos['num_oxxos'].max()}
- Rango intercuartílico: {datos['num_oxxos'].quantile(0.75) - datos['num_oxxos'].quantile(0.25):.2f}

CONCLUSIONES:
1. Hay una distribución desigual de Oxxos entre alcaldías
2. {datos['partido_ganador'].mode()[0]} controla la mayoría de alcaldías ({datos['partido_ganador'].value_counts().iloc[0]} de {len(datos)})
3. La correlación entre votos y número de Oxxos es: {np.corrcoef(datos['votos_totales'], datos['num_oxxos'])[0,1]:.3f}
"""
    
    # Guardar reporte
    report_path = paths['reports'] / 'reporte_analisis_detallado.txt'
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        logger.info(f"Reporte detallado guardado: {report_path}")
        return True
    except Exception as e:
        logger.error(f"Error guardando reporte: {e}")
        return False

def main():
    """Función principal de análisis"""
    logger = setup_logging('polioxxo.analyze')
    
    logger.info("🔍 INICIANDO ANÁLISIS ESTADÍSTICO DETALLADO")
    logger.info("=" * 50)
    
    try:
        # Realizar análisis
        stats = analyze_distribution()
        if not stats:
            logger.error("Fallo en análisis de distribución")
            return False
        
        political_analysis = analyze_political_correlation()
        if political_analysis is False:
            logger.error("Fallo en análisis político")
            return False
        
        # Crear visualizaciones
        if create_visualizations():
            logger.info("✅ Visualizaciones creadas")
        else:
            logger.warning("⚠️ Error creando visualizaciones")
        
        # Crear reporte detallado
        if create_detailed_report():
            logger.info("✅ Reporte detallado creado")
        else:
            logger.warning("⚠️ Error creando reporte")
        
        logger.info("=" * 50)
        logger.info("🎉 ANÁLISIS COMPLETADO EXITOSAMENTE")
        
        paths = get_project_paths()
        logger.info(f"📊 Reportes en: {paths['reports']}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error en análisis: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
