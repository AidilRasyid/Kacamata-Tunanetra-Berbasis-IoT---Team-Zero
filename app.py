import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import time

# ==========================================
# KONFIGURASI DASHBOARD
# ==========================================
st.set_page_config(
    page_title="Team ZERO - IoT Dashboard",
    page_icon="📡",
    layout="wide"
)

def muat_css(nama_file):
    try:
        with open(nama_file) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass

muat_css("style.css")

URL_API = "http://127.0.0.1:8000/api/monitoring-data"

st.title("Dashboard Monitoring Jarak Sensor")
st.write("Projek IoT Real-time System - Team ZERO")
st.markdown("---")


# ==========================================
# CLASS LARAVEL API
# ==========================================
class LaravelAPI:
    def __init__(self, url):
        self.url = url

    def ambil_data(self):
        try:
            response = requests.get(self.url, timeout=1.5)

            if response.status_code == 200:
                return response.json()

            return None

        except Exception as e:
            print(e)
            return None


# ==========================================
# CLASS FUZZY LOGIC
# ==========================================
class FuzzyLogic:

    @staticmethod
    def hitung_keanggotaan(jarak):

        if jarak <= 30:
            mu_dekat = 1.0
        elif 30 < jarak <= 50:
            mu_dekat = (50 - jarak) / 20.0
        else:
            mu_dekat = 0.0

    # Himpunan Sedang
        if jarak <= 30 or jarak > 70:
            mu_sedang = 0.0
        elif 30 < jarak <= 50:
            mu_sedang = (jarak - 30) / 20.0
        elif 50 < jarak <= 70:
            mu_sedang = (70 - jarak) / 20.0
        else:
            mu_sedang = 0.0

    # Himpunan Jauh
        if jarak <= 50:
            mu_jauh = 0.0
        elif 50 < jarak <= 70:
            mu_jauh = (jarak - 50) / 20.0
        else:
            mu_jauh = 1.0

        return mu_dekat, mu_sedang, mu_jauh


# ==========================================
# CLASS GRAFIK FUZZY
# ==========================================
class GrafikFuzzy:

    @staticmethod
    def buat_grafik(jarak_aktual, nama_sensor):

        x_vals = np.linspace(0, 80, 400)

        y_dekat = [FuzzyLogic.hitung_keanggotaan(x)[0] for x in x_vals]
        y_sedang = [FuzzyLogic.hitung_keanggotaan(x)[1] for x in x_vals]
        y_jauh = [FuzzyLogic.hitung_keanggotaan(x)[2] for x in x_vals]

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=x_vals, y=y_dekat,
            name='Dekat',
            line=dict(color='#ff4b4b', width=3)
        ))

        fig.add_trace(go.Scatter(
            x=x_vals, y=y_sedang,
            name='Sedang',
            line=dict(color='#ffa500', width=3)
        ))

        fig.add_trace(go.Scatter(
            x=x_vals, y=y_jauh,
            name='Jauh',
            line=dict(color='#00cb30', width=3)
        ))

        fig.add_vline(
            x=jarak_aktual,
            line_dash="dash",
            line_color="#1f77b4",
            line_width=2.5,
            annotation_text=f"Jarak: {jarak_aktual} cm",
            annotation_position="top right"
        )

        fig.update_layout(
            title=f"Distance Membership Functions - {nama_sensor}",
            xaxis_title="Distance (cm)",
            yaxis_title="Membership Degree (µ)",
            yaxis=dict(range=[-0.05, 1.05]),
            height=240,
            margin=dict(l=20, r=20, t=45, b=20),
            hovermode="x unified",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        return fig


api = LaravelAPI(URL_API)
data_json = api.ambil_data()

if data_json and len(data_json) > 0:

    df = pd.DataFrame(data_json)
    df = df.iloc[::-1].reset_index(drop=True)

    data_terbaru = df.iloc[-1]

    j1 = float(data_terbaru['jarak1'])
    j2 = float(data_terbaru['jarak2'])
    j3 = float(data_terbaru['jarak3'])

    waktu_update = data_terbaru['waktu']

    col1, col2, col3 = st.columns(3)

    with col1:
        status1 = "🔴DEKAT" if j1 <= 30 else "🟡SEDANG" if j1 <= 50 else "🟢JAUH"
        st.metric("Sensor 1 (Bawah)", f"{j1} cm")
        st.markdown(f"Status: **{status1}**")

    with col2:
        status2 = "🔴DEKAT" if j2 <= 30 else "🟡SEDANG" if j2 <= 50 else "🟢JAUH"
        st.metric("Sensor 2 (Tengah)", f"{j2} cm")
        st.markdown(f"Status: **{status2}**")

    with col3:
        status3 = "🔴DEKAT" if j3 <= 30 else "🟡SEDANG" if j3 <= 50 else "🟢JAUH"
        st.metric("Sensor 3 (Atas)", f"{j3} cm")
        st.markdown(f"Status: **{status3}**")

    st.caption(f"Terakhir Diperbarui: {waktu_update}")
    st.markdown("---")

    sensors = [
        ("Sensor 1 (Bawah)", j1, "Sensor 1"),
        ("Sensor 2 (Tengah)", j2, "Sensor 2"),
        ("Sensor 3 (Atas)", j3, "Sensor 3"),
    ]

    for judul, jarak, nama_sensor in sensors:
        with st.container(border=True):
            st.markdown(f"#### Kacamata {judul}")

            c_data, c_graph = st.columns([1, 2])

            with c_data:
                mu_d, mu_s, mu_j = FuzzyLogic.hitung_keanggotaan(jarak)

                st.write("**Nilai Derajat Keanggotaan (µ):**")
                st.progress(mu_d, text=f"µ Dekat (Bahaya): {round(mu_d, 2)}")
                st.progress(mu_s, text=f"µ Sedang (Waspada): {round(mu_s, 2)}")
                st.progress(mu_j, text=f"µ Jauh (Aman): {round(mu_j, 2)}")

            with c_graph:
                st.plotly_chart(
                    GrafikFuzzy.buat_grafik(jarak, nama_sensor),
                    use_container_width=True
                )

    st.markdown("---")

    st.subheader("Grafik Tren Jarak Sensor (Real-time)")

    fig = px.line(
        df,
        x='waktu',
        y=['jarak1', 'jarak2', 'jarak3'],
        labels={
            'value': 'Jarak (cm)',
            'waktu': 'Waktu',
            'variable': 'Sensor'
        },
        title="Pergerakan Objek Terhadap Kacamata Sensor"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    st.subheader("Tabel Riwayat Data")

    st.dataframe(df.iloc[::-1], use_container_width=True)

    csv_data = df.to_csv(index=False).encode('utf-8')

    st.download_button(
        label="Unduh Semua Laporan (CSV)",
        data=csv_data,
        file_name='laporan_sensor_team_zero.csv',
        mime='text/csv'
    )

else:
    st.warning("Menunggu suplai data dari Backend Laravel...")
    st.info(f"Mencoba menyambung ke API: {URL_API}")

time.sleep(2)
st.rerun()
