import streamlit as st
import pickle
import numpy as np
import geopandas as gpd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
import json

st.set_page_config(
    page_title="Klasifikasi Pengelolaan Sampah",
    layout="wide"  # Ubah ke wide untuk peta lebih lebar
)

# Custom CSS untuk styling modern dan responsif tema
st.markdown("""
<style>
    /* Variabel CSS untuk tema gelap/terang */
    :root {
        --card-bg: var(--secondary-background-color);
        --text-primary: var(--text-color);
        --text-secondary: var(--secondary-text-color);
        --border-radius: 12px;
        --shadow-sm: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
        --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
    }
    
    /* Status card styling */
    .status-card {
        background: var(--secondary-background-color);
        border-radius: var(--border-radius);
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: var(--shadow-md);
        transition: all 0.3s ease;
    }
    
    .status-card h2 {
        margin: 0;
        font-weight: 600;
        letter-spacing: -0.02em;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .status-card p {
        margin: 0.75rem 0 0 0;
        opacity: 0.85;
    }
    
    .metric-card {
        background: var(--secondary-background-color);
        border-radius: var(--border-radius);
        padding: 1rem;
        text-align: center;
        box-shadow: var(--shadow-sm);
        transition: all 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-md);
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
    
    .recommendation-item {
        padding: 0.5rem 0;
        border-bottom: 1px solid rgba(128, 128, 128, 0.2);
    }
    
    .recommendation-item:last-child {
        border-bottom: none;
    }
    
    .prob-table {
        width: 100%;
        margin-top: 0.75rem;
        border-collapse: collapse;
    }
    
    .prob-table tr td {
        padding: 0.5rem;
        border-bottom: 1px solid rgba(128, 128, 128, 0.1);
    }
    
    .prob-table tr:last-child td {
        border-bottom: none;
    }
    
    .prob-bar-container {
        width: 100%;
        background: rgba(128, 128, 128, 0.2);
        border-radius: 4px;
        height: 6px;
        overflow: hidden;
    }
    
    .prob-bar {
        background: linear-gradient(90deg, var(--primary-color) 0%, var(--primary-color) var(--percent), transparent var(--percent));
        height: 100%;
        width: 100%;
        border-radius: 4px;
        transition: width 0.3s ease;
    }
    
    .info-box {
        background: rgba(70, 130, 200, 0.1);
        border-left: 4px solid var(--primary-color);
        padding: 1rem;
        border-radius: var(--border-radius);
        margin: 1rem 0;
    }
    
    /* Icon styling */
    .status-icon {
        font-size: 1.75rem;
        filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
    }
    
    /* Map container */
    .map-container {
        border-radius: var(--border-radius);
        overflow: hidden;
        box-shadow: var(--shadow-md);
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Load model
@st.cache_resource
def load_model():
    with open("model.pkl", "rb") as f:
        return pickle.load(f)

model = load_model()

# Load GeoJSON data (kita buat data contoh, ganti dengan file GeoJSON asli jika ada)
@st.cache_data
def load_geojson():
    gdf = gpd.read_file("3273-kota-bandung-level-kewilayahan.json")  # Ganti dengan file asli
    return gdf

# Konstanta label dengan icon elegant
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

# Sidebar untuk kontrol peta
with st.sidebar:
    st.markdown("### 🗺️ Peta Sebaran SWK")
    st.markdown("---")
    show_map = st.checkbox("Tampilkan Peta", value=True)
    show_labels = st.checkbox("Tampilkan Label SWK", value=True)
    st.markdown("---")
    st.markdown("**Keterangan Warna:**")
    st.markdown("🔴 **Merah**: Kritis")
    st.markdown("🟡 **Kuning**: Waspada")
    st.markdown("🟢 **Hijau**: Aman")

# Header
st.markdown(
    "<h1 style='text-align:center; font-weight:700; letter-spacing:-0.02em;'>🗑️ Klasifikasi Pengelolaan Sampah</h1>"
    "<p style='text-align:center; opacity:0.7; margin-top:-0.5rem;'>Kota Bandung — Berbasis Waste Burden Index (WBI)</p>",
    unsafe_allow_html=True
)
st.divider()

# Layout dengan 2 kolom: kiri untuk input, kanan untuk peta
col_left, col_right = st.columns([1, 1.2])

with col_left:
    # Panduan fitur
    with st.expander("📋 Panduan Pengisian Fitur", expanded=False):
        st.markdown("""
        | Fitur | Keterangan | Rentang |
        |---|---|---|
        | **Rasio Angkut** | Proporsi sampah yang berhasil diangkut | 0.0 – 1.0 |
        | **Rasio Diolah** | Proporsi sampah yang berhasil diolah | 0.0 – 1.0 |
        | **Rasio Sisa** | Proporsi sampah yang tersisa | 0.0 – 1.0 |
        | **Indeks Jarak** | Indeks jarak tempuh TPS ke TPA | 0.0 – 1.0 |
        
        > **Catatan**: Nilai mendekati 1.0 lebih baik untuk rasio angkut dan diolah, tapi perlu diwaspadai untuk rasio sisa dan indeks jarak.
        """)
    
    # Mode input
    mode = st.radio("Pilih metode input:", ["Input Manual", "Pilih Contoh Data SWK"], horizontal=True)
    
    CONTOH_DATA = {
        "SWK Bojonagara": {"rasio_angkut": 0.55, "rasio_diolah": 0.30, "rasio_sisa": 0.45, "indeks_jarak": 0.80},
        "SWK Cibeunying": {"rasio_angkut": 0.72, "rasio_diolah": 0.50, "rasio_sisa": 0.28, "indeks_jarak": 0.55},
        "SWK Tegallega": {"rasio_angkut": 0.90, "rasio_diolah": 0.75, "rasio_sisa": 0.10, "indeks_jarak": 0.30},
        "SWK Ubermanik": {"rasio_angkut": 0.88, "rasio_diolah": 0.70, "rasio_sisa": 0.12, "indeks_jarak": 0.35},
        "SWK Kordoba": {"rasio_angkut": 0.85, "rasio_diolah": 0.65, "rasio_sisa": 0.15, "indeks_jarak": 0.40},
        "SWK Karees": {"rasio_angkut": 0.82, "rasio_diolah": 0.60, "rasio_sisa": 0.18, "indeks_jarak": 0.45}
    }
    
    if mode == "Pilih Contoh Data SWK":
        pilihan = st.selectbox("Pilih SWK:", list(CONTOH_DATA.keys()))
        data = CONTOH_DATA[pilihan]
        rasio_angkut = data["rasio_angkut"]
        rasio_diolah = data["rasio_diolah"]
        rasio_sisa = data["rasio_sisa"]
        indeks_jarak = data["indeks_jarak"]
        st.info(f"📌 Data otomatis terisi untuk: **{pilihan}**")
    else:
        rasio_angkut = None
        rasio_diolah = None
        rasio_sisa = None
        indeks_jarak = None
    
    # Form input
    st.markdown("### 📊 Input Data Fitur")
    col1, col2 = st.columns(2)
    
    with col1:
        rasio_angkut = st.number_input(
            "Rasio Angkut",
            min_value=0.0, max_value=1.0, step=0.01, format="%.3f",
            value=float(rasio_angkut) if rasio_angkut is not None else 0.75,
            help="Proporsi sampah yang berhasil diangkut (0.0 – 1.0)"
        )
        rasio_diolah = st.number_input(
            "Rasio Diolah",
            min_value=0.0, max_value=1.0, step=0.01, format="%.3f",
            value=float(rasio_diolah) if rasio_diolah is not None else 0.50,
            help="Proporsi sampah yang berhasil diolah (0.0 – 1.0)"
        )
    
    with col2:
        rasio_sisa = st.number_input(
            "Rasio Sisa",
            min_value=0.0, max_value=1.0, step=0.01, format="%.3f",
            value=float(rasio_sisa) if rasio_sisa is not None else 0.25,
            help="Proporsi sampah yang tersisa (0.0 – 1.0)"
        )
        indeks_jarak = st.number_input(
            "Indeks Jarak",
            min_value=0.0, max_value=1.0, step=0.01, format="%.3f",
            value=float(indeks_jarak) if indeks_jarak is not None else 0.40,
            help="Indeks jarak TPS ke TPA yang dinormalisasi (0.0 – 1.0)"
        )
    
    # Prediksi
    if st.button("🔍 Klasifikasikan", use_container_width=True, type="primary"):
        fitur = np.array([[rasio_angkut, rasio_diolah, rasio_sisa, indeks_jarak]])
        
        try:
            prediksi = model.predict(fitur)[0]
            label = str(prediksi).strip().upper()
            
            if label not in LABEL_CONFIG:
                label = "WASPADA"
            
            cfg = LABEL_CONFIG[label]
            
            # Status card dengan Streamlit native components
            with st.container():
                if label == "KRITIS":
                    st.error(f"**{cfg['icon']} STATUS: {label}**")
                elif label == "WASPADA":
                    st.warning(f"**{cfg['icon']} STATUS: {label}**")
                else:
                    st.success(f"**{cfg['icon']} STATUS: {label}**")
                
                st.markdown(cfg['desc'])
            
            # Probabilitas menggunakan komponen Streamlit native
            if hasattr(model, "predict_proba"):
                st.markdown("### 📈 Probabilitas per Kategori")
                proba = model.predict_proba(fitur)[0]
                classes = [str(c).upper() for c in model.classes_]
                
                proba_data = []
                for c, p in sorted(zip(classes, proba), key=lambda x: -x[1]):
                    proba_data.append({"Kategori": c, "Probabilitas": f"{p*100:.1f}%", "Nilai": p})
                
                for item in proba_data:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**{item['Kategori']}**")
                        st.progress(item['Nilai'], text=f"{item['Probabilitas']}")
                    with col2:
                        st.markdown(f"<h3 style='text-align:right; margin:0;'>{item['Probabilitas']}</h3>", 
                                   unsafe_allow_html=True)
            
            # Ringkasan input dengan metric cards
            st.markdown("### 📊 Ringkasan Input")
            col_a, col_b, col_c, col_d = st.columns(4)
            
            with col_a:
                st.metric("Rasio Angkut", f"{rasio_angkut:.3f}")
            with col_b:
                st.metric("Rasio Diolah", f"{rasio_diolah:.3f}")
            with col_c:
                st.metric("Rasio Sisa", f"{rasio_sisa:.3f}")
            with col_d:
                st.metric("Indeks Jarak", f"{indeks_jarak:.3f}")
            
            # Rekomendasi
            st.markdown("### 💡 Rekomendasi")
            rekomendasi = []
            if rasio_sisa > 0.3:
                rekomendasi.append("⚠️ **Rasio sisa tinggi** — tambah frekuensi pengangkutan atau kapasitas TPS.")
            if rasio_angkut < 0.7:
                rekomendasi.append("⚠️ **Rasio angkut rendah** — evaluasi armada dan jadwal pengangkutan.")
            if rasio_diolah < 0.4:
                rekomendasi.append("⚠️ **Rasio diolah rendah** — tingkatkan kapasitas fasilitas pengolahan.")
            if indeks_jarak > 0.7:
                rekomendasi.append("⚠️ **Jarak ke TPA jauh** — pertimbangkan optimasi rute atau TPA alternatif.")
            if not rekomendasi:
                rekomendasi.append("✅ Semua indikator dalam kondisi baik. Pertahankan performa saat ini.")
            
            for r in rekomendasi:
                st.markdown(r)
                
        except Exception as e:
            st.error(f"❌ Terjadi kesalahan saat prediksi: {e}")

with col_right:
    if show_map:
        st.markdown("### 🗺️ Peta Wilayah SWK Kota Bandung")
        
        # Load data SWK
        swk_data = load_geojson()
        
        # Hitung status untuk setiap SWK berdasarkan data contoh
        swk_status = {}
        for nama, data in CONTOH_DATA.items():
            fitur = np.array([[data["rasio_angkut"], data["rasio_diolah"], data["rasio_sisa"], data["indeks_jarak"]]])
            try:
                pred = model.predict(fitur)[0]
                swk_status[nama] = str(pred).strip().upper()
            except:
                swk_status[nama] = "WASPADA"
        
        # Buat peta dengan Folium
        center_lat = -6.9146
        center_lon = 107.6098
        m = folium.Map(location=[center_lat, center_lon], zoom_start=13, control_scale=True)
        
        # Tambahkan tile layer yang lebih professional
        folium.TileLayer('CartoDB positron', name='Light Map', show=True).add_to(m)
        folium.TileLayer('OpenStreetMap', name='Street Map', show=False).add_to(m)
        
        # Tambahkan marker untuk setiap SWK
        for nama, koord in swk_data.items():
            status = swk_status.get(nama, "WASPADA")
            
            # Tentukan warna marker berdasarkan status
            if status == "KRITIS":
                color = "red"
                icon_color = "white"
                status_text = "KRITIS"
            elif status == "AMAN":
                color = "green"
                icon_color = "white"
                status_text = "AMAN"
            else:
                color = "orange"
                icon_color = "white"
                status_text = "WASPADA"
            
            # Data parameter untuk ditampilkan di popup
            param_data = CONTOH_DATA.get(nama, {})
            
            # Buat popup HTML
            popup_html = f"""
            <div style="min-width: 200px;">
                <h4 style="margin: 0 0 10px 0; color: {color};">{nama}</h4>
                <p style="margin: 5px 0;"><strong>Status:</strong> {status_text}</p>
                <hr style="margin: 8px 0;">
                <p style="margin: 5px 0; font-size: 12px;"><strong>Rasio Angkut:</strong> {param_data.get('rasio_angkut', 0):.2f}</p>
                <p style="margin: 5px 0; font-size: 12px;"><strong>Rasio Diolah:</strong> {param_data.get('rasio_diolah', 0):.2f}</p>
                <p style="margin: 5px 0; font-size: 12px;"><strong>Rasio Sisa:</strong> {param_data.get('rasio_sisa', 0):.2f}</p>
                <p style="margin: 5px 0; font-size: 12px;"><strong>Indeks Jarak:</strong> {param_data.get('indeks_jarak', 0):.2f}</p>
            </div>
            """
            
            # Tambahkan marker
            folium.Marker(
                location=[koord["lat"], koord["lon"]],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"{nama} - {status_text}",
                icon=folium.Icon(color=color, icon_color=icon_color, icon="info-sign", prefix='glyphicon')
            ).add_to(m)
            
            # Tambahkan label jika dipilih
            if show_labels:
                folium.Marker(
                    location=[koord["lat"] + 0.002, koord["lon"]],
                    icon=folium.DivIcon(
                        html=f'<div style="font-size: 10px; font-weight: bold; background: white; padding: 2px 6px; border-radius: 4px; border: 1px solid {color}; white-space: nowrap;">{nama}</div>'
                    )
                ).add_to(m)
        
        # Tambahkan legend
        legend_html = '''
        <div style="position: fixed; bottom: 30px; right: 30px; z-index: 1000; background: white; padding: 10px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.2); font-size: 12px;">
            <strong>Status SWK</strong><br>
            <span style="color: red;">●</span> Kritis<br>
            <span style="color: orange;">●</span> Waspada<br>
            <span style="color: green;">●</span> Aman
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Tambahkan kontrol layer
        folium.LayerControl().add_to(m)
        
        # Tampilkan peta
        st.components.v1.html(m._repr_html_(), height=600)
        
        # Informasi tambahan
        st.caption("Klik pada marker untuk melihat detail parameter setiap SWK")
    else:
        st.info("🗺️ Aktifkan 'Tampilkan Peta' di sidebar untuk melihat visualisasi sebaran SWK Kota Bandung")

# Footer
st.divider()
st.markdown(
    "<div style='text-align:center; opacity:0.6; font-size:0.875rem;'>"
    "Developed with ❤️ by <strong>Masoem University</strong> – Fakultas Teknik<br>"
    "Data SWK berdasarkan klasifikasi model WBI"
    "</div>",
    unsafe_allow_html=True
)
