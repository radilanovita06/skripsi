import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(
    page_title="Sistem Monitoring Anggaran",
    page_icon="🏛️",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background: #0b1727 !important;
}

[data-testid="stAppViewContainer"] {
    background: linear-gradient(180deg, #10233d 0%, #183250 45%, #213d5e 100%) !important;
}

.block-container {
    padding-top: 2rem;
    max-width: 1450px;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #081729, #102947) !important;
    border-right: 2px solid #C8A951;
}

[data-testid="stSidebar"] * {
    color: white !important;
}

.gov-header {
    background: linear-gradient(135deg, #0f2d52, #214d7d);
    border-radius: 28px;
    padding: 35px;
    border-left: 8px solid #C8A951;
    box-shadow: 0 20px 40px rgba(0,0,0,.35);
    margin-bottom: 30px;
}

.gov-header h1 {
    color: white !important;
    font-size: 34px;
    margin: 0;
}

.gov-header p {
    color: #dbeafe !important;
    margin-top: 10px;
}

.card {
    background: rgba(18, 33, 53, 0.94);
    border-radius: 26px;
    padding: 30px;
    border: 1px solid rgba(255,255,255,.08);
    box-shadow: 0 20px 50px rgba(0,0,0,.25);
}

.chart-card {
    background: rgba(22, 40, 63, 0.92);
    border-radius: 22px;
    padding: 22px;
    border: 1px solid rgba(255,255,255,.08);
    box-shadow: 0 15px 35px rgba(0,0,0,.20);
}

h1, h2, h3, h4, h5, h6, label, p, span {
    color: #f1f5f9 !important;
}

.stTextInput input,
.stNumberInput input,
.stTextArea textarea {
    background: #16283f !important;
    color: white !important;
    border-radius: 14px !important;
    border: 1px solid #35506f !important;
}

.stSelectbox div[data-baseweb="select"],
.stMultiSelect div[data-baseweb="select"] {
    background: #16283f !important;
    border-radius: 14px !important;
    color: white !important;
    border: 1px solid #35506f !important;
}

.stButton button,
.stFormSubmitButton button,
.stDownloadButton button {
    background: linear-gradient(135deg, #C8A951, #d8bc6b) !important;
    color: #0f172a !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 14px 26px !important;
    font-weight: 700 !important;
}

.metric-card {
    background: linear-gradient(135deg, #16283f, #213754);
    border-radius: 22px;
    padding: 24px;
    border-left: 6px solid #C8A951;
    box-shadow: 0 15px 35px rgba(0,0,0,.20);
}

.metric-title {
    color: #b6c2d1 !important;
    font-size: 14px;
}

.metric-value {
    color: white !important;
    font-size: 26px;
    font-weight: 800;
}

[data-testid="stDataFrame"] {
    border-radius: 18px;
    overflow: hidden;
    border: 1px solid #35506f;
}

hr {
    border-color: rgba(255,255,255,.15);
}
</style>
""", unsafe_allow_html=True)

if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame()

bulan_list = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember"
]

penanggung_jawab_list = [
    "Sekretariat",
    "Direktorat Industri Hasil Hutan dan Perkebunan",
    "Direktorat Industri Makanan, Hasil Laut dan Perikanan",
    "Direktorat Industri Minuman, Hasil Tembakau dan Bahan Penyegar",
    "Direktorat Industri Kimia, Oleokimia dan Pakan"
]

template_columns = [
    "Tanggal",
    "Penanggung Jawab",
    "Kegiatan",
    "Pagu",
    "Realisasi",
    "Sisa Anggaran",
    "Presentase",
    "Realisasi Bulanan",
    "Persen Bulanan"
]

def format_rupiah(x):
    try:
        return f"Rp{float(x):,.0f}".replace(",", ".")
    except:
        return "Rp0"

def format_percent(x):
    try:
        return f"{float(x):.3f}%".replace(".", ",")
    except:
        return "0,000%"

def clean_money(x):
    if pd.isna(x):
        return 0

    cleaned = (
        str(x)
        .replace("Rp", "")
        .replace("rp", "")
        .replace(".", "")
        .replace(",", ".")
        .strip()
    )

    value = pd.to_numeric(cleaned, errors="coerce")
    return 0 if pd.isna(value) else value

def clean_percent(x):
    if pd.isna(x):
        return 0

    cleaned = str(x).replace("%", "").replace(",", ".").strip()
    value = pd.to_numeric(cleaned, errors="coerce")
    return 0 if pd.isna(value) else value

def prepare_raw(df):
    df = df.copy()

    for col in template_columns:
        if col not in df.columns:
            df[col] = 0 if col not in ["Tanggal", "Penanggung Jawab", "Kegiatan"] else ""

    df = df[template_columns]

    for col in ["Pagu", "Realisasi", "Sisa Anggaran", "Realisasi Bulanan"]:
        df[col] = df[col].apply(clean_money)

    for col in ["Presentase", "Persen Bulanan"]:
        df[col] = df[col].apply(clean_percent)

    df["Sisa Anggaran"] = df["Pagu"] - df["Realisasi"]

    df["Presentase"] = df.apply(
        lambda row: (row["Realisasi"] / row["Pagu"] * 100) if row["Pagu"] > 0 else 0,
        axis=1
    )

    df["Persen Bulanan"] = df.apply(
        lambda row: (row["Realisasi Bulanan"] / row["Pagu"] * 100) if row["Pagu"] > 0 else 0,
        axis=1
    )

    return df

def prepare_display(df, show_kegiatan=False):
    df = df.copy().reset_index(drop=True)

    if not show_kegiatan:
        df = df.drop(columns=["Kegiatan"], errors="ignore")

    df.insert(0, "NO", range(1, len(df) + 1))

    for col in ["Pagu", "Realisasi", "Sisa Anggaran", "Realisasi Bulanan"]:
        if col in df.columns:
            df[col] = df[col].apply(format_rupiah)

    for col in ["Presentase", "Persen Bulanan"]:
        if col in df.columns:
            df[col] = df[col].apply(format_percent)

    return df

def convert_to_csv(df):
    return df.to_csv(index=False).encode("utf-8-sig")

def chart_bar(df, x_col, y_col, title):
    chart = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
        .encode(
            x=alt.X(f"{x_col}:N", sort="-y", title=None),
            y=alt.Y(f"{y_col}:Q", title=None),
            tooltip=[x_col, y_col]
        )
        .properties(height=320, title=title)
        .configure_title(color="#f1f5f9", fontSize=16)
        .configure_axis(labelColor="#f1f5f9", titleColor="#f1f5f9", gridColor="#35506f")
        .configure_view(strokeWidth=0)
    )
    return chart

def chart_line(df, x_col, y_col, title):
    df = df.copy()
    df["Bulan Order"] = df[x_col].apply(lambda x: bulan_list.index(x) if x in bulan_list else 99)
    df = df.sort_values("Bulan Order")

    chart = (
        alt.Chart(df)
        .mark_line(point=True, strokeWidth=3)
        .encode(
            x=alt.X(f"{x_col}:N", sort=bulan_list, title=None),
            y=alt.Y(f"{y_col}:Q", title=None),
            tooltip=[x_col, y_col]
        )
        .properties(height=320, title=title)
        .configure_title(color="#f1f5f9", fontSize=16)
        .configure_axis(labelColor="#f1f5f9", titleColor="#f1f5f9", gridColor="#35506f")
        .configure_view(strokeWidth=0)
    )
    return chart

st.markdown("""
<div class="gov-header">
    <h1>🏛️ Sistem Monitoring Anggaran</h1>
    <p>Monitoring Pagu, Realisasi, dan Sisa Anggaran berdasarkan Penanggung Jawab dan Periode</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.title("Menu Sistem")

menu = st.sidebar.radio(
    "Pilih Menu",
    [
        "Upload Data Satu Persatu",
        "Upload Menggunakan Template",
        "Melihat Semua Data"
    ]
)

if menu == "Upload Data Satu Persatu":

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Input Data Anggaran")

    with st.form("form_input_anggaran"):
        col1, col2 = st.columns(2)

        with col1:
            tanggal = st.selectbox("Periode", bulan_list)
            pj = st.selectbox("Penanggung Jawab", penanggung_jawab_list)
            kegiatan = st.text_area("Kegiatan")

        with col2:
            pagu = st.number_input("Pagu (Rp)", min_value=0, step=1000000, format="%d")
            realisasi = st.number_input("Realisasi (Rp)", min_value=0, step=1000000, format="%d")
            realisasi_bulanan = st.number_input("Realisasi Bulanan (Rp)", min_value=0, step=1000000, format="%d")

            sisa = pagu - realisasi
            presentase = (realisasi / pagu * 100) if pagu > 0 else 0
            persen_bulanan = (realisasi_bulanan / pagu * 100) if pagu > 0 else 0

            st.markdown(f"""
            <div style="
                background:#16283f;
                padding:18px;
                border-radius:14px;
                border-left:6px solid #C8A951;
                font-size:17px;
                font-weight:700;
                color:#ffffff;
                margin-top:18px;
            ">
                💰 Sisa Anggaran: {format_rupiah(sisa)}<br>
                📈 Presentase: {format_percent(presentase)}<br>
                📊 Persen Bulanan: {format_percent(persen_bulanan)}
            </div>
            """, unsafe_allow_html=True)

        submit = st.form_submit_button("Simpan Data")

    if submit:
        new_data = pd.DataFrame([{
            "Tanggal": tanggal,
            "Penanggung Jawab": pj,
            "Kegiatan": kegiatan,
            "Pagu": pagu,
            "Realisasi": realisasi,
            "Sisa Anggaran": sisa,
            "Presentase": presentase,
            "Realisasi Bulanan": realisasi_bulanan,
            "Persen Bulanan": persen_bulanan
        }])

        st.session_state.data = pd.concat([st.session_state.data, new_data], ignore_index=True)
        st.success("Data berhasil disimpan 😹")

    st.markdown("</div>", unsafe_allow_html=True)

elif menu == "Upload Menggunakan Template":

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Upload Menggunakan Template")

    template_df = pd.DataFrame(columns=template_columns)

    st.download_button(
        "Download Template CSV",
        data=convert_to_csv(template_df),
        file_name="Template_Monitoring_Anggaran.csv",
        mime="text/csv"
    )

    uploaded_file = st.file_uploader("Upload CSV / Excel", type=["csv", "xlsx", "xls"])

    if uploaded_file:
        try:
            if uploaded_file.name.endswith(".csv"):
                df_upload = pd.read_csv(uploaded_file)
            else:
                df_upload = pd.read_excel(uploaded_file)

            missing_cols = [
                col for col in ["Tanggal", "Penanggung Jawab", "Kegiatan", "Pagu", "Realisasi"]
                if col not in df_upload.columns
            ]

            if missing_cols:
                st.error(f"Kolom wajib kurang: {missing_cols}")
            else:
                df_upload = prepare_raw(df_upload)

                st.session_state.data = pd.concat(
                    [st.session_state.data, df_upload],
                    ignore_index=True
                )

                st.success("Upload berhasil")

                st.subheader("Preview Data Upload")
                st.dataframe(
                    prepare_display(df_upload, show_kegiatan=True),
                    use_container_width=True,
                    hide_index=True
                )

        except Exception as e:
            st.error(f"Gagal upload file: {e}")

    st.markdown("</div>", unsafe_allow_html=True)

elif menu == "Melihat Semua Data":

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Monitoring Data Anggaran")

    if st.session_state.data.empty:
        st.warning("Belum ada data masuk 🥀")

    else:
        df = prepare_raw(st.session_state.data)

        col1, col2 = st.columns(2)

        with col1:
            selected_pj = st.multiselect(
                "Filter Penanggung Jawab",
                sorted(df["Penanggung Jawab"].dropna().unique()),
                default=sorted(df["Penanggung Jawab"].dropna().unique())
            )

        with col2:
            selected_periode = st.multiselect(
                "Filter Periode",
                bulan_list,
                default=sorted(df["Tanggal"].dropna().unique())
            )

        filtered_df = df[
            df["Penanggung Jawab"].isin(selected_pj)
            &
            df["Tanggal"].isin(selected_periode)
        ].copy()

        total_pagu = filtered_df["Pagu"].sum()
        total_realisasi = filtered_df["Realisasi"].sum()
        total_sisa = filtered_df["Sisa Anggaran"].sum()
        total_realisasi_bulanan = filtered_df["Realisasi Bulanan"].sum()
        total_presentase = (total_realisasi / total_pagu * 100) if total_pagu > 0 else 0

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Total Pagu</div>
                <div class="metric-value">{format_rupiah(total_pagu)}</div>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Total Realisasi</div>
                <div class="metric-value">{format_rupiah(total_realisasi)}</div>
            </div>
            """, unsafe_allow_html=True)

        with c3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Total Sisa Anggaran</div>
                <div class="metric-value">{format_rupiah(total_sisa)}</div>
            </div>
            """, unsafe_allow_html=True)

        with c4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Total Presentase</div>
                <div class="metric-value">{format_percent(total_presentase)}</div>
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        summary_pj = filtered_df.groupby(
            "Penanggung Jawab",
            as_index=False
        )[["Pagu", "Realisasi", "Sisa Anggaran", "Realisasi Bulanan"]].sum()

        summary_pj["Presentase"] = summary_pj.apply(
            lambda row: (row["Realisasi"] / row["Pagu"] * 100) if row["Pagu"] > 0 else 0,
            axis=1
        )

        summary_period = filtered_df.groupby(
            "Tanggal",
            as_index=False
        )[["Pagu", "Realisasi", "Sisa Anggaran", "Realisasi Bulanan"]].sum()

        summary_period["Presentase"] = summary_period.apply(
            lambda row: (row["Realisasi"] / row["Pagu"] * 100) if row["Pagu"] > 0 else 0,
            axis=1
        )

        st.subheader("Grafik Monitoring")

        g1, g2 = st.columns(2)

        with g1:
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            st.altair_chart(
                chart_bar(summary_pj, "Penanggung Jawab", "Realisasi", "Realisasi per Penanggung Jawab"),
                use_container_width=True
            )
            st.markdown("</div>", unsafe_allow_html=True)

        with g2:
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            st.altair_chart(
                chart_bar(summary_pj, "Penanggung Jawab", "Sisa Anggaran", "Sisa Anggaran per Penanggung Jawab"),
                use_container_width=True
            )
            st.markdown("</div>", unsafe_allow_html=True)

        g3, g4 = st.columns(2)

        with g3:
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            st.altair_chart(
                chart_line(summary_period, "Tanggal", "Realisasi", "Trend Realisasi per Periode"),
                use_container_width=True
            )
            st.markdown("</div>", unsafe_allow_html=True)

        with g4:
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            st.altair_chart(
                chart_line(summary_period, "Tanggal", "Pagu", "Trend Pagu per Periode"),
                use_container_width=True
            )
            st.markdown("</div>", unsafe_allow_html=True)

        st.divider()

        st.subheader("Detail Data")
        display_df = prepare_display(filtered_df, show_kegiatan=False)

        st.dataframe(display_df, use_container_width=True, hide_index=True)

        st.download_button(
            "Download Data",
            data=convert_to_csv(display_df),
            file_name="Monitoring_Anggaran.csv",
            mime="text/csv"
        )

        st.subheader("Detail Data Lengkap Dengan Kegiatan")
        full_display_df = prepare_display(filtered_df, show_kegiatan=True)

        st.dataframe(full_display_df, use_container_width=True, hide_index=True)

        st.download_button(
            "Download Data Lengkap",
            data=convert_to_csv(full_display_df),
            file_name="Monitoring_Anggaran_Lengkap.csv",
            mime="text/csv"
        )

        st.subheader("Summary Penanggung Jawab")
        st.dataframe(
            prepare_display(summary_pj, show_kegiatan=False),
            use_container_width=True,
            hide_index=True
        )

        st.subheader("Summary Periode")
        st.dataframe(
            prepare_display(summary_period, show_kegiatan=False),
            use_container_width=True,
            hide_index=True
        )

    st.markdown("</div>", unsafe_allow_html=True)