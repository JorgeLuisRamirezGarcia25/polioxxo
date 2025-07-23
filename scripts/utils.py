#!/usr/bin/env python3
"""
Utilidades comunes para el proyecto polioxxo
"""

import logging
import geopandas as gpd
import pandas as pd
from pathlib import Path

def setup_logging(name='polioxxo', level=logging.INFO):
    """
    Configura logging consistente para todos los scripts
    """
    # Asegurar que existe el directorio de logs
    base_dir = Path(__file__).parent.parent
    logs_dir = base_dir / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    log_file = logs_dir / 'polioxxo.log'
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding='utf-8')
        ]
    )
    return logging.getLogger(name)

def ensure_same_crs(gdf1, gdf2, target_crs='EPSG:4326'):
    """
    Asegura que dos GeoDataFrames tengan el mismo CRS
    """
    if gdf1.crs != target_crs:
        gdf1 = gdf1.to_crs(target_crs)
    if gdf2.crs != target_crs:
        gdf2 = gdf2.to_crs(target_crs)
    return gdf1, gdf2

def validate_geometry(gdf):
    """
    Valida y repara geometrías en un GeoDataFrame
    """
    logger = logging.getLogger('polioxxo.utils')
    
    # Contar geometrías válidas
    valid_geoms = gdf.geometry.is_valid.sum()
    total_geoms = len(gdf)
    
    logger.info(f"Geometrías válidas: {valid_geoms}/{total_geoms}")
    
    if valid_geoms < total_geoms:
        logger.info("Reparando geometrías inválidas...")
        gdf.loc[~gdf.geometry.is_valid, 'geometry'] = gdf.loc[~gdf.geometry.is_valid, 'geometry'].buffer(0)
        
        # Verificar reparación
        valid_after = gdf.geometry.is_valid.sum()
        logger.info(f"Geometrías válidas después de reparación: {valid_after}/{total_geoms}")
    
    return gdf

def create_project_structure():
    """
    Crea la estructura de directorios del proyecto
    """
    base_dir = Path(__file__).parent.parent
    
    directories = [
        "data/raw",
        "data/processed", 
        "data/external",
        "maps",
        "reports",
        "logs"
    ]
    
    for directory in directories:
        (base_dir / directory).mkdir(parents=True, exist_ok=True)
    
    return base_dir

def get_project_paths():
    """
    Retorna diccionario con paths importantes del proyecto
    """
    base_dir = Path(__file__).parent.parent
    
    return {
        'base': base_dir,
        'data_raw': base_dir / "data" / "raw",
        'data_processed': base_dir / "data" / "processed",
        'data_external': base_dir / "data" / "external",
        'maps': base_dir / "maps",
        'reports': base_dir / "reports",
        'scripts': base_dir / "scripts",
        'logs': base_dir / "logs"
    }

def save_geodataframe(gdf, filepath, driver='GPKG'):
    """
    Guarda un GeoDataFrame con manejo de errores
    """
    logger = logging.getLogger('polioxxo.utils')
    
    try:
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        gdf.to_file(filepath, driver=driver)
        logger.info(f"Archivo guardado: {filepath}")
        return True
        
    except Exception as e:
        logger.error(f"Error guardando {filepath}: {e}")
        return False

def load_geodataframe(filepath):
    """
    Carga un GeoDataFrame con manejo de errores
    """
    logger = logging.getLogger('polioxxo.utils')
    
    try:
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {filepath}")
        
        gdf = gpd.read_file(filepath)
        logger.info(f"Archivo cargado: {filepath} ({len(gdf)} registros)")
        return gdf
        
    except Exception as e:
        logger.error(f"Error cargando {filepath}: {e}")
        return None

