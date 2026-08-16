import streamlit as st
import pandas as pd
import numpy as np
import joblib

# Plotly dipakai untuk gauge chart. Kalau belum ter-install, app tetap
# jalan dengan fallback progress bar sederhana.
try:
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# ============================================================
# KONFIGURASI HALAMAN
# ============================================================
st.set_page_config(
    page_title="Jendela Udara | Safe-Air Planner",
    page_icon="🌬️",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ============================================================
# CUSTOM CSS — TEMA "JENDELA UDARA"
# Palet terinspirasi langit: biru cerah = aman, kuning kabut = waspada,
# merah senja = bahaya. Motif garis tipis di header meniru kisi jendela.
# ============================================================
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

:root {
    --sky-deep: #155E9E;
    --sky-bright: #2E9BF0;
    --air-safe: #17A673;
    --air-warn: #E8A317;
    --air-danger: #E2483D;
    --ink: #16324F;
}

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
    color: var(--ink);
}
h1, h2, h3, h4, .hero-title { font-family: 'Poppins', sans-serif; }

#MainMenu, footer { visibility: hidden; }

/* ---------- HERO ---------- */
.hero-wrap {
    position: relative;
    background: linear-gradient(135deg, var(--sky-deep) 0%, var(--sky-bright) 100%);
    border-radius: 22px;
    padding: 2.4rem 1.8rem;
    margin-bottom: 1.6rem;
    overflow: hidden;
    box-shadow: 0 14px 34px rgba(21, 94, 158, 0.28);
}
.hero-wrap::before {
    content: "";
    position: absolute; inset: 0;
    background-image:
        linear-gradient(rgba(255,255,255,0.14) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.14) 1px, transparent 1px);
    background-size: 34px 34px;
    opacity: 0.6;
}
.hero-inner { position: relative; z-index: 1; text-align: center; }
.hero-title {
    color: #fff; font-weight: 800; font-size: 2.1rem; margin: 0 0 .4rem 0;
    letter-spacing: -0.02em;
}
.hero-sub {
    color: rgba(255,255,255,0.92); font-size: .98rem; max-width: 30rem; margin: 0 auto;
}

/* ---------- CARD CONTAINER (native st.container(border=True)) ---------- */
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 18px !important;
    box-shadow: 0 6px 18px rgba(21, 50, 79, 0.06);
}

/* ---------- RESULT CARDS ---------- */
.result-card {
    border-radius: 18px;
    padding: 1.4rem 1.6rem;
    margin-top: .4rem;
    border-left: 6px solid transparent;
}
.result-safe   { background:#EAFBF4; border-left-color: var(--air-safe); }
.result-warn   { background:#FFF8E8; border-left-color: var(--air-warn); }
.result-danger { background:#FDEDEC; border-left-color: var(--air-danger); }
.result-title  { font-family:'Poppins', sans-serif; font-weight:700; font-size:1.1rem; margin-bottom:.3rem; color: var(--ink); }
.result-body   { font-size:.95rem; line-height:1.55; color: var(--ink); }

/* ---------- SUBMIT BUTTON ---------- */
div[data-testid="stFormSubmitButton"] button,
div.stButton > button {
    background: linear-gradient(135deg, var(--sky-deep), var(--sky-bright));
    color: #fff; border: none; border-radius: 999px;
    padding: .65rem 1rem; font-weight: 700;
    box-shadow: 0 8px 18px rgba(46,155,240,0.35);
    transition: transform .15s ease, box-shadow .15s ease;
}
div[data-testid="stFormSubmitButton"] button:hover,
div.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 22px rgba(46,155,240,0.45);
    color: #fff;
}

/* ---------- SIDEBAR ---------- */
/* Background terang dipasangkan eksplisit dengan warna teks gelap,
   supaya tetap kontras baik app jalan di tema Light maupun Dark. */
[data-testid="stSidebar"] {
    background: #F5F9FD !important;
}
[data-testid="stSidebar"] * {
    color: var(--ink) !important;
}
[data-testid="stSidebar"] small {
    color: rgba(22, 50, 79, 0.65) !important;
}

@media (prefers-reduced-motion: reduce) {
    * { transition: none !important; animation: none !important; }
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ============================================================
# HELPER — GAUGE CHART
# ============================================================
def build_gauge(value: float):
    if value >= 75:
        bar_color = "#17A673"
    elif value >= 50:
        bar_color = "#E8A317"
    else:
        bar_color = "#E2483D"

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            number={"suffix": "%", "font": {"size": 40, "family": "Poppins, sans-serif", "color": "#16324F"}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#94A3B8"},
                "bar": {"color": bar_color, "thickness": 0.28},
                "bgcolor": "white",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 50], "color": "#FDEDEC"},
                    {"range": [50, 75], "color": "#FFF8E8"},
                    {"range": [75, 100], "color": "#EAFBF4"},
                ],
                "threshold": {
                    "line": {"color": "#16324F", "width": 3},
                    "thickness": 0.8,
                    "value": value,
                },
            },
        )
    )
    fig.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": "Plus Jakarta Sans, sans-serif", "color": "#16324F"},
    )
    return fig


