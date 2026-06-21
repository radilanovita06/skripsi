import streamlit as st
import pandas as pd
import altair as alt
from io import BytesIO

st.set_page_config(
    page_title="Sistem Monitoring Anggaran",
    page_icon="🏛️",
    layout="wide"
)

st.markdown("""
<style>
.stApp { background: #0b1727 !important; }
[data-testid="stAppViewContainer"] {
    background: linear-gradient(180deg, #10233d 0%, #183250 45%, #213d5e 100%) !important;
}
.block-container { padding-top: 2rem; max-width: 1450px; }
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #081729, #102947) !important;
    border-right: 2px solid #C8A951;
}
[data-testid="stSidebar"] * { color: white !important; }
.gov-header {
    background: linear-gradient(135deg, #0f2d52, #214d7d);
    border-radius: 28px;
    padding: 35px;
    border-left: 8px solid #C8A951;
    box-shadow: 0 20px 40px rgba(0,0,0,.35);
    margin-bottom: 30px;
}
.gov-header h1 { color: white !important; font-size: 34px; margin: 0; }
.gov-header p { color: #dbeafe !important; margin-top: 10px; }
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
}
h1, h2, h3, h4, h5, h6, label, p, span { color: #f1f5f9 !important; }
.stTextInput input,
.stNumberInput input,
.stTextArea textarea,
.stDateInput input {
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
    font-weight: 700 !important;
}
.metric-card {
    background: linear-gradient(135deg, #16283f, #213754);
    border-radius: 22px;
    padding: 24px;
    border-left: 6px solid #C8A951;
    box-shadow: 0 15px 35px rgba(0,0,0,.20);
}
.metric-title { color: #b6c2d1 !important; font-size: 14px; }
.metric-value { color: white !important; font-size: 25px; font-weight: 800; }
[data-testid="stDataFrame"] {
    border-radius: 18px;
    overflow: hidden;
    border: 1px solid #35506f;
}
.login-wrap { max-width: 460px; margin: 7vh auto 0 auto; }
.login-logo {
    width: 72px; height: 72px; margin: 0 auto 18px auto;
    border-radius: 22px; display: flex; align-items: center;
    justify-content: center; font-size: 34px;
    background: linear-gradient(135deg, #C8A951, #ead58f);
}
.login-title { text-align: center; font-size: 30px; font-weight: 800; color: white !important; }
.login-subtitle { text-align: center; color: #b6c2d1 !important; margin-bottom: 28px; }
.user-card {
    background: rgba(255,255,255,.06);
    border: 1px solid rgba(255,255,255,.10);
    border-radius: 16px; padding: 14px; margin: 10px 0 18px 0;
}
.user-name { font-weight: 800; color: white !important; }
.user-role { font-size: 12px; color: #cbd5e1 !important; }
</style>
""", unsafe_allow_html=True)

# =========================================================
# AKUN LOGIN
# Ganti username/password di sini.
# Untuk produksi, simpan password di database atau st.secrets.
# =========================================================
USERS = {
    "admin": {
        "password": "admin123",
        "name": "Administrator",
        "role": "Admin"
    },
    "operator": {
        "password": "operator123",
        "name": "Operator Anggaran",
        "role": "Operator"
    }
}

BULAN_LIST = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember"
]

TEMPLATE_COLUMNS = [
    "Tanggal",
    "No",
    "MAK",
    "Kegiatan",
    "Pagu",
    "Realisasi",
    "Sisa Anggaran"
]