def create_electoral_districts():
    """
    Crea datos sintéticos de distritos electorales de CDMX
    """
    logger = logging.getLogger('polioxxo.utils')
    
    # 24 Distritos electorales locales de CDMX con datos sintéticos
    districts_data = {
        'DISTRITO_01': {'alcaldia': 'GUSTAVO A MADERO', 'diputado_ganador': 'MORENA', 'votos_distrito': 95000, 'participacion': 58.2},
        'DISTRITO_02': {'alcaldia': 'GUSTAVO A MADERO', 'diputado_ganador': 'MORENA', 'votos_distrito': 87000, 'participacion': 55.8},
        'DISTRITO_03': {'alcaldia': 'AZCAPOTZALCO', 'diputado_ganador': 'MORENA', 'votos_distrito': 89000, 'participacion': 61.4},
        'DISTRITO_04': {'alcaldia': 'MIGUEL HIDALGO', 'diputado_ganador': 'PAN', 'votos_distrito': 78000, 'participacion': 67.2},
        'DISTRITO_05': {'alcaldia': 'CUAUHTEMOC', 'diputado_ganador': 'MORENA', 'votos_distrito': 82000, 'participacion': 63.8},
        'DISTRITO_06': {'alcaldia': 'VENUSTIANO CARRANZA', 'diputado_ganador': 'MORENA', 'votos_distrito': 91000, 'participacion': 59.7},
        'DISTRITO_07': {'alcaldia': 'IZTACALCO', 'diputado_ganador': 'MORENA', 'votos_distrito': 85000, 'participacion': 62.1},
        'DISTRITO_08': {'alcaldia': 'BENITO JUAREZ', 'diputado_ganador': 'PAN', 'votos_distrito': 93000, 'participacion': 71.5},
        'DISTRITO_09': {'alcaldia': 'IZTAPALAPA', 'diputado_ganador': 'MORENA', 'votos_distrito': 105000, 'participacion': 54.3},
        'DISTRITO_10': {'alcaldia': 'IZTAPALAPA', 'diputado_ganador': 'MORENA', 'votos_distrito': 98000, 'participacion': 52.8},
        'DISTRITO_11': {'alcaldia': 'IZTAPALAPA', 'diputado_ganador': 'MORENA', 'votos_distrito': 102000, 'participacion': 53.6},
        'DISTRITO_12': {'alcaldia': 'IZTAPALAPA', 'diputado_ganador': 'MORENA', 'votos_distrito': 96000, 'participacion': 51.9},
        'DISTRITO_13': {'alcaldia': 'XOCHIMILCO', 'diputado_ganador': 'MORENA', 'votos_distrito': 79000, 'participacion': 56.4},
        'DISTRITO_14': {'alcaldia': 'TLAHUAC', 'diputado_ganador': 'MORENA', 'votos_distrito': 73000, 'participacion': 58.7},
        'DISTRITO_15': {'alcaldia': 'MILPA ALTA', 'diputado_ganador': 'MORENA', 'votos_distrito': 48000, 'participacion': 61.2},
        'DISTRITO_16': {'alcaldia': 'TLALPAN', 'diputado_ganador': 'MORENA', 'votos_distrito': 92000, 'participacion': 60.3},
        'DISTRITO_17': {'alcaldia': 'COYOACAN', 'diputado_ganador': 'MORENA', 'votos_distrito': 88000, 'participacion': 65.8},
        'DISTRITO_18': {'alcaldia': 'COYOACAN', 'diputado_ganador': 'MORENA', 'votos_distrito': 91000, 'participacion': 64.2},
        'DISTRITO_19': {'alcaldia': 'ALVARO OBREGON', 'diputado_ganador': 'MORENA', 'votos_distrito': 94000, 'participacion': 59.1},
        'DISTRITO_20': {'alcaldia': 'ALVARO OBREGON', 'diputado_ganador': 'MORENA', 'votos_distrito': 87000, 'participacion': 57.8},
        'DISTRITO_21': {'alcaldia': 'MAGDALENA CONTRERAS', 'diputado_ganador': 'MORENA', 'votos_distrito': 71000, 'participacion': 60.9},
        'DISTRITO_22': {'alcaldia': 'CUAJIMALPA', 'diputado_ganador': 'PAN', 'votos_distrito': 65000, 'participacion': 68.4},
        'DISTRITO_23': {'alcaldia': 'GUSTAVO A MADERO', 'diputado_ganador': 'MORENA', 'votos_distrito': 89000, 'participacion': 56.7},
        'DISTRITO_24': {'alcaldia': 'AZCAPOTZALCO', 'diputado_ganador': 'MORENA', 'votos_distrito': 81000, 'participacion': 59.3},
    }
    
    logger.info(f"Creados {len(districts_data)} distritos electorales")
    return districts_data

def create_summary_report(data_dict, output_path):
    """
    Crea un reporte resumen del proyecto
    """
    logger = logging.getLogger('polioxxo.utils')
    
    try:
        report_lines = [
            "=" * 60,
            "REPORTE RESUMEN - POLIOXXO",
            "Análisis de Oxxos en CDMX por Alcaldías y Distritos Electorales",
            "=" * 60,
            ""
        ]
        
        for section, data in data_dict.items():
            report_lines.append(f"{section}:")
            if isinstance(data, dict):
                for key, value in data.items():
                    report_lines.append(f"  - {key}: {value}")
            else:
                report_lines.append(f"  {data}")
            report_lines.append("")
        
        report_content = "\n".join(report_lines)
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"Reporte creado: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error creando reporte: {e}")
        return False
