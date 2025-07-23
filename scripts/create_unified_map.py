#!/usr/bin/env python3
"""
Script para crear mapa unificado - Polioxxo

Mapa interactivo que permite cambiar entre:
1. Vista de Alcaldías con Oxxos
2. Vista de Distritos Electorales con Oxxos
3. Vista comparativa (ambos superpuestos)
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

def create_unified_map():
    """
    Crea mapa unificado con alcaldías y distritos electorales
    """
    logger = setup_logging('polioxxo.unified_map')
    paths = get_project_paths()
    
    logger.info("🗺️ Creando mapa unificado alcaldías + distritos...")
    
    try:
        # Cargar todos los datos necesarios
        logger.info("Cargando datos...")
        
        # Datos de alcaldías
        alcaldias_path = paths['data_processed'] / 'datos_combinados.gpkg'
        oxxos_alcaldia_path = paths['data_processed'] / 'oxxos_con_alcaldia.gpkg'
        
        # Datos de distritos
        districts_path = paths['data_processed'] / 'distritos_electorales.gpkg'
        oxxos_distrito_path = paths['data_processed'] / 'oxxos_con_distrito.gpkg'
        
        # Verificar que existan todos los archivos
        required_files = [alcaldias_path, oxxos_alcaldia_path, districts_path, oxxos_distrito_path]
        missing_files = [f for f in required_files if not f.exists()]
        
        if missing_files:
            logger.error(f"Archivos faltantes: {missing_files}")
            logger.info("Ejecuta primero: python scripts/analyze_districts.py")
            return False
        
        # Cargar datos
        alcaldias = gpd.read_file(alcaldias_path)
        oxxos_alcaldia = gpd.read_file(oxxos_alcaldia_path)
        districts = gpd.read_file(districts_path)
        oxxos_distrito = gpd.read_file(oxxos_distrito_path)
        
        logger.info(f"Cargados: {len(alcaldias)} alcaldías, {len(districts)} distritos")
        logger.info(f"Oxxos: {len(oxxos_alcaldia)} con alcaldía, {len(oxxos_distrito)} con distrito")
        
        # Convertir todo a WGS84 para Folium
        alcaldias = alcaldias.to_crs('EPSG:4326')
        oxxos_alcaldia = oxxos_alcaldia.to_crs('EPSG:4326')
        districts = districts.to_crs('EPSG:4326')
        oxxos_distrito = oxxos_distrito.to_crs('EPSG:4326')
        
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
        
        # === SECCIÓN 1: ALCALDÍAS ===
        logger.info("Agregando capa de alcaldías...")
        
        alcaldias_group = folium.FeatureGroup(name='🏛️ Alcaldías', show=True)
        
        for _, alcaldia in alcaldias.iterrows():
            if pd.isna(alcaldia.geometry):
                continue
                
            color = party_colors.get(alcaldia.get('partido_ganador', 'Sin datos'), '#808080')
            num_oxxos = alcaldia.get('num_oxxos', 0)
            
            # Popup de alcaldía
            votos_totales = alcaldia.get('votos_totales', 0)
            densidad = (num_oxxos/votos_totales*10000) if votos_totales > 0 else 0
            
            popup_html = f"""
            <div style="font-family: Arial; width: 280px;">
                <h3 style="color: {color}; margin-bottom: 10px;">
                    🏛️ {alcaldia.get('alcaldia', 'Sin nombre')}
                </h3>
                <hr style="margin: 10px 0;">
                <b>🗳️ Partido ganador:</b> <span style="color: {color}; font-weight: bold;">{alcaldia.get('partido_ganador', 'Sin datos')}</span><br>
                <b>📊 Votos totales:</b> {votos_totales:,}<br>
                <b>📈 Porcentaje:</b> {alcaldia.get('porcentaje', 0):.1f}%<br>
                <b>🏪 Oxxos:</b> {num_oxxos}<br>
                <hr style="margin: 10px 0;">
                <small>Densidad: {densidad:.2f} Oxxos por 10k votantes</small>
            </div>
            """
            
            tooltip = f"{alcaldia.get('alcaldia', 'Sin nombre')} - {alcaldia.get('partido_ganador', 'Sin datos')} ({num_oxxos} Oxxos)"
            
            folium.GeoJson(
                alcaldia['geometry'].__geo_interface__,
                style_function=lambda feature, color=color: {
                    'fillColor': color,
                    'color': 'black',
                    'weight': 2,
                    'fillOpacity': 0.6,
                    'opacity': 1.0
                },
                popup=folium.Popup(popup_html, max_width=320),
                tooltip=tooltip
            ).add_to(alcaldias_group)
        
        alcaldias_group.add_to(m)
        
        # === SECCIÓN 2: DISTRITOS ELECTORALES ===
        logger.info("Agregando capa de distritos...")
        
        districts_group = folium.FeatureGroup(name='📊 Distritos Electorales', show=False)
        
        for _, district in districts.iterrows():
            if pd.isna(district.geometry):
                continue
                
            color = party_colors.get(district.get('diputado_ganador', 'Sin datos'), '#808080')
            
            # Contar Oxxos en este distrito
            oxxos_en_distrito = len(oxxos_distrito[oxxos_distrito['distrito'] == district['distrito']]) if 'distrito' in oxxos_distrito.columns else 0
            
            # Popup de distrito
            votos_distrito = district.get('votos_distrito', 0)
            densidad_distrito = (oxxos_en_distrito/votos_distrito*10000) if votos_distrito > 0 else 0
            
            popup_html = f"""
            <div style="font-family: Arial; width: 280px;">
                <h3 style="color: {color}; margin-bottom: 10px;">
                    📊 {district.get('distrito', 'Sin nombre')}
                </h3>
                <hr style="margin: 10px 0;">
                <b>🏛️ Alcaldía base:</b> {district.get('alcaldia', 'Sin datos')}<br>
                <b>🗳️ Diputado ganador:</b> <span style="color: {color}; font-weight: bold;">{district.get('diputado_ganador', 'Sin datos')}</span><br>
                <b>📊 Votos distrito:</b> {votos_distrito:,}<br>
                <b>📈 Participación:</b> {district.get('participacion', 0):.1f}%<br>
                <b>🏪 Oxxos en distrito:</b> {oxxos_en_distrito}<br>
                <hr style="margin: 10px 0;">
                <small>Densidad: {densidad_distrito:.2f} Oxxos por 10k votos</small>
            </div>
            """
            
            tooltip = f"{district.get('distrito', 'Sin nombre')} - {district.get('diputado_ganador', 'Sin datos')} ({oxxos_en_distrito} Oxxos)"
            
            folium.GeoJson(
                district['geometry'].__geo_interface__,
                style_function=lambda feature, color=color: {
                    'fillColor': color,
                    'color': 'white',
                    'weight': 1.5,
                    'fillOpacity': 0.4,
                    'opacity': 0.9,
                    'dashArray': '8, 4'
                },
                popup=folium.Popup(popup_html, max_width=320),
                tooltip=tooltip
            ).add_to(districts_group)
        
        districts_group.add_to(m)
        
        # === SECCIÓN 3: OXXOS POR ALCALDÍAS ===
        logger.info("Agregando Oxxos por alcaldías...")
        
        oxxos_alcaldia_clusters = {}
        for party in party_colors.keys():
            if party != 'Sin datos':
                oxxos_alcaldia_clusters[party] = plugins.MarkerCluster(
                    name=f'🏪 Oxxos Alcaldías {party}',
                    overlay=True,
                    control=True,
                    show=True,
                    options={'maxClusterRadius': 40, 'disableClusteringAtZoom': 14}
                )
        
        # Agregar Oxxos de alcaldías
        for _, oxxo in oxxos_alcaldia.iterrows():
            if pd.isna(oxxo.geometry):
                continue
                
            lat = oxxo.geometry.y
            lon = oxxo.geometry.x
            
            # Obtener partido de la alcaldía
            alcaldia_name = oxxo.get('alcaldia', 'Sin alcaldía')
            alcaldia_info = alcaldias[alcaldias['alcaldia'] == alcaldia_name]
            party = alcaldia_info['partido_ganador'].iloc[0] if len(alcaldia_info) > 0 else 'Sin datos'
            
            color = party_colors.get(party, '#808080')
            
            # Popup del Oxxo
            popup_html = f"""
            <div style="font-family: Arial; width: 220px;">
                <h4 style="color: {color};">🏪 OXXO</h4>
                <hr>
                <b>🏛️ Alcaldía:</b> {alcaldia_name}<br>
                <b>🗳️ Partido:</b> <span style="color: {color}; font-weight: bold;">{party}</span><br>
                <b>📍 Dirección:</b> {oxxo.get('direccion', 'No disponible')}<br>
            </div>
            """
            
            marker = folium.CircleMarker(
                location=[lat, lon],
                radius=5,
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"OXXO - {alcaldia_name}",
                color='white',
                weight=1,
                fillColor=color,
                fillOpacity=0.8
            )
            
            if party in oxxos_alcaldia_clusters:
                marker.add_to(oxxos_alcaldia_clusters[party])
            else:
                marker.add_to(m)
        
        # Agregar clusters de alcaldías al mapa
        for cluster in oxxos_alcaldia_clusters.values():
            cluster.add_to(m)
        
        # === SECCIÓN 4: OXXOS POR DISTRITOS ===
        logger.info("Agregando Oxxos por distritos...")
        
        oxxos_district_clusters = {}
        for party in party_colors.keys():
            if party != 'Sin datos':
                oxxos_district_clusters[party] = plugins.MarkerCluster(
                    name=f'📊 Oxxos Distritos {party}',
                    overlay=True,
                    control=True,
                    show=False,
                    options={'maxClusterRadius': 40, 'disableClusteringAtZoom': 14}
                )
        
        # Agregar Oxxos de distritos
        for _, oxxo in oxxos_distrito.iterrows():
            if pd.isna(oxxo.geometry):
                continue
                
            lat = oxxo.geometry.y
            lon = oxxo.geometry.x
            
            # Obtener partido del distrito
            distrito_name = oxxo.get('distrito', 'Sin distrito')
            district_info = districts[districts['distrito'] == distrito_name]
            party = district_info['diputado_ganador'].iloc[0] if len(district_info) > 0 else 'Sin datos'
            
            color = party_colors.get(party, '#808080')
            
            # Popup del Oxxo
            popup_html = f"""
            <div style="font-family: Arial; width: 220px;">
                <h4 style="color: {color};">🏪 OXXO</h4>
                <hr>
                <b>📊 Distrito:</b> {distrito_name}<br>
                <b>🗳️ Diputado partido:</b> <span style="color: {color}; font-weight: bold;">{party}</span><br>
                <b>📍 Dirección:</b> {oxxo.get('direccion', 'No disponible')}<br>
            </div>
            """
            
            marker = folium.CircleMarker(
                location=[lat, lon],
                radius=4,
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"OXXO - {distrito_name}",
                color='white',
                weight=1,
                fillColor=color,
                fillOpacity=0.7
            )
            
            if party in oxxos_district_clusters:
                marker.add_to(oxxos_district_clusters[party])
            else:
                marker.add_to(m)
        
        # Agregar clusters de distritos al mapa
        for cluster in oxxos_district_clusters.values():
            cluster.add_to(m)
        
        # === LEYENDA INTERACTIVA ===
        legend_html = '''
        <div style="position: fixed; 
                    top: 10px; right: 10px; width: 300px; height: auto; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:12px; padding: 15px; border-radius: 5px;">
        <h3 style="margin-top: 0;">🗺️ Mapa Unificado CDMX</h3>
        <hr>
        
        <h4>🎨 Partidos Políticos:</h4>
        '''
        
        for party, color in party_colors.items():
            if party != 'Sin datos':
                count_alcaldias = len(alcaldias[alcaldias['partido_ganador'] == party])
                count_districts = len(districts[districts['diputado_ganador'] == party])
                legend_html += f'''
                <p style="margin: 5px 0;"><span style="color:{color}; font-size: 16px;">●</span> <b>{party}</b><br>
                <small style="margin-left: 20px;">Alcaldías: {count_alcaldias} | Distritos: {count_districts}</small></p>
                '''
        
        legend_html += '''
        <hr>
        <h4>📋 Capas Disponibles:</h4>
        <p><b>🏛️ Alcaldías:</b> Polígonos sólidos<br>
        <b>📊 Distritos:</b> Polígonos punteados<br>
        <b>🏪 Oxxos:</b> Puntos agrupados</p>
        
        <hr>
        <p><small><b>💡 Tip:</b> Usa el control de capas para cambiar entre vistas de alcaldías y distritos</small></p>
        </div>
        '''
        
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # === CONTROLES ADICIONALES ===
        
        # Control de capas expandido
        folium.LayerControl(collapsed=False, position='topleft').add_to(m)
        
        # Plugin de pantalla completa
        plugins.Fullscreen(position='topright').add_to(m)
        
        # Plugin de medición
        plugins.MeasureControl(primary_length_unit='kilometers').add_to(m)
        
        # Minimapa
        minimap = plugins.MiniMap(toggle_display=True, position='bottomleft')
        m.add_child(minimap)
        
        # === JAVASCRIPT PERSONALIZADO PARA CAMBIO RÁPIDO ===
        toggle_script = '''
        <script>
        function toggleAlcaldias() {
            // Activar capas de alcaldías
            document.querySelectorAll('input[type="checkbox"]').forEach(function(checkbox) {
                if (checkbox.nextSibling && checkbox.nextSibling.textContent) {
                    var text = checkbox.nextSibling.textContent.trim();
                    if (text.includes('Alcaldías') || text.includes('Oxxos Alcaldías')) {
                        checkbox.checked = true;
                        checkbox.dispatchEvent(new Event('change'));
                    } else if (text.includes('Distritos') || text.includes('Oxxos Distritos')) {
                        checkbox.checked = false;
                        checkbox.dispatchEvent(new Event('change'));
                    }
                }
            });
        }
        
        function toggleDistritos() {
            // Activar capas de distritos
            document.querySelectorAll('input[type="checkbox"]').forEach(function(checkbox) {
                if (checkbox.nextSibling && checkbox.nextSibling.textContent) {
                    var text = checkbox.nextSibling.textContent.trim();
                    if (text.includes('Distritos') || text.includes('Oxxos Distritos')) {
                        checkbox.checked = true;
                        checkbox.dispatchEvent(new Event('change'));
                    } else if (text.includes('Alcaldías') || text.includes('Oxxos Alcaldías')) {
                        checkbox.checked = false;
                        checkbox.dispatchEvent(new Event('change'));
                    }
                }
            });
        }
        
        function toggleComparativo() {
            // Activar todas las capas
            document.querySelectorAll('input[type="checkbox"]').forEach(function(checkbox) {
                if (checkbox.nextSibling && checkbox.nextSibling.textContent) {
                    var text = checkbox.nextSibling.textContent.trim();
                    if (text.includes('Alcaldías') || text.includes('Distritos') || text.includes('Oxxos')) {
                        checkbox.checked = true;
                        checkbox.dispatchEvent(new Event('change'));
                    }
                }
            });
        }
        </script>
        
        <div style="position: fixed; bottom: 20px; left: 20px; z-index: 9999;">
            <div style="background: white; padding: 10px; border-radius: 5px; border: 2px solid #ccc;">
                <h4 style="margin: 0 0 10px 0;">🚀 Cambio Rápido</h4>
                <button onclick="toggleAlcaldias()" style="margin: 2px; padding: 8px 12px; background: #0080FF; color: white; border: none; border-radius: 3px; cursor: pointer;">🏛️ Solo Alcaldías</button><br>
                <button onclick="toggleDistritos()" style="margin: 2px; padding: 8px 12px; background: #8B4513; color: white; border: none; border-radius: 3px; cursor: pointer;">📊 Solo Distritos</button><br>
                <button onclick="toggleComparativo()" style="margin: 2px; padding: 8px 12px; background: #FF0000; color: white; border: none; border-radius: 3px; cursor: pointer;">🔄 Vista Comparativa</button>
            </div>
        </div>
        '''
        
        m.get_root().html.add_child(folium.Element(toggle_script))
        
        # Guardar mapa
        output_path = paths['maps'] / 'mapa_unificado_cdmx.html'
        m.save(str(output_path))
        
        logger.info(f"✅ Mapa unificado guardado: {output_path}")
        logger.info("🎉 Funcionalidades incluidas:")
        logger.info("  - Cambio entre alcaldías y distritos electorales")
        logger.info("  - Vista comparativa superpuesta")
        logger.info("  - Botones de cambio rápido")
        logger.info("  - Control de capas expandido")
        logger.info("  - Tooltips y popups informativos")
        
        return True
        
    except Exception as e:
        logger.error(f"Error creando mapa unificado: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Función principal"""
    logger = setup_logging('polioxxo.unified_map')
    
    logger.info("🗺️ INICIANDO CREACIÓN DE MAPA UNIFICADO")
    logger.info("=" * 50)
    
    try:
        if not create_unified_map():
            logger.error("Error en la creación del mapa unificado")
            return False
        
        paths = get_project_paths()
        logger.info("=" * 50)
        logger.info("🎉 MAPA UNIFICADO COMPLETADO")
        logger.info(f"📁 Mapa guardado en: {paths['maps']}/mapa_unificado_cdmx.html")
        logger.info("🚀 Abre el archivo HTML para ver el mapa interactivo!")
        
        return True
        
    except Exception as e:
        logger.error(f"Error general: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