# ============================================================
# HERO
# ============================================================
st.markdown(
    """
    <div class="hero-wrap">
        <div class="hero-inner">
            <div class="hero-title">🌬️ Jendela Udara</div>
            <div class="hero-sub">Safe-Air Planner — intip probabilitas udara Banda Aceh tetap aman
            untuk aktivitas luar ruanganmu hari ini.</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("### 🪟 Tentang Jendela Udara")
    st.write(
        "Jendela Udara membantu kamu menimbang risiko paparan polutan sebelum "
        "beraktivitas di luar ruangan, berdasarkan model prediksi *survival* "
        "terhadap kadar CO, NO₂, O₃, dan SO₂."
    )
    st.markdown("### 🎯 Skala Probabilitas")
    st.markdown(
        "- 🟢 **≥ 75%** — Aman beraktivitas\n"
        "- 🟡 **50–74%** — Waspada, pakai masker\n"
        "- 🔴 **< 50%** — Tunda aktivitas luar ruangan"
    )
    st.caption(
        "⚠️ Kadar polutan saat ini masih input manual (simulasi). "
        "Integrasi sensor real-time menyusul."
    )

# ============================================================
# MUAT MODEL
# ============================================================
@st.cache_resource
def load_model():
    try:
        return joblib.load("safe_air_model.pkl")
    except FileNotFoundError:
        return None


model = load_model()

if model is None:
    st.markdown(
        """
        <div class="result-card result-danger">
            <div class="result-title">⚠️ Model tidak ditemukan</div>
            <div class="result-body">Pastikan file <code>safe_air_model.pkl</code> berada di folder
            yang sama dengan <code>app.py</code>, lalu muat ulang halaman.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    # --------------------------------------------------------
    # FORM INPUT
    # --------------------------------------------------------
    with st.form("perencanaan_form"):
        with st.container(border=True):
            st.markdown("#### 📋 Rencana Aktivitasmu")
            c1, c2 = st.columns([2, 1])
            with c1:
                aktivitas = st.text_input(
                    "Nama Aktivitas",
                    "Olahraga",
                    placeholder="mis: Lari Sore, Main Bola",
                )
            with c2:
                durasi = st.slider("Durasi (jam)", min_value=1, max_value=8, value=2)

        with st.container(border=True):
            st.markdown("#### 🔬 Kondisi Udara Saat Ini")
            st.caption("Simulasi input manual — nantinya bisa otomatis dari sensor.")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                co_val = st.number_input(
                    "🚗 CO", value=0.300, help="Karbon monoksida — umumnya dari asap kendaraan."
                )
            with col2:
                no2_val = st.number_input(
                    "🏭 NO2", value=5.0, help="Nitrogen dioksida — dari pembakaran industri & kendaraan."
                )
            with col3:
                o3_val = st.number_input(
                    "☀️ O3", value=40, help="Ozon permukaan — cenderung naik saat siang terik."
                )
            with col4:
                so2_val = st.number_input(
                    "🌋 SO2", value=2.0, help="Sulfur dioksida — dari aktivitas vulkanik & industri."
                )

        submit = st.form_submit_button(
            "🔍 Cek Keamanan Udara", use_container_width=True, type="primary"
        )

    # --------------------------------------------------------
    # EKSEKUSI & OUTPUT
    # --------------------------------------------------------
    if submit:
        input_data = pd.DataFrame(
            {"co": [co_val], "no2": [no2_val], "o3": [o3_val], "so2": [so2_val]}
        )

        probabilitas = None
        error_msg = None

        with st.spinner("🔎 Menghitung probabilitas udara aman..."):
            try:
                surv_funcs = model.predict_survival_function(input_data)
                times = surv_funcs.index.values

                if durasi in times:
                    probabilitas = surv_funcs.loc[durasi].values[0] * 100
                else:
                    waktu_terdekat = min(times, key=lambda x: abs(x - durasi))
                    probabilitas = surv_funcs.loc[waktu_terdekat].values[0] * 100
            except Exception as e:
                error_msg = str(e)

        if error_msg is not None:
            st.markdown(
                f"""
                <div class="result-card result-danger">
                    <div class="result-title">⚠️ Terjadi Kesalahan</div>
                    <div class="result-body">Kalkulasi matematis gagal: {error_msg}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown("### 📊 Hasil Prediksi")

            if PLOTLY_AVAILABLE:
                st.plotly_chart(build_gauge(probabilitas), use_container_width=True)
            else:
                st.progress(min(int(probabilitas), 100) / 100)
                st.write(f"**Probabilitas: {probabilitas:.1f}%**")

            if probabilitas >= 75:
                st.markdown(
                    f"""
                    <div class="result-card result-safe">
                        <div class="result-title">✅ Aman untuk {aktivitas}!</div>
                        <div class="result-body">Probabilitas udara tetap sehat selama {durasi} jam
                        ke depan: <b>{probabilitas:.1f}%</b>. Nikmati aktivitasmu di luar ruangan!</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            elif 50 <= probabilitas < 75:
                st.markdown(
                    f"""
                    <div class="result-card result-warn">
                        <div class="result-title">⚠️ Hati-hati saat {aktivitas}</div>
                        <div class="result-body">Probabilitas udara sehat tersisa
                        <b>{probabilitas:.1f}%</b>. Disarankan memakai masker atau kurangi durasi
                        aktivitas.</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
                    <div class="result-card result-danger">
                        <div class="result-title">❌ Tidak Disarankan!</div>
                        <div class="result-body">Probabilitas anjlok ke <b>{probabilitas:.1f}%</b>.
                        Potensi lonjakan polutan tinggi — sebaiknya tunda {aktivitas} di luar
                        ruangan.</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with st.container(border=True):
                st.markdown("#### 🧪 Data yang Digunakan")
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("CO", co_val)
                m2.metric("NO2", no2_val)
                m3.metric("O3", o3_val)
                m4.metric("SO2", so2_val)

    st.caption("Dibuat untuk warga Banda Aceh 🌊 · Jendela Udara")
