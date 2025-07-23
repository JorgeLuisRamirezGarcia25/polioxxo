#!/usr/bin/env python3
"""
Script de limpieza del proyecto Polioxxo
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import shutil
from pathlib import Path
import logging
import argparse
from scripts.utils import setup_logging, get_project_paths

def clean_raw_data():
    """Limpia datos raw"""
    logger = setup_logging('polioxxo.clean')
    paths = get_project_paths()
    
    raw_dir = paths['data_raw']
    if not raw_dir.exists():
        logger.info("No existe directorio de datos raw")
        return True
    
    try:
        # Contar archivos
        files = list(raw_dir.glob('*'))
        if not files:
            logger.info("No hay archivos raw para limpiar")
            return True
        
        logger.info(f"Limpiando {len(files)} archivos raw:")
        for file_path in files:
            if file_path.is_file():
                size_mb = file_path.stat().st_size / (1024 * 1024)
                logger.info(f"  - {file_path.name} ({size_mb:.1f} MB)")
                file_path.unlink()
            elif file_path.is_dir():
                logger.info(f"  - {file_path.name}/ (directorio)")
                shutil.rmtree(file_path)
        
        logger.info("✅ Datos raw limpiados")
        return True
        
    except Exception as e:
        logger.error(f"Error limpiando datos raw: {e}")
        return False

def clean_processed_data():
    """Limpia datos procesados"""
    logger = setup_logging('polioxxo.clean')
    paths = get_project_paths()
    
    processed_dir = paths['data_processed']
    if not processed_dir.exists():
        logger.info("No existe directorio de datos procesados")
        return True
    
    try:
        files = list(processed_dir.glob('*'))
        if not files:
            logger.info("No hay archivos procesados para limpiar")
            return True
        
        logger.info(f"Limpiando {len(files)} archivos procesados:")
        for file_path in files:
            if file_path.is_file():
                size_mb = file_path.stat().st_size / (1024 * 1024)
                logger.info(f"  - {file_path.name} ({size_mb:.1f} MB)")
                file_path.unlink()
        
        logger.info("✅ Datos procesados limpiados")
        return True
        
    except Exception as e:
        logger.error(f"Error limpiando datos procesados: {e}")
        return False

def clean_maps():
    """Limpia mapas generados"""
    logger = setup_logging('polioxxo.clean')
    paths = get_project_paths()
    
    maps_dir = paths['maps']
    if not maps_dir.exists():
        logger.info("No existe directorio de mapas")
        return True
    
    try:
        files = list(maps_dir.glob('*.html'))
        if not files:
            logger.info("No hay mapas para limpiar")
            return True
        
        logger.info(f"Limpiando {len(files)} mapas:")
        for file_path in files:
            size_mb = file_path.stat().st_size / (1024 * 1024)
            logger.info(f"  - {file_path.name} ({size_mb:.1f} MB)")
            file_path.unlink()
        
        logger.info("✅ Mapas limpiados")
        return True
        
    except Exception as e:
        logger.error(f"Error limpiando mapas: {e}")
        return False

def clean_reports():
    """Limpia reportes y visualizaciones"""
    logger = setup_logging('polioxxo.clean')
    paths = get_project_paths()
    
    reports_dir = paths['reports']
    if not reports_dir.exists():
        logger.info("No existe directorio de reportes")
        return True
    
    try:
        files = list(reports_dir.glob('*'))
        if not files:
            logger.info("No hay reportes para limpiar")
            return True
        
        logger.info(f"Limpiando {len(files)} archivos de reportes:")
        for file_path in files:
            if file_path.is_file():
                size_mb = file_path.stat().st_size / (1024 * 1024)
                logger.info(f"  - {file_path.name} ({size_mb:.2f} MB)")
                file_path.unlink()
        
        logger.info("✅ Reportes limpiados")
        return True
        
    except Exception as e:
        logger.error(f"Error limpiando reportes: {e}")
        return False

def clean_logs():
    """Limpia archivos de log"""
    logger = setup_logging('polioxxo.clean')
    paths = get_project_paths()
    
    logs_dir = paths['logs']
    if not logs_dir.exists():
        logger.info("No existe directorio de logs")
        return True
    
    try:
        files = list(logs_dir.glob('*.log'))
        if not files:
            logger.info("No hay logs para limpiar")
            return True
        
        logger.info(f"Limpiando {len(files)} archivos de log:")
        for file_path in files:
            size_mb = file_path.stat().st_size / (1024 * 1024)
            logger.info(f"  - {file_path.name} ({size_mb:.2f} MB)")
            file_path.unlink()
        
        logger.info("✅ Logs limpiados")
        return True
        
    except Exception as e:
        logger.error(f"Error limpiando logs: {e}")
        return False

def clean_cache():
    """Limpia archivos de cache de Python"""
    logger = setup_logging('polioxxo.clean')
    paths = get_project_paths()
    
    project_root = paths['project_root']
    
    try:
        # Limpiar __pycache__
        pycache_dirs = list(project_root.glob('**/__pycache__'))
        if pycache_dirs:
            logger.info(f"Limpiando {len(pycache_dirs)} directorios __pycache__:")
            for pycache_dir in pycache_dirs:
                logger.info(f"  - {pycache_dir.relative_to(project_root)}")
                shutil.rmtree(pycache_dir)
        
        # Limpiar archivos .pyc
        pyc_files = list(project_root.glob('**/*.pyc'))
        if pyc_files:
            logger.info(f"Limpiando {len(pyc_files)} archivos .pyc")
            for pyc_file in pyc_files:
                pyc_file.unlink()
        
        if pycache_dirs or pyc_files:
            logger.info("✅ Cache de Python limpiado")
        else:
            logger.info("No hay cache para limpiar")
        
        return True
        
    except Exception as e:
        logger.error(f"Error limpiando cache: {e}")
        return False

def show_disk_usage():
    """Muestra el uso de disco antes y después de la limpieza"""
    logger = setup_logging('polioxxo.clean')
    paths = get_project_paths()
    
    try:
        total_size = 0
        category_sizes = {}
        
        # Calcular tamaños por categoría
        for category, path in paths.items():
            if category == 'project_root':
                continue
            
            if path.exists():
                size = sum(f.stat().st_size for f in path.glob('**/*') if f.is_file())
                category_sizes[category] = size
                total_size += size
        
        logger.info("📊 USO DE DISCO POR CATEGORÍA:")
        for category, size in category_sizes.items():
            size_mb = size / (1024 * 1024)
            logger.info(f"  {category}: {size_mb:.2f} MB")
        
        total_mb = total_size / (1024 * 1024)
        logger.info(f"  TOTAL: {total_mb:.2f} MB")
        
        return total_size
        
    except Exception as e:
        logger.error(f"Error calculando uso de disco: {e}")
        return 0

def main():
    """Función principal de limpieza"""
    parser = argparse.ArgumentParser(description='Limpieza del proyecto Polioxxo')
    parser.add_argument('--all', action='store_true', help='Limpiar todo')
    parser.add_argument('--raw', action='store_true', help='Limpiar datos raw')
    parser.add_argument('--processed', action='store_true', help='Limpiar datos procesados')
    parser.add_argument('--maps', action='store_true', help='Limpiar mapas')
    parser.add_argument('--reports', action='store_true', help='Limpiar reportes')
    parser.add_argument('--logs', action='store_true', help='Limpiar logs')
    parser.add_argument('--cache', action='store_true', help='Limpiar cache')
    parser.add_argument('--dry-run', action='store_true', help='Solo mostrar qué se limpiaría')
    
    args = parser.parse_args()
    
    logger = setup_logging('polioxxo.clean')
    
    logger.info("🧹 INICIANDO LIMPIEZA DEL PROYECTO")
    logger.info("=" * 40)
    
    # Mostrar uso inicial
    initial_size = show_disk_usage()
    
    if args.dry_run:
        logger.info("⚠️ MODO DRY-RUN - Solo mostrando qué se limpiaría")
        return True
    
    success = True
    
    try:
        # Determinar qué limpiar
        clean_all = args.all or not any([args.raw, args.processed, args.maps, args.reports, args.logs, args.cache])
        
        if clean_all or args.cache:
            success &= clean_cache()
        
        if clean_all or args.logs:
            success &= clean_logs()
        
        if clean_all or args.raw:
            success &= clean_raw_data()
        
        if clean_all or args.processed:
            success &= clean_processed_data()
        
        if clean_all or args.maps:
            success &= clean_maps()
        
        if clean_all or args.reports:
            success &= clean_reports()
        
        # Mostrar uso final
        logger.info("\n" + "=" * 40)
        final_size = show_disk_usage()
        
        if initial_size > 0:
            saved_mb = (initial_size - final_size) / (1024 * 1024)
            if saved_mb > 0:
                logger.info(f"💾 Espacio liberado: {saved_mb:.2f} MB")
            else:
                logger.info("💾 No se liberó espacio")
        
        if success:
            logger.info("🎉 LIMPIEZA COMPLETADA EXITOSAMENTE")
        else:
            logger.warning("⚠️ LIMPIEZA COMPLETADA CON ERRORES")
        
        return success
        
    except Exception as e:
        logger.error(f"Error en limpieza: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
