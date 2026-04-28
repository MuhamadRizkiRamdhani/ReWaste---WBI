import streamlit as st
import pickle
import numpy as np
import pandas as pd

st.set_page_config(
    page_title="Klasifikasi Pengelolaan Sampah - Kota Bandung",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS untuk tampilan profesional eksekutif
st.markdown("""
<style>
    /* Reset & base */
    .main > div {
        padding: 0rem 1rem;
    }
    
    /* Header profesional */
    .executive-header {
        border-bottom: 3px solid #2C3E50;
        padding-bottom: 1rem;
        margin-bottom: 2rem;
    }
    
    .executive-title {
        font-size: 1.75rem;
        font-weight: 600;
        color: #2C3E50;
        letter-spacing: -0.01em;
        margin: 0;
    }
    
    .executive-subtitle {
        font-size: 0.875rem;
        color: #7F8C8D;
        margin-top: 0.25rem;
    }
    
    /* Status card profesional */
    .status-card {
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        border-left: 5px solid;
    }
    
    .status-card h3 {
        margin: 0 0 0.5rem 0;
        font-size: 1.25rem;
        font-weight: 600;
    }
    
    .status-card p {
        margin: 0;
        font-size: 0.875rem;
        line-height: 1.5;
    }
    
    /* Metric cards */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin: 1.5rem 0;
    }
    
    .metric-item {
        background: #F8F9FA;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        border: 1px solid #E9ECEF;
    }
    
    .metric-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #6C757D;
        margin-bottom: 0.5rem;
    }
    
    .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #2C3E50;
    }
    
    /* Tabel probabilitas */
    .probability-section {
        margin: 1.5rem 0;
        background: #F8F9FA;
        border-radius: 8px;
        padding: 1rem;
        border: 1px solid #E9ECEF;
    }
    
    .section-title {
        font-size: 0.875rem;
        font-weight: 600;
        color: #2C3E50;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #E9ECEF;
    }
    
    /* Rekomendasi */
    .recommendation-card {
        background: #F8F9FA;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 3px solid #2C3E50;
    }
    
    /* Dark mode adjustments */
    @media (prefers-color-scheme: dark) {
        .metric-item, .probability-section, .recommendation-card {
            background: #2D2D2D;
            border-color: #404040;
        }
        .metric-value, .section-title, .executive-title {
            color: #E0E0E0;
        }
        .metric-label, .executive-subtitle {
            color: #A0A0A0;
        }
    }
    
    /* Divider */
    .custom-divider {
        margin: 1.5rem 0;
        border-top: 1px solid #E9ECEF;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 1.5rem 0 0.5rem 0;
        font-size: 0.75rem;
        color: #6C757D;
        border-top: 1px solid #E9ECEF;
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Load model
@st.cache_resource
def load_model():
    with open("model.pkl", "rb") as f:
        return pickle.load(f)

model = load_model()

# Konstanta label
LABEL_CONFIG = {
    "KRITIS": {
        "color": "#C0392B",
        "bg": "#FADBD8",
        "border": "#C0392B",
        "desc": "Pengelolaan sampah dalam kondisi kritis. Diperlukan tindakan segera."
    },
    "WASPADA": {
        "color": "#D68910", 
        "bg": "#FDEBD0",
        "border": "#D68910",
        "desc": "Pengelolaan sampah perlu perhatian lebih. Risiko meningkat."
    },
    "AMAN": {
        "color": "#1E8449", 
        "bg": "#D5F5E3",
        "border": "#1E8449",
        "desc": "Pengelolaan sampah berjalan dengan baik."
    },
}

# Header profesional
st.markdown("""
<div class="executive-header">
    <div class="executive-title">Sistem Klasifikasi Pengelolaan Sampah</div>
    <div class="executive-subtitle">Dinas Lingkungan Hidup Kota Bandung | Waste Burden Index (WBI)</div>
</div>
""", unsafe_allow_html=True)

# Panduan fitur
with st.expander("Petunjuk Teknis", expanded=False):
    st.markdown("""
    **Definisi Parameter:**
    
    | Parameter | Deskripsi | Rentang |
    |---|---|---|
    | Rasio Angkut | Volume sampah terangkut / total volume sampah | 0.00 - 1.00 |
    | Rasio Diolah | Volume sampah terolah / total volume sampah | 0.00 - 1.00 |
    | Rasio Sisa | Volume sampah tidak terkelola / total volume sampah | 0.00 - 1.00 |
    | Indeks Jarak | Normalisasi jarak TPS ke TPA | 0.00 - 1.00 |
    
    > **Catatan:** Nilai optimal Rasio Angkut dan Rasio Diolah mendekati 1.00. Rasio Sisa dan Indeks Jarak semakin kecil semakin baik.
    """)

# Mode input
mode = st.radio("Metode Input Data:", ["Input Manual", "Contoh Data SWK"], horizontal=True)

CONTOH_DATA = {
    "SWK Bojonagara": {"rasio_angkut": 0.55, "rasio_diolah": 0.30, "rasio_sisa": 0.45, "indeks_jarak": 0.80},
    "SWK Cibeunying": {"rasio_angkut": 0.72, "rasio_diolah": 0.50, "rasio_sisa": 0.28, "indeks_jarak": 0.55},
    "SWK Tegallega": {"rasio_angkut": 0.90, "rasio_diolah": 0.75, "rasio_sisa": 0.10, "indeks_jarak": 0.30},
    "SWK Ubermanik": {"rasio_angkut": 0.88, "rasio_diolah": 0.70, "rasio_sisa": 0.12, "indeks_jarak": 0.35},
    "SWK Kordoba": {"rasio_angkut": 0.85, "rasio_diolah": 0.65, "rasio_sisa": 0.15, "indeks_jarak": 0.40},
    "SWK Karees": {"rasio_angkut": 0.82, "rasio_diolah": 0.60, "rasio_sisa": 0.18, "indeks_jarak": 0.45}
}

if mode == "Contoh Data SWK":
    pilihan = st.selectbox("Pilih Wilayah SWK:", list(CONTOH_DATA.keys()))
    data = CONTOH_DATA[pilihan]
    rasio_angkut = data["rasio_angkut"]
    rasio_diolah = data["rasio_diolah"]
    rasio_sisa = data["rasio_sisa"]
    indeks_jarak = data["indeks_jarak"]
    st.info(f"Data terisi: {pilihan}")
else:
    rasio_angkut = None
    rasio_diolah = None
    rasio_sisa = None
    indeks_jarak = None

# Form input
st.markdown("### Parameter Input")
col1, col2 = st.columns(2)

with col1:
    rasio_angkut = st.number_input(
        "Rasio Angkut",
        min_value=0.0, max_value=1.0, step=0.01, format="%.3f",
        value=float(rasio_angkut) if rasio_angkut is not None else 0.75
    )
    rasio_diolah = st.number_input(
        "Rasio Diolah",
        min_value=0.0, max_value=1.0, step=0.01, format="%.3f",
        value=float(rasio_diolah) if rasio_diolah is not None else 0.50
    )

with col2:
    rasio_sisa = st.number_input(
        "Rasio Sisa",
        min_value=0.0, max_value=1.0, step=0.01, format="%.3f",
        value=float(rasio_sisa) if rasio_sisa is not None else 0.25
    )
    indeks_jarak = st.number_input(
        "Indeks Jarak",
        min_value=0.0, max_value=1.0, step=0.01, format="%.3f",
        value=float(indeks_jarak) if indeks_jarak is not None else 0.40
    )

# Tombol analisis
col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
with col_btn2:
    analyze = st.button("Analisis Data", use_container_width=True, type="primary")

if analyze:
    fitur = np.array([[rasio_angkut, rasio_diolah, rasio_sisa, indeks_jarak]])
    
    try:
        prediksi = model.predict(fitur)[0]
        label = str(prediksi).strip().upper()
        
        if label not in LABEL_CONFIG:
            label = "WASPADA"
        
        cfg = LABEL_CONFIG[label]
        
        # Status card
        st.markdown("### Hasil Klasifikasi")
        
        if label == "KRITIS":
            st.markdown(f"""
            <div class="status-card" style="background:{cfg['bg']}; border-left-color:{cfg['border']};">
                <h3 style="color:{cfg['color']};">Status: {label}</h3>
                <p>{cfg['desc']}</p>
            </div>
            """, unsafe_allow_html=True)
        elif label == "WASPADA":
            st.markdown(f"""
            <div class="status-card" style="background:{cfg['bg']}; border-left-color:{cfg['border']};">
                <h3 style="color:{cfg['color']};">Status: {label}</h3>
                <p>{cfg['desc']}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="status-card" style="background:{cfg['bg']}; border-left-color:{cfg['border']};">
                <h3 style="color:{cfg['color']};">Status: {label}</h3>
                <p>{cfg['desc']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Probabilitas dengan tabel profesional
        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(fitur)[0]
            classes = [str(c).upper() for c in model.classes_]
            
            proba_df = pd.DataFrame([
                {"Kategori": c, "Probabilitas": f"{p*100:.1f}%", "Nilai": p}
                for c, p in sorted(zip(classes, proba), key=lambda x: -x[1])
            ])
            
            st.markdown('<div class="probability-section">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Distribusi Probabilitas</div>', unsafe_allow_html=True)
            
            for _, row in proba_df.iterrows():
                col1, col2, col3 = st.columns([2, 1, 3])
                with col1:
                    st.markdown(f"**{row['Kategori']}**")
                with col2:
                    st.markdown(f"<span style='font-weight:600;'>{row['Probabilitas']}</span>", unsafe_allow_html=True)
                with col3:
                    st.progress(row['Nilai'])
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Metric cards
        st.markdown('<div class="section-title">Ringkasan Parameter</div>', unsafe_allow_html=True)
        
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Rasio Angkut", f"{rasio_angkut:.3f}")
        with m2:
            st.metric("Rasio Diolah", f"{rasio_diolah:.3f}")
        with m3:
            st.metric("Rasio Sisa", f"{rasio_sisa:.3f}")
        with m4:
            st.metric("Indeks Jarak", f"{indeks_jarak:.3f}")
        
        # Rekomendasi teknis
        st.markdown('<div class="section-title">Rekomendasi Teknis</div>', unsafe_allow_html=True)
        
        rekomendasi = []
        if rasio_sisa > 0.3:
            rekomendasi.append("• Meningkatkan frekuensi pengangkutan sampah")
            rekomendasi.append("• Optimalisasi kapasitas TPS")
        if rasio_angkut < 0.7:
            rekomendasi.append("• Evaluasi jumlah dan rute armada pengangkut")
            rekomendasi.append("• Penjadwalan ulang operasional")
        if rasio_diolah < 0.4:
            rekomendasi.append("• Peningkatan kapasitas fasilitas pengolahan")
            rekomendasi.append("• Optimalisasi pengolahan sampah TPS")
        if indeks_jarak > 0.7:
            rekomendasi.append("• Kajian rute transportasi sampah")
            rekomendasi.append("• Evaluasi lokasi TPA alternatif")
        
        if not rekomendasi:
            st.markdown('<div class="recommendation-card">✓ Seluruh parameter dalam batas optimal. Pertahankan kinerja saat ini.</div>', unsafe_allow_html=True)
        else:
            for r in rekomendasi:
                st.markdown(f'<div class="recommendation-card">{r}</div>', unsafe_allow_html=True)
        
        # Tanda tangan digital (opsional)
        st.caption(f"*Hasil analisis berdasarkan model WBI • {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}*")
        
    except Exception as e:
        st.error(f"Error: {e}")

# Footer
st.markdown("""
<div class="footer">
    Universitas Ma'soem<br>
    Fakultas Teknik | © 2026
</div>
""", unsafe_allow_html=True)