def init_state():
    defaults = {
        "authenticated": False,
        "current_user": None,
        "data": pd.DataFrame(columns=TEMPLATE_COLUMNS),
        "edit_index": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_state()


def login_user(username: str, password: str) -> bool:
    user = USERS.get(username.strip())
    if user and user["password"] == password:
        st.session_state.authenticated = True
        st.session_state.current_user = {
            "username": username.strip(),
            "name": user["name"],
            "role": user["role"]
        }
        return True
    return False


def logout_user():
    st.session_state.authenticated = False
    st.session_state.current_user = None
    st.session_state.edit_index = None
    st.rerun()


def is_admin() -> bool:
    return (
        st.session_state.current_user is not None
        and st.session_state.current_user.get("role") == "Admin"
    )


def clean_money(value):
    if pd.isna(value) or value == "":
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    cleaned = (
        str(value)
        .replace("Rp", "")
        .replace("rp", "")
        .replace(" ", "")
        .replace(".", "")
        .replace(",", ".")
    )
    result = pd.to_numeric(cleaned, errors="coerce")
    return 0.0 if pd.isna(result) else float(result)


def format_rupiah(value):
    try:
        return f"Rp{float(value):,.0f}".replace(",", ".")
    except (TypeError, ValueError):
        return "Rp0"


def normalize_headers(df: pd.DataFrame) -> pd.DataFrame:
    """Rapikan nama kolom agar tahan terhadap spasi, kapital, dan typo umum."""
    df = df.copy()

    aliases = {
        "tanggal": "Tanggal",
        "date": "Tanggal",
        "no": "No",
        "nomor": "No",
        "mak": "MAK",
        "kegiatan": "Kegiatan",
        "pagu": "Pagu",
        "realisasi": "Realisasi",
        "realosaso": "Realisasi",
        "sisa anggaran": "Sisa Anggaran",
        "sisa amggaran": "Sisa Anggaran",
    }

    renamed = {}
    for col in df.columns:
        cleaned = " ".join(str(col).replace("\ufeff", "").strip().split()).lower()
        renamed[col] = aliases.get(cleaned, str(col).strip())

    return df.rename(columns=renamed)


def read_uploaded_file(uploaded_file) -> pd.DataFrame:
    filename = uploaded_file.name.lower()

    if filename.endswith(".csv"):
        # sep=None + python engine mendeteksi koma, titik koma, atau tab otomatis.
        return pd.read_csv(uploaded_file, sep=None, engine="python", encoding="utf-8-sig")

    try:
        return pd.read_excel(uploaded_file, engine="calamine")
    except (ImportError, ModuleNotFoundError) as exc:
        raise RuntimeError(
            "Mesin pembaca Excel belum terpasang. Pastikan requirements.txt berisi "
            "python-calamine dan pandas>=2.2.0."
        ) from exc


def normalize_bulan(value):
    """Baca nama bulan tanpa tanggal/tahun, termasuk singkatan dan angka 1-12."""
    if pd.isna(value) or str(value).strip() == "":
        return ""

    text = str(value).strip().lower()
    aliases = {
        "1": "Januari", "01": "Januari", "jan": "Januari", "januari": "Januari",
        "2": "Februari", "02": "Februari", "feb": "Februari", "februari": "Februari",
        "3": "Maret", "03": "Maret", "mar": "Maret", "maret": "Maret",
        "4": "April", "04": "April", "apr": "April", "april": "April",
        "5": "Mei", "05": "Mei", "may": "Mei", "mei": "Mei",
        "6": "Juni", "06": "Juni", "jun": "Juni", "juni": "Juni",
        "7": "Juli", "07": "Juli", "jul": "Juli", "juli": "Juli",
        "8": "Agustus", "08": "Agustus", "agu": "Agustus", "aug": "Agustus", "agustus": "Agustus",
        "9": "September", "09": "September", "sep": "September", "september": "September",
        "10": "Oktober", "okt": "Oktober", "oct": "Oktober", "oktober": "Oktober",
        "11": "November", "nov": "November", "november": "November",
        "12": "Desember", "des": "Desember", "dec": "Desember", "desember": "Desember",
    }

    if text in aliases:
        return aliases[text]

    # Tetap bisa membaca jika Excel menyimpan tanggal lengkap.
    parsed = pd.to_datetime(value, errors="coerce", dayfirst=True)
    if not pd.isna(parsed):
        return BULAN_LIST[parsed.month - 1]

    return str(value).strip().title()


def normalize_data(df: pd.DataFrame) -> pd.DataFrame:
    df = normalize_headers(df)

    for col in TEMPLATE_COLUMNS:
        if col not in df.columns:
            df[col] = "" if col in ["Tanggal", "MAK", "Kegiatan"] else 0

    df = df[TEMPLATE_COLUMNS]
    df["Tanggal"] = df["Tanggal"].apply(normalize_bulan)
    df["MAK"] = df["MAK"].fillna("").astype(str).str.strip()
    df["Kegiatan"] = df["Kegiatan"].fillna("").astype(str).str.strip()
    df["Pagu"] = df["Pagu"].apply(clean_money)
    df["Realisasi"] = df["Realisasi"].apply(clean_money)
    df["Sisa Anggaran"] = df["Pagu"] - df["Realisasi"]
    df = df.reset_index(drop=True)
    df["No"] = range(1, len(df) + 1)
    return df


def display_data(df: pd.DataFrame) -> pd.DataFrame:
    result = normalize_data(df)
    for col in ["Pagu", "Realisasi", "Sisa Anggaran"]:
        result[col] = result[col].apply(format_rupiah)
    return result


def to_csv(df: pd.DataFrame):
    return df.to_csv(index=False).encode("utf-8-sig")


def to_xlsx(df: pd.DataFrame):
    try:
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Data Anggaran")
        return output.getvalue()
    except ModuleNotFoundError as exc:
        st.error("XlsxWriter belum terpasang. Template CSV tetap bisa dipakai.")
        st.code("pip install XlsxWriter")
        return None


def show_login():
    st.markdown("""
    <div class="login-wrap">
        <div class="login-logo">🏛️</div>
        <div class="login-title">Sistem Monitoring Anggaran</div>
        <div class="login-subtitle">Masuk untuk mengakses dashboard</div>
    </div>
    """, unsafe_allow_html=True)

    _, center, _ = st.columns([1, 1.15, 1])
    with center:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Masuk", use_container_width=True)

        if submitted:
            if login_user(username, password):
                st.rerun()
            else:
                st.error("Username atau password salah")
        st.markdown("</div>", unsafe_allow_html=True)


if not st.session_state.authenticated:
    show_login()
    st.stop()

current_user = st.session_state.current_user

st.sidebar.title("Menu Sistem")
st.sidebar.caption("Versi aplikasi: 2026.06.21-v2-no-openpyxl")
st.sidebar.markdown(f"""
<div class="user-card">
    <div class="user-name">{current_user['name']}</div>
    <div class="user-role">{current_user['role']}</div>
</div>
""", unsafe_allow_html=True)

menu_items = [
    "Input Data",
    "Upload Template",
    "Lihat Semua Data"
]
if is_admin():
    menu_items.append("Kelola Data")

menu = st.sidebar.radio("Pilih Menu", menu_items)

if st.sidebar.button("Logout", use_container_width=True):
    logout_user()

st.markdown("""
<div class="gov-header">
    <h1>🏛️ Sistem Monitoring Anggaran</h1>
    <p>Monitoring Pagu, Realisasi, dan Sisa Anggaran</p>
</div>
""", unsafe_allow_html=True)

# =========================================================
# INPUT DATA - ADMIN DAN OPERATOR
# =========================================================
if menu == "Input Data":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Input Data Anggaran")

    with st.form("input_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            tanggal = st.selectbox("Tanggal (Bulan)", BULAN_LIST)
            mak = st.text_input("MAK", placeholder="Contoh: 521211")
            kegiatan = st.text_area("Kegiatan")
        with col2:
            pagu = st.number_input("Pagu (Rp)", min_value=0, step=1_000_000)
            realisasi = st.number_input("Realisasi (Rp)", min_value=0, step=1_000_000)
            sisa = pagu - realisasi
            st.info(f"Sisa Anggaran: {format_rupiah(sisa)}")

        submitted = st.form_submit_button("Simpan Data", use_container_width=True)

    if submitted:
        if not mak.strip() or not kegiatan.strip():
            st.error("MAK dan Kegiatan wajib diisi")
        else:
            new_row = pd.DataFrame([{
                "Tanggal": tanggal,
                "No": 0,
                "MAK": mak.strip(),
                "Kegiatan": kegiatan.strip(),
                "Pagu": pagu,
                "Realisasi": realisasi,
                "Sisa Anggaran": sisa
            }])
            st.session_state.data = normalize_data(
                pd.concat([st.session_state.data, new_row], ignore_index=True)
            )
            st.success("Data berhasil disimpan")

    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# UPLOAD - ADMIN DAN OPERATOR
# =========================================================
elif menu == "Upload Template":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Upload Data Menggunakan Template")

    template = pd.DataFrame(columns=TEMPLATE_COLUMNS)
    template["Tanggal"] = pd.Series(dtype="object")

    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "Download Template CSV",
            data=to_csv(template),
            file_name="Template_Monitoring_Anggaran.csv",
            mime="text/csv",
            use_container_width=True
        )
    with c2:
        xlsx_template = to_xlsx(template)
        if xlsx_template is not None:
            st.download_button(
                "Download Template XLSX",
                data=xlsx_template,
                file_name="Template_Monitoring_Anggaran.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

    uploaded_file = st.file_uploader("Upload CSV atau XLSX", type=["csv", "xlsx", "xls", "xlsm", "xlsb"])

    if uploaded_file is not None:
        try:
            upload_df = read_uploaded_file(uploaded_file)
            upload_df = normalize_headers(upload_df)

            required = ["Tanggal", "MAK", "Kegiatan", "Pagu", "Realisasi"]
            missing = [col for col in required if col not in upload_df.columns]

            if missing:
                detected = ", ".join(map(str, upload_df.columns.tolist())) or "tidak ada kolom"
                st.error(f"Kolom wajib belum ada: {', '.join(missing)}")
                st.caption(f"Kolom yang terbaca: {detected}")
                st.info(
                    "Gunakan header: Tanggal, No, MAK, Kegiatan, Pagu, Realisasi, Sisa Anggaran. Kolom Tanggal boleh berisi Januari, Februari, dan seterusnya tanpa tahun."
                )
            else:
                upload_df = normalize_data(upload_df)
                st.subheader("Preview")
                st.dataframe(display_data(upload_df), use_container_width=True, hide_index=True)

                if st.button("Simpan Data Upload", use_container_width=True):
                    st.session_state.data = normalize_data(
                        pd.concat([st.session_state.data, upload_df], ignore_index=True)
                    )
                    st.success("Data upload berhasil disimpan")
                    st.rerun()

        except Exception as exc:
            st.error(f"File gagal dibaca: {exc}")

    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# LIHAT DATA - ADMIN DAN OPERATOR
# =========================================================
elif menu == "Lihat Semua Data":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Monitoring Data Anggaran")

    if st.session_state.data.empty:
        st.warning("Belum ada data")
    else:
        df = normalize_data(st.session_state.data)

        col1, col2 = st.columns(2)
        with col1:
            search_mak = st.text_input("Cari MAK")
        with col2:
            search_kegiatan = st.text_input("Cari Kegiatan")

        filtered = df.copy()
        if search_mak:
            filtered = filtered[
                filtered["MAK"].str.contains(search_mak, case=False, na=False)
            ]
        if search_kegiatan:
            filtered = filtered[
                filtered["Kegiatan"].str.contains(search_kegiatan, case=False, na=False)
            ]

        total_pagu = filtered["Pagu"].sum()
        total_realisasi = filtered["Realisasi"].sum()
        total_sisa = filtered["Sisa Anggaran"].sum()

        c1, c2, c3 = st.columns(3)
        for column, title, value in [
            (c1, "Total Pagu", total_pagu),
            (c2, "Total Realisasi", total_realisasi),
            (c3, "Total Sisa Anggaran", total_sisa),
        ]:
            with column:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">{title}</div>
                    <div class="metric-value">{format_rupiah(value)}</div>
                </div>
                """, unsafe_allow_html=True)

        st.divider()

        summary = (
            filtered.groupby("MAK", as_index=False)[["Pagu", "Realisasi", "Sisa Anggaran"]]
            .sum()
        )

        if not summary.empty:
            chart = (
                alt.Chart(summary)
                .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
                .encode(
                    x=alt.X("MAK:N", title="MAK", sort="-y"),
                    y=alt.Y("Realisasi:Q", title="Realisasi"),
                    tooltip=["MAK", "Realisasi"]
                )
                .properties(height=320, title="Realisasi per MAK")
                .configure_title(color="#f1f5f9", fontSize=16)
                .configure_axis(labelColor="#f1f5f9", titleColor="#f1f5f9", gridColor="#35506f")
                .configure_view(strokeWidth=0)
            )
            st.altair_chart(chart, use_container_width=True)

        st.subheader("Detail Data")
        display_df = display_data(filtered)
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        st.download_button(
            "Download Data",
            data=to_csv(display_df),
            file_name="Monitoring_Anggaran.csv",
            mime="text/csv"
        )

        if not is_admin():
            st.info("Akun Operator hanya dapat input, upload, lihat, dan download data")

    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# KELOLA DATA - KHUSUS ADMIN
# =========================================================
elif menu == "Kelola Data":
    if not is_admin():
        st.error("Akses ditolak")
        st.stop()

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Kelola Data")

    if st.session_state.data.empty:
        st.warning("Belum ada data yang bisa dikelola")
    else:
        df = normalize_data(st.session_state.data)
        st.caption("Admin bisa mengubah data langsung di tabel, lalu klik Simpan Perubahan.")

        editable_df = df.copy()

        edited_df = st.data_editor(
            editable_df,
            use_container_width=True,
            hide_index=True,
            num_rows="fixed",
            disabled=["No", "Sisa Anggaran"],
            column_config={
                "Tanggal": st.column_config.SelectboxColumn(
                    "Tanggal", options=BULAN_LIST, required=True
                ),
                "No": st.column_config.NumberColumn("No"),
                "MAK": st.column_config.TextColumn("MAK", required=True),
                "Kegiatan": st.column_config.TextColumn("Kegiatan", required=True),
                "Pagu": st.column_config.NumberColumn("Pagu", min_value=0, format="Rp %.0f"),
                "Realisasi": st.column_config.NumberColumn("Realisasi", min_value=0, format="Rp %.0f"),
                "Sisa Anggaran": st.column_config.NumberColumn("Sisa Anggaran", format="Rp %.0f"),
            },
            key="admin_editor"
        )

        if st.button("Simpan Perubahan", use_container_width=True):
            st.session_state.data = normalize_data(edited_df)
            st.success("Perubahan berhasil disimpan")
            st.rerun()

        st.divider()
        st.subheader("Hapus Data")

        delete_options = df.index.tolist()
        selected_rows = st.multiselect(
            "Pilih data yang mau dihapus",
            options=delete_options,
            format_func=lambda idx: (
                f"No {df.loc[idx, 'No']} | {df.loc[idx, 'MAK']} | "
                f"{df.loc[idx, 'Kegiatan']}"
            )
        )

        confirm_delete = st.checkbox("Saya yakin mau menghapus data yang dipilih")

        if st.button(
            "Hapus Data Terpilih",
            use_container_width=True,
            disabled=not selected_rows or not confirm_delete
        ):
            remaining = df.drop(index=selected_rows).reset_index(drop=True)
            st.session_state.data = normalize_data(remaining)
            st.success(f"{len(selected_rows)} data berhasil dihapus")
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
