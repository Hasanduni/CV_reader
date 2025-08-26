import streamlit as st
import re
from PyPDF2 import PdfReader
from dateutil import parser
from dateutil.relativedelta import relativedelta
from datetime import datetime
import pandas as pd
import os
import json
import gspread
from google.oauth2.service_account import Credentials

# --- Extract text from PDF ---
def extract_text_from_pdf(uploaded_file):
    pdf_reader = PdfReader(uploaded_file)
    text = ""
    for page in pdf_reader.pages:
        if page.extract_text():
            text += page.extract_text() + "\n"
    return text

def parse_cv(text, candidate_id=9999):
    # Universities
    uni_patterns = re.findall(r"(University of [A-Za-z ]+|Institute of [A-Za-z ]+)", text)

    # Degrees/Courses
    degrees = re.findall(
        r"(?:Degree:\s*)?(B\.?Sc\.?(?:\s*\(Hons\))?[^\n,]*|Bachelor[^\n,]*|Diploma[^\n,]*|Undergraduate[^\n,]*)",
        text,
    )

    # Internships
    internships = re.findall(r"(?:Internship at|Intern at|[A-Za-z ]+ Intern)", text)

    # Current roles
    current_roles = re.findall(r"(?:Current Role:\s*-?\s*)([A-Za-z ]+)", text)

    # Experience patterns
    exp_patterns = re.findall(
        r"((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|"
        r"Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s?\d{4}\s*[–-]\s*"
        r"(?:Present|(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|"
        r"Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s?\d{4}))",
        text,
    )

    # Skills and Tools
    skills = re.findall(
        r"(Python|Java|SQL|HTML|CSS|JavaScript|Machine Learning|Deep Learning|Data Science|R|C\+\+)",
        text,
        re.IGNORECASE,
    )
    tools = re.findall(
        r"(TensorFlow|PyTorch|Pandas|NumPy|Excel|Git|Docker|Spark|scikit-learn|Eclipse|NetBeans|MySQL)",
        text,
        re.IGNORECASE,
    )

    # --- Calculate total experience in months ---
    total_exp_months = 0
    for exp_line in exp_patterns:
        try:
            start, end = re.findall(r"(\w+ \d{4}|Present)", exp_line)
            start_date = parser.parse(start)
            end_date = datetime.today() if end.lower() == "present" else parser.parse(end)
            diff = relativedelta(end_date, start_date)
            total_exp_months += diff.years * 12 + diff.months
        except:
            continue

    years = total_exp_months // 12
    months = total_exp_months % 12

    # --- Map to your spreadsheet columns ---
    row = {
        "Candidate_ID": candidate_id,
        "Course_University": "; ".join(degrees) + " | " + "; ".join(list(set(uni_patterns))) if (degrees or uni_patterns) else "-",
        "Language_Proficiency": "English",
        "Previous_Internship": "; ".join(internships) if internships else "None",
        "Experience_Years": f"{years}.{months:02d}",
        "Skills": ", ".join(list(set(skills + tools))) if (skills or tools) else "-",
        "Current_Role": "; ".join(current_roles) if current_roles else "-",
        "Target_Role": "-",  # empty for now
    }

    return row, exp_patterns


# --- Streamlit UI ---
st.set_page_config(page_title="CV Parser", page_icon="📄", layout="wide")
st.title("📄 CV Parser")
st.write("Upload a CV (PDF)")

uploaded_file = st.file_uploader("Upload CV (PDF only)", type=["pdf"])

if uploaded_file is not None:
    text = extract_text_from_pdf(uploaded_file)
    row, experience_lines = parse_cv(text)

    # Candidate Info Card
    st.subheader("✅ Parsed CV (Profile Summary)")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            f"""
            <div style="background-color:#ADD8E6; color:#000; padding:20px; border-radius:12px;
                box-shadow:0 4px 12px rgba(0,0,0,0.1);">
                <h3 style="margin-top:0;color:#2c3e50;">👤 Candidate </h3>
                <p><b>🎓 Course & University:</b> {row['Course_University']}</p>
                <p><b>🌐 Language:</b> {row['Language_Proficiency']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div style="background-color:#ADD8E6; color:#000; padding:20px; border-radius:12px;
                box-shadow:0 4px 12px rgba(0,0,0,0.1);">
                <p><b>👨‍🎓 Previous Internships:</b> {row['Previous_Internship']}</p>
                <p><b>⏳ Experience:</b> {row['Experience']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Skills & Tools
    if row["Skills"] != "-":
        st.markdown("### 🛠 Skills & Tools")
        skills_list = [s.strip() for s in row["Skills"].split(",")]
        skill_html = " ".join(
            [
                f"<span style='background:#3498db;color:white;padding:6px 10px;border-radius:12px;margin:3px;display:inline-block;'>{skill}</span>"
                for skill in skills_list
            ]
        )
        st.markdown(skill_html, unsafe_allow_html=True)

    # Download Section
    st.subheader("📥 Download Extracted Data")
    df = pd.DataFrame([row])
    csv = df.to_csv(index=False).encode("utf-8")
    excel_file = "cv_aligned.xlsx"
    df.to_excel(excel_file, index=False)

    st.download_button("⬇ Download CSV", data=csv, file_name="cv_aligned.csv", mime="text/csv")
    with open(excel_file, "rb") as f:
        st.download_button(
            "⬇ Download Excel",
            data=f,
            file_name="cv_aligned.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    if os.path.exists(excel_file):
        os.remove(excel_file)

    # --- Save to Google Sheets ---
    st.subheader("☁ Save to Google Sheets")

    # Use Streamlit Secrets
    key_dict = json.loads(st.secrets["GOOGLE_SHEET_KEY"])
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(key_dict, scopes=scopes)
    client = gspread.authorize(creds)

    sheet = client.open_by_url(
        "https://docs.google.com/spreadsheets/d/1o7KkNumt_MSO-knsuZHNKnCq0fzCTfv-P0ArDzfvA4c/edit#gid=476317413"
    ).sheet1

    if st.button("💾 Save to Google Sheet"):
        sheet.append_row(list(row.values()))
        st.success("Candidate data saved to Google Sheet ✅")
