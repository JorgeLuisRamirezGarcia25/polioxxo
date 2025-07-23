#!/usr/bin/env python3
"""
Script para crear mapa interactivo de distritos electorales - Polioxxo

Este script crea mapas específicos para:
1. Distritos electorales con Oxxos
2. Comparación alcaldías vs distritos
3. Análisis de participación electoral
"""

import sys
import os
from pathlib import Path

# Agregar ruta del proyecto al path de Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import geopandas as gpd
import pandas as pd
import folium
from folium import plugins
import json
import logging

from scripts.utils import setup_logging, get_project_paths, load_geodataframe

def create_district_electoral_map():
    """
    Crea mapa interactivo de distritos electorales con Oxxos
    """
    logger = setup_logging('polioxxo.district_map')
    paths = get_project_paths()
    
    logger.info("🗺️ Creando mapa de distritos electorales...")
    
    try:
        # Cargar datos
        oxxos_path = paths['data_processed'] / 'oxxos_con_distrito.gpkg'
        districts_path = paths['data_processed'] / 'distritos_electorales.gpkg'
        
        if not oxxos_path.exists() or not districts_path.exists():
            logger.error("Datos de distritos no encontrados. Ejecuta primero analyze_districts.py")
            return False
        
        oxxos = gpd.read_file(oxxos_path)
        districts = gpd.read_file(districts_path)
        
        logger.info(f"Cargados {len(oxxos)} Oxxos y {len(districts)} distritos")
        
        # Convertir a WGS84 para Folium
        oxxos = oxxos.to_crs('EPSG:4326')
        districts = districts.to_crs('EPSG:4326')
        
        # Crear mapa base centrado en CDMX
        center_lat = 19.4326
        center_lon = -99.1332
        
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=10,
            tiles=None,
            width='100%',
            height='100%'
        )
        
        # Capas base
        folium.TileLayer('OpenStreetMap', name='OpenStreetMap').add_to(m)
        folium.TileLayer('CartoDB Positron', name='CartoDB Positron').add_to(m)
        folium.TileLayer('CartoDB Dark_Matter', name='CartoDB Dark').add_to(m)
        
        # Colores por partido
        party_colors = {
            'MORENA': '#8B4513',
            'PAN': '#0080FF',
            'PRI': '#FF0000',
            'Sin datos': '#808080'
        }
        
        # Agregar distritos como polígonos
        logger.info("Agregando distritos al mapa...")
        
        district_group = folium.FeatureGroup(name='Distritos Electorales')
        
        for _, district in districts.iterrows():
            # Contar Oxxos en este distrito
            oxxos_en_distrito = len(oxxos[oxxos['distrito'] == district['distrito']])
            
            color = party_colors.get(district['diputado_ganador'], '#808080')
            
            # Popup con información del distrito
            popup_html = f"""
            <div style="font-family: Arial; width: 250px;">
                <h4 style="color: {color}; margin-bottom: 10px;">
                    📊 {district['distrito']}
                </h4>
                <hr style="margin: 10px 0;">
                <b>🏛️ Alcaldía:</b> {district['alcaldia']}<br>
                <b>🗳️ Diputado ganador:</b> <span style="color: {color}; font-weight: bold;">{district['diputado_ganador']}</span><br>
                <b>📊 Votos:</b> {district['votos_distrito']:,}<br>
                <b>📈 Participación:</b> {district['participacion']:.1f}%<br>
                <b>🏪 Oxxos en distrito:</b> {oxxos_en_distrito}<br>
                <hr style="margin: 10px 0;">
                <small>Densidad: {oxxos_en_distrito/district['votos_distrito']*10000:.2f} Oxxos por 10k votos</small>
            </div>
            """
            
            tooltip = f"{district['distrito']} - {district['diputado_ganador']} ({oxxos_en_distrito} Oxxos)"
            
            folium.GeoJson(
                district['geometry'].__geo_interface__,
                style_function=lambda feature, color=color: {
                    'fillColor': color,
                    'color': 'black',
                    'weight': 1,
                    'fillOpacity': 0.3,
                    'opacity': 0.8
                },
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=tooltip
            ).add_to(district_group)
        
        district_group.add_to(m)
        
        # Agregar Oxxos por distrito con colores según partido del distrito
        logger.info("Agregando Oxxos al mapa...")
        
        # Crear clusters por partido
        party_groups = {}
        for party in party_colors.keys():
            if party != 'Sin datos':
                party_groups[party] = plugins.MarkerCluster(
                    name=f'Oxxos en Distritos {party}',
                    overlay=True,
                    control=True,
                    options={
                        'maxClusterRadius': 50,
                        'disableClusteringAtZoom': 15
                    }
                )
        
        # Agregar Oxxos a clusters
        for _, oxxo in oxxos.iterrows():
            if pd.isna(oxxo.geometry):
                continue
                
            lat = oxxo.geometry.y
            lon = oxxo.geometry.x
            
            party = oxxos.loc[oxxos.index == oxxo.name, 'diputado_ganador'].iloc[0] if 'diputado_ganador' in oxxos.columns else 'Sin datos'
            distrito = oxxo.get('distrito', 'Sin distrito')
            alcaldia = oxxo.get('alcaldia', 'Sin alcaldía')
            
            color = party_colors.get(party, '#808080')
            
            # Popup del Oxxo
            popup_html = f"""
            <div style="font-family: Arial; width: 200px;">
                <h4 style="color: {color};">🏪 OXXO</h4>
                <hr>
                <b>📍 Distrito:</b> {distrito}<br>
                <b>🏛️ Alcaldía:</b> {alcaldia}<br>
                <b>🗳️ Partido distrito:</b> <span style="color: {color}; font-weight: bold;">{party}</span><br>
                <b>📍 Dirección:</b> {oxxo.get('direccion', 'No disponible')}<br>
            </div>
            """
            
            marker = folium.CircleMarker(
                location=[lat, lon],
                radius=4,
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"OXXO - {distrito}",
                color='white',
                weight=1,
                fillColor=color,
                fillOpacity=0.8
            )
            
            if party in party_groups:
                marker.add_to(party_groups[party])
            else:
                marker.add_to(m)
        
        # Agregar clusters al mapa
        for group in party_groups.values():
            group.add_to(m)
        
        # Crear leyenda
        legend_html = '''
        <div style="position: fixed; 
                    top: 10px; right: 10px; width: 200px; height: auto; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <h4>🗳️ Distritos Electorales CDMX</h4>
        <hr>
        '''
        
        for party, color in party_colors.items():
            if party != 'Sin datos':
                count_districts = len(districts[districts['diputado_ganador'] == party])
                count_oxxos = len(oxxos[oxxos['diputado_ganador'] == party]) if 'diputado_ganador' in oxxos.columns else 0
                legend_html += f'''
                <p><span style="color:{color}; font-size: 20px;">●</span> {party} 
                <br><small>{count_districts} distritos, {count_oxxos} Oxxos</small></p>
                '''
        
        legend_html += '''
        <hr>
        <small>
        📊 Polígonos = Distritos<br>
        🏪 Puntos = Tiendas Oxxo<br>
        Click para más detalles
        </small>
        </div>
        '''
        
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Control de capas
        folium.LayerControl(collapsed=False).add_to(m)
        
        # Plugin de pantalla completa
        plugins.Fullscreen().add_to(m)
        
        # Plugin de medición
        plugins.MeasureControl().add_to(m)
        
        # Guardar mapa
        output_path = paths['maps'] / 'mapa_distritos_electorales_cdmx.html'
        m.save(str(output_path))
        
        logger.info(f"✅ Mapa de distritos guardado: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error creando mapa de distritos: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_comparison_map():
    """
    Crea mapa comparativo entre alcaldías y distritos
    """
    logger = setup_logging('polioxxo.comparison_map')
    paths = get_project_paths()
    
    logger.info("🗺️ Creando mapa comparativo alcaldías vs distritos...")
    
    try:
        # Cargar datos
        alcaldias_path = paths['data_processed'] / 'datos_combinados.gpkg'
        districts_path = paths['data_processed'] / 'distritos_electorales.gpkg'
        
        if not alcaldias_path.exists() or not districts_path.exists():
            logger.error("Datos no encontrados")
            return False
        
        alcaldias = gpd.read_file(alcaldias_path)
        districts = gpd.read_file(districts_path)
        
        # Convertir a WGS84
        alcaldias = alcaldias.to_crs('EPSG:4326')
        districts = districts.to_crs('EPSG:4326')
        
        # Crear mapa dual
        m = folium.Map(
            location=[19.4326, -99.1332],
            zoom_start=10,
            tiles='CartoDB Positron'
        )
        
        # Colores
        party_colors = {'MORENA': '#8B4513', 'PAN': '#0080FF', 'PRI': '#FF0000'}
        
        # Grupo de alcaldías
        alcaldias_group = folium.FeatureGroup(name='Alcaldías', show=True)
        for _, alcaldia in alcaldias.iterrows():
            color = party_colors.get(alcaldia['partido_ganador'], '#808080')
            
            folium.GeoJson(
                alcaldia['geometry'].__geo_interface__,
                style_function=lambda feature, color=color: {
                    'fillColor': color,
                    'color': 'black',
                    'weight': 2,
                    'fillOpacity': 0.5,
                    'opacity': 1.0
                },
                tooltip=f"{alcaldia['alcaldia']} - {alcaldia['partido_ganador']} ({alcaldia['num_oxxos']} Oxxos)"
            ).add_to(alcaldias_group)
        
        # Grupo de distritos
        districts_group = folium.FeatureGroup(name='Distritos Electorales', show=False)
        for _, district in districts.iterrows():
            color = party_colors.get(district['diputado_ganador'], '#808080')
            
            folium.GeoJson(
                district['geometry'].__geo_interface__,
                style_function=lambda feature, color=color: {
                    'fillColor': color,
                    'color': 'white',
                    'weight': 1,
                    'fillOpacity': 0.3,
                    'opacity': 0.8,
                    'dashArray': '5, 5'
                },
                tooltip=f"{district['distrito']} - {district['diputado_ganador']}"
            ).add_to(districts_group)
        
        alcaldias_group.add_to(m)
        districts_group.add_to(m)
        
        # Control de capas
        folium.LayerControl().add_to(m)
        
        # Leyenda comparativa
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; right: 10px; width: 250px; height: auto; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:12px; padding: 10px">
        <h4>🏛️ Comparativo Territorial</h4>
        <hr>
        <p><b>Alcaldías:</b> Líneas sólidas, relleno opaco</p>
        <p><b>Distritos:</b> Líneas punteadas, relleno transparente</p>
        <hr>
        <p>Activa/desactiva capas para comparar</p>
        </div>
        '''
        
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Guardar
        output_path = paths['maps'] / 'mapa_comparativo_alcaldias_distritos.html'
        m.save(str(output_path))
        
        logger.info(f"✅ Mapa comparativo guardado: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error creando mapa comparativo: {e}")
        return False

def main():
    """Función principal"""
    logger = setup_logging('polioxxo.district_map')
    
    logger.info("🗺️ INICIANDO CREACIÓN DE MAPAS DE DISTRITOS")
    logger.info("=" * 50)
    
    try:
        # Crear mapa principal de distritos
        logger.info("Creando mapa principal de distritos...")
        if not create_district_electoral_map():
            logger.error("Error en mapa de distritos")
            return False
        
        # Crear mapa comparativo
        logger.info("Creando mapa comparativo...")
        if not create_comparison_map():
            logger.error("Error en mapa comparativo")
            return False
        
        paths = get_project_paths()
        logger.info("=" * 50)
        logger.info("🎉 MAPAS DE DISTRITOS COMPLETADOS")
        logger.info(f"📁 Mapas guardados en: {paths['maps']}")
        logger.info("- mapa_distritos_electorales_cdmx.html")
        logger.info("- mapa_comparativo_alcaldias_distritos.html")
        
        return True
        
    except Exception as e:
        logger.error(f"Error general: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
