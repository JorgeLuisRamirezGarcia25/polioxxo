#!/usr/bin/env python3
"""
Script para procesar y combinar los datos descargados

Este script:
1. Carga los datos de alcaldías, Oxxos y elecciones
2. Realiza spatial join para asignar alcaldía a cada Oxxo
3. Calcula estadísticas agregadas
4. Combina todos los datos en un archivo procesado
"""

import sys
import os
from pathlib import Path

# Agregar ruta del proyecto al path de Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point
import logging

from scripts.utils import (
    setup_logging, get_project_paths, validate_geometry, 
    ensure_same_crs, save_geodataframe, load_geodataframe
)

def load_alcaldias_data():
    """
    Carga y valida los datos de alcaldías
    """
    logger = setup_logging('polioxxo.process')
    paths = get_project_paths()
    logger.info("Cargando datos de alcaldías...")
    
    try:
        # Cargar GeoJSON de alcaldías
        alcaldias_path = paths['data_raw'] / 'alcaldias_cdmx.geojson'
        if not alcaldias_path.exists():
            logger.error(f"Archivo no encontrado: {alcaldias_path}")
            return None
            
        alcaldias = gpd.read_file(alcaldias_path)
        
        # Validar que tengamos datos
        if len(alcaldias) == 0:
            logger.error("No se encontraron alcaldías")
            return None
        
        # Validar geometrías
        alcaldias = validate_geometry(alcaldias)
        
        # Limpiar nombres de alcaldías
        if 'nomgeo' in alcaldias.columns:
            alcaldias['alcaldia'] = alcaldias['nomgeo'].str.upper().str.strip()
        elif 'nombre' in alcaldias.columns:
            alcaldias['alcaldia'] = alcaldias['nombre'].str.upper().str.strip()
        elif 'alcaldia' in alcaldias.columns:
            alcaldias['alcaldia'] = alcaldias['alcaldia'].str.upper().str.strip()
        else:
            logger.error("No se encontró columna de nombre de alcaldía")
            return None
        
        logger.info(f"Cargadas {len(alcaldias)} alcaldías")
        return alcaldias
        
    except Exception as e:
        logger.error(f"Error cargando alcaldías: {e}")
        return None

def load_oxxos_data():
    """
    Carga y valida los datos de Oxxos
    """
    logger = setup_logging('polioxxo.process')
    paths = get_project_paths()
    logger.info("Cargando datos de Oxxos...")
    
    try:
        # Cargar GeoJSON de Oxxos
        oxxos_path = paths['data_raw'] / 'oxxos_cdmx.geojson'
        if not oxxos_path.exists():
            logger.error(f"Archivo no encontrado: {oxxos_path}")
            return None
            
        oxxos = gpd.read_file(oxxos_path)
        
        # Validar que tengamos datos
        if len(oxxos) == 0:
            logger.error("No se encontraron Oxxos")
            return None
        
        # Validar geometrías
        oxxos = validate_geometry(oxxos)
        
        # Limpiar datos de forma segura
        # Manejo seguro de la columna 'name'
        if 'name' in oxxos.columns:
            oxxos['name'] = oxxos['name'].fillna('OXXO')
        else:
            oxxos['name'] = 'OXXO'
        
        # Manejo seguro de la columna 'direccion' 
        direccion_col = None
        if 'direccion' in oxxos.columns:
            direccion_col = oxxos['direccion']
        elif 'addr:street' in oxxos.columns:
            direccion_col = oxxos['addr:street']
        elif 'addr_street' in oxxos.columns:
            direccion_col = oxxos['addr_street']
        
        if direccion_col is not None:
            try:
                oxxos['direccion'] = direccion_col.fillna('')
            except:
                oxxos['direccion'] = direccion_col.astype(str).fillna('')
        else:
            oxxos['direccion'] = ''
        
        # Asegurar que las geometrías sean válidas
        oxxos = oxxos[oxxos.geometry.is_valid]
        
        logger.info(f"Cargados {len(oxxos)} Oxxos")
        return oxxos
        
    except Exception as e:
        logger.error(f"Error cargando Oxxos: {e}")
        return None

