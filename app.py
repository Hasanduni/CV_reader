import streamlit as st
from PyPDF2 import PdfReader
from datetime import datetime
import pandas as pd
import os
import json
from openai import OpenAI

# --- Glama AI API Key ---
GLAMA_API_KEY = "glama_eyJhcGlLZXkiOiIxNWVmYzFmNS03ZDFhLTQyMGItODAwYy1iZjQ1ZDhhMzljNDkifQ"

# Initialize OpenAI-compatible client for Glama
client = OpenAI(
    api_key=GLAMA_API_KEY,
    base_url="https://glama.ai/api/gateway/openai/v1"
)

# --- Extract text from PDF ---
def extract_text_from_pdf(uploaded_file):
    pdf_reader = PdfReader(uploaded_file)
    text = ""
    for page in pdf_reader.pages:
        if page.extract_text():
            text += page.extract_text() + "\n"
    return text

# --- Glama CV parsing ---
def extract_cv_with_glama(text, candidate_id=9999):
    prompt = f"""
    Extract the following fields from the CV text below in JSON format:
    - University
    - Degree/Course
    - Previous Internships
    - Current Role
    - Skills & Tools
    - Experience History: list each experience with role, company, start_date, end_date

    CV Text:
    {text}
    """
    response = client.chat.completions.create(
        model="gemini-1",  # or "openai/gpt-4o"
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    result_text = response.choices[0].message.content
    try:
        data = json.loads(result_text)
    except:
        data = {}
    data["Candidate_ID"] = candidate_id
    return data

# --- Calculate total experience ---
def calculate_experience(experience_list):
    from dateutil import parser
    from dateutil.relativedelta import relativedelta
    total_months = 0
    lines = []
    for exp in experience_list:
        role = exp.get("role", "")
        company = exp.get("company", "")
        start = exp.get("start_date", "")
        end = exp.get("end_date", "Present")
        lines.append(f"{role} at {company}: {start} – {end}")
        try:
            start_date = parser.parse(start)
            end_date = datetime.today() if end.lower() == "present" else parser.parse(end)
            diff = relativedelta(end_date, start_date)
            total_months += diff.years * 12 + diff.months
        except:
            continue
    years = total_months // 12
    months = total_months % 12
    return f"{int(years)} years {int(months)} months", lines

# --- Streamlit UI ---
st.set_page_config(page_title="CV Parser with Glama", page_icon="📄", layout="wide")
st.title("📄 CV Parser using Glama AI")

upload_option = st.radio("Choose input type:", ["PDF Upload", "CSV Upload"])
candidate_id = 1001

# --- PDF Upload ---
if upload_option == "PDF Upload":
    uploaded_file = st.file_uploader("Upload CV (PDF only)", type=["pdf"])
    if uploaded_file is not None:
        text = extract_text_from_pdf(uploaded_file)
        row = extract_cv_with_glama(text, candidate_id)

        exp_list = row.get("Experience History", [])
        experience_str, experience_lines = calculate_experience(exp_list)
        row["Experience"] = experience_str

        # --- Candidate Info Cards ---
        st.subheader("✅ Parsed CV (Profile Summary)")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div style="background-color:#ADD8E6; color:#000; padding:20px; border-radius:12px;
                box-shadow:0 4px 12px rgba(0,0,0,0.1);">
                <h3 style="margin-top:0;color:#2c3e50;">👤 Candidate #{row.get('Candidate_ID')}</h3>
                <p><b>🎓 University:</b> {row.get('University', '-')}</p>
                <p><b>📘 Course:</b> {row.get('Degree/Course', '-')}</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div style="background-color:#ADD8E6; color:#000; padding:20px; border-radius:12px;
                box-shadow:0 4px 12px rgba(0,0,0,0.1);">
                <p><b>💼 Current Role:</b> {row.get('Current Role', '-')}</p>
                <p><b>👨‍🎓 Previous Internships:</b> {row.get('Previous Internships', 'None')}</p>
                <p><b>⏳ Experience:</b> {row.get('Experience')}</p>
            </div>
            """, unsafe_allow_html=True)

        # --- Skills & Tools ---
        skills_str = ", ".join(row.get("Skills & Tools", [])) if row.get("Skills & Tools") else "-"
        if skills_str != "-":
            st.markdown("### 🛠 Skills & Tools")
            skills_list = [s.strip() for s in skills_str.split(",")]
            skill_html = " ".join([
                f"<span style='background:#3498db;color:white;padding:6px 10px;border-radius:12px;margin:3px;display:inline-block;'>{skill}</span>"
                for skill in skills_list
            ])
            st.markdown(skill_html, unsafe_allow_html=True)

        # --- Detailed Experience ---
        if experience_lines:
            with st.expander("📂 Detailed Experience History"):
                for exp in experience_lines:
                    st.markdown(f"- {exp}")

        # --- Download Section ---
        st.subheader("📥 Download Extracted Data")
        df = pd.DataFrame([row])
        csv = df.to_csv(index=False).encode("utf-8")
        excel_file = "cv_extracted.xlsx"
        df.to_excel(excel_file, index=False)
        st.download_button("⬇️ Download CSV", data=csv, file_name="cv_extracted.csv", mime="text/csv")
        with open(excel_file, "rb") as f:
            st.download_button("⬇️ Download Excel", data=f, file_name="cv_extracted.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        if os.path.exists(excel_file):
            os.remove(excel_file)

# --- CSV Upload ---
elif upload_option == "CSV Upload":
    uploaded_csv = st.file_uploader("Upload CSV file with CV Text column", type=["csv"])
    if uploaded_csv is not None:
        df_input = pd.read_csv(uploaded_csv)
        if "CV Text" not in df_input.columns:
            st.error("CSV must contain a 'CV Text' column")
        else:
            parsed_rows = []
            for idx, row_data in df_input.iterrows():
                row_parsed = extract_cv_with_glama(row_data["CV Text"], candidate_id + idx)
                exp_list = row_parsed.get("Experience History", [])
                experience_str, _ = calculate_experience(exp_list)
                row_parsed["Experience"] = experience_str
                parsed_rows.append(row_parsed)

            df_output = pd.DataFrame(parsed_rows)
            st.dataframe(df_output)

            csv = df_output.to_csv(index=False).encode("utf-8")
            excel_file = "cv_extracted_batch.xlsx"
            df_output.to_excel(excel_file, index=False)
            st.download_button("⬇️ Download CSV", data=csv, file_name="cv_extracted_batch.csv", mime="text/csv")
            with open(excel_file, "rb") as f:
                st.download_button("⬇️ Download Excel", data=f, file_name="cv_extracted_batch.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            if os.path.exists(excel_file):
                os.remove(excel_file)
