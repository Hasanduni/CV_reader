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
        text += page.extract_text() + "\n"
    return text

# --- Function to parse CV text ---
def parse_cv(text):
    data = {
        "University / Educational Institution": [],
        "Qualifications / Degrees": [],
        "Skills": [],
        "Tools & Technologies": [],
        "Internships": [],
        "Previous Experience (total years)": [],
        "Certifications": [],
        "Current Role": []
    }

    # Example regex / keyword extraction (basic - can be improved with NLP)
    universities = re.findall(r"(University of [A-Za-z ]+|[A-Za-z ]+ University)", text)
    degrees = re.findall(r"(Bachelor|Master|PhD|Diploma|BSc|MSc|MBA|BE|ME|BS|MS)[^,\n]*", text)
    skills = re.findall(r"(Python|Java|C\+\+|SQL|Machine Learning|Data Science|Deep Learning|Statistics|R|Tableau|PowerBI)", text, re.IGNORECASE)
    tools = re.findall(r"(TensorFlow|PyTorch|Scikit-learn|Pandas|NumPy|Excel|Git|Docker|Kubernetes|Hadoop|Spark)", text, re.IGNORECASE)
    internships = re.findall(r"(Internship at [A-Za-z ]+|Intern at [A-Za-z ]+)", text)
    experience_years = re.findall(r"(\d+)\+?\s+years", text)
    certifications = re.findall(r"(Certified [A-Za-z ]+|AWS Certification|Azure Certification|Google Cloud Certification)", text)
    current_roles = re.findall(r"(Software Engineer|Data Scientist|ML Engineer|Research Assistant|Analyst|Developer)[^,\n]*", text)

    # Store extracted data
    data["University / Educational Institution"] = list(set(universities))
    data["Qualifications / Degrees"] = list(set(degrees))
    data["Skills"] = list(set(skills))
    data["Tools & Technologies"] = list(set(tools))
    data["Internships"] = list(set(internships))
    data["Previous Experience (total years)"] = list(set(experience_years))
    data["Certifications"] = list(set(certifications))
    data["Current Role"] = list(set(current_roles))

    return data

# --- Streamlit UI ---
st.title("📄 CV Parser App")
st.write("Upload a CV (PDF) and extract structured information.")

uploaded_file = st.file_uploader("Upload CV (PDF only)", type=["pdf"])

if uploaded_file is not None:
    text = extract_text_from_pdf(uploaded_file)
    extracted_data = parse_cv(text)

    st.subheader("📊 Extracted CV Information")

    # Convert to DataFrame for display
    df = pd.DataFrame([(k, ", ".join(v) if v else "-") for k, v in extracted_data.items()],
                      columns=["Category", "Extracted Information"])

    st.table(df)

    # --- Download options ---
    csv = df.to_csv(index=False).encode("utf-8")
    excel_file = "cv_extracted.xlsx"
    df.to_excel(excel_file, index=False)

    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name="cv_extracted.csv",
        mime="text/csv",
    )

    with open(excel_file, "rb") as f:
        st.download_button(
            label="📥 Download Excel",
            data=f,
            file_name="cv_extracted.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    # Clean up
    if os.path.exists(excel_file):
        os.remove(excel_file)
