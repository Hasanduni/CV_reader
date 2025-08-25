import streamlit as st
import re
import os
from PyPDF2 import PdfReader
import pandas as pd
from dateutil import parser
from datetime import datetime

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
    # Universities + inline degrees
    uni_patterns = re.findall(r"([A-Za-z ]+(University|Institute)[^\n]+)", text)

    # Experience lines with roles + dates
    exp_patterns = re.findall(
        r"([A-Za-z ]*(Intern|Engineer|Scientist|Analyst)[^\n]*\d{4} ?[–-] ?(Present|\d{4}))", text
    )

    # Skills and tools
    skills = re.findall(r"(Python|Java|SQL|Machine Learning|Deep Learning|Data Science|R|C\+\+)", text, re.IGNORECASE)
    tools = re.findall(r"(TensorFlow|PyTorch|Pandas|NumPy|Excel|Git|Docker|Spark|scikit-learn)", text, re.IGNORECASE)

    # Calculate experience years from dates
    total_exp_years = 0
    for exp_line in exp_patterns:
        line = exp_line[0]
        dates = re.findall(r"(\w+ \d{4}|\d{4}|Present)", line)
        if len(dates) == 2:
            start, end = dates
        elif len(dates) == 1:
            start, end = dates[0], "Present"
        else:
            continue

        try:
            start_date = parser.parse(start)
        except:
            start_date = None
        if end.lower() == "present":
            end_date = datetime.today()
        else:
            try:
                end_date = parser.parse(end)
            except:
                end_date = None
        if start_date and end_date:
            total_exp_years += (end_date - start_date).days / 365.0

    total_exp_years = round(total_exp_years, 1)

    # Combine results
    parsed_data = {
        "Candidate_ID": candidate_id,
        "Universities": [u[0] for u in uni_patterns],
        "Experiences": [e[0] for e in exp_patterns],
        "Skills": list(set(skills + tools)),
        "Experience_Years": total_exp_years
    }
    return parsed_data

# --- Streamlit UI ---
st.title("📄 CV Parser → Job Dataset Aligner")
st.write("Upload a CV (PDF) → extract structured info → compute experience automatically → download for dataset")

uploaded_file = st.file_uploader("Upload CV (PDF only)", type=["pdf"])

if uploaded_file is not None:
    text = extract_text_from_pdf(uploaded_file)
    parsed_data = parse_cv(text)

    st.subheader("✅ Extracted CV Information")

    # Display as readable text
    if parsed_data["Universities"]:
        st.markdown("**🎓 Universities / Degrees**")
        for u in parsed_data["Universities"]:
            st.write("- " + u)

    if parsed_data["Experiences"]:
        st.markdown("**💼 Experience**")
        for e in parsed_data["Experiences"]:
            st.write("- " + e)

    if parsed_data["Skills"]:
        st.markdown("**🛠️ Skills & Tools**")
        st.write(", ".join(parsed_data["Skills"]))

    st.markdown(f"**📊 Total Experience (Years):** {parsed_data['Experience_Years']}")

    # Save structured row for dataset
    row = {
        "Candidate_ID": parsed_data["Candidate_ID"],
        "University": "; ".join(parsed_data["Universities"]) if parsed_data["Universities"] else "-",
        "Course": "-",  # Could extract degree names separately if needed
        "Language_Proficiency": "English",
        "Previous_Internship": "-", 
        "Experience_Years": parsed_data["Experience_Years"],
        "Skills": ", ".join(parsed_data["Skills"]),
        "Current_Role": "-", 
        "Target_Role": "-"  
    }
    df = pd.DataFrame([row])

    # --- Download options ---
    csv = df.to_csv(index=False).encode("utf-8")
    excel_file = "cv_aligned.xlsx"
    df.to_excel(excel_file, index=False)

    st.download_button("📥 Download CSV (aligned row)", data=csv, file_name="cv_aligned.csv", mime="text/csv")
    with open(excel_file, "rb") as f:
        st.download_button("📥 Download Excel (aligned row)", data=f, file_name="cv_aligned.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    if os.path.exists(excel_file):
        os.remove(excel_file)
