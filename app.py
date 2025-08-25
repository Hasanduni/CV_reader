import streamlit as st
import re
from PyPDF2 import PdfReader
from dateutil import parser
from datetime import datetime
import pandas as pd
import os

# --- Extract text from PDF ---
def extract_text_from_pdf(uploaded_file):
    pdf_reader = PdfReader(uploaded_file)
    text = ""
    for page in pdf_reader.pages:
        if page.extract_text():
            text += page.extract_text() + "\n"
    return text

# --- Parse CV text ---
def parse_cv(text, candidate_id=9999):
    uni_patterns = re.findall(r"([A-Za-z ]+(University|Institute)[^\n]+)", text)
    degrees = re.findall(r"(Bachelor|Master|PhD|Diploma|BSc|MSc|MBA|BE|ME|BS|MS)[^,\n]*", text)
    internships = re.findall(r"(Internship at [A-Za-z ]+|Intern at [A-Za-z ]+)", text)
    current_roles = re.findall(r"(Software Engineer|Data Scientist|ML Engineer|Research Assistant|Analyst|Developer)[^,\n]*", text)

    exp_patterns = re.findall(
        r"([A-Za-z &]*(Intern|Engineer|Scientist|Analyst)[^\n]*\d{4} ?[–-] ?(Present|\d{4}))", text
    )

    skills = re.findall(r"(Python|Java|SQL|Machine Learning|Deep Learning|Data Science|R|C\+\+)", text, re.IGNORECASE)
    tools = re.findall(r"(TensorFlow|PyTorch|Pandas|NumPy|Excel|Git|Docker|Spark|scikit-learn)", text, re.IGNORECASE)

    total_exp_years = 0
    experience_lines = []
    for exp_line in exp_patterns:
        line = exp_line[0].strip()
        experience_lines.append(line)
        dates = re.findall(r"(\w+ \d{4}|\d{4}|Present)", line)
        if len(dates) >= 1:
            start = dates[0]
            end = dates[1] if len(dates) > 1 else "Present"
            try:
                start_date = parser.parse(start)
            except:
                continue
            end_date = datetime.today() if end.lower() == "present" else parser.parse(end)
            total_exp_years += (end_date - start_date).days / 365.0
    total_exp_years = round(total_exp_years, 1)

    row = {
        "Candidate_ID": candidate_id,
        "University": "; ".join([u[0] for u in uni_patterns]) if uni_patterns else "-",
        "Course": "; ".join(degrees) if degrees else "-",
        "Language_Proficiency": "English",
        "Previous_Internship": "; ".join(internships) if internships else "None",
        "Experience_Years": total_exp_years,
        "Skills": ", ".join(list(set(skills + tools))) if (skills or tools) else "-",
        "Current_Role": "; ".join(current_roles) if current_roles else "-",
        "Target_Role": "-"
    }

    return row, experience_lines

# --- Streamlit UI ---
st.set_page_config(page_title="CV Parser", page_icon="📄", layout="wide")
st.title("📄 CV Parser → Structured Layout")
st.write("Upload a CV (PDF) → Extract structured information with a modern UI")

uploaded_file = st.file_uploader("Upload CV (PDF only)", type=["pdf"])

if uploaded_file is not None:
    text = extract_text_from_pdf(uploaded_file)
    row, experience_lines = parse_cv(text)

    # --- Modern Card Layout ---
    st.subheader("✅ Candidate Information")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**🎓 University:** {row['University']}")
        st.markdown(f"**📘 Course:** {row['Course']}")
        st.markdown(f"**🌐 Languages:** {row['Language_Proficiency']}")

    with col2:
        st.markdown(f"**💼 Current Role:** {row['Current_Role']}")
        st.markdown(f"**⏳ Experience (Years):** {row['Experience_Years']}")
        st.markdown(f"**🛠 Skills & Tools:** {row['Skills']}")

    st.markdown(f"**👨‍🎓 Previous Internship(s):** {row['Previous_Internship']}")
    st.markdown(f"**🎯 Target Role:** {row['Target_Role']}")

    # --- Expandable for detailed experience ---
    if experience_lines:
        with st.expander("📂 Detailed Experiences"):
            for exp in experience_lines:
                st.markdown(f"- {exp}")

    # --- Download Section ---
    st.subheader("📥 Download Extracted Data")
    df = pd.DataFrame([row])
    csv = df.to_csv(index=False).encode("utf-8")
    excel_file = "cv_aligned.xlsx"
    df.to_excel(excel_file, index=False)

    st.download_button("⬇️ Download CSV", data=csv, file_name="cv_aligned.csv", mime="text/csv")
    with open(excel_file, "rb") as f:
        st.download_button("⬇️ Download Excel", data=f, file_name="cv_aligned.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    if os.path.exists(excel_file):
        os.remove(excel_file)
