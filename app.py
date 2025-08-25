import streamlit as st
import pandas as pd
import re
import os
from PyPDF2 import PdfReader

# --- Function to extract text from uploaded PDF ---
def extract_text_from_pdf(uploaded_file):
    pdf_reader = PdfReader(uploaded_file)
    text = ""
    for page in pdf_reader.pages:
        if page.extract_text():
            text += page.extract_text() + "\n"
    return text

# --- Function to parse CV text ---
def parse_cv(text, candidate_id=9999):
    # Extract using regex
    universities = re.findall(r"(University of [A-Za-z ]+|[A-Za-z ]+ University)", text)
    degrees = re.findall(r"(Bachelor|Master|PhD|Diploma|BSc|MSc|MBA|BE|ME|BS|MS)[^,\n]*", text)
    skills = re.findall(r"(Python|Java|C\+\+|SQL|Machine Learning|Data Science|Deep Learning|Statistics|R|Tableau|PowerBI)", text, re.IGNORECASE)
    tools = re.findall(r"(TensorFlow|PyTorch|Scikit-learn|Pandas|NumPy|Excel|Git|Docker|Kubernetes|Hadoop|Spark)", text, re.IGNORECASE)
    internships = re.findall(r"(Internship at [A-Za-z ]+|Intern at [A-Za-z ]+)", text)
    experience_years = re.findall(r"(\d+)\+?\s+years", text)
    current_roles = re.findall(r"(Software Engineer|Data Scientist|ML Engineer|Research Assistant|Analyst|Developer)[^,\n]*", text)

    # --- Map to dataset schema ---
    university = universities[0] if universities else "-"
    course = degrees[0] if degrees else "-"
    language = "English"   # default, improve if multilingual detection needed
    internship = internships[0] if internships else "None"
    exp_years = float(experience_years[0]) if experience_years else 0.0
    skills_combined = ", ".join(set(skills + tools)) if (skills or tools) else "-"
    current_role = current_roles[0] if current_roles else "-"
    target_role = "-"  # placeholder, model can predict later

    # Create structured row
    row = {
        "Candidate_ID": candidate_id,
        "University": university,
        "Course": course,
        "Language_Proficiency": language,
        "Previous_Internship": internship,
        "Experience_Years": exp_years,
        "Skills": skills_combined,
        "Current_Role": current_role,
        "Target_Role": target_role
    }

    return row

# --- Streamlit UI ---
st.title("📄 CV Parser → Job Dataset Aligner")
st.write("Upload a CV (PDF) → extract info → align with job recommendation dataset schema → download as CSV/Excel")

uploaded_file = st.file_uploader("Upload CV (PDF only)", type=["pdf"])

if uploaded_file is not None:
    text = extract_text_from_pdf(uploaded_file)
    parsed_row = parse_cv(text)

    st.subheader("📊 Parsed CV → Dataset Row")
    df = pd.DataFrame([parsed_row])
    st.table(df)

    # --- Download options ---
    csv = df.to_csv(index=False).encode("utf-8")
    excel_file = "cv_aligned.xlsx"
    df.to_excel(excel_file, index=False)

    st.download_button(
        label="📥 Download CSV (aligned row)",
        data=csv,
        file_name="cv_aligned.csv",
        mime="text/csv",
    )

    with open(excel_file, "rb") as f:
        st.download_button(
            label="📥 Download Excel (aligned row)",
            data=f,
            file_name="cv_aligned.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    # Clean up
    if os.path.exists(excel_file):
        os.remove(excel_file)
