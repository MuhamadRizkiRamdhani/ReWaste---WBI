with col_right:
    if show_map:
        st.markdown("### 🗺️ Peta Wilayah Kota Bandung")
        
        try:
            # Load GeoJSON
            with open("3273-kota-bandung-level-kewilayahan.json", "r") as f:
                geojson_data = json.load(f)
            
            center_lat = -6.9146
            center_lon = 107.6098
            
            m = folium.Map(location=[center_lat, center_lon], zoom_start=11, control_scale=True)
            
            folium.TileLayer('CartoDB positron', name='Light Map', show=True).add_to(m)
            folium.TileLayer('OpenStreetMap', name='Street Map', show=False).add_to(m)
            
            def get_wilayah_color(wilayah_name):
                status = st.session_state.wilayah_status.get(wilayah_name, "")
                if status == "KRITIS":
                    return "#E74C3C"
                elif status == "WASPADA":
                    return "#F39C12"
                elif status == "AMAN":
                    return "#27AE60"
                else:
                    return "#95A5A6"
            
            if show_boundary and geojson_data:
                for feature in geojson_data.get('features', []):
                    props = feature.get('properties', {})
                    wilayah_name = props.get('nama_wilayah', '')
                    
                    fill_color = get_wilayah_color(wilayah_name)
                    params = st.session_state.wilayah_params.get(wilayah_name, {})
                    
                    # Buat popup text dengan aman
                    status_text = st.session_state.wilayah_status.get(wilayah_name, 'Belum diprediksi')
                    angkut_val = params.get('rasio_angkut')
                    diolah_val = params.get('rasio_diolah')
                    sisa_val = params.get('rasio_sisa')
                    jarak_val = params.get('indeks_jarak')
                    
                    angkut_str = f"{angkut_val:.3f}" if angkut_val is not None else '-'
                    diolah_str = f"{diolah_val:.3f}" if diolah_val is not None else '-'
                    sisa_str = f"{sisa_val:.3f}" if sisa_val is not None else '-'
                    jarak_str = f"{jarak_val:.3f}" if jarak_val is not None else '-'
                    
                    popup_html = f"""
                    <div style="min-width: 200px;">
                        <b>{wilayah_name}</b><br>
                        Status: {status_text}<br>
                        <hr style="margin: 5px 0;">
                        Rasio Angkut: {angkut_str}<br>
                        Rasio Diolah: {diolah_str}<br>
                        Rasio Sisa: {sisa_str}<br>
                        Indeks Jarak: {jarak_str}
                    </div>
                    """
                    
                    folium.GeoJson(
                        feature,
                        name=wilayah_name if wilayah_name else 'Wilayah',
                        style_function=lambda x, color=fill_color: {
                            'fillColor': color,
                            'color': '#2C3E50',
                            'weight': 1.5,
                            'fillOpacity': 0.6 if color != "#95A5A6" else 0.3,
                        },
                        tooltip=folium.Tooltip(wilayah_name if wilayah_name else "Wilayah", sticky=True),
                        popup=folium.Popup(popup_html, max_width=300)
                    ).add_to(m)
                    
                    if show_labels and wilayah_name:
                        try:
                            if feature.get('geometry', {}).get('type') == 'Polygon':
                                coords = feature['geometry']['coordinates'][0]
                                if coords:
                                    lats = [c[1] for c in coords]
                                    lons = [c[0] for c in coords]
                                    center_lat_label = sum(lats) / len(lats)
                                    center_lon_label = sum(lons) / len(lons)
                                    
                                    folium.Marker(
                                        location=[center_lat_label, center_lon_label],
                                        icon=folium.DivIcon(
                                            html=f'<div style="font-size: 10px; font-weight: 600; background: white; padding: 2px 6px; border-radius: 4px; border: 1px solid {fill_color}; white-space: nowrap;">{wilayah_name}</div>'
                                        )
                                    ).add_to(m)
                        except:
                            pass
            
            legend_html = '''
            <div style="position: fixed; bottom: 30px; right: 30px; z-index: 1000; background: white; padding: 10px 14px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.2); font-size: 12px;">
                <strong>Status Wilayah</strong><br>
                <span style="color: #e74c3c;">■</span> Kritis<br>
                <span style="color: #f39c12;">■</span> Waspada<br>
                <span style="color: #27ae60;">■</span> Aman<br>
                <span style="color: #95a5a6;">■</span> Belum Diprediksi
            </div>
            '''
            m.get_root().html.add_child(folium.Element(legend_html))
            
            folium.LayerControl().add_to(m)
            
            st_folium(m, width=None, height=600, key="bandung_map")
            
            st.caption("📌 Klik wilayah untuk melihat detail | Warna berubah setelah melakukan klasifikasi")
            
        except FileNotFoundError:
            st.error("File GeoJSON tidak ditemukan")
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.info("🗺️ Aktifkan 'Tampilkan Peta' di sidebar")
