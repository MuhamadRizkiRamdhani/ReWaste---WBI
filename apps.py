import streamlit as st
import pickle
import numpy as np

st.set_page_config(
    page_title="Klasifikasi Pengelolaan Sampah",
    page_icon="🗑️",
    layout="centered"
)
# ── Load model ──────────────────────────────────────────────────────────────
@st.cache_resource
def load_model():
    with open("model.pkl", "rb") as f:
        return pickle.load(f)

model = load_model()

# ── Konstanta label ──────────────────────────────────────────────────────────
LABEL_CONFIG = {
    "KRITIS":  {"color": "#ffd5d5", "border": "#E74C3C", "icon": "🔴", "desc": "Pengelolaan sampah dalam kondisi kritis. Diperlukan tindakan segera."},
    "WASPADA": {"color": "#fff3cd", "border": "#F39C12", "icon": "🟡", "desc": "Pengelolaan sampah perlu perhatian lebih. Risiko meningkat."},
    "AMAN":    {"color": "#d4edda", "border": "#27AE60", "icon": "🟢", "desc": "Pengelolaan sampah berjalan dengan baik."},
}

# ── Halaman ──────────────────────────────────────────────────────────────────


st.markdown(
    "<h1 style='text-align:center;'>🗑️ Klasifikasi Pengelolaan Sampah</h1>"
    "<p style='text-align:center; color:gray;'>Kota Bandung — Berbasis Waste Burden Index (WBI)</p>",
    unsafe_allow_html=True
)
st.divider()

# ── Penjelasan fitur ─────────────────────────────────────────────────────────
with st.expander("ℹ️ Panduan Pengisian Fitur"):
    st.markdown("""
| Fitur | Keterangan | Rentang Umum |
|---|---|---|
| **Rasio Angkut** | Proporsi sampah yang berhasil diangkut dari total input | 0.0 – 1.0 |
| **Rasio Diolah** | Proporsi sampah yang berhasil diolah | 0.0 – 1.0 |
| **Rasio Sisa** | Proporsi sampah yang tersisa (tidak terangkut/diolah) | 0.0 – 1.0 |
| **Indeks Jarak** | Indeks jarak tempuh TPS ke TPA (dinormalisasi) | 0.0 – 1.0 |
    """)

# ── Pilihan mode input ───────────────────────────────────────────────────────
mode = st.radio("Pilih metode input:", ["Input Manual", "Pilih Contoh Data SWK"], horizontal=True)

CONTOH_DATA = {
    "SWK Bojonagara":  {"rasio_angkut": 0.55, "rasio_diolah": 0.30, "rasio_sisa": 0.45, "indeks_jarak": 0.80},
    "SWK Cibeunying": {"rasio_angkut": 0.72, "rasio_diolah": 0.50, "rasio_sisa": 0.28, "indeks_jarak": 0.55},
    "SWK Tegallega":     {"rasio_angkut": 0.90, "rasio_diolah": 0.75, "rasio_sisa": 0.10, "indeks_jarak": 0.30},
    "SWK Ubermanik":     {"rasio_angkut": 0.90, "rasio_diolah": 0.75, "rasio_sisa": 0.10, "indeks_jarak": 0.30},
    "SWK Kordoba":     {"rasio_angkut": 0.90, "rasio_diolah": 0.75, "rasio_sisa": 0.10, "indeks_jarak": 0.30},
    "SWK Karees":     {"rasio_angkut": 0.90, "rasio_diolah": 0.75, "rasio_sisa": 0.10, "indeks_jarak": 0.30}
    
}

if mode == "Pilih Contoh Data SWK":
    pilihan = st.selectbox("Pilih SWK:", list(CONTOH_DATA.keys()))
    data = CONTOH_DATA[pilihan]
    rasio_angkut  = data["rasio_angkut"]
    rasio_diolah  = data["rasio_diolah"]
    rasio_sisa    = data["rasio_sisa"]
    indeks_jarak  = data["indeks_jarak"]
    st.info(f"Data otomatis terisi untuk: **{pilihan}**")
else:
    rasio_angkut  = None
    rasio_diolah  = None
    rasio_sisa    = None
    indeks_jarak  = None

# ── Form input ───────────────────────────────────────────────────────────────
st.markdown("### 📥 Masukkan Data Fitur")
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

# ── Prediksi ─────────────────────────────────────────────────────────────────
st.markdown("")
if st.button("🔍 Prediksi Klasifikasi", use_container_width=True, type="primary"):
    fitur = np.array([[rasio_angkut, rasio_diolah, rasio_sisa, indeks_jarak]])
    
    try:
        prediksi = model.predict(fitur)[0]
        label = str(prediksi).strip().upper()
        
        # Fallback jika label tidak dikenali
        if label not in LABEL_CONFIG:
            label = "WASPADA"
        
        cfg = LABEL_CONFIG[label]

        # Coba ambil probabilitas (jika model mendukung)
        proba_html = ""
        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(fitur)[0]
            classes = [str(c).upper() for c in model.classes_]
            proba_rows = "".join(
                f"<tr><td>{LABEL_CONFIG.get(c, {}).get('icon', '')} {c}</td>"
                f"<td><b>{p*100:.1f}%</b></td></tr>"
                for c, p in sorted(zip(classes, proba), key=lambda x: -x[1])
            )
            proba_html = f"""
            <p style='margin-top:12px; font-weight:bold;'>Probabilitas per Label:</p>
            <table style='width:100%; border-collapse:collapse;'>
              <tr style='background:#f0f0f0;'><th style='text-align:left;padding:4px'>Label</th><th style='text-align:left;padding:4px'>Probabilitas</th></tr>
              {proba_rows}
            </table>
            """

        st.markdown(f"""
            <div style='background-color:#0D9AAC;
                        border-left: 6px solid {cfg["border"]};
                        padding:20px; border-radius:8px; margin-top:10px;'>
                <h2 style='margin:0;'>{cfg["icon"]} Status: <b>{label}</b></h2>
                <p style='margin:8px 0 0 0;'>{cfg["desc"]}</p>
                {proba_html}
            </div>
        """, unsafe_allow_html=True)

        # Ringkasan fitur
        st.markdown("### 🧾 Ringkasan Input")
        col_a, col_b, col_c, col_d = st.columns(4)
        col_a.metric("Rasio Angkut", f"{rasio_angkut:.3f}")
        col_b.metric("Rasio Diolah", f"{rasio_diolah:.3f}")
        col_c.metric("Rasio Sisa",   f"{rasio_sisa:.3f}")
        col_d.metric("Indeks Jarak", f"{indeks_jarak:.3f}")

        # Rekomendasi otomatis
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
        st.error(f"Terjadi kesalahan saat prediksi: {e}")

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    "<div style='text-align:center; color:#888888; font-size:14px;'>"
    "Developed by <strong>Masoem University</strong> – Fakultas Teknik"
    "</div>",
    unsafe_allow_html=True
)
