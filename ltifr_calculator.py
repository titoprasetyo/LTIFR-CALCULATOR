import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
from io import BytesIO
import tempfile

# ReportLab untuk tabel PDF
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# =============================
# Fungsi Hitung LTIFR
# =============================
def hitung_ltifr(lti, jam_kerja):
    if jam_kerja <= 0:
        return None
    return round((lti * 1_000_000) / jam_kerja, 2)

# =============================
# Fungsi Export PDF Kalkulator
# =============================
def buat_pdf_kalkulator(lti, jam_kerja, hasil):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "Laporan LTIFR - Kalkulator", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Jumlah LTI       : {lti}", ln=True)
    pdf.cell(0, 10, f"Total Jam Kerja  : {jam_kerja}", ln=True)
    pdf.cell(0, 10, f"Hasil LTIFR      : {hasil}", ln=True)

    return pdf.output(dest="S").encode("latin1")

# =============================
# Fungsi Export PDF Excel (TABEL RAPIH)
# =============================
def buat_pdf_excel(df, stats, fig_buf):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
    elements = []
    styles = getSampleStyleSheet()

    # Judul
    elements.append(Paragraph("📊 Laporan LTIFR - Data Excel", styles['Title']))
    elements.append(Spacer(1, 12))

    # Tabel Data
    data = [df.columns.tolist()] + df.values.tolist()
    table = Table(data, repeatRows=1)

    # Style tabel
    style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4a90e2")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('FONTSIZE', (0,1), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('BACKGROUND', (0,1), (-1,-1), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ])
    table.setStyle(style)
    elements.append(table)

    elements.append(Spacer(1, 20))

    # Statistik
    elements.append(Paragraph("📈 Statistik LTIFR", styles['Heading2']))
    stat_data = [
        ["LTIFR Terendah", stats["min"]],
        ["LTIFR Tertinggi", stats["max"]],
        ["Rata-rata LTIFR", stats["mean"]],
    ]
    stat_table = Table(stat_data)
    stat_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('ALIGN', (0,0), (-1,-1), 'CENTER')
    ]))
    elements.append(stat_table)

    elements.append(Spacer(1, 20))

    # Grafik
    elements.append(Paragraph("📊 Grafik Tren LTIFR", styles['Heading2']))
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
        tmpfile.write(fig_buf.getbuffer())
        tmp_path = tmpfile.name
    from reportlab.platypus import Image
    elements.append(Image(tmp_path, width=500, height=250))

    doc.build(elements)
    buffer.seek(0)
    return buffer

# =============================
# Konfigurasi Halaman
# =============================
st.set_page_config(
    page_title="LTIFR Dashboard",
    page_icon="📊",
    layout="centered"
)

st.markdown("<h1 style='text-align: center; color: #2E86C1;'>📊 LTIFR Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: gray;'>Lost Time Injury Frequency Rate</h4>", unsafe_allow_html=True)
st.write("---")

# =============================
# Pilihan Mode
# =============================
mode = st.radio("Pilih Mode:", ["🧮 Kalkulator LTIFR", "📂 Upload Excel"], horizontal=True)