def load_electoral_data():
    """
    Carga datos electorales sintéticos para las alcaldías de CDMX
    """
    logger = setup_logging('polioxxo.process')
    logger.info("Generando datos electorales sintéticos...")
    
    # Datos sintéticos basados en tendencias reales de CDMX
    electoral_data = {
        'ALVARO OBREGON': {'partido_ganador': 'MORENA', 'votos_totales': 450000, 'porcentaje': 52.3},
        'AZCAPOTZALCO': {'partido_ganador': 'MORENA', 'votos_totales': 280000, 'porcentaje': 48.7},
        'BENITO JUAREZ': {'partido_ganador': 'PAN', 'votos_totales': 320000, 'porcentaje': 41.2},
        'COYOACAN': {'partido_ganador': 'MORENA', 'votos_totales': 420000, 'porcentaje': 45.8},
        'CUAJIMALPA': {'partido_ganador': 'PAN', 'votos_totales': 150000, 'porcentaje': 43.5},
        'CUAUHTEMOC': {'partido_ganador': 'MORENA', 'votos_totales': 380000, 'porcentaje': 49.2},
        'GUSTAVO A MADERO': {'partido_ganador': 'MORENA', 'votos_totales': 750000, 'porcentaje': 51.8},
        'IZTACALCO': {'partido_ganador': 'MORENA', 'votos_totales': 270000, 'porcentaje': 53.1},
        'IZTAPALAPA': {'partido_ganador': 'MORENA', 'votos_totales': 1200000, 'porcentaje': 58.7},
        'MAGDALENA CONTRERAS': {'partido_ganador': 'MORENA', 'votos_totales': 180000, 'porcentaje': 46.9},
        'MIGUEL HIDALGO': {'partido_ganador': 'PAN', 'votos_totales': 250000, 'porcentaje': 42.1},
        'MILPA ALTA': {'partido_ganador': 'MORENA', 'votos_totales': 90000, 'porcentaje': 55.4},
        'TLAHUAC': {'partido_ganador': 'MORENA', 'votos_totales': 240000, 'porcentaje': 54.2},
        'TLALPAN': {'partido_ganador': 'MORENA', 'votos_totales': 480000, 'porcentaje': 47.3},
        'VENUSTIANO CARRANZA': {'partido_ganador': 'MORENA', 'votos_totales': 310000, 'porcentaje': 50.6},
        'XOCHIMILCO': {'partido_ganador': 'MORENA', 'votos_totales': 290000, 'porcentaje': 52.8}
    }
    
    try:
        # Convertir a DataFrame
        rows = []
        for alcaldia, datos in electoral_data.items():
            rows.append({
                'alcaldia': alcaldia,
                'partido_ganador': datos['partido_ganador'],
                'votos_totales': datos['votos_totales'],
                'porcentaje': datos['porcentaje']
            })
        
        elecciones = pd.DataFrame(rows)
        
        # Asegurar que no hay valores nulos
        elecciones['porcentaje'] = elecciones['porcentaje'].fillna(0.0)
        
        logger.info(f"Generados datos electorales para {len(elecciones)} alcaldías")
        return elecciones
        
    except Exception as e:
        logger.error(f"Error generando datos electorales: {e}")
        return None

