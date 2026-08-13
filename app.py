import streamlit as st
import pandas as pd
import pickle
import numpy as np

# Konfigurasi Halaman Web
st.set_page_config(page_title="Jendela Udara | Safe-Air Planner", page_icon="🌬️", layout="centered")

# --- Muat Model ---
@st.cache_resource
def load_model():
    try:
        with open("safe_air_model.pkl", "rb") as file:
            model = pickle.load(file)
        return model
    except FileNotFoundError:
        return None

model = load_model()

# --- Antarmuka Pengguna ---
st.title("🌬️ Jendela Udara (Safe-Air Planner)")
st.write("Ketahui probabilitas udara di Banda Aceh tetap aman untuk aktivitas luar ruanganmu hari ini.")

if model is None:
    st.error("Model tidak ditemukan! Pastikan file 'safe_air_model.pkl' berada di folder yang sama dengan app.py")
else:
    # Form Input untuk Pengguna Awam
    with st.form("perencanaan_form"):
        st.subheader("Rencana Aktivitasmu")
        
        aktivitas = st.text_input("Nama Aktivitas (mis: Lari Sore, Main Bola)", "Olahraga")
        durasi = st.slider("Berapa lama rencananya? (Jam)", min_value=1, max_value=8, value=2)
        
        # Simulasi sensor saat ini (Di dunia nyata, ini diambil dari API sensor udara)
        st.write("---")
        st.write("*Simulasi Kondisi Udara Saat Ini (Input Manual Sementara):*")
        col1, col2, col3 = st.columns(3)
        with col1:
            co = st.number_input("Kadar CO saat ini", value=300)
        with col2:
            no2 = st.number_input("Kadar NO2 saat ini", value=5.0)
        with col3:
            o3 = st.number_input("Kadar O3 saat ini", value=40)
            
        submit = st.form_submit_button("Cek Keamanan Udara")

    # --- Eksekusi dan Output Visual ---
    if submit:
        # Menyiapkan data input seperti format saat pelatihan
        input_data = pd.DataFrame({
            'carbon_monoxide': [co],
            'nitrogen_dioxide': [no2],
            'ozone': [o3]
        })
        
        # Menghitung probabilitas survival di jam ke-{durasi}
        try:
            surv_funcs = model.predict_survival_function(input_data)
            # Mengambil probabilitas pada index waktu = durasi
            # Catatan: Indeks pada surv_funcs tergantung pada data latih (jam)
            times = surv_funcs.index.values
            
            if durasi in times:
                probabilitas = surv_funcs.loc[durasi].values[0] * 100
            else:
                # Interpolasi dasar jika waktu tidak pas di index
                waktu_terdekat = min(times, key=lambda x: abs(x - durasi))
                probabilitas = surv_funcs.loc[waktu_terdekat].values[0] * 100
                
            # Logika Keputusan & Visualisasi
            st.write("### Hasil Prediksi")
            
            if probabilitas >= 75:
                st.success(f"✅ **Aman!** Ada probabilitas {probabilitas:.1f}% udara tetap sehat selama {durasi} jam ke depan untuk {aktivitas}.")
            elif 50 <= probabilitas < 75:
                st.warning(f"⚠️ **Hati-hati.** Probabilitas udara sehat tersisa {probabilitas:.1f}%. Disarankan memakai masker atau kurangi durasi {aktivitas}.")
            else:
                st.error(f"❌ **Tidak Disarankan!** Probabilitas anjlok ke {probabilitas:.1f}%. Potensi lonjakan polutan sangat tinggi. Sebaiknya tunda aktivitas luar ruangan.")
                
        except Exception as e:
            st.error(f"Terjadi kesalahan saat kalkulasi matematis: {e}")