# =============================
# MODE KALKULATOR
# =============================
if mode == "🧮 Kalkulator LTIFR":
    st.subheader("🧮 Kalkulator LTIFR")
    col1, col2 = st.columns(2)

    with col1:
        jumlah_lti = st.number_input("🔴 Jumlah LTI", min_value=0, step=1)

    with col2:
        jam_kerja = st.number_input("⏱️ Total Jam Kerja", min_value=0, step=1000)

    if st.button("⚡ Hitung LTIFR", use_container_width=True):
        hasil = hitung_ltifr(jumlah_lti, jam_kerja)
        if hasil is not None:
            st.success(f"✅ LTIFR = **{hasil}**")
            st.markdown(
                f"""
                <div style="background-color:#E8F6F3;padding:20px;border-radius:15px;text-align:center;">
                    <h2 style="color:#117A65;">📈 Hasil Perhitungan</h2>
                    <h1 style="color:#0B5345;">{hasil}</h1>
                    <p style="color:gray;">(Lost Time Injury Frequency Rate)</p>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Tombol Download PDF
            pdf_bytes = buat_pdf_kalkulator(jumlah_lti, jam_kerja, hasil)
            st.download_button("📥 Download PDF", data=pdf_bytes, file_name="ltifr_kalkulator.pdf", mime="application/pdf")
        else:
            st.error("❌ Jam kerja harus lebih dari 0 untuk menghitung LTIFR.")

# =============================
# MODE UPLOAD EXCEL
# =============================
elif mode == "📂 Upload Excel":
    st.subheader("📂 Upload Data LTIFR (Excel)")
    uploaded_file = st.file_uploader("Upload file Excel (.xlsx)", type=["xlsx"])

    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)

            if all(col in df.columns for col in ["Bulan", "LTI", "Jam_Kerja"]):
                df["LTIFR"] = df.apply(lambda x: hitung_ltifr(x["LTI"], x["Jam_Kerja"]), axis=1)

                st.success("✅ Data berhasil dimuat!")
                st.write("### Data LTIFR")
                st.dataframe(df)

                # Pilihan jenis grafik
                chart_type = st.selectbox("Pilih Jenis Grafik:", ["Line", "Bar", "Pie"])

                st.write(f"### 📊 Grafik LTIFR ({chart_type})")
                fig, ax = plt.subplots()

                if chart_type == "Line":
                    ax.plot(df["Bulan"], df["LTIFR"], marker="o", linestyle="-", linewidth=2, color="teal")
                    ax.set_title("Tren LTIFR per Bulan", fontsize=14, color="navy")
                    ax.set_xlabel("Bulan")
                    ax.set_ylabel("LTIFR")
                    ax.grid(True)

                elif chart_type == "Bar":
                    ax.bar(df["Bulan"], df["LTIFR"], color="orange")
                    ax.set_title("LTIFR per Bulan", fontsize=14, color="navy")
                    ax.set_xlabel("Bulan")
                    ax.set_ylabel("LTIFR")

                elif chart_type == "Pie":
                    ax.pie(df["LTIFR"], labels=df["Bulan"], autopct="%1.1f%%", startangle=90)
                    ax.set_title("Distribusi LTIFR per Bulan", fontsize=14, color="navy")

                st.pyplot(fig)

                # Simpan grafik ke buffer
                fig_buf = BytesIO()
                fig.savefig(fig_buf, format="png")
                fig_buf.seek(0)

                # Statistik
                st.write("### 📈 Statistik LTIFR")
                col1, col2, col3 = st.columns(3)
                col1.metric("📉 LTIFR Terendah", df["LTIFR"].min())
                col2.metric("📈 LTIFR Tertinggi", df["LTIFR"].max())
                col3.metric("⚖️ Rata-rata LTIFR", round(df["LTIFR"].mean(), 2))

                # Tombol Download PDF
                stats = {
                    "min": df["LTIFR"].min(),
                    "max": df["LTIFR"].max(),
                    "mean": round(df["LTIFR"].mean(), 2)
                }
                pdf_buffer = buat_pdf_excel(df, stats, fig_buf)
                st.download_button("📥 Download PDF", data=pdf_buffer, file_name="ltifr_excel.pdf", mime="application/pdf")

            else:
                st.error("❌ Format Excel salah. Pastikan ada kolom: **Bulan, LTI, Jam_Kerja**")

        except Exception as e:
            st.error(f"⚠️ Gagal membaca file: {e}")

    else:
        st.info("📌 Silakan upload file Excel untuk melihat grafik LTIFR.")

# =============================
# Info Rumus
# =============================
st.write("---")
st.markdown("""
### ℹ️ Rumus LTIFR  
\\[
LTIFR = \\frac{Jumlah\\ LTI \\times 1.000.000}{Total\\ Jam\\ Kerja}
\\]

📌 **Keterangan**  
- **LTI** = Lost Time Injury  
- **Jam Kerja** = Total jam kerja karyawan dalam periode tertentu  
- Faktor **1.000.000** digunakan agar hasil perbandingan seragam  
""")
