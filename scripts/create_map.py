#!/usr/bin/env python3
"""
Script para crear mapa interactivo de Oxxos en CDMX
"""

import geopandas as gpd
import folium
from folium import plugins
import pandas as pd
from pathlib import Path
import logging

def setup_logging():
    """Configura logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger('mapa_oxxos')

def main():
    """Función principal para crear el mapa"""
    logger = setup_logging()
    logger.info("Iniciando creación del mapa...")
    
    try:
        # Directorios
        base_dir = Path(__file__).parent.parent
        processed_dir = base_dir / "data" / "processed"
        output_dir = base_dir / "maps"
        output_dir.mkdir(exist_ok=True)
        
        # Cargar datos
        logger.info("Cargando datos...")
        
        datos_combinados = gpd.read_file(processed_dir / "datos_combinados.gpkg")
        oxxos_data = gpd.read_file(processed_dir / "oxxos_con_alcaldia.gpkg")
        
        logger.info(f"Datos cargados: {len(datos_combinados)} alcaldías, {len(oxxos_data)} Oxxos")
        
        # Convertir a WGS84 para Folium
        if datos_combinados.crs != "EPSG:4326":
            datos_combinados = datos_combinados.to_crs("EPSG:4326")
        if oxxos_data.crs != "EPSG:4326":
            oxxos_data = oxxos_data.to_crs("EPSG:4326")
        
        # Centro del mapa (CDMX)
        center_lat = 19.4326
        center_lon = -99.1332
        
        # Crear mapa
        mapa = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=10,
            tiles='OpenStreetMap'
        )
        
        # Colores por partido
        colores_partidos = {
            'MORENA': '#8B4513',
            'PAN': '#0080FF', 
            'PRI': '#FF0000',
            'OTRO': '#808080'
        }
        
        # Agregar alcaldías
        logger.info("Agregando alcaldías al mapa...")
        for idx, row in datos_combinados.iterrows():
            try:
                partido = row.get('partido_ganador', 'OTRO')
                color = colores_partidos.get(partido, '#808080')
                num_oxxos = row.get('num_oxxos', 0)
                
                popup_info = f"""
                <b>{row['alcaldia']}</b><br>
                Partido: {partido}<br>
                Oxxos: {num_oxxos}<br>
                Votos: {row.get('votos_totales', 'N/A'):,}
                """
                
                folium.GeoJson(
                    row['geometry'].__geo_interface__,
                    style_function=lambda feature, color=color: {
                        'fillColor': color,
                        'color': 'black',
                        'weight': 2,
                        'fillOpacity': 0.3,
                        'opacity': 0.8
                    },
                    popup=folium.Popup(popup_info, max_width=200),
                    tooltip=f"{row['alcaldia']} ({partido}) - {num_oxxos} Oxxos"
                ).add_to(mapa)
                
            except Exception as e:
                logger.warning(f"Error agregando alcaldía {row.get('alcaldia', idx)}: {e}")
        
        # Cluster de Oxxos
        logger.info("Agregando Oxxos al mapa...")
        marker_cluster = plugins.MarkerCluster().add_to(mapa)
        
        oxxos_agregados = 0
        for idx, oxxo in oxxos_data.iterrows():
            try:
                if pd.notna(oxxo.geometry) and hasattr(oxxo.geometry, 'y'):
                    lat, lon = oxxo.geometry.y, oxxo.geometry.x
                    alcaldia = oxxo.get('alcaldia', 'Sin asignar')
                    
                    folium.Marker(
                        location=[lat, lon],
                        popup=f"OXXO en {alcaldia}",
                        tooltip=f"OXXO - {alcaldia}",
                        icon=folium.Icon(color='red', icon='shopping-cart')
                    ).add_to(marker_cluster)
                    
                    oxxos_agregados += 1
                    
            except Exception as e:
                logger.debug(f"Error agregando Oxxo {idx}: {e}")
                continue
        
        logger.info(f"Agregados {oxxos_agregados} Oxxos al mapa")
        
        # Leyenda
        leyenda_html = f'''
        <div style="position: fixed; top: 10px; left: 50px; width: 200px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <h4>Mapa Oxxos CDMX</h4>
        <p><b>{len(oxxos_data):,} Oxxos</b> en <b>{len(datos_combinados)} alcaldías</b></p>
        <hr>
        <p><span style="color:#8B4513">⬛</span> MORENA</p>
        <p><span style="color:#0080FF">⬛</span> PAN</p>
        <p><span style="color:#FF0000">⬛</span> PRI</p>
        </div>
        '''
        mapa.get_root().html.add_child(folium.Element(leyenda_html))
        
        # Guardar mapa
        mapa_path = output_dir / "mapa_oxxos_cdmx.html"
        mapa.save(str(mapa_path))
        
        logger.info(f"✅ Mapa guardado en: {mapa_path}")
        logger.info(f"📊 Total: {oxxos_agregados} Oxxos en {len(datos_combinados)} alcaldías")
        
        # Reporte
        print(f"\n🎉 ¡Mapa creado exitosamente!")
        print(f"📍 Archivo: {mapa_path}")
        print(f"📊 {oxxos_agregados:,} Oxxos en {len(datos_combinados)} alcaldías")
        print(f"🌐 Abre el archivo HTML en tu navegador")
        
        return str(mapa_path)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()
