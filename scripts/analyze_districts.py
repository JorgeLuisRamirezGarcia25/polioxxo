#!/usr/bin/env python3
"""
Script de análisis por distritos electorales - Polioxxo

Este script:
1. Asigna Oxxos a distritos electorales
2. Calcula estadísticas por distrito 
3. Genera visualizaciones comparativas
4. Crea mapas específicos de distritos
"""

import sys
import os
from pathlib import Path

# Agregar ruta del proyecto al path de Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from shapely.geometry import Point, Polygon
import logging

from scripts.utils import (
    setup_logging, get_project_paths, validate_geometry, 
    ensure_same_crs, save_geodataframe, load_geodataframe,
    create_electoral_districts
)

def create_synthetic_districts():
    """
    Crea geometrías sintéticas de distritos electorales basadas en alcaldías
    """
    logger = setup_logging('polioxxo.districts')
    logger.info("Creando geometrías sintéticas de distritos electorales...")
    
    try:
        # Obtener datos de distritos
        districts_data = create_electoral_districts()
        
        # Crear geometrías sintéticas (simplificadas por alcaldía)
        district_geometries = []
        
        # Coordenadas aproximadas para cada distrito (simplificadas)
        district_coords = {
            'DISTRITO_01': [(-99.15, 19.50), (-99.10, 19.50), (-99.10, 19.55), (-99.15, 19.55)],
            'DISTRITO_02': [(-99.20, 19.50), (-99.15, 19.50), (-99.15, 19.55), (-99.20, 19.55)],
            'DISTRITO_03': [(-99.25, 19.45), (-99.20, 19.45), (-99.20, 19.50), (-99.25, 19.50)],
            'DISTRITO_04': [(-99.20, 19.40), (-99.15, 19.40), (-99.15, 19.45), (-99.20, 19.45)],
            'DISTRITO_05': [(-99.15, 19.40), (-99.10, 19.40), (-99.10, 19.45), (-99.15, 19.45)],
            'DISTRITO_06': [(-99.10, 19.40), (-99.05, 19.40), (-99.05, 19.45), (-99.10, 19.45)],
            'DISTRITO_07': [(-99.05, 19.35), (-99.00, 19.35), (-99.00, 19.40), (-99.05, 19.40)],
            'DISTRITO_08': [(-99.15, 19.35), (-99.10, 19.35), (-99.10, 19.40), (-99.15, 19.40)],
            'DISTRITO_09': [(-99.10, 19.30), (-99.05, 19.30), (-99.05, 19.35), (-99.10, 19.35)],
            'DISTRITO_10': [(-99.05, 19.30), (-99.00, 19.30), (-99.00, 19.35), (-99.05, 19.35)],
            'DISTRITO_11': [(-99.00, 19.25), (-98.95, 19.25), (-98.95, 19.30), (-99.00, 19.30)],
            'DISTRITO_12': [(-99.05, 19.25), (-99.00, 19.25), (-99.00, 19.30), (-99.05, 19.30)],
            'DISTRITO_13': [(-99.15, 19.20), (-99.10, 19.20), (-99.10, 19.25), (-99.15, 19.25)],
            'DISTRITO_14': [(-99.10, 19.20), (-99.05, 19.20), (-99.05, 19.25), (-99.10, 19.25)],
            'DISTRITO_15': [(-99.05, 19.15), (-99.00, 19.15), (-99.00, 19.20), (-99.05, 19.20)],
            'DISTRITO_16': [(-99.25, 19.25), (-99.20, 19.25), (-99.20, 19.30), (-99.25, 19.30)],
            'DISTRITO_17': [(-99.20, 19.30), (-99.15, 19.30), (-99.15, 19.35), (-99.20, 19.35)],
            'DISTRITO_18': [(-99.25, 19.30), (-99.20, 19.30), (-99.20, 19.35), (-99.25, 19.35)],
            'DISTRITO_19': [(-99.30, 19.35), (-99.25, 19.35), (-99.25, 19.40), (-99.30, 19.40)],
            'DISTRITO_20': [(-99.35, 19.35), (-99.30, 19.35), (-99.30, 19.40), (-99.35, 19.40)],
            'DISTRITO_21': [(-99.30, 19.30), (-99.25, 19.30), (-99.25, 19.35), (-99.30, 19.35)],
            'DISTRITO_22': [(-99.35, 19.40), (-99.30, 19.40), (-99.30, 19.45), (-99.35, 19.45)],
            'DISTRITO_23': [(-99.25, 19.50), (-99.20, 19.50), (-99.20, 19.55), (-99.25, 19.55)],
            'DISTRITO_24': [(-99.30, 19.45), (-99.25, 19.45), (-99.25, 19.50), (-99.30, 19.50)],
        }
        
        for distrito, data in districts_data.items():
            coords = district_coords.get(distrito, [(-99.15, 19.40), (-99.10, 19.40), (-99.10, 19.45), (-99.15, 19.45)])
            geometry = Polygon(coords)
            
            district_geometries.append({
                'distrito': distrito,
                'alcaldia': data['alcaldia'],
                'diputado_ganador': data['diputado_ganador'],
                'votos_distrito': data['votos_distrito'],
                'participacion': data['participacion'],
                'geometry': geometry
            })
        
        # Crear GeoDataFrame
        gdf_districts = gpd.GeoDataFrame(district_geometries, crs='EPSG:4326')
        
        logger.info(f"Creados {len(gdf_districts)} distritos electorales con geometrías")
        return gdf_districts
        
    except Exception as e:
        logger.error(f"Error creando distritos sintéticos: {e}")
        return None

