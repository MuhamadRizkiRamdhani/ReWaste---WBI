import streamlit as st
import pickle
import numpy as np

st.set_page_config(
    page_title="Klasifikasi Pengelolaan Sampah",
    layout="centered"
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
    
    .prob-table td {
        padding: 0.5rem;
        border-bottom: 1px solid rgba(128, 128, 128, 0.1);
    }
    
    .prob-table tr:last-child td {
        border-bottom: none;
    }
    
    .prob-bar {
        background: linear-gradient(90deg, var(--primary-color) 0%, var(--primary-color) var(--percent), rgba(128,128,128,0.2) var(--percent));
        border-radius: 4px;
        height: 6px;
        width: 100%;
        margin-top: 4px;
    }
    
    .info-box {
        background: rgba(70, 130, 200, 0.1);
        border-left: 4px solid var(--primary-color);
        padding: 1rem;
        border-radius: var(--border-radius);
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

# Konstanta label tanpa emoticon
LABEL_CONFIG = {
    "KRITIS": {
        "color": "#E74C3C", 
        "bg": "rgba(231, 76, 60, 0.15)", 
        "border": "#E74C3C",
        "desc": "Pengelolaan sampah dalam kondisi kritis. Diperlukan tindakan segera."
    },
    "WASPADA": {
        "color": "#F39C12", 
        "bg": "rgba(243, 156, 18, 0.15)", 
        "border": "#F39C12",
        "desc": "Pengelolaan sampah perlu perhatian lebih. Risiko meningkat."
    },
    "AMAN": {
        "color": "#27AE60", 
        "bg": "rgba(39, 174, 96, 0.15)", 
        "border": "#27AE60",
        "desc": "Pengelolaan sampah berjalan dengan baik."
    },
}

# Header
st.markdown(
    "<h1 style='text-align:center; font-weight:700; letter-spacing:-0.02em;'>Klasifikasi Pengelolaan Sampah</h1>"
    "<p style='text-align:center; opacity:0.7; margin-top:-0.5rem;'>Kota Bandung — Berbasis Waste Burden Index (WBI)</p>",
    unsafe_allow_html=True
)
st.divider()

# Panduan fitur
with st.expander("Panduan Pengisian Fitur", expanded=False):
    st.markdown("""
    | Fitur | Keterangan | Rentang |
    |---|---|---|
    | **Rasio Angkut** | Proporsi sampah yang berhasil diangkut dari total input | 0.0 – 1.0 |
    | **Rasio Diolah** | Proporsi sampah yang berhasil diolah | 0.0 – 1.0 |
    | **Rasio Sisa** | Proporsi sampah yang tersisa (tidak terangkut/diolah) | 0.0 – 1.0 |
    | **Indeks Jarak** | Indeks jarak tempuh TPS ke TPA (dinormalisasi) | 0.0 – 1.0 |
    
    > **Catatan**: Nilai mendekati 1.0 menunjukkan kondisi yang lebih baik untuk rasio angkut dan diolah, namun perlu diwaspadai untuk rasio sisa dan indeks jarak.
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
    st.info(f"Data otomatis terisi untuk: **{pilihan}**")
else:
    rasio_angkut = None
    rasio_diolah = None
    rasio_sisa = None
    indeks_jarak = None

# Form input
st.markdown("### Input Data Fitur")
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
if st.button("Klasifikasikan", use_container_width=True, type="primary"):
    fitur = np.array([[rasio_angkut, rasio_diolah, rasio_sisa, indeks_jarak]])
    
    try:
        prediksi = model.predict(fitur)[0]
        label = str(prediksi).strip().upper()
        
        if label not in LABEL_CONFIG:
            label = "WASPADA"
        
        cfg = LABEL_CONFIG[label]
        
        # Probabilitas
        proba_html = ""
        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(fitur)[0]
            classes = [str(c).upper() for c in model.classes_]
            
            proba_rows = ""
            for c, p in sorted(zip(classes, proba), key=lambda x: -x[1]):
                proba_rows += f"""
                <tr>
                    <td style="padding:0.5rem 0;"><strong>{c}</strong></td>
                    <td style="padding:0.5rem 0; text-align:right;"><strong>{p*100:.1f}%</strong></td>
                </tr>
                <tr>
                    <td colspan="2" style="padding:0 0 0.5rem 0;">
                        <div class="prob-bar" style="--percent: {p*100}%"></div>
                    </td>
                </tr>
                """
            
            proba_html = f"""
            <div style="margin-top: 1rem;">
                <p style="font-weight:600; margin-bottom:0.5rem;">Probabilitas per Kategori</p>
                <table style="width:100%;">
                    {proba_rows}
                </table>
            </div>
            """
        
        # Status card
        st.markdown(f"""
        <div class="status-card" style="border-left: 4px solid {cfg['border']}; background: {cfg['bg']};">
            <h2 style="color: {cfg['color']};">Status: {label}</h2>
            <p>{cfg['desc']}</p>
            {proba_html}
        </div>
        """, unsafe_allow_html=True)
        
        # Ringkasan input dengan metric cards
        st.markdown("### Ringkasan Input")
        col_a, col_b, col_c, col_d = st.columns(4)
        
        with col_a:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Rasio Angkut</div>
                <div class="metric-value">{rasio_angkut:.3f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_b:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Rasio Diolah</div>
                <div class="metric-value">{rasio_diolah:.3f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_c:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Rasio Sisa</div>
                <div class="metric-value">{rasio_sisa:.3f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_d:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Indeks Jarak</div>
                <div class="metric-value">{indeks_jarak:.3f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Rekomendasi
        st.markdown("### Rekomendasi")
        rekomendasi = []
        if rasio_sisa > 0.3:
            rekomendasi.append("Rasio sisa tinggi — tambah frekuensi pengangkutan atau kapasitas TPS.")
        if rasio_angkut < 0.7:
            rekomendasi.append("Rasio angkut rendah — evaluasi armada dan jadwal pengangkutan.")
        if rasio_diolah < 0.4:
            rekomendasi.append("Rasio diolah rendah — tingkatkan kapasitas fasilitas pengolahan.")
        if indeks_jarak > 0.7:
            rekomendasi.append("Jarak ke TPA jauh — pertimbangkan optimasi rute atau TPA alternatif.")
        if not rekomendasi:
            rekomendasi.append("Semua indikator dalam kondisi baik. Pertahankan performa saat ini.")
        
        for r in rekomendasi:
            st.markdown(f"• {r}")
            
    except Exception as e:
        st.error(f"Terjadi kesalahan saat prediksi: {e}")

# Footer
st.divider()
st.markdown(
    "<div style='text-align:center; opacity:0.6; font-size:0.875rem;'>"
    "Developed by <strong>Masoem University</strong> – Fakultas Teknik"
    "</div>",
    unsafe_allow_html=True
)
