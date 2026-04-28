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

# Load model
@st.cache_resource
def load_model():
    with open("model.pkl", "rb") as f:
        return pickle.load(f)

model = load_model()

# Inisialisasi session state
if 'wilayah_status' not in st.session_state:
    st.session_state.wilayah_status = {}

if 'wilayah_params' not in st.session_state:
    st.session_state.wilayah_params = {}

if 'prediction_made' not in st.session_state:
    st.session_state.prediction_made = False

# Konstanta label
LABEL_CONFIG = {
    "KRITIS": {
        "color": "#E74C3C", 
        "icon": "⚠️",
        "desc": "Pengelolaan sampah dalam kondisi kritis. Diperlukan tindakan segera."
    },
    "WASPADA": {
        "color": "#F39C12", 
        "icon": "📌",
        "desc": "Pengelolaan sampah perlu perhatian lebih. Risiko meningkat."
    },
    "AMAN": {
        "color": "#27AE60", 
        "icon": "✓",
        "desc": "Pengelolaan sampah berjalan dengan baik."
    },
}

# Data wilayah (manual karena GeoJSON mungkin bermasalah)
WILAYAH_DATA = {
    "Ujungberung": {"lat": -6.905, "lon": 107.685},
    "Cicendo": {"lat": -6.905, "lon": 107.605},
    "Bandung Kidul": {"lat": -6.945, "lon": 107.625},
    "Bandung Kulon": {"lat": -6.925, "lon": 107.585},
    "Bandung Wetan": {"lat": -6.895, "lon": 107.615},
    "Cibeunying": {"lat": -6.885, "lon": 107.635},
    "Coblong": {"lat": -6.875, "lon": 107.615},
    "Sumur Bandung": {"lat": -6.915, "lon": 107.605},
}

# Header
st.title("🗑️ Klasifikasi Pengelolaan Sampah")
st.caption("Kota Bandung — Berbasis Waste Burden Index (WBI)")
st.divider()

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Pengaturan")
    show_labels = st.checkbox("Tampilkan Label", value=True)
    st.markdown("---")
    st.markdown("**Keterangan Warna Marker:**")
    st.markdown("🔴 **Merah**: Kritis")
    st.markdown("🟡 **Kuning**: Waspada")
    st.markdown("🟢 **Hijau**: Aman")
    st.markdown("⚪ **Abu-abu**: Belum Diprediksi")
    
    if st.button("Reset Semua Data"):
        st.session_state.wilayah_status = {}
        st.session_state.wilayah_params = {}
        st.session_state.prediction_made = False
        st.rerun()

# Layout 2 kolom
col_left, col_right = st.columns([1, 1.2])