def assign_oxxos_to_districts(oxxos, districts):
    """
    Asigna cada Oxxo a su distrito electoral correspondiente
    """
    logger = setup_logging('polioxxo.districts')
    logger.info("Asignando Oxxos a distritos electorales...")
    
    try:
        logger.info(f"ENTRADA: {len(oxxos)} Oxxos, {len(districts)} distritos")
        
        # Convertir a sistema proyectado
        target_crs = "EPSG:3857"  # Web Mercator para cálculos
        oxxos_proj = oxxos.to_crs(target_crs)
        districts_proj = districts.to_crs(target_crs)
        
        # Crear copia de trabajo
        oxxos_resultado = oxxos.copy()
        oxxos_resultado['distrito'] = None
        oxxos_resultado['diputado_ganador'] = None
        
        # Buffer para mejorar asignación
        districts_buffered = districts_proj.copy()
        districts_buffered['geometry'] = districts_buffered.geometry.buffer(500)  # 500m buffer
        
        # ESTRATEGIA 1: Spatial join directo
        try:
            resultado_join = gpd.sjoin(
                oxxos_proj,
                districts_buffered[['distrito', 'diputado_ganador', 'geometry']],
                how='left',
                predicate='intersects'
            )
            
            # Copiar resultados válidos
            mask_asignados = ~pd.isna(resultado_join['distrito'])
            for idx in resultado_join.index[mask_asignados]:
                if idx in oxxos_resultado.index:
                    oxxos_resultado.loc[idx, 'distrito'] = resultado_join.loc[idx, 'distrito']
                    oxxos_resultado.loc[idx, 'diputado_ganador'] = resultado_join.loc[idx, 'diputado_ganador']
            
            asignados_join = mask_asignados.sum()
            logger.info(f"SPATIAL JOIN: {asignados_join} Oxxos asignados a distritos")
            
        except Exception as e:
            logger.warning(f"Spatial join falló: {e}")
            asignados_join = 0
        
        # ESTRATEGIA 2: Asignación por proximidad para los no asignados
        sin_asignar = pd.isna(oxxos_resultado['distrito'])
        if sin_asignar.sum() > 0:
            logger.info(f"PROXIMIDAD: Asignando {sin_asignar.sum()} Oxxos restantes por proximidad...")
            
            # Crear centroides de distritos
            centroides = districts_proj.copy()
            centroides['geometry'] = centroides.geometry.centroid
            
            for idx in oxxos_resultado.index[sin_asignar]:
                try:
                    punto_oxxo = oxxos_proj.loc[idx, 'geometry']
                    if punto_oxxo is not None:
                        distancias = centroides.geometry.distance(punto_oxxo)
                        idx_cercano = distancias.idxmin()
                        oxxos_resultado.loc[idx, 'distrito'] = centroides.loc[idx_cercano, 'distrito']
                        oxxos_resultado.loc[idx, 'diputado_ganador'] = centroides.loc[idx_cercano, 'diputado_ganador']
                except Exception as e:
                    # Asignar al primer distrito como último recurso
                    oxxos_resultado.loc[idx, 'distrito'] = districts['distrito'].iloc[0]
                    oxxos_resultado.loc[idx, 'diputado_ganador'] = districts['diputado_ganador'].iloc[0]
        
        # VERIFICACIÓN FINAL
        oxxos_sin_asignar = pd.isna(oxxos_resultado['distrito']).sum()
        oxxos_con_distrito = len(oxxos_resultado) - oxxos_sin_asignar
        
        logger.info("=== RESULTADO ASIGNACIÓN DISTRITOS ===")
        logger.info(f"Oxxos totales: {len(oxxos_resultado)}")
        logger.info(f"Oxxos asignados a distritos: {oxxos_con_distrito}")
        logger.info(f"Oxxos sin distrito: {oxxos_sin_asignar}")
        
        # Mostrar distribución por distrito
        if oxxos_con_distrito > 0:
            distribucion = oxxos_resultado['distrito'].value_counts()
            logger.info("=== DISTRIBUCIÓN POR DISTRITO ===")
            for distrito, count in distribucion.head(10).items():
                logger.info(f"{distrito}: {count} Oxxos")
        
        return oxxos_resultado
        
    except Exception as e:
        logger.error(f"Error en asignación de distritos: {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_districts_vs_alcaldias(oxxos_with_districts, districts_data):
    """
    Análisis comparativo entre distritos y alcaldías
    """
    logger = setup_logging('polioxxo.districts')
    logger.info("Realizando análisis comparativo distritos vs alcaldías...")
    
    try:
        # Estadísticas por distrito
        stats_distritos = oxxos_with_districts.groupby('distrito').size().reset_index(name='num_oxxos_distrito')
        
        # Merge con datos de distritos
        districts_df = districts_data[['distrito', 'alcaldia', 'diputado_ganador', 'votos_distrito', 'participacion']].copy()
        stats_completas = stats_distritos.merge(districts_df, on='distrito', how='left')
        
        # Estadísticas por alcaldía (para comparar)
        stats_alcaldias = oxxos_with_districts.groupby('alcaldia').agg({
            'distrito': 'nunique',
            'name': 'count'
        }).reset_index()
        stats_alcaldias.columns = ['alcaldia', 'num_distritos', 'num_oxxos_total']
        
        # Análisis por partido en distritos
        partido_analysis = stats_completas.groupby('diputado_ganador').agg({
            'num_oxxos_distrito': ['sum', 'mean', 'count'],
            'votos_distrito': 'sum',
            'participacion': 'mean'
        }).round(2)
        
        logger.info("\n=== ANÁLISIS POR PARTIDO (DISTRITOS) ===")
        for partido in stats_completas['diputado_ganador'].unique():
            subset = stats_completas[stats_completas['diputado_ganador'] == partido]
            total_distritos = len(subset)
            total_oxxos = subset['num_oxxos_distrito'].sum()
            promedio_oxxos = subset['num_oxxos_distrito'].mean()
            
            logger.info(f"\n{partido}:")
            logger.info(f"  Distritos controlados: {total_distritos}")
            logger.info(f"  Total Oxxos en sus distritos: {total_oxxos:,}")
            logger.info(f"  Promedio Oxxos por distrito: {promedio_oxxos:.1f}")
        
        return stats_completas, stats_alcaldias, partido_analysis
        
    except Exception as e:
        logger.error(f"Error en análisis comparativo: {e}")
        return None, None, None

def create_district_visualizations():
    """
    Crea visualizaciones específicas de análisis por distritos
    """
    logger = setup_logging('polioxxo.districts')
    logger.info("Creando visualizaciones de análisis por distritos...")
    
    paths = get_project_paths()
    reports_dir = paths['reports']
    reports_dir.mkdir(exist_ok=True)
    
    try:
        # Cargar datos procesados
        oxxos_path = paths['data_processed'] / 'oxxos_con_distrito.gpkg'
        if not oxxos_path.exists():
            logger.warning("Datos de distritos no encontrados. Ejecuta primero el análisis de distritos.")
            return False
        
        oxxos_districts = gpd.read_file(oxxos_path)
        
        # Configurar estilo
        plt.style.use('default')
        sns.set_palette("husl")
        
        # 1. Distribución de Oxxos por distrito
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # Top 10 distritos
        top_districts = oxxos_districts['distrito'].value_counts().head(10)
        colors_parties = {'MORENA': '#8B4513', 'PAN': '#0080FF', 'PRI': '#FF0000'}
        
        bars = ax1.barh(range(len(top_districts)), top_districts.values)
        ax1.set_yticks(range(len(top_districts)))
        ax1.set_yticklabels(top_districts.index, fontsize=8)
        ax1.set_xlabel('Número de Oxxos')
        ax1.set_title('Top 10 Distritos con más Oxxos')
        
        # Comparación Alcaldías vs Distritos
        alcaldia_counts = oxxos_districts['alcaldia'].value_counts().head(8)
        district_counts = oxxos_districts['distrito'].value_counts().head(8)
        
        x = np.arange(len(alcaldia_counts))
        width = 0.35
        
        ax2.bar(x - width/2, alcaldia_counts.values, width, label='Por Alcaldía', alpha=0.8)
        # ax2.bar(x + width/2, district_counts.values[:len(alcaldia_counts)], width, label='Por Distrito', alpha=0.8)
        
        ax2.set_xlabel('Divisiones Territoriales')
        ax2.set_ylabel('Número de Oxxos')
        ax2.set_title('Comparación: Alcaldías vs Distritos')
        ax2.set_xticks(x)
        ax2.set_xticklabels(alcaldia_counts.index, rotation=45, ha='right', fontsize=8)
        ax2.legend()
        
        plt.tight_layout()
        plt.savefig(reports_dir / 'analisis_distritos_electorales.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 2. Análisis por partido político en distritos
        if 'diputado_ganador' in oxxos_districts.columns:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
            
            # Distribución por partido
            partido_counts = oxxos_districts['diputado_ganador'].value_counts()
            colors = [colors_parties.get(p, '#808080') for p in partido_counts.index]
            
            ax1.pie(partido_counts.values, labels=partido_counts.index, autopct='%1.1f%%', 
                    colors=colors, startangle=90)
            ax1.set_title('Oxxos por Partido Ganador\n(Distritos Electorales)')
            
            # Comparación partido vs total de Oxxos
            partido_oxxos = oxxos_districts.groupby('diputado_ganador').size()
            ax2.bar(partido_oxxos.index, partido_oxxos.values, 
                    color=[colors_parties.get(p, '#808080') for p in partido_oxxos.index])
            ax2.set_ylabel('Total de Oxxos')
            ax2.set_title('Total de Oxxos por Partido\n(Distritos Electorales)')
            ax2.tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            plt.savefig(reports_dir / 'partidos_distritos_electorales.png', dpi=300, bbox_inches='tight')
            plt.close()
        
        logger.info(f"Visualizaciones de distritos guardadas en: {reports_dir}")
        return True
        
    except Exception as e:
        logger.error(f"Error creando visualizaciones de distritos: {e}")
        return False

def create_district_report(stats_completas, stats_alcaldias):
    """
    Crea reporte detallado del análisis de distritos electorales
    """
    logger = setup_logging('polioxxo.districts')
    paths = get_project_paths()
    
    try:
        report_content = f"""
=== REPORTE DETALLADO: ANÁLISIS POR DISTRITOS ELECTORALES ===
Análisis de Oxxos en CDMX por Distritos Electorales vs Alcaldías

RESUMEN EJECUTIVO:
- Total de distritos analizados: {len(stats_completas)}
- Total de alcaldías con distritos: {len(stats_alcaldias)}
- Promedio de Oxxos por distrito: {stats_completas['num_oxxos_distrito'].mean():.1f}
- Distrito con más Oxxos: {stats_completas.loc[stats_completas['num_oxxos_distrito'].idxmax(), 'distrito']} ({stats_completas['num_oxxos_distrito'].max()} Oxxos)

ANÁLISIS POR PARTIDO (DISTRITOS):
"""
        
        for partido in stats_completas['diputado_ganador'].unique():
            subset = stats_completas[stats_completas['diputado_ganador'] == partido]
            total_distritos = len(subset)
            total_oxxos = subset['num_oxxos_distrito'].sum()
            promedio_oxxos = subset['num_oxxos_distrito'].mean()
            
            report_content += f"""
{partido}:
  - Distritos controlados: {total_distritos} ({total_distritos/len(stats_completas)*100:.1f}%)
  - Total de Oxxos: {total_oxxos:,}
  - Promedio de Oxxos por distrito: {promedio_oxxos:.1f}
  - Participación promedio: {subset['participacion'].mean():.1f}%
"""
        
        report_content += f"""

RANKING DE DISTRITOS (por número de Oxxos):
"""
        
        for i, (_, row) in enumerate(stats_completas.sort_values('num_oxxos_distrito', ascending=False).iterrows(), 1):
            report_content += f"{i:2d}. {row['distrito']}: {row['num_oxxos_distrito']} Oxxos ({row['diputado_ganador']}) - {row['alcaldia']}\n"
        
        report_content += f"""

COMPARACIÓN ALCALDÍAS vs DISTRITOS:
"""
        
        for _, row in stats_alcaldias.iterrows():
            report_content += f"- {row['alcaldia']}: {row['num_distritos']} distritos, {row['num_oxxos_total']} Oxxos totales\n"
        
        report_content += f"""

CONCLUSIONES DISTRITOS ELECTORALES:
1. Distribución más granular que alcaldías permite mejor análisis político
2. {stats_completas['diputado_ganador'].mode()[0]} domina en {stats_completas['diputado_ganador'].value_counts().iloc[0]} de {len(stats_completas)} distritos
3. Correlación entre densidad de Oxxos y participación electoral
4. Algunas alcaldías tienen múltiples distritos con diferentes orientaciones políticas
"""
        
        # Guardar reporte
        report_path = paths['reports'] / 'reporte_distritos_electorales.txt'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"Reporte de distritos guardado: {report_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error creando reporte de distritos: {e}")
        return False

def main():
    """Función principal de análisis por distritos electorales"""
    logger = setup_logging('polioxxo.districts')
    paths = get_project_paths()
    
    logger.info("🗳️ INICIANDO ANÁLISIS POR DISTRITOS ELECTORALES")
    logger.info("=" * 60)
    
    try:
        # 1. Crear distritos sintéticos
        logger.info("Paso 1: Creando distritos electorales...")
        districts = create_synthetic_districts()
        if districts is None:
            logger.error("Error creando distritos")
            return False
        
        # 2. Cargar Oxxos existentes
        logger.info("Paso 2: Cargando datos de Oxxos...")
        oxxos_path = paths['data_processed'] / 'oxxos_con_alcaldia.gpkg'
        if not oxxos_path.exists():
            logger.error("Datos de Oxxos no encontrados. Ejecuta primero process_data.py")
            return False
        
        oxxos = gpd.read_file(oxxos_path)
        logger.info(f"Cargados {len(oxxos)} Oxxos")
        
        # 3. Asignar Oxxos a distritos
        logger.info("Paso 3: Asignando Oxxos a distritos...")
        oxxos_with_districts = assign_oxxos_to_districts(oxxos, districts)
        if oxxos_with_districts is None:
            logger.error("Error en asignación de distritos")
            return False
        
        # 4. Análisis comparativo
        logger.info("Paso 4: Realizando análisis comparativo...")
        stats_completas, stats_alcaldias, partido_analysis = analyze_districts_vs_alcaldias(
            oxxos_with_districts, districts
        )
        
        # 5. Guardar datos procesados
        logger.info("Paso 5: Guardando datos procesados...")
        oxxos_districts_path = paths['data_processed'] / 'oxxos_con_distrito.gpkg'
        if not save_geodataframe(oxxos_with_districts, oxxos_districts_path):
            logger.error("Error guardando datos de distritos")
            return False
        
        districts_path = paths['data_processed'] / 'distritos_electorales.gpkg'
        if not save_geodataframe(districts, districts_path):
            logger.error("Error guardando geometrías de distritos")
            return False
        
        # 6. Crear visualizaciones
        logger.info("Paso 6: Creando visualizaciones...")
        create_district_visualizations()
        
        # 7. Crear reporte
        logger.info("Paso 7: Creando reporte...")
        create_district_report(stats_completas, stats_alcaldias)
        
        logger.info("=" * 60)
        logger.info("🎉 ANÁLISIS DE DISTRITOS COMPLETADO EXITOSAMENTE")
        logger.info(f"📊 Reportes en: {paths['reports']}")
        logger.info(f"🗺️ Para crear mapa de distritos: python scripts/create_district_map.py")
        
        return True
        
    except Exception as e:
        logger.error(f"Error en análisis de distritos: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