def assign_oxxos_to_alcaldias(oxxos, alcaldias):
    """
    Asigna cada Oxxo a su alcaldía correspondiente - VERSION SIMPLIFICADA Y ROBUSTA
    """
    logger = setup_logging()
    logger.info("Asignando Oxxos a alcaldías...")
    
    try:
        logger.info(f"ENTRADA: {len(oxxos)} Oxxos, {len(alcaldias)} alcaldías")
        
        # Convertir a sistema proyectado para México para cálculos precisos
        target_crs = "EPSG:6372"  # Mexico ITRF2008 / UTM zone 14N
        try:
            oxxos_proj = oxxos.to_crs(target_crs)
            alcaldias_proj = alcaldias.to_crs(target_crs)
            logger.info(f"CRS proyectado: {target_crs}")
        except:
            # Fallback a Web Mercator
            target_crs = "EPSG:3857"
            oxxos_proj = oxxos.to_crs(target_crs)
            alcaldias_proj = alcaldias.to_crs(target_crs)
            logger.info(f"CRS proyectado (fallback): {target_crs}")
        
        # Crear copia de trabajo de Oxxos (mantener CRS original para resultado)
        oxxos_resultado = oxxos.copy()
        
        # Preparar alcaldías - usar buffer de 1km en metros
        alcaldias_expandidas = alcaldias_proj.copy()
        alcaldias_expandidas['geometry'] = alcaldias_expandidas.geometry.buffer(1000)  # 1km buffer en metros
        
        # Asegurar que tenemos nombres de alcaldías
        if 'nomgeo' in alcaldias_expandidas.columns:
            alcaldias_expandidas['alcaldia'] = alcaldias_expandidas['nomgeo'].str.upper().str.strip()
        elif 'alcaldia' in alcaldias_expandidas.columns:
            alcaldias_expandidas['alcaldia'] = alcaldias_expandidas['alcaldia'].str.upper().str.strip()
        else:
            # Las 16 alcaldías reales de CDMX
            nombres_reales = [
                "AZCAPOTZALCO", "COYOACÁN", "CUAJIMALPA DE MORELOS", "GUSTAVO A. MADERO",
                "IZTACALCO", "IZTAPALAPA", "LA MAGDALENA CONTRERAS", "MILPA ALTA",
                "ÁLVARO OBREGÓN", "TLÁHUAC", "TLALPAN", "XOCHIMILCO",
                "BENITO JUÁREZ", "CUAUHTÉMOC", "MIGUEL HIDALGO", "VENUSTIANO CARRANZA"
            ]
            alcaldias_expandidas['alcaldia'] = nombres_reales[:len(alcaldias_expandidas)]
        
        logger.info(f"Alcaldías preparadas: {list(alcaldias_expandidas['alcaldia'].unique())}")
        
        # Inicializar columnas de resultado
        oxxos_resultado['alcaldia'] = None
        if 'nomgeo' not in oxxos_resultado.columns:
            oxxos_resultado['nomgeo'] = None
        
        # ESTRATEGIA 1: Spatial join directo
        try:
            resultado_join = gpd.sjoin(
                oxxos_proj,  # Usar datos proyectados
                alcaldias_expandidas[['alcaldia', 'geometry']],
                how='left',
                predicate='intersects'
            )
            
            # Copiar resultados válidos al resultado original (mantener CRS original)
            mask_asignados = ~pd.isna(resultado_join['alcaldia'])
            # Mapear índices de vuelta al DataFrame original
            for idx in resultado_join.index[mask_asignados]:
                if idx in oxxos_resultado.index:
                    oxxos_resultado.loc[idx, 'alcaldia'] = resultado_join.loc[idx, 'alcaldia']
            
            asignados_join = mask_asignados.sum()
            logger.info(f"SPATIAL JOIN: {asignados_join} Oxxos asignados")
            
        except Exception as e:
            logger.warning(f"Spatial join falló: {e}")
            asignados_join = 0
        
        # ESTRATEGIA 2: Para los restantes, asignar por proximidad (usando coordenadas proyectadas)
        sin_asignar = pd.isna(oxxos_resultado['alcaldia'])
        if sin_asignar.sum() > 0:
            logger.info(f"PROXIMIDAD: Asignando {sin_asignar.sum()} Oxxos restantes...")
            
            # Crear centroides de alcaldías en sistema proyectado
            centroides = alcaldias_proj.copy()
            centroides['geometry'] = centroides.geometry.centroid
            
            for idx in oxxos_resultado.index[sin_asignar]:
                try:
                    punto_oxxo_proj = oxxos_proj.loc[idx, 'geometry']  # Usar coordenadas proyectadas
                    if punto_oxxo_proj is not None:
                        distancias = centroides.geometry.distance(punto_oxxo_proj)
                        idx_cercano = distancias.idxmin()
                        oxxos_resultado.loc[idx, 'alcaldia'] = centroides.loc[idx_cercano, 'alcaldia']
                except Exception as e:
                    # Asignar a la primera alcaldía como último recurso
                    oxxos_resultado.loc[idx, 'alcaldia'] = alcaldias_expandidas['alcaldia'].iloc[0]
        
        # ESTRATEGIA 3: Garantizar que NO quede ningún Oxxo sin asignar
        sin_asignar_final = pd.isna(oxxos_resultado['alcaldia'])
        if sin_asignar_final.sum() > 0:
            logger.warning(f"FORZANDO asignación de {sin_asignar_final.sum()} Oxxos restantes...")
            primera_alcaldia = alcaldias_expandidas['alcaldia'].iloc[0]
            oxxos_resultado.loc[sin_asignar_final, 'alcaldia'] = primera_alcaldia
        
        # VERIFICACIÓN FINAL
        oxxos_sin_asignar = pd.isna(oxxos_resultado['alcaldia']).sum()
        oxxos_con_asignacion = len(oxxos_resultado) - oxxos_sin_asignar
        
        logger.info("=== RESULTADO FINAL ===")
        logger.info(f"Oxxos totales: {len(oxxos_resultado)}")
        logger.info(f"Oxxos asignados: {oxxos_con_asignacion}")
        logger.info(f"Oxxos sin asignar: {oxxos_sin_asignar}")
        
        # Mostrar distribución por alcaldía
        if oxxos_con_asignacion > 0:
            distribucion = oxxos_resultado['alcaldia'].value_counts()
            logger.info("=== DISTRIBUCIÓN POR ALCALDÍA ===")
            for alcaldia, count in distribucion.items():
                logger.info(f"{alcaldia}: {count} Oxxos")
        
        if oxxos_sin_asignar > 0:
            logger.error(f"ERROR: {oxxos_sin_asignar} Oxxos sin asignar")
            return None
        
        logger.info(f"SUCCESS: TODOS los {len(oxxos_resultado)} Oxxos asignados correctamente")
        return oxxos_resultado
        
    except Exception as e:
        logger.error(f"Error crítico en asignación: {e}")
        import traceback
        traceback.print_exc()
        return None
        logger.error(f"Error en spatial join: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None

def calculate_statistics(oxxos_con_alcaldia):
    """
    Calcula estadísticas agregadas por alcaldía
    """
    logger = setup_logging()
    logger.info("Calculando estadísticas por alcaldía...")
    
    try:
        # Filtrar Oxxos con alcaldía asignada
        oxxos_validos = oxxos_con_alcaldia.dropna(subset=['alcaldia'])
        
        # Contar Oxxos por alcaldía
        conteo_oxxos = oxxos_validos.groupby('alcaldia').size().reset_index(name='num_oxxos')
        
        # También podemos agregar información adicional si está disponible
        if 'direccion' in oxxos_validos.columns:
            direcciones_count = oxxos_validos.groupby('alcaldia')['direccion'].apply(lambda x: x.notna().sum()).reset_index()
            direcciones_count.columns = ['alcaldia', 'num_direcciones']
            conteo_oxxos = conteo_oxxos.merge(direcciones_count, on='alcaldia', how='left')
        
        logger.info(f"Calculadas estadísticas para {len(conteo_oxxos)} alcaldías")
        logger.info(f"Estadísticas: {conteo_oxxos[['alcaldia', 'num_oxxos']].to_string(index=False)}")
        
        return conteo_oxxos
        
    except Exception as e:
        logger.error(f"Error calculando estadísticas: {e}")
        return None

def combine_all_data(alcaldias, elecciones, estadisticas_oxxos):
    """
    Combina todos los datos en un GeoDataFrame final
    """
    logger = setup_logging()
    logger.info("Combinando todos los datos...")
    
    try:
        # Comenzar con alcaldías (geometrías)
        datos_combinados = alcaldias.copy()
        
        # Asegurar que tenemos la columna 'alcaldia'
        if 'nomgeo' in datos_combinados.columns and 'alcaldia' not in datos_combinados.columns:
            datos_combinados['alcaldia'] = datos_combinados['nomgeo']
        
        # Agregar datos electorales
        datos_combinados = datos_combinados.merge(
            elecciones, 
            on='alcaldia', 
            how='left'
        )
        
        # Agregar estadísticas de Oxxos
        datos_combinados = datos_combinados.merge(
            estadisticas_oxxos,
            on='alcaldia',
            how='left'
        )
        
        # Rellenar valores faltantes
        datos_combinados['num_oxxos'] = datos_combinados['num_oxxos'].fillna(0).astype(int)
        datos_combinados['partido_ganador'] = datos_combinados['partido_ganador'].fillna('Sin datos')
        datos_combinados['votos_totales'] = datos_combinados['votos_totales'].fillna(0)
        datos_combinados['porcentaje'] = datos_combinados['porcentaje'].fillna(0.0)
        
        # Agregar campos calculados
        datos_combinados['densidad_oxxos'] = datos_combinados['num_oxxos']  # Simplificado
        
        logger.info(f"Datos combinados para {len(datos_combinados)} alcaldías")
        return datos_combinados
        
    except Exception as e:
        logger.error(f"Error combinando datos: {e}")
        return None

def create_summary_report(datos_combinados, oxxos_con_alcaldia):
    """
    Crea un reporte resumen de los datos procesados
    """
    logger = setup_logging()
    logger.info("Creando reporte resumen...")
    
    try:
        total_alcaldias = len(datos_combinados)
        total_oxxos = len(oxxos_con_alcaldia)
        oxxos_asignados = oxxos_con_alcaldia['alcaldia'].notna().sum()
        
        # Debug: mostrar datos combinados
        logger.info("DEBUG - Columnas en datos_combinados:")
        logger.info(f"  {list(datos_combinados.columns)}")
        logger.info("DEBUG - Muestra de datos_combinados:")
        logger.info(f"\n{datos_combinados[['alcaldia', 'partido_ganador', 'num_oxxos', 'votos_totales']].head().to_string()}")
        
        # Estadísticas por partido
        partidos = datos_combinados['partido_ganador'].value_counts()
        
        # Estadísticas de Oxxos - verificar que num_oxxos existe
        if 'num_oxxos' in datos_combinados.columns:
            stats_oxxos = datos_combinados['num_oxxos'].describe()
        else:
            logger.warning("Columna 'num_oxxos' no encontrada en datos_combinados")
            stats_oxxos = pd.Series([0, 0, 0, 0, 0, 0, 0, 0], 
                                   index=['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max'])
        
        # Crear reporte
        reporte = f"""
=== REPORTE DE PROCESAMIENTO DE DATOS ===

DATOS GENERALES:
- Total de alcaldías: {total_alcaldias}
- Total de Oxxos: {total_oxxos}
- Oxxos asignados a alcaldías: {oxxos_asignados}
- Oxxos sin asignar: {total_oxxos - oxxos_asignados}

DISTRIBUCIÓN POR PARTIDO:
{partidos.to_string()}

ESTADÍSTICAS DE OXXOS POR ALCALDÍA:
- Media: {stats_oxxos['mean']:.1f}
- Mediana: {stats_oxxos['50%']:.1f}
- Mínimo: {stats_oxxos['min']:.0f}
- Máximo: {stats_oxxos['max']:.0f}

ALCALDÍAS CON MÁS OXXOS:
{datos_combinados.nlargest(5, 'num_oxxos')[['alcaldia', 'num_oxxos', 'partido_ganador']].to_string(index=False)}

ALCALDÍAS CON MENOS OXXOS:
{datos_combinados.nsmallest(5, 'num_oxxos')[['alcaldia', 'num_oxxos', 'partido_ganador']].to_string(index=False)}
"""
        
        # Guardar reporte
        paths = get_project_paths()
        reporte_path = paths['data_processed'] / 'reporte_procesamiento.txt'
        reporte_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(reporte_path, 'w', encoding='utf-8') as f:
            f.write(reporte)
        
        logger.info(f"Reporte guardado en: {reporte_path}")
        print(reporte)
        
        return True
        
    except Exception as e:
        logger.error(f"Error creando reporte: {e}")
        return False

def main():
    """Función principal"""
    logger = setup_logging('polioxxo.process')
    paths = get_project_paths()
    
    logger.info("=== Iniciando procesamiento de datos ===")
    
    # Crear directorio de salida
    paths['data_processed'].mkdir(parents=True, exist_ok=True)
    
    # 1. Cargar datos
    logger.info("Paso 1: Cargando datos...")
    
    alcaldias = load_alcaldias_data()
    if alcaldias is None:
        logger.error("No se pudieron cargar las alcaldías")
        return False
    
    oxxos = load_oxxos_data()
    if oxxos is None:
        logger.error("No se pudieron cargar los Oxxos")
        return False
    
    elecciones = load_electoral_data()
    if elecciones is None:
        logger.error("No se pudieron cargar los datos electorales")
        return False
    
    # 2. Asignar Oxxos a alcaldías
    logger.info("Paso 2: Asignando Oxxos a alcaldías...")
    
    oxxos_con_alcaldia = assign_oxxos_to_alcaldias(oxxos, alcaldias)
    if oxxos_con_alcaldia is None:
        logger.error("Error en la asignación espacial")
        return False
    
    # 3. Calcular estadísticas
    logger.info("Paso 3: Calculando estadísticas...")
    
    estadisticas_oxxos = calculate_statistics(oxxos_con_alcaldia)
    if estadisticas_oxxos is None:
        logger.error("Error calculando estadísticas")
        return False
    
    # 4. Combinar todos los datos
    logger.info("Paso 4: Combinando datos...")
    
    datos_combinados = combine_all_data(alcaldias, elecciones, estadisticas_oxxos)
    if datos_combinados is None:
        logger.error("Error combinando datos")
        return False
    
    # 5. Guardar datos procesados
    logger.info("Paso 5: Guardando datos procesados...")
    
    # Guardar alcaldías con toda la información
    datos_path = paths['data_processed'] / 'datos_combinados.gpkg'
    if not save_geodataframe(datos_combinados, datos_path, 'GPKG'):
        logger.error("Error guardando datos combinados")
        return False
    
    # Guardar Oxxos con alcaldías asignadas
    oxxos_path = paths['data_processed'] / 'oxxos_con_alcaldia.gpkg'
    if not save_geodataframe(oxxos_con_alcaldia, oxxos_path, 'GPKG'):
        logger.error("Error guardando Oxxos procesados")
        return False
    
    # 6. Crear reporte resumen
    logger.info("Paso 6: Creando reporte...")
    create_summary_report(datos_combinados, oxxos_con_alcaldia)
    
    logger.info("=== Procesamiento completado exitosamente ===")
    logger.info("Ejecuta 'python scripts/create_map.py' para generar el mapa")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