with col_left:
    with st.expander("📋 Panduan Pengisian"):
        st.markdown("""
        | Parameter | Keterangan | Rentang |
        |---|---|---|
        | **Rasio Angkut** | Proporsi sampah yang berhasil diangkut | 0.0 – 1.0 |
        | **Rasio Diolah** | Proporsi sampah yang berhasil diolah | 0.0 – 1.0 |
        | **Rasio Sisa** | Proporsi sampah yang tersisa | 0.0 – 1.0 |
        | **Indeks Jarak** | Indeks jarak tempuh TPS ke TPA | 0.0 – 1.0 |
        """)
    
    selected_wilayah = st.selectbox("Pilih Wilayah:", list(WILAYAH_DATA.keys()))
    
    # Ambil data tersimpan
    saved = st.session_state.wilayah_params.get(selected_wilayah, {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        rasio_angkut = st.number_input(
            "Rasio Angkut", min_value=0.0, max_value=1.0, step=0.01,
            value=float(saved.get('rasio_angkut', 0.75))
        )
        rasio_diolah = st.number_input(
            "Rasio Diolah", min_value=0.0, max_value=1.0, step=0.01,
            value=float(saved.get('rasio_diolah', 0.50))
        )
    
    with col2:
        rasio_sisa = st.number_input(
            "Rasio Sisa", min_value=0.0, max_value=1.0, step=0.01,
            value=float(saved.get('rasio_sisa', 0.25))
        )
        indeks_jarak = st.number_input(
            "Indeks Jarak", min_value=0.0, max_value=1.0, step=0.01,
            value=float(saved.get('indeks_jarak', 0.40))
        )
    
    if st.button("🔍 Klasifikasikan", type="primary", use_container_width=True):
        fitur = np.array([[rasio_angkut, rasio_diolah, rasio_sisa, indeks_jarak]])
        
        try:
            pred = model.predict(fitur)[0]
            label = str(pred).strip().upper()
            
            if label not in LABEL_CONFIG:
                label = "WASPADA"
            
            # Simpan ke session state
            st.session_state.wilayah_status[selected_wilayah] = label
            st.session_state.wilayah_params[selected_wilayah] = {
                "rasio_angkut": rasio_angkut,
                "rasio_diolah": rasio_diolah,
                "rasio_sisa": rasio_sisa,
                "indeks_jarak": indeks_jarak
            }
            st.session_state.prediction_made = True
            
            cfg = LABEL_CONFIG[label]
            
            # Tampilkan hasil
            if label == "KRITIS":
                st.error(f"**{cfg['icon']} STATUS: {label}**")
            elif label == "WASPADA":
                st.warning(f"**{cfg['icon']} STATUS: {label}**")
            else:
                st.success(f"**{cfg['icon']} STATUS: {label}**")
            
            st.write(cfg['desc'])
            
            # Probabilitas
            if hasattr(model, "predict_proba"):
                st.write("**Probabilitas:**")
                proba = model.predict_proba(fitur)[0]
                classes = [str(c).upper() for c in model.classes_]
                for c, p in zip(classes, proba):
                    st.progress(p, text=f"{c}: {p*100:.1f}%")
            
            # Ringkasan
            st.write("**Ringkasan Input:**")
            ma, mb, mc, md = st.columns(4)
            ma.metric("Rasio Angkut", f"{rasio_angkut:.3f}")
            mb.metric("Rasio Diolah", f"{rasio_diolah:.3f}")
            mc.metric("Rasio Sisa", f"{rasio_sisa:.3f}")
            md.metric("Indeks Jarak", f"{indeks_jarak:.3f}")
            
            st.rerun()
            
        except Exception as e:
            st.error(f"Error: {e}")

with col_right:
    st.markdown("### 🗺️ Peta Wilayah Kota Bandung")
    
    # Buat peta
    center_lat = -6.9146
    center_lon = 107.6098
    
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=12,
        tiles='OpenStreetMap'  # Pake yang pasti jalan
    )
    
    # Tambahkan marker untuk setiap wilayah
    for wilayah, coords in WILAYAH_DATA.items():
        status = st.session_state.wilayah_status.get(wilayah, "")
        
        # Tentukan warna
        if status == "KRITIS":
            color = "red"
            status_text = "KRITIS"
        elif status == "WASPADA":
            color = "orange"
            status_text = "WASPADA"
        elif status == "AMAN":
            color = "green"
            status_text = "AMAN"
        else:
            color = "gray"
            status_text = "Belum Diprediksi"
        
        # Data parameter
        params = st.session_state.wilayah_params.get(wilayah, {})
        
        # Popup info
        popup_text = f"""
        <b>{wilayah}</b><br>
        Status: <span style="color:{color}">{status_text}</span><br>
        <hr>
        Rasio Angkut: {params.get('rasio_angkut', '-')}<br>
        Rasio Diolah: {params.get('rasio_diolah', '-')}<br>
        Rasio Sisa: {params.get('rasio_sisa', '-')}<br>
        Indeks Jarak: {params.get('indeks_jarak', '-')}
        """
        
        # Tambah marker
        folium.Marker(
            location=[coords["lat"], coords["lon"]],
            popup=folium.Popup(popup_text, max_width=250),
            tooltip=f"{wilayah} - {status_text}",
            icon=folium.Icon(color=color, icon="info-sign")
        ).add_to(m)
        
        # Tambah label
        if show_labels:
            folium.Marker(
                location=[coords["lat"] + 0.008, coords["lon"]],
                icon=folium.DivIcon(
                    html=f'<div style="font-size: 10px; font-weight: bold; background: white; padding: 2px 6px; border-radius: 4px; border: 1px solid {color};">{wilayah}</div>'
                )
            ).add_to(m)
    
    # Legend
    legend_html = '''
    <div style="position: fixed; bottom: 30px; right: 30px; background: white; padding: 10px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); font-size: 12px; z-index: 1000;">
        <b>Status Wilayah</b><br>
        <span style="color:red;">●</span> Kritis<br>
        <span style="color:orange;">●</span> Waspada<br>
        <span style="color:green;">●</span> Aman<br>
        <span style="color:gray;">●</span> Belum Diprediksi
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Tampilkan peta
    st_folium(m, width=None, height=550)
    
    st.caption("Klik marker untuk melihat detail | Warna berubah setelah klasifikasi")

# Footer
st.divider()
st.markdown(
    "<div style='text-align:center; color:gray;'>Developed by Masoem University – Fakultas Teknik</div>",
    unsafe_allow_html=True
)
