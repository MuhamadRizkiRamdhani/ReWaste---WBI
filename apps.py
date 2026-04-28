import streamlit as st
import pickle
import numpy as np
import folium
from streamlit_folium import st_folium
import json

st.set_page_config(
    page_title="Klasifikasi Pengelolaan Sampah",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    :root {
        --card-bg: var(--secondary-background-color);
        --text-primary: var(--text-color);
        --text-secondary: var(--secondary-text-color);
        --border-radius: 12px;
        --shadow-sm: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
        --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
    }
    
    .status-card {
        background: var(--secondary-background-color);
        border-radius: var(--border-radius);
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: var(--shadow-md);
        transition: all 0.3s ease;
    }
    
    .metric-card {
        background: var(--secondary-background-color);
        border-radius: var(--border-radius);
        padding: 1rem;
        text-align: center;
        box-shadow: var(--shadow-sm);
        transition: all 0.2s ease;
    }
    
    .metric-value {
        font-size: 1.75rem;
        font-weight: 700;
        margin: 0.5rem 0;
    }
    
    .metric-label {
        font-size: 0.875rem;
        opacity: 0.7;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
</style>
""", unsafe_allow_html=True)

# Load model
@st.cache_resource
def load_model():
    with open("model.pkl", "rb") as f:
        return pickle.load(f)

model = load_model()

# Load GeoJSON
@st.cache_data
def load_geojson():
    with open("3273-kota-bandung-level-kewilayahan.json", "r") as f:
        data = json.load(f)
    return data

# Inisialisasi session state
if 'wilayah_status' not in st.session_state:
    st.session_state.wilayah_status = {}

if 'wilayah_params' not in st.session_state:
    st.session_state.wilayah_params = {}

if 'map_key' not in st.session_state:
    st.session_state.map_key = 0

# Konstanta label
LABEL_CONFIG = {
    "KRITIS": {
        "color": "#E74C3C", 
        "bg": "rgba(231, 76, 60, 0.15)", 
        "border": "#E74C3C",
        "icon": "⚠️",
        "desc": "Pengelolaan sampah dalam kondisi kritis. Diperlukan tindakan segera."
    },
    "WASPADA": {
        "color": "#F39C12", 
        "bg": "rgba(243, 156, 18, 0.15)", 
        "border": "#F39C12",
        "icon": "📌",
        "desc": "Pengelolaan sampah perlu perhatian lebih. Risiko meningkat."
    },
    "AMAN": {
        "color": "#27AE60", 
        "bg": "rgba(39, 174, 96, 0.15)", 
        "border": "#27AE60",
        "icon": "✓",
        "desc": "Pengelolaan sampah berjalan dengan baik."
    },
}

# Default params
DEFAULT_PARAMS = {
    "rasio_angkut": 0.75,
    "rasio_diolah": 0.50,
    "rasio_sisa": 0.25,
    "indeks_jarak": 0.40
}

# Ekstrak nama wilayah dari GeoJSON
geojson_data = load_geojson()
wilayah_names = []
for feature in geojson_data.get('features', []):
    nama = feature.get('properties', {}).get('nama_wilayah', '')
    if nama:
        wilayah_names.append(nama)

# Sidebar
with st.sidebar:
    st.markdown("### 🗺️ Pengaturan Peta")
    st.markdown("---")
    show_boundary = st.checkbox("Tampilkan Batas Wilayah", value=True)
    show_labels = st.checkbox("Tampilkan Label Wilayah", value=True)
    st.markdown("---")
    st.markdown("**Keterangan Warna:**")
    st.markdown("🔴 **Merah**: Kritis")
    st.markdown("🟡 **Kuning**: Waspada")
    st.markdown("🟢 **Hijau**: Aman")
    st.markdown("⚪ **Abu-abu**: Belum Diprediksi")
    st.markdown("---")
    
    if st.button("🔄 Reset Semua Data", use_container_width=True):
        st.session_state.wilayah_status = {}
        st.session_state.wilayah_params = {}
        st.session_state.map_key += 1
        st.rerun()

# Header
st.markdown(
    "<h1 style='text-align:center; font-weight:700;'>🗑️ Klasifikasi Pengelolaan Sampah</h1>"
    "<p style='text-align:center; opacity:0.7;'>Kota Bandung — Berbasis Waste Burden Index (WBI)</p>",
    unsafe_allow_html=True
)
st.divider()

# Layout
col_left, col_right = st.columns([1, 1.2])

with col_left:
    with st.expander("📋 Panduan Pengisian Fitur", expanded=False):
        st.markdown("""
        | Fitur | Keterangan | Rentang |
        |---|---|---|
        | **Rasio Angkut** | Proporsi sampah yang berhasil diangkut | 0.0 – 1.0 |
        | **Rasio Diolah** | Proporsi sampah yang berhasil diolah | 0.0 – 1.0 |
        | **Rasio Sisa** | Proporsi sampah yang tersisa | 0.0 – 1.0 |
        | **Indeks Jarak** | Indeks jarak tempuh TPS ke TPA | 0.0 – 1.0 |
        """)
    
    if wilayah_names:
        selected_wilayah = st.selectbox("Pilih Wilayah:", wilayah_names)
        
        saved_params = st.session_state.wilayah_params.get(selected_wilayah, DEFAULT_PARAMS.copy())
        
        st.markdown("### 📊 Input Data Fitur")
        col1, col2 = st.columns(2)
        
        with col1:
            rasio_angkut = st.number_input(
                "Rasio Angkut",
                min_value=0.0, max_value=1.0, step=0.01, format="%.3f",
                value=saved_params["rasio_angkut"]
            )
            rasio_diolah = st.number_input(
                "Rasio Diolah",
                min_value=0.0, max_value=1.0, step=0.01, format="%.3f",
                value=saved_params["rasio_diolah"]
            )
        
        with col2:
            rasio_sisa = st.number_input(
                "Rasio Sisa",
                min_value=0.0, max_value=1.0, step=0.01, format="%.3f",
                value=saved_params["rasio_sisa"]
            )
            indeks_jarak = st.number_input(
                "Indeks Jarak",
                min_value=0.0, max_value=1.0, step=0.01, format="%.3f",
                value=saved_params["indeks_jarak"]
            )
        
        if st.button("🔍 Klasifikasikan", use_container_width=True, type="primary"):
            fitur = np.array([[rasio_angkut, rasio_diolah, rasio_sisa, indeks_jarak]])
            
            try:
                prediksi = model.predict(fitur)[0]
                label = str(prediksi).strip().upper()
                
                if label not in LABEL_CONFIG:
                    label = "WASPADA"
                
                st.session_state.wilayah_status[selected_wilayah] = label
                st.session_state.wilayah_params[selected_wilayah] = {
                    "rasio_angkut": rasio_angkut,
                    "rasio_diolah": rasio_diolah,
                    "rasio_sisa": rasio_sisa,
                    "indeks_jarak": indeks_jarak
                }
                st.session_state.map_key += 1
                
                cfg = LABEL_CONFIG[label]
                
                if label == "KRITIS":
                    st.error(f"**{cfg['icon']} STATUS: {label}**")
                elif label == "WASPADA":
                    st.warning(f"**{cfg['icon']} STATUS: {label}**")
                else:
                    st.success(f"**{cfg['icon']} STATUS: {label}**")
                
                st.markdown(cfg['desc'])
                
                if hasattr(model, "predict_proba"):
                    st.markdown("### 📈 Probabilitas")
                    proba = model.predict_proba(fitur)[0]
                    classes = [str(c).upper() for c in model.classes_]
                    
                    for c, p in sorted(zip(classes, proba), key=lambda x: -x[1]):
                        st.markdown(f"**{c}**")
                        st.progress(p, text=f"{p*100:.1f}%")
                
                st.markdown("### 📊 Ringkasan Input")
                col_a, col_b, col_c, col_d = st.columns(4)
                col_a.metric("Rasio Angkut", f"{rasio_angkut:.3f}")
                col_b.metric("Rasio Diolah", f"{rasio_diolah:.3f}")
                col_c.metric("Rasio Sisa", f"{rasio_sisa:.3f}")
                col_d.metric("Indeks Jarak", f"{indeks_jarak:.3f}")
                
                st.markdown("### 💡 Rekomendasi")
                rekomendasi = []
                if rasio_sisa > 0.3:
                    rekomendasi.append("⚠️ Rasio sisa tinggi — tambah frekuensi pengangkutan")
                if rasio_angkut < 0.7:
                    rekomendasi.append("⚠️ Rasio angkut rendah — evaluasi armada")
                if rasio_diolah < 0.4:
                    rekomendasi.append("⚠️ Rasio diolah rendah — tingkatkan kapasitas pengolahan")
                if indeks_jarak > 0.7:
                    rekomendasi.append("⚠️ Jarak ke TPA jauh — optimasi rute")
                if not rekomendasi:
                    rekomendasi.append("✅ Semua indikator dalam kondisi baik")
                
                for r in rekomendasi:
                    st.markdown(r)
                
                st.rerun()
                    
            except Exception as e:
                st.error(f"❌ Error: {e}")
    else:
        st.error("Tidak dapat memuat data wilayah dari GeoJSON")

with col_right:
    st.markdown("### 🗺️ Peta Wilayah Kota Bandung")
    
    try:
        # Load GeoJSON
        with open("3273-kota-bandung-level-kewilayahan.json", "r") as f:
            geojson_data_map = json.load(f)
        
        # Center map
        center_lat = -6.9146
        center_lon = 107.6098
        
        # Buat peta dengan tile default yang visible
        m = folium.Map(
            location=[center_lat, center_lon], 
            zoom_start=11, 
            control_scale=True,
            tiles='CartoDB positron'  # Langsung tampilkan peta, tidak kosong
        )
        
        # Fungsi warna
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
        
        # Tampilkan batas wilayah
        if show_boundary:
            for feature in geojson_data_map.get('features', []):
                props = feature.get('properties', {})
                wilayah_name = props.get('nama_wilayah', '')
                
                fill_color = get_wilayah_color(wilayah_name)
                params = st.session_state.wilayah_params.get(wilayah_name, {})
                
                # Persiapkan data popup
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
                
                # Opacity lebih rendah untuk yang belum diprediksi
                opacity = 0.6 if fill_color != "#95A5A6" else 0.3
                
                folium.GeoJson(
                    feature,
                    name=wilayah_name if wilayah_name else 'Wilayah',
                    style_function=lambda x, color=fill_color, op=opacity: {
                        'fillColor': color,
                        'color': '#2C3E50',
                        'weight': 1.5,
                        'fillOpacity': op,
                    },
                    tooltip=folium.Tooltip(wilayah_name if wilayah_name else "Wilayah", sticky=True),
                    popup=folium.Popup(popup_html, max_width=300)
                ).add_to(m)
                
                # Label wilayah
                if show_labels and wilayah_name:
                    try:
                        geom = feature.get('geometry', {})
                        if geom.get('type') == 'Polygon':
                            coords = geom['coordinates'][0]
                            if coords and len(coords) > 0:
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
                    except Exception as e:
                        pass
        
        # Legend
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
        
        # Tampilkan peta dengan key yang unik agar refresh
        st_folium(m, width=None, height=600, key=f"bandung_map_{st.session_state.map_key}")
        
        st.caption("📌 Klik wilayah untuk melihat detail | Warna berubah setelah melakukan klasifikasi | Data tersimpan per wilayah")
        
    except FileNotFoundError:
        st.error("File GeoJSON '3273-kota-bandung-level-kewilayahan.json' tidak ditemukan")
    except Exception as e:
        st.error(f"Error memuat peta: {e}")

# Footer
st.divider()
st.markdown(
    "<div style='text-align:center; opacity:0.6; font-size:0.875rem;'>"
    "Developed by <strong>Masoem University</strong> – Fakultas Teknik"
    "</div>",
    unsafe_allow_html=True
)